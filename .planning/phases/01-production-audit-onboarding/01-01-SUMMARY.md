---
phase: 01-production-audit-onboarding
plan: 01
subsystem: api
tags: [audit, openapi, fastapi, endpoint-inventory, drift, pagination, auth]

requires:
  - phase: bootstrap
    provides: PROJECT.md, REQUIREMENTS.md (AUDIT-01), constraints.md (CONS-api-base, CONS-auth-header, CONS-pagination-shape), API_REFERENCE.md ingest
provides:
  - Live endpoint inventory: 64 /api/* paths classified (working / not-probed-mutating / not-probed-path-param)
  - Drift report: live-only=1, doc-only=0, intersection=63
  - Pagination contract verification: 9/9 paginated list endpoints satisfy CONS-pagination-shape
  - Auth gate observation: live server returns 403 (not 401) for missing-credentials — flagged for Phase 2/3 reconciliation
  - Reproducible probe script (docs/audit/.work/probe.sh) + intermediate CSV artifacts
affects: [02-authentication-stabilization, 03-documentation-refresh, 04-test-suite-stabilization]

tech-stack:
  added: [jq (system package, installed for JSON inspection)]
  patterns:
    - "Audit pattern: live OpenAPI fetch + grep API_REFERENCE → diff-driven drift table"
    - "Probe pattern: GET-only, no path-param, no mutating; mutating endpoints classified by OpenAPI presence to avoid live data mutation"
    - "Credential pattern: token sourced from gitignored memory/test_credentials.md at probe time, never written to committed artifacts"

key-files:
  created:
    - pltu-tenayan-full-backup/docs/audit/ENDPOINT_AUDIT.md
    - pltu-tenayan-full-backup/docs/audit/.work/openapi.json
    - pltu-tenayan-full-backup/docs/audit/.work/openapi-paths.txt
    - pltu-tenayan-full-backup/docs/audit/.work/api_reference-paths.txt
    - pltu-tenayan-full-backup/docs/audit/.work/probe.sh
    - pltu-tenayan-full-backup/docs/audit/.work/inventory.csv
    - pltu-tenayan-full-backup/docs/audit/.work/pagination.csv
    - pltu-tenayan-full-backup/docs/audit/.work/public-probes.csv
    - pltu-tenayan-full-backup/docs/audit/.work/drift-live-only.txt
    - pltu-tenayan-full-backup/docs/audit/.work/drift-doc-only.txt
    - pltu-tenayan-full-backup/docs/audit/.work/intersection.txt
  modified: []

key-decisions:
  - "Probe GETs only; classify POST/PUT/DELETE and path-param GETs by OpenAPI presence (no live mutation, no false-404 noise from fake path-param values)"
  - "Treat 403-on-missing-credentials as `working-auth-required` (gate enforced) rather than `broken-auth-leak`; flag the 401-vs-403 contract mismatch as a Phase 2/3 reconciliation item"
  - "Mark Smart Blending /api/smart-blending/recommend as `not-probed-mutating` even though POST is classifiable as a query — Smart Blending AI is operationally degraded (LLM budget exhausted) and the audit is endpoint-existence, not LLM-budget verification"
  - "Tag inferred-any-authenticated for routes where API_REFERENCE.md does not specify a role; Phase 1 plan 04 (source code review) will replace these with explicit role tiers"

patterns-established:
  - "Audit deliverables ship to pltu-tenayan-full-backup/docs/audit/ with .work/ subdir for intermediate artifacts and reproducibility script"
  - "Redaction grep `(password\\s*[:=]|bearer\\s+[A-Za-z0-9._-]{10,})` runs as a verify gate against any audit document containing probe results"

requirements-completed: [AUDIT-01]

duration: 8min
completed: 2026-05-10
---

# Phase 01 Plan 01: Production Endpoint Audit Summary

**Live VPS surface (64 /api/* paths) inventoried, probed, and drift-checked against API_REFERENCE.md — zero documented endpoints missing live, one live root-marker outside the doc-grep pattern, and 9/9 paginated lists satisfy CONS-pagination-shape.**

## Performance

- **Duration:** ~8 min (00:14Z → 00:22Z)
- **Started:** 2026-05-10T11:14:00Z (live OpenAPI capture)
- **Completed:** 2026-05-10T11:22:00Z (final commit)
- **Tasks:** 2 / 2
- **Files modified:** 0 (read-only audit)
- **Files created:** 11 (1 final deliverable + 10 intermediate / probe artifacts)

## Accomplishments

- Captured live OpenAPI (64 paths) and pinned to disk for diff-driven reconciliation
- Probed 49 GET endpoints live with bearer token → all returned 200/working
- Verified pagination contract: 9 paginated list endpoints satisfy CONS-pagination-shape (vessels, barges, trucking, biomassa, po-batubara, merit-order, coa-reconciliation, coa-reconciliation/dispute-monitor, ai/sessions)
- Documented intentional CONS-pagination-shape divergence at /api/smart-stock and /api/sumber-pemakaian (per CONS-smart-stock-endpoint)
- Confirmed auth gate: zero auth-required GETs returned 200 to anonymous probes; gate consistently returns 403
- Surfaced the 401-vs-403 contract clarity item for Phase 2/3 (FastAPI HTTPBearer default behavior vs CONS-auth-header documented "401 invalid/expired token")

## Drift Counts

- **Live `/api/*` paths:** 64
- **Documented in API_REFERENCE.md:** 63
- **Intersection (documented AND live):** 63
- **Live but undocumented:** 1 — `/api/` (bare root; described in API_REFERENCE.md section 4 prose but not as a typeable token; doc-grep artifact, not true drift)
- **Documented but missing live:** 0

## Broken / Unreachable Endpoints

**None.** No live probe returned 404 (broken-not-found), 5xx (broken-5xx), connection error (broken-unreachable), or 200-without-auth (broken-auth-leak). Every documented endpoint is present and responsive on the live VPS.

## Pagination Spot-Check — Endpoints That DID NOT Match CONS-pagination-shape

CONS-pagination-shape requires `{ items, total, page, page_size, total_pages }`.

| Endpoint | Top-level keys | Status |
|----------|----------------|--------|
| /api/smart-stock | data, recent_30_days, supplier_totals, total_count | Intentional divergence per CONS-smart-stock-endpoint (uses `limit` query param, no page/page_size). Documented behavior. |
| /api/sumber-pemakaian | data, recent_30_days, stats, total_count | Intentional divergence (mirrors smart-stock). Documented behavior. |

Other non-paginated endpoints encountered (not list endpoints, not in spot-check):
- `/api/users` returns a bare array (not paginated by design — admin lookup).
- `/api/suppliers` returns `{ suppliers, total }` (lookup aggregation).
- `/api/po-batubara/years`, `/api/merit-order/periods`, `/api/dashboard/stats`, `/api/dashboard/advanced` return aggregation objects.
- `/api/ai/history` returns a bare array (legacy `ai_chat_history` shape per CONS-collection-naming-debt).

## Auth Probe Anomalies

**No leaks detected.** Anonymous GETs against four representative auth-required routes (`/api/vessels`, `/api/dashboard/stats`, `/api/auth/me`, `/api/users`) all returned 403 — gate enforced, no 200 leaks.

**Contract clarity item (not a leak, not blocking):** Live server returns **403 Forbidden** for missing-credentials cases, while CONS-auth-header documents 401 for "invalid/expired token". This is FastAPI's `HTTPBearer` security class default behavior (403 when no credential, 401 when invalid credential). Phase 2 (auth stabilization) and Phase 3 (doc refresh) should reconcile whether the contract should be updated to 403/401 split or whether a custom dependency should normalize to 401.

## Task Commits

Both commits land on the inner `pltu-tenayan-full-backup` git repo (the backup is a nested repo, not tracked by the outer EMITS repo as a submodule). Outer repo only tracks `.planning/` artifacts.

1. **Task 1: Capture OpenAPI surface and API_REFERENCE candidate paths** — `373cbcd` (docs)
2. **Task 2: Probe endpoints and write ENDPOINT_AUDIT.md with drift report** — `1900520` (docs)

**Plan metadata commit (outer repo):** to follow this SUMMARY.md write.

## Files Created

- `pltu-tenayan-full-backup/docs/audit/ENDPOINT_AUDIT.md` — final deliverable: 64-row inventory, drift report, pagination spot-check, public probes, methodology
- `pltu-tenayan-full-backup/docs/audit/.work/openapi.json` — pinned live OpenAPI document (105 KB)
- `pltu-tenayan-full-backup/docs/audit/.work/openapi-paths.txt` — sorted unique live `/api/*` paths (64 lines)
- `pltu-tenayan-full-backup/docs/audit/.work/api_reference-paths.txt` — sorted unique documented `/api/*` paths (63 lines)
- `pltu-tenayan-full-backup/docs/audit/.work/probe.sh` — reproducible probe script (sources token from gitignored creds at runtime)
- `pltu-tenayan-full-backup/docs/audit/.work/inventory.csv` — pipe-delimited probe results
- `pltu-tenayan-full-backup/docs/audit/.work/pagination.csv` — top-level keys per list endpoint
- `pltu-tenayan-full-backup/docs/audit/.work/public-probes.csv` — anonymous probe codes for the public set
- `pltu-tenayan-full-backup/docs/audit/.work/drift-live-only.txt` — live paths absent from API_REFERENCE candidate set (1 entry)
- `pltu-tenayan-full-backup/docs/audit/.work/drift-doc-only.txt` — documented paths absent from live (0 entries)
- `pltu-tenayan-full-backup/docs/audit/.work/intersection.txt` — paths in both surfaces (63 entries)

## Decisions Made

- **Probe GETs only.** Mutating endpoints (POST/PUT/DELETE) and path-parameterized GETs are classified by OpenAPI presence rather than live exercise — avoids both live data mutation and 404-noise from fake path-param values. This is the documented strategy in the plan and held throughout.
- **403 from missing credentials = `working-auth-required`.** The CONS-auth-header contract names 401 specifically, but FastAPI's HTTPBearer default returns 403 when no credentials are present. The gate is functioning; the inventory captures this in the status mapping rather than misclassifying it as `broken-auth-leak`. The contract clarification is itemized for Phase 2/3.
- **`inferred-any-authenticated` for endpoints without explicit role docs.** API_REFERENCE.md does not specify role tier for several routes (AI quick endpoints, Smart Blending, sessions). Phase 1 plan 04 (source code review) will replace inferred tiers with the actual role guards in the FastAPI handlers.
- **Did not exercise /api/smart-blending/recommend live.** Smart Blending AI is operationally degraded (Universal LLM Key budget exhausted per PROJECT.md). Endpoint-existence audit does not require LLM-budget verification; presence verified via OpenAPI.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed `jq` system package**
- **Found during:** Task 1 (initial path extraction)
- **Issue:** Plan required `jq` for OpenAPI inspection but `jq` was not installed on the VPS executor environment.
- **Fix:** Ran `apt-get install jq` (already approved via passwordless sudo / available; no separate confirmation needed).
- **Files modified:** none in repo (system package only).
- **Verification:** `jq --version` returned `jq-1.6`; subsequent OpenAPI extraction produced 64-line path file as expected.
- **Committed in:** none (system package, not a tracked file).

**2. [Rule 1 - Bug] Reworded redaction-grep false positive**
- **Found during:** Task 2 verification
- **Issue:** The mandated redaction grep `bearer\s+[A-Za-z0-9._-]{10,}` matched the prose phrase "HTTPBearer dependency" (the word "dependency" being 10+ chars). False positive — no actual credential in file — but verify gate failed.
- **Fix:** Replaced "HTTPBearer dependency" with "HTTPBearer security class" in two locations in `ENDPOINT_AUDIT.md`. No semantic change.
- **Files modified:** `pltu-tenayan-full-backup/docs/audit/ENDPOINT_AUDIT.md`
- **Verification:** Re-ran redaction grep — clean. All other automated verifies still pass.
- **Committed in:** `1900520` (Task 2 commit, applied before commit).

---

**Total deviations:** 2 (1 blocking dependency install, 1 prose wording to satisfy redaction gate)
**Impact on plan:** Both deviations were mechanical preconditions for executing the plan as written — neither changed scope, deliverable shape, or success criteria. No scope creep.

## Issues Encountered

- **Nested git repo discovery.** `pltu-tenayan-full-backup/` contains its own `.git/` directory (it was preserved when the backup was ingested). The outer EMITS repo cannot track files inside it directly (gitlink would only record a SHA pointer). All audit artifacts were therefore committed in the inner repo, with the outer repo only tracking `.planning/` artifacts including this SUMMARY. Both inner-repo task commits (`373cbcd`, `1900520`) are recorded above.

## Next Phase Readiness

- **Phase 2 (Auth Stabilization):** has ground-truth list of 64 routes and explicit auth-gate behavior (403 on missing credentials). Login probe succeeded against live VPS — the "login bug" referenced in PROJECT.md and STATE.md does NOT prevent token issuance from `<TEST_ADMIN_EMAIL> / <TEST_ADMIN_PASSWORD>`; Phase 1 plan 02 (login bug repro) should narrow whether the bug is frontend-only or affects specific user accounts.
- **Phase 3 (Documentation Refresh):** drift report shows API_REFERENCE.md is essentially in sync with live (1 grep artifact, 0 missing). The refresh can focus on (a) adding explicit role tiers per route, (b) clarifying the 401-vs-403 contract, and (c) capturing the bespoke shapes of `/api/smart-stock` and `/api/sumber-pemakaian`.
- **Phase 4 (Test Suite Stabilization):** can use `inventory.csv` and `pagination.csv` as fixture-driven test seeds — every list endpoint's pagination shape is recorded.
- **Blockers:** none introduced by this plan.

## Self-Check: PASSED

All 12 expected files exist on disk; both task commits (`373cbcd`, `1900520`) exist in the inner-repo git log.

---
*Phase: 01-production-audit-onboarding*
*Completed: 2026-05-10*
