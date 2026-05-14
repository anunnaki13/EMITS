# Phase 31 Patterns

## Runtime Status Service

- Keep API output secret-free and allowlisted.
- Prefer small helper functions in `backend/services/runtime_status.py`.
- Return `unknown` when production-only metadata cannot be read instead of failing the whole runtime status response.

## Admin API

- Keep admin runtime routes in `backend/routers/admin.py`.
- Pydantic request bodies sanitize inputs before persistence.
- Status endpoints return JSON objects without Mongo `_id`.

## Runtime UI

- Keep Settings runtime health inside `RuntimeHealthPanel`.
- Use existing `HealthTile`, `StatusBadge`, Indonesian copy, and compact dark operational styling.
- Avoid adding a new page for release metadata; the admin runtime panel is the existing surface.

## Operations Scripts

- Bash scripts use `set -euo pipefail` and environment-variable overrides.
- Defaults match `/opt/pltu-tenayan/app`, `/var/www/emits`, and `/var/log/emits`.
- Evidence paths are printed at the end so operators can paste paths into handoff notes without copying secrets.

## Documentation

- `docs/operations/PRODUCTION_RUNBOOK.md` remains the canonical deploy/restart/runtime runbook.
- Phase validation docs must identify local validation separately from manual VPS validation.
