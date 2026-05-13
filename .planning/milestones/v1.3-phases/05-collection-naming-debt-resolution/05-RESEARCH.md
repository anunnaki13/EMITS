# Phase 05: Collection Naming Debt Resolution - Research

**Researched:** 2026-05-11
**Domain:** MongoDB collection migration, Python script authoring, operator runbook documentation
**Confidence:** HIGH (all critical findings verified against live codebase and running mongod)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `smartstock` is canonical (NOT `smart_stock`). 207 production records. `smart_stock` is legacy; 0 records; read at `server.py:2377` (AI module). Phase 5 switches all legacy reads to `smartstock` and drops `smart_stock` after the observation window.

- **D-02:** `sumberpemakaian` is canonical (NOT `sumber_pemakaian`). 208 production records. `sumber_pemakaian` is legacy; 0 records; read at `server.py:2385` (AI module). Phase 5 switches all legacy reads to `sumberpemakaian` and drops `sumber_pemakaian`.

- **D-03:** `app_settings` is canonical (NOT `settings`). 1 production record. `settings` is legacy; 0 records; read at `server.py:4382` (COA export) and `server.py:2425` (AI COA-alerts context). Phase 5 switches BOTH lines to `app_settings` and drops `settings`.

- **D-04:** `ai_chat_history` is canonical (NOT `ai_conversations`). Active read assigned at `server.py:2264`. `ai_conversations` is legacy; 0 records; planner MUST grep for remaining `ai_conversations` reads.

- **D-05:** Each of D-01..D-04 lands as a separate locked MADR-format ADR at `.planning/decisions/ADR-009-canonical-smartstock.md` through `ADR-012-canonical-ai-chat-history.md`.

- **D-06:** Read-path switch FIRST → observation window → drop legacy. Order: update 5+ lines in `server.py`, deploy to VPS, smoke-test, ≥48h observation, run `migrate_collection_names.py --apply`, re-run pytest.

- **D-07:** Pre-drop count-check: migration script MUST assert `db[legacy_name].count_documents({}) == 0` before dropping. Script HALTS if any count > 0.

- **D-08:** No bidirectional data copy. Legacy collections are confirmed empty; the D-07 count guard is the safety net.

- **D-09:** `mongodump` full-DB backup before any production change. Command: `mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out /home/damnation/backups/pre-phase5-$(date +%Y%m%d-%H%M%S)/`.

- **D-10:** Rollback = `git revert <merge-commit>` for code + `mongorestore --drop` for data (only if collections were dropped AND a row appears missing). Both documented separately in MIGRATION_RUNBOOK.md.

- **D-11:** Backup retained ≥30 days after milestone v1.0 close. No auto-delete in script.

- **D-12:** Dry-run on `pltu_tenayan_migration_dryrun` (mongodump→restore snapshot, NOT factory data). Script `--verify` mode emits row counts and field-level checksums. pytest -q exit 0 = cutover gate.

- **D-13:** Production cutover gate: code-deploy via LOCAL_SETUP.md §"VPS Service Recovery" procedure.

- **D-14:** Post-cutover regression: `pytest backend/tests -q` MUST exit 0 before legacy-drop step.

### Claude's Discretion

- Exact ADR slug naming (planner picks consistent with ADR-001..008 style).
- Migration-script CLI flag design (`--dry-run`, `--apply`, `--verify`, `--target-db`).
- Where MIGRATION_RUNBOOK.md lives (inner repo `pltu-tenayan-full-backup/docs/` vs outer `.planning/runbooks/`).
- Plan decomposition: 4 ADRs could be one plan or four; planner decides.
- Whether Phase 5 owns the literal production cutover or stops at "ready-to-apply" with the runbook handed to the operator.

### Deferred Ideas (OUT OF SCOPE)

- Snake_case refactor of all collection names (Phase 8 or post-milestone).
- Index rationalization / schema validation on canonical collections.
- Performance optimization on AI module post-migration.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEBT-01 | Canonical-name decision recorded in an ADR for each duplicate pair | ADR-009..012 MADR format verified against ADR-001..008 style; exact structure in Research Focus 1 |
| DEBT-02 | Migration script dry-run on production copy, zero data-loss diff | Exact mongodump/mongorestore commands verified live; checksum strategy in Research Focus 4 |
| DEBT-03 | Backend code reads only canonical names; grep confirms zero legacy reads | Comprehensive grep completed — all 10 legacy-read lines identified; Research Focus 2 |
| DEBT-04 | Migration applied to production with verified backup and documented rollback | mongodump/mongorestore flags verified; MIGRATION_RUNBOOK.md structure in Research Focus 7 |
| DEBT-05 | DATABASE_SCHEMA.md and code comments no longer mark any collection as "legacy" | All "legacy" occurrences in DATABASE_SCHEMA.md catalogued; cleanup scope in Research Focus 8 |
</phase_requirements>

---

## Summary

Phase 5 resolves four duplicate-collection-name debts identified by the Phase-3 audit. The work is concentrated in: (a) four locked ADRs recording canonical choices, (b) switching 10 legacy-read lines in `server.py` to canonical names, (c) a migration script that drops the four empty legacy collections after a dry-run on a production snapshot, and (d) a MIGRATION_RUNBOOK.md operator document. The phase does NOT move any data — all four legacy collections are confirmed empty in the live database (verified 2026-05-11 by `db.getCollectionNames()` which shows only the canonical names exist; the legacy names are absent entirely from the live `pltu_tenayan` DB).

The most important audit finding is that the CONTEXT.md line-number citations were partially outdated. The actual legacy-read count is **10 lines** across `server.py`, not the "5+" mentioned in the context. Specifically, `db.smart_stock` appears at lines 2379, 2395, and 2863 (3 lines); `db.sumber_pemakaian` appears at lines 2387, 2398, 2868, and 2877 (4 lines); and `db.settings` appears at lines 2427, 2926, and 4346 (3 lines). The `ai_conversations` collection does NOT appear anywhere in `server.py` — only the `ai_chat_collection = db.ai_chat_history` assignment at line 2266. There are zero legacy reads for the `ai_conversations` pair.

The infrastructure is well-suited for this phase. MongoDB 7.0.32 with mongodump/mongorestore version 100.16.1 confirms `--nsFrom`/`--nsTo` namespace-remapping flags are available. The Phase-4 test infrastructure (isolated `pltu_tenayan_test_<sessionid>` DB, conftest.py lifecycle) provides a safe regression surface. The migration script must include a `--target-db` override flag so pytest invocations cannot accidentally target the production DB.

**Primary recommendation:** Implement 4 plans: (1) 4 ADRs, (2) server.py read-path edits + migration script + dryrun test, (3) MIGRATION_RUNBOOK.md, (4) DATABASE_SCHEMA.md cleanup. The production cutover (mongodump backup + deploy + drop) is documented in the runbook and executed by the operator; Phase 5 does not automate the production cutover itself.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Canonical name decisions (ADRs) | Planning/docs tier | — | Documentation-only artifacts in `.planning/decisions/`; no runtime impact |
| Legacy-read replacement in server.py | API/Backend | — | All collection access is in FastAPI route handlers and helper functions; no frontend or CDN involvement |
| Migration script (drop empty legacies) | API/Backend | Database/Storage | Python script interacts with mongod directly; the backend process is NOT involved |
| Backup/restore (mongodump/mongorestore) | Database/Storage | — | Pure mongod tooling; independent of the FastAPI process |
| DATABASE_SCHEMA.md cleanup | Planning/docs tier | — | Markdown document update; no runtime impact |
| Smoke test after read-switch deploy | API/Backend | — | curl probes against live backend endpoints |

---

## Research Focus 1: mongodump / mongorestore Exact CLI

### What it is

The dry-run procedure requires: dump live DB → restore to a differently-named DB → apply migration on the dryrun DB → verify → drop dryrun DB. The production rollback path requires: restore backup over the live DB with `--drop`.

### Recommended approach (VERIFIED against live tooling)

**Tooling versions on VPS (VERIFIED):**
- mongodump: 100.16.1 [VERIFIED: `mongodump --version`]
- mongorestore: 100.16.1 [VERIFIED: `mongorestore --version`]
- mongosh: 2.8.3 [VERIFIED: `mongosh --version`]
- MongoDB server: 7.0.32 [VERIFIED: `mongosh --eval "db.version()" --quiet`]
- `--nsFrom` / `--nsTo` flags: AVAILABLE in mongorestore 100.16.1 [VERIFIED: `mongorestore --help`]

**Step 1 — Full-DB dump (backup or dryrun snapshot):**

