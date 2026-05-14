# Phase 31 Research: Runtime Evidence

## Existing Runtime Surface

- Backend runtime service: `backend/services/runtime_status.py`
  - Builds `/api/admin/runtime/status`.
  - Uses allowlisted runtime facts: version env, database ping, static frontend presence, backup health, latest smoke report, and disk usage.
  - Persists smoke reports in `runtime_smoke_reports`.

- Admin runtime API: `backend/routers/admin.py`
  - `GET /api/admin/runtime/status`
  - `POST /api/admin/runtime/smoke-report`
  - Both require admin auth through `require_role(["admin"])`.

- Runtime UI: `frontend/src/components/RuntimeHealthPanel.js`
  - Fetches runtime status from Settings.
  - Shows aggregate status, version/build text, backend/database/backup/smoke/disk tiles, and latest smoke entries.

- Operations scripts:
  - `ops/scripts/runtime_status.sh` checks production host state and runs smoke check.
  - `ops/scripts/smoke_check.py` performs HTTP/Mongo/auth/API checks and writes JSON evidence.
  - `ops/scripts/deploy.sh` runs deploy and smoke check after build/restart.

## Gaps Against OPS4

- OPS4-01: `runtime_status.sh` prints useful output and writes smoke JSON, but it does not yet preserve the full command transcript as an auditable runtime report artifact.
- OPS4-02: smoke API recording exists and has backend tests; Phase 31 should preserve and document this contract while making the UI copy explicit.
- OPS4-03: production runbook needs exact v1.4 release gate commands, artifact paths, fallback steps, and evidence retention.
- OPS4-04: backend build metadata exists through env, but frontend static build metadata is not a first-class runtime field; the admin UI should distinguish backend build from static frontend build.
- OPS4-05: local development cannot silently mark real VPS verification as passed; validation must record a manual gate when the real VPS command was not executed.

## Implementation Direction

1. Make `runtime_status.sh` tee its full output to a timestamped report under a configurable runtime evidence directory.
2. Add static frontend version metadata support through a generated `version.json` served with the frontend build and read by backend runtime status.
3. Add git SHA fallback for backend runtime metadata when `APP_BUILD_ID` is not provided.
4. Update runtime UI to show backend and frontend release/build metadata separately.
5. Update tests and runbook so the behavior is mechanically checked locally and operationally checkable on the VPS.
