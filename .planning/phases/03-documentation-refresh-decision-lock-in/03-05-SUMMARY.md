---
phase: 03-documentation-refresh-decision-lock-in
plan: 05
subsystem: docs
tags: [database-schema, deployment-guide, credential-hygiene, blending-formula, schema-audit, docs-01, docs-03]

# Dependency graph
requires:
  - phase: 03-documentation-refresh-decision-lock-in
    provides: "Plan 03-02 VPS Service Recovery runbook in LOCAL_SETUP.md (cross-linked from DEPLOYMENT_GUIDE.md per D-11)"
  - phase: 03-documentation-refresh-decision-lock-in
    provides: "Plan 03-04 readme.md Known Issues pointer (must be preserved; no overlap edit)"
provides:
  - "DATABASE_SCHEMA.md 'Duplicate Pair Active Read Targets' section (Phase-3 audit, 2026-05-10) — 4-row determination table with code-line evidence; defers rename to Phase 5"
  - "DEPLOYMENT_GUIDE.md reconciled — no inline secrets, actual VPS posture documented (port 8013/3013), SERVICE RECOVERY cross-link to LOCAL_SETUP.md (D-11 reciprocal pointer)"
  - "scripts/check_credentials.sh — DEPLOYMENT_GUIDE.md exemption removed (now 14 exemptions, down from 15)"
  - "docs/audit/CREDENTIAL_HYGIENE.md — DEPLOYMENT_GUIDE.md exemption struck and documented as cleared 2026-05-10"
  - "frontend/public/docs/Smart_Blending_AI_Formula.md — Phase-3 verification stamp appended (NO DRIFT vs CONS-blending-formula)"
  - "docs/audit/SMART_BLENDING_FORMULA_AUDIT.md — new clause-by-clause audit log (26 clauses, all NO DRIFT)"
  - "readme.md — backend port corrected from 8001 to 8013; REACT_APP_BACKEND_URL note added; Plan 03-04 Known Issues pointer preserved"
affects: [phase-4-testing, phase-5-collection-naming-debt, phase-6-llm-budget]

# Tech tracking
tech-stack:
  added: []  # Pure documentation — no new libraries
  patterns:
    - "Phase-3 audit stamp pattern: appended '---' + Phase-3 verification block at end of formula doc; additive-only"
    - "Credential exemption clearance pattern: inline ${TEST_ADMIN_PASSWORD} / ${MONGO_URL} placeholders + comment citing source doc; remove from EXCLUDE array; strike in CREDENTIAL_HYGIENE.md"

key-files:
  created:
    - pltu-tenayan-full-backup/docs/audit/SMART_BLENDING_FORMULA_AUDIT.md
  modified:
    - pltu-tenayan-full-backup/DATABASE_SCHEMA.md
    - pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md
    - pltu-tenayan-full-backup/scripts/check_credentials.sh
    - pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md
    - pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
    - pltu-tenayan-full-backup/readme.md

key-decisions:
  - "Both-names-actively-read documented for 3 of 4 pairs (smartstock/smart_stock, sumberpemakaian/sumber_pemakaian, app_settings/settings) — the AI module reads the legacy names while CRUD reads the active names; Phase 5 must consolidate"
  - "DEPLOYMENT_GUIDE.md reconciles actual VPS posture as a callout at the top rather than overwriting all port references — the guide remains valid for fresh deployments choosing any port, while the actual production topology is clearly called out"
  - "Smart Blending formula audit outcome: NO DRIFT — additive stamp only; no content corrections needed"

patterns-established:
  - "Determination table pattern for duplicate collection pairs: Active (read target) | Legacy | Active count | Legacy count | Code evidence (file:line)"
  - "VPS posture callout pattern: add a 'Catatan: Postur VPS Produksi Saat Ini' note at the top of the relevant guide section rather than modifying all generic examples"

requirements-completed: [DOCS-01, DOCS-03]

# Metrics
duration: ~25min
completed: 2026-05-11
---

# Phase 03 Plan 05: DATABASE_SCHEMA audit + DEPLOYMENT_GUIDE reconciliation + Smart Blending verify — Summary

