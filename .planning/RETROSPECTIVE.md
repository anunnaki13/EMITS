# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.3 — Production Operations & Decision Intelligence

**Shipped:** 2026-05-14
**Phases:** 7 | **Implementation summaries:** 7 | **Sessions:** continued Codex/GSD execution

### What Was Built

- Static nginx production operation with admin runtime status, smoke evidence, deployment/runbook updates, and safe web-side status allowlisting.
- Real dashboard drilldowns into stock, PO, COA, dispute, and management report pages with preserved period/supplier/mode context.
- Backend service boundaries for dashboard, management reports, shared query filters, trend analytics, data quality, and advisor logic.
- Data quality monitor with issue detection, import-preview impact, report/dashboard caveats, UI surface, and CSV export.
- Trend analytics and deterministic stock forecasting in dashboard, management report, PDF, and Excel exports.
- AI advisor v3 with trend/data-quality context, confidence, limitations, grouped recommendations, owner roles, and optional LLM memo polish.
- Operator UI polish with first-viewport quick actions, role-aware data-quality link, visible caveats, stable card sizing, and Laporan hook cleanup.

### What Worked

- Layering data quality, trend analytics, and advisor improvements on top of shared report/dashboard services kept the payloads consistent.
- Focused backend tests were enough to protect response contracts while allowing incremental refactors.
- Keeping LLM polish optional preserved deterministic advisor behavior and avoided unsupported operational claims.

### What Was Inefficient

- React hook warnings remain in legacy page groups, so build output is still noisy despite being documented and reduced.
- Visual verification still relies on production build plus code review rather than screenshot automation.
- The GSD archive command created a useful base archive, but milestone docs still needed manual cleanup for local date, richer summaries, and current project wording.

### Patterns Established

- Management-facing analytics should carry data-quality caveats and confidence metadata rather than showing silent totals.
- Advisor output should group recommendations by urgency and owner while citing only source slices already visible in the report payload.
- Dashboard first-viewport actions should be role-aware when they link to role-restricted workflows.

### Key Lessons

1. Backend service boundaries made later features faster because data quality, trend analytics, and advisor v3 could share one report context.
2. For plant operations, honest caveats are as important as richer charts; sparse or suspicious data must be visible before recommendations.
3. Incremental frontend hook cleanup is safer than broad page refactors when pages close over auth, filters, pagination, and toast behavior.

### Cost Observations

- Model mix: not tracked precisely.
- Sessions: multiple continuation turns after Claude/GSD handoff.
- Notable: persistent `.planning` artifacts allowed Phase 26-28 and milestone audit to continue without losing context.

---

## Milestone: v1.2 — Operational Reliability & Data Governance

**Shipped:** 2026-05-13
**Phases:** 5 | **Implementation summaries:** 5 | **Sessions:** continued from Claude/GSD handoff into Codex

### What Was Built

- Backup automation with settings, retention, history, restore validation, and backup health visibility.
- COA combined workbook governance with preview, validation, diff/duplicate detection, import history, and rollback-safe behavior.
- Production deployment hardening with service templates, env examples, deploy helper, smoke script, and operations runbook.
- Dashboard command center v3 for stock risk, arrival realization, dispute/umpire status, supplier risk, filters, and drilldowns.
- Management report v2 and source-bound AI advisor with supplier scorecards, recommendations, and Indonesian memo drafting.

### What Worked

- Keeping v1.2 focused on operational safety produced features that directly reduce production risk.
- Shared report payloads kept management exports and AI recommendations aligned instead of creating separate data interpretations.
- Focused tests plus the smoke script gave a practical confidence gate without requiring a full end-to-end browser suite.

### What Was Inefficient

- Several phase artifacts were created as SUMMARY/VALIDATION/VERIFICATION only, so GSD's roadmap analyzer undercounted plans during milestone close.
- Existing React hook warnings still create noisy build output even though the production build passes and the warning register documents the intentional exclusions.
- Pre-existing local tracked dirt remains outside the milestone commits and should be cleaned in a dedicated repository hygiene pass if it starts blocking workflows.

### Patterns Established

- Source slices and data health metadata should accompany any management-facing analytics or AI response.
- Destructive data operations should use preview, explicit commit mode, history, and rollback snapshot as a standard pattern.
- Operations work should ship with a runbook and an executable smoke check in the same phase.

### Key Lessons

1. Treat audit output as the source of truth when analyzer metadata is incomplete, but record the mismatch as process debt.
2. For production plant software, reliability and reversibility features are usually higher leverage than adding more dashboard widgets.
3. Deterministic recommendations can be safer than LLM-first recommendations when the source data must remain auditable.

### Cost Observations

- Model mix: not tracked precisely across the Claude-to-Codex handoff.
- Sessions: multiple continuation turns.
- Notable: the workflow stayed effective because `.planning/STATE.md`, phase summaries, and audit artifacts preserved enough context to resume without restarting.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.1 | Multiple | 16 | Stabilized inherited production system and established ADR/test/doc baselines. |
| v1.2 | Multiple | 5 | Shifted from stabilization to operational reliability, data governance, and decision support. |
| v1.3 | Multiple | 7 | Shifted from reliability features to production operability, service boundaries, data quality, trends, and source-aware advisor workflows. |

### Cumulative Quality

| Milestone | Tests | Coverage | Quality Gate |
|-----------|-------|----------|--------------|
| v1.1 | Integration smoke 7/7 | Production stabilization scope | Audit passed. |
| v1.2 | 13 focused tests + smoke 10/10 | 32/32 active requirements | Audit completed with non-blocking tech debt only. |
| v1.3 | Focused backend tests per phase + frontend build | 37/37 active requirements | Audit completed with non-blocking tech debt only. |

### Top Lessons

1. Keep production secrets and credentials out of committed artifacts even when test convenience suffers.
2. Archive milestone requirements immediately after close so future planning starts from a clean requirement set.
3. Every operationally risky data path should expose preview, traceability, and rollback evidence.
4. Decision intelligence features need caveats, confidence, and source slices as first-class UI/API fields.
