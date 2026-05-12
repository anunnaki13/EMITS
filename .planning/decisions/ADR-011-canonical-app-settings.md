# ADR-011: app_settings as Canonical Application-Settings Collection Name

## Status

Accepted (locked, 2026-05-11) — promoted from Phase-3 duplicate-pair audit; canonical name selected per D-03 in 05-CONTEXT.md.

## Context

EMITS maintains an `app_settings` collection holding a single COA (Certificate of Analysis) pricing-configuration record, most critically the `price_per_kcal_per_ton` coefficient used by the COA export PDF and AI COA-alerts features. At the time Phase 5 is planned, the live `pltu_tenayan` database contains **1 record** in `app_settings` and **0 records** in `settings` — confirmed by `db.getCollectionNames()` output on 2026-05-11, which shows `settings` is entirely absent from the live database.

The duplicate arose because the `/settings/coa` REST endpoint was authored using the descriptive `app_settings` collection name, while the COA export PDF path and the AI COA-alerts context builder were authored separately and used the generic name `settings`. This created a **silent operational impact**: the COA export PDF endpoint and two AI endpoints were reading from `settings` (0 records, absent from DB), causing silent fallback to a **hardcoded default** of `price_per_kcal_per_ton = 50`. The actual configured price stored in `app_settings` was never read by these paths.

The three legacy reads in `server.py`:

- `server.py:2427` — `settings = await db.settings.find_one({"type": "coa"})` — AI context builder, "coa_reconciliation" module branch
- `server.py:2926` — `settings = await db.settings.find_one({"type": "coa"})` — `/ai/quick/coa-alerts` endpoint
- `server.py:4346` — `settings = await db.settings.find_one({"type": "coa"})` — COA export PDF endpoint

The canonical reads (DO NOT change) in `server.py`:

- `server.py:3817` — `settings = await db.app_settings.find_one({"type": "coa"}, {"_id": 0})` — GET /settings/coa
- `server.py:3825` — `await db.app_settings.update_one(` — PUT /settings/coa
- `server.py:3901` — `coa_settings = await db.app_settings.find_one({"type": "coa"}, {"_id": 0})` — COA KPI endpoint

The Phase-3 audit (DATABASE_SCHEMA.md §"Duplicate Pair Active Read Targets", lines 695-735, audit table row at line 706) documented this as "Both names actively read — `/settings/coa` GET/PUT uses `app_settings`; COA export and AI COA-alerts use `settings`" with deferred canonical selection to Phase 5.

Note: There is no `from .settings import settings` or similar Python module import in `server.py` — the word `settings` in affected lines refers only to the local variable holding the database result, not a Python module. After Plan 05-02 edits, the local variable name `settings` can remain as-is; only the `db.settings` → `db.app_settings` token changes (minimal diff).

DEBT-01 in `.planning/REQUIREMENTS.md` requires that a canonical-name decision be recorded in an ADR for each duplicate pair. This ADR satisfies that requirement for the `app_settings` / `settings` pair.

## Decision

**`app_settings`** is the canonical collection name. `settings` is rejected as the legacy duplicate.

After Phase 5 Plan 05-02 lands, all three legacy `db.settings.find_one({"type": "coa"})` reads in `server.py` (lines 2427, 2926, 4346) reference `db.app_settings` instead. Each is a single token swap; the local variable name `settings` on the left-hand side of the assignment is unchanged for minimal diff.

The empty `settings` collection is dropped in Plan 05-04 after a ≥48h observation window per D-06. The migration script asserts `db.settings.count_documents({}) == 0` immediately before the drop (D-07 count guard), halting if any document appeared during the observation window.

## Consequences

**Positive:**

- COA export PDF endpoint (`server.py:4346`) now reads the real configured `price_per_kcal_per_ton` from `app_settings` instead of falling back to the hardcoded default 50 — a material behavioural fix to the COA export feature.
- AI COA-alerts endpoint (`/api/ai/quick/coa-alerts`, `server.py:2926`) now computes `potential_loss` using the real configured price instead of the hardcoded default 50. Alert thresholds and recommendations become operationally meaningful.
- AI context builder for "coa_reconciliation" module (`server.py:2427`) feeds the LLM real COA pricing context, improving AI advice quality.
- Single source of truth: `db.app_settings` is the only Mongo expression referencing this collection after Plan 05-02.
- `grep -c "db\.settings\.find_one" server.py` becomes 0 — the codebase is auditable via a single grep.
- The name `app_settings` is unambiguous and avoids Python module-namespace collision risk with any future `import settings` pattern.
- DATABASE_SCHEMA.md "legacy" marking for this pair is removed in Plan 05-04.

