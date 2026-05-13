# Visual Smoke QA

Date: 2026-05-14
Scope: Phase 29 frontend browser screenshot smoke coverage.

## Covered Pages

| Page | URL | Required Coverage |
|------|-----|-------------------|
| Dashboard | `/dashboard` | Stock, arrival/realisasi, dispute/umpire, and data-quality surfaces. |
| Management Report | `/laporan?tab=management` | Management summary, export action, stock and arrival cards. |
| Data Quality | `/data-quality` | Data-quality page anchor, summary/rule/action surface. |
| Dispute Monitor | `/dispute-monitor` | Dispute counters, table/list surface, dispute action copy. |
| Settings Runtime Status | `/settings` | Settings page and Status Operasional runtime panel. |

## Commands

List tests without launching a browser:

```bash
cd frontend
npx playwright test --list --config=playwright.config.js
```

Run browser smoke against an existing app:

```bash
cd frontend
VISUAL_SMOKE_BASE_URL=http://127.0.0.1:3000 \
VISUAL_SMOKE_TOKEN=<admin-or-operator-token> \
npm run visual:smoke
```

Or authenticate through the login page:

```bash
cd frontend
VISUAL_SMOKE_BASE_URL=http://127.0.0.1:3000 \
VISUAL_SMOKE_EMAIL=<admin-email> \
VISUAL_SMOKE_PASSWORD=<password> \
npm run visual:smoke
```

Use `VISUAL_SMOKE_START_SERVER=1` when the smoke run should start `npm start` automatically.

When running against a local FastAPI backend on another port, set backend CORS explicitly for the frontend origin, for example:

```bash
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

## What Fails The Smoke

- Authenticated run lands on `/login`.
- Required page anchors are missing.
- Body text is nearly blank.
- Document has horizontal overflow beyond the viewport.
- Visible text elements have obvious same-band collisions.

Screenshots are written under `frontend/test-results/visual-smoke/` for each Playwright project.

## Phase 29 Verification

On 2026-05-14 the suite passed 10/10 against a local isolated test environment:

- backend: `127.0.0.1:18029`
- frontend: `127.0.0.1:3029`
- database: `emits_visual_smoke_phase29`
- viewport projects: `desktop-chromium`, `tablet-chromium`
