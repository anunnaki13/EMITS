"""Factory for merit_order documents (Phase 4 D-02).

Critical: _seed_baseline_data in conftest.py calls make_merit_order(year=2024, month=N)
for N in [1,2,3] so that test_merit_order.py tests have baseline data in the test DB.

Field names match MeritOrderCreate (server.py:519-531):
  periode, periode_year, periode_month, pemasok, moda,
  tipikal_kcal_kg, jenis_kontrak, harga_batubara, harga_freight,
  harga_cif, rp_kg, rp_kcal

Rule 1 fix (04-05): original factory had wrong field names (supplier, coal_type, etc.)
that did not match the server model, causing test_03_merit_order_data_structure to fail
with "Missing field: periode" after the pagination envelope migration.
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
    """Insert one minimal merit_order document into the test DB. Returns doc dict (without _id).

    Fields match MeritOrderCreate model (server.py:519-531) so that test assertions
    checking for 'periode', 'pemasok', 'moda', etc. pass against seeded test data.
    """
    # Default uses year/month overrides to build a deterministic periode string.
    year = overrides.pop("year", 2024)
    month = overrides.pop("month", 1)
    doc = {
        "id": str(uuid.uuid4()),
        "periode": f"{year}-{month:02d}-01",
        "periode_year": year,
        "periode_month": month,
        "pemasok": "PT TEST SUPPLIER",
        "moda": "Vessel",
        "tipikal_kcal_kg": 4200.0,
        "jenis_kontrak": "CIF",
        "harga_batubara": 850000.0,
        "harga_freight": 50000.0,
        "harga_cif": 900000.0,
        "rp_kg": 900.0,
        "rp_kcal": 0.214286,
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