```bash
# Pre-production backup (D-09)
BACKUP_DIR="/home/damnation/backups/pre-phase5-$(date +%Y%m%d-%H%M%S)"
mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out "$BACKUP_DIR"
# Output structure: $BACKUP_DIR/pltu_tenayan/<collection>.bson + <collection>.metadata.json
# Verify: count .bson files matches expected collection count
ls "$BACKUP_DIR/pltu_tenayan/"*.bson | wc -l   # expect 13 collections
```

**Step 2 — Restore to dryrun DB with namespace remapping (D-12):**

```bash
# Dump to tmp dir for dryrun (separate from the backup dir)
SNAP_DIR="/tmp/pltu_tenayan_snapshot_$(date +%Y%m%d-%H%M%S)"
mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out "$SNAP_DIR"

# Restore to dryrun DB — nsFrom/nsTo remaps every collection in the dump
mongorestore \
  --uri mongodb://localhost:27017 \
  --nsFrom 'pltu_tenayan.*' \
  --nsTo 'pltu_tenayan_migration_dryrun.*' \
  "$SNAP_DIR"
# Result: pltu_tenayan_migration_dryrun.smartstock, .sumberpemakaian, .app_settings, etc.
```

**Step 3 — Drop dryrun DB after verification:**

```bash
# Via mongosh (preferred — no ambiguity)
mongosh pltu_tenayan_migration_dryrun --eval "db.dropDatabase()"

# Or via pymongo from within the migration script:
# client.drop_database("pltu_tenayan_migration_dryrun")
```

**Step 4 — Production rollback (D-10, data-restore path only):**

```bash
# Code rollback (always first):
# git revert <merge-commit>  # reverts the server.py legacy-read edits
# cd /home/damnation/emits/pltu-tenayan-full-backup/backend
# <VPS Service Recovery procedure from LOCAL_SETUP.md>

# Data rollback (only if legacy collections were dropped AND data appears missing):
BACKUP_DIR="/home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS"
mongorestore \
  --drop \
  --uri mongodb://localhost:27017 \
  --nsInclude 'pltu_tenayan.*' \
  "$BACKUP_DIR"
# --drop drops each target collection before restoring from dump
# --nsInclude 'pltu_tenayan.*' restores only the pltu_tenayan namespace
```

### Pitfalls / landmines

- `--nsFrom`/`--nsTo` operate on the dump DIRECTORY, not `--db`. Pass the snapshot dir, not `$SNAP_DIR/pltu_tenayan/`. [VERIFIED: mongorestore --help output]
- `mongorestore --drop` with `--nsInclude` only drops collections it finds in the dump — it will NOT drop collections added post-backup. This is safe; the legacy collections were empty and are not in the dump.
- The dryrun DB name `pltu_tenayan_migration_dryrun` does NOT start with `pltu_tenayan_test_`, so the conftest.py safety guard (`assert TEST_DB_NAME.startswith("pltu_tenayan_test_")`) will not protect it. The migration script must have its own guard: assert `--target-db != "pltu_tenayan"` before any drop operation.
- Since the legacy collections do NOT exist in the live DB (confirmed), the dryrun will not find them either. The script's `--apply` step on the dryrun DB will find zero legacy collections and report "no work to do" — which is the correct, expected behavior and proves the system is already in a clean state. The planner must document this explicitly in the runbook so the operator is not confused.

### Source citations

- [VERIFIED: `mongodump --version`] — version 100.16.1
- [VERIFIED: `mongorestore --help`] — `--nsFrom`, `--nsTo`, `--nsInclude`, `--drop` flags confirmed present
- [VERIFIED: `mongosh --version`] — 2.8.3
- [VERIFIED: `mongosh --eval "db.version()" --quiet`] — 7.0.32

---

## Research Focus 2: Comprehensive server.py Legacy-Read Grep

### What it is

A complete audit of all legacy collection reads in `server.py`, closing the gap on `ai_conversations` (which Phase-3 audit did not anchor) and confirming the exact line set the planner must edit.

### Complete legacy-read inventory (VERIFIED)

**`db.smart_stock` (legacy — must switch to `db.smartstock`):**

| Line | Context |
|------|---------|
| 2379 | `penerimaan_data = await db.smart_stock.find(` — AI context builder, "smart_stock" module branch |
| 2395 | `total_penerimaan = await db.smart_stock.aggregate([` — AI context builder, same branch |
| 2863 | `total_penerimaan = await db.smart_stock.aggregate([` — `/ai/quick/smart-stock` endpoint |

**`db.sumber_pemakaian` (legacy — must switch to `db.sumberpemakaian`):**

| Line | Context |
|------|---------|
| 2387 | `pemakaian_data = await db.sumber_pemakaian.find(` — AI context builder, "smart_stock" module branch |
| 2398 | `total_pemakaian = await db.sumber_pemakaian.aggregate([` — AI context builder, same branch |
| 2868 | `total_pemakaian = await db.sumber_pemakaian.aggregate([` — `/ai/quick/smart-stock` endpoint |
| 2877 | `avg_usage = await db.sumber_pemakaian.aggregate([` — `/ai/quick/smart-stock` endpoint |

**`db.settings` (legacy — must switch to `db.app_settings`):**

| Line | Context |
|------|---------|
| 2427 | `settings = await db.settings.find_one({"type": "coa"})` — AI context builder, "coa_reconciliation" module branch |
| 2926 | `settings = await db.settings.find_one({"type": "coa"})` — `/ai/quick/coa-alerts` endpoint |
| 4346 | `settings = await db.settings.find_one({"type": "coa"})` — COA export PDF endpoint |

**`ai_conversations` (ZERO occurrences):**

`grep -n "ai_conversations" server.py` returns NO output. [VERIFIED]

The `ai_conversations` collection is completely absent from `server.py`. The only AI history collection reference is line 2266: `ai_chat_collection = db.ai_chat_history` — which already uses the canonical name. D-04 is satisfied by the existing code; the only work for D-04 is the ADR documentation (ADR-012) and the database-side drop of the empty `ai_conversations` collection (which does not exist in the live DB either — confirmed by `db.getCollectionNames()`).

**Important discrepancy from CONTEXT.md:**

CONTEXT.md cited lines 2377, 2385, 2425, 4382. The actual legacy-read lines are:

| CONTEXT.md cited | Actual lines | Discrepancy |
|-----------------|-------------|-------------|
| 2377 (`smart_stock`) | 2379, 2395, 2863 | 3 lines, not 1; line 2377 is a string literal "smart_stock" in a Python `if module in [...]` condition — NOT a collection read |
| 2385 (`sumber_pemakaian`) | 2387, 2398, 2868, 2877 | 4 lines, not 1 |
| 2425 (`settings`) | 2427, 2926, 4346 | 3 lines, not 2; line 4346, not 4382 |
| 4382 (`settings`) | 4346 | Line number differs by 36 (likely result of intervening edits after the Phase-3 audit) |

**Line 2377 clarification:** Line 2377 contains `if module in ["general", "smart_stock"]:` — this is a Python string literal comparing the `module` parameter, NOT a MongoDB collection read. It does NOT need to be changed by Phase 5.

**`db.app_settings` (canonical — DO NOT change):**

| Line | Context |
|------|---------|
| 3817 | `settings = await db.app_settings.find_one({"type": "coa"}, {"_id": 0})` — GET /settings/coa |
| 3825 | `await db.app_settings.update_one(` — PUT /settings/coa |
| 3901 | `coa_settings = await db.app_settings.find_one({"type": "coa"}, {"_id": 0})` — COA KPI endpoint |

**`db.smartstock` (canonical — DO NOT change):** lines 3078, 3083, 3130, 3257, 3261, 3283, 3313, 3325, 3637 — all CRUD endpoints.

**`db.sumberpemakaian` (canonical — DO NOT change):** lines 3352, 3357, 3363, 3429, 3535, 3538, 3557, 3576 — all CRUD endpoints.

### Pitfalls / landmines

- Line 2377 string `"smart_stock"` in `if module in ["general", "smart_stock"]` is NOT a collection read — do NOT edit it. The module string key is used in prompt-template dictionaries (line 2565: `"smart_stock": base_prompt + ...`) and must remain as-is.
- The `settings` local variable name (e.g., `settings = await db.settings.find_one(...)`) shadows the collection operation. After the edit, the local variable will still be named `settings` — that is fine; only the `db.settings` part changes to `db.app_settings`. The local variable name can stay `settings` or be renamed `app_settings` — either is correct Python. For minimal diff, leave the local variable name unchanged.
- There is no `from .settings import settings` or similar Python module import in `server.py` — confirmed by absence of any `import settings` pattern. The word "settings" is safe to grep for `db.settings` without import collision.

### Source citations

