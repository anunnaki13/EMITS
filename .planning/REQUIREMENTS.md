# Requirements: EMITS v1.2 — Operational Reliability & Data Governance

v1.1 requirements are complete and archived in:

- [v1.1 Requirements Archive](milestones/v1.1-REQUIREMENTS.md)
- [v1.1 Milestone Audit](v1.1-MILESTONE-AUDIT.md)

## Milestone Goal

Make EMITS safer to operate as production software by automating backups, hardening deployment, making COA data imports reversible/validated, and polishing the control-room experience.

## Active Requirements

### Backup Automation (BACKUP2)

- [x] **BACKUP2-01**: Admin can configure scheduled database/application backups without manual button clicks.
- [x] **BACKUP2-02**: Admin can view backup history with last success, file size, collection counts, duration, and failure reason.
- [x] **BACKUP2-03**: Admin can configure a retention policy and old backups are pruned safely without deleting the latest successful backup.
- [x] **BACKUP2-04**: Admin can run restore validation before restore writes any production data.
- [x] **BACKUP2-05**: Dashboard/settings surfaces show backup health status so stale or failed backups are visible.

### COA Import Governance (COAIMP)

- [x] **COAIMP-01**: Admin/operator can upload one combined COA workbook and preview parsed records before committing.
- [x] **COAIMP-02**: Preview shows record counts, date range, source coverage, critical/warning deltas, and row-level validation issues.
- [x] **COAIMP-03**: Preview detects duplicate shipments and differences against existing `coa_reconciliation` records.
- [x] **COAIMP-04**: Commit supports explicit modes for replace-all and merge/update, with clear confirmation copy for destructive operations.
- [x] **COAIMP-05**: Import history records filename, actor, timestamp, counts, mode, validation summary, and before/after totals.
- [x] **COAIMP-06**: Existing dispute/umpire workflow notes and attachments are preserved or explicitly reported when an import would overwrite them.

### Deployment Hardening (DEPLOY)

- [x] **DEPLOY-01**: Backend and frontend are managed by repeatable service definitions with restart policy and log locations documented.
- [x] **DEPLOY-02**: Production environment variables and secrets are documented through examples/runbooks without committing real secrets.
- [x] **DEPLOY-03**: Operator can run one documented smoke check covering frontend, backend health, MongoDB, auth, dashboard, COA, and reports.
- [x] **DEPLOY-04**: Deployment runbook includes backup-before-deploy, build, restart, rollback, and post-deploy verification steps.
- [x] **DEPLOY-05**: Repository root, generated artifacts, ignored local files, and deployable source boundaries are explicit and clean.

### Dashboard Command Center v3 (DASH3)

- [ ] **DASH3-01**: Dashboard first viewport prioritizes stock risk, burn/coverage estimate, arrival schedule vs realization, and dispute/umpire status.
- [ ] **DASH3-02**: Operator can filter dashboard by period, supplier, and mode without breaking existing module pages.
- [ ] **DASH3-03**: Dashboard cards link to filtered drilldowns for stock, arrivals, COA reconciliation, dispute monitor, and reports.
- [ ] **DASH3-04**: Dashboard highlights supplier quality/risk signals using COA delta, shipment timeliness, and active disputes.
- [ ] **DASH3-05**: Dashboard layout remains readable on common desktop and tablet widths with no overlapping text or controls.

### Management Reports v2 (REPORT2)

- [ ] **REPORT2-01**: Management report can generate a monthly executive summary with stock, arrivals, supplier performance, COA quality, disputes, and potential loss.
- [ ] **REPORT2-02**: Supplier scorecard ranks suppliers by volume, timeliness, COA delta, dispute count, and risk status.
- [ ] **REPORT2-03**: PDF and Excel exports include the same filter scope and source-count traceability shown on screen.
- [ ] **REPORT2-04**: Report generation handles empty/partial data periods with clear Indonesian copy instead of broken charts or blank exports.

### AI Advisor v2 (AI2)

- [ ] **AI2-01**: AI answers for operational analysis include bounded source context and visible source slice labels.
- [ ] **AI2-02**: AI can recommend next actions for low stock, delayed arrivals, high COA delta, and stale disputes.
- [ ] **AI2-03**: AI can draft an Indonesian management memo from the current filtered report context.
- [ ] **AI2-04**: AI guardrails prevent unsupported claims when required source data is missing.

### Engineering Cleanup (CLEANUP)

- [ ] **CLEANUP-01**: Existing React `react-hooks/exhaustive-deps` warnings are resolved or documented with intentional exclusions.
- [x] **CLEANUP-02**: Focused pytest runs load local test admin credentials consistently without exposing secrets in committed files.
- [x] **CLEANUP-03**: Local-only artifacts (`.env`, generated folders, runtime metadata) are either ignored, documented, or cleaned from the working tree.

## Future Requirements

- Multi-plant support and tenant separation.
- Multi-provider LLM abstraction beyond the current Gemini/OpenRouter path.
- Realtime websocket collaboration.
- Mobile-native application.
- Advanced forecasting models beyond rule-based burn/arrival/stock projections.

## Out of Scope

- Replacing MongoDB, FastAPI, or React.
- Storing production secrets or test credentials in committed docs.
- Force-pushing or rewriting GitHub history to clean local-only artifacts.
- Changing existing role names (`admin`, `operator`, `viewer`) unless a future security milestone explicitly scopes it.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BACKUP2-01..05 | Phase 17 | Complete |
| COAIMP-01..06 | Phase 18 | Complete |
| DEPLOY-01..05 | Phase 19 | Complete |
| CLEANUP-02..03 | Phase 19 | Complete |
| DASH3-01..05 | Phase 20 | Planned |
| CLEANUP-01 | Phase 20 | Planned |
| REPORT2-01..04 | Phase 21 | Planned |
| AI2-01..04 | Phase 21 | Planned |
