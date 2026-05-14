# Milestones

## v1.3 Production Operations & Decision Intelligence (Shipped: 2026-05-14)

**Status:** shipped, audit completed with non-blocking tech debt
**Phases:** 22-28
**Requirements:** 37/37 active v1.3 requirements satisfied
**Verification:** 7/7 phases have verification and validation artifacts
**Integration:** 11/11 audit integration checks passing

### Delivered

- Static nginx production operation with admin runtime health, operator smoke evidence, and safer deploy/runbook flow.
- Dashboard drilldowns that preserve period, supplier, and mode context into stock, PO, COA, dispute, and reports.
- Backend service boundaries for dashboard, management reports, shared filters, and operational advisor calculations.
- Data quality monitor with rule-based issue detection, dashboard/report caveats, import-preview impact, and CSV export.
- Trend analytics and stock forecasting for dashboard, report UI, PDF, and Excel exports.
- AI advisor v3 with trend/data-quality source context, confidence, limitations, grouped recommendations, and deterministic fallback.
- Operator UI/UX polish with first-viewport quick actions, visible quality caveats, role-aware data-quality action, and Laporan hook cleanup.

### Stats

- 7 phases, 7 implementation summaries
- 37 requirements satisfied
- Focused backend tests passed in each phase; frontend build passing with documented legacy hook warnings
- Git range: `87d9c97` -> `97411f9`

### Archives

- [Roadmap archive](milestones/v1.3-ROADMAP.md)
- [Requirements archive](milestones/v1.3-REQUIREMENTS.md)
- [Milestone audit](milestones/v1.3-MILESTONE-AUDIT.md)
- [Phase archive index](milestones/v1.3-phases/INDEX.md)

### Deferred

- Legacy React hook warnings were closed in Phase 29 of v1.4.
- Nyquist validation metadata was backfilled or explicitly excepted in Phase 30 of v1.4.
- Browser screenshot automation was added in Phase 29 of v1.4.
- Full `ops/scripts/runtime_status.sh` should still be run on the real VPS after deployment.
- Data-quality scans and forecasts remain deterministic/rule-based; persisted snapshots or statistical prediction can be future phases.

---

## v1.2 Operational Reliability & Data Governance (Shipped: 2026-05-13)

**Status:** shipped, audit completed with non-blocking tech debt
**Phases:** 17-21
**Requirements:** 32/32 active v1.2 requirements satisfied
**Verification:** 5/5 phases have verification and validation artifacts
**Integration smoke:** 10/10 checks passing

### Delivered

- Automated backup scheduling, retention, history, restore validation, and backup health visibility.
- Made recurring combined COA workbook imports previewable, validated, traceable, and rollback-safe.
- Hardened deployment operations with service templates, env examples, deploy helper, smoke check, and production runbook.
- Rebuilt the dashboard first viewport around stock risk, arrival realization, dispute/umpire status, and supplier risk signals.
- Added management report v2, supplier scorecard, source-traceable exports, and a bounded AI advisor with Indonesian memo drafting.

### Stats

- 5 phases, 5 implementation summaries
- 30 non-planning source/doc files changed across the v1.2 git range
- 32 requirements satisfied
- 13 focused tests passing, frontend build passing, smoke check 10/10 passing
- Git range: `1b9f9ce` -> `38a31e7`

### Archives

- [Roadmap archive](milestones/v1.2-ROADMAP.md)
- [Requirements archive](milestones/v1.2-REQUIREMENTS.md)
- [Milestone audit](milestones/v1.2-MILESTONE-AUDIT.md)

### Deferred

- SUMMARY/VALIDATION GSD metadata backfill remains optional process cleanup.
- React hook dependency warnings remain documented in `docs/quality/REACT_HOOK_WARNINGS.md`.
- VPS production frontend should use nginx static build rather than dev `yarn start`.
- Optional LLM polish can be layered over the deterministic management report advisor later.

---

## v1.1 — Shipped 2026-05-12

**Status:** shipped, audit passed  
**Phases:** 1-16  
**Requirements:** 72/72 phase requirements satisfied  
**Verification:** 16/16 phases have verification and validation artifacts  
**Integration smoke:** 7/7 endpoints passing

### Delivered

- Stabilized production auth, docs, tests, and collection naming.
- Restored OpenRouter-backed AI, Smart Blending, and AI chat memory.
- Continued backend modularization and added cross-module filters.
- Upgraded dashboard, alerts, dispute/umpire workflow, import preview, audit logs, management reports, and contextual AI.

### Archives

- [Roadmap archive](milestones/v1.1-ROADMAP.md)
- [Requirements archive](milestones/v1.1-REQUIREMENTS.md)
- [Milestone audit](v1.1-MILESTONE-AUDIT.md)

### Deferred

- BACKUP2 scheduled backup automation remains backlog.
- React hook dependency warnings remain non-blocking cleanup.
- Focused pytest for later phases needs local test credential exports to avoid skips.
