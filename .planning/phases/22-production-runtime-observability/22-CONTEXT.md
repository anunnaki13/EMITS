# Phase 22: Production Runtime & Observability - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Source:** v1.3 roadmap and existing operations code review

## Phase Boundary

Phase 22 delivers production runtime visibility and deploy evidence for the single-host EMITS VPS. It does not change the domain workflows for fuel receipt, COA, reporting, or AI advice.

## Requirements

- OPS3-01: Serve the production frontend as a static nginx site with `/api` reverse proxy; real operation must not depend on `yarn start`.
- OPS3-02: Provide one deploy/status command that verifies backend, frontend static build, nginx, MongoDB, disk usage, latest backup, and app version.
- OPS3-03: Add an admin-visible runtime health surface in the app.
- OPS3-04: Update the production runbook for restart, rollback, nginx reload, smoke check, and failure triage.
- OPS3-05: Make post-deploy smoke evidence auditable as a report artifact or persisted status record.

## Decisions

- Keep the single-host VPS topology from v1.2: nginx serves the frontend and reverse-proxies `/api/*` to FastAPI on `127.0.0.1:8013`.
- Preserve all public `/api/*` contracts. New runtime endpoints belong under `/api/admin/*` and must require `admin`.
- Do not expose production secrets, raw environment values, JWT secrets, database URLs, or test credentials in runtime status.
- Do not execute shell commands from the web request path. Runtime status may inspect safe Python-level facts: DB ping, disk usage, backup health, version/build env values, and last persisted smoke result.
- `ops/scripts/smoke_check.py` is the canonical smoke runner. Extend it rather than adding a parallel checker.
- Settings is the existing admin-only page. Phase 22 may add a runtime health panel there or a small admin subpage, but it should not create a marketing-style dashboard.

## Existing Anchors

- `backend/server.py` exposes `/api/health` with a minimal healthy/timestamp response.
- `backend/routers/admin.py` already owns admin-only backup, restore, audit-log endpoints.
- `backend/services/backup_service.py` already computes backup health and backup history.
- `ops/scripts/deploy.sh` already builds the frontend, rsyncs `frontend/build/` to `/var/www/emits`, restarts backend, reloads nginx, and runs smoke check.
- `ops/scripts/smoke_check.py` already verifies frontend, backend health, MongoDB, auth, dashboard, COA, and management report.
- `docs/operations/PRODUCTION_RUNBOOK.md`, `ops/nginx/emits.conf.example`, `ops/systemd/emits-backend.service.example`, and `ops/env/*.example` already describe the static nginx deployment path.
- `frontend/src/pages/SettingsPage.js` already includes admin backup, restore, alert, audit, COA, AI, and user-management sections.

## Non-Goals

- No multi-host orchestration.
- No new managed cloud service.
- No secrets in committed docs or UI.
- No destructive cleanup of existing dirty local artifacts.
- No replacement of nginx/systemd with another runtime stack.

## Canonical References

- `.planning/REQUIREMENTS.md` - OPS3 requirements.
- `.planning/ROADMAP.md` - Phase 22 scope and success criteria.
- `.planning/decisions/ADR-006-api-prefix-and-frontend-base-url.md` - `/api/*` and frontend base URL contract.
- `docs/operations/PRODUCTION_RUNBOOK.md` - current deployment/runbook baseline.
- `ops/scripts/deploy.sh` - current deploy automation.
- `ops/scripts/smoke_check.py` - current smoke evidence source.
- `ops/nginx/emits.conf.example` - static frontend and reverse-proxy template.
- `backend/routers/admin.py` - admin-only endpoint ownership.
- `backend/services/backup_service.py` - backup health integration.
- `frontend/src/pages/SettingsPage.js` - admin UI insertion point.

---
*Phase: 22-production-runtime-observability*
*Context gathered: 2026-05-13*
