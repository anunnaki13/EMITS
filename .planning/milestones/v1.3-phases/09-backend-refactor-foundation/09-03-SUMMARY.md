---
phase: 09-backend-refactor-foundation
plan: 03
status: completed
completed_at: "2026-05-11T23:56:43+07:00"
requirements: [REFAC-03]
---

# 09-03 Summary — PO Batubara / Merit Order Router Extraction

## Completed

- Added `backend/routers/planning_data.py`.
- Moved PO Batubara endpoints out of `server.py`:
  - `GET /api/po-batubara`
  - `GET /api/po-batubara/years`
  - `POST /api/po-batubara`
  - `GET /api/po-batubara/{po_id}`
  - `PUT /api/po-batubara/{po_id}`
  - `DELETE /api/po-batubara/{po_id}`
  - `DELETE /api/po-batubara`
  - `POST /api/upload/po-batubara`
- Moved Merit Order endpoints out of `server.py`:
  - `GET /api/merit-order`
  - `GET /api/merit-order/periods`
  - `POST /api/merit-order`
  - `GET /api/merit-order/{mo_id}`
  - `PUT /api/merit-order/{mo_id}`
  - `DELETE /api/merit-order/{mo_id}`
  - `DELETE /api/merit-order`
  - `POST /api/upload/merit-order`
- Mounted `planning_data_router` under the existing `/api` router.
- Preserved existing URL and response contracts.

## Verification

Command run from `pltu-tenayan-full-backup/backend`:

```bash
./.venv/bin/python -m py_compile server.py routers/planning_data.py
TEST_ADMIN_EMAIL=<TEST_ADMIN_EMAIL> TEST_ADMIN_PASSWORD=<TEST_ADMIN_PASSWORD> AI_FAKE=1 ./.venv/bin/pytest tests/test_po_batubara.py tests/test_merit_order.py -q
```

Result: `21 passed, 1 skipped`.

## Notes

- The skipped PO by-id test is data-dependent and skips when no PO item exists in the isolated test database.
- `server.py` is now 2520 lines after Phase 9 extractions.
