# Roadmap: EMITS

## Milestones

- **v1.3 Production Operations & Decision Intelligence** - shipped 2026-05-14. [Roadmap archive](milestones/v1.3-ROADMAP.md), [requirements archive](milestones/v1.3-REQUIREMENTS.md), [audit](milestones/v1.3-MILESTONE-AUDIT.md).
- **v1.2 Operational Reliability & Data Governance** - shipped 2026-05-13. [Roadmap archive](milestones/v1.2-ROADMAP.md), [requirements archive](milestones/v1.2-REQUIREMENTS.md), [audit](milestones/v1.2-MILESTONE-AUDIT.md).
- **v1.1 Production Stabilization & Operational Upgrades** - shipped 2026-05-12. [Roadmap archive](milestones/v1.1-ROADMAP.md), [requirements archive](milestones/v1.1-REQUIREMENTS.md), [audit](v1.1-MILESTONE-AUDIT.md).

## Current Status

v1.3 is shipped with accepted non-blocking tech debt. No active milestone is open; the next planning step is to define v1.4 requirements and roadmap.

## Completed Milestones

<details open>
<summary>v1.3 Production Operations & Decision Intelligence (Phases 22-28) - shipped 2026-05-14</summary>

- [x] Phase 22: Production Runtime & Observability - static nginx deployment path, runtime status, smoke evidence, and production runbook.
- [x] Phase 23: Dashboard Drilldown Integration - dashboard filters flow into stock, PO, COA, dispute, and report pages.
- [x] Phase 24: Backend Service Boundary Refactor - dashboard/report/advisor calculations moved into tested services.
- [x] Phase 25: Data Quality Monitor - stale, missing, duplicate, outlier, and inconsistent records are visible and exportable.
- [x] Phase 26: Trend Analytics & Forecasting - period comparisons, supplier trends, stock forecast, and export context.
- [x] Phase 27: AI Advisor v3 - trend/data-quality context, confidence, limitations, grouped recommendations, and deterministic fallback.
- [x] Phase 28: Operator UI/UX Polish - faster dashboard workflows, visible quality caveats, stable layouts, and Laporan hook cleanup.

Result: 37/37 v1.3 requirements satisfied. Audit status: `tech_debt` only.

</details>

<details>
<summary>v1.2 Operational Reliability & Data Governance (Phases 17-21) - shipped 2026-05-13</summary>

- [x] Phase 17: Backup & Disaster Recovery Automation.
- [x] Phase 18: COA Import Governance v2.
- [x] Phase 19: Production Deployment Hardening.
- [x] Phase 20: Dashboard Command Center v3.
- [x] Phase 21: Management Reports & AI Advisor v2.

</details>

<details>
<summary>v1.1 Production Stabilization & Operational Upgrades (Phases 1-16) - shipped 2026-05-12</summary>

See [v1.1 roadmap archive](milestones/v1.1-ROADMAP.md).

</details>

## Next Step

Start the next milestone:

```bash
$gsd-new-milestone
```
