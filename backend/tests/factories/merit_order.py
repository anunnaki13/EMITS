"""Factory for merit_order documents (Phase 4 D-02).

Critical: _seed_baseline_data in conftest.py calls make_merit_order(year=2024, month=N)
for N in [1,2,3] so that existing test_merit_order.py:71 (assert len(data) > 0) and
:314 (assert len(data) >= 1) pass against a fresh test DB.
"""
import os
import uuid
from datetime import datetime, timezone

import pymongo


def _get_test_db_name() -> str:
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError(
            "MONGO_TEST_DB_NAME unset — factories must be called from inside a test session."
        )
    return name


def make_merit_order(**overrides) -> dict:
    """Insert one minimal merit_order document into the test DB. Returns doc dict (without _id)."""
    doc = {
        "id": str(uuid.uuid4()),
        "year": 2025,
        "month": 1,
        "supplier": "PT TEST SUPPLIER",
        "coal_type": "LRC",
        "gcv_contract": 4200.0,
        "gcv_actual": 4150.0,
        "price_per_kcal": 0.018,
        "price_per_mt": 75.0,
        "bl_mt": 5000.0,
        "ds_mt": 4950.0,
        "source": "Vessel",
        "rank": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "test-factory",
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].merit_order.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    return doc
