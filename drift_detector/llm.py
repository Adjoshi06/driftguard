from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .config import LLMSettings
from .models import DriftCandidate, DriftIssue, Severity

logger = logging.getLogger(__name__)


def create_chat_model(settings: LLMSettings) -> BaseChatModel:
    provider = settings.provider.lower()

    if provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "langchain-community package is required for Ollama provider"
            ) from exc

        return ChatOllama(
            model=settings.model,
            base_url=settings.base_url,
            temperature=settings.temperature,
        )

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "langchain-openai package is required for OpenAI provider"
            ) from exc

        return ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key,
            temperature=settings.temperature,
            base_url=settings.base_url,
        )

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "langchain-anthropic package is required for Anthropic provider"
            ) from exc

        return ChatAnthropic(
            model=settings.model,
            api_key=settings.api_key,
            temperature=settings.temperature,
        )

    # Fallback to generic constructor via LangChain hub
    try:
        from langchain.chat_models import init_chat_model
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            f"Unsupported LLM provider '{settings.provider}'. "
            "Install provider-specific LangChain integration."
        ) from exc

    logger.warning(
        "Using generic init_chat_model for provider '%s'. "
        "Ensure the provider is supported by LangChain.",
        settings.provider,
    )
    return init_chat_model(
        model=settings.model,
        model_provider=settings.provider,
        temperature=settings.temperature,
        api_key=settings.api_key,
    )


class LLMClient:
    """Wraps LangChain chat models to provide consistent suggestions."""

    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model
        self._chain = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        (
                            "You are a senior technical writer assisting developers in "
                            "keeping documentation aligned with code changes. "
                            "Analyze the provided change and documentation context. "
                            "Suggest concise, actionable documentation updates. "
                            "Respond as JSON with keys: summary (string), "
                            "severity (critical|medium|low), suggestion (string), "
                            "doc_excerpt (optional string)."
                        ),
                    ),
                    (
                        "human",
                        (
                            "Code change (type: {drift_type}):\n{code_change}\n\n"
                            "Documentation references (changed={doc_changed}):\n"
                            "{documentation}\n\n"
                            "Why it matters: {candidate_description}"
                        ),
                    ),
                ]
            )
            | chat_model
            | StrOutputParser()
        )

    def generate_issue(
        self,
        candidate: DriftCandidate,
        *,
        fallback_severity: Severity = Severity.MEDIUM,
    ) -> DriftIssue:
        documentation_text = []
        doc_changed = []
        for ref in candidate.documentation:
            doc_changed.append("yes" if ref.changed else "no")
            documentation_text.append(
                f"{ref.file_path} (changed={ref.changed}):\n{ref.snippet}"
            )

        if not documentation_text:
            documentation_text.append("No related documentation found.")
            doc_changed.append("n/a")

        prompt_inputs = {
            "drift_type": candidate.drift_type.value,
            "code_change": candidate.change.summary
            + "\n\n"
            + (candidate.change.new_code or candidate.change.old_code or ""),
            "documentation": "\n\n---\n\n".join(documentation_text),
            "doc_changed": ", ".join(doc_changed),
            "candidate_description": candidate.description,
        }

        try:
            raw = self._chain.invoke(prompt_inputs)
            data = json.loads(raw)
        except Exception as exc:  # pragma: no cover - runtime fallback
            logger.warning("LLM suggestion failed (%s). Using fallback.", exc)
            data = {
                "summary": candidate.description,
                "severity": fallback_severity.value,
                "suggestion": "Review and update related documentation accordingly.",
                "doc_excerpt": None,
            }

        severity = _parse_severity(data.get("severity"), fallback_severity)
        suggestion = data.get("suggestion") or candidate.description
        summary = data.get("summary") or candidate.description
        doc_excerpt = data.get("doc_excerpt")

        return DriftIssue(
            drift_type=candidate.drift_type,
            severity=severity,
            file_path=candidate.change.file_path,
            summary=summary,
            suggestion=suggestion,
            code_snippet=candidate.change.new_code or candidate.change.old_code or "",
            documentation_snippet=doc_excerpt,
            metadata={
                "provider": type(self.chat_model).__name__,
                "symbol": candidate.change.symbol,
            },
        )


def _parse_severity(value: Optional[str], default: Severity) -> Severity:
    if not value:
        return default
    normalized = value.strip().lower()
    for severity in Severity:
        if severity.value == normalized:
            return severity
    return default