- [VERIFIED: `grep -n "db\.smart_stock\b" server.py`]
- [VERIFIED: `grep -n "db\.sumber_pemakaian\b" server.py`]
- [VERIFIED: `grep -n 'db\["settings"\]\|db\.settings\b\|db\["app_settings"\]\|db\.app_settings\b' server.py`]
- [VERIFIED: `grep -n "ai_conversations" server.py`] — zero results
- [VERIFIED: `mongosh pltu_tenayan --eval "db.getCollectionNames().join('\n')" --quiet`] — legacy collection names absent from live DB

---

## Research Focus 3: MongoDB Version Detection

### What it is

Version-specific behaviour of mongodump, mongorestore, and mongosh affects which flags are safe to use in the runbook and migration script.

### Findings (VERIFIED)

| Component | Version | Source |
|-----------|---------|--------|
| MongoDB server | **7.0.32** | `mongosh --eval "db.version()" --quiet` |
| mongodump | **100.16.1** | `mongodump --version` |
| mongorestore | **100.16.1** | `mongorestore --version` |
| mongosh | **2.8.3** | `mongosh --version` |
| Legacy `mongo` shell | NOT available | `mongo` command not found |

**Flag availability at this version:**
- `--nsFrom` / `--nsTo` in mongorestore: AVAILABLE [VERIFIED: mongorestore --help]
- `--nsInclude` in mongorestore: AVAILABLE [VERIFIED: mongorestore --help]
- `--drop` in mongorestore: AVAILABLE [VERIFIED: mongorestore --help]
- `--uri` in mongodump: AVAILABLE [VERIFIED: mongodump --help shows `--uri=mongodb-uri`]
- `mongosh` (modern shell): AVAILABLE — use `mongosh` not `mongo` in all runbook commands

MongoDB 7.0 deprecates the `dbHash` command in some contexts but it is still available [ASSUMED — not tested live; see Research Focus 4 for the recommended alternative].

### Source citations

- [VERIFIED: shell probes listed above]

---

## Research Focus 4: Checksum Verification Strategy

### What it is

D-12 mandates that `--verify` mode emits "row counts and field-level checksums" to confirm zero data-loss. The migration ONLY drops empty legacy collections; the canonical collections are untouched. Therefore the checksums are taken on canonical collections BEFORE and AFTER `--apply` and must be byte-identical.

### Recommended approach

**Method: per-document JSON-md5, sorted aggregate** [RECOMMENDED — portable, no deprecated commands]

```python
import hashlib
import json
from pymongo import MongoClient

def collection_checksum(db, collection_name: str) -> dict:
    """
    Compute a deterministic checksum over all documents in a collection.

    Strategy:
    - Fetch all documents sorted by _id (stable iteration order).
    - Serialize each as json.dumps(doc, sort_keys=True, default=str) — handles
      ObjectId, datetime, Decimal128 via default=str.
    - md5 over the concatenation of all per-doc hashes (sorted lexicographically
      to make the aggregate order-independent).
    - Returns {"count": int, "checksum": str (hex)}.

    Performance: on 207 + 208 + 1 + 10 = 426 documents total, completes in < 1 s.
    """
    docs = list(db[collection_name].find({}, {"_id": 0}).sort("_id", 1))
    count = len(docs)
    per_doc_hashes = sorted(
        hashlib.md5(
            json.dumps(doc, sort_keys=True, default=str).encode()
        ).hexdigest()
        for doc in docs
    )
    aggregate = hashlib.md5("|".join(per_doc_hashes).encode()).hexdigest()
    return {"count": count, "checksum": aggregate}


CANONICAL_COLLECTIONS = ["smartstock", "sumberpemakaian", "app_settings", "ai_chat_history"]

def verify(target_db_name: str, label: str, client: MongoClient):
    db = client[target_db_name]
    print(f"\n=== VERIFY: {label} ({target_db_name}) ===")
    results = {}
    for coll in CANONICAL_COLLECTIONS:
        r = collection_checksum(db, coll)
        print(f"  {coll}: count={r['count']}, checksum={r['checksum']}")
        results[coll] = r
    return results

# Usage in migration script --verify mode:
# before = verify("pltu_tenayan_migration_dryrun", "BEFORE", client)
# ... apply() ...
# after = verify("pltu_tenayan_migration_dryrun", "AFTER", client)
# assert before == after, f"CHECKSUM MISMATCH: {before} != {after}"
```

**Why not `dbHash`?** MongoDB's `dbHash` command hashes each collection using a deterministic algorithm and is available in 7.0, but its output format changed across versions and it requires admin privilege. The md5-over-JSON approach is portable, testable, and version-independent. [ASSUMED — dbHash not tested live]

**Performance budget:** 207 + 208 + 1 + 10 = 426 total documents. JSON serialization + md5 for 426 docs is sub-second on any modern machine. Well within the 30-second budget.

**Expected `--verify` output on a clean dryrun run (since legacy collections do not exist in live DB):**

Since legacy collections are not present in the live DB at all, the dryrun DB (restored from a snapshot) will also have no legacy collections. The `--apply` step will iterate the 4 legacy names, find each has 0 documents or does not exist, and the drop step will be a no-op. The checksums of canonical collections will be byte-identical before and after because the apply step touched nothing. This is the CORRECT result — Phase 5 is cleaning up code reads, not data.

### Source citations

- [VERIFIED: `mongosh pltu_tenayan --eval "['smartstock','sumberpemakaian','app_settings','ai_chat_history'].forEach(c=>print(c+': '+db[c].countDocuments()))" --quiet`] — 207, 208, 1, 10
- [ASSUMED] dbHash availability in MongoDB 7.0 — not tested

---

## Research Focus 5: Migration Script Idempotency

### What it is

The migration script must be safe to run twice without producing a different result on the second run.

### Recommended approach

**Script interface:**

```
migrate_collection_names.py [--target-db DB_NAME] [--apply] [--verify]

Flags:
  --target-db DB_NAME   Target database (default: pltu_tenayan).
                        SAFETY GUARD: if not set and DB_NAME env var == "pltu_tenayan",
                        the script demands explicit --target-db confirmation.
  --apply               Execute the drop of empty legacy collections.
                        Without this flag, the script runs in dry-run mode:
                        it reports what it WOULD do without doing it.
  --verify              Emit row counts and md5 checksums for all 4 canonical
                        collections. Can be combined with --apply to verify
                        before and after.
```

**Idempotency patterns:**

```python
LEGACY_COLLECTIONS = ["smart_stock", "sumber_pemakaian", "settings", "ai_conversations"]
CANONICAL_COLLECTIONS = ["smartstock", "sumberpemakaian", "app_settings", "ai_chat_history"]

def apply(db):
    for legacy_name in LEGACY_COLLECTIONS:
        existing_names = db.list_collection_names()

        if legacy_name not in existing_names:
            print(f"  [SKIP] {legacy_name}: does not exist (already clean or never created)")
            continue

        # Pre-drop count-check (D-07)
        count = db[legacy_name].count_documents({})
        if count > 0:
            raise RuntimeError(
                f"HALT: {legacy_name} has {count} document(s). "
                f"This phase assumes all legacy collections are empty. "
                f"Investigate before proceeding — do NOT drop."
            )

        # Drop empty legacy collection
        db[legacy_name].drop()
        print(f"  [DROPPED] {legacy_name} (was empty, confirmed count=0)")

    print("\nApply complete. All legacy collections dropped (or were absent).")
```

**Idempotency guarantee:**
- Run 1 on dryrun DB that has legacy collections: finds them, count=0, drops them, exits 0.
- Run 2 on same dryrun DB: legacy names not in `list_collection_names()`, prints SKIP for each, exits 0.
- Run `--verify` after `--apply`: checksums match (canonical collections untouched). CLEAN.

**Dry-run DB existence check (at start of `--apply` on dryrun DB):**

```python
def check_dryrun_db(client, dryrun_db_name):
    """
    Dryrun-specific guard: if the dryrun DB does not exist or has no
    collections, report 'no work to do' and exit 0.
    This happens when legacy collections are absent from the live DB
    (as confirmed for pltu_tenayan on 2026-05-11).
    """
    colls = client[dryrun_db_name].list_collection_names()
    legacy_present = [c for c in LEGACY_COLLECTIONS if c in colls]
    if not legacy_present:
        print(f"[INFO] No legacy collections found in {dryrun_db_name}. No work to do.")
        return False
    return True
```

### Pitfalls / landmines

- The conftest.py `_backend_lifecycle` fixture injects `MONGO_TEST_DB_NAME` into the spawned uvicorn subprocess. The migration script reads `--target-db` from its own CLI args, NOT from `MONGO_TEST_DB_NAME`. These two env vars do NOT interfere. However: if someone runs `python migrate_collection_names.py` from within a pytest session without providing `--target-db`, the default falls back to `DB_NAME` env var which is `"pltu_tenayan"` — that would target production. The safety guard (require `--target-db` or explicit confirmation when target is "pltu_tenayan") prevents this.
- `db.list_collection_names()` is a synchronous pymongo call. The migration script uses synchronous pymongo (not async motor), because it is a standalone operator script, not a FastAPI route handler.

