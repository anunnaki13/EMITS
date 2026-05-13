# Phase 13 Plan 01 Summary: Excel Import Preview & Validation

Completed: 2026-05-12

## Outcome

Excel import for PO Batubara and Merit Order now supports preview, validation, duplicate detection, commit modes, and import history.

## Backend

Added endpoints:

- `POST /api/import-preview/{dataset}`
- `POST /api/import-preview/{preview_id}/commit`
- `GET /api/import-history`

Supported datasets:

- `po-batubara`
- `merit-order`

Preview behavior:

- Parses Excel into records without writing target data.
- Reports required-column issues.
- Reports duplicate rows inside the uploaded file.
- Reports possible duplicates against existing database records.
- Stores preview payload in `import_previews`.

Commit modes:

- `append`: insert all parsed rows.
- `replace`: delete all target rows and insert parsed rows.
- `merge`: upsert by dataset key.

Commit writes `import_history` with filename, mode, row count, issue count, inserted/updated/deleted counts, actor, and timestamp.

Existing upload endpoints still work and now share the same parser helpers:

- `POST /api/upload/po-batubara`
- `POST /api/upload/merit-order`

## Frontend

Updated:

- `POBatubaraPage.js`
- `MeritOrderPage.js`

Upload dialogs now:

- Preview the file first.
- Show row count and issue count.
- Show sample parsed rows.
- Let admin/operator choose `append`, `merge`, or `replace`.
- Block commit while preview has issues.

## Verification

Backend:

```bash
./.venv/bin/python -m py_compile routers/planning_data.py
TEST_ADMIN_EMAIL=<TEST_ADMIN_EMAIL> TEST_ADMIN_PASSWORD=<TEST_ADMIN_PASSWORD> AI_FAKE=1 ./.venv/bin/pytest \
  tests/test_import_preview.py tests/test_po_batubara.py tests/test_merit_order.py -q
```

Result: `23 passed, 1 skipped`.

Frontend:

```bash
npm run build
```

Result: build succeeded. Existing unrelated `react-hooks/exhaustive-deps` warnings remain.

Runtime smoke on port 8013:

- `/api/health`: 200
- `/api/import-history?page_size=5`: 200
