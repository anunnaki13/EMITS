"""Factory for barge documents (Phase 4 D-02)."""
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


def make_barge(**overrides) -> dict:
    """Insert one minimal barge document into the test DB. Returns doc dict (without _id)."""
    doc = {
        "id": str(uuid.uuid4()),
        "periode": "Jan-2026",
        "shipment_code": f"SHP-FACT-{uuid.uuid4().hex[:8]}",
        "voyage_code": f"VYG-FACT-{uuid.uuid4().hex[:4]}",
        "shipment": f"SHP-FACT",
        "suppliers": "PT TEST SUPPLIER",
        "voyage": "V001",
        "tb": "TB TEST",
        "bg": "BG001",
        "coal_from": "Kalimantan",
        "ta": "2026-01-15 08:00",
        "gcv_arb": 4200.0,
        "tm_arb": 30.5,
        "ash_arb": 5.0,
        "ts_arb": 0.3,
        "bl_mt": 3000.0,
        "ds_mt": 2950.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "test-factory",
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].barges.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    return doc
