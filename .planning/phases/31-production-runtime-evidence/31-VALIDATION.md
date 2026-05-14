---
phase: 31
requirements:
  - OPS4-01
  - OPS4-02
  - OPS4-03
  - OPS4-04
  - OPS4-05
nyquist_status: planned
validation_owner: codex
---

# Phase 31 Validation Plan

## Gates

| Requirement | Validation |
|-------------|------------|
| OPS4-01 | `runtime_status.sh` has syntax validation and writes/prints a runtime report artifact path. |
| OPS4-02 | Existing admin smoke report tests pass and runtime UI still displays latest smoke status. |
| OPS4-03 | Production runbook includes v1.4 gate commands, artifact paths, fallback steps, and retention policy. |
| OPS4-04 | Backend tests cover version metadata shape and frontend build metadata; frontend build validates runtime panel compile. |
| OPS4-05 | Phase verification explicitly records real VPS runtime execution as manual when unavailable locally. |

## Commands

```bash
bash -n ops/scripts/runtime_status.sh ops/scripts/deploy.sh
python3 -m py_compile ops/scripts/smoke_check.py
cd backend && pytest tests/test_admin_runtime_status.py
cd frontend && CI=true npm run build
git diff --check -- ops docs backend frontend .planning
```

## Results

| Command | Result |
|---------|--------|
| `bash -n ops/scripts/runtime_status.sh ops/scripts/deploy.sh` | Pending |
| `python3 -m py_compile ops/scripts/smoke_check.py` | Pending |
| `cd backend && pytest tests/test_admin_runtime_status.py` | Pending |
| `cd frontend && CI=true npm run build` | Pending |
| `git diff --check -- ops docs backend frontend .planning` | Pending |

## Residual Risks

- Real VPS command execution may remain manual if production access is unavailable in this development session.
- The static frontend build metadata is only as accurate as the release build process that writes `version.json`.
