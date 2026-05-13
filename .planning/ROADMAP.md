# Roadmap: EMITS v1.3 - Production Operations & Decision Intelligence

## Milestones

- **v1.3 Production Operations & Decision Intelligence** - Phases 22-28, planned 2026-05-13.
- **v1.2 Operational Reliability & Data Governance** - Phases 17-21, shipped 2026-05-13. [Roadmap archive](milestones/v1.2-ROADMAP.md), [requirements archive](milestones/v1.2-REQUIREMENTS.md), [audit](milestones/v1.2-MILESTONE-AUDIT.md).
- **v1.1 Production Stabilization & Operational Upgrades** - Phases 1-16, shipped 2026-05-12. [Roadmap archive](milestones/v1.1-ROADMAP.md), [requirements archive](milestones/v1.1-REQUIREMENTS.md), [audit](v1.1-MILESTONE-AUDIT.md).

## Current Status

v1.3 is in planning. The milestone continues phase numbering from v1.2 and focuses on production operations, backend maintainability, data quality, trend analytics, AI advice, and UI/UX polish.

## Milestone Goal

Move EMITS from feature-complete enough toward a more operable, maintainable, decision-oriented production system: static nginx deployment, real drilldowns, cleaner backend service boundaries, data quality monitoring, trend analytics, safer AI advice, and stronger operator UI polish.

## Planned Phases

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 22 | Production Runtime & Observability | Real production operation uses static nginx frontend, visible runtime health, and auditable smoke evidence. | OPS3-01..05 | 5 |
| 23 | Dashboard Drilldown Integration | Dashboard filters become real working context inside destination pages. | DRILL3-01..05 | 5 |
| 24 | Backend Service Boundary Refactor | Shared dashboard/report/advisor logic is moved into testable services without breaking API contracts. | REF3-01..06 | 6 |
| 25 | Data Quality Monitor | Operators can see stale, missing, duplicate, outlier, and inconsistent data before it misleads decisions. | DQ3-01..06 | 6 |
| 26 | Trend Analytics & Forecasting | Dashboard and reports explain period-over-period movement and projected stock coverage. | TREND3-01..05 | 5 |
| 27 | AI Advisor v3 | Advisor explains trend/data-quality context with source slices, limitations, and deterministic fallback. | AI3-01..05 | 5 |
| 28 | Operator UI/UX Polish | Monitoring and reporting workflows become cleaner, faster, and more stable on desktop/tablet. | UX3-01..05 | 5 |

## Phase Details

### Phase 22: Production Runtime & Observability

**Goal:** Real production operation uses static nginx frontend, visible runtime health, and auditable smoke evidence.

**Requirements:** OPS3-01, OPS3-02, OPS3-03, OPS3-04, OPS3-05

**Success criteria:**
1. React production build can be served through nginx with `/api` reverse proxy and no `yarn start` runtime dependency.
2. One command verifies backend, frontend static build, nginx, MongoDB, disk, latest backup, and app version.
3. Admin runtime health panel exposes current service, DB, backup, smoke, and build/version status.
4. Production runbook reflects the actual static-nginx deployment path, rollback, and triage flow.
5. Smoke checks produce auditable status evidence for post-deploy review.

### Phase 23: Dashboard Drilldown Integration

**Goal:** Dashboard filters become real working context inside destination pages.

**Requirements:** DRILL3-01, DRILL3-02, DRILL3-03, DRILL3-04, DRILL3-05

**Success criteria:**
1. Stock, arrivals/PO, COA, dispute, and reports pages read dashboard query filters and apply them to visible data.
2. Destination pages show filter chips, reset controls, and clear Indonesian empty states.
3. Back navigation returns users to the originating dashboard context.
4. Filter handling does not break direct page visits without query parameters.
5. Focused tests cover representative dashboard-to-destination drilldown flows.

### Phase 24: Backend Service Boundary Refactor

**Goal:** Shared dashboard/report/advisor logic is moved into testable services without breaking API contracts.

**Requirements:** REF3-01, REF3-02, REF3-03, REF3-04, REF3-05, REF3-06

**Success criteria:**
1. Shared calculations for operational dashboard, management reports, and advisor are extracted into service-layer modules.
2. Date/number/period/supplier/mode normalization helpers are consolidated.
3. Router handlers stay thin and keep existing auth/role and response behavior.
4. Service-level tests run without live secrets or live LLM calls.
5. Existing response contracts and smoke checks remain compatible.
6. Touched backend errors use the existing Indonesian error taxonomy.

