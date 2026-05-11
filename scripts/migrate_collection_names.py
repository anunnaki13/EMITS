#!/usr/bin/env python3
"""
migrate_collection_names.py — Phase 5 Collection Naming Debt Resolution
ADR-009..012 (see .planning/decisions/).

Drops empty legacy collections after asserting count_documents({}) == 0 per D-07.
This is an idempotent one-way migration: legacy → canonical collection names.

USAGE:
  python scripts/migrate_collection_names.py --target-db DB_NAME [--dry-run | --apply] [--verify]

EXAMPLES:
  # Safe exploration (dry-run against a test DB):
  python scripts/migrate_collection_names.py --target-db pltu_tenayan_migration_dryrun --dry-run

  # Apply against a test DB (verify canonical checksums are unchanged):
  python scripts/migrate_collection_names.py --target-db pltu_tenayan_test_snapshot --apply --verify

  # Production cutover (requires explicit --target-db flag per safety guard):
  python scripts/migrate_collection_names.py --target-db pltu_tenayan --apply --verify

FLAGS:
  --target-db DB_NAME   Required for non-dryrun targets. Defaults to env DB_NAME
                        or "pltu_tenayan" (production) but a bare invocation
                        targeting "pltu_tenayan" without explicit --target-db
                        is REJECTED with exit code 1.
  --dry-run             Report what would be dropped without dropping. Default
                        behavior when neither --apply nor --verify is given.
  --apply               Execute the drop step (after the pre-drop count guard
                        succeeds for each legacy collection).
  --verify              Emit row counts + md5 checksums for the 4 canonical
                        collections. Can be combined with --apply (emits BEFORE
                        and AFTER and asserts byte-equal).

EXIT CODES:
  0  success (idempotent — re-runs after a clean run also exit 0)
  1  safety guard tripped (production target without explicit flag, or
     pre-drop count > 0 for any legacy collection, or checksum mismatch)
  2  CLI usage error

CONSTANTS (locked by Phase 5):
  LEGACY_TO_CANONICAL = {
      "smart_stock":      "smartstock",       # ADR-009 / D-01
      "sumber_pemakaian": "sumberpemakaian",  # ADR-010 / D-02
      "settings":         "app_settings",     # ADR-011 / D-03
      "ai_conversations": "ai_chat_history",  # ADR-012 / D-04
  }
  PRODUCTION_DB = "pltu_tenayan"

IDEMPOTENCY CONTRACT:
  Run 1: finds legacy collections, asserts count==0, drops them. Exit 0.
  Run 2 (same DB): legacy names not in list_collection_names() → prints
    [SKIP] <name> — does not exist for each. Exit 0.
  --verify --apply together: checksums of canonical collections BEFORE and
    AFTER must match (canonical untouched).
"""

import argparse
import hashlib
import json
import os
import sys

from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Constants (locked by Phase 5 decisions — do NOT change)
# ---------------------------------------------------------------------------

LEGACY_TO_CANONICAL = {
    "smart_stock":      "smartstock",       # ADR-009 / D-01
    "sumber_pemakaian": "sumberpemakaian",  # ADR-010 / D-02
    "settings":         "app_settings",     # ADR-011 / D-03
    "ai_conversations": "ai_chat_history",  # ADR-012 / D-04
}

LEGACY_COLLECTIONS = list(LEGACY_TO_CANONICAL.keys())
CANONICAL_COLLECTIONS = list(LEGACY_TO_CANONICAL.values())
PRODUCTION_DB = "pltu_tenayan"


# ---------------------------------------------------------------------------
# Checksum helpers (from RESEARCH Focus 4 — deterministic, order-independent)
# ---------------------------------------------------------------------------

def collection_checksum(db, collection_name: str) -> dict:
    """Deterministic checksum: md5-over-sorted-JSON. Order-independent.

    Returns {"count": int, "checksum": str} where checksum is "empty" for
    an empty collection or an md5 hex string for non-empty collections.
    """
    docs = list(db[collection_name].find({}, {"_id": 0}).sort("_id", 1))
    count = len(docs)
    per_doc_hashes = sorted(
        hashlib.md5(json.dumps(doc, sort_keys=True, default=str).encode()).hexdigest()
        for doc in docs
    )
    aggregate = (
        hashlib.md5("|".join(per_doc_hashes).encode()).hexdigest()
        if per_doc_hashes else "empty"
    )
    return {"count": count, "checksum": aggregate}


def verify_checksums(db, target_db_name: str) -> dict:
    """Print and return checksums for all 4 canonical collections.

    Args:
        db: pymongo Database object
        target_db_name: DB name string (for display purposes)

    Returns:
        dict mapping canonical_collection_name → {"count": int, "checksum": str}
    """
    print(f"\n[VERIFY] Checksums for '{target_db_name}':")
    results = {}
    for coll in CANONICAL_COLLECTIONS:
        result = collection_checksum(db, coll)
        print(f"  {coll}: count={result['count']}, checksum={result['checksum']}")
        results[coll] = result
    return results


# ---------------------------------------------------------------------------
# Migration core
# ---------------------------------------------------------------------------

