---
phase: 33
plan: 33-01
requirements:
  - REG4-01
  - REG4-02
  - REG4-03
  - REG4-04
status: complete
completed_at: "2026-05-14T13:07:42+07:00"
---

# Plan 33-01 Summary

## Completed Work

- Added `ops/scripts/release_gate.py`, a one-command local release gate for
  repo hygiene, focused backend regressions, frontend warning-budget build, and
  smoke evidence.
- Grouped backend pytest execution sequentially so each group owns the isolated
  test backend lifecycle on port 18013 without cross-process collision.
- Added release artifacts under ignored `ops/release-artifacts/`, with JSON and
  Markdown summaries containing git metadata, step statuses, warnings/skips, and
  next action.
- Updated test seeding so admin, operator, and viewer users are registered in
  the isolated test DB when credentials are available, allowing role regression
  tests to run in the release gate.
- Updated the production runbook to call the new release gate before deploy and
  runtime evidence commands.
- Added unit tests for release-gate helper behavior and secret redaction.

## Validation

- `python3 -m py_compile ops/scripts/release_gate.py tests/test_release_gate.py backend/tests/conftest.py`: pass.
- `python3 -m pytest tests/test_release_gate.py tests/test_repo_hygiene.py -q`: pass, 4 passed.
- `bash scripts/check_credentials.sh`: pass.
- `git diff --check -- .gitignore ops/scripts/release_gate.py tests/test_release_gate.py backend/tests/conftest.py docs/operations/PRODUCTION_RUNBOOK.md .planning/phases/33-regression-release-gate`: pass.
- `python3 ops/scripts/release_gate.py --base-url http://127.0.0.1:8013 --frontend-url http://127.0.0.1:3013 --timeout 1200`: pass.

Release gate step results:

| Step | Result |
|------|--------|
| repo_hygiene | passed |
| backend_auth | passed |
| backend_dashboard | passed |
| backend_coa_import | passed |
| backend_reports_quality | passed |
| backend_trends_advisor | passed |
| backend_runtime_rekap | passed |
| frontend_build_checked | passed |
| smoke_check | passed |

Artifact paths:

- `ops/release-artifacts/release-gate-20260514T060356.json`
- `ops/release-artifacts/release-gate-20260514T060356.md`
- `ops/release-artifacts/smoke-20260514T060648Z.json`

## Residual Risks

- Smoke status was not recorded through `/api/admin/runtime/smoke-report`
  because the gate was run without `--record-smoke-status`; operators should use
  that flag when real smoke credentials are available in their shell.
- Release artifacts are ignored by git and should be retained on the host or
  attached to release notes by the operator.
