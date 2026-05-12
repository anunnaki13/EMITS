import os
import uuid
from datetime import datetime, timezone

import pymongo
import requests


def _db():
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError("MONGO_TEST_DB_NAME unset")
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
    return client, client[name]


def test_dashboard_operational_empty_shape(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/dashboard/operational", headers=admin_headers, timeout=15)
    assert r.status_code == 200, f"/dashboard/operational: {r.status_code} {r.text[:300]}"
    body = r.json()

    assert body["period"] == "all"
    assert isinstance(body["available_periods"], list)
    for section in ["stock", "arrivals", "disputes"]:
        assert section in body

    for key in [
        "current_stock",
        "total_penerimaan",
        "total_pemakaian",
        "avg_daily_usage",
        "days_of_supply",
        "status",
        "label",
        "reorder_risk",
        "reorder_threshold_days",
    ]:
        assert key in body["stock"]
    for key in [
        "scheduled_count",
        "realized_count",
        "count_gap",
        "fulfillment_rate",
        "tonnage_fulfillment_rate",
        "at_risk_count",
        "at_risk_schedule",
        "realized_by_mode",
        "upcoming_schedule",
    ]:
        assert key in body["arrivals"]
    for key in ["critical_count", "warning_count", "umpire", "recent"]:
        assert key in body["disputes"]


def test_dashboard_operational_period_filters_seeded_data(base_url, admin_headers):
    client, db = _db()
    marker = f"dash-op-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    try:
        db.smartstock.insert_one({
            "id": f"{marker}-stock",
            "date": "2026-05-05",
            "stock_awal": 1000.0,
            "total_penerimaan": 500.0,
            "stock_akhir": 1500.0,
            "created_at": now,
            "_marker": marker,
        })
        db.sumberpemakaian.insert_one({
            "id": f"{marker}-usage",
            "date": "2026-05-06",
            "stock_awal": 1500.0,
            "total_pemakaian": 300.0,
            "created_at": now,
            "_marker": marker,
        })
        db.po_batubara.insert_one({
            "id": f"{marker}-po",
            "no_jadwal": "JADWAL-DASH-01",
            "supplier_name": "PT DASHBOARD TEST",
            "moda": "Vessel",
            "time_arrival": "2026-05-10 08:00",
            "tonase_po": 1000.0,
            "created_at": now,
            "_marker": marker,
        })
        db.vessels.insert_one({
            "id": f"{marker}-vessel",
            "shipment_code": "DASH-VESSEL-01",
            "suppliers": "PT DASHBOARD TEST",
            "name_of_vessel": "MV DASHBOARD",
            "time_arrival": "2026-05-12 08:00",
            "ds_mt": 800.0,
            "created_at": now,
            "_marker": marker,
        })
        db.coa_reconciliation.insert_one({
            "id": f"{marker}-coa",
            "shipment": "DASH-COA-01",
            "suppliers": "PT DASHBOARD TEST",
            "completed_unloading": "2026-05-13",
            "status": "critical",
            "umpire_status": "in_progress",
            "delta_loading_internal": 180.0,
            "created_at": now,
            "_marker": marker,
        })

        r = requests.get(
            f"{base_url}/api/dashboard/operational?period=2026-05",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200, f"/dashboard/operational: {r.status_code} {r.text[:300]}"
        body = r.json()

        assert body["period"] == "2026-05"
        assert body["stock"]["total_penerimaan"] >= 500.0
        assert body["stock"]["total_pemakaian"] >= 300.0
        assert body["stock"]["status"] in {"critical", "warning", "watch", "healthy", "unknown"}
        assert body["stock"]["reorder_threshold_days"] == 14
        assert body["arrivals"]["scheduled_count"] >= 1
        assert body["arrivals"]["realized_count"] >= 1
        assert body["arrivals"]["fulfillment_rate"] is not None
        assert body["arrivals"]["tonnage_fulfillment_rate"] is not None
        assert body["arrivals"]["at_risk_count"] >= 0
        assert any(item["mode"] == "vessel" for item in body["arrivals"]["realized_by_mode"])
        assert body["disputes"]["critical_count"] >= 1
        assert body["disputes"]["umpire"]["in_progress"] >= 1
        assert any(item["shipment"] == "DASH-COA-01" for item in body["disputes"]["recent"])
        assert all("aging_days" in item for item in body["disputes"]["recent"])
    finally:
        for collection in [db.smartstock, db.sumberpemakaian, db.po_batubara, db.vessels, db.coa_reconciliation]:
            collection.delete_many({"_marker": marker})
        client.close()
