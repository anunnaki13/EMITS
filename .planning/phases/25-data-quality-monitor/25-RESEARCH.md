# Phase 25 Research - Data Quality Monitor

Date: 2026-05-14
Status: complete

## Implementation Findings

### Existing Backend Patterns

`backend/routers/alerts.py` is the closest pattern for rule evaluation:

- rule config lives near the evaluator
- issue candidates have stable keys
- messages are Indonesian
- endpoint recomputes and returns a summary

`backend/routers/admin.py` is the closest pattern for export:

- query filters are mapped to Mongo query dictionaries
- CSV export uses `Response` with `text/csv`
- role gates use `require_role(["admin"])`

`backend/routers/planning_data.py` and `backend/services/coa_reconciliation.py` already produce import validation issues with `type`, `field`, `message`, and sometimes `severity`.

### Recommended Backend Shape

Add `backend/services/data_quality.py`:

- `build_data_quality_report(module="all", severity="all", limit=100)`
- `build_data_quality_export_rows(module="all", severity="all")`
- `summarize_import_quality(dataset, records, existing_issues)`
- `summarize_coa_preview_quality(preview)`

Add `backend/routers/data_quality.py`:

- `GET /api/data-quality/summary`
- `GET /api/data-quality/issues`
- `GET /api/data-quality/export`
- optional `POST /api/data-quality/recompute` if persistence/snapshot is needed during implementation

Include router in `backend/server.py`.

### Issue Shape

Recommended issue contract:

```json
{
  "key": "coa_reconciliation:coa_outlier_delta:LOT463",
  "module": "coa_reconciliation",
  "collection": "coa_reconciliation",
  "severity": "critical",
  "type": "coa_outlier_delta",
  "field": "delta_loading_internal",
  "source_record_id": "record-id",
  "source_label": "LOT 463",
  "source_path": "/coa-reconciliation",
  "message": "Delta COA shipment LOT 463 melewati ambang critical.",
  "suggested_fix": "Validasi nilai loading/internal dan lanjutkan dispute/umpire bila bukti lengkap.",
  "metadata": {}
}
```

Summary contract:

```json
{
  "status": "critical",
  "generated_at": "...",
  "counts": {"critical": 1, "warning": 2, "info": 0, "total": 3},
  "modules": [{"module": "coa_reconciliation", "critical": 1, "warning": 0, "total": 1}],
  "issues": [],
  "caveats": ["1 issue critical kualitas data perlu ditindaklanjuti sebelum laporan dipakai final."]
}
```

### Checks To Implement

Minimum checks for DQ3-01:

- stale module data: latest date older than threshold for stock, PO, arrivals, COA
- missing dates: date field absent/empty in key collections
- duplicate keys: shipment/PO/import identity duplicates
- negative/unrealistic numeric values: negative tonnage, impossible GCV, negative stock/pemakaian
- COA outlier delta: warning/critical threshold for reconciliation deltas

Suggested thresholds:

- stale stock/usage: latest date older than 7 days
- stale PO/arrival/COA: latest date older than 30 days
- GCV ARB: warning if outside 2500-6000
- tonnage/stock/pemakaian: critical if negative
- COA delta: warning >= 100, critical >= 150

### Frontend Shape

Add `frontend/src/pages/DataQualityPage.js`.

Use a dense operational layout:

- top severity summary cards
- filter row for module/severity
- issue table/list with stable height and wrap-safe text
- action buttons: refresh/recompute, export CSV
- Indonesian healthy/empty/error states

Add route `/data-quality` in `frontend/src/App.js` for admin/operator.
Add navigation item in `frontend/src/components/Layout.js` near operational/admin monitoring.

### Data Quality Caveats

Add a compact `data_quality` object to:

- `build_dashboard_operational(...)`
- `build_management_report(...)`

This should be additive, preserving current contracts.

### Import Flow Impact

PO/Merit import preview should return:

- `data_quality`: summary derived from preview issues and record checks

COA combined preview should include compatible quality summary from existing COA issues.

Do not block commit automatically in Phase 25 unless existing validation already rejects invalid data.

## Risks And Mitigations

- Broad scans can be slow on production collections.
  - Use projections, caps/limits for issue lists, and aggregation for duplicate keys.

- Over-strict thresholds can generate noisy warnings.
  - Keep thresholds explicit in `DATA_QUALITY_RULES` and include suggested fixes.

- Response contract changes can break frontend.
  - Additive `data_quality` fields only; existing tests continue to pass.

- Import preview paths differ between PO/Merit and COA workbook import.
  - Add helper functions and tests for both existing preview surfaces.
