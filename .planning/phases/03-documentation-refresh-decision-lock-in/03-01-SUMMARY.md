---
phase: 03-documentation-refresh-decision-lock-in
plan: 01
subsystem: docs
tags: [adr, madr, decision-records, documentation, mongodb, fastapi, react, jwt, gemini, pagination]

# Dependency graph
requires:
  - phase: 02-authentication-stabilization
    provides: AUTH_CONTRACT.md (D-AUTH-01, D-AUTH-02) — referenced by ADR-004 as Phase-2 reconciliation source-of-truth
provides:
  - 8 locked ADR files at .planning/decisions/ADR-001..008-*.md (MADR layout, Status/Context/Decision/Consequences/Alternatives/References)
  - Authoritative anchor for IMPLICIT-001..008 — future plans cite ADR-NNN paths instead of re-deriving from PROJECT.md text
  - Code-anchor proofs (file:line) per ADR documenting where each decision is in effect today
  - Cross-link from ADR-004 to docs/audit/AUTH_CONTRACT.md
affects: [03-02, 03-03, 03-04, 03-05, downstream-phases]  # Phase-3 plans 02-05 cite ADR paths; future phases inherit the locked decisions.

# Tech tracking
tech-stack:
  added: []  # Pure documentation plan — no new libraries.
  patterns:
    - "MADR-format ADR layout (Status/Context/Decision/Consequences/Alternatives/References) — adopted as the project's ADR template"
    - "Locked-status header literal: 'Accepted (locked, YYYY-MM-DD) — promoted from IMPLICIT-NNN'"
    - "References-section policy: every ADR cites (a) source IMPLICIT line, (b) ≥1 code anchor file:line, (c) related CONS-* constraint"

key-files:
  created:
    - .planning/decisions/ADR-001-mongodb-datastore.md
    - .planning/decisions/ADR-002-fastapi-python-backend.md
    - .planning/decisions/ADR-003-react-frontend-stack.md
    - .planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md
    - .planning/decisions/ADR-005-gemini-via-emergentintegrations.md
    - .planning/decisions/ADR-006-api-prefix-and-frontend-base-url.md
    - .planning/decisions/ADR-007-persistence-projection-uuid-iso.md
    - .planning/decisions/ADR-008-pagination-shape.md
  modified: []

key-decisions:
  - "ADR-001 locks MongoDB-via-Motor as the v1 primary datastore; alternative datastores (Postgres / SQLite / split) rejected at current row counts"
  - "ADR-002 locks FastAPI 0.110.x on Python 3.11+ as the backend framework; OpenAPI generation feeds Phase-3 plan-03 API_REFERENCE regeneration (D-04)"
  - "ADR-003 locks React 19 + React Router 7 + Tailwind + Shadcn/UI (vendored Radix); AUTHFIX-04 carries the Radix Select ResizeObserver evaluation forward"
  - "ADR-004 locks JWT (HS256, 24h) + bcrypt + admin/operator/viewer; HTTP error map 400/401/403/404/500 reconciled per Phase-2 D-AUTH-01 / D-AUTH-02; cross-link to AUTH_CONTRACT.md"
  - "ADR-005 locks Google Gemini (gemini-2.5-flash) via emergentintegrations as v1 LLM provider; BudgetExceededError documented as environmental, not code defect"
  - "ADR-006 locks /api/* prefix on backend + REACT_APP_BACKEND_URL on frontend; no /api/v1 versioning in v1"
  - "ADR-007 locks Mongo {_id: 0} projection + uuid.uuid4() id field + ISO 8601 datetimes"
  - "ADR-008 locks pagination envelope {items, total, page, page_size, total_pages}; default page=1, page_size=50; caps 500 / 50000"

patterns-established:
  - "ADR file naming: kebab-case slug derived from IMPLICIT subject (e.g., ADR-NNN-<short-slug>.md); 3-digit zero-padded numbering"
  - "ADR References section structure: Source IMPLICIT line → Code anchors (file:line bullet list) → Related constraints (CONS-* bullet list) → Sibling docs"
  - "ADR Consequences split into Positive / Negative-or-accepted-tradeoffs bullet groups (per CONTEXT.md D-01 implicit guidance, surfaced in plan template)"

requirements-completed: [DOCS-04, STAB-04]

# Metrics
duration: ~25min
completed: 2026-05-10
---

# Phase 03 Plan 01: ADR Lock-In Summary

**Eight MADR-format ADR files promote IMPLICIT-001..008 to locked, code-anchored architectural decisions — first authoritative ADR set for EMITS, used by downstream Phase-3 plans (API_REFERENCE regen, PROJECT.md cross-link) instead of re-deriving from PROJECT.md text.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-10T14:25:00Z (approx — plan execution kickoff)
- **Completed:** 2026-05-10T14:49:57Z
- **Tasks:** 3 / 3
- **Files created:** 8 (all ADR files in `.planning/decisions/`)
- **Files modified:** 0 (pure new-file additions)

