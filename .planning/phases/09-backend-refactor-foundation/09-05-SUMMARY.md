# Phase 09 Plan 05 Summary: Backend Cleanup and Contract Tests

Completed: 2026-05-12

## Outcome

Plan 09-05 completed. Stale duplicate routers were removed, backend imports were cleaned, focused contract tests passed, and the remaining `server.py` ownership boundary is documented.

## Changes

- Removed stale duplicate router files:
  - `pltu-tenayan-full-backup/backend/routers/ai.py`
  - `pltu-tenayan-full-backup/backend/routers/data.py`
- Updated `pltu-tenayan-full-backup/backend/routers/__init__.py` so the package no longer exports removed router modules.
- Removed unused AI client and legacy utility imports from `pltu-tenayan-full-backup/backend/server.py`.

## Remaining `server.py` Boundary

After Phase 9, `server.py` still owns only the legacy core app shell plus the rekap receipt surface:

- FastAPI app setup, middleware, exception handlers, and audit middleware.
- Rekap CRUD endpoints for:
  - `/api/vessels`
  - `/api/barges`
  - `/api/trucking`
  - `/api/biomassa`
- Excel upload endpoints for:
  - `/api/upload/vessel`
  - `/api/upload/barge`
  - `/api/upload/trucking`
  - `/api/upload/biomassa`
- `/api/suppliers`
- `/api/`
- `/api/health`

Extracted router ownership now covers auth/users, admin backup/restore/audit logs, dashboard, COA, smart-stock/sumber-pemakaian, PO Batubara, Merit Order, AI intelligence, conversations, quick analysis, and Smart Blending.

## Verification

Backend compile and focused contract tests:

```bash
./.venv/bin/python -m py_compile server.py routers/*.py models/__init__.py
TEST_ADMIN_EMAIL=<TEST_ADMIN_EMAIL> TEST_ADMIN_PASSWORD=<TEST_ADMIN_PASSWORD> AI_FAKE=1 ./.venv/bin/pytest \
  tests/test_admin_backup_restore.py tests/test_admin_audit_logs.py \
  tests/test_dashboard_operational.py tests/test_dashboard_advanced.py \
  tests/test_po_batubara.py tests/test_merit_order.py \
  tests/test_ai_endpoints.py tests/test_ai_chat_endpoints.py tests/test_smart_blending_data.py \
  tests/test_rekap_filters.py tests/test_pagination_shape.py -q
```

Result: `77 passed, 1 skipped`.

Runtime smoke on port 8013:

- `/api/health`: 200
- `/api/auth/login`: 200
- `/api/admin/audit-logs`: 200
- `/api/dashboard/operational`: 200
- `/api/dashboard/stats`: 200
- `/api/dashboard/advanced`: 200
- `/api/po-batubara`: 200
- `/api/po-batubara/years`: 200
- `/api/merit-order`: 200
- `/api/merit-order/periods`: 200
- `/api/ai/quick/smart-stock`: 200
- `/api/ai/conversations`: 200

## Notes

The first contract-test run failed during server startup because `routers/__init__.py` still imported the removed stale modules. That package export was corrected and the focused suite then passed.
