---
phase: 29
requirements:
  - QA4-01
  - QA4-02
  - QA4-03
  - QA4-04
  - QA4-05
nyquist_status: planned
validation_owner: codex
---

# Phase 29 Validation Plan

## Gates

| Requirement | Validation |
|-------------|------------|
| QA4-01 | `npm run build` emits no undocumented React hook warnings; register updated. |
| QA4-02 | Playwright visual smoke test list includes dashboard, management report, data quality, dispute monitor, and settings runtime status for desktop/tablet projects. |
| QA4-03 | Visual smoke helpers assert non-empty page body, required anchors, no horizontal overflow, and no obvious text collisions. |
| QA4-04 | `npm run build:checked` compares actual build output with `docs/quality/REACT_HOOK_WARNINGS.md` and fails on drift. |
| QA4-05 | Covered state copy is reviewed for Indonesian loading/error/empty/success wording. |

## Commands

```bash
cd frontend && npm run build
cd frontend && npm run build:checked
cd frontend && npx playwright test --list --config=playwright.config.js
```

Full browser execution requires a reachable frontend/backend plus either `VISUAL_SMOKE_TOKEN` or `VISUAL_SMOKE_EMAIL`/`VISUAL_SMOKE_PASSWORD`.