### Source citations

- `pltu-tenayan-full-backup/backend/tests/conftest.py:159-168` — `_drop_test_db` safety guard pattern (`if not TEST_DB_NAME.startswith("pltu_tenayan_test_"): return`)
- [VERIFIED: codebase grep and live DB state]

---

## Research Focus 6: AI Module Post-Migration Smoke Test

### What it is

Once Phase 5 lands, the AI module starts reading REAL data from canonical collections (207 smartstock + 208 sumberpemakaian + 1 app_settings records) instead of the empty legacy collections. This is a behavioral change — AI endpoints will now return non-empty context.

### Affected AI endpoints and code paths

**Endpoint 1: `GET /ai/quick/smart-stock`** (lines 2859–2902)

```
db.smart_stock → db.smartstock (3 lines: 2863, 2868, 2877)
```

After migration: `total_penerimaan` aggregate will return actual data (207 records). `avg_usage` will return actual 30-day average. The return shape is a simple dict with numeric fields — no code path assumes empty. `if total_penerimaan else 0` guards handle both cases. **Risk: LOW** — handles non-empty gracefully.

**Endpoint 2: `GET /ai/quick/coa-alerts`** (lines 2904–2960)

```
db.settings → db.app_settings (line 2926)
```

After migration: `settings.get("price_per_kcal_per_ton", 50)` reads the real value (currently hardcoded default 50 from the empty legacy). With app_settings having 1 record (type="coa"), the real price will be used in the potential_loss calculation. The `if settings else 50` guard handles both cases. **Risk: LOW** — handles non-empty gracefully. However, the **potential_loss value will change** when the real price is read — this is a behavioral change the operator should observe in the 48h window.

**Endpoint 3: `POST /ai/query`** (line 2621) — context builder function (lines ~2320-2453)

```
db.smart_stock (lines 2379, 2395)
db.sumber_pemakaian (lines 2387, 2398)
db.settings (line 2427)
```

After migration: the context builder will include real data in the AI prompt. `if penerimaan_data:` and `if pemakaian_data:` guards on lines 2383, 2391 handle non-empty correctly. The `if settings else 50` pattern on line 2428 is safe. **Risk: LOW** — all branches handle non-empty.

**Endpoint 4: COA export PDF** (line 4346)

```
db.settings → db.app_settings
```

After migration: `price_per_kcal` reads real value from app_settings. Same pattern: `settings.get(..., 50) if settings else 50`. **Risk: LOW**.

### Recommended smoke-test procedure

Run AFTER deploying the server.py read-path edits (D-06 step 1-3), BEFORE the 48h observation window:

```bash
# Source admin credentials from test_credentials.md
cd /home/damnation/emits/pltu-tenayan-full-backup
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"

# 1. Login and capture token
TOKEN=$(curl -fsS -X POST http://localhost:8013/api/auth/login \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,os;print(json.dumps({'email':os.environ['TEST_ADMIN_EMAIL'],'password':os.environ['TEST_ADMIN_PASSWORD']}))")" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

# 2. Smoke: /ai/quick/smart-stock — should now return non-zero penerimaan
curl -fsS http://localhost:8013/api/ai/quick/smart-stock \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 3. Smoke: /ai/quick/coa-alerts — potential_loss now uses real price_per_kcal
curl -fsS http://localhost:8013/api/ai/quick/coa-alerts \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 4. Smoke: AI query (general module) — context should now include real smart stock data
curl -fsS -X POST http://localhost:8013/api/ai/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "berapa total stok batubara saat ini?", "module": "smart_stock"}' \
  | python3 -m json.tool

unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD TOKEN
```

**What to look for:**
- `/ai/quick/smart-stock`: `total_penerimaan > 0`, `current_stock` is a realistic number (not 0).
- `/ai/quick/coa-alerts`: Response returns 200; `potential_loss` may differ from the pre-migration value (expected — now uses real settings).
- `/ai/query` (smart_stock module): Response returns 200; no 500 errors.

### Source citations

- `pltu-tenayan-full-backup/backend/server.py:2859-2902` — get_smart_stock_summary
- `pltu-tenayan-full-backup/backend/server.py:2904-2960` — get_coa_alerts
- `pltu-tenayan-full-backup/backend/server.py:2379-2406` — AI context builder (smart_stock branch)
- `pltu-tenayan-full-backup/backend/server.py:2427-2436` — AI context builder (coa_reconciliation settings branch)

---

## Research Focus 7: MIGRATION_RUNBOOK.md Placement + Structure

### Recommended placement

`pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` — top-level of the inner repo, alongside `LOCAL_SETUP.md`.

Rationale: LOCAL_SETUP.md §"VPS Service Recovery" is the operator reference for deploy/restart and lives at the inner-repo top level. MIGRATION_RUNBOOK.md is a sibling operator document. The test runner document `TEST-RUNNER.md` lives inside `tests/` because it is test-infrastructure-specific; MIGRATION_RUNBOOK.md is broader (covers backup, deploy, and DB operations) and belongs at the top level. [ASSUMED — no existing `docs/runbooks/` directory confirmed]

### Recommended sections and content

```markdown
# MIGRATION_RUNBOOK.md — Collection Naming Debt Resolution

## 0. Prerequisites
- mongodump, mongorestore, mongosh available on PATH (all available on VPS — verified 2026-05-11)
- Python venv at backend/.venv is active
- DB_NAME=pltu_tenayan is set
- Admin credentials sourced from memory/test_credentials.md (per LOCAL_SETUP.md §9)

## 1. Backup Procedure (D-09)
Full-DB mongodump before any production change. Commands verbatim.

## 2. Dryrun Procedure (D-12)
mongodump snapshot → mongorestore to pltu_tenayan_migration_dryrun → run script --verify BEFORE + --apply + --verify AFTER → confirm checksums match → drop dryrun DB.

## 3. Read-Path Switch Deploy (D-06 steps 1–3)
server.py edits (already committed) → git pull → restart uvicorn per LOCAL_SETUP.md §"VPS Service Recovery" → smoke test (Research Focus 6 curl commands).

## 4. Observation Window Checklist (≥48h)
Checklist items operator verifies during the 48h window before dropping legacy collections.

## 5. pytest Regression Gate (D-14)
`cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q` must exit 0. Follow TEST-RUNNER.md for credential setup.

## 6. Legacy-Drop Procedure (D-06 step 5)
Run `python scripts/migrate_collection_names.py --apply` (target-db defaults to pltu_tenayan after production confirmation). Re-verify with --verify.

## 7. Rollback Procedure
### 7a. Code-only rollback
git revert + redeploy.
### 7b. Full data restore
mongorestore --drop from backup dir.

## 8. Cleanup Procedure (DEBT-05)
DATABASE_SCHEMA.md update — remove "legacy" markings per plan 05-04.

## 9. Cross-References
- LOCAL_SETUP.md §"VPS Service Recovery" — uvicorn restart commands.
- TEST-RUNNER.md — pytest credential setup.
- .planning/decisions/ADR-009..012 — canonical name sources.

## 10. Backup Retention
Keep pre-phase5 backup for ≥30 days after milestone v1.0 close (D-11).
```

### Documentation style (from TEST-RUNNER.md) [VERIFIED]

- Numbered steps with exact commands in bash fences
- "Expected:" comments after verification commands
- Troubleshooting section at bottom
- Cross-references to other operator documents by file path + section anchor
- No inline credentials — source from env vars

### Source citations

- `pltu-tenayan-full-backup/LOCAL_SETUP.md:245-333` — §"VPS Service Recovery" structure [VERIFIED]
- `pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md` — documentation style [VERIFIED]

---

## Research Focus 8: DATABASE_SCHEMA.md Cleanup Scope (DEBT-05)

### What it is

DEBT-05 requires removing "legacy" markings from DATABASE_SCHEMA.md and code comments post-migration. This is a documentation-only change.

### Exact lines / sections containing "legacy" markings [VERIFIED by grep]

