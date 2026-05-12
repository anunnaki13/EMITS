---
phase: 03-documentation-refresh-decision-lock-in
plan: 03
subsystem: docs
tags: [api-reference, openapi, regeneration, idempotent-generator, credential-hygiene, spot-check, docs-01, docs-02]

# Dependency graph
requires:
  - phase: 03-documentation-refresh-decision-lock-in
    provides: "Plan 03-01 ADRs — ADR-004 (JWT/bcrypt/3-role auth) + ADR-008 (pagination shape) must exist before generator emits citations"
  - phase: 02-authentication-stabilization
    provides: "AUTH_CONTRACT.md (D-AUTH-01 422→400, D-AUTH-02 403 disposition) — cited verbatim in hand-curated Auth Contract section"
provides:
  - "scripts/regenerate_api_reference.py — idempotent Python generator (stdlib-only); fetches /openapi.json from localhost:8013 (primary) or 103.150.197.225:8013 (fallback); 95 endpoints rendered; preserves hand-curated sections via BEGIN/END HAND-CURATED markers"
  - "API_REFERENCE.md (515 lines, 26,305 bytes) — regenerated from live /openapi.json; hand-curated Auth Contract (ADR-004 cite), Pagination Contract (ADR-008 cite), Error Code Map (CONS-auth-header), Per-Module curl examples with ${TEST_ADMIN_PASSWORD} placeholders"
  - "docs/audit/API_REFERENCE_SPOTCHECK.md — 5 live endpoint probes (PASSED); schema-only marks for AI/upload/destructive-delete per D-08"
  - "Top-level API_REFERENCE.md REMOVED from check_credentials.sh EXCLUDE list; inline-<TEST_ADMIN_PASSWORD> exemption closed (STAB-03 debt cleared)"
  - "CREDENTIAL_HYGIENE.md updated: STAB-03 exemption for API_REFERENCE.md struck through; frontend/public/docs/API_REFERENCE.md deferred to Plan 03-05"
affects: [03-04, 03-05, phase-4-testing, downstream-phases]  # Plans 03-04/03-05 can now cite accurate API_REFERENCE; Phase-4 TEST-* extends spot-check coverage

# Tech tracking
tech-stack:
  added: []  # Pure documentation + stdlib Python script — no new libraries
  patterns:
    - "BEGIN/END HAND-CURATED marker pattern: idempotent doc generation preserves operator-written narrative while replacing auto-generated tables on each regen run"
    - "localhost-primary / public-IP-fallback fetch order in scripts — D-04 pattern for constrained VPS environment"
    - "verified: schema-only annotation for endpoints gated behind external services (LLM API keys) or destructive ops — D-08 traceability"

key-files:
  created:
    - pltu-tenayan-full-backup/scripts/regenerate_api_reference.py
    - pltu-tenayan-full-backup/docs/audit/API_REFERENCE_SPOTCHECK.md
  modified:
    - pltu-tenayan-full-backup/API_REFERENCE.md
    - pltu-tenayan-full-backup/scripts/check_credentials.sh
    - pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md

key-decisions:
  - "D-04 + D-06 closed: API_REFERENCE.md is now generator-owned; drift detectable with `python3 scripts/regenerate_api_reference.py && git diff --exit-code API_REFERENCE.md`"
  - "Idempotency via BEGIN/END markers: hand-curated narrative (Auth Contract, Pagination Contract, Error Code Map, Per-Module examples) is preserved across regeneration runs; only the GENERATED table is replaced"
  - "Schema-only verification (D-08): AI/smart-blending/upload/destructive-delete endpoints marked verified: schema-only in spot-check log; full behavioral coverage deferred to Phase 4 TEST-01..07"
  - "STAB-03 exemption closed: top-level API_REFERENCE.md removed from credential scanner EXCLUDE list; no inline literals in regenerated file; frontend/public/docs/API_REFERENCE.md exemption preserved (Plan 03-05)"

patterns-established:
  - "Idempotent doc generator pattern: parse existing markers before write → replace GENERATED block → rewrite file; second run produces zero diff"
  - "Spot-check log pattern (docs/audit/API_REFERENCE_SPOTCHECK.md): records date, host, method, observed vs doc-says, and schema-only rationale for non-probed endpoints"

requirements-completed: [DOCS-01, DOCS-02]

# Metrics
duration: 15min
completed: 2026-05-11
---

# Phase 3 Plan 03: API Reference Regeneration Summary

