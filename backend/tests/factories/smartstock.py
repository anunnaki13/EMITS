"""Factory for smartstock documents (Phase 6 OPS-01 field-name fix).

Canonical fields per live mongosh probe (06-RESEARCH.md §Focus 2):
  id, date, stock_awal, suppliers, total_penerimaan, created_at, updated_at

There is NO top-level `tonase` field. The aggregation field is `total_penerimaan`.
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


def make_smartstock(**overrides) -> dict:
    """Insert one smartstock document into the test DB. Returns doc dict (without _id).

    Required by Phase 6 test_smart_blending_data.py::test_smartstock_sum and
    test_smart_stock_endpoint. Uses canonical field `total_penerimaan` (not `tonase`).
    """
    doc = {
        "id": str(uuid.uuid4()),
        "date": overrides.pop("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "stock_awal": overrides.pop("stock_awal", 100000000),
        "suppliers": overrides.pop("suppliers", {}),
        "total_penerimaan": overrides.pop("total_penerimaan", 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].smartstock.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    return doc
