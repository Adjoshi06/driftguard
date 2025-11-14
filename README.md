# Driftguard

Detects gaps between source code changes and related documentation updates. Designed for minimal setup while remaining flexible across LLM providers.

## Features

- Analyzes git diffs between commits, branches, or arbitrary revisions.
- Detects common drift scenarios:
  - New Python functions without docstrings.
  - Function signature changes not reflected in docs.
  - Removed code still referenced in documentation.
- Automatically discovers relevant documentation references (`README`, `docs/`, `examples/`, etc.).
- Uses LangChain to plug into Ollama, OpenAI, Anthropic, or any compatible LLM for drift assessment and suggestion generation.
- CLI-first workflow with optional report saving (`terminal`, `json`, or `html`).
- Exit code 1 when critical issues are found (handy for CI/CD).

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
# or source .venv/bin/activate on macOS/Linux

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to point at your preferred LLM provider and model (examples provided below).

Run against the current repository:

```bash
python drift_detector.py --since HEAD~1
```

Compare two commits:

```bash
python drift_detector.py --from abc123 --to def456
```

Analyze another branch:

```bash
python drift_detector.py --branch feature/new-api
```

Save the report and emit JSON:

```bash
python drift_detector.py --since HEAD~1 --output-format json --save-report
```

## Configuration

The detector pulls defaults from environment variables (loaded via `.env` if present).

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
LLM_BASE_URL=http://localhost:11434
LLM_API_KEY=
LLM_TEMPERATURE=0.1

SEVERITY_THRESHOLD=medium
AUTO_IGNORE_PRIVATE_FUNCTIONS=true
CHECK_EXAMPLES=true
CHECK_INLINE_COMMENTS=true

OUTPUT_FORMAT=terminal
SAVE_REPORT=false
REPORT_PATH=./drift_reports/
```

Override any option at runtime via CLI flags (e.g., `--provider openai --model gpt-4o-mini`).

### Provider Notes

- **Ollama**: start the Ollama server locally, ensure `LLM_BASE_URL` matches your endpoint.
- **OpenAI**: install `langchain-openai`, set `LLM_API_KEY`, optionally override `LLM_BASE_URL` for Azure.
- **Anthropic**: install `langchain-anthropic`, set `LLM_API_KEY`.
- **Other providers**: supply the `LLM_PROVIDER` name recognized by LangChain’s `init_chat_model`.

### Severity Threshold

`SEVERITY_THRESHOLD` (or `--severity-threshold`) filters results below the chosen level:
`low` < `medium` < `critical`. CI pipelines can set this to `medium` or `critical`.

## How It Works

1. **Git Analysis** – `GitPython` calculates the diff between the selected revisions. Python functions are parsed via `ast` to capture signatures, docstrings, and code blocks.
2. **Documentation Discovery** – All docs (`README*`, `docs/`, `examples/`, etc.) are scanned for references to changed symbols.
3. **Drift Heuristics** – Built-in checks flag likely drift scenarios (missing docstrings, signature changes, removed features still documented, and general mismatches).
4. **LLM Evaluation** – Detected candidates are sent to the configured LLM through LangChain. The model produces severity, rationale, and concrete update suggestions in JSON.
5. **Reporting** – Results are grouped by severity and rendered to the terminal, JSON, or basic HTML. Saved reports include timestamps for tracking.

## Example Output

```
Documentation Drift Report — 2 issues detected, 1 critical, 1 medium

CRITICAL (1)
- src/api/users.py: Signature for users.create changed but docs were not updated
  Suggestion: Update API docs in docs/api/users.md to reflect the new payload schema.

MEDIUM (1)
- src/metrics.py: Function metrics.calculate_summary was added without a docstring
  Suggestion: Add a docstring describing parameters `data`, `threshold`, and the return type.
```

## Extending the Prototype

- Add `.driftignore` support for ignoring directories or file patterns.
- Persist history with ChromaDB (hook into `drift_detector/report.py` or a new module).
- Implement auto-fix mode that drafts doc updates via the LLM and opens a PR.
- Expand language support by adding language-specific analyzers in `git_analysis.py`.

## Troubleshooting

- **No model found** – Ensure provider-specific LangChain packages are installed (`langchain-community`, `langchain-openai`, etc.).
- **Parsing errors** – Invalid or generated Python files may fail `ast` parsing; these are skipped with a warning.
- **Slow analyses** – Larger diffs benefit from local Ollama models or batching `LLM_TEMPERATURE=0`. Adjust severity thresholds to reduce LLM calls.

## License

MIT 


