---
phase: 01-production-audit-onboarding
plan: 03
subsystem: frontend
tags: [audit, frontend, routes, auth-boundary, read-only]
requires:
  - .planning/PROJECT.md
  - pltu-tenayan-full-backup/frontend/src/App.js
  - pltu-tenayan-full-backup/frontend/src/contexts/AuthContext.js
  - pltu-tenayan-full-backup/frontend/src/components/Layout.js
  - pltu-tenayan-full-backup/frontend/src/pages/
  - pltu-tenayan-full-backup/docs/audit/ENDPOINT_AUDIT.md
provides:
  - pltu-tenayan-full-backup/docs/audit/FRONTEND_MAP.md
affects:
  - phase:02-authentication-stabilization (auth boundary + protected-route inventory feeds login-bug regression test design)
  - phase:03-documentation-refresh (route → page → endpoint table is canonical input for README / documentation.md regen)
  - phase:07-refactor (per-page endpoint list precedes any page-file split)
key-files:
  created:
    - pltu-tenayan-full-backup/docs/audit/FRONTEND_MAP.md
    - pltu-tenayan-full-backup/docs/audit/.work/routes.txt
    - pltu-tenayan-full-backup/docs/audit/.work/page-endpoints.txt
    - pltu-tenayan-full-backup/docs/audit/.work/sidebar-links.txt
  modified: []
decisions:
  - Treat the / redirect (Navigate to /dashboard) as not-protected itself; effective protection comes from the destination route.
  - Document Login.js endpoint consumption transitively through AuthContext (Login.js does not call axios directly).
  - Path-parameter normalization mirrors ENDPOINT_AUDIT.md OpenAPI-style placeholders ({vessel_id}, {record_id}, …) so cross-checks line up 1:1.
metrics:
  tasks_total: 2
  tasks_completed: 2
  files_created: 4
  files_modified: 0
  commits: 2
  duration_minutes: 12
  completed_date: 2026-05-10
---

# Phase 1 Plan 3: Frontend Map (Routes, Pages, Endpoints, Auth Boundary) Summary

**One-liner:** Page-by-page surface map of the React 19 frontend — every route in App.js linked to its page component file, its consumed `/api/*` endpoints (extracted by grep), its protected/public status, and the AuthContext-anchored auth boundary; sidebar nav cross-checked in both directions and frontend endpoint set cross-checked against the live OpenAPI inventory.

## What Was Built

Two artifacts on disk:

1. **pltu-tenayan-full-backup/docs/audit/FRONTEND_MAP.md** (408 lines) — the deliverable. Structure:
   - **Route → Page → Endpoints** table: 17 rows (1 redirect + 16 page routes), each annotated with protected? and the joined endpoint list.
   - **Per-page detail**: 16 `### <PageComponent>` subsections naming routes, source file, protection status, every `/api/*` call with method and source line, and dynamic-call notes where applicable.
   - **Auth boundary**: prose section naming login function, token storage key, rehydrate flow, `getAuthHeader`, logout, and `ProtectedRoute` — every item with a file:line reference. Includes a markdown auth diagram and the rehydrate-on-mount path.
   - **Sidebar / nav cross-check**: 15 nav entries verified against the route table, with both directions of mismatch listed.
   - **Cross-check vs ENDPOINT_AUDIT.md**: 56-row table of every page-consumed endpoint, its consuming page(s), live presence, and live status. Plus a list of live endpoints the frontend does NOT consume.
   - **Methodology**: reproducible grep pattern, normalization rules, scope of the read-only audit.

