"""Phase 6 OPS-01 regression tests: smart-blending data correctness.

Validates that server.py aggregation pipelines reference the canonical field names
from the live MongoDB schema (06-RESEARCH.md §Focus 2):
  - smartstock: `total_penerimaan` (NOT `tonase`)
  - sumberpemakaian: `total_pemakaian` (NOT `batubara_mt` / `biomassa_mt`)

Three tests (06-VALIDATION.md rows 06-02-01, 06-02-02, 06-02-03):
  1. test_smartstock_sum        — direct pymongo aggregation
  2. test_sumberpemakaian_sum   — direct pymongo aggregation
  3. test_smart_stock_endpoint  — HTTP GET /api/ai/quick/smart-stock via test backend

Data-quality caveat (RESEARCH Pitfall 5): live data may still show zero totals due to
upstream Excel upload-parser artifact (supplier key mis-parsed as "TOTAL_PENERIMAAN\n_MT").
That is a separate data-quality concern outside Phase 6 scope. These tests seed deterministic
values to verify aggregation field-name correctness independently of upload quality.
"""
import os

import pymongo
import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_test_db_name() -> str:
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        pytest.skip("MONGO_TEST_DB_NAME unset — run inside a pytest session (conftest seeds it)")
    return name


def _mongo_client():
    url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    return pymongo.MongoClient(url, serverSelectionTimeoutMS=3000)


# ---------------------------------------------------------------------------
# Test 1: smartstock $sum "$total_penerimaan"
# ---------------------------------------------------------------------------

def test_smartstock_sum(_backend_lifecycle):
    """06-02-01: seeded smartstock docs aggregate to expected total via $total_penerimaan.

    Seeds 3 docs with known values, runs the same $group pipeline that server.py uses,
    asserts the sum is non-zero and matches the seeded total exactly.
    """
    from tests.factories.smartstock import make_smartstock

    db_name = _get_test_db_name()
    client = _mongo_client()
    try:
        # Isolate: drop any pre-existing docs seeded by other tests.
        client[db_name].smartstock.delete_many({"_test_smartstock_sum": True})

        make_smartstock(total_penerimaan=1000, _test_smartstock_sum=True)
        make_smartstock(total_penerimaan=2000, _test_smartstock_sum=True)
        make_smartstock(total_penerimaan=3000, _test_smartstock_sum=True)

        result = list(client[db_name].smartstock.aggregate([
            {"$match": {"_test_smartstock_sum": True}},
            {"$group": {"_id": None, "total": {"$sum": "$total_penerimaan"}}}
        ]))
    finally:
        client.close()

    assert result, "aggregation returned empty — smartstock docs not inserted correctly"
    total = result[0]["total"]
    assert total != 0, f"$sum '$total_penerimaan' returned 0 — field name mismatch"
    assert total == 6000, f"expected 6000, got {total}"


# ---------------------------------------------------------------------------
# Test 2: sumberpemakaian $sum "$total_pemakaian"
# ---------------------------------------------------------------------------

def test_sumberpemakaian_sum(_backend_lifecycle):
    """06-02-02: seeded sumberpemakaian docs aggregate to expected total via $total_pemakaian.

    Seeds 3 docs with known values, runs the same $group pipeline that server.py uses,
    asserts the sum is non-zero and matches the seeded total exactly.
    """
    from tests.factories.sumberpemakaian import make_sumberpemakaian

    db_name = _get_test_db_name()
    client = _mongo_client()
    try:
        client[db_name].sumberpemakaian.delete_many({"_test_sumberpemakaian_sum": True})

        make_sumberpemakaian(total_pemakaian=500, _test_sumberpemakaian_sum=True)
        make_sumberpemakaian(total_pemakaian=700, _test_sumberpemakaian_sum=True)
        make_sumberpemakaian(total_pemakaian=900, _test_sumberpemakaian_sum=True)

        result = list(client[db_name].sumberpemakaian.aggregate([
            {"$match": {"_test_sumberpemakaian_sum": True}},
            {"$group": {"_id": None, "total_pemakaian": {"$sum": "$total_pemakaian"}}}
        ]))
    finally:
        client.close()

    assert result, "aggregation returned empty — sumberpemakaian docs not inserted correctly"
    total = result[0]["total_pemakaian"]
    assert total != 0, f"$sum '$total_pemakaian' returned 0 — field name mismatch"
    assert total == 2100, f"expected 2100, got {total}"


# ---------------------------------------------------------------------------
# Test 3: /api/ai/quick/smart-stock returns current_stock != 0 with seeded data
# ---------------------------------------------------------------------------

def test_smart_stock_endpoint(_backend_lifecycle, base_url, admin_headers):
    """06-02-03: GET /api/ai/quick/smart-stock returns non-zero current_stock.

    Seeds 2 smartstock + 2 sumberpemakaian docs with non-zero values into the test DB,
    then hits the endpoint (running at base_url via _backend_lifecycle on :18013).

    Asserts:
    - HTTP 200
    - current_stock != 0 (field-name fix + seeded data)
    - Response uses canonical key names: total_penerimaan, total_pemakaian (not tonase / batubara_mt)
    """
    from tests.factories.smartstock import make_smartstock
    from tests.factories.sumberpemakaian import make_sumberpemakaian

    db_name = _get_test_db_name()
    client = _mongo_client()
    try:
        # Seed via direct pymongo so we know what values the endpoint will aggregate.
        make_smartstock(total_penerimaan=10000)
        make_smartstock(total_penerimaan=5000)
        make_sumberpemakaian(total_pemakaian=1000)
        make_sumberpemakaian(total_pemakaian=500)
    finally:
        client.close()

    r = requests.get(f"{base_url}/api/ai/quick/smart-stock", headers=admin_headers, timeout=15)
    assert r.status_code == 200, f"/api/ai/quick/smart-stock: {r.status_code} {r.text[:300]}"

    body = r.json()

    # Canonical key names must be present (not old wrong names).
    assert "total_penerimaan" in body, f"missing 'total_penerimaan' key: {list(body.keys())}"
    assert "total_pemakaian" in body, f"missing 'total_pemakaian' key: {list(body.keys())}"
    assert "current_stock" in body, f"missing 'current_stock' key: {list(body.keys())}"

    # With seeded non-zero penerimaan > pemakaian, current_stock must be non-zero.
    assert body["current_stock"] != 0, (
        f"current_stock == 0 after seeding penerimaan=15000 and pemakaian=1500. "
        f"Field-name fix may not be effective or DB seeding failed. body={body}"
    )
    assert body["total_penerimaan"] != 0, (
        f"total_penerimaan == 0 — aggregation on '$total_penerimaan' still returns 0. body={body}"
    )