**DATABASE_SCHEMA.md gains a Phase-3 audit section naming active read targets for all 4 duplicate collection pairs (with code-line evidence); DEPLOYMENT_GUIDE.md secrets stripped + D-11 cross-link added; Smart_Blending_AI_Formula.md verified NO DRIFT against CONS-blending-formula; all work in one atomic inner-repo commit (a96ad39).**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-11
- **Completed:** 2026-05-11
- **Tasks:** 3 / 3
- **Files modified:** 7 (6 modified, 1 created)
- **Commits:** 1 inner-repo + 1 outer-repo (docs/state)

## Accomplishments

### Task 1: DATABASE_SCHEMA.md duplicate-pair active-target audit

Appended new H2 section `## Duplicate Pair Active Read Targets (Phase-3 audit, 2026-05-10)` with a 4-row determination table:

| Pair | Active | Legacy | Active count | Legacy count | Code evidence |
|------|--------|--------|--------------|--------------|---------------|
| smartstock vs smart_stock | **Both names actively read** (CRUD→smartstock, AI module→smart_stock) | N/A (Phase 5) | 207 | 0 | server.py:3100 (CRUD), server.py:2377 (AI) |
| sumberpemakaian vs sumber_pemakaian | **Both names actively read** (CRUD→sumberpemakaian, AI module→sumber_pemakaian) | N/A (Phase 5) | 208 | 0 | server.py:3374 (CRUD), server.py:2385 (AI) |
| app_settings vs settings | **Both names actively read** (settings endpoint→app_settings, COA export+AI→settings) | N/A (Phase 5) | 1 | 0 | server.py:3853 (settings endpoint), server.py:4382 (COA export), server.py:2425 (AI) |
| ai_chat_history vs ai_conversations | ai_chat_history | ai_conversations | 10 | 0 | server.py:2264 (module-level alias `ai_chat_collection = db.ai_chat_history`) |

**Key finding:** 3 of 4 pairs are BOTH actively read by different code paths. The CRUD module writes to one name; the AI intelligence module reads the other (legacy) name, getting 0 records. This silent data gap in the AI module is specifically flagged for Phase 5 resolution.

DATABASE_SCHEMA.md: 692 → 738 lines.

### Task 2: DEPLOYMENT_GUIDE.md reconciliation

- `DEPLOYMENT_GUIDE.md`:
  - Replaced `<TEST_ADMIN_PASSWORD>` literal (line 351) with `${TEST_ADMIN_PASSWORD}` placeholder + source comment
  - Replaced `${MONGO_URL}` (line 199) with `${MONGO_URL}` placeholder + ADR-001 topology note
  - Added "Catatan: Postur VPS Produksi Saat Ini" callout (port 8013 backend, port 3013 frontend, localhost:27017 MongoDB, prod REACT_APP_BACKEND_URL) after section 1 header
  - Added frontend `.env` examples for prod and dev local
  - Updated curl example URL to use actual prod URL `http://103.150.197.225:8013`
  - Added new H2 `## 21. Service Recovery (post-restart)` cross-linking `LOCAL_SETUP.md#vps-service-recovery-post-restart` (D-11 reciprocal pointer)
  - Final line count: 590 (> 540 min_lines requirement)
- `scripts/check_credentials.sh`: removed `"DEPLOYMENT_GUIDE.md"` from EXCLUDE array; added clearance comment noting 2026-05-10 by plan 03-05
- `docs/audit/CREDENTIAL_HYGIENE.md`: struck DEPLOYMENT_GUIDE.md exemption with clearance note; separated `frontend/public/docs/DEPLOYMENT_GUIDE.md` into its own bullet as still-deferred

Credential scanner: 15 exemptions → 14 exemptions (DEPLOYMENT_GUIDE.md cleared).

### Task 3: Smart_Blending_AI_Formula.md verification + audit log + readme verification

**Smart_Blending_AI_Formula.md:** Full clause-by-clause comparison against all CONS-blending-* constraints. Outcome: **NO DRIFT** — 26 clauses verified, all match. Appended Phase-3 verification stamp + operational status note (budget-exhausted caveat).

