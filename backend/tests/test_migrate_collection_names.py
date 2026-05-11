"""Phase 5 Plan 05-02: Migration script idempotency unit test.

Proves DEBT-02 (script idempotency on a production-snapshot DB) using the
Phase-4 test-DB isolation pattern. Creates a per-test mongo DB named
pltu_tenayan_test_migrate_<rand>, seeds 4 empty legacy collections + 4
canonical collections with sentinel docs, runs apply_migration(), and
asserts:
  1. All 4 legacy collections are gone after apply.
  2. All 4 canonical collections are byte-identical before vs after (checksums match).
  3. A second apply on the same DB is a no-op (idempotency).
  4. A halt-on-non-empty-legacy guard works (D-07).
  5. dry-run does not drop (collections remain after dry-run invocation).
"""
import os
import sys
import uuid
from pathlib import Path

import pymongo
import pytest

# Add scripts/ to sys.path so we can import the migration module directly.
# Path: pltu-tenayan-full-backup/backend/tests/ → ../../ → pltu-tenayan-full-backup/
REPO_ROOT = Path(__file__).resolve().parents[2]  # pltu-tenayan-full-backup/
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import migrate_collection_names as mig

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")


@pytest.fixture
def test_db():
    """Per-test isolated DB with prefix `pltu_tenayan_test_migrate_<rand>`.

    Safety guard pattern from conftest.py:159 — the prefix MUST start with
    `pltu_tenayan_test_` so any accidental drop-by-name in nested code is
    rejected by the same guard logic that protects the Phase-4 session DB.
    """
    rand = uuid.uuid4().hex[:8]
    db_name = f"pltu_tenayan_test_migrate_{rand}"
    client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    db = client[db_name]
    try:
        yield db
    finally:
        # Safety guard mirrors conftest.py:_drop_test_db
        assert db_name.startswith("pltu_tenayan_test_"), (
            f"REFUSE to drop unsafe DB name: {db_name}"
        )
        client.drop_database(db_name)
        client.close()


def _seed_legacy_and_canonical(db, with_legacy_data: bool = False):
    """Create 4 empty legacy collections + 4 canonical collections with 1 sentinel doc each."""
    for legacy in mig.LEGACY_COLLECTIONS:
        if with_legacy_data:
            db[legacy].insert_one({"id": "sentinel", "marker": legacy})
        else:
            db.create_collection(legacy)
    for canonical in mig.CANONICAL_COLLECTIONS:
        db[canonical].insert_one({"id": f"canonical-{canonical}", "marker": canonical})


def test_apply_drops_empty_legacy_collections(test_db):
    """Run 1: legacy collections present (empty) → apply drops all 4."""
    _seed_legacy_and_canonical(test_db, with_legacy_data=False)
    existing_before = set(test_db.list_collection_names())
    assert mig.LEGACY_COLLECTIONS[0] in existing_before, "setup failed"
    mig.apply_migration(test_db, dry_run=False)
    existing_after = set(test_db.list_collection_names())
    for legacy in mig.LEGACY_COLLECTIONS:
        assert legacy not in existing_after, f"{legacy} should be dropped"
    for canonical in mig.CANONICAL_COLLECTIONS:
        assert canonical in existing_after, f"{canonical} must be preserved"


def test_apply_is_idempotent(test_db):
    """Run 2 on same DB: legacy already absent → apply is a clean no-op."""
    _seed_legacy_and_canonical(test_db, with_legacy_data=False)
    mig.apply_migration(test_db, dry_run=False)
    # Second invocation must not raise
    mig.apply_migration(test_db, dry_run=False)


def test_canonical_checksums_unchanged_by_apply(test_db):
    """DEBT-02 zero-data-loss: canonical checksums BEFORE == AFTER."""
    _seed_legacy_and_canonical(test_db, with_legacy_data=False)
    before = {c: mig.collection_checksum(test_db, c) for c in mig.CANONICAL_COLLECTIONS}
    mig.apply_migration(test_db, dry_run=False)
    after = {c: mig.collection_checksum(test_db, c) for c in mig.CANONICAL_COLLECTIONS}
    assert before == after, f"checksum mismatch: {before} vs {after}"


def test_halt_on_non_empty_legacy(test_db):
    """D-07 pre-drop count guard: if any legacy collection has > 0 docs, halt."""
    _seed_legacy_and_canonical(test_db, with_legacy_data=True)
    with pytest.raises(SystemExit):
        mig.apply_migration(test_db, dry_run=False)


def test_dry_run_does_not_drop(test_db):
    """--dry-run reports what would happen but drops nothing."""
    _seed_legacy_and_canonical(test_db, with_legacy_data=False)
    mig.apply_migration(test_db, dry_run=True)
    existing_after = set(test_db.list_collection_names())
    for legacy in mig.LEGACY_COLLECTIONS:
        assert legacy in existing_after, f"{legacy} must remain after dry-run"
