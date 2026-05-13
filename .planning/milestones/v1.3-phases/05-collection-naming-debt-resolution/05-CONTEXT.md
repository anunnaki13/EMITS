# Phase 05: Collection Naming Debt Resolution - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve the four duplicate-collection-name debts identified by Phase-3 plan 03-05 audit: `smartstock` / `smart_stock`, `sumberpemakaian` / `sumber_pemakaian`, `app_settings` / `settings`, `ai_chat_history` / `ai_conversations`. For each pair: a canonical name is recorded in an ADR, the codebase reads only the canonical name (legacy reads removed), an empty-legacy drop is performed safely after a verified backup and observation window, and DATABASE_SCHEMA.md is cleaned of "legacy" markings.

The phase is operational/data-debt, not a refactor of code structure. The active CRUD endpoints already write to the active names (which are the chosen canonical names per D-01); the legacy collections are empty (0 records) per the audit. The work concentrates in: (a) ADR drafting, (b) 4–6 file:line edits in `server.py` to switch legacy reads → canonical, (c) a dry-run-then-apply migration script that drops empty legacy collections, (d) a backup + rollback runbook, (e) DATABASE_SCHEMA.md + comment cleanup.

**In scope:** DEBT-01..DEBT-05 (REQUIREMENTS.md lines 45-49). Four ADRs (one per pair) under `.planning/decisions/`. Migration script at `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` with dry-run + apply modes. Read-path edits in `pltu-tenayan-full-backup/backend/server.py` for the AI-module reads (lines 2377, 2385, 2425) and COA export (line 4382), plus any `ai_conversations` read (Phase-3 audit didn't show this one — the planner must re-grep). MIGRATION_RUNBOOK.md operator procedure (backup → dry-run → verify → cutover → observation → drop legacy → cleanup). DATABASE_SCHEMA.md update (drop "legacy" markings post-cutover). pytest suite must continue to exit 0 against the canonical-only codebase.

**Out of scope:**
- Renaming any of the four ACTIVE collections (e.g., `smartstock` → `smart_stock`). The active names ARE the canonical names per D-01; we are not refactoring for Python-idiomatic snake_case.
- Data movement between collections — every legacy collection has 0 records per the Phase-3 audit; this phase only switches code reads and drops empty legacy collections. Defensive bidirectional copy was rejected (D-02) because the legacy collections are confirmed empty.
- Frontend code changes — frontend hits API endpoints, not Mongo collection names; no frontend impact.
- New tests beyond what is needed to assert the migration is idempotent on a production-snapshot DB (the existing pytest suite + Phase-4 infra is sufficient for regression).
- Performance / index work on the canonical collections — deferred to a future polish phase.
- Index rationalization or schema validation rules — out of phase scope.

</domain>

<decisions>
## Implementation Decisions

### Canonical names (D-01..D-05 — one ADR per pair + a meta ADR)

- **D-01:** **`smartstock`** is canonical (NOT `smart_stock`). 207 production records. Active read in `pltu-tenayan-full-backup/backend/server.py:3100` (CRUD endpoints). `smart_stock` is the legacy name; 0 records; read at `server.py:2377` (AI module). Phase 5 switches `server.py:2377` to read from `smartstock` and drops `smart_stock` after the observation window.

- **D-02:** **`sumberpemakaian`** is canonical (NOT `sumber_pemakaian`). 208 production records. Active read in `server.py:3374` (CRUD). `sumber_pemakaian` is the legacy name; 0 records; read at `server.py:2385` (AI module). Phase 5 switches `server.py:2385` to read from `sumberpemakaian` and drops `sumber_pemakaian`.

- **D-03:** **`app_settings`** is canonical (NOT `settings`). 1 production record. Active read in `server.py:3853` (`/settings/coa` endpoint). `settings` is the legacy name; 0 records; read at `server.py:4382` (COA export) and `server.py:2425` (AI COA-alerts context). Phase 5 switches BOTH of those lines to read from `app_settings` and drops `settings`.

- **D-04:** **`ai_chat_history`** is canonical (NOT `ai_conversations`). Active read assigned at `server.py:2264` (`AI_CHAT_HISTORY_COLLECTION` constant). `ai_conversations` is the legacy name; 0 records; the planner MUST grep `server.py` for any remaining `ai_conversations` reads (the Phase-3 audit table did not enumerate code anchors for `ai_conversations`; planner closes that gap during planning).

- **D-05:** Each of D-01..D-04 lands as a separate locked MADR-format ADR at `.planning/decisions/ADR-009-canonical-smartstock.md` through `ADR-012-canonical-ai-chat-history.md`. Status: `Accepted (locked, YYYY-MM-DD)`. Each ADR cites the Phase-3 audit table row (`pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §"Duplicate-pair active-target audit") AND the `server.py:line` evidence for the canonical choice. The four ADRs are siblings to the existing eight ADRs (ADR-001..008) from Phase 3.

### Migration sequencing (D-06)

- **D-06:** **Read-path switch FIRST → observation window → drop legacy.** Order of operations:
  1. Update the 5+ legacy-read lines in `server.py` (lines 2377, 2385, 2425, 4382, plus any `ai_conversations` reads the planner discovers). Each edit is a 1-line code change replacing the legacy collection name with the canonical.
  2. Deploy to VPS (pull, restart uvicorn).
  3. Smoke-test the live endpoints that previously read from legacy (in particular: AI module endpoints + COA export).
  4. **Observation window: ≥48 hours** before dropping legacy collections — gives time to spot any missed read path (e.g., a script outside `server.py`, a cron, a frontend bypass).
  5. Run `migrate_collection_names.py --apply` to drop the 4 empty legacy collections.
  6. Re-run `pytest backend/tests -q` against canonical-only codebase, confirm exit 0.

- **D-07:** Defensive count-check pre-drop: the migration script MUST assert `db[legacy_name].count_documents({}) == 0` for each of the 4 legacy collections immediately before dropping. If any legacy collection has gained even 1 document during the observation window (silent write path missed by the audit), the script HALTS and the operator is alerted — no data-loss drop.

- **D-08:** Bidirectional data copy was REJECTED. Audit confirmed 0 records in all 4 legacy collections; introducing a copy step adds complexity without safety in this case. The D-07 count guard is the safety net.

### Backup + rollback procedure (D-09..D-11 — DEBT-04)

- **D-09:** **`mongodump`** full-DB backup before any production change. Command (documented verbatim in MIGRATION_RUNBOOK.md): `mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out /home/damnation/backups/pre-phase5-$(date +%Y%m%d-%H%M%S)/`. Estimated size: tens of MB. Verify integrity post-dump via `bsondump` smoke or row-count cross-check.

- **D-10:** **Rollback path** documented in MIGRATION_RUNBOOK.md §"Rollback":
  - Code rollback: `git revert <merge-commit>` on the inner repo (`pltu-tenayan-full-backup/`).
  - Data rollback (only if legacy collections were dropped AND a row appears missing): `mongorestore --drop --uri mongodb://localhost:27017 --nsInclude 'pltu_tenayan.*' /home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS/`.
  - The runbook documents both as separate procedures since most rollback scenarios only need code-revert, not data-restore.

- **D-11:** **Backup retention:** keep the pre-phase5 backup for ≥30 days after milestone v1.0 close. Operator's call after that; reference the policy in MIGRATION_RUNBOOK.md but do NOT auto-delete in the script.

### Test gating + production cutover (D-12..D-14 — DEBT-02)

- **D-12:** **Dry-run on a production-snapshot DB**, NOT on Phase-4 factory data. Procedure:
  1. `mongodump --db pltu_tenayan --out /tmp/pltu_tenayan_snapshot/` then `mongorestore --nsFrom 'pltu_tenayan.*' --nsTo 'pltu_tenayan_migration_dryrun.*' /tmp/pltu_tenayan_snapshot/`.
  2. Run `migrate_collection_names.py --target-db pltu_tenayan_migration_dryrun --apply` (the script accepts a target-DB override).
  3. **DEBT-02 zero-data-loss diff:** the script's `--verify` mode emits row counts and field-level checksums (md5 of sorted-doc JSON) for the 4 canonical collections BEFORE and AFTER the migration. Both must be byte-identical (since only empty legacy collections are dropped, the canonical collections must be untouched).
  4. Drop the dryrun DB after verification: `mongosh pltu_tenayan_migration_dryrun --eval "db.dropDatabase()"`.

- **D-13:** **Production cutover gate:** the code-deploy in step D-06.1-2 happens via the standard VPS recovery flow (LOCAL_SETUP.md §"VPS Service Recovery"). Maintenance window ~5 minutes (uvicorn restart). The legacy-drop step (D-06.5) happens after the ≥48h observation window — that step itself is non-disruptive (dropping empty collections has no traffic impact).

- **D-14:** **Post-cutover regression bar:** `pytest backend/tests -q` MUST exit 0 against the canonical-only codebase before the legacy-drop step. If pytest reveals a failing test that depends on a legacy collection name, that's a code path the audit missed — fix-forward in Phase 5 by adding the missing read-path edit.

### Claude's Discretion

- Exact ADR slug naming (e.g., `ADR-009-canonical-smartstock.md` vs `ADR-009-collection-smartstock.md`) — planner picks consistent with ADR-001..008 style.
- Migration-script CLI flag design (`--dry-run`, `--apply`, `--verify`, `--target-db`) — planner picks; smallest surface that supports the D-12 flow.
- Where MIGRATION_RUNBOOK.md lives (inner repo `pltu-tenayan-full-backup/docs/` vs outer `.planning/runbooks/`) — planner picks based on existing runbook precedent (VPS Service Recovery lives in `pltu-tenayan-full-backup/LOCAL_SETUP.md`, so inner-repo seems consistent).
- Plan decomposition: 4 ADRs could be one plan or four; planner decides based on atomic-commit ergonomics. Likely 2–4 plans total: (a) 4 ADRs, (b) read-path edits + migration script + tests, (c) MIGRATION_RUNBOOK.md + DATABASE_SCHEMA.md cleanup, (d) production cutover (if Phase 5 owns the actual prod apply — see open question).
- Whether Phase 5 owns the literal production cutover or stops at "ready-to-apply" with the runbook handed to the operator — the planner addresses this open question via a small AskUserQuestion to the user at planning time.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase boundary + requirements
- `.planning/ROADMAP.md` §"Phase 5: Collection Naming Debt Resolution" — goal + 5 SC + dependencies (Phase 4).
- `.planning/REQUIREMENTS.md` lines 45-49 — DEBT-01..DEBT-05 verbatim text.
- `.planning/PROJECT.md` §"Active" item DEBT-01 — collection naming standardization scope statement.

### Phase-3 audit (THE source-of-truth for this phase)
- `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §"Duplicate-pair active-target audit" (lines 697-735, including the audit table at lines 704-706) — the row-count + code-anchor evidence per pair. Plans MUST cite this audit table in each ADR's References section.
- `.planning/phases/03-documentation-refresh-decision-lock-in/03-05-SUMMARY.md` — Phase-3 plan 03-05 summary explicitly identifying 3 of 4 pairs as "both actively read" silent data-gap (AI module reads legacy=empty).

### Existing ADRs (style precedent — Phase 5 follows the same pattern)
- `.planning/decisions/ADR-001-mongodb-datastore.md` through `.planning/decisions/ADR-008-pagination-shape.md` — eight existing locked MADR-format ADRs (Phase 3 plan 03-01). Phase 5 adds ADR-009..ADR-012 with the SAME format: Status / Context / Decision / Consequences / Alternatives / References.

### Phase-4 carry-forward (test infrastructure Phase 5 builds on)
- `pltu-tenayan-full-backup/backend/tests/conftest.py` — Phase-4 conftest with `_backend_lifecycle` (port 18013), `_seed_baseline_data`, isolated `pltu_tenayan_test_<sessionid>` DB. Phase 5 migration script can be tested using this infra.
- `pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md` — operator runbook; MIGRATION_RUNBOOK.md should follow the same documentation style.
- `pltu-tenayan-full-backup/backend/tests/factories/` — 8 factory modules from Phase 4; can seed test fixtures for migration verification if needed.

### VPS recovery / deploy posture
- `pltu-tenayan-full-backup/LOCAL_SETUP.md` §"VPS Service Recovery (post-restart)" — the canonical uvicorn-restart procedure. Phase 5's code-deploy step follows the same flow.

### Backup / mongo tooling
- `mongodump` / `mongorestore` are standard MongoDB CLI tools; no project-specific wrapper exists. Plan 5's MIGRATION_RUNBOOK.md documents exact invocations.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase-4 pytest infrastructure** — `pytest tests/ -q` exits 0 against canonical-only code; Phase 5's read-path edits are validated by re-running the same suite (regression bar).
- **`tests/test_clean_checkout_gate.py`** — structural gate from Plan 04-04 that catches import errors on the test surface; Phase 5 read-path edits to `server.py` should not introduce import errors (this gate flags them if so).
- **`pltu-tenayan-full-backup/scripts/check_credentials.sh`** — pattern for one-shot bash scripts that operators run; Phase 5's `migrate_collection_names.py` is a similar deliverable but Python (because mongo client operations).
- **`tests/factories/`** — if the migration script needs a quick non-production validation, seed via these factories.

### Established Patterns
- **MADR-format ADRs** with Status / Context / Decision / Consequences / Alternatives / References — Phase 5 follows verbatim.
- **Two-repo commit boundary** — code (server.py, migration script, MIGRATION_RUNBOOK.md, DATABASE_SCHEMA.md) commits to inner repo `pltu-tenayan-full-backup/`; ADRs + SUMMARY.md + STATE/ROADMAP updates commit to outer `.planning/` repo. Same protocol as Phases 1–4.
- **`_seed_baseline_data` in conftest** — already seeds canonical collections; Phase 5 doesn't need to extend it (legacy reads only affect AI module, not the seeded data path).
- **Drop-DB guard pattern** — Phase 4 conftest asserts `TEST_DB_NAME.startswith("pltu_tenayan_test_")` before drops. Phase 5's migration script uses the same guard pattern: assert collection name is in the locked legacy-name set before `drop()`.

### Integration Points
- **server.py 5+ line edits** — lines 2377 (smart_stock → smartstock), 2385 (sumber_pemakaian → sumberpemakaian), 2425 (settings → app_settings), 4382 (settings → app_settings), plus any `ai_conversations` references the planner discovers via grep. Each is a 1-line `db[legacy] → db[canonical]` swap.
- **AI module** — the silent data-gap consumer. Once Phase 5 lands, the AI module will start reading real data (207/208/1 records vs the current 0). This may trigger NEW failure modes in AI endpoints if they were previously returning empty-result paths happily; the planner must include a Phase-5 smoke-test step that exercises the AI endpoints post-migration.
- **MIGRATION_RUNBOOK.md** — lives at `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` or `pltu-tenayan-full-backup/docs/MIGRATION_RUNBOOK.md`; planner decides based on existing runbook precedent.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly preferred "active name = canonical" over snake_case-idiomatic refactor. The chosen path is the minimum-disruption path consistent with the EMITS milestone-v1.0 stabilization posture.
- The user explicitly accepted `mongodump --db pltu_tenayan` + `git revert` as the rollback procedure, declining per-collection .bson granularity and declining the dual-read code window option.
- Observation window ≥48 hours between read-switch deploy and legacy-drop is implicit in the "Update reads first, drop legacy after" choice; the planner sets the exact duration in the runbook.

</specifics>

<deferred>
## Deferred Ideas

### Snake_case refactor of all collection names
- **Origin:** Mentioned during D-01 discussion as the alternative to "active name = canonical".
- **Why deferred:** Out of scope for milestone v1.0 stabilization; would rename 416 production records across 4 collections + update all CRUD endpoints. Pure refactor with no functional gain — collections work fine under their current names.
- **Proposed home:** A future polish phase (Phase 8 or post-milestone). Low priority; not blocking.

### Index rationalization / schema validation on canonical collections
- **Origin:** Mentioned out-of-scope.
- **Why deferred:** Phase 5 is naming-debt-only. Index design is a different concern.
- **Proposed home:** Future polish phase.

### Performance optimization on AI module post-migration
- **Origin:** AI module will start reading real data for the first time once Phase 5 lands. If aggregation queries are slow on 207+208 records, that's a new performance concern.
- **Why deferred:** Will only surface once Phase 5 lands. If observed, owner is Phase 6 (Operational Unblocks) or a follow-on.

### Reviewed Todos (not folded)
- None — `gsd-sdk query todo.match-phase 5` returned 0 todos.

</deferred>

---

*Phase: 05-collection-naming-debt-resolution*
*Context gathered: 2026-05-11*
