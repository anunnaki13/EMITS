# Requirements: EMITS v1.3 - Production Operations & Decision Intelligence

**Defined:** 2026-05-13
**Core Value:** Operators and admins at PLTU Tenayan can trust EMITS as the single source of truth for fuel-receipt data, COA reconciliation, and AI-assisted decision support.

v1.2 requirements are complete and archived in:

- [v1.2 Requirements Archive](milestones/v1.2-REQUIREMENTS.md)
- [v1.2 Milestone Audit](milestones/v1.2-MILESTONE-AUDIT.md)

## Milestone Goal

Move EMITS from feature-complete enough toward a more operable, maintainable, decision-oriented production system: static nginx deployment, real drilldowns, cleaner backend service boundaries, data quality monitoring, trend analytics, safer AI advice, and stronger operator UI polish.

## Active Requirements

### Production Runtime & Observability (OPS3)

- [x] **OPS3-01**: Production frontend can be built and served as a static nginx site with `/api` reverse proxy; real operation no longer depends on `yarn start`.
- [x] **OPS3-02**: Operator can run one deploy/status command that verifies backend, frontend static build, nginx, MongoDB, disk usage, latest backup, and app version.
- [x] **OPS3-03**: Admin can view runtime health in the app, including backend status, DB connectivity, latest backup, latest smoke result, and build/version metadata.
- [x] **OPS3-04**: Production runbook covers restart, rollback, nginx reload, smoke check, and failure triage using current service paths.
- [x] **OPS3-05**: Post-deploy smoke check writes auditable evidence as a report artifact or persisted status record.

### Dashboard Drilldowns (DRILL3)

- [x] **DRILL3-01**: Dashboard query filters for period, supplier, mode, and status are consumed by destination pages instead of only being passed in URLs.
- [x] **DRILL3-02**: Stock, arrivals/PO, COA, dispute, and report pages show active filter chips and clear reset actions when opened from dashboard cards.
- [x] **DRILL3-03**: Drilldown pages show clear Indonesian empty/partial-data states when filters return sparse results.
- [x] **DRILL3-04**: Dashboard drilldowns preserve navigation context so users can return to the originating filtered dashboard state.
- [x] **DRILL3-05**: Tests cover representative dashboard-to-destination drilldowns and filtered API payloads.

### Backend Refactor & Service Boundaries (REF3)

- [x] **REF3-01**: Shared dashboard, report, and AI advisor calculations move into service-layer functions with explicit inputs and outputs.
- [x] **REF3-02**: Duplicate date, number, period, supplier, and mode normalization helpers are consolidated and tested.
- [x] **REF3-03**: Router handlers stay thin: auth/role gate, request validation, service call, and response mapping.
- [x] **REF3-04**: Service-layer functions have focused unit tests that do not require committed secrets or live LLM calls.
- [x] **REF3-05**: Public API response contracts remain backward compatible unless a requirement explicitly documents a change.
- [x] **REF3-06**: Common backend errors use the existing Indonesian error taxonomy consistently across touched routes.

### Data Quality Monitor (DQ3)

- [x] **DQ3-01**: System computes data quality checks for stale data, missing dates, duplicates, negative/unrealistic values, and COA outlier deltas.
- [x] **DQ3-02**: Admin/operator can view a data quality summary and issue list with module, severity, source record, and suggested fix.
- [x] **DQ3-03**: Dashboard and management reports include data-quality caveats when source data is incomplete or suspicious.
- [x] **DQ3-04**: Import flows surface data-quality impact before commit when uploaded data would create warnings or critical issues.
- [x] **DQ3-05**: Data quality results are exportable or auditable for management follow-up.
- [x] **DQ3-06**: Tests cover clean, warning, and critical data-quality cases.

### Trend Analytics & Forecasting (TREND3)

- [x] **TREND3-01**: Dashboard and reports can compare current period to previous period for stock, arrivals, supplier performance, COA delta, and disputes.
- [x] **TREND3-02**: Supplier trend cards show volume, timeliness, quality delta, and dispute trend with clear risk labels.
- [x] **TREND3-03**: Stock forecast projects coverage using configurable burn assumptions and expected arrivals.
- [x] **TREND3-04**: Trend charts degrade safely for sparse historical data with Indonesian explanation instead of misleading charts.
- [x] **TREND3-05**: PDF and Excel exports include trend context matching the on-screen filter scope.

### AI Advisor v3 (AI3)

- [ ] **AI3-01**: Advisor can summarize trend and data-quality findings using visible source slices.
- [ ] **AI3-02**: Advisor can optionally use a configured LLM for narrative polish while deterministic fallback remains available.
- [ ] **AI3-03**: Advisor exposes confidence and limitations when data quality or historical coverage is weak.
- [ ] **AI3-04**: Advisor recommendations are grouped by urgency and suggested owner or operating role.
- [ ] **AI3-05**: Tests prevent unsupported claims and prevent accidental live LLM calls in normal test runs.

### UI/UX Operator Polish (UX3)

- [ ] **UX3-01**: Dashboard, report, and control pages share cleaner layout patterns for filters, headers, badges, loading states, and empty states.
- [ ] **UX3-02**: Top workflows require fewer clicks for monitoring stock, arrivals, COA disputes, and report/advisor review.
- [ ] **UX3-03**: Common desktop and tablet layouts have stable dimensions with no overlapping text, controls, cards, or charts.
- [ ] **UX3-04**: Loading, error, empty, partial-data, and success states use consistent Indonesian copy.
- [ ] **UX3-05**: Legacy React hook warnings are reduced where safe or kept in the warning register with explicit rationale.

## Future Requirements

- Multi-plant support and tenant separation.
- Multi-provider LLM routing and per-user AI budget tracking beyond the current configured provider path.
- Mobile-native application.
- Cursor-based pagination if row counts outgrow offset pagination.
- Predictive models trained from historical plant data beyond rule-based trend and coverage projection.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replacing MongoDB, FastAPI, or React | Locked architecture; v1.3 is incremental hardening and intelligence work. |
| Multi-tenant or multi-plant deployment | Current production scope is PLTU Tenayan only. |
| Rewriting all modules to a new frontend framework | Too much regression risk for a live plant workflow. |
| Fully autonomous AI actions | Advisor can recommend and draft, but operators/admins remain decision owners. |
| Storing production secrets or test credentials in committed docs | Credential hygiene remains locked. |
| Force-pushing or rewriting GitHub history to clean old artifacts | Repository hygiene must be forward-safe and non-destructive. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| OPS3-01..05 | Phase 22 | Complete |
| DRILL3-01..05 | Phase 23 | Complete |
| REF3-01..06 | Phase 24 | Complete |
| DQ3-01..06 | Phase 25 | Complete |
| TREND3-01..05 | Phase 26 | Complete |
| AI3-01..05 | Phase 27 | Pending |
| UX3-01..05 | Phase 28 | Pending |

**Coverage:**
- v1.3 requirements: 37 total
- Mapped to phases: 37
- Unmapped: 0
- Complete: 27

---
*Requirements defined: 2026-05-13*
*Last updated: 2026-05-14 after Phase 26 completion*