| Line | Content | Action |
|------|---------|--------|
| 13 | "Beberapa nama koleksi menunjukkan adanya legacy/transitional structure" | Rewrite: remove "legacy/transitional structure" reference; state collection names are standardized |
| 27 | `- smart_stock` (in collection list) | Delete this entry (legacy name, no longer in DB) |
| 28 | `- sumber_pemakaian` (in collection list) | Delete this entry |
| 34 | `- ai_conversations` (in collection list) | Delete this entry |
| 37 | "smartstock dan smart_stock tampak hidup berdampingan; ini mengindikasikan naming legacy/transisi" | Delete or rewrite |
| 38 | "sumber_pemakaian dan sumberpemakaian juga mengindikasikan pola serupa" | Delete or rewrite |
| 40 | "ai_chat_history dan ai_conversations..." | Delete or rewrite |
| 374 | `## 9.1 smartstock / smart_stock` | Rename to `## 9.1 smartstock` |
| 412 | `## 9.2 Catatan naming` (the "kode aktif list smart stock membaca dari db.smartstock, tetapi nama smart_stock juga muncul..." paragraph) | Delete entirely (no longer true) |
| 419 | `## 10.1 sumber_pemakaian / sumberpemakaian` | Rename to `## 10.1 sumberpemakaian` |
| 452 | "Seperti smart stock, ada indikasi naming legacy yang harus distandardisasi" | Delete |
| 554 | `## 12.2 settings` section: "Muncul di kode, namun penggunaan aktifnya perlu diverifikasi. Potensial legacy/global settings collection." | Delete the entire `## 12.2 settings` subsection |
| 576 | "Masih relevan untuk compatibility/history lama, namun fitur session-based yang lebih jelas kini menggunakan ai_conversations" | Rewrite: ai_chat_history is the canonical collection; ai_conversations was a legacy duplicate, now dropped |
| 578 | `## 13.2 ai_conversations` section | Delete the entire section |
| 629 | `ai_conversations.user_id → users.id` in relations table | Delete this row |
| 651–656 | Section 16.1 "Naming Koleksi" with 4 standardization bullets | Replace with "Resolved by Phase 5 (2026-MM-DD)" or delete section 16.1 |
| 682 | `sumber_pemakaian` in index recommendations table | Update to `sumberpemakaian` |
| 685 | `ai_conversations` in index recommendations table | Delete this row |
| 697–739 | §"Duplicate Pair Active Read Targets (Phase-3 audit...)" entire section | See recommendation below |

### Recommended treatment for the Phase-3 audit table (lines 695–739)

**Option A — Archive with resolved annotation (RECOMMENDED):**

Rename the section to `## Duplicate Pair Resolution Log (Phase-3 audit + Phase-5 resolution)` and add a resolved-date row per pair:

```markdown
## Duplicate Pair Resolution Log

| Pair | Canonical | Legacy (resolved) | Resolved | Notes |
|------|-----------|------------------|----------|-------|
| smartstock / smart_stock | smartstock | smart_stock | Phase 5 (2026-XX-XX) | Dropped; 0 records at drop time |
| sumberpemakaian / sumber_pemakaian | sumberpemakaian | sumber_pemakaian | Phase 5 (2026-XX-XX) | Dropped; 0 records at drop time |
| app_settings / settings | app_settings | settings | Phase 5 (2026-XX-XX) | Dropped; 0 records at drop time |
| ai_chat_history / ai_conversations | ai_chat_history | ai_conversations | Phase 5 (2026-XX-XX) | Dropped; 0 records at drop time (collection was absent from live DB) |
```

This preserves audit provenance while being clear that the debt is resolved.

**Option B — Delete entirely:** Simpler, but loses the audit trail.

**Recommendation:** Option A. The Phase-3 audit methodology and row-count evidence are useful historical context.

### Source citations

- [VERIFIED: `grep -n "legacy\|duplicate\|smart_stock\|sumber_pemakaian\|ai_conversations" DATABASE_SCHEMA.md`]

---

## Research Focus 9: Plan Decomposition Recommendation

See `## Plan Decomposition Recommendation` section below.

---

## Research Focus 10: Validation Architecture

See `## Validation Architecture` section below.

---

## Research Focus 11: Pitfalls / Landmines Specific to This Codebase

### Pitfall A: MONGO_TEST_DB_NAME contamination

**What goes wrong:** The conftest.py `_backend_lifecycle` fixture sets `os.environ["MONGO_TEST_DB_NAME"] = TEST_DB_NAME` at module import time. If the migration script is run inside a pytest session (e.g., via `subprocess.run(["python", "migrate_collection_names.py"])` from a test), it will inherit `MONGO_TEST_DB_NAME` from the environment.

**Why it matters:** The migration script must NOT read `MONGO_TEST_DB_NAME`. It reads only `--target-db` CLI arg and `DB_NAME` env var.

**Prevention:** Migration script ignores `MONGO_TEST_DB_NAME` entirely. It reads `DB_NAME` env var as its production-DB default but requires `--target-db` for any non-interactive run. The safety guard (assert target != production without explicit flag) prevents accidents.

### Pitfall B: `settings` variable name collision

**What goes wrong:** After editing `db.settings.find_one(...)` to `db.app_settings.find_one(...)`, the local variable is still named `settings = await db.app_settings.find_one(...)`. This is valid Python. However, the variable `settings` is used in the lines immediately after (e.g., `price_per_kcal = settings.get(..., 50) if settings else 50`). No change needed to those lines — they reference the local variable, not the collection.

**Prevention:** Make the minimal diff: change only `db.settings` → `db.app_settings` on the three affected lines. Do not rename the local variable `settings` → that would be a broader refactor and is out of Phase 5 scope.

### Pitfall C: Test/migration ordering — `_seed_baseline_data` does NOT seed legacy collections

**What goes wrong:** The conftest.py `_seed_baseline_data` fixture seeds `merit_order` documents and an admin user. It does NOT insert data into any of the 4 legacy collections (`smart_stock`, `sumber_pemakaian`, `settings`, `ai_conversations`). If the migration script is run during a pytest session against the test DB, the script will find 0 legacy collections and exit cleanly. This is the correct behavior.

**Why it matters:** The planner does NOT need to add a test that seeds legacy data and then drops it. The migration script's dryrun test (Plan 05-02) uses the real production snapshot, not the Phase-4 factory infrastructure.

### Pitfall D: mongodump on a live backend — read consistency

**What goes wrong (potential concern):** mongodump on a live database while uvicorn is writing takes per-collection point-in-time snapshots, not a single cross-collection snapshot.

**Why this is NOT a concern for Phase 5:** All 4 legacy collections have 0 records and are not written to by any active code path. The canonical collections (smartstock, sumberpemakaian, app_settings, ai_chat_history) may receive writes during the dump, but Phase 5 does not migrate data between collections — it only drops empty collections. The backup integrity is sufficient for rollback: any documents written after the dump would need to be manually re-entered, but since we are only dropping empty legacy collections (not canonical ones), no data is at risk.

**Documentation:** Note this in MIGRATION_RUNBOOK.md §1 as a non-concern with explanation.

### Pitfall E: `ai_conversations` collection does not exist in live DB

**What goes wrong:** A planner might create a drop task for `ai_conversations` expecting the collection to exist. It does NOT exist in the live `pltu_tenayan` DB.

**Correct handling:** The migration script's idempotency pattern (`if legacy_name not in db.list_collection_names(): print("SKIP, does not exist")`) handles this transparently. The ADR still documents the canonical choice (D-04). The DATABASE_SCHEMA.md cleanup still removes `ai_conversations` mentions. The "drop" task is a no-op at execution time.

### Pitfall F: Line number drift between Phase-3 audit and current server.py

**What goes wrong:** The Phase-3 audit cited specific line numbers (2377, 2385, 2425, 4382). Current server.py has the legacy reads at 2379/2395/2863, 2387/2398/2868/2877, 2427/2926/4346. Line numbers shifted.

**Prevention:** The implementation task must grep for `db.smart_stock`, `db.sumber_pemakaian`, `db.settings` immediately before making edits to confirm current line numbers — never rely on Phase-3 audit line citations.

---

## Research Focus 12: Anti-Patterns

| Anti-Pattern | Why Bad | Correct Practice |
|---|---|---|
| Drop collection without pre-drop count assertion | Data loss if a silent write path was missed | D-07: `count_documents({}) == 0` before every `drop()` |
| Run migration on production without dry-run first | Cannot verify checksum parity without a test environment | D-12: always dry-run on `pltu_tenayan_migration_dryrun` first |
| Commit ADR + code edits in the same commit | Violates two-repo commit boundary (outer `.planning/` vs inner `pltu-tenayan-full-backup/`) | ADRs committed to outer repo; server.py edits committed to inner repo |
| Claim DEBT-02 closed without showing `--verify` output | Silent assumption that checksums match | `--verify` must emit checksums BEFORE and AFTER; both must match and be present in the plan summary |
| Leave "legacy" annotations in DATABASE_SCHEMA.md post-migration | DEBT-05 explicitly requires removal | Plan 05-04 must update DATABASE_SCHEMA.md as part of the plan, not deferred |
| Edit line 2377 (the `if module in ["general", "smart_stock"]` string) | This is a module key string, not a collection name | Only edit lines where `db.smart_stock` / `db.sumber_pemakaian` / `db.settings` appear as collection access |

---

