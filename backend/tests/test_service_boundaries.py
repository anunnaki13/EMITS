import asyncio
import os
import uuid

import pymongo


def _db():
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError("MONGO_TEST_DB_NAME unset")
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
    return client, client[name]


async def _build_service_payloads(supplier: str, user: dict) -> tuple[dict, dict, dict]:
    from services.dashboard_metrics import build_dashboard_operational
    from services.management_reports import build_management_report
    from services.operational_advisor import build_operational_advisor

    report = await build_management_report("2026-05", supplier, None, None, user)
    dashboard = await build_dashboard_operational("2026-05", supplier, "vessel", user)
    advisor = await build_operational_advisor("2026-05", supplier, None, None, user)
    return report, dashboard, advisor


def test_service_builders_return_backend_contracts_without_http():
    client, db = _db()
    marker = f"svc-boundary-{uuid.uuid4().hex[:8]}"
    supplier = f"PT SERVICE {marker.upper()}"
    user = {"id": "svc-test", "email": "svc-test@example.com"}
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
        db.po_batubara.insert_one({
            "id": f"{marker}-po",
            "no_jadwal": "SVC-PO-01",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-05-10",
            "tonase_po": 1000,
            "_marker": marker,
        })
        db.vessels.insert_one({
            "id": f"{marker}-vessel",
            "shipment_code": "SVC-VESSEL-01",
            "name_of_vessel": "MV SERVICE",
            "suppliers": supplier,
            "time_arrival": "2026-05-12",
            "completed_unloading": "2026-05-12",
            "ds_mt": 800,
            "gcv_arb": 4200,
            "_marker": marker,
        })
        db.coa_reconciliation.insert_one({
            "id": f"{marker}-coa",
            "shipment": "SVC-COA-01",
            "suppliers": supplier,
            "completed_unloading": "2026-05-01",
            "status": "critical",
            "umpire_status": "in_progress",
            "delta_loading_internal": -25,
            "ds_mt": 800,
            "_marker": marker,
        })

        report, dashboard, advisor = asyncio.run(_build_service_payloads(supplier, user))
        assert report["filter_scope"] == {
            "period": "2026-05",
            "supplier": supplier,
            "date_from": None,
            "date_to": None,
        }
        assert report["source_counts"]["po_batubara"] == 1
        assert report["source_counts"]["vessel"] == 1
        assert report["arrivals"]["scheduled_tonnage"] == 1000
        assert report["arrivals"]["realized_tonnage"] == 800
        assert report["quality"]["critical_count"] == 1
        assert report["data_health"]["empty"] is False

        assert dashboard["filters"] == {
            "period": "2026-05",
            "supplier": supplier,
            "mode": "vessel",
        }
        assert dashboard["arrivals"]["scheduled_count"] == 1
        assert dashboard["arrivals"]["realized_count"] == 1
        assert dashboard["disputes"]["critical_count"] == 1
        assert dashboard["supplier_risk"][0]["supplier"] == supplier

        assert advisor["filter_scope"]["supplier"] == supplier
        assert advisor["guardrails"]["bounded_context"] is True
        assert advisor["guardrails"]["llm_required"] is False
        assert "Memo Manajemen Bahan Bakar" in advisor["memo_draft"]
        recommendation_ids = {item["id"] for item in advisor["recommendations"]}
        assert {"arrival-risk", "coa-quality-risk", "stale-disputes"} <= recommendation_ids
    finally:
        for collection in ["smartstock", "sumberpemakaian", "po_batubara", "vessels", "coa_reconciliation"]:
            db[collection].delete_many({"_marker": marker})
        client.close()