### Phase 25: Data Quality Monitor

**Goal:** Operators can see stale, missing, duplicate, outlier, and inconsistent data before it misleads decisions.

**Requirements:** DQ3-01, DQ3-02, DQ3-03, DQ3-04, DQ3-05, DQ3-06

**Success criteria:**
1. Data quality checks identify stale records, missing dates, duplicates, unrealistic values, and COA outlier deltas.
2. Admin/operator UI shows issue summary, severity, module, source record, and suggested fix.
3. Dashboard and management reports include caveats when data quality affects interpretation.
4. COA/import flows show data-quality impact before commit.
5. Quality results can be exported or audited.
6. Tests cover clean, warning, and critical quality cases.

### Phase 26: Trend Analytics & Forecasting

**Goal:** Dashboard and reports explain period-over-period movement and projected stock coverage.

**Requirements:** TREND3-01, TREND3-02, TREND3-03, TREND3-04, TREND3-05

**Success criteria:**
1. Dashboard and reports compare current period to previous period for stock, arrivals, suppliers, COA deltas, and disputes.
2. Supplier trend cards explain volume, timeliness, quality delta, and dispute direction.
3. Stock coverage forecast uses configurable burn assumptions and expected arrivals.
4. Sparse historical data renders honest partial-data states instead of misleading charts.
5. PDF/Excel exports include trend context for the same filter scope.

### Phase 27: AI Advisor v3

**Goal:** Advisor explains trend/data-quality context with source slices, limitations, and deterministic fallback.

**Requirements:** AI3-01, AI3-02, AI3-03, AI3-04, AI3-05

**Success criteria:**
1. Advisor summarizes trends and data-quality caveats using visible source slices.
2. Optional LLM narrative polish can be used only when configured, while deterministic fallback remains reliable.
3. Advisor clearly exposes confidence and limitations when data is sparse or suspicious.
4. Recommendations are grouped by urgency and suggested owner/role.
5. Tests guard against unsupported claims and accidental live LLM calls.

### Phase 28: Operator UI/UX Polish

**Goal:** Monitoring and reporting workflows become cleaner, faster, and more stable on desktop/tablet.

**Requirements:** UX3-01, UX3-02, UX3-03, UX3-04, UX3-05

**Success criteria:**
1. Dashboard, report, and control surfaces share consistent filter/header/badge/state patterns.
2. Monitoring stock, arrivals, disputes, and report/advisor review takes fewer clicks.
3. Common desktop and tablet layouts avoid overlapping text, controls, cards, and charts.
4. Loading/error/empty/partial/success copy is consistent Indonesian text.
5. React hook warnings are reduced where safe or documented with explicit rationale.

## Requirement Coverage

| Requirement Group | Covered By | Status |
|-------------------|------------|--------|
| OPS3-01..05 | Phase 22 | Pending |
| DRILL3-01..05 | Phase 23 | Pending |
| REF3-01..06 | Phase 24 | Pending |
| DQ3-01..06 | Phase 25 | Pending |
| TREND3-01..05 | Phase 26 | Pending |
| AI3-01..05 | Phase 27 | Pending |
| UX3-01..05 | Phase 28 | Pending |

Coverage: 37/37 active v1.3 requirements mapped; 0/37 complete.

## Completed Milestones

<details>
<summary>v1.2 Operational Reliability & Data Governance (Phases 17-21) - shipped 2026-05-13</summary>

- [x] Phase 17: Backup & Disaster Recovery Automation
- [x] Phase 18: COA Import Governance v2
- [x] Phase 19: Production Deployment Hardening
- [x] Phase 20: Dashboard Command Center v3
- [x] Phase 21: Management Reports & AI Advisor v2

See [v1.2 roadmap archive](milestones/v1.2-ROADMAP.md).

</details>

<details>
<summary>v1.1 Production Stabilization & Operational Upgrades (Phases 1-16) - shipped 2026-05-12</summary>

See [v1.1 roadmap archive](milestones/v1.1-ROADMAP.md).

</details>

## Next Step

Execute Phase 22:

```bash
$gsd-execute-phase 22
```