## Standard Stack

### Core (Phase 5)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pymongo | 4.x (pinned in requirements.txt) | Migration script sync DB operations | Motor (async) is for FastAPI; standalone script uses sync pymongo |
| mongodump | 100.16.1 (on VPS) | Full-DB backup | Official MongoDB tooling |
| mongorestore | 100.16.1 (on VPS) | DB restore + namespace remapping | Official MongoDB tooling |
| mongosh | 2.8.3 (on VPS) | DB inspection and drop commands | Replaces legacy `mongo` shell |
| hashlib + json (stdlib) | Python stdlib | Collection checksums | No external dependency needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| motor (existing) | 3.3.1 | Async DB access in FastAPI | server.py edits only |
| pytest | existing | Regression test after edits | Phase 5 gate (D-14) |

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-DB backup | Custom BSON serializer | `mongodump` | Edge cases: oplog capture, index metadata, gridfs — mongodump handles all |
| DB restore + namespace remap | Python copy-collection loop | `mongorestore --nsFrom/--nsTo` | Handles BSON types, indexes, metadata files atomically |
| Collection existence check | Regex on error message | `db.list_collection_names()` | Direct, stable API |
| Checksum of MongoDB collection | MongoDB JS `$function` aggregation | Python md5-over-JSON | More portable; no server-side JS dependency; no mongosh required at verify time |

---

## Architecture Patterns

### Migration Script Structure

```
pltu-tenayan-full-backup/scripts/
├── check_credentials.sh          # Existing pattern (bash one-shot operator script)
└── migrate_collection_names.py   # Phase 5 deliverable (Python, sync pymongo)
```

### Recommended Project Structure (Phase 5 deliverables)

```
.planning/decisions/
├── ADR-001..008-*.md             # Existing
├── ADR-009-canonical-smartstock.md    # Phase 5 new
├── ADR-010-canonical-sumberpemakaian.md
├── ADR-011-canonical-app-settings.md
└── ADR-012-canonical-ai-chat-history.md

pltu-tenayan-full-backup/
├── MIGRATION_RUNBOOK.md          # Phase 5 new (top-level, next to LOCAL_SETUP.md)
├── backend/
│   └── server.py                 # 10 line edits (3+4+3 for the 3 pairs)
└── scripts/
    └── migrate_collection_names.py  # Phase 5 new
```

### ADR Pattern (from ADR-001..008) [VERIFIED]

```markdown
# ADR-NNN: [Title]

## Status

Accepted (locked, YYYY-MM-DD) — [rationale or predecessor reference]

## Context

[Why this decision was needed; Phase-3 audit evidence; CONS-collection-naming-debt]

## Decision

[The canonical name and what it means for Phase 5]

## Consequences

**Positive:** [...]
**Negative / accepted tradeoffs:** [...]

## Alternatives Considered

[The rejected alternative name; why rejected]

## References

- Phase-3 audit: pltu-tenayan-full-backup/DATABASE_SCHEMA.md §"Duplicate Pair Active Read Targets" (lines 704-707)
- Code evidence: server.py:LINE (canonical CRUD read); server.py:LINE (legacy AI read — fixed in Phase 5)
- .planning/REQUIREMENTS.md DEBT-01 (or whichever DEBT-NN applies)
```

### Anti-Patterns to Avoid

- **Bidirectional copy step:** Rejected by D-08 — all legacy collections are empty, copy adds complexity without safety.
- **Dual-read window (read both, prefer canonical):** Rejected by user — over-engineered for empty legacy collections.
- **Per-collection granular backup (.bson per collection):** Rejected by D-09 — full DB backup via `mongodump` is sufficient.

---

## Runtime State Inventory

This is a rename/code-switch phase (reading canonical instead of legacy collection names). The four legacy collections contain 0 documents and do NOT exist in the live DB.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — legacy collections (`smart_stock`, `sumber_pemakaian`, `settings`, `ai_conversations`) have 0 documents and do NOT exist in `pltu_tenayan` | No data migration needed; drop-if-exists is a no-op |
| Live service config | None — no external service config (Datadog, n8n, Tailscale) references these collection names | None |
| OS-registered state | None — no Task Scheduler / pm2 / systemd / launchd entries reference these collection names | None |
| Secrets and env vars | `DB_NAME=pltu_tenayan` in backend/.env — not changed by Phase 5 | None |
| Build artifacts | None — Python scripts have no compiled artifacts; no egg-info for the migration script | None |

**Key runtime finding:** The legacy collection names are absent from the live `pltu_tenayan` DB entirely. `db.getCollectionNames()` returns only the 13 canonical collection names. The Phase 5 "drop" step is a no-op on the live DB — but the code still reads from the legacy names (which Motor/pymongo silently treats as reads against an empty or non-existent collection, returning empty results). That is the silent data-gap the phase resolves by switching the code reads.

---

## Common Pitfalls

### Pitfall 1: Line number drift from Phase-3 audit citations

**What goes wrong:** CONTEXT.md cited specific line numbers that have drifted. The actual legacy-read lines are different (see Research Focus 2 complete table).
**Why it happens:** Code changed between Phase-3 audit (2026-05-10) and now.
**How to avoid:** Always grep immediately before editing; never trust archived line numbers.
**Warning signs:** If `diff` shows no change after supposedly editing line 2425, the edit landed on the wrong line.

### Pitfall 2: Missing the `/ai/quick/smart-stock` endpoint reads (lines 2863, 2868, 2877)

**What goes wrong:** The CONTEXT.md audit table said lines 2377 and 2385 are the AI module reads. The `/ai/quick/smart-stock` endpoint at lines 2859–2902 is a SEPARATE endpoint that ALSO reads from `db.smart_stock` (line 2863) and `db.sumber_pemakaian` (lines 2868, 2877). Missing these 3 lines means the endpoint still reads from legacy after the migration — a partially-applied fix.
**How to avoid:** Use the comprehensive grep output from Research Focus 2; address all 10 lines.
**Warning signs:** Post-deploy, `GET /api/ai/quick/smart-stock` still returns `total_penerimaan: 0` instead of the real 207-record aggregate.

### Pitfall 3: Missing the second `db.settings` read at `/ai/quick/coa-alerts` (line 2926)

**What goes wrong:** CONTEXT.md listed 2425 and 4382 as the only `db.settings` reads. There is a third at line 2926 in the `/ai/quick/coa-alerts` endpoint. Missing it means coa-alerts still uses hardcoded default pricing after the migration.
**How to avoid:** Use Research Focus 2 grep results; all three `db.settings` lines (2427, 2926, 4346) must be changed.
**Warning signs:** Post-deploy, `/api/ai/quick/coa-alerts` potential_loss still uses default price (50) rather than the real setting.

### Pitfall 4: dryrun confusion when legacy collections are absent

**What goes wrong:** Operator runs `migrate_collection_names.py --apply --target-db pltu_tenayan_migration_dryrun` and sees "no work to do" messages for all 4 collections. May interpret this as the script being broken.
**Why it happens:** The legacy collections don't exist in the live DB, so the dryrun DB snapshot won't have them either.
**How to avoid:** Document this explicitly in MIGRATION_RUNBOOK.md §2: "If the script reports 'SKIP — collection does not exist' for all 4 legacy names, this is the EXPECTED result. It confirms the live DB is already clean. Proceed to step 3 (code deploy)."

### Pitfall 5: `pytest` picks up the migration script and tries to test it as a module

**What goes wrong:** If `migrate_collection_names.py` is placed in `backend/scripts/` (inside the `backend/` tree), pytest discovery may import it.
**How to avoid:** Place the script at `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` (the existing `scripts/` directory, outside `backend/tests/`). The conftest.py only discovers tests in `tests/`.

---

## Code Examples

### Migration script skeleton (verified patterns)

