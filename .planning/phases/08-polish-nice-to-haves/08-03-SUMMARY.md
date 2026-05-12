---
phase: 08-polish-nice-to-haves
plan: 03
status: completed
completed_at: "2026-05-11T21:41:24+07:00"
requirements: [POLISH-03]
---

# 08-03 Summary — Admin Backup / Restore Controls

## Completed

- Added admin-only `POST /api/admin/backup`.
- Added admin-only `POST /api/admin/restore`.
- Backup includes the 13 active collections documented in `DATABASE_SCHEMA.md`.
- Backup omits MongoDB `_id` fields so the JSON can be restored into a fresh install.
- Restore requires explicit confirmation string `RESTORE`.
- Restore validates schema version, rejects unknown collections, and rejects incomplete backups before writing.
- Restore supports `dry_run` validation for UI-side file checks.
- Added Settings page controls to download a JSON backup, choose a restore file, validate it, and perform restore only after typed confirmation.
- Added backend tests for backup shape, confirmation rejection, dry-run restore validation, and incomplete-backup rejection.

## Verification

- `TEST_ADMIN_EMAIL=<TEST_ADMIN_EMAIL> TEST_ADMIN_PASSWORD=<TEST_ADMIN_PASSWORD> AI_FAKE=1 ./.venv/bin/pytest tests/test_admin_backup_restore.py -q` passed: 4 tests.
- `yarn build` in `pltu-tenayan-full-backup/frontend` passed.
- Runtime backend restarted on port 8013 through tmux.
- `/api/health` returned 200.
- Runtime backup smoke returned schema version 1, 13 active collections, and 2304 total documents.

## Notes

- Actual destructive restore was not smoke-tested against the live runtime. The automated coverage uses dry-run validation to avoid rewriting active local data during verification.
