# Phase 26 Research - Trend Analytics & Forecasting

Date: 2026-05-14
Status: complete

## Implementation Findings

### Backend Shape

The cleanest implementation is a new service module:

- `backend/services/trend_analytics.py`

The service should be consumed additively by:

- `build_dashboard_operational(...)` in `backend/services/dashboard_metrics.py`
- `build_management_report(...)` in `backend/services/management_reports.py`

Recommended public functions:

- `build_trend_analytics(period="all", supplier="all", mode="all", date_from=None, date_to=None)`
- `build_dashboard_trends(period="all", supplier="all", mode="all")`
- `build_management_trends(period="all", supplier="all", date_from=None, date_to=None)`

Use the service to avoid duplicating current-vs-previous calculations between dashboard and reports.

### Period Comparison Strategy

For a month period (`YYYY-MM`), compare to previous month.

For a year period (`YYYY`), compare to previous year.

For an explicit `date_from/date_to` range, compare to an immediately preceding range of the same number of days.

For `all`, use the latest 30-day window compared to the 30 days before it when dated data exists. If no dated data exists, return sparse state with Indonesian caveats.

### Metrics

Minimum trend metrics:

- Stock: current stock, total penerimaan, total pemakaian, average daily burn, coverage days.
- Arrivals: scheduled tonnage/count, realized tonnage/count, fulfillment rate, at-risk schedule.
- Supplier: realized volume, fulfillment/timeliness, average COA delta, active disputes.
- COA quality: average/max delta, critical count, warning count.
- Disputes: active umpire count and stale dispute count.

Each metric should include:

- `current`
- `previous`
- `delta`
- `delta_percent`
- `direction`
- `status`
- `label`

### Stock Forecast

Forecast should be deterministic:

- current stock from latest `smartstock.stock_akhir` fallback calculation
- burn assumption from selected period average daily usage, or recent 30-day usage fallback
- expected arrivals from upcoming `po_batubara.time_arrival`
- horizons: 7, 14, 30 days
- projected stock and coverage days

The payload must explain assumptions in Indonesian and flag low confidence when burn or expected-arrival data is sparse.

### Sparse Data Handling

Do not draw misleading conclusions when current or previous period has too few records.

Recommended shape:

```json
{
  "sparse_data": true,
  "confidence": "low",
  "caveats": [
    "Data historis periode pembanding belum cukup; tren ditampilkan sebagai indikasi awal."
  ]
}
```

Use source counts from stock, PO, arrivals, and COA records to decide confidence.

### Frontend Shape

Dashboard:

- add a compact "Trend & Forecast" section using `operationalStats.trend_analytics`
- show 3-5 compact cards: stock coverage forecast, arrival fulfillment movement, quality delta movement, dispute movement, supplier risk trend
- show caveat callout when sparse/low confidence

Management report:

- add trend summary rows/cards under existing management report summary
- add supplier trend table/cards using `managementReport.trend_analytics.supplier_trends`
- add stock forecast box

Exports:

- Excel: add `Trend Analytics`, `Supplier Trends`, and `Stock Forecast` sheets.
- PDF: add a trend/forecast section before source slices.
- Export data should use the same `managementReport` object currently displayed, so filter scope remains identical.

## Risks And Mitigations

- Circular import risk between `management_reports.py` and trend service.
  - Keep `trend_analytics.py` independent from management report builders and use low-level collection queries.

- Date field inconsistencies across arrivals.
  - Use the same field choices as existing dashboard/report functions, and keep any differences explicit.

- Forecast confidence can be overstated.
  - Include `confidence`, `sparse_data`, and `caveats`; do not hide missing burn/arrival assumptions.

- Existing exports can become too wide.
  - Add separate sheets for Excel and compact PDF tables instead of overloading existing sheets.

