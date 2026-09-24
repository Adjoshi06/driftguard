---
name: local-dev
description: How to get driftguard running locally and verify the primary flow — validated during onboarding (2026-09-24).
---

# Local dev — driftguard

Python CLI only: no services to start, no migrations, no secrets required.
The LLM is optional — `drift_detector/llm.py` catches provider failures and
falls back to heuristic severity/suggestions, so everything below works offline.

## Setup (from repo root)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # all settings optional; defaults target local Ollama
```

Dependency gotcha (fixed in requirements.txt during onboarding):
`langchain-community` must stay `<0.4` — the 0.4.x sunset release removed
`ChatOllama`, which `drift_detector/llm.py` imports (0.3.31 verified).

## Start / run

```bash
# from the driftguard checkout — the package is not installed, it is path-imported
.venv/bin/python -m drift_detector --since HEAD~1
# or the README's legacy entry point:
.venv/bin/python drift_detector.py --since HEAD~1
```

No port parsing needed — CLI tool, nothing listens.

## Verify (primary flow, proven 2026-09-24)

```bash
# 1. help
.venv/bin/python -m drift_detector --help

# 2. self-scan (docs-only change → 0 issues, exit 0)
.venv/bin/python -m drift_detector --since HEAD~1

# 3. JSON report to disk
.venv/bin/python -m drift_detector --since HEAD~1 --output-format json --save-report

# 4. real drift detection on a scratch repo
rm -rf /tmp/drift-demo && mkdir -p /tmp/drift-demo && cd /tmp/drift-demo
git init -q && git config user.email d@demo.io && git config user.name demo
printf '# Demo\n\nUse `util.format_price` to format prices.\n' > README.md
git add -A && git commit -qm init
printf 'def format_price(cents, currency="USD"):\n    return f"{cents/100:.2f} {currency}"\n' > util.py
git add -A && git commit -qm 'add format_price'
PYTHONPATH=<driftguard checkout> <venv>/bin/python -m drift_detector \
  --repo /tmp/drift-demo --since HEAD~1 --output-format json
# Expected: JSON with 1 issue, drift_type "missing_docstring", severity medium
```

- Observed output: `{"summary": "1 issues detected, 1 medium", "issues": [{"drift_type":
  "missing_docstring", "severity": "medium", "file_path": "util.py", ...}]}` — the
  `metadata.provider` field shows `ChatOllama`, proving the fallback path ran.

## Source fix made during onboarding (required to run at all)

`drift_detector/git_analysis.py`: GitPython does not populate
`Diff.change_type` for diffs created with `create_patch=True` (verified on
3.1.62 with and without rename detection), so every modified file crashed in
`_map_change_type` with `AttributeError: 'NoneType' object has no attribute
'upper'`. Fix: when `change_type` is `None`, infer ADDED/REMOVED/MODIFIED from
which blobs (`a_blob`/`b_blob`) are present.

## Known limitations

- No lint/typecheck/test config exists — `python -m compileall drift_detector`
  is the smoke check.
- Analyze repos outside this checkout via `--repo` + `PYTHONPATH`.
- chromadb is in requirements but not yet wired into the code (README roadmap).
