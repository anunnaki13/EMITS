---
phase: 09-backend-refactor-foundation
plan: 01
status: completed
completed_at: "2026-05-11T23:20:00+07:00"
requirements: [REFAC-01]
---

# 09-01 Summary — Admin Router Extraction

## Completed

- Added `backend/routers/admin.py`.
- Moved admin-only endpoints out of `server.py`:
  - `POST /api/admin/backup`
  - `GET /api/admin/audit-logs`
  - `POST /api/admin/restore`
- Moved backup collection inventory and restore payload validation into the admin router.
- Mounted `admin_router` under the existing `/api` router.
- Preserved the `/api/admin/*` URL contract and existing Indonesian error messages.

## Verification

Command run from `pltu-tenayan-full-backup/backend`:

```bash
./.venv/bin/python -m py_compile server.py routers/admin.py
TEST_ADMIN_EMAIL=<TEST_ADMIN_EMAIL> TEST_ADMIN_PASSWORD=<TEST_ADMIN_PASSWORD> AI_FAKE=1 ./.venv/bin/pytest tests/test_admin_backup_restore.py tests/test_admin_audit_logs.py -q
```

Result: `5 passed`.

## Notes

- Audit middleware remains in `server.py` for now because it is cross-cutting and needs to observe requests across multiple routers.
