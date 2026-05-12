# Roadmap: EMITS v1.2 — Operational Reliability & Data Governance

## Current Status

v1.1 is complete, audit-passed, and archived:

- [v1.1 Roadmap Archive](milestones/v1.1-ROADMAP.md)
- [v1.1 Requirements Archive](milestones/v1.1-REQUIREMENTS.md)
- [v1.1 Milestone Audit](v1.1-MILESTONE-AUDIT.md)

v1.2 continues phase numbering from v1.1. The milestone prioritizes production safety, data governance, and operator decision quality.

## Milestone Goal

Make EMITS safer to operate as production software by automating backups, hardening deployment, making COA data imports reversible/validated, and polishing the control-room experience.

## Planned Phases

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 17 | Backup & Disaster Recovery Automation | Scheduled backups, retention, backup health, and restore validation are available to admins. | BACKUP2-01..05 | 5 |
| 18 | COA Import Governance v2 | Combined COA workbook imports become previewable, validated, traceable, and rollback-safe. | COAIMP-01..06 | 5 |
| 19 | Production Deployment Hardening | Running/deploying EMITS is repeatable, documented, and cleanly separated from local artifacts/secrets. | DEPLOY-01..05, CLEANUP-02..03 | 5 |
| 20 | Dashboard Command Center v3 | Operators get a sharper first screen for stock risk, arrivals, disputes, supplier risk, and drilldowns. | DASH3-01..05, CLEANUP-01 | 5 |
| 21 | Management Reports & AI Advisor v2 | Management summaries, supplier scorecards, and source-backed AI recommendations support decisions. | REPORT2-01..04, AI2-01..04 | 5 |

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| 17 | Complete | Backup scheduler/settings/history/health shipped. |
| 18 | Next | COA import preview/diff/history/rollback safeguards. |
| 19 | Planned | Deployment hardening and repo/test hygiene. |
| 20 | Planned | Dashboard v3 and React hook cleanup. |
| 21 | Planned | Reports v2 and AI advisor v2. |

## Phase Details

### Phase 17: Backup & Disaster Recovery Automation

**Goal:** Admins can rely on scheduled backups and know whether the latest recoverable backup is healthy.

**Requirements:** BACKUP2-01, BACKUP2-02, BACKUP2-03, BACKUP2-04, BACKUP2-05

**Success criteria:**
1. Admin can configure backup schedule and retention from settings or a documented admin command.
2. Backup execution writes history with status, size, duration, collection counts, and error details.
3. Retention pruning cannot delete the latest successful backup.
4. Restore validation reports schema/count issues before any restore writes data.
5. UI/API exposes backup health so stale or failed backups are visible.

### Phase 18: COA Import Governance v2

**Goal:** The new combined COA workbook flow becomes safe for recurring monthly updates, not only one-off replacement.

**Requirements:** COAIMP-01, COAIMP-02, COAIMP-03, COAIMP-04, COAIMP-05, COAIMP-06

**Success criteria:**
1. Admin/operator can preview a combined workbook without mutating `coa_reconciliation`.
2. Preview reports parsed counts, date range, validation issues, duplicates, and source coverage.
3. Preview shows before/after diff against existing shipments.
4. Commit requires explicit mode selection and confirmation for replace-all behavior.
5. Import history captures actor, filename, timestamp, counts, mode, validation summary, and preservation/overwrite notes.

### Phase 19: Production Deployment Hardening

**Goal:** Deployment and runtime operations are reproducible, observable, and not dependent on ad hoc shell memory.

**Requirements:** DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05, CLEANUP-02, CLEANUP-03

**Success criteria:**
1. Backend/frontend service definitions or equivalent deployment scripts are documented and tested.
2. Production env handling is represented by examples/runbooks without committing secrets.
3. One smoke command/checklist verifies frontend, backend health, MongoDB, auth, dashboard, COA, and reports.
4. Rollback path is documented for both code deploy and data import mistakes.
5. Repository hygiene is explicit: local-only artifacts are ignored, documented, or removed from the working tree.

### Phase 20: Dashboard Command Center v3

**Goal:** The dashboard becomes the actual first screen for operators to understand stock risk, arrivals, and disputes quickly.

**Requirements:** DASH3-01, DASH3-02, DASH3-03, DASH3-04, DASH3-05, CLEANUP-01

**Success criteria:**
1. First viewport prioritizes stock risk, burn/coverage, arrival realization, and COA dispute status.
2. Period/supplier/mode filters work consistently and preserve existing module navigation.
3. Cards drill down into filtered stock, arrivals, COA, dispute, and report views.
4. Supplier risk signals combine quality delta, timeliness, and active dispute state.
5. Frontend build remains clean or intentionally documented for hook dependency exceptions.

### Phase 21: Management Reports & AI Advisor v2

**Goal:** Management can generate actionable monthly summaries and AI can explain/recommend using bounded source context.

**Requirements:** REPORT2-01, REPORT2-02, REPORT2-03, REPORT2-04, AI2-01, AI2-02, AI2-03, AI2-04

**Success criteria:**
1. Monthly report summarizes stock, arrivals, supplier performance, COA quality, disputes, and potential loss.
2. Supplier scorecard ranks volume, timeliness, COA delta, dispute count, and risk.
3. PDF/Excel exports match on-screen filters and include source-count traceability.
4. AI recommendations cite source slices and refuse unsupported claims when data is missing.
5. AI can draft Indonesian management memo text from the current report context.

## Requirement Coverage

| Requirement Group | Covered By | Status |
|-------------------|------------|--------|
| BACKUP2-01..05 | Phase 17 | Planned |
| COAIMP-01..06 | Phase 18 | Planned |
| DEPLOY-01..05 | Phase 19 | Planned |
| CLEANUP-02..03 | Phase 19 | Planned |
| DASH3-01..05 | Phase 20 | Planned |
| CLEANUP-01 | Phase 20 | Planned |
| REPORT2-01..04 | Phase 21 | Planned |
| AI2-01..04 | Phase 21 | Planned |

Coverage: 32/32 active v1.2 requirements mapped.

## Next Step

Start execution with Phase 17:

```bash
$gsd-discuss-phase 17
```

or skip discussion and plan directly:

```bash
$gsd-plan-phase 17
```
