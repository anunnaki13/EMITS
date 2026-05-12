# ADR-010: sumberpemakaian as Canonical Pemakaian Source Collection Name

## Status

Accepted (locked, 2026-05-11) — promoted from Phase-3 duplicate-pair audit; canonical name selected per D-02 in 05-CONTEXT.md.

## Context

EMITS maintains a `sumberpemakaian` collection holding fuel-consumption source records (pemakaian = consumption/usage) used by the smart-stock dashboard and AI intelligence features. At the time Phase 5 is planned, the live `pltu_tenayan` database contains **208 records** in `sumberpemakaian` and **0 records** in `sumber_pemakaian` — confirmed by `db.getCollectionNames()` output on 2026-05-11, which shows `sumber_pemakaian` is entirely absent from the live database.

The duplicate arose from the same root cause as the `smartstock` / `smart_stock` pair: the CRUD endpoints and the AI Intelligence module were authored independently using different naming conventions. The CRUD module consistently wrote to `sumberpemakaian` (no underscore separator), accumulating 208 production records. The AI module read from `db.sumber_pemakaian` (underscore-separated). This created a **silent data-gap**: the AI quick-smart-stock endpoint and the AI context builder — both of which feed real consumption-rate context to the LLM for smart-blending and stock recommendations — have always read from `sumber_pemakaian` (0 records) while all real pemakaian data lives in `sumberpemakaian`.

The four legacy reads span two functional areas of `server.py`:

- `server.py:2387` — `pemakaian_data = await db.sumber_pemakaian.find(` — AI context builder, "smart_stock" module branch
- `server.py:2398` — `total_pemakaian = await db.sumber_pemakaian.aggregate([` — AI context builder, same branch
- `server.py:2868` — `total_pemakaian = await db.sumber_pemakaian.aggregate([` — `/ai/quick/smart-stock` endpoint
- `server.py:2877` — `avg_usage = await db.sumber_pemakaian.aggregate([` — `/ai/quick/smart-stock` endpoint (average usage computation)

The CRUD read/write paths at `server.py:3352, 3357, 3363, 3429, 3535, 3538, 3557, 3576` all use `db.sumberpemakaian` (canonical) and must not be changed.

The Phase-3 audit (DATABASE_SCHEMA.md §"Duplicate Pair Active Read Targets", lines 695-735, audit table row at line 705) documented this as "Both names actively read — CRUD endpoints use `sumberpemakaian`; AI module uses `sumber_pemakaian`" with deferred canonical selection to Phase 5.

DEBT-01 in `.planning/REQUIREMENTS.md` requires that a canonical-name decision be recorded in an ADR for each duplicate pair. This ADR satisfies that requirement for the `sumberpemakaian` / `sumber_pemakaian` pair.

## Decision

**`sumberpemakaian`** is the canonical collection name. `sumber_pemakaian` is rejected as the legacy duplicate.

After Phase 5 Plan 05-02 lands, all backend reads in `server.py` reference only `db.sumberpemakaian`. The four legacy AI-module lines (2387, 2398, 2868, 2877) are the only changes required — each is a single token swap from `db.sumber_pemakaian` to `db.sumberpemakaian`.

The empty `sumber_pemakaian` collection is dropped in Plan 05-04 after a ≥48h observation window per D-06. The migration script (`pltu-tenayan-full-backup/scripts/migrate_collection_names.py`) asserts `db.sumber_pemakaian.count_documents({}) == 0` immediately before the drop (D-07 count guard), halting if any document appeared during the observation window.

## Consequences

**Positive:**

- The AI quick-smart-stock endpoint (`/api/ai/quick/smart-stock`) now reads real consumption data: 208 pemakaian records instead of empty-collection zeros. Smart-blending and stock recommendations gain real usage-rate context.
- The `avg_usage` computation (server.py:2877) now reflects actual historical consumption rates rather than returning null/zero from an empty collection — directly improving AI recommendation quality.
- The AI context builder feeds real pemakaian data to the LLM for the "smart_stock" module branch.
- Single source of truth: `db.sumberpemakaian` is the only Mongo expression referencing this collection after Plan 05-02.
- `grep -c "db\.sumber_pemakaian\b" server.py` becomes 0 — the codebase is auditable via a single grep.
- DATABASE_SCHEMA.md "legacy" marking for this pair is removed in Plan 05-04.

