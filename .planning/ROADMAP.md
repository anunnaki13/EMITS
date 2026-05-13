# Roadmap: EMITS

## Milestones

- **v1.2 Operational Reliability & Data Governance** — Phases 17-21, shipped 2026-05-13. [Roadmap archive](milestones/v1.2-ROADMAP.md), [requirements archive](milestones/v1.2-REQUIREMENTS.md), [audit](milestones/v1.2-MILESTONE-AUDIT.md).
- **v1.1 Production Stabilization & Operational Upgrades** — Phases 1-16, shipped 2026-05-12. [Roadmap archive](milestones/v1.1-ROADMAP.md), [requirements archive](milestones/v1.1-REQUIREMENTS.md), [audit](v1.1-MILESTONE-AUDIT.md).

## Current Status

v1.2 is complete, archived, and audit-reviewed with `tech_debt` status only. No product requirement, integration, or E2E blocker remains open.

## Completed Phases

<details>
<summary>v1.2 Operational Reliability & Data Governance (Phases 17-21) — shipped 2026-05-13</summary>

- [x] Phase 17: Backup & Disaster Recovery Automation — scheduled backup settings, history, retention, restore validation, and backup health.
- [x] Phase 18: COA Import Governance v2 — combined workbook preview, validation, diff/duplicate detection, import history, and rollback-safe behavior.
- [x] Phase 19: Production Deployment Hardening — systemd/nginx/env templates, deploy helper, smoke check, runbook, and repository hygiene.
- [x] Phase 20: Dashboard Command Center v3 — stock risk, arrival realization, dispute/umpire, supplier risk, filters, and drilldowns.
- [x] Phase 21: Management Reports & AI Advisor v2 — source-traceable management report, supplier scorecard, exports, recommendations, and memo draft.

</details>

<details>
<summary>v1.1 Production Stabilization & Operational Upgrades (Phases 1-16) — shipped 2026-05-12</summary>

See [v1.1 roadmap archive](milestones/v1.1-ROADMAP.md).

</details>

## Next Step

Start the next milestone with fresh requirements:

```bash
$gsd-new-milestone
```