**Negative / accepted tradeoffs:**

- 3 lines in `server.py` must be edited atomically (2427, 2926, 4346) in Plan 05-02; tests must be re-run after the edit to confirm zero regression.
- The `potential_loss` values returned by `/api/ai/quick/coa-alerts` will change post-migration (was: based on hardcoded default 50; now: based on real configured `price_per_kcal_per_ton`). Operators MUST verify COA-alerts output during the ≥48h observation window per RESEARCH.md Focus 6 behavioural-change note.
- A ≥48h observation window is required between the read-switch deploy and the `settings` collection drop.
- The drop step is irreversible without a `mongorestore` from the pre-phase5 backup (D-09).

## Alternatives Considered

**`settings` (shorter, generic) as canonical** — rejected. While `settings` is shorter and follows a common Python naming pattern, it holds 0 production records. Choosing it as canonical would require renaming the 1 production record in `app_settings` and updating 3 canonical endpoint lines (3817, 3825, 3901). Additionally, `settings` is a common Python module name (e.g., Django/Flask `settings.py`), making it a namespace-collision-prone identifier; `app_settings` is unambiguous in any Python context. The minimum-disruption path is to fix the 3 AI/export reads and keep the 1 production record in place. Snake_case renaming is deferred to Phase 8.

**Bidirectional dual-read window** — rejected per D-08. The legacy `settings` collection is confirmed empty (0 records); the D-07 count guard in the migration script is the appropriate safety mechanism.

## References

- **Source decision:** `.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md` §"Implementation Decisions" D-03.
- **Phase-3 audit:** `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §"Duplicate Pair Active Read Targets (Phase-3 audit, 2026-05-10)" lines 695-735 — audit table row at line 706: "app_settings vs settings | Both names actively read — `/settings/coa` GET/PUT uses `app_settings`; COA export and AI COA-alerts use `settings` | Active count: 1 | Legacy count: 0".
- **Code anchors — canonical reads (DO NOT change):**
  - `pltu-tenayan-full-backup/backend/server.py:3817` — `db.app_settings.find_one` (GET /settings/coa)
  - `pltu-tenayan-full-backup/backend/server.py:3825` — `db.app_settings.update_one` (PUT /settings/coa)
  - `pltu-tenayan-full-backup/backend/server.py:3901` — `db.app_settings.find_one` (COA KPI endpoint)
- **Code anchors — legacy reads (to be fixed in Plan 05-02):**
  - `pltu-tenayan-full-backup/backend/server.py:2427` — `db.settings.find_one({"type": "coa"})` (AI context builder)
  - `pltu-tenayan-full-backup/backend/server.py:2926` — `db.settings.find_one({"type": "coa"})` (`/ai/quick/coa-alerts` endpoint)
  - `pltu-tenayan-full-backup/backend/server.py:4346` — `db.settings.find_one({"type": "coa"})` (COA export PDF endpoint)
- **Behavioural change note:** `.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md` Focus 6 "Endpoint 2: /ai/quick/coa-alerts" — `potential_loss` values will change post-migration from hardcoded-50 basis to real configured `price_per_kcal_per_ton`.
- **Research verification:** `.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md` §"Research Focus 2: Comprehensive server.py Legacy-Read Grep" — all line numbers VERIFIED 2026-05-11. Note: CONTEXT.md originally cited line 4382; actual line is 4346 (corrected in RESEARCH.md Focus 2 discrepancy table).
- **Requirement:** `.planning/REQUIREMENTS.md` DEBT-01 — "Canonical-name decision recorded in an ADR for each duplicate pair."
- **Sibling ADRs:** `.planning/decisions/ADR-009-canonical-smartstock.md`, `.planning/decisions/ADR-010-canonical-sumberpemakaian.md`, `.planning/decisions/ADR-012-canonical-ai-chat-history.md` — the four canonical-name ADRs land together as a set in Phase 5 Plan 05-01.
