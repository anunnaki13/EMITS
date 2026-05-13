# 08-01 Summary — Operational Dashboard Redesign

Completed: 2026-05-11

## Outcome

Dashboard is now oriented around operational monitoring instead of generic chart ordering.

The first viewport prioritizes:

- Monitoring stock batubara.
- Jadwal vs realisasi kedatangan bahan bakar.
- Dispute / umpire batubara.

## Backend Changes

- Added additive endpoint: `GET /api/dashboard/operational?period=...`
- Response sections:
  - `stock`
  - `arrivals`
  - `disputes`
  - `available_periods`
- Existing `/api/dashboard/stats` and `/api/dashboard/advanced` were preserved.
- Added regression tests in `backend/tests/test_dashboard_operational.py`.

## Frontend Changes

- Updated `frontend/src/pages/Dashboard.js`.
- Added dashboard period filter.
- Added first-viewport operational modules:
  - Stock Batubara KPI panel.
  - Jadwal vs Realisasi Kedatangan panel.
  - Dispute / Umpire panel.
  - Jadwal Kedatangan Terdekat table when data exists.
- Existing supporting charts remain below the operational modules.

## Verification

Commands run:

```bash
cd pltu-tenayan-full-backup/backend
TEST_ADMIN_EMAIL="$(awk '/^- Email:/{print $3; exit}' ../memory/test_credentials.md)" \
TEST_ADMIN_PASSWORD="$(awk '/^- Password:/{print $3; exit}' ../memory/test_credentials.md)" \
AI_FAKE=1 ./.venv/bin/pytest tests/test_dashboard_operational.py tests/test_dashboard_advanced.py -q
```

Result: `14 passed`.

```bash
cd pltu-tenayan-full-backup/frontend
yarn build
```

Result: passed with existing React hook dependency warnings.

Runtime:

- Backend restarted on port `8013`, PID `139953`.
- `/api/health` returned HTTP 200.
- `GET /api/dashboard/operational?period=all` returned HTTP 200 with `stock`, `arrivals`, and `disputes` sections.

## Residual Notes

- Theme toggle, backup/restore, and audit trail remain for 08-02 through 08-04.