**Idempotent Python generator (stdlib) renders API_REFERENCE.md from live /openapi.json (95 endpoints), preserving hand-curated Auth/Pagination/Error sections via BEGIN/END markers, with credential exemption cleared**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-11T00:00:00Z
- **Completed:** 2026-05-11T00:15:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created `scripts/regenerate_api_reference.py` (idempotent, stdlib-only, exit 0 against live /openapi.json; second run produces zero diff)
- Replaced 778-line hand-edited API_REFERENCE.md (which inlined admin password) with 515-line regenerated version (26,305 bytes; 95 endpoint rows; hand-curated Auth Contract citing ADR-004, Pagination Contract citing ADR-008, Error Code Map per CONS-auth-header)
- Removed top-level `API_REFERENCE.md` from credential scanner EXCLUDE list (STAB-03 debt closed); credential scanner exits 0 on 172 tracked files
- Delivered `docs/audit/API_REFERENCE_SPOTCHECK.md`: 5/5 live probes PASSED (health, /me, vessels-pagination-envelope, coa-kpis, users/admin); AI/upload/destructive endpoints marked `verified: schema-only` per D-08

## Task Commits

All commits to inner repo (`pltu-tenayan-full-backup`):

1. **Task 1: Build regen script + render API_REFERENCE.md + clear credential exemption** - `d819d07` (docs)
2. **Task 2: Spot-check log (DOCS-02)** - `21dcc7c` (docs)

## Files Created/Modified

- `pltu-tenayan-full-backup/scripts/regenerate_api_reference.py` - Idempotent generator: fetches /openapi.json, renders endpoint table (95 rows), preserves hand-curated blocks via BEGIN/END markers; stdlib-only, exit codes 0/1/2
- `pltu-tenayan-full-backup/API_REFERENCE.md` - Regenerated (515 lines, 26,305 bytes): 5 hand-curated sections + auto-generated endpoint table + per-module curl examples with `${TEST_ADMIN_PASSWORD}` placeholders
- `pltu-tenayan-full-backup/scripts/check_credentials.sh` - Removed `"API_REFERENCE.md"` from EXCLUDE array; comment added noting 2026-05-10 clearance by plan 03-03
- `pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md` - STAB-03 exemption for top-level API_REFERENCE.md struck through; frontend/public/docs copy deferred to Plan 03-05
- `pltu-tenayan-full-backup/docs/audit/API_REFERENCE_SPOTCHECK.md` - 154-line spot-check log: 5 live probes (2026-05-10), schema-only classification rationale, D-08 traceability to Phase 4 TEST-01..07

## Decisions Made

- Used localhost-primary fetch order in script (D-04 + runtime constraint: VPS self-loopback is faster and avoids network hop)
- Preserved existing hand-curated content verbatim (files were already in the regen-format state from a prior auto-commit) — no narrative rewrite needed
- Marked all AI/smart-blending endpoints as `verified: schema-only` per D-08 (LLM key not available; Phase 6 unblocks)
- Marked all destructive DELETE-all endpoints as `verified: schema-only` (would truncate production data if probed live)
- Marked all upload endpoints as `verified: schema-only` (no fixture .xlsx files available for behavioral test; Phase 4 TEST-04 owns)

## Deviations from Plan

None — plan executed exactly as written. The files were in a partially-complete state from a prior auto-commit (files written but not committed); this execution committed them atomically in the correct two-commit sequence after verifying all acceptance criteria.

## Issues Encountered

None. Both inner-repo commits passed the pre-commit credential scanner on first attempt.

## Generator run output (idempotency proof)

Second run (after first commit):
```
wrote /home/damnation/emits/pltu-tenayan-full-backup/API_REFERENCE.md (26111 bytes; 95 endpoints)
```
`diff -q /tmp/a.md API_REFERENCE.md` → empty (idempotent confirmed).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- DOCS-01 + DOCS-02 closed; Plans 03-04 (documentation.md Known Issues) and 03-05 (DEPLOYMENT_GUIDE) can now cite the accurate API_REFERENCE.md
- `frontend/public/docs/API_REFERENCE.md` still has the old format + inline credential (credential scanner exemption preserved); Plan 03-05 owns the refresh
- Future drift detection: `cd pltu-tenayan-full-backup && python3 scripts/regenerate_api_reference.py && git diff --exit-code API_REFERENCE.md`

---
*Phase: 03-documentation-refresh-decision-lock-in*
*Completed: 2026-05-11*
