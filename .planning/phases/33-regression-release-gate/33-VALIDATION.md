---
phase: 33
requirements:
  - REG4-01
  - REG4-02
  - REG4-03
  - REG4-04
nyquist_status: passed
validation_owner: codex
---

# Phase 33 Validation Plan

## Gates

| Requirement | Validation |
|-------------|------------|
| REG4-01 | `ops/scripts/release_gate.py` runs focused backend pytest groups for auth, dashboard, COA/import, reports, data quality, trends, advisor, runtime status, and rekap sorting. |
| REG4-02 | The same gate runs `npm run build:checked`, which runs the production build and compares hook warnings against `docs/quality/REACT_HOOK_WARNINGS.md`. |
| REG4-03 | The gate runs `ops/scripts/smoke_check.py` when backend health is reachable, or writes a skip reason when it is not. |
| REG4-04 | The gate writes JSON and Markdown artifacts with step results, warnings/skips, git SHA/tag, dirty status, and next action. |

## Commands

```bash
python3 -m py_compile ops/scripts/release_gate.py tests/test_release_gate.py backend/tests/conftest.py
python3 -m pytest tests/test_release_gate.py tests/test_repo_hygiene.py -q
bash scripts/check_credentials.sh
git diff --check -- .gitignore ops/scripts/release_gate.py tests/test_release_gate.py backend/tests/conftest.py docs/operations/PRODUCTION_RUNBOOK.md .planning/phases/33-regression-release-gate
TEST_ADMIN_EMAIL=... TEST_ADMIN_PASSWORD=... TEST_OPERATOR_EMAIL=... TEST_OPERATOR_PASSWORD=... TEST_VIEWER_EMAIL=... TEST_VIEWER_PASSWORD=... python3 ops/scripts/release_gate.py --base-url http://127.0.0.1:8013 --frontend-url http://127.0.0.1:3013 --timeout 1200
```

## Results

Validated on 2026-05-14:

| Command | Result |
|---------|--------|
| `python3 -m py_compile ops/scripts/release_gate.py tests/test_release_gate.py backend/tests/conftest.py` | Pass |
| `python3 -m pytest tests/test_release_gate.py tests/test_repo_hygiene.py -q` | Pass: 4 passed |
| `bash scripts/check_credentials.sh` | Pass |
| `git diff --check -- .gitignore ops/scripts/release_gate.py tests/test_release_gate.py backend/tests/conftest.py docs/operations/PRODUCTION_RUNBOOK.md .planning/phases/33-regression-release-gate` | Pass |
| `python3 ops/scripts/release_gate.py --base-url http://127.0.0.1:8013 --frontend-url http://127.0.0.1:3013 --timeout 1200` | Pass: repo hygiene, 6 backend groups, frontend build, and smoke check passed. Artifact: `ops/release-artifacts/release-gate-20260514T060356.json`. |

## Residual Risks

- The smoke check ran without `--record-smoke-status`, so auth-only smoke endpoints and admin runtime smoke persistence remain a production-operator gate when real smoke credentials are exported.
- Release artifacts are intentionally ignored and retained locally/operator-side, not committed to git.
