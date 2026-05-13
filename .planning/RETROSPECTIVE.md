# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

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

### Cumulative Quality

| Milestone | Tests | Coverage | Quality Gate |
|-----------|-------|----------|--------------|
| v1.1 | Integration smoke 7/7 | Production stabilization scope | Audit passed. |
| v1.2 | 13 focused tests + smoke 10/10 | 32/32 active requirements | Audit completed with non-blocking tech debt only. |

### Top Lessons

1. Keep production secrets and credentials out of committed artifacts even when test convenience suffers.
2. Archive milestone requirements immediately after close so future planning starts from a clean requirement set.
3. Every operationally risky data path should expose preview, traceability, and rollback evidence.
