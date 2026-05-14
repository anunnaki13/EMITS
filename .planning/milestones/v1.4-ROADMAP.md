# Roadmap: EMITS v1.4 - Production QA & Cleanup

## Milestones

- **v1.4 Production QA & Cleanup** - Phases 29-33, planned 2026-05-14.
- **v1.3 Production Operations & Decision Intelligence** - shipped 2026-05-14. [Roadmap archive](milestones/v1.3-ROADMAP.md), [requirements archive](milestones/v1.3-REQUIREMENTS.md), [audit](milestones/v1.3-MILESTONE-AUDIT.md).
- **v1.2 Operational Reliability & Data Governance** - shipped 2026-05-13. [Roadmap archive](milestones/v1.2-ROADMAP.md), [requirements archive](milestones/v1.2-REQUIREMENTS.md), [audit](milestones/v1.2-MILESTONE-AUDIT.md).
- **v1.1 Production Stabilization & Operational Upgrades** - shipped 2026-05-12. [Roadmap archive](milestones/v1.1-ROADMAP.md), [requirements archive](milestones/v1.1-REQUIREMENTS.md), [audit](v1.1-MILESTONE-AUDIT.md).

## Current Status

v1.4 implementation is complete; milestone audit/ship prep is ready.

## Milestone Goal

Turn the accepted v1.3 tech debt into concrete release-quality gates: clean frontend warning posture, repeatable visual QA, complete GSD validation metadata, real VPS runtime evidence, repository hygiene, and a consolidated regression pack.

## Planned Phases

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 29 | Frontend Warning & Visual QA | Remove or strictly account for frontend warnings and add browser visual smoke coverage for key operator/admin pages. | QA4-01..05 | Complete |
| 30 | GSD Metadata & Phase Archive Hygiene | Make planning state, archived phase docs, Nyquist metadata, and future completion templates consistent and discoverable. | META4-01..04 | Complete |
| 31 | Production Runtime Evidence | Capture real production runtime/smoke evidence and make release version metadata visible and auditable. | OPS4-01..05 | Complete |
| 32 | Repository Hygiene & Secret Safety | Resolve or document local artifact dirt, stop build-cache churn, and keep credential scanning effective. | REPO4-01..04 | Complete |
| 33 | Regression & Release Gate | Provide one release gate that runs backend, frontend, smoke, warning-budget, and artifact-summary checks. | REG4-01..04 | Complete |

## Phase Details

### Phase 29: Frontend Warning & Visual QA

**Goal:** Remove or strictly account for frontend warnings and add browser visual smoke coverage for key operator/admin pages.

**Requirements:** QA4-01, QA4-02, QA4-03, QA4-04, QA4-05

**Status:** Complete

**Success criteria:**
1. Remaining React hook warnings are fixed where safe, and any remaining warning is explicitly documented with owner/rationale.
2. Playwright or equivalent browser smoke captures desktop/tablet screenshots for dashboard, management report, data quality, dispute monitor, and settings runtime status.
3. Visual checks fail on blank critical panels, missing primary controls, or obvious text overlap in covered pages.
4. `npm run build` warning output is compared against `docs/quality/REACT_HOOK_WARNINGS.md`.
5. Covered pages use consistent Indonesian state copy for loading, error, empty, partial-data, and success states.

### Phase 30: GSD Metadata & Phase Archive Hygiene

**Goal:** Make planning state, archived phase docs, Nyquist metadata, and future completion templates consistent and discoverable.

**Requirements:** META4-01, META4-02, META4-03, META4-04

**Status:** Complete

**Success criteria:**
1. Shipped phase validation docs expose consistent Nyquist metadata or documented exceptions.
2. Active `.planning/phases/` contains only active milestone work while archived phase docs remain discoverable under milestone archives.
3. GSD health/progress output points to current v1.4 artifacts and does not instruct users to use stale v1.3 active files.
4. Future phase docs have a consistent SUMMARY/VERIFICATION/VALIDATION template with requirement frontmatter and residual-risk notes.

### Phase 31: Production Runtime Evidence

**Goal:** Capture real production runtime/smoke evidence and make release version metadata visible and auditable.

**Requirements:** OPS4-01, OPS4-02, OPS4-03, OPS4-04, OPS4-05

**Status:** Complete

**Success criteria:**
1. Full runtime status command produces an auditable production report artifact.
2. Smoke check records status through the admin API and latest result appears in runtime health UI.
3. Production runbook includes v1.4 release gate, artifact paths, fallback steps, and evidence retention.
4. Admin-visible build/version metadata includes deployed git SHA or release tag for backend and static frontend.
5. If real VPS access is unavailable during development, the release process marks runtime verification as a manual gate instead of a silent pass.

### Phase 32: Repository Hygiene & Secret Safety

**Goal:** Resolve or document local artifact dirt, stop build-cache churn, and keep credential scanning effective.

**Requirements:** REPO4-01, REPO4-02, REPO4-03, REPO4-04

**Status:** Complete

**Success criteria:**
1. Pre-existing local dirt is either resolved safely or documented as intentional local-only state without committing secrets.
2. Frontend build/test workflows no longer append cache pack paths to `.gitignore` or stage generated build-cache artifacts.
3. Credential scanning blocks real secret patterns while keeping local test credentials out of committed files.
4. A repo hygiene check reports release-blocking dirty changes separately from intentional local-only files.

### Phase 33: Regression & Release Gate

**Goal:** Provide one release gate that runs backend, frontend, smoke, warning-budget, and artifact-summary checks.

**Requirements:** REG4-01, REG4-02, REG4-03, REG4-04

**Status:** Complete

**Success criteria:**
1. One command runs focused backend regressions for auth, dashboard, COA/import, reports, data quality, trends, advisor, and runtime status.
2. One command runs frontend production build and validates warning output against the warning register.
3. Smoke-check execution is included, or the artifact records a clear skip reason when services are unavailable.
4. Release artifact summary includes command results, warnings, skipped checks, git SHA/tag, and next action.

## Requirement Coverage

| Requirement Group | Covered By | Status |
|-------------------|------------|--------|
| QA4-01..05 | Phase 29 | Complete |
| META4-01..04 | Phase 30 | Complete |
| OPS4-01..05 | Phase 31 | Complete |
| REPO4-01..04 | Phase 32 | Complete |
| REG4-01..04 | Phase 33 | Complete |

Coverage: 22/22 active v1.4 requirements mapped; 22/22 complete.

## Completed Milestones

<details>
<summary>v1.3 Production Operations & Decision Intelligence (Phases 22-28) - shipped 2026-05-14</summary>

- [x] Phase 22: Production Runtime & Observability.
- [x] Phase 23: Dashboard Drilldown Integration.
- [x] Phase 24: Backend Service Boundary Refactor.
- [x] Phase 25: Data Quality Monitor.
- [x] Phase 26: Trend Analytics & Forecasting.
- [x] Phase 27: AI Advisor v3.
- [x] Phase 28: Operator UI/UX Polish.

</details>

## Next Step

Complete or audit milestone v1.4:

```bash
$gsd-audit-milestone
```