**Negative / accepted tradeoffs:**

- 4 lines in `server.py` must be edited atomically (2387, 2398, 2868, 2877) in Plan 05-02; tests must be re-run after the edit to confirm zero regression.
- A ≥48h observation window is required between the read-switch deploy and the `sumber_pemakaian` collection drop — operators must verify AI smart-stock endpoints return real pemakaian data during this window.
- The AI quick-smart-stock endpoint behaviour changes post-migration: average usage values and total pemakaian figures will shift from 0 to real data. This is the correct behaviour but operators must be aware of the change and verify during the observation window.
- The drop step is irreversible without a `mongorestore` from the pre-phase5 backup (D-09).

## Alternatives Considered

**`sumber_pemakaian` (snake_case-idiomatic) as canonical** — rejected. While `sumber_pemakaian` follows Python snake_case convention, it holds 0 production records. Choosing it as canonical would require renaming 208 production records plus updating all 8 CRUD endpoint lines (3352, 3357, 3363, 3429, 3535, 3538, 3557, 3576). The minimum-disruption path consistent with the stabilize-before-upgrade posture is to keep all 208 records in place and fix only the 4 AI-module reads. Snake_case normalization is deferred to Phase 8.

**Bidirectional dual-read window** — rejected per D-08. The legacy `sumber_pemakaian` collection is confirmed empty (0 records); the D-07 count guard in the migration script is the appropriate safety mechanism.

**Snake_case refactor of all collection names** — deferred to Phase 8. Out of scope for milestone v1.0 stabilization.

## References

- **Source decision:** `.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md` §"Implementation Decisions" D-02.
- **Phase-3 audit:** `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §"Duplicate Pair Active Read Targets (Phase-3 audit, 2026-05-10)" lines 695-735 — audit table row at line 705: "sumberpemakaian vs sumber_pemakaian | Both names actively read — CRUD endpoints use `sumberpemakaian`; AI module uses `sumber_pemakaian` | Active count: 208 | Legacy count: 0".
- **Code anchors — canonical CRUD reads (DO NOT change):**
  - `pltu-tenayan-full-backup/backend/server.py:3352` — `db.sumberpemakaian` CRUD read (canonical, active today)
  - `pltu-tenayan-full-backup/backend/server.py:3357, 3363, 3429, 3535, 3538, 3557, 3576` — remaining CRUD endpoint reads (all canonical)
- **Code anchors — legacy AI reads (to be fixed in Plan 05-02):**
  - `pltu-tenayan-full-backup/backend/server.py:2387` — `db.sumber_pemakaian.find` (AI context builder)
  - `pltu-tenayan-full-backup/backend/server.py:2398` — `db.sumber_pemakaian.aggregate` (AI context builder)
  - `pltu-tenayan-full-backup/backend/server.py:2868` — `db.sumber_pemakaian.aggregate` (`/ai/quick/smart-stock` endpoint, total pemakaian)
  - `pltu-tenayan-full-backup/backend/server.py:2877` — `db.sumber_pemakaian.aggregate` (`/ai/quick/smart-stock` endpoint, avg_usage)
- **Research verification:** `.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md` §"Research Focus 2: Comprehensive server.py Legacy-Read Grep" — all line numbers VERIFIED 2026-05-11.
- **Requirement:** `.planning/REQUIREMENTS.md` DEBT-01 — "Canonical-name decision recorded in an ADR for each duplicate pair."
- **Sibling ADRs:** `.planning/decisions/ADR-009-canonical-smartstock.md`, `.planning/decisions/ADR-011-canonical-app-settings.md`, `.planning/decisions/ADR-012-canonical-ai-chat-history.md` — the four canonical-name ADRs land together as a set in Phase 5 Plan 05-01.
