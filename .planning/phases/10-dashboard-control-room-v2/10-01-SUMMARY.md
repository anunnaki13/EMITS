# Phase 10 Plan 01 Summary: Dashboard Control Room v2

Completed: 2026-05-12

## Outcome

Dashboard upgraded into an operational control-room view focused on the three signals requested by the project owner:

- Monitoring stock batubara.
- Monitoring jadwal vs realisasi kedatangan bahan bakar.
- Monitoring dispute / umpire batubara.

## Backend Contract

Updated `GET /api/dashboard/operational` to expose decision-ready fields:

- `stock.status`
- `stock.label`
- `stock.reorder_risk`
- `stock.reorder_threshold_days`
- `arrivals.fulfillment_rate`
- `arrivals.tonnage_fulfillment_rate`
- `arrivals.at_risk_count`
- `arrivals.at_risk_schedule`
- `disputes.recent[].aging_days`

## Frontend

Updated `pltu-tenayan-full-backup/frontend/src/pages/Dashboard.js`:

- First viewport now prioritizes stock health, days of supply, reorder threshold, arrival fulfilment, at-risk schedule count, and active dispute/umpire priority.
- Added source drilldowns to Smart Stock, PO Batubara, Laporan, and Dispute Monitor, preserving selected period in the URL query.
- Reworked schedule table to show at-risk entries first.
- Added dispute aging display in the priority queue.

## Verification

Backend:

```bash
./.venv/bin/python -m py_compile routers/dashboard.py
TEST_ADMIN_EMAIL=<TEST_ADMIN_EMAIL> TEST_ADMIN_PASSWORD=<TEST_ADMIN_PASSWORD> AI_FAKE=1 ./.venv/bin/pytest tests/test_dashboard_operational.py tests/test_dashboard_advanced.py -q
```

Result: `14 passed`.

Frontend:

```bash
npm run build
```

Result: build succeeded. Existing unrelated `react-hooks/exhaustive-deps` warnings remain in multiple pages.

Runtime smoke on port 8013:

- `/api/health`: 200
- `/api/dashboard/operational`: 200
- New stock and arrival risk fields present in response.
