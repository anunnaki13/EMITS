# Phase 28 UI Spec - Operator UI/UX Polish

Date: 2026-05-14
Status: ready

## Dashboard Contract

First viewport order:

- Header and filters.
- Quick actions:
  - Stock Batubara
  - Jadwal PO
  - Dispute / Umpire
  - Report Manajemen
  - Data Quality
- Primary operational cards:
  - Monitoring Stock Batubara
  - Jadwal vs Realisasi
  - Dispute / Umpire
  - Risiko Supplier
- Data-quality caveat when applicable.
- Trend & Forecast.

## Report Contract

Management report tab should:

- Keep filters stable.
- Show trend/advisor sections without overlapping text.
- Show advisor confidence/limitations and grouped recommendations.
- Avoid extra click paths for memo/advisor review.

## States

Partial data:

- Show compact amber caveat in Indonesian.

Critical data quality:

- Show red/amber caveat with link to Data Quality Monitor.

Empty data:

- Keep existing Indonesian empty text.

Loading:

- Keep spinner/skeleton behavior.

## Visual Rules

- No hero sections.
- No decorative gradients or blobs.
- Cards and tiles must wrap cleanly on tablet.
- Long Indonesian text wraps inside tiles/rows.
- Do not introduce new UI dependencies.

