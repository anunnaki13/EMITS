---
phase: 33
title: Regression & Release Gate
requirements:
  - REG4-01
  - REG4-02
  - REG4-03
  - REG4-04
status: context
---

# Phase 33 Context

## Objective

Provide one repeatable release gate command for EMITS v1.4 that runs focused
backend regressions, frontend warning-budget build, smoke verification or a
clear skip reason, and writes compact release artifacts.

## Inputs

- `.planning/ROADMAP.md` Phase 33 success criteria.
- `.planning/REQUIREMENTS.md` REG4-01..04.
- Phase 29: `frontend/scripts/check-hook-warning-register.js` and
  `npm run build:checked`.
- Phase 31: `ops/scripts/smoke_check.py`, runtime status artifacts, and runbook
  manual gate policy.
- Phase 32: `scripts/check_repo_hygiene.py`.

## Scope

- Add a release gate command under `ops/scripts/`.
- Keep backend tests grouped sequentially so the test backend on port 18013 does
  not collide across concurrent pytest sessions.
- Write ignored JSON/Markdown artifacts under `ops/release-artifacts/`.
- Update runbook with the new gate command.

## Out Of Scope

- Remote CI/CD migration.
- Full production deploy automation beyond existing `deploy.sh` and
  `runtime_status.sh`.
- Storing secrets or smoke credentials in committed files.
