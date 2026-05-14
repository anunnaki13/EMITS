---
phase: 31
plan: 31-01
requirements:
  - OPS4-01
  - OPS4-02
  - OPS4-03
  - OPS4-04
  - OPS4-05
status: complete
completed_at: "2026-05-14T10:44:48+07:00"
---

# Plan 31-01 Summary

## Completed Work

- Added runtime report evidence output to `ops/scripts/runtime_status.sh`; the script now tees its full transcript to `RUNTIME_EVIDENCE_DIR` and prints both runtime report and smoke JSON paths.
- Updated `ops/scripts/deploy.sh` to generate static frontend `version.json` with app version, release tag, build id, git SHA, and build timestamp during deploy.
- Extended `backend/services/runtime_status.py` with backend git SHA fallback, backend/frontend version metadata, placeholder filtering, and frontend `version.json` parsing.
- Updated `RuntimeHealthPanel` to show backend and static frontend build identifiers separately in Settings runtime health.
- Updated production deployment/runbook docs with v1.4 release gate commands, artifact paths, fallback steps, evidence retention, and manual gate rules.
- Added backend test coverage for static frontend version metadata and expanded runtime status shape assertions.

## Validation

- `bash -n ops/scripts/runtime_status.sh ops/scripts/deploy.sh`: pass.
- `python3 -m py_compile backend/services/runtime_status.py ops/scripts/smoke_check.py scripts/check_planning_hygiene.py`: pass.
- `cd backend && .venv/bin/pytest tests/test_admin_runtime_status.py`: pass, 2 passed and 2 skipped for local-only admin credentials.
- `cd frontend && CI=true npm run build`: pass.
- `git diff --check -- ops docs backend frontend .planning DEPLOYMENT_GUIDE.md scripts/check_planning_hygiene.py`: pass.

## Residual Risks

- Real VPS runtime execution is intentionally documented as a manual release gate until an operator runs `ops/scripts/runtime_status.sh` on the production host.
- Frontend build metadata depends on the deploy path that writes `version.json`; manual frontend copies must preserve that file.
