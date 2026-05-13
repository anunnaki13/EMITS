---
phase: 22-production-runtime-observability
plan: 01
subsystem: production-operations
tags: [runtime-status, observability, nginx-static, smoke-evidence, admin-ui]
requires:
  - phase: 19-production-deployment-hardening
    provides: static nginx baseline, deploy script, smoke check baseline
provides:
  - admin-only runtime status API and smoke report persistence
  - operator runtime status command and JSON smoke evidence workflow
  - Settings page runtime health panel
  - updated production runbook and deployment guide
affects: [admin-settings, deploy, smoke-check, production-runbook, phase-23]
tech-stack:
  added: []
  patterns:
    - allowlisted runtime status service with no web-triggered shell commands
    - JSON smoke evidence written locally and optionally persisted through admin API
key-files:
  created:
    - backend/services/runtime_status.py
    - backend/tests/test_admin_runtime_status.py
    - ops/scripts/runtime_status.sh
    - frontend/src/components/RuntimeHealthPanel.js
  modified:
    - backend/routers/admin.py
    - ops/scripts/smoke_check.py
    - ops/scripts/deploy.sh
    - ops/env/backend.env.example
    - ops/env/frontend.env.example
    - ops/nginx/emits.conf.example
    - frontend/src/pages/SettingsPage.js
    - docs/operations/PRODUCTION_RUNBOOK.md
    - DEPLOYMENT_GUIDE.md
    - docs/quality/REACT_HOOK_WARNINGS.md
key-decisions:
  - "Keep shell/service checks in ops/scripts/runtime_status.sh; the web API only uses safe Python-level checks."
  - "Treat persisted smoke reports as operational evidence, not security authorization evidence."
  - "Place runtime health inside Settings as an extracted component to avoid expanding the monolithic page further."
patterns-established:
  - "Runtime status responses expose allowlisted fields only and omit Mongo `_id`."
  - "Deploy and runtime status scripts write timestamped smoke evidence JSON."
requirements-completed:
  - OPS3-01
  - OPS3-02
  - OPS3-03
  - OPS3-04
  - OPS3-05
duration: 38 min
completed: 2026-05-13
---

# Phase 22 Plan 01: Production Runtime & Observability Summary

**Static nginx production operation with admin runtime health, operator smoke evidence, and safer deploy/runbook flow**

## Performance

- **Duration:** 38 min
- **Started:** 2026-05-13T16:26:00+07:00
- **Completed:** 2026-05-13T17:04:22Z
- **Tasks:** 5
- **Files modified:** 18

## Accomplishments

- Added `GET /api/admin/runtime/status` and `POST /api/admin/runtime/smoke-report`, both admin-only and secret-safe.
- Extended smoke checks with JSON evidence and optional persistence, then wired deploy and `runtime_status.sh` to produce auditable artifacts.
- Added `Status Operasional` to admin Settings with backend, MongoDB, backup, smoke, and disk status.
- Updated production docs so static nginx, `/var/www/emits`, port `8013`, runtime status, smoke evidence, rollback, and triage are consistent.

## Task Commits

1. **Backend runtime status service, admin endpoints, and tests** - `3fddc1d`
2. **Smoke evidence and operator status command** - `0ddf098`
3. **Admin runtime health panel** - `aca9e40`
4. **Runbook, env templates, and static nginx cutover docs** - `f47fac8`

## Verification

- `python3 -m py_compile backend/services/runtime_status.py backend/routers/admin.py ops/scripts/smoke_check.py` - PASS
- `ops/scripts/pytest_with_local_credentials.sh tests/test_admin_runtime_status.py tests/test_admin_backup_restore.py -q` - PASS, 8 passed
- `bash -n ops/scripts/deploy.sh ops/scripts/runtime_status.sh` - PASS
- `ops/scripts/smoke_check.py --help | rg "json-output|record-status"` - PASS
- `cd frontend && npm run build` - PASS with documented legacy hook warnings only
- `rg -n "runtime status|smoke evidence|static nginx|nginx -t|rollback" docs/operations/PRODUCTION_RUNBOOK.md DEPLOYMENT_GUIDE.md ops/env ops/nginx` - PASS

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial runtime test assertion checked for substring `_id`, which incorrectly matched safe field `build_id`. The test now recursively checks actual Mongo `_id` keys instead.
- Real VPS nginx/systemd smoke execution was not run from this development environment; the runbook and `runtime_status.sh` provide the production follow-up command.

## User Setup Required

None for code. On the production host, set safe metadata placeholders in `backend/.env`: `APP_VERSION`, `APP_BUILD_ID`, `APP_ENV`, `FRONTEND_STATIC_ROOT`, and `SMOKE_EVIDENCE_DIR`.

## Next Phase Readiness

Phase 23 can use the improved production safety net before changing dashboard drilldown behavior. No active blocker for Phase 23 planning.

---
*Phase: 22-production-runtime-observability*
*Completed: 2026-05-13*