```python
#!/usr/bin/env python3
"""
migrate_collection_names.py — Phase 5 Collection Naming Debt Resolution
Usage:
  python migrate_collection_names.py [--target-db DB] [--apply] [--verify]

Source: pltu-tenayan-full-backup/backend/tests/conftest.py (safety-guard pattern)
"""
import argparse
import hashlib
import json
import sys
from pymongo import MongoClient

LEGACY_TO_CANONICAL = {
    "smart_stock": "smartstock",
    "sumber_pemakaian": "sumberpemakaian",
    "settings": "app_settings",
    "ai_conversations": "ai_chat_history",
}
CANONICAL_COLLECTIONS = list(LEGACY_TO_CANONICAL.values())
PRODUCTION_DB = "pltu_tenayan"


def collection_checksum(db, collection_name: str) -> dict:
    docs = list(db[collection_name].find({}, {"_id": 0}).sort("_id", 1))
    count = len(docs)
    per_doc_hashes = sorted(
        hashlib.md5(
            json.dumps(doc, sort_keys=True, default=str).encode()
        ).hexdigest()
        for doc in docs
    )
    aggregate = hashlib.md5("|".join(per_doc_hashes).encode()).hexdigest() if per_doc_hashes else "empty"
    return {"count": count, "checksum": aggregate}


def verify_checksums(db, target_db_name: str) -> dict:
    print(f"\n--- Checksums for {target_db_name} ---")
    results = {}
    for coll in CANONICAL_COLLECTIONS:
        r = collection_checksum(db, coll)
        print(f"  {coll}: count={r['count']}, checksum={r['checksum']}")
        results[coll] = r
    return results


def apply_migration(db, dry_run: bool = True):
    for legacy_name, canonical_name in LEGACY_TO_CANONICAL.items():
        existing = db.list_collection_names()
        if legacy_name not in existing:
            print(f"  [SKIP] {legacy_name} — does not exist (already clean or never created)")
            continue
        count = db[legacy_name].count_documents({})
        if count > 0:
            print(f"  [HALT] {legacy_name} has {count} document(s)! Expected 0. Aborting.", file=sys.stderr)
            sys.exit(1)
        if dry_run:
            print(f"  [DRY-RUN] Would drop {legacy_name} (count=0, canonical={canonical_name})")
        else:
            db[legacy_name].drop()
            print(f"  [DROPPED] {legacy_name} (count=0, canonical={canonical_name})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-db", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    import os
    target_db = args.target_db or os.environ.get("DB_NAME", PRODUCTION_DB)

    # Safety guard: production target requires explicit --target-db flag
    if target_db == PRODUCTION_DB and args.target_db is None:
        print(f"ERROR: Targeting production DB '{PRODUCTION_DB}' requires explicit --target-db {PRODUCTION_DB}.", file=sys.stderr)
        sys.exit(1)

    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = MongoClient(mongo_url)
    db = client[target_db]

    if args.verify:
        before = verify_checksums(db, target_db)

    if args.apply:
        print(f"\n--- Apply migration on {target_db} ---")
        apply_migration(db, dry_run=False)
    elif not args.verify:
        print(f"\n--- Dry-run on {target_db} (use --apply to execute) ---")
        apply_migration(db, dry_run=True)

    if args.verify and args.apply:
        after = verify_checksums(db, target_db)
        if before != after:
            print("CHECKSUM MISMATCH — canonical collections changed during migration!", file=sys.stderr)
            sys.exit(1)
        print("\n[OK] Checksums match before and after. Zero data loss confirmed.")

    client.close()


if __name__ == "__main__":
    main()
```

### server.py edit examples (minimal diff)

```python
# BEFORE (line 2379):
penerimaan_data = await db.smart_stock.find(
# AFTER:
penerimaan_data = await db.smartstock.find(

# BEFORE (line 2395):
total_penerimaan = await db.smart_stock.aggregate([
# AFTER:
total_penerimaan = await db.smartstock.aggregate([

# BEFORE (line 2427):
settings = await db.settings.find_one({"type": "coa"})
# AFTER:
settings = await db.app_settings.find_one({"type": "coa"})
# NOTE: local variable name "settings" unchanged — only db.settings → db.app_settings
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `mongo` shell (legacy) | `mongosh` (modern) | MongoDB 6.0+ | Runbook must use `mongosh`, not `mongo` — confirmed `mongo` not available on VPS |
| `db.runCommand({dbHash: 1})` | md5-over-JSON in Python | Still available in 7.0 but requires admin privilege | Python approach is more portable and testable |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `dbHash` requires admin privilege in MongoDB 7.0 | Research Focus 4 | Low — the md5-over-JSON alternative is the recommended approach regardless |
| A2 | No existing `docs/runbooks/` directory in pltu-tenayan-full-backup | Research Focus 7 | Low — if it exists, place MIGRATION_RUNBOOK.md there; otherwise top-level is correct |

---

## Open Questions (RESOLVED 2026-05-11)

Both questions resolved by the planner during plan creation:

1. **Does Phase 5 own the actual production cutover?**
   - **RESOLVED:** Plan 05-04 owns the cutover with `autonomous: false` + 3 sequential `checkpoint:human-verify` tasks (05-04-01 backup taken, 05-04-02 dry-run + read-switch deploy, 05-04-03 observation window elapsed + production --apply). The operator drives each checkpoint manually; the GSD plan tracks the artifacts (backup directory, deployed commit hash, observation-window confirmation, post-drop verification). MIGRATION_RUNBOOK.md §6 documents exact commands. Plan 05-04 Task 4 (auto) then cleans up DATABASE_SCHEMA.md after the operator confirms checkpoints 1-3.

2. **Test for the migration script itself?**
   - **RESOLVED:** Plan 05-02 Task 3 delivers `test_migrate_collection_names.py` with 5 idempotency / halt-guard pytest tests: (a) script created with 4 empty legacy collections, --apply drops them, (b) running --apply twice produces zero diff, (c) pre-drop count guard halts if `legacy.count_documents({}) > 0`, (d) --target-db flag routes to override DB, (e) --verify mode emits row-count + checksum parity. Tests use the Phase-4 isolated test DB infra.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| mongodump | DEBT-02, DEBT-04 backup | Yes | 100.16.1 | — |
| mongorestore | DEBT-02, DEBT-04 rollback | Yes | 100.16.1 | — |
| mongosh | MIGRATION_RUNBOOK.md | Yes | 2.8.3 | pymongo from script |
| pymongo | Migration script | Yes (pinned in requirements.txt) | 4.x | — |
| Python 3.11+ venv | Migration script | Yes (backend/.venv confirmed) | 3.11 | — |
| pytest | DEBT-14 regression gate | Yes (Phase-4 infra) | existing | — |

**Missing dependencies:** None — all required tools are available on the VPS.

---

## Validation Architecture

> `nyquist_validation: true` in `.planning/config.json`

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (Phase-4 infra, existing) |
| Config file | `pltu-tenayan-full-backup/backend/pytest.ini` (pythonpath=.) |
| Quick run command | `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q -x` |
| Full suite command | `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEBT-01 | 4 ADR files exist with correct Status line | Filesystem assertion | `ls .planning/decisions/ADR-009*.md ADR-010*.md ADR-011*.md ADR-012*.md` | No — Wave 0 |
| DEBT-02 | Migration script `--verify` exits 0, checksums match | Script self-assert | `python scripts/migrate_collection_names.py --target-db pltu_tenayan_migration_dryrun --apply --verify` | No — Wave 0 |
| DEBT-03 | Zero legacy collection reads in server.py | grep assertion | `grep -cE 'db\.(smart_stock|sumber_pemakaian|settings)\b' backend/server.py; # must be 0` | No — Wave 0 (add to existing test gate) |
| DEBT-03 | pytest still exits 0 after server.py edits | Regression | `.venv/bin/pytest tests/ -q` | Yes (existing suite) |
| DEBT-03 | Migration script idempotency (run twice = same result) | Unit | `pytest tests/test_migration_script.py -q` | No — Wave 0 |
| DEBT-04 | Backup dir exists at expected path | Filesystem assertion | `ls /home/damnation/backups/pre-phase5-*/pltu_tenayan/*.bson | wc -l` (manual / runbook) | No — manual |
| DEBT-04 | MIGRATION_RUNBOOK.md exists with "Rollback" section | Grep | `grep -c "Rollback" pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` | No — Wave 0 |
| DEBT-05 | "legacy" appears 0 or 1 times in DATABASE_SCHEMA.md | Grep | `grep -ic "legacy" pltu-tenayan-full-backup/DATABASE_SCHEMA.md` | No — add to test_clean_checkout_gate.py |

### Sampling Rate

- **Per task commit:** `grep -E 'db\.(smart_stock|sumber_pemakaian|settings)\b' backend/server.py` (zero-output assertion)
- **Per wave merge:** `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `pltu-tenayan-full-backup/backend/tests/test_migration_script.py` — unit test for migration script idempotency (covers DEBT-02, DEBT-03)
- [ ] Add DEBT-03 grep assertion to `test_clean_checkout_gate.py`: assert `db.smart_stock`, `db.sumber_pemakaian`, `db.settings` do not appear in `server.py`
- [ ] Add DEBT-05 grep assertion to `test_clean_checkout_gate.py`: assert `legacy` count in DATABASE_SCHEMA.md is below threshold

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` per `.planning/config.json`

