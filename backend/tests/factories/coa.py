"""Factory for coa_reconciliation documents (Phase 4 D-02)."""
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


def make_coa(**overrides) -> dict:
    """Insert one minimal coa_reconciliation document into the test DB. Returns doc dict (without _id)."""
    doc = {
        "id": str(uuid.uuid4()),
        "shipment_code": f"SHP-FACT-{uuid.uuid4().hex[:8]}",
        "supplier": "PT TEST SUPPLIER",
        "no_coa": f"COA-FACT-{uuid.uuid4().hex[:6]}",
        "no_cow": f"COW-FACT-{uuid.uuid4().hex[:6]}",
        "tgl_terbit_coa": "2026-01-17",
        "tgl_terbit_cow": "2026-01-15",
        "gcv_coa": 4200.0,
        "gcv_cow": 4150.0,
        "gcv_deviation": -50.0,
        "ash_coa": 5.0,
        "ash_cow": 5.2,
        "ash_deviation": 0.2,
        "ts_coa": 0.3,
        "ts_cow": 0.31,
        "ts_deviation": 0.01,
        "status": "verified",
        "source": "Vessel",
        "bl_mt": 5000.0,
        "ds_mt": 4950.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "test-factory",
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].coa_reconciliation.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    return doc
