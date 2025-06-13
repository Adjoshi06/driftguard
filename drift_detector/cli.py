from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional, Sequence

from .config import Settings, load_settings
from .drift_analysis import DriftDetector
from .llm import LLMClient, create_chat_model
from .models import DriftReport, Severity
from .report import ReportRenderer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect documentation drift in a git repository."
    )
    parser.add_argument("--repo", default=".", help="Path to the git repository.")
    parser.add_argument("--from", dest="from_ref", help="Base commit ref for diff.")
    parser.add_argument("--to", dest="to_ref", help="Target commit ref for diff.")
    parser.add_argument(
        "--since",
        help="Commit reference to compare against (e.g., HEAD~1).",
    )
    parser.add_argument(
        "--branch",
        help="Branch to compare against the current HEAD.",
    )
    parser.add_argument(
        "--output-format",
        choices=("terminal", "json", "html"),
        help="Override output format.",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Persist report to disk (uses REPORT_PATH or default).",
    )
    parser.add_argument(
        "--report-path",
        help="Directory where reports should be saved.",
    )
    parser.add_argument(
        "--provider",
        help="Override LLM provider (ollama, openai, anthropic, ...).",
    )
    parser.add_argument("--model", help="Override LLM model identifier.")
    parser.add_argument("--api-key", help="Override LLM API key.")
    parser.add_argument("--base-url", help="Override LLM base URL (for local endpoints).")
    parser.add_argument(
        "--temperature",
        type=float,
        help="Override LLM temperature.",
    )
    parser.add_argument(
        "--severity-threshold",
        choices=[s.value for s in Severity],
        help="Only report issues at or above this severity.",
    )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_path = Path(args.repo).expanduser().resolve()
    _ensure_env_overrides(args)

    settings = load_settings(
        repo_path,
        since=args.since,
        from_ref=args.from_ref,
        to_ref=args.to_ref,
        branch=args.branch,
    )

    if args.output_format:
        settings.output.format = args.output_format
    if args.save_report:
        settings.output.save_report = True
    if args.report_path:
        settings.output.report_path = Path(args.report_path).expanduser().resolve()
    if args.severity_threshold:
        settings.analysis.severity_threshold = args.severity_threshold

    chat_model = create_chat_model(settings.llm)
    llm_client = LLMClient(chat_model)

    detector = DriftDetector.from_settings(settings, llm_client)
    report = detector.run(
        from_ref=settings.from_ref,
        to_ref=settings.to_ref,
        since=settings.since,
        branch=settings.branch,
    )

    renderer = ReportRenderer(output_format=settings.output.format)
    output = renderer.render(report)
    print(output)

    if settings.output.save_report:
        saved_path = renderer.save(report, settings.output.report_path)
        print(f"\nReport saved to {saved_path}")

    if _has_critical_issues(report):
        return 1
    return 0


def _ensure_env_overrides(args: argparse.Namespace) -> None:
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model
    if args.api_key:
        os.environ["LLM_API_KEY"] = args.api_key
    if args.base_url:
        os.environ["LLM_BASE_URL"] = args.base_url
    if args.temperature is not None:
        os.environ["LLM_TEMPERATURE"] = str(args.temperature)
    if args.severity_threshold:
        os.environ["SEVERITY_THRESHOLD"] = args.severity_threshold
    if args.output_format:
        os.environ["OUTPUT_FORMAT"] = args.output_format
    if args.report_path:
        os.environ["REPORT_PATH"] = args.report_path


def _has_critical_issues(report: DriftReport) -> bool:
    return any(issue.severity == Severity.CRITICAL for issue in report.issues)