Phase 5 is a data-migration and documentation phase with no new authentication, authorization, or user-facing surface changes.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth changes in Phase 5 |
| V3 Session Management | No | No session changes |
| V4 Access Control | No | No endpoint additions |
| V5 Input Validation | Partial | Migration script `--target-db` arg validated (must not be production without explicit flag) |
| V6 Cryptography | No | md5 used for data-integrity checksums only (not for security — this is appropriate) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Migration script targeting production without intent | Tampering | `--target-db` required; safety guard rejects bare `DB_NAME=pltu_tenayan` invocation |
| Backup file left world-readable | Information Disclosure | `mongodump` output directory at `/home/damnation/backups/`; ensure directory permissions are 700 (operator responsibility, note in runbook) |
| `mongorestore --drop` on wrong DB | Tampering | `--nsInclude 'pltu_tenayan.*'` scopes the restore; guard against omitting it |

---

## Sources

### Primary (HIGH confidence)

- `pltu-tenayan-full-backup/backend/server.py` — comprehensive grep for all collection reads [VERIFIED]
- `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` — legacy-marking lines catalogued [VERIFIED]
- `pltu-tenayan-full-backup/backend/tests/conftest.py` — Phase-4 test infra patterns [VERIFIED]
- `pltu-tenayan-full-backup/LOCAL_SETUP.md` §"VPS Service Recovery" — operator runbook style [VERIFIED]
- `pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md` — documentation style [VERIFIED]
- Live mongodump/mongorestore/mongosh version probes [VERIFIED: shell commands]
- Live MongoDB server version: 7.0.32 [VERIFIED: mongosh --eval "db.version()"]
- Live `pltu_tenayan` collection inventory [VERIFIED: db.getCollectionNames()]
- Live document counts: smartstock=207, sumberpemakaian=208, app_settings=1, ai_chat_history=10 [VERIFIED: mongosh countDocuments]

### Secondary (MEDIUM confidence)

- `.planning/decisions/ADR-001..008-*.md` — MADR ADR format and style precedent [VERIFIED: read ADR-001, ADR-008]
- `.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md` — locked decisions D-01..D-14 [VERIFIED]

### Tertiary (LOW confidence)

- None — all claims verified or assumed with explicit tagging.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools verified on VPS with version probes
- Architecture (legacy-read locations): HIGH — comprehensive grep verified live; discrepancies from CONTEXT.md documented
- Pitfalls: HIGH — derived from live codebase reading + Phase-4 conftest patterns
- Database state: HIGH — live mongosh probes confirmed collection inventory and counts

**Research date:** 2026-05-11
**Valid until:** 2026-07-11 (stable tech stack; 60-day window)

---

## Plan Decomposition Recommendation

### Plan 05-01: 4 Canonical-Name ADRs

**Wave:** 1
**Depends on:** None (outer-repo only; parallel-safe)
**Requirements closed:** DEBT-01
**Two-repo boundary:** Outer `.planning/` only
**Files modified:**
- `.planning/decisions/ADR-009-canonical-smartstock.md` (new)
- `.planning/decisions/ADR-010-canonical-sumberpemakaian.md` (new)
- `.planning/decisions/ADR-011-canonical-app-settings.md` (new)
- `.planning/decisions/ADR-012-canonical-ai-chat-history.md` (new)

**Tasks:**
1. Draft ADR-009 (smartstock canonical) citing server.py:3078 (CRUD) and 2379/2395/2863 (legacy AI reads)
2. Draft ADR-010 (sumberpemakaian canonical) citing server.py:3352 (CRUD) and 2387/2398/2868/2877 (legacy AI reads)
3. Draft ADR-011 (app_settings canonical) citing server.py:3817 (CRUD) and 2427/2926/4346 (legacy settings reads)
4. Draft ADR-012 (ai_chat_history canonical) citing server.py:2266 (module-level assignment); note ai_conversations absent from live DB

**Verification:** `ls .planning/decisions/ADR-009*.md .planning/decisions/ADR-010*.md .planning/decisions/ADR-011*.md .planning/decisions/ADR-012*.md` exits 0; each file contains `## Status` and `Accepted (locked,` string.

---

### Plan 05-02: server.py Read-Path Edits + Migration Script + Tests

**Wave:** 1 (can run parallel to 05-01 in theory, but the two-repo boundary means inner-repo commits)
**Depends on:** 05-01 (ADRs must exist so the code edits can cite the ADR in commit message)
**Requirements closed:** DEBT-03 (read-path edits), partial DEBT-02 (migration script exists + unit-tested)
**Two-repo boundary:** Inner `pltu-tenayan-full-backup/` only
**Files modified:**
- `pltu-tenayan-full-backup/backend/server.py` (10 line edits: 2379, 2395, 2863 [smart_stock→smartstock]; 2387, 2398, 2868, 2877 [sumber_pemakaian→sumberpemakaian]; 2427, 2926, 4346 [settings→app_settings])
- `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` (new)
- `pltu-tenayan-full-backup/backend/tests/test_migration_script.py` (new)
- `pltu-tenayan-full-backup/backend/tests/test_clean_checkout_gate.py` (add DEBT-03 grep assertion)

**Tasks:**
1. Edit server.py: change 10 legacy-read lines (see Research Focus 2 table)
2. Write `scripts/migrate_collection_names.py` with `--target-db`, `--apply`, `--verify` interface
3. Write `tests/test_migration_script.py` (unit test: create test DB with empty legacy collections → apply() → assert all 4 dropped)
4. Update `test_clean_checkout_gate.py`: add assertion that `db.smart_stock`, `db.sumber_pemakaian`, `db.settings` do not appear in server.py
5. Run full pytest suite and verify exit 0

**Verification:** `grep -cE 'db\.(smart_stock|sumber_pemakaian|settings)\b' backend/server.py` == 0; `.venv/bin/pytest tests/ -q` exits 0.

---

### Plan 05-03: MIGRATION_RUNBOOK.md

**Wave:** 2 (depends on 05-02 so the runbook can reference the actual script + exact commands)
**Depends on:** 05-02 (migration script must exist to be documented)
**Requirements closed:** DEBT-04 (documentation half — backup procedure + rollback documented)
**Two-repo boundary:** Inner `pltu-tenayan-full-backup/` only
**Files modified:**
- `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` (new)

**Tasks:**
1. Write MIGRATION_RUNBOOK.md with sections: Prerequisites, Backup, Dryrun, Read-Path Deploy, Observation Window, pytest Gate, Legacy-Drop, Rollback (code-only + data-restore), Cleanup, Cross-References, Backup Retention
2. Include exact dryrun commands with verified flags (from Research Focus 1)
3. Include smoke-test curl commands (from Research Focus 6)
4. Cross-link to LOCAL_SETUP.md §"VPS Service Recovery" for uvicorn restart
5. Document that "no legacy collections found = expected result" for the dryrun (Pitfall 4)

**Verification:** `grep -c "Rollback" pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` >= 1; `grep -c "mongodump" MIGRATION_RUNBOOK.md` >= 1.

---

### Plan 05-04: DATABASE_SCHEMA.md Cleanup (DEBT-05) + Phase Closure

**Wave:** 2 (depends on 05-03; can begin after runbook is committed)
**Depends on:** 05-03
**Requirements closed:** DEBT-05 (all "legacy" markings removed from DATABASE_SCHEMA.md); phase closure items (STATE.md, ROADMAP.md)
**Two-repo boundary:** Inner `pltu-tenayan-full-backup/` + outer `.planning/`
**Files modified:**
- `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` (remove all "legacy" markings per Research Focus 8 table; convert Phase-3 audit table to Resolution Log)
- `.planning/STATE.md` (phase 5 completion)
- `.planning/ROADMAP.md` (Phase 5 checkbox)

**Tasks:**
1. Edit DATABASE_SCHEMA.md:
   - Remove legacy collection names from §2 collection list (lines 27, 28, 34)
   - Rewrite §9.2, §10.1 catatan naming, §12.2 settings, §13.2 ai_conversations (delete or rewrite per Research Focus 8)
   - Update index recommendations table (remove `sumber_pemakaian`, `ai_conversations` rows)
   - Convert §"Duplicate Pair Active Read Targets" to §"Duplicate Pair Resolution Log" with resolved-date annotation
   - Delete §16.1 "Naming Koleksi" standardization bullets (now resolved)
2. Update ROADMAP.md: check off Phase 5 success criteria
3. Update STATE.md: phase 5 complete

**Verification:** `grep -ic "legacy" pltu-tenayan-full-backup/DATABASE_SCHEMA.md` returns 0 or 1 (only the Section 18 historical summary reference, if kept); `grep -c "Resolved" DATABASE_SCHEMA.md` >= 4.

---

**Note on production cutover:** The actual execution of `mongodump` + `mongorestore` dryrun + `--apply` on production is an operator-run procedure guided by MIGRATION_RUNBOOK.md. It is NOT a committed plan artifact because it depends on a ≥48h observation window that cannot be encoded as a single-session plan. The plans above deliver all CODE and DOCUMENTATION artifacts; the operator executes the migration using the runbook after the plans are committed.

