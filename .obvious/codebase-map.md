# Codebase map — driftguard

Single-app Python CLI. Depth 2. One top-level package, no sub-apps.

| Path | Kind | What it does |
|---|---|---|
| `drift_detector.py` | file | Legacy root entry point; delegates to `run_cli` |
| `.env.example` | config | Template for all runtime settings (LLM, thresholds, output) |
| `requirements.txt` | deps | GitPython, LangChain (+providers), python-dotenv, chromadb |
| `drift_detector/__init__.py` | module | Package marker |
| `drift_detector/__main__.py` | module | `python -m drift_detector` entry |
| `drift_detector/cli.py` | module | argparse CLI; wires Settings → GitAnalyzer/DocumentationFinder/LLMClient → DriftDetector → ReportRenderer |
| `drift_detector/config.py` | module | Dataclass settings (`LLMSettings`, `AnalysisSettings`) loaded from env/`.env` via python-dotenv |
| `drift_detector/git_analysis.py` | module | GitPython diff → `CodeChange`s; Python functions parsed with `ast` (signatures, docstrings) |
| `drift_detector/doc_discovery.py` | module | `DocumentationFinder`: indexes README/docs/examples, finds references to changed symbols |
| `drift_detector/drift_analysis.py` | module | `DriftDetector`: heuristic drift rules (missing docstring, signature change, removed-but-documented) + orchestration |
| `drift_detector/llm.py` | module | Provider factory (`ollama`/`openai`/`anthropic`/generic) + LLMClient chain; falls back to heuristic output when the LLM is unreachable |
| `drift_detector/models.py` | module | Dataclasses/enums: `DriftReport`, `DriftIssue`, `DriftCandidate`, `CodeChange`, `Severity`, `DriftType` |
| `drift_detector/report.py` | module | `ReportRenderer`: terminal/JSON/HTML output; `save()` writes timestamped reports |

Data flow: `cli.run_cli` → `Settings` (env) → `GitAnalyzer.collect_changes`
(diff of resolved refs) → `DocumentationFinder.references_for_symbol` →
`DriftDetector.run` heuristics → `LLMClient.generate_issue` (optional LLM
grading; falls back) → `ReportRenderer.render/save`. Exit code 1 when critical
issues are found.