**SMART_BLENDING_FORMULA_AUDIT.md (new):** 26-row clause-by-clause table. Outcome: NO DRIFT. Operational caveat documents that the formula is correct but LLM budget is exhausted (Phase 6 unblocks). 75 lines.

**readme.md:**
- Corrected backend startup port from `8001` to `8013` (actual VPS port)
- Added production note: `REACT_APP_BACKEND_URL=http://localhost:8013` for dev local
- Preserved Plan 03-04 Known Issues pointer line (`> **Status terkini:**`) intact
- No other drift found (roles: admin/operator/viewer correct per ADR-004; features list accurate; tech stack correct)

## Task Commits

All files committed atomically to inner repo:

1. **Inner-repo atomic commit (Tasks 1-3)** — `a96ad39` (`docs(docs-01,docs-03): final reconciliation — schema audit, deploy guide cleanup, blending formula verify (D-11 reciprocal)`) — 7 files, inner `pltu-tenayan-full-backup` repo

## Live Verification Data

**MongoDB collection counts (2026-05-11):**
```
smartstock:       207  (active write target for CRUD)
smart_stock:        0  (AI module reads this — silent data gap)
sumberpemakaian:  208  (active write target for CRUD)
sumber_pemakaian:   0  (AI module reads this — silent data gap)
app_settings:       1  (settings endpoint reads/writes this)
settings:           0  (COA export + AI module reads this — silent data gap)
ai_chat_history:   10  (assigned at server.py:2264)
ai_conversations:   0  (unused)
```

**Credential scanner:** `OK: no tracked credential patterns found in 173 files (after 14 exemptions).`

## Smart Blending Formula Audit — Literal Outcome Line

`NO DRIFT — The formula doc matches all CONS-blending-* clauses exactly. No corrections were required.`

## Remaining Credential Scanner Exemptions (post-plan state)

The EXCLUDE list in `scripts/check_credentials.sh` now contains 14 entries:

**Self-references (always exempt):**
- `scripts/check_credentials.sh`
- `docs/audit/CREDENTIAL_HYGIENE.md`
- `docs/audit/LOGIN_BUG.md`

**Test code (TODO Phase 4 TEST-02):**
- `backend/tests/test_dashboard_advanced.py`
- `backend/tests/test_coa_reconciliation.py`
- `backend/tests/test_merit_order.py`
- `backend/tests/test_po_batubara.py`

**Test reports (TODO Phase 4 TEST-02):**
- `test_reports/iteration_3.json`
- `test_reports/iteration_4.json`
- `test_reports/iteration_5.json`
- `test_reports/iteration_6.json`

**Frontend doc viewer mirror copies (TODO Phase 4 or later):**
- `frontend/public/docs/API_REFERENCE.md`
- `frontend/public/docs/DEPLOYMENT_GUIDE.md`

**PRD (TODO Phase 3 STAB-03 — redact credentials block):**
- `memory/PRD.md`

