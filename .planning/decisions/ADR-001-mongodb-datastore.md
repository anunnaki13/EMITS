# ADR-001: MongoDB (via Motor) as Primary Datastore

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-001.

## Context

EMITS is the in-production Fuel Management System for PLTU Tenayan. At the time this ADR is locked, the system is already serving live operational data from a single VPS (`103.150.197.225`): 111 vessel records, 461 trucking rows, 721 COA reconciliation rows (the largest collection), 207 smartstock rows, 301 PO Batubara rows, 58 merit-order rows, 45 biomassa rows, plus users, app_settings, ai_chat_history, sumberpemakaian, and a handful of legacy duplicates. All of this lives in MongoDB on the same host as the FastAPI backend.

The project is in a **stabilize-before-upgrade** posture (PROJECT.md "Context"): the owner is learning the existing surface on real production data before any structural change. There is no operational pain pointing at the datastore layer — read latency is fine for the current row counts, the COA reconciliation document shape is naturally hierarchical (loading/unloading/internal quality samples + umpire workflow nested inside), and the Excel-ingest pipeline writes whole documents at a time without a relational schema being a forcing function.

There are zero migrations in flight. There is no "we wish we had Postgres" outstanding pain. The risk profile of swapping a datastore against 721 live COA rows + 461 live trucking rows + the rest is dramatically larger than any benefit — and the v1 success criteria (REQ-coa-reconciliation, REQ-rekap-penerimaan-bb, REQ-pagination-server-side, REQ-smart-stock) are already shipping on the current Mongo install.

This ADR locks MongoDB-via-Motor as the datastore for v1 so future ingest passes, plans, and contributors stop re-deriving the choice from PROJECT.md text every time.

## Decision

Use **MongoDB** as the single primary datastore for v1 of EMITS. Access it from the FastAPI backend via the **`motor`** async driver (`AsyncIOMotorClient`).

Specifically:

- One Mongo instance per deployment (currently the same VPS host, internal network).
- Connection string sourced from `MONGO_URL` env var.
- Database name sourced from `DB_NAME` env var (production: `pltu_tenayan`).
- All read/write paths in the backend route through the single `motor.motor_asyncio.AsyncIOMotorClient` instance created at import time in `server.py`.
- Persistence-layer rules (projection `{_id: 0}`, application-level UUID `id`, ISO 8601 datetimes) are split out into ADR-007 and remain canonical when changing data-access code.

This ADR does NOT lock the *individual* collection schemas (those evolve with feature work; see DATABASE_SCHEMA.md and the `CONS-*-schema` constraints in `.planning/intel/constraints.md`). It locks only the choice of datastore and the driver.

## Consequences

**Positive:**

- Document-shape collections fit the COA reconciliation domain (loading/unloading/internal quality samples + umpire workflow nested in one record) without join overhead.
- Excel-ingest pipelines (vessels, barges, trucking, biomassa, PO Batubara, merit-order, smart-stock, COA reconciliation) write whole documents and don't need a migration step when adding optional fields.
- `motor` async client integrates cleanly with FastAPI's async request handlers — no thread-pool detour for I/O.
- Operational footprint is small: one Mongo daemon, no schema migration tooling, no ORM layer to upgrade.
- Single-host VPS topology stays viable at current row counts (largest collection 721 rows, smart-stock cap at 50000 still well within Mongo's comfort zone).

**Negative / accepted tradeoffs:**

- No SQL-style joins; cross-collection analytics (e.g., COA vs vessel quality) require either application-layer joins or `$lookup` aggregation pipelines, both of which the AI Intelligence Agent and dashboard layers handle in code today.
- No referential integrity at the datastore layer; FK-style invariants (e.g., `created_by` → `users.id`) live in application code (CONS-logical-relations).
- Collection-naming debt is real: `smartstock` vs `smart_stock`, `sumber_pemakaian` vs `sumberpemakaian`, `app_settings` vs `settings`, `ai_chat_history` vs `ai_conversations` (CONS-collection-naming-debt). Phase 5 owns the standardization migration; this ADR explicitly does NOT pretend that surface is clean today.
- Migrating off Mongo later (v2 if multi-tenant or hard analytics requirements land) means rewriting the persistence layer; ADR-007's projection contract softens this by keeping `_id` invisible to the API.

## Alternatives Considered

- **PostgreSQL** — rejected. Would require schema design + migration of 721-row COA + 461-row trucking + 207-row smart-stock + 111-row vessels with no immediate operational benefit; adds an ORM layer and migration tooling for zero current pain.
- **SQLite** — rejected. Single-host fits, but the document-shape COA reconciliation workload (nested loading/unloading/internal quality + umpire result) maps poorly onto a relational schema, and concurrent-write semantics at the operator + admin + parser-job level are weaker than Mongo.
- **Split datastore (Mongo for documents + Postgres for relational summaries)** — rejected. Operational overhead (two daemons, two backup paths, two driver layers) is unjustified at current scale; a single store keeps the ops surface small.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-001 row (line 89: "Datastore (LOCKED, implicit/inherited): MongoDB as primary datastore via Motor").
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/backend/server.py:7` — `from motor.motor_asyncio import AsyncIOMotorClient`
  - `pltu-tenayan-full-backup/backend/server.py:28` — `client = AsyncIOMotorClient(mongo_url)` (single client instance constructed at import time, used by every route)
  - `pltu-tenayan-full-backup/backend/requirements.txt:60` — `motor==3.3.1` (pinned dependency)
- **Related constraints:** `.planning/intel/constraints.md` → CONS-collection-inventory (live-collection list), CONS-collection-naming-debt (Phase-5 standardization scope).
- **Sibling docs:** `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` (per-collection field inventory).
