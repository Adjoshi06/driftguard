from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class LLMSettings:
    provider: str = "ollama"
    model: str = "llama3.1"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.0


@dataclass
class AnalysisSettings:
    severity_threshold: str = "low"
    auto_ignore_private_functions: bool = True
    check_examples: bool = True
    check_inline_comments: bool = True


@dataclass
class OutputSettings:
    format: str = "terminal"
    save_report: bool = False
    report_path: Path = Path("./drift_reports")


@dataclass
class Settings:
    repo_path: Path
    llm: LLMSettings
    analysis: AnalysisSettings
    output: OutputSettings
    since: Optional[str] = None
    from_ref: Optional[str] = None
    to_ref: Optional[str] = None
    branch: Optional[str] = None


def _env_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(
    repo_path: Path,
    *,
    since: Optional[str] = None,
    from_ref: Optional[str] = None,
    to_ref: Optional[str] = None,
    branch: Optional[str] = None,
) -> Settings:
    load_dotenv()

    llm = LLMSettings(
        provider=os.getenv("LLM_PROVIDER", "ollama"),
        model=os.getenv("LLM_MODEL", "llama3.1"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
    )

    analysis = AnalysisSettings(
        severity_threshold=os.getenv("SEVERITY_THRESHOLD", "low"),
        auto_ignore_private_functions=_env_bool(
            os.getenv("AUTO_IGNORE_PRIVATE_FUNCTIONS"), True
        ),
        check_examples=_env_bool(os.getenv("CHECK_EXAMPLES"), True),
        check_inline_comments=_env_bool(os.getenv("CHECK_INLINE_COMMENTS"), True),
    )

    output = OutputSettings(
        format=os.getenv("OUTPUT_FORMAT", "terminal"),
        save_report=_env_bool(os.getenv("SAVE_REPORT"), False),
        report_path=Path(os.getenv("REPORT_PATH", "./drift_reports")),
    )

    return Settings(
        repo_path=repo_path,
        llm=llm,
        analysis=analysis,
        output=output,
        since=since,
        from_ref=from_ref,
        to_ref=to_ref,
        branch=branch,
    )

