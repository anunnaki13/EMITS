# Phase 22 Research: Production Runtime & Observability

**Phase:** 22 - Production Runtime & Observability
**Date:** 2026-05-13
**Question:** What needs to be known to plan static nginx operation, runtime status, smoke evidence, and admin visibility safely?

## Current Implementation Map

### Backend Health

- `backend/server.py` has a minimal `GET /api/health` endpoint returning `{"status": "healthy", "timestamp": ...}`.
- This is useful for external smoke checks but too shallow for admin runtime observability because it does not check MongoDB, backup health, smoke evidence, frontend build, disk, or version metadata.

### Admin Router

- `backend/routers/admin.py` owns `/api/admin/*` and uses `require_role(["admin"])`.
- Existing admin endpoints already expose backup settings/history and audit logs.
- Best fit for Phase 22:
  - `GET /api/admin/runtime/status`
  - `POST /api/admin/runtime/smoke-report`

### Backup Health

- `backend/services/backup_service.py` provides `get_backup_health(settings=None)` and returns status, stale flag, reason, latest success/event, interval, retention, and max backup values.
- Runtime status should reuse this instead of recomputing backup state.

### Smoke Check

- `ops/scripts/smoke_check.py` already verifies:
  - backend health
  - frontend HTML
  - MongoDB ping
  - auth login
  - auth rehydrate
  - dashboard stats
  - dashboard operational
  - COA list
  - COA KPIs
  - management report
- It currently prints pass/fail lines and exits 0/1. It does not persist JSON evidence.
- Best extension: collect structured results, print existing output for compatibility, optionally write JSON to a path, and optionally POST a smoke report back to the new admin endpoint using the login token it already obtains.

### Deploy Script

- `ops/scripts/deploy.sh` already:
  - checks clean tree
  - pulls source
  - runs mongodump
  - installs backend deps
  - builds frontend
  - rsyncs `frontend/build/` to `/var/www/emits`
  - restarts backend
  - reloads nginx
  - runs smoke check
- Phase 22 should harden this by making smoke evidence explicit and by documenting static frontend cutover status rather than changing deployment architecture.

### Frontend Admin UI

- `frontend/src/pages/SettingsPage.js` is admin-only through `App.js` and already includes backup health, backup history, audit logs, alert overview, COA settings, AI settings, and user management.
- It currently has a large monolithic structure and a documented hook warning. For Phase 22, a small extracted `RuntimeHealthPanel` component is preferable to making `SettingsPage.js` even larger.

## Recommended Runtime Status Shape

`GET /api/admin/runtime/status` should return a stable, non-secret JSON shape:

```json
{
  "status": "healthy|warning|critical",
  "generated_at": "ISO-8601",
  "version": {
    "app_version": "string|null",
    "build_id": "string|null",
    "environment": "production|development|unknown"
  },
  "backend": {
    "status": "healthy",
    "api_prefix": "/api",
    "process": "uvicorn"
  },
  "database": {
    "status": "healthy|critical",
    "name": "sanitized DB name",
    "collections": 14
  },
  "frontend": {
    "status": "unknown|healthy|warning",
    "static_root": "sanitized configured path",
    "build_present": true
  },
  "backup": {
    "status": "disabled|healthy|warning",
    "reason": "Indonesian text",
    "latest_success": {}
  },
  "smoke": {
    "status": "pass|fail|unknown",
    "finished_at": "ISO-8601|null",
    "passed": 10,
    "failed": 0,
    "results": []
  },
  "disk": {
    "status": "healthy|warning|critical",
    "total_bytes": 0,
    "used_bytes": 0,
    "free_bytes": 0,
    "used_percent": 0
  }
}
```

## Implementation Notes

- Keep shell/service checks out of backend request handling. Python can safely check DB ping, disk usage, backup health, and local build path existence. `systemctl` and `nginx -t` belong in `ops/scripts/runtime_status.sh`, not the web API.
- Store smoke evidence in MongoDB collection `runtime_smoke_reports` with projection `{"_id": 0}` on reads.
- The smoke-report POST endpoint must be admin-only. The smoke script can authenticate using the existing test/admin credentials and reuse the token.
- `smoke_check.py` should not print credentials or raw tokens. JSON evidence should include URLs at host level only, check names, ok flags, details, and timestamps.
- Version/build metadata can come from safe env vars such as `APP_VERSION`, `APP_BUILD_ID`, and `APP_ENV`; examples can be documented in `ops/env/backend.env.example`.
- Frontend status can use `REACT_APP_BUILD_ID` for display if available, and backend can report static root existence through env `FRONTEND_STATIC_ROOT`.

## UI Research

- The runtime panel should be operational and dense, not decorative.
- Place it near the top of Settings for admins because it answers "is the system healthy?" before configuration tasks.
- Use four compact status groups:
  - Runtime
  - Database
  - Backup
  - Smoke Check
- Show a disk usage progress bar only if values are available.
- Status colors:
  - healthy/pass: emerald
  - warning/unknown/disabled: amber or slate
  - critical/fail: red
- The UI must not show raw env values, file paths with secrets, Mongo URL, JWT secret, API keys, or token details.

## Validation Architecture

- Backend unit/integration:
  - Add `backend/tests/test_admin_runtime_status.py`.
  - Cover auth/role gate, response shape, DB status, backup health presence, smoke-report persistence, and no secret-looking fields.
- Script:
  - Run `python3 -m py_compile ops/scripts/smoke_check.py`.
  - Run smoke script with local backend and frontend when services are available.
  - Add `--json-output`/`--record-status` behavior tests only if cheap and not requiring live services.
- Frontend:
  - `npm run build` must pass.
  - Runtime panel should not introduce new hook warnings when practical. If warning remains, update `docs/quality/REACT_HOOK_WARNINGS.md` with explicit Phase 22 rationale.
- Docs:
  - Runbook must include static nginx cutover and smoke evidence path.

## Risks

| Risk | Mitigation |
|------|------------|
| Runtime endpoint leaks secrets | Return allowlisted fields only; never serialize env wholesale. |
| Web endpoint executes host commands | Keep `systemctl`, `nginx -t`, and shell checks in ops scripts only. |
| Smoke report can be spoofed | Admin-only POST; report is operational evidence, not an authorization primitive. |
| Static frontend base URL is wrong | Keep `REACT_APP_BACKEND_URL` guidance explicit in `ops/env/frontend.env.example` and runbook. |
| SettingsPage grows harder to maintain | Prefer extracted runtime panel component. |

## Planning Recommendation

Use one implementation plan with four waves:

1. Backend runtime status service and tests.
2. Smoke/status scripts and evidence persistence.
3. Admin UI runtime panel.
4. Runbook/env/docs and final verification.

---
*Research complete: 2026-05-13*
