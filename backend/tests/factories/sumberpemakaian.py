"""Factory for sumberpemakaian documents (Phase 6 OPS-01 field-name fix).

Canonical fields per live mongosh probe (06-RESEARCH.md §Focus 2):
  id, date, stock_awal, suppliers, total_pemakaian, created_at, updated_at

There are NO `batubara_mt`, `biomassa_mt`, `tanggal`, or `energy_mwh` fields.
The single total field is `total_pemakaian`.
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


def make_sumberpemakaian(**overrides) -> dict:
    """Insert one sumberpemakaian document into the test DB. Returns doc dict (without _id).

    Required by Phase 6 test_smart_blending_data.py::test_sumberpemakaian_sum and
    test_smart_stock_endpoint. Uses canonical field `total_pemakaian` (not batubara_mt/biomassa_mt).
    """
    doc = {
        "id": str(uuid.uuid4()),
        "date": overrides.pop("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "stock_awal": overrides.pop("stock_awal", 100000000),
        "suppliers": overrides.pop("suppliers", {"_": {}}),
        "total_pemakaian": overrides.pop("total_pemakaian", 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].sumberpemakaian.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    return doc
