# ADR-009: smartstock as Canonical Smart-Stock Collection Name

## Status

Accepted (locked, 2026-05-11) — promoted from Phase-3 duplicate-pair audit; canonical name selected per D-01 in 05-CONTEXT.md.

## Context

EMITS maintains a `smartstock` collection holding fuel-stock penerimaan (receipt) records used across the smart-stock dashboard and AI intelligence features. At the time Phase 5 is planned, the live `pltu_tenayan` database contains **207 records** in `smartstock` and **0 records** in `smart_stock` — confirmed by `db.getCollectionNames()` output on 2026-05-11, which shows `smart_stock` is entirely absent from the live database.

The duplicate arose because two independent code paths used different names. The CRUD endpoints (Phase-1 ingest pipeline) wrote consistently to `smartstock` (no underscore), accumulating 207 production records. The AI Intelligence module was authored separately and read from `db.smart_stock` (underscore-separated). This created a **silent data-gap**: the AI quick-smart-stock endpoint (`/api/ai/quick/smart-stock`) and the AI context builder have always returned empty/zero results because they read from `smart_stock` (0 records) while all real data lives in `smartstock`.

The three legacy reads are concentrated in two functional areas of `server.py`:

- `server.py:2379` — `penerimaan_data = await db.smart_stock.find(` — AI context builder, "smart_stock" module branch
- `server.py:2395` — `total_penerimaan = await db.smart_stock.aggregate([` — AI context builder, same branch
- `server.py:2863` — `total_penerimaan = await db.smart_stock.aggregate([` — `/ai/quick/smart-stock` endpoint

The CRUD read/write paths at `server.py:3078, 3083, 3130, 3257, 3261, 3283, 3313, 3325, 3637` all use `db.smartstock` (canonical) and must not be changed.

The Phase-3 audit (DATABASE_SCHEMA.md §"Duplicate Pair Active Read Targets", lines 695-735, audit table row at line 704) documented this as "Both names actively read — CRUD endpoints use `smartstock`; AI module uses `smart_stock`" with deferred canonical selection to Phase 5.

DEBT-01 in `.planning/REQUIREMENTS.md` requires that a canonical-name decision be recorded in an ADR for each duplicate pair. This ADR satisfies that requirement for the `smartstock` / `smart_stock` pair.

## Decision

**`smartstock`** is the canonical collection name. `smart_stock` is rejected as the legacy duplicate.

After Phase 5 Plan 05-02 lands, all backend reads in `server.py` reference only `db.smartstock`. The three legacy AI-module lines (2379, 2395, 2863) are the only changes required — each is a single token swap from `db.smart_stock` to `db.smartstock`.

The empty `smart_stock` collection is dropped in Plan 05-04 after a ≥48h observation window per D-06. The migration script (`pltu-tenayan-full-backup/scripts/migrate_collection_names.py`) asserts `db.smart_stock.count_documents({}) == 0` immediately before the drop (D-07 count guard), halting if any document appeared during the observation window.

Note: `server.py:2377` contains a Python string literal `if module in ["general", "smart_stock"]` — this is a parameter comparison, NOT a MongoDB collection read, and is explicitly excluded from Phase 5 edits.

## Consequences

**Positive:**

- The AI quick-smart-stock endpoint (`/api/ai/quick/smart-stock`) now returns real aggregates over 207 production records instead of empty zeros — a material fix to AI recommendation quality.
- The AI context builder no longer silently reads an empty collection; smart-stock module context fed to the LLM is now real data.
- Single source of truth: `db.smartstock` is the only Mongo expression referencing this collection after Plan 05-02.
- `grep -c "db\.smart_stock\b" server.py` becomes 0 — the codebase is now auditable via a single grep.
- DATABASE_SCHEMA.md "legacy" marking for this pair is removed in Plan 05-04, eliminating the "both names actively read" ambiguity for future contributors.

**Negative / accepted tradeoffs:**

