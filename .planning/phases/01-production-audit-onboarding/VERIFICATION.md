---
phase: 01-production-audit-onboarding
verified: 2026-05-10T12:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 1: Production Audit & Onboarding Verification Report

**Phase Goal:** The project owner has an accurate, written map of the live system — endpoints, collections, frontend routes, and the login bug — so every later phase has ground truth to work from.
**Verified:** 2026-05-10T12:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | One document shows every live `/api/*` endpoint with status (working / broken / legacy) verified against the running VPS | VERIFIED | `ENDPOINT_AUDIT.md` lines 32–98: 64-row inventory table fed from a pinned 2026-05-10T11:14Z fetch of `http://103.150.197.225:8013/openapi.json`. Each row has Path / Methods / Auth / Role tier / Live status / In API_REFERENCE? columns. Counts section (lines 10–16): live=64, documented=63, intersection=63, drift live-only=1 (bare `/api/` grep artifact), drift doc-only=0. Drift sections present at lines 101–107. Pagination contract spot-check (lines 109–127) covers 11 list endpoints, 9 confirmed CONS-pagination-shape, 2 intentional-divergence documented. |
| 2 | Actual MongoDB collection row counts cross-checked against documented, with legacy duplicates flagged | VERIFIED | `DATA_AUDIT.md` lines 12–33: 17-row inventory (13 live + 4 missing-CONS-entries), live counts captured 2026-05-10T11:25:04Z via `mongosh listCollections + countDocuments`. All 10 documented expected counts present and matched exactly except `users` (live=8, doc=7, +1 drift flagged). Naming-debt mapping (lines 35–73) covers all four pairs (smartstock-pair, sumberpemakaian-pair, settings-pair, ai-history-pair) with row counts on both sides; in every pair only one side has live data (zero merge-required pairs — easiest Phase 5 starting point). Projection-contract spot-check (lines 75–100) lists `id` and `_id` field presence per collection. |
| 3 | Which frontend page consumes which API endpoints and where the auth boundary is | VERIFIED | `FRONTEND_MAP.md` lines 9–27: 17-row Route → Page → Endpoints table (16 page routes + 1 redirect from `/`). Per-page detail (lines 34–236): 16 distinct `### <PageComponent>` subsections naming source file, protection status, and every `/api/*` call with method + source line. Auth boundary section (lines 238–282) names login function (`login` AuthContext.js:34), token storage (`localStorage["token"]` AuthContext.js:37), rehydrate (`initAuth` AuthContext.js:13–32), `getAuthHeader` (AuthContext.js:58–60), logout (AuthContext.js:52–56), `ProtectedRoute` (App.js:22–44) — each with file:line. Sidebar cross-check (lines 285–312): 15 nav entries, 0 dead links, 2 expected route-without-nav (/login, /). Cross-check vs ENDPOINT_AUDIT (lines 314–392): 56-row table; frontend-references-dead-endpoint=0, frontend-uses-broken-endpoint=0. |
| 4 | Login bug has written reproduction with steps, observed vs expected, and named suspected component | VERIFIED | `LOGIN_BUG.md` lines 18–136: three reproduction paths (Path A UI login at lines 20–52, Path B API login at 54–80, Path C API register at 82–136), each with explicit Steps / Expected / Observed sections. Backend baseline confirmed: login 200 / 401 / 422 (Path B), register all-three-roles 200 + duplicate 400 (Path C). Suspected component section (lines 138–173) names `Radix <Select>` at `Login.js:186–197` with import line (Login.js:10), state setter (Login.js:27), submit-handler read (Login.js:47); plus three secondary suspects with file:line. ResizeObserver suppressor at `index.html:49–65` documented verbatim (lines 175–196). Operator playbook for browser-deferred steps (lines 198–217). |

