# Phase 22 Patterns

**Phase:** 22 - Production Runtime & Observability
**Date:** 2026-05-13

## Backend Patterns

| Target | Existing Pattern | Notes |
|--------|------------------|-------|
| Admin-only runtime endpoints | `backend/routers/admin.py` uses `APIRouter(prefix="/admin")` and `Depends(require_role(["admin"]))` | Add runtime endpoints here to preserve `/api/admin/*` ownership. |
| DB access | `backend/utils/database.py` exposes `db` and `client` | Runtime status can ping `client.admin.command("ping")` and inspect collection count without exposing `MONGO_URL`. |
| Backup health | `backend/services/backup_service.py:get_backup_health` | Reuse for backup status instead of duplicating stale/healthy logic. |
| Response projection | Existing routers use Mongo projection `{"_id": 0}` | Runtime smoke reports must omit `_id`. |
| Indonesian errors | Admin and COA routers raise `HTTPException(..., detail="...")` with Indonesian copy | New errors should follow this style. |

## Ops Patterns

| Target | Existing Pattern | Notes |
|--------|------------------|-------|
| Smoke check | `ops/scripts/smoke_check.py` with `CheckResult` dataclass and line-by-line PASS/FAIL output | Extend structured output while preserving current CLI output. |
| Deploy flow | `ops/scripts/deploy.sh` | Add smoke evidence flags instead of creating a second deploy path. |
| Static frontend | `ops/nginx/emits.conf.example` and `docs/operations/PRODUCTION_RUNBOOK.md` | Keep nginx root `/var/www/emits` and `/api/` reverse proxy. |
| Env examples | `ops/env/backend.env.example`, `ops/env/frontend.env.example` | Add safe version/build/static-root vars; never add real secrets. |

## Frontend Patterns

| Target | Existing Pattern | Notes |
|--------|------------------|-------|
| Admin page | `frontend/src/pages/SettingsPage.js` | Existing admin route and section cards. Prefer extracted component for runtime panel. |
| Auth header | `useAuth().getAuthHeader()` | Runtime panel should use the same auth helper. |
| Toast/error behavior | Settings page uses `sonner` toast and console fallback for optional sections | Runtime panel can show inline error plus toast only for explicit refresh failures. |
| Icons | Existing page uses lucide-react | Use lucide icons, not custom SVG. |
| Dark cards | Existing Settings page uses `glass-card border-white/5 p-6` | Match style, but avoid nested cards. |

## Test Patterns

| Target | Existing Pattern | Notes |
|--------|------------------|-------|
| Admin integration tests | `backend/tests/test_admin_backup_restore.py` uses `base_url` and `admin_headers` | Add `test_admin_runtime_status.py` in same style. |
| Local credentials | `ops/scripts/pytest_with_local_credentials.sh` | Verification should use this helper for auth-backed focused tests. |
| Frontend build | Existing phases use `npm run build` | Keep as frontend gate. |

---
*Pattern mapping created inline from direct code inspection.*
