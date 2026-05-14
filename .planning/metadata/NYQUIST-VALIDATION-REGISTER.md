# Nyquist Validation Metadata Register

**Created:** 2026-05-14
**Owner:** Phase 30 GSD Metadata & Phase Archive Hygiene
**Scope:** Current and archived phase `*-VALIDATION.md` files.

## Standard

Every validation file must expose one of:

- `nyquist_status: planned|passed|failed|partial`
- `nyquist_status: legacy_exception` with a short exception reason
- historical `nyquist_compliant: true|false`

`legacy_exception` means the validation artifact was created before the v1.4 metadata standard, but the archived evidence is preserved and cross-linked from the archive index.

## Current Active Milestone

No active milestone is currently defined. Start the next planning cycle with
`$gsd-new-milestone`.

## Archived v1.4 Workspace

| Phase | Validation File | Metadata Status |
|-------|-----------------|-----------------|
| 29 | `.planning/milestones/v1.4-phases/29-frontend-warning-visual-qa/29-VALIDATION.md` | `nyquist_status: passed` |
| 30 | `.planning/milestones/v1.4-phases/30-gsd-metadata-phase-archive-hygiene/30-VALIDATION.md` | `nyquist_status: passed` |
| 31 | `.planning/milestones/v1.4-phases/31-production-runtime-evidence/31-VALIDATION.md` | `nyquist_status: passed` |
| 32 | `.planning/milestones/v1.4-phases/32-repository-hygiene-secret-safety/32-VALIDATION.md` | `nyquist_status: passed` |
| 33 | `.planning/milestones/v1.4-phases/33-regression-release-gate/33-VALIDATION.md` | `nyquist_status: passed` |

## Archived v1.3 Workspace

| Phase | Validation File | Metadata Status |
|-------|-----------------|-----------------|
| 01 | `.planning/milestones/v1.3-phases/01-production-audit-onboarding/01-VALIDATION.md` | `nyquist_compliant: true` |
| 02 | `.planning/milestones/v1.3-phases/02-authentication-stabilization/02-VALIDATION.md` | `nyquist_compliant: true` |
| 03 | `.planning/milestones/v1.3-phases/03-documentation-refresh-decision-lock-in/03-VALIDATION.md` | `nyquist_compliant: true` |
| 04 | `.planning/milestones/v1.3-phases/04-test-suite-stabilization/04-VALIDATION.md` | `nyquist_status: partial` |
| 05 | `.planning/milestones/v1.3-phases/05-collection-naming-debt-resolution/05-VALIDATION.md` | `nyquist_status: partial` |
| 06 | `.planning/milestones/v1.3-phases/06-operational-unblocks/06-VALIDATION.md` | `nyquist_status: passed` |
| 07 | `.planning/milestones/v1.3-phases/07-upgrade-backlog-foundation/07-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 08 | `.planning/milestones/v1.3-phases/08-polish-nice-to-haves/08-VALIDATION.md` | `nyquist_status: passed` |
| 09 | `.planning/milestones/v1.3-phases/09-backend-refactor-foundation/09-VALIDATION.md` | `nyquist_status: passed` |
| 10 | `.planning/milestones/v1.3-phases/10-dashboard-control-room-v2/10-VALIDATION.md` | `nyquist_status: passed` |
| 11 | `.planning/milestones/v1.3-phases/11-alerts-notifications/11-VALIDATION.md` | `nyquist_status: passed` |
| 12 | `.planning/milestones/v1.3-phases/12-formal-dispute-umpire-workflow/12-VALIDATION.md` | `nyquist_status: passed` |
| 13 | `.planning/milestones/v1.3-phases/13-excel-import-preview-validation/13-VALIDATION.md` | `nyquist_status: passed` |
| 14 | `.planning/milestones/v1.3-phases/14-audit-trail-v2/14-VALIDATION.md` | `nyquist_status: passed` |
| 15 | `.planning/milestones/v1.3-phases/15-management-reports/15-VALIDATION.md` | `nyquist_status: passed` |
| 16 | `.planning/milestones/v1.3-phases/16-contextual-ai-assistant/16-VALIDATION.md` | `nyquist_status: passed` |
| 17 | `.planning/milestones/v1.3-phases/17-backup-disaster-recovery-automation/17-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 18 | `.planning/milestones/v1.3-phases/18-coa-import-governance-v2/18-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 19 | `.planning/milestones/v1.3-phases/19-production-deployment-hardening/19-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 20 | `.planning/milestones/v1.3-phases/20-dashboard-command-center-v3/20-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 21 | `.planning/milestones/v1.3-phases/21-management-reports-ai-advisor-v2/21-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 22 | `.planning/milestones/v1.3-phases/22-production-runtime-observability/22-VALIDATION.md` | `nyquist_compliant: true` |
| 23 | `.planning/milestones/v1.3-phases/23-dashboard-drilldown-integration/23-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 24 | `.planning/milestones/v1.3-phases/24-backend-service-boundary-refactor/24-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 25 | `.planning/milestones/v1.3-phases/25-data-quality-monitor/25-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 26 | `.planning/milestones/v1.3-phases/26-trend-analytics-forecasting/26-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 27 | `.planning/milestones/v1.3-phases/27-ai-advisor-v3/27-VALIDATION.md` | `nyquist_status: legacy_exception` |
| 28 | `.planning/milestones/v1.3-phases/28-operator-ui-ux-polish/28-VALIDATION.md` | `nyquist_status: legacy_exception` |

## Verification

Run:

```bash
python3 scripts/check_planning_hygiene.py
```