def apply_migration(db, dry_run: bool) -> dict:
    """Apply (or dry-run) the legacy → canonical collection name migration.

    For each legacy collection name:
      - If it does not exist in the DB: print [SKIP] and continue (idempotent).
      - If it has > 0 documents: print [HALT] and sys.exit(1) (D-07 guard).
      - If dry_run=True: print [DRY-RUN] only, do not drop.
      - If dry_run=False: drop the collection and print [DROPPED].

    Args:
        db: pymongo Database object (sync — NOT motor)
        dry_run: if True, report without dropping

    Returns:
        dict mapping legacy_name → "skipped" | "dropped" | "would-drop"
    """
    results = {}
    existing = set(db.list_collection_names())

    for legacy_name, canonical_name in LEGACY_TO_CANONICAL.items():
        if legacy_name not in existing:
            print(
                f"[SKIP] {legacy_name} — does not exist "
                f"(already clean or never created)"
            )
            results[legacy_name] = "skipped"
            continue

        count = db[legacy_name].count_documents({})
        if count > 0:
            print(
                f"[HALT] {legacy_name} has {count} document(s). "
                f"Expected 0. Aborting (per D-07).",
                file=sys.stderr,
            )
            sys.exit(1)

        if dry_run:
            print(
                f"[DRY-RUN] Would drop {legacy_name} "
                f"(count=0, canonical={canonical_name})"
            )
            results[legacy_name] = "would-drop"
        else:
            db[legacy_name].drop()
            print(
                f"[DROPPED] {legacy_name} "
                f"(count=0, canonical={canonical_name})"
            )
            results[legacy_name] = "dropped"

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 5 migration: drop legacy collection names after verifying "
            "they are empty (count_documents == 0). Idempotent. "
            "See ADR-009..012 in .planning/decisions/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Dry-run against a dedicated dryrun DB:\n"
            "  python scripts/migrate_collection_names.py "
            "--target-db pltu_tenayan_migration_dryrun --dry-run\n\n"
            "  # Apply + verify against a test snapshot DB:\n"
            "  python scripts/migrate_collection_names.py "
            "--target-db pltu_tenayan_test_snapshot --apply --verify\n\n"
            "  # Production cutover (MUST use explicit --target-db):\n"
            "  python scripts/migrate_collection_names.py "
            "--target-db pltu_tenayan --apply --verify\n"
        ),
    )
    parser.add_argument(
        "--target-db",
        metavar="DB_NAME",
        default=None,
        help=(
            "MongoDB database name to operate on. "
            f"Required when targeting '{PRODUCTION_DB}' — bare invocation "
            f"that resolves to '{PRODUCTION_DB}' without this flag exits 1."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Report what would be dropped without dropping. "
            "Default behavior when neither --apply nor --verify is given."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Execute the drop step (after the pre-drop count guard succeeds "
            "for each legacy collection)."
        ),
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help=(
            "Emit row counts + md5 checksums for the 4 canonical collections. "
            "Can be combined with --apply (emits BEFORE and AFTER, asserts byte-equal)."
        ),
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Mutual exclusion: --dry-run and --apply cannot both be set
    # ------------------------------------------------------------------
    if args.dry_run and args.apply:
        print(
            "ERROR: --dry-run and --apply are mutually exclusive. "
            "Choose one.",
            file=sys.stderr,
        )
        sys.exit(2)

    # ------------------------------------------------------------------
    # Default to dry-run when neither --apply nor --verify is given
    # ------------------------------------------------------------------
    if not args.apply and not args.verify:
        args.dry_run = True

    # ------------------------------------------------------------------
    # Resolve target DB name
    # ------------------------------------------------------------------
    if args.target_db:
        target_db = args.target_db
    else:
        target_db = os.environ.get("DB_NAME") or PRODUCTION_DB

    # ------------------------------------------------------------------
    # Production-DB safety guard (RESEARCH Pitfall A)
    # Targeting pltu_tenayan requires explicit --target-db flag to prevent
    # accidental production access from bare invocations or misconfigured env.
    # ------------------------------------------------------------------
    if target_db == PRODUCTION_DB and args.target_db is None:
        print(
            f"ERROR: Targeting production DB '{PRODUCTION_DB}' requires "
            f"explicit --target-db {PRODUCTION_DB} flag. "
            f"Add '--target-db {PRODUCTION_DB}' to confirm intent.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Connect to MongoDB (sync pymongo — standalone operator script)
    # ------------------------------------------------------------------
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    db = client[target_db]

    print(f"[INFO] Connected to MongoDB: {mongo_url}")
    print(f"[INFO] Target DB: {target_db}")
    print(f"[INFO] Mode: {'dry-run' if args.dry_run else 'apply'}")
    print()

    # ------------------------------------------------------------------
    # Verify BEFORE (if --verify)
    # ------------------------------------------------------------------
    before = None
    if args.verify:
        before = verify_checksums(db, target_db)
        print()

    # ------------------------------------------------------------------
    # Run migration
    # ------------------------------------------------------------------
    apply_migration(db, dry_run=not args.apply)

    # ------------------------------------------------------------------
    # Verify AFTER (if --verify --apply) and assert byte-equal
    # ------------------------------------------------------------------
    if args.verify and args.apply:
        print()
        after = verify_checksums(db, target_db)
        if before != after:
            print(
                "\nCHECKSUM MISMATCH — canonical collections changed during migration!",
                file=sys.stderr,
            )
            print(f"  BEFORE: {before}", file=sys.stderr)
            print(f"  AFTER:  {after}", file=sys.stderr)
            client.close()
            sys.exit(1)
        print(
            "\n[OK] Checksums match before and after. Zero data loss confirmed."
        )

    client.close()


if __name__ == "__main__":
    main()
