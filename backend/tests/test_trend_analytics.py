import asyncio
import os
import uuid

import pymongo
import requests


_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)


def _db():
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError("MONGO_TEST_DB_NAME unset")
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
    return client, client[name]


async def _build_trends(**kwargs):
    from services.trend_analytics import build_trend_analytics

    return await build_trend_analytics(**kwargs)


def _run(coro):
    return _LOOP.run_until_complete(coro)


def _seed_trend_records(db, marker: str, supplier: str):
    db.smartstock.insert_many([
        {
            "id": f"{marker}-stock-current",
            "date": "2026-03-15",
            "stock_awal": 1200,
            "total_penerimaan": 1000,
            "stock_akhir": 2000,
            "_marker": marker,
        },
        {
            "id": f"{marker}-stock-previous",
            "date": "2026-03-05",
            "stock_awal": 1000,
            "total_penerimaan": 600,
            "stock_akhir": 1500,
            "_marker": marker,
        },
    ])
    db.sumberpemakaian.insert_many([
        {
            "id": f"{marker}-usage-current",
            "date": "2026-03-16",
            "total_pemakaian": 330,
            "_marker": marker,
        },
        {
            "id": f"{marker}-usage-previous",
            "date": "2026-03-06",
            "total_pemakaian": 440,
            "_marker": marker,
        },
    ])
    db.po_batubara.insert_many([
        {
            "id": f"{marker}-po-current",
            "no_jadwal": f"{marker}-JADWAL-CURRENT",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-03-16",
            "tonase_po": 1000,
            "_marker": marker,
        },
        {
            "id": f"{marker}-po-previous",
            "no_jadwal": f"{marker}-JADWAL-PREVIOUS",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-03-04",
            "tonase_po": 500,
            "_marker": marker,
        },
        {
            "id": f"{marker}-po-forecast",
            "no_jadwal": f"{marker}-JADWAL-FORECAST",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-05-20",
            "tonase_po": 1200,
            "_marker": marker,
        },
    ])
    db.vessels.insert_many([
        {
            "id": f"{marker}-vessel-current",
            "shipment_code": f"{marker}-VESSEL-CURRENT",
            "suppliers": supplier,
            "completed_unloading": "2026-03-17",
            "time_arrival": "2026-03-16",
            "ds_mt": 900,
            "gcv_arb": 4200,
            "_marker": marker,
        },
        {
            "id": f"{marker}-vessel-previous",
            "shipment_code": f"{marker}-VESSEL-PREVIOUS",
            "suppliers": supplier,
            "completed_unloading": "2026-03-05",
            "time_arrival": "2026-03-04",
            "ds_mt": 400,
            "gcv_arb": 4100,
            "_marker": marker,
        },
    ])
    db.coa_reconciliation.insert_many([
        {
            "id": f"{marker}-coa-current",
            "shipment": f"{marker}-COA-CURRENT",
            "suppliers": supplier,
            "completed_unloading": "2026-03-17",
            "status": "warning",
            "umpire_status": "in_progress",
            "delta_loading_internal": 35,
            "ds_mt": 900,
            "_marker": marker,
        },
        {
            "id": f"{marker}-coa-previous",
            "shipment": f"{marker}-COA-PREVIOUS",
            "suppliers": supplier,
            "completed_unloading": "2026-03-05",
            "status": "warning",
            "umpire_status": "completed",
            "delta_loading_internal": 90,
            "ds_mt": 400,
            "_marker": marker,
        },
    ])