## Accomplishments

- `.planning/decisions/` directory created and populated with the project's first 8 locked ADRs
- Each ADR uses the full MADR layout (Status / Context / Decision / Consequences / Alternatives Considered / References) per D-01
- Each Status line is the literal D-02 form: `Accepted (locked, 2026-05-10) — promoted from IMPLICIT-NNN.`
- Each References section cites the source IMPLICIT line in PROJECT.md, at least one code anchor (`file:line`), and the related CONS-* constraint when applicable — per D-03
- ADR-004 cross-links `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` (Phase-2 D-AUTH-01 / D-AUTH-02 reconciliation)
- ADR-005 explicitly documents the BudgetExceededError as environmental, not a code defect (Consequences/Negative section)
- ADR-008 includes a verbatim 6-line snippet of the canonical pagination return shape from `backend/server.py:716-722`
- DOCS-04 + STAB-04 requirements are now testably-true (8 ADR files exist, each with locked status + code anchors)

## IMPLICIT → ADR Mapping

| ADR | Subject | Source IMPLICIT (PROJECT.md) | Primary code anchor | CONS-* link |
|-----|---------|------------------------------|---------------------|-------------|
| ADR-001 | MongoDB (via Motor) as Primary Datastore | IMPLICIT-001 (PROJECT.md L89) | `backend/server.py:7,28` (Motor import + AsyncIOMotorClient init) | CONS-collection-inventory, CONS-collection-naming-debt |
| ADR-002 | FastAPI on Python 3.11+ as Backend Stack | IMPLICIT-002 (PROJECT.md L87) | `backend/server.py:1,37` + `backend/requirements.txt` (fastapi 0.110.1, bcrypt, motor, pandas, openpyxl, xlrd, reportlab) | — |
| ADR-003 | React 19 + Router 7 + Tailwind + Shadcn/UI | IMPLICIT-003 (PROJECT.md L88) | `frontend/package.json` (react ^19, react-router-dom ^7.5.1, @radix-ui/react-select ^2.2.2, tailwind, axios, recharts, jspdf, xlsx) | — |
| ADR-004 | JWT + bcrypt + 3-role Auth Model | IMPLICIT-004 (PROJECT.md L90) | `backend/server.py:15-16,45-56,577,586-597,599-604` | CONS-auth-header |
| ADR-005 | Gemini via emergentintegrations as v1 AI Provider | IMPLICIT-005 (PROJECT.md L94) | `backend/server.py:19,2260-2261,2619` + `backend/requirements.txt:20,33,34` | CONS-ai-query-endpoint, CONS-smart-blending-endpoint (operational note) |
| ADR-006 | /api/* Prefix + REACT_APP_BACKEND_URL | IMPLICIT-006 (PROJECT.md L91) | `backend/server.py:60` + `frontend/src/contexts/AuthContext.js:6` | CONS-api-base |
| ADR-007 | Projection {_id:0} + UUID id + ISO 8601 | IMPLICIT-007 (PROJECT.md L92) | `backend/server.py:13,14,590,614,714,726` | CONS-projection-id-contract |
| ADR-008 | Pagination Envelope {items,total,page,page_size,total_pages} | IMPLICIT-008 (PROJECT.md L93) | `backend/server.py:685-722` (verbatim snippet 716-722) | CONS-pagination-shape, CONS-smart-stock-endpoint, CONS-coa-reconciliation-endpoint |

## Task Commits

This plan is structurally **one atomic commit for all 8 ADR files** (per Task 3 in the plan: "Single commit on outer repo `main` containing all 8 ADR files"). Tasks 1 and 2 wrote files but deferred staging to Task 3.

1. **Task 1: Write ADR-001..004** — files written, no commit (per plan)
2. **Task 2: Write ADR-005..008** — files written, no commit (per plan)
3. **Task 3: Atomic commit of all 8 ADR files** — `f6f3ab3` (`docs(phase-3): promote IMPLICIT-001..008 to locked ADRs (DOCS-04, STAB-04)`)

**Plan metadata commit:** will be recorded by orchestrator after this SUMMARY.md + STATE.md updates land (separate commit per execute-plan protocol).

## Files Created/Modified

- `.planning/decisions/ADR-001-mongodb-datastore.md` — Locks MongoDB-via-Motor as primary datastore (v1)
- `.planning/decisions/ADR-002-fastapi-python-backend.md` — Locks FastAPI 0.110.x on Python 3.11+ + supporting library set
- `.planning/decisions/ADR-003-react-frontend-stack.md` — Locks React 19 + Router 7 + Tailwind + Shadcn/UI (vendored Radix), CRA + craco + Yarn
- `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md` — Locks JWT (HS256, 24h) + bcrypt + admin/operator/viewer + 400/401/403/404/500 error map; cross-links AUTH_CONTRACT.md
- `.planning/decisions/ADR-005-gemini-via-emergentintegrations.md` — Locks Gemini-2.5-flash via emergentintegrations as v1 LLM provider; BudgetExceededError documented as environmental
- `.planning/decisions/ADR-006-api-prefix-and-frontend-base-url.md` — Locks `/api/*` backend prefix + `REACT_APP_BACKEND_URL` frontend base
- `.planning/decisions/ADR-007-persistence-projection-uuid-iso.md` — Locks `{_id:0}` Mongo projection + `uuid.uuid4()` id + ISO 8601 datetimes + audit metadata field names
- `.planning/decisions/ADR-008-pagination-shape.md` — Locks `{items, total, page, page_size, total_pages}` envelope; default page=1, page_size=50; caps 500 / 50000 (smart-stock)

## Decisions Made

All ADR-internal decisions (Decision-section content, Alternatives Considered selections) are documented per-ADR. No execution-time architectural decisions outside the plan; the plan specified each ADR's slug, decision text, anchor map, and rejection rationales.

One non-architectural execution decision: **the plan structures all 8 files as a single atomic commit (per Task 3 wording)**, so I deferred staging in Tasks 1 and 2 even though the GSD per-task-commit protocol normally calls for one commit per task. The plan is explicit ("Do not commit yet — Task 3 commits all 8 files together") and follows the documented atomic-commit acceptance criterion. This matches Phase-2's "atomic per-task commits" pattern at the *plan* granularity rather than the *task* granularity for this specific shape of work.

## Code-Anchor Drift Notes (plan-time vs execute-time)

The plan listed code anchors against `backend/server.py` line numbers. At execute time, all anchors verified accurate against the live file:

- `server.py:7` — `from motor.motor_asyncio import AsyncIOMotorClient` ✓
- `server.py:28` — `client = AsyncIOMotorClient(mongo_url)` ✓
- `server.py:60` — `api_router = APIRouter(prefix="/api")` ✓
- `server.py:577` — `def create_token(...)` ✓
- `server.py:599` — `def require_role(...)` ✓
- `server.py:15-16` — `import jwt` + `import bcrypt` ✓
- `server.py:19` — `from emergentintegrations.llm.chat import LlmChat, UserMessage` ✓
- `server.py:714` — `db.vessels.find(query, {"_id": 0}).sort(...)` ✓
- `server.py:716-722` — pagination return shape ✓ (snippet copied verbatim into ADR-008)

**One drift item documented in ADR-005 (intentional, not a defect):** the plan suggested citing a `backend/services/` AI wiring file. Actual `services/` directory contains `coa_reconciliation.py` + `excel_parser.py` only — there is no dedicated AI service module today. AI wiring lives at `server.py:19` (top-level import) and `server.py:2260-2261` (in-file section header). ADR-005 documents this drift in the Code Anchors section as a forward note: "a future plan may introduce `services/ai_intelligence.py` to host the `LlmChat` instantiation."

## Deviations from Plan

None - plan executed exactly as written. All 3 tasks completed per their `<action>` and `<verify>` blocks; all `<acceptance_criteria>` met.

## Issues Encountered

None. Code anchors all verified accurate; one expected drift documented in ADR-005 (no `services/ai_intelligence.py` module today; not a regression).

## User Setup Required

None - this plan is pure documentation; no environment variables, no external service configuration.

## Next Phase Readiness

- ✓ ADR-001..008 ready for citation by Phase-3 plans 02-05 (API_REFERENCE generator can cite ADR-006/007/008; PROJECT.md cross-link plan can replace IMPLICIT-NNN references with ADR-NNN paths).
- ✓ DOCS-04 + STAB-04 requirements ready to be marked complete in REQUIREMENTS.md.
- ✓ Future planning rounds and contributors have a stable, code-anchored decision set instead of re-deriving from PROJECT.md text.

## Self-Check: PASSED

**File existence:**

- FOUND: .planning/decisions/ADR-001-mongodb-datastore.md
- FOUND: .planning/decisions/ADR-002-fastapi-python-backend.md
- FOUND: .planning/decisions/ADR-003-react-frontend-stack.md
- FOUND: .planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md
- FOUND: .planning/decisions/ADR-005-gemini-via-emergentintegrations.md
- FOUND: .planning/decisions/ADR-006-api-prefix-and-frontend-base-url.md
- FOUND: .planning/decisions/ADR-007-persistence-projection-uuid-iso.md
- FOUND: .planning/decisions/ADR-008-pagination-shape.md

**Commit existence:** FOUND: f6f3ab3 (`docs(phase-3): promote IMPLICIT-001..008 to locked ADRs (DOCS-04, STAB-04)`)

**MADR-heading + locked-status check:** PASS for all 8 files (verified by Tasks 1 + 2 `<verify>` automation, re-verified post-commit).

---
*Phase: 03-documentation-refresh-decision-lock-in*
*Completed: 2026-05-10*
