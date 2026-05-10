"""Factory for po_batubara documents (Phase 4 D-02)."""
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


def make_po_batubara(**overrides) -> dict:
    """Insert one minimal po_batubara document into the test DB. Returns doc dict (without _id)."""
    doc = {
        "id": str(uuid.uuid4()),
        "year": 2026,
        "month": 1,
        "supplier": "PT TEST SUPPLIER",
        "po_number": f"PO-FACT-{uuid.uuid4().hex[:8]}",
        "contract_quantity_mt": 50000.0,
        "delivered_mt": 5000.0,
        "remaining_mt": 45000.0,
        "gcv_contract": 4200.0,
        "price_per_mt": 75.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "test-factory",
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].po_batubara.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    return doc
