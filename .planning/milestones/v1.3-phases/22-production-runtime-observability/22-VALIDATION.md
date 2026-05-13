---
phase: 22
slug: production-runtime-observability
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-13
---

# Phase 22 - Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Backend framework | pytest via `backend/pytest.ini` |
| Frontend framework | React build via `npm run build` |
| Ops scripts | Python compile and shell smoke execution |
| Quick run command | `python3 -m py_compile backend/services/runtime_status.py backend/routers/admin.py ops/scripts/smoke_check.py` |
| Focused backend command | `ops/scripts/pytest_with_local_credentials.sh tests/test_admin_runtime_status.py tests/test_admin_backup_restore.py -q` |
| Frontend command | `cd frontend && npm run build` |
| Smoke command | `ops/scripts/smoke_check.py --base-url http://127.0.0.1:8013 --frontend-url http://127.0.0.1:3013` |

## Sampling Rate

- After backend runtime endpoint task: run quick compile and focused runtime tests.
- After ops script task: run Python compile and script help/JSON-output checks.
- After frontend task: run `npm run build`.
- Before verification: run focused backend tests, frontend build, and smoke check when local services are running.

## Per-Task Verification Map

| Task ID | Requirement | Threat Ref | Test Type | Automated Command | Status |
|---------|-------------|------------|-----------|-------------------|--------|
| 22-01-01 | OPS3-03 | T22-01, T22-02 | backend integration | `ops/scripts/pytest_with_local_credentials.sh tests/test_admin_runtime_status.py -q` | pending |
| 22-01-02 | OPS3-02, OPS3-05 | T22-03 | script/compile | `python3 -m py_compile ops/scripts/smoke_check.py` | pending |
| 22-01-03 | OPS3-03 | T22-01 | frontend build | `cd frontend && npm run build` | pending |
| 22-01-04 | OPS3-01, OPS3-04 | T22-04 | docs/static check | `rg -n "static nginx|smoke evidence|runtime status" docs/operations ops/env ops/nginx` | pending |
| 22-01-05 | OPS3-01..05 | all | full sweep | focused tests + build + smoke check | pending |

## Wave 0 Requirements

- [ ] `backend/tests/test_admin_runtime_status.py` exists and covers response shape, admin auth, smoke-report persistence, and no secret-like fields.
- [ ] `backend/services/runtime_status.py` exists and isolates status collection from router logic.
- [ ] Runtime status endpoint does not execute shell commands.
- [ ] Smoke script can produce structured evidence.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real VPS static nginx cutover | OPS3-01 | Requires production host service files and nginx reload | Follow `docs/operations/PRODUCTION_RUNBOOK.md`, run deploy script, then smoke check using production URLs. |
| Visual layout at tablet width | OPS3-03 | Browser rendering is visual | Open `/settings` as admin and confirm status tiles do not overlap at desktop/tablet widths. |

## Validation Sign-Off

- [ ] All tasks have automated verification or explicit manual gate.
- [ ] No three consecutive implementation tasks without an automated check.
- [ ] Frontend build passes.
- [ ] Runtime endpoint does not leak secrets.
- [ ] Smoke evidence is persisted or written as JSON artifact.
- [ ] `nyquist_compliant: true` remains set in frontmatter.

**Approval:** pending
