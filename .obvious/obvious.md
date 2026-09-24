# obvious.md — Adjoshi06/driftguard

Documentation-drift detector for Python repos: analyzes git diffs, finds Python
symbol changes, cross-references docs, and uses an LLM (via LangChain) to grade
severity and suggest doc updates. CLI-first; exits 1 on critical findings.

## Stack

- **Language/runtime:** Python (developed against 3.13; any 3.10+ should work)
- **Key libraries:** GitPython (diffs), LangChain (+ langchain-openai/anthropic),
  python-dotenv, chromadb (declared; not yet wired up)
- **App type:** single CLI tool — no web server, no database, no background services
- **LLM:** optional at runtime. If the configured provider is unreachable, each
  issue falls back to heuristic severity/suggestion (see `drift_detector/llm.py`).

## Commands

```bash
# Setup (from repo root)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # edit LLM_* settings; all optional

# Primary flow — README quick start (run from repo root so the package imports)
.venv/bin/python -m drift_detector --since HEAD~1

# Compare arbitrary revisions / branches / other repos
.venv/bin/python -m drift_detector --from <ref> --to <ref>
.venv/bin/python -m drift_detector --branch <branch>
.venv/bin/python -m drift_detector --repo /path/to/other/repo --since HEAD~1

# JSON report saved to disk
.venv/bin/python -m drift_detector --since HEAD~1 --output-format json --save-report

# Analyzing a repo outside this checkout: put the package on PYTHONPATH
PYTHONPATH=<this repo> .venv/bin/python -m drift_detector --repo <target> --since HEAD~1
```

Notes:
- Run the module from the driftguard checkout (or set `PYTHONPATH`); `python -m
  drift_detector` is not installed as a package, there is no setup.py/pyproject.
- `drift_detector.py` at the repo root is the README-documented legacy entry
  point (`python drift_detector.py --since HEAD~1`) — same `run_cli`.

## Environment

`.env` (from `.env.example`) — all optional, safe defaults:
`LLM_PROVIDER` (default ollama), `LLM_MODEL`, `LLM_BASE_URL` (default
http://localhost:11434), `LLM_API_KEY`, `LLM_TEMPERATURE`,
`SEVERITY_THRESHOLD`, `AUTO_IGNORE_PRIVATE_FUNCTIONS`, `CHECK_EXAMPLES`,
`CHECK_INLINE_COMMENTS`, `OUTPUT_FORMAT`, `SAVE_REPORT`, `REPORT_PATH`.
No API key is required for local verification — LLM failures fall back to
heuristic output.

## Known dependency pins (important)

- `langchain-community<0.4` — the 0.4.x sunset release removed
  `ChatOllama`, which `drift_detector/llm.py` imports. 0.3.31 verified.

## Codebase map

Single Python package; ~1 top-level dir. Full table: see
[`.obvious/codebase-map.md`](codebase-map.md).

- `drift_detector.py` — legacy root entry point (delegates to `run_cli`)
- `drift_detector/cli.py` — argparse CLI, wires settings → detector → renderer
- `drift_detector/config.py` — dataclass settings loaded from env/`.env`
- `drift_detector/git_analysis.py` — GitPython diff parsing, Python `ast` extraction
- `drift_detector/doc_discovery.py` — indexes README/docs/examples for symbol references
- `drift_detector/drift_analysis.py` — heuristic drift rules + orchestration
- `drift_detector/llm.py` — LangChain provider factory + suggestion chain with fallback
- `drift_detector/models.py` — dataclasses/enums (DriftReport, DriftIssue, Severity…)
- `drift_detector/report.py` — terminal/JSON/HTML rendering + report saving

## Local verification

See `.obvious/skills/local-dev/SKILL.md` for the full validated procedure
(verified 2026-09-24). Quick checks:

1. `.venv/bin/python -m drift_detector --help` — exits 0, prints usage.
2. `.venv/bin/python -m drift_detector --since HEAD~1` — exits 0 on this repo.
3. End-to-end drift detection on a scratch repo — flags a new undocumented
   function as `missing_docstring` / medium. Scripted in the skill file.
4. `.venv/bin/python -m compileall drift_detector` — compiles clean.
   (No lint/typecheck/test config exists in the repo yet.)

## Local Verification Summary

| Check | Result |
|---|---|
| Deps install (requirements.txt, pinned) | pass |
| `--help` | pass (exit 0) |
| `--since HEAD~1` on this repo | pass (exit 0, report rendered) |
| JSON + `--save-report` | pass (report written to `drift_reports/`) |
| E2E drift detection on scratch repo | pass (`missing_docstring` detected) |
| `compileall` smoke check | pass |
| Lint / typecheck / unit tests | none exist in repo (nothing to run) |
| Exit-code contract (1 on critical) | pass (observed on unrunnable-module error path; critical-path exercised via threshold) |

## Sandbox snapshot

- **snapshotId:** `g3ehlavipu8w7rv2htb8:default`
- **capturedAt:** `2026-09-24T19:06:42Z`
- **state captured:** `.venv` with deps installed (incl. `langchain-community` 0.3.31
  pin), `.env` from example, branch `obvious/onboarding`.

## Onboarding fixes (this run)

Two minimal source fixes were required to make the README quick start run —
both are part of this setup PR:

1. `drift_detector/git_analysis.py` — GitPython does not populate
   `Diff.change_type` for diffs created with `create_patch=True`, so every
   modified file crashed with `AttributeError: 'NoneType' object has no attribute
   'upper'`. The fix infers change type from blob sides.
2. `requirements.txt` — upper-bounded `langchain-community<0.4` (0.4.x removed
   `ChatOllama`).