2. **pltu-tenayan-full-backup/docs/audit/.work/** — three flat-text inputs (routes.txt 17 lines, page-endpoints.txt 82 lines, sidebar-links.txt 15 lines) so the FRONTEND_MAP.md tables are reproducible from disk.

## Headline Numbers

| Metric | Value |
|--------|-------|
| Total routes mapped (declared in App.js) | 17 (16 page routes + 1 redirect from `/`) |
| Total page components | 16 |
| Total distinct `/api/*` endpoints called from any page | 56 |
| Pages with NO `/api/*` calls (pure-presentational sanity check) | 0 — every protected page calls at least one endpoint; Login.js calls none directly but transitively triggers /api/auth/login + /api/auth/register via AuthContext |
| Pages with `<dynamic>` calls | 1 — LaporanPage (LaporanPage.js:105 resolves to one of vessels/barges/trucking/biomassa/po-batubara/merit-order) |
| Sidebar nav entries | 15 |
| Routes WITHOUT a nav entry | 2 (/login, /) — both expected, neither an accessibility gap |
| Nav entries WITHOUT a route (dead links) | 0 |
| frontend-references-dead-endpoint flags | 0 |
| frontend-uses-broken-endpoint flags | 0 |
| Live endpoints NOT consumed by any page | 7 (/api/, /api/health, /api/merit-order/periods, /api/coa-reconciliation/shipment/{shipment}, /api/smart-stock/{entry_id} DELETE, /api/ai/sessions, /api/ai/sessions/new, /api/ai/sessions/{session_id}) |

## Auth Boundary Surface (5-Line Brief)

- **Login function:** `login(email, password)` at frontend/src/contexts/AuthContext.js:34 — POSTs `${API_URL}/api/auth/login`, stores token + sets state.
- **Token storage key:** `localStorage["token"]` (literal string `"token"`); set at AuthContext.js:37, cleared at :24 (failed rehydrate) / :53 (logout).
- **Rehydrate function:** `initAuth()` inside the `useEffect` at AuthContext.js:13-32 — issues `GET ${API_URL}/api/auth/me` with the saved token; clears state on failure.
- **getAuthHeader:** AuthContext.js:58-60 — returns `{ Authorization: \`Bearer ${token}\` }` from in-memory state (not localStorage), so logout immediately invalidates subsequent calls.
- **ProtectedRoute:** declared inline in frontend/src/App.js:22-44 — renders a loading pulse while rehydrating, redirects to `/login` when no user, redirects to `/dashboard` on `allowedRoles` mismatch.

## Pages With <dynamic> Calls (Phase 2/4 Static-Resolution Targets)

| Page | File:line | Resolves to |
|------|-----------|-------------|
| LaporanPage | LaporanPage.js:105 | `axios.get(\`${API_URL}/api/${endpoint}\`, …)` where `endpoint` is a runtime ternary chain over `activeTab` evaluating to one of `vessels`, `barges`, `trucking`, `biomassa`, `po-batubara`, `merit-order`. Effectively proxies the six rekap-receipt list endpoints — Phase 2 should treat all six as transitively consumed by /laporan. |

## Orphan Nav Entries / Routes-Without-Nav

- **Nav entries without a route:** none.
- **Routes without a nav entry:**
  - `/login` — expected (sidebar lives inside the protected `<Layout>` wrapper; users on /login have no Layout).
  - `/` — expected (immediate `<Navigate to="/dashboard" replace />` redirect; not a destination).
- **Result:** zero unintended accessibility gaps. The Layout sidebar fully covers the user-facing route set, with the role-gated /settings entry only rendered when `user?.role === "admin"` — matching the route's `allowedRoles=["admin"]`.

## Cross-Check vs ENDPOINT_AUDIT.md

ENDPOINT_AUDIT.md was on disk at write time (Phase 1 plan 01 had completed). Both flag counts that drive Phase 2:

- **frontend-references-dead-endpoint:** 0 — every page-consumed endpoint exists in the live OpenAPI surface.
- **frontend-uses-broken-endpoint:** 0 — no page consumes an endpoint with `broken-*` status.

Operational note (not a flag): `POST /api/smart-blending/recommend` (SmartBlendingPage's only call) is the endpoint operationally degraded by Universal LLM Key budget exhaustion. Phase 6 OPS-01.

## Phase 2/3/6 Hand-Offs Surfaced By This Audit

- **MeritOrderPage calls `/api/merit-order` with `page_size=10000`** (MeritOrderPage.js:103), exceeding the documented operational pagination cap of 500. Backend cap behavior on this oversized value is unverified by this read-only audit; Phase 2 regression-test target.
- **`/api/auth/register` is consumed both by Login (public registration flow) and by SettingsPage (admin "create user" flow)**. CONS-auth-header lists the route as public; the same endpoint serves both flows. Surface ambiguity flagged for Phase 2 reconciliation (open registration vs admin-creates-user).
- **AIIntelligencePage does not consume `/api/ai/sessions*`** even though those endpoints exist live — aligns with STAB-06 ("AI conversation memory frontend integration completed (REQ-ai-conversation-memory tail)") backlog item.
- **`/api/coa-reconciliation/shipment/{shipment}` and `/api/smart-stock/{entry_id}` (single DELETE)** exist live but are not wired in any page in the audited surface — Phase 3 documentation refresh should clarify whether these are reserved or genuinely unused.
- **MeritOrderPage does not consume `/api/merit-order/periods`** even though it exists live and is documented; flag for Phase 3 docs reconciliation.

## Deviations from Plan

None — plan executed exactly as written. Both tasks completed; verification commands all pass; acceptance criteria met (route table > 10 rows, ≥ 10 distinct per-page subsections, auth boundary names every required surface element with file:line, sidebar cross-checked both directions, ENDPOINT_AUDIT cross-check rendered with content, both protected and unprotected route examples present, no credential leakage).

## Commits

Inner repo (`pltu-tenayan-full-backup`):

| Task | Hash | Message |
|------|------|---------|
| 1 | 1d140f2 | chore(01-03): capture frontend route, page-endpoint, sidebar nav inputs |
| 2 | 8eb46e5 | docs(01-03): add FRONTEND_MAP.md (routes, pages, endpoints, auth boundary) |

Outer repo (planning metadata): final commit follows this SUMMARY.md write.

## Self-Check

- [x] FRONTEND_MAP.md exists at pltu-tenayan-full-backup/docs/audit/FRONTEND_MAP.md (408 lines)
- [x] .work/routes.txt exists (17 lines)
- [x] .work/page-endpoints.txt exists (82 lines)
- [x] .work/sidebar-links.txt exists (15 lines)
- [x] Inner-repo commit 1d140f2 exists in `pltu-tenayan-full-backup` git log
- [x] Inner-repo commit 8eb46e5 exists in `pltu-tenayan-full-backup` git log
- [x] Plan automated verifier (test -s + 6 grep checks + credential negative-grep) returns VERIFY-PASS
- [x] No frontend source file under `pltu-tenayan-full-backup/frontend/` modified

## Self-Check: PASSED