def test_trend_analytics_current_previous_supplier_and_forecast():
    client, db = _db()
    marker = f"trend-svc-{uuid.uuid4().hex[:8]}"
    supplier = f"PT TREND {marker.upper()}"
    try:
        _seed_trend_records(db, marker, supplier)

        payload = _run(_build_trends(
            period="all",
            supplier=supplier,
            mode="vessel",
            date_from="2026-03-10",
            date_to="2026-03-20",
        ))

        assert payload["period_comparison"]["mode"] == "date_range"
        assert payload["confidence"] in {"high", "medium"}
        assert payload["sparse_data"] is False
        assert payload["metrics"]["stock"]["current"] == 2000
        assert payload["metrics"]["stock"]["previous"] == 1500
        assert payload["metrics"]["arrivals"]["current"] == 90
        assert payload["metrics"]["quality_delta"]["status"] == "improving"
        assert payload["metrics"]["disputes"]["status"] == "worsening"
        assert payload["stock_forecast"]["avg_daily_usage"] > 0
        assert payload["stock_forecast"]["expected_arrivals_30d"] >= 1200
        assert len(payload["stock_forecast"]["horizons"]) == 3

        supplier_row = next(item for item in payload["supplier_trends"] if item["supplier"] == supplier)
        assert supplier_row["risk_status"] in {"low", "medium", "high"}
        assert supplier_row["volume"]["delta"] == 500
        assert supplier_row["quality_delta"]["status"] == "improving"
        assert supplier_row["disputes"]["status"] == "worsening"
    finally:
        for collection in ["smartstock", "sumberpemakaian", "po_batubara", "vessels", "coa_reconciliation"]:
            db[collection].delete_many({"_marker": marker})
        client.close()


def test_trend_analytics_sparse_data_degrades_with_indonesian_caveat():
    client, db = _db()
    marker = f"trend-sparse-{uuid.uuid4().hex[:8]}"
    supplier = f"PT SPARSE {marker.upper()}"
    try:
        db.smartstock.insert_one({
            "id": f"{marker}-stock",
            "date": "2026-01-10",
            "stock_awal": 100,
            "total_penerimaan": 50,
            "stock_akhir": 120,
            "_marker": marker,
        })

        payload = _run(_build_trends(
            period="all",
            supplier=supplier,
            date_from="2026-01-10",
            date_to="2026-01-11",
        ))

        assert payload["sparse_data"] is True
        assert payload["confidence"] == "low"
        assert any("Data historis periode pembanding belum cukup" in item for item in payload["caveats"])
        assert any("pemakaian stock" in item for item in payload["caveats"])
    finally:
        db.smartstock.delete_many({"_marker": marker})
        client.close()


def test_dashboard_and_management_report_include_trend_analytics(base_url, admin_headers):
    client, db = _db()
    marker = f"trend-api-{uuid.uuid4().hex[:8]}"
    supplier = f"PT TREND API {marker.upper()}"
    try:
        _seed_trend_records(db, marker, supplier)

        dashboard = requests.get(
            f"{base_url}/api/dashboard/operational",
            headers=admin_headers,
            params={"period": "2026-03", "supplier": supplier, "mode": "vessel"},
            timeout=20,
        )
        assert dashboard.status_code == 200, dashboard.text[:300]
        dashboard_body = dashboard.json()
        assert "trend_analytics" in dashboard_body
        assert "stock_forecast" in dashboard_body["trend_analytics"]
        assert "supplier_trends" in dashboard_body["trend_analytics"]
        assert "arrivals" in dashboard_body["trend_analytics"]["metrics"]

        report = requests.get(
            f"{base_url}/api/reports/management",
            headers=admin_headers,
            params={"date_from": "2026-03-10", "date_to": "2026-03-20", "supplier": supplier},
            timeout=20,
        )
        assert report.status_code == 200, report.text[:300]
        report_body = report.json()
        assert "trend_analytics" in report_body
        assert report_body["trend_analytics"]["filter_scope"]["supplier"] == supplier
        assert report_body["trend_analytics"]["stock_forecast"]["horizons"]
        assert any(item["supplier"] == supplier for item in report_body["trend_analytics"]["supplier_trends"])
    finally:
        for collection in ["smartstock", "sumberpemakaian", "po_batubara", "vessels", "coa_reconciliation"]:
            db[collection].delete_many({"_marker": marker})
        client.close()