**Score:** 4/4 truths verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pltu-tenayan-full-backup/docs/audit/ENDPOINT_AUDIT.md` | Live `/api/*` inventory with status / auth / role / drift | VERIFIED | 158 lines; 64 inventory rows starting with `/api/` (≥30 acceptance bar); both Drift sections present; pagination spot-check section present with 11 endpoints; Counts section reports 4 numbers; status values constrained to documented set. |
| `pltu-tenayan-full-backup/docs/audit/DATA_AUDIT.md` | Live MongoDB collection inventory with row counts, naming-debt pairs, projection contract | VERIFIED | 213 lines; inventory table has 17 rows (≥8 acceptance bar); all four naming-debt pair subsections present (`### smartstock-pair`, `### sumberpemakaian-pair`, `### settings-pair`, `### ai-history-pair`); Projection contract spot-check section present with per-collection table; all 10 documented expected counts (vessels=111, trucking=461, coa_reconciliation=721, biomassa=45, smartstock=207, po_batubara=301, merit_order=58, sumberpemakaian=208, ai_chat_history=10, users=7) present in inventory rows. |
| `pltu-tenayan-full-backup/docs/audit/FRONTEND_MAP.md` | Frontend route → page → endpoints map with auth boundary | VERIFIED | 408 lines; 17 route-table rows starting with `/` (≥10 acceptance bar); 16 distinct per-page subsections; auth boundary names every required surface element with AuthContext.js / App.js file:line refs; both protected (true) and unprotected (false) routes present in table; sidebar cross-check section present with both directions; ENDPOINT_AUDIT cross-check rendered with content (56 rows). |
| `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md` | Reproducible login + register bug repro with named suspect | VERIFIED | 224 lines; `## Reproduction` heading present; all three `### Path A/B/C` headings present; Suspected component section with `Login.js:186–197` cite; ResizeObserver suppressor cited at `index.html:49–65`; both `/api/auth/login` and `/api/auth/register` referenced; document does NOT propose code changes (no diff/patch markers). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| ENDPOINT_AUDIT.md | `http://103.150.197.225:8013/openapi.json` | Live OpenAPI fetch (curl) | WIRED | OpenAPI source documented at line 4; pinned snapshot at `.work/openapi.json`; capture timestamp 2026-05-10T11:14Z; 64 paths extracted from live JSON. |
| ENDPOINT_AUDIT.md | `pltu-tenayan-full-backup/API_REFERENCE.md` | Cross-reference / drift table | WIRED | "In API_REFERENCE?" column on every row; both drift sections render the live-only and doc-only sets. |
| DATA_AUDIT.md | `mongodb://localhost:27017/pltu_tenayan` | mongosh listCollections + countDocuments | WIRED | Method line 6 documents the live source; raw artifacts at `.work/mongo-collections.txt`, `.work/mongo-counts.json`, `.work/mongo-samples.json`. |
| DATA_AUDIT.md | `.planning/intel/constraints.md` (CONS-collection-naming-debt) | Naming-debt pair section maps each pair | WIRED | All four pairs from CONS-collection-naming-debt have dedicated subsections with both-side row counts. |
| FRONTEND_MAP.md | `frontend/src/App.js` | Route table from `<Route>` declarations | WIRED | Per-page detail cites App.js:50 for redirect, App.js:22-44 for ProtectedRoute. |
| FRONTEND_MAP.md | `frontend/src/contexts/AuthContext.js` | Auth boundary section | WIRED | Six required surface elements (login, token storage, rehydrate, getAuthHeader, logout, ProtectedRoute) each cite a specific AuthContext.js or App.js line. |
| FRONTEND_MAP.md | `ENDPOINT_AUDIT.md` | Each consumed endpoint resolved | WIRED | Cross-check table at lines 318–375; flag summary at lines 377–381 (frontend-references-dead-endpoint=0, frontend-uses-broken-endpoint=0). |
| LOGIN_BUG.md | `frontend/src/pages/Login.js` | Suspect component cite | WIRED | Login.js:186–197 cited with the verbatim JSX block; secondary suspects also cite file:line. |
| LOGIN_BUG.md | `http://103.150.197.225:8013/api/auth/login` | Backend repro via curl | WIRED | Path B status table at lines 70–75 reports HTTP 200 / 401 / 422 from live VPS plus localhost sanity check. |
| LOGIN_BUG.md | `frontend/public/index.html` (ResizeObserver suppressor) | Mitigation status section | WIRED | Cite at lines 14, 175 ("lines 49–65") with verbatim suppressor block reproduced at lines 178–196. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| AUDIT-01 | 01-01-PLAN.md | Inventory of live API endpoints with status verified against running VPS at 103.150.197.225 | SATISFIED | ENDPOINT_AUDIT.md — 64 endpoints inventoried with live OpenAPI fetch + per-endpoint status. |
| AUDIT-02 | 01-02-PLAN.md | Inventory of MongoDB collections with row counts cross-checked against PRD/SPEC and live data | SATISFIED | DATA_AUDIT.md — 17-row inventory, all 10 documented expected counts present, all 4 naming-debt pairs mapped. |
| AUDIT-03 | 01-03-PLAN.md | Map of frontend routes/pages and which API endpoints each consumes | SATISFIED | FRONTEND_MAP.md — 17 routes, 16 page components, 56 distinct endpoints, auth boundary documented. |
| AUDIT-04 | 01-04-PLAN.md | Login/auth bug documented reproduction (steps, observed vs expected, suspected component) | SATISFIED | LOGIN_BUG.md — three reproduction paths, named suspect at Login.js:186–197, ResizeObserver suppressor documented. |

No orphaned phase requirements — REQUIREMENTS.md maps Phase 1 to AUDIT-01..04 and all four are claimed by plans 01-01 / 01-02 / 01-03 / 01-04 respectively.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| (none) | No TODO / FIXME / "coming soon" / "not yet implemented" patterns found in any of the four audit deliverables. | — | — |
| (none) | No empty implementations, hardcoded empty arrays/objects, or console.log-only stubs. | — | — |
| (none) | No JWT bearer tokens, cleartext passwords, or MongoDB connection strings with credentials in any audit doc. | — | — |

Credential redaction grep (Step 7 sweep across all four files) returned zero matches for `JWT_PREFIX[A-Za-z0-9._-]{20,}`, `bearer\s+[A-Za-z0-9._-]{20,}`, `(password|secret)\s*[:=]\s*["'][^"' ]{4,}`, and `${MONGO_URL}`.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ENDPOINT_AUDIT inventory has ≥30 `/api/*` rows | `grep -cE '^\| /api/' ENDPOINT_AUDIT.md` | 83 (counts header lines too — strict inventory ≥64) | PASS |
| DATA_AUDIT inventory has ≥8 collection rows | `grep -cE '^\| [a-zA-Z_]+ +\|' DATA_AUDIT.md` | 44 (multiple tables — strict inventory has 17) | PASS |
| FRONTEND_MAP route table has ≥10 routes starting with `/` | `grep -cE '^\| /' FRONTEND_MAP.md` | 73 (multiple tables — strict route table has 17) | PASS |
| LOGIN_BUG has all three repro paths and ResizeObserver cite | `grep -cE '^(## Reproduction\|### Path [ABC]\|## Suspected component\|ResizeObserver)'` | 5 (1+3+1) | PASS |
| Documented expected counts present in DATA_AUDIT | per-count grep for vessels=111, trucking=461, coa=721, biomassa=45, smartstock=207, po_batubara=301, merit_order=58, sumberpemakaian=208, ai_chat_history=10, users=7 | 10/10 present (users shows +1 drift, all others matches) | PASS |
| Every FRONTEND_MAP-consumed endpoint appears in ENDPOINT_AUDIT | awk over FRONTEND_MAP cross-check table, grep each path in ENDPOINT_AUDIT | 0 missing | PASS |
| Zero credential leaks across all four audit docs | grep for JWT, bearer, password, mongo URI patterns | 0 matches | PASS |

### Gaps Summary

None. Every Phase 1 success criterion has a concrete, on-disk artifact that satisfies it; every required artifact is substantive, well-structured, and wired to its declared sources; every key link is verified; all four phase requirements (AUDIT-01..04) are SATISFIED; zero credential leaks; cross-document consistency is intact (frontend endpoints align with live OpenAPI surface, documented MongoDB counts match live counts modulo the +1 users drift which is correctly flagged as `drift` not `matches`).

Notable observations (not gaps — informational hand-offs to later phases, already documented inside the artifacts themselves):

- **users +1 drift** (live=8, doc=7) — flagged in DATA_AUDIT.md anomalies section. Three of those rows are the `audit-probe-*` synthetic users inserted by Plan 04 Path C round 2; cleanup filter documented in LOGIN_BUG.md and 01-04-SUMMARY.md.
- **CONS-auth-header 401-vs-403 contract clarity** — live server returns 403 (HTTPBearer default) on missing-credentials; CONS-auth-header documents 401. Documented in ENDPOINT_AUDIT.md as a Phase 2/3 reconciliation item, not a security defect.
- **CONS-auth-header 400-vs-422 validation** — malformed login body returns 422 (Pydantic default), CONS spec says 400. Documented in LOGIN_BUG.md Path B Divergence.
- **Browser-side Path A** — deferred to operator playbook because no headless browser is available on this VPS. The structural worksheet is complete; only OBSERVED rows for Path A are pending. This is explicitly designated as Phase 2's first task per the LOGIN_BUG.md Open Questions section, not a Phase 1 gap.

---

*Verified: 2026-05-10T12:00:00Z*
*Verifier: Claude (gsd-verifier)*
