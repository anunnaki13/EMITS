import os
import uuid

import pymongo
import requests


def _db():
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError("MONGO_TEST_DB_NAME unset")
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
    return client, client[name]


def test_management_report_summarizes_sources_filters_and_traceability(base_url, admin_headers):
    client, db = _db()
    marker = f"report-{uuid.uuid4().hex[:8]}"
    supplier = f"PT {marker.upper()}"
    other_supplier = f"PT OTHER {marker.upper()}"
    try:
        db.smartstock.insert_one({
            "id": f"{marker}-stock",
            "date": "2026-05-12",
            "stock_awal": 1000,
            "total_penerimaan": 500,
            "stock_akhir": 1200,
            "_marker": marker,
        })
        db.sumberpemakaian.insert_one({
            "id": f"{marker}-usage",
            "date": "2026-05-12",
            "total_pemakaian": 300,
            "_marker": marker,
        })
        db.po_batubara.insert_many([
            {
                "id": f"{marker}-po",
                "supplier_name": supplier,
                "time_arrival": "2026-05-12",
                "tonase_po": 1000,
                "_marker": marker,
            },
            {
                "id": f"{marker}-po-other",
                "supplier_name": other_supplier,
                "time_arrival": "2026-05-12",
                "tonase_po": 9000,
                "_marker": marker,
            },
        ])
        db.vessels.insert_one({
            "id": f"{marker}-vessel",
            "suppliers": supplier,
            "completed_unloading": "2026-05-12",
            "ds_mt": 800,
            "gcv_arb": 4200,
            "_marker": marker,
        })
        db.coa_reconciliation.insert_one({
            "id": f"{marker}-coa",
            "suppliers": supplier,
            "completed_unloading": "2026-05-12",
            "status": "critical",
            "umpire_status": "in_progress",
            "delta_loading_internal": -25,
            "ds_mt": 800,
            "_marker": marker,
        })

        response = requests.get(
            f"{base_url}/api/reports/management",
            headers=admin_headers,
            params={"date_from": "2026-05-01", "date_to": "2026-05-31", "supplier": supplier},
            timeout=15,
        )
        assert response.status_code == 200, response.text[:300]
        body = response.json()

        assert body["supplier"] == supplier
        assert body["generated_at"]
        assert body["source_counts"]["po_batubara"] == 1
        assert body["source_counts"]["vessel"] == 1
        assert body["stock"]["current_stock"] == 1200
        assert body["arrivals"]["scheduled_tonnage"] == 1000
        assert body["arrivals"]["realized_tonnage"] == 800
        assert body["quality"]["avg_gcv"] == 4200
        assert body["potential_loss"]["potential_loss_mt"] == 25
        assert body["disputes"]["critical_count"] == 1
        assert body["disputes"]["umpire"]["active"] == 1
        assert body["supplier_performance"][0]["supplier"] == supplier
    finally:
        for collection in ["smartstock", "sumberpemakaian", "po_batubara", "vessels", "coa_reconciliation"]:
            db[collection].delete_many({"_marker": marker})
        client.close()