Cleared in this phase (Phase 3): `API_REFERENCE.md` (plan 03-03), `DEPLOYMENT_GUIDE.md` (plan 03-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Backend startup port in readme.md was 8001 instead of 8013**
- **Found during:** Task 3 (readme.md verification)
- **Issue:** `readme.md` Menjalankan Aplikasi section used `--port 8001` but actual VPS production runs on port 8013; would mislead a developer reproducing the production environment
- **Fix:** Corrected to `--port 8013`; added production note with correct REACT_APP_BACKEND_URL
- **Files modified:** `pltu-tenayan-full-backup/readme.md`
- **Commit:** a96ad39

**2. [Rule 2 - Missing info] DEPLOYMENT_GUIDE.md port references inconsistent with actual VPS**
- **Found during:** Task 2 (port reconciliation)
- **Issue:** DEPLOYMENT_GUIDE.md consistently used port 8001 for internal uvicorn throughout, but actual production runs 8013. Replacing all 8001 references would make the generic deployment guide incorrect for deployments choosing a different port.
- **Fix:** Added "Catatan: Postur VPS Produksi Saat Ini" callout at top of section 2 documenting actual VPS state (8013/3013) without overwriting generic examples; updated the curl verification example to use the actual prod URL
- **Files modified:** `pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md`
- **Commit:** a96ad39

## Known Stubs

None — all content added is grounded in live system evidence (MongoDB counts, grep line references, and direct formula clause comparison).

## Threat Flags

None — this plan adds documentation only; no new network endpoints, auth paths, file access patterns, or schema changes.

## Phase 3 Closure

All 5 plans of Phase 3 are now complete:

| Plan | Title | Status | Key deliverable |
|------|-------|--------|-----------------|
| 03-01 | ADR promotion | Complete | 8 locked ADRs at .planning/decisions/ |
| 03-02 | VPS recovery runbook + ROADMAP fix | Complete | LOCAL_SETUP.md §VPS Service Recovery; ROADMAP D-13 wording fix |
| 03-03 | API_REFERENCE regeneration | Complete | scripts/regenerate_api_reference.py; API_REFERENCE.md (95 endpoints); API_REFERENCE.md credential exemption cleared |
| 03-04 | Known Issues + readme pointer + PROJECT.md ADR cross-link | Complete | documentation.md §Known Issues (5 entries); readme.md pointer; PROJECT.md ADR cross-link table |
| 03-05 | DATABASE_SCHEMA audit + DEPLOYMENT_GUIDE cleanup + blending verify | Complete | This SUMMARY |

Requirements closed by Phase 3: DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05, STAB-04.

## Self-Check: PASSED

**File existence:**
- FOUND: `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` (contains `## Duplicate Pair Active Read Targets`)
- FOUND: `pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md` (contains `${TEST_ADMIN_PASSWORD}`, `${MONGO_URL}`, `VPS Service Recovery`)
- FOUND: `pltu-tenayan-full-backup/scripts/check_credentials.sh` (DEPLOYMENT_GUIDE.md not in EXCLUDE)
- FOUND: `pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md` (DEPLOYMENT_GUIDE.md cleared note)
- FOUND: `pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md` (contains `CONS-blending-formula`)
- FOUND: `pltu-tenayan-full-backup/docs/audit/SMART_BLENDING_FORMULA_AUDIT.md` (new file, exists)
- FOUND: `pltu-tenayan-full-backup/readme.md` (contains `Known Issues`, port 8013)

**Commit existence:**
- FOUND: inner `a96ad39` (`docs(docs-01,docs-03): final reconciliation — ...`)

**Verification checks:**
- DATABASE_SCHEMA.md `^## Duplicate Pair Active Read Targets` count: 1
- `backend/server.py:<line>` references in DATABASE_SCHEMA.md: 4
- No `<TEST_ADMIN_PASSWORD>` in DEPLOYMENT_GUIDE.md: PASS
- No `mongodb(+srv)://user:pass@` in DEPLOYMENT_GUIDE.md: PASS
- `VPS Service Recovery` cross-link in DEPLOYMENT_GUIDE.md: PASS
- `${TEST_ADMIN_PASSWORD}` in DEPLOYMENT_GUIDE.md: PASS
- `${MONGO_URL}` in DEPLOYMENT_GUIDE.md: PASS
- Port 8013 in DEPLOYMENT_GUIDE.md: PASS
- `DEPLOYMENT_GUIDE.md` not in scripts/check_credentials.sh EXCLUDE: PASS
- `API_REFERENCE.md` not in scripts/check_credentials.sh EXCLUDE: PASS
- `CONS-blending-formula` in Smart_Blending_AI_Formula.md: PASS
- `docs/audit/SMART_BLENDING_FORMULA_AUDIT.md` exists: PASS
- `## Outcome` heading in audit log: PASS
- Credential scanner exit 0: PASS
- readme.md `Known Issues` pointer preserved: PASS
- readme.md port 8013: PASS

---
*Phase: 03-documentation-refresh-decision-lock-in*
*Plan: 05 (FINAL)*
*Completed: 2026-05-11*