- 3 lines in `server.py` must be edited atomically (2379, 2395, 2863) in Plan 05-02; tests must be re-run after the edit to confirm zero regression.
- A ≥48h observation window is required between the read-switch deploy and the `smart_stock` collection drop — operators must verify AI smart-stock endpoints return real data during this window.
- The AI quick-smart-stock endpoint behaviour changes after migration: it was returning 0/empty results (from the empty `smart_stock` collection); after the fix it will return real 207-record aggregates. This is the correct behaviour but operators must be aware of the change during the observation window.
- The drop step is irreversible without a `mongorestore` from the pre-phase5 backup (D-09); the backup must be taken and verified before Plan 05-02 is deployed to production.

## Alternatives Considered

**`smart_stock` (snake_case-idiomatic) as canonical** — rejected. While `smart_stock` follows Python snake_case convention, it holds 0 production records. Choosing it as canonical would require renaming 207 production records (a non-trivial data movement operation) plus updating all 9 CRUD endpoint lines (3078, 3083, 3130, 3257, 3261, 3283, 3313, 3325, 3637). The minimum-disruption path consistent with the stabilize-before-upgrade posture is to keep all 207 records where they are and fix only the 3 AI-module reads. Snake_case normalization of all collection names is deferred to a future polish phase (Phase 8 or post-milestone).

**Bidirectional dual-read window** — rejected per D-08. The legacy `smart_stock` collection is confirmed empty (0 records); introducing a dual-read code window adds code complexity and test surface for zero safety benefit. The D-07 count guard in the migration script is the appropriate safety mechanism.

**Snake_case refactor of all collection names** — deferred to Phase 8. Out of scope for milestone v1.0 stabilization. No functional gain at current scale; pure cosmetic.

## References

- **Source decision:** `.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md` §"Implementation Decisions" D-01.
- **Phase-3 audit:** `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §"Duplicate Pair Active Read Targets (Phase-3 audit, 2026-05-10)" lines 695-735 — audit table row at line 704: "smartstock vs smart_stock | Both names actively read — CRUD endpoints use `smartstock`; AI module uses `smart_stock` | Active count: 207 | Legacy count: 0".
- **Code anchors — canonical CRUD reads (DO NOT change):**
  - `pltu-tenayan-full-backup/backend/server.py:3078` — `db.smartstock` CRUD read (canonical, active today)
  - `pltu-tenayan-full-backup/backend/server.py:3083, 3130, 3257, 3261, 3283, 3313, 3325, 3637` — remaining CRUD endpoint reads (all canonical)
- **Code anchors — legacy AI reads (to be fixed in Plan 05-02):**
  - `pltu-tenayan-full-backup/backend/server.py:2379` — `db.smart_stock.find` (AI context builder)
  - `pltu-tenayan-full-backup/backend/server.py:2395` — `db.smart_stock.aggregate` (AI context builder)
  - `pltu-tenayan-full-backup/backend/server.py:2863` — `db.smart_stock.aggregate` (`/ai/quick/smart-stock` endpoint)
- **Line 2377 exclusion:** `server.py:2377` is `if module in ["general", "smart_stock"]` — a Python string literal, NOT a collection read; explicitly excluded from Phase 5 edits (RESEARCH.md Focus 2 §Pitfalls).
- **Research verification:** `.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md` §"Research Focus 2: Comprehensive server.py Legacy-Read Grep" — all line numbers VERIFIED 2026-05-11.
- **Requirement:** `.planning/REQUIREMENTS.md` DEBT-01 — "Canonical-name decision recorded in an ADR for each duplicate pair."
- **Sibling ADRs:** `.planning/decisions/ADR-010-canonical-sumberpemakaian.md`, `.planning/decisions/ADR-011-canonical-app-settings.md`, `.planning/decisions/ADR-012-canonical-ai-chat-history.md` — the four canonical-name ADRs land together as a set in Phase 5 Plan 05-01.
