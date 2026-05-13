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


def test_dashboard_drilldown_filters_scope_stock_po_coa_and_disputes(base_url, admin_headers):
    client, db = _db()
    marker = f"drilldown-{uuid.uuid4().hex[:8]}"
    supplier = f"PT {marker.upper()}"
    other_supplier = f"PT OTHER {marker.upper()}"
    supplier_key = supplier.replace(" ", "_").upper()
    other_supplier_key = other_supplier.replace(" ", "_").upper()

    try:
        db.smartstock.insert_many([
            {
                "id": f"{marker}-stock-match",
                "date": "2026-03-10",
                "stock_awal": 1000,
                "suppliers": {supplier_key: {"A": 10, "B": 20, "C": 30}},
                "total_penerimaan": 60,
                "stock_akhir": 1060,
                "_marker": marker,
            },
            {
                "id": f"{marker}-stock-other",
                "date": "2026-03-11",
                "stock_awal": 2000,
                "suppliers": {other_supplier_key: {"A": 90, "B": 0, "C": 0}},
                "total_penerimaan": 90,
                "stock_akhir": 2090,
                "_marker": marker,
            },
        ])
        db.po_batubara.insert_many([
            {
                "id": f"{marker}-po-match",
                "po_number": f"{marker}-PO-1",
                "supplier_name": supplier,
                "completed_year": 2026,
                "completed_month": 3,
                "completed": "2026-03-12",
                "periode": "2026-03-01",
                "tonase_po": 100,
                "total": 1000,
                "_marker": marker,
            },
            {
                "id": f"{marker}-po-other",
                "po_number": f"{marker}-PO-2",
                "supplier_name": other_supplier,
                "completed_year": 2026,
                "completed_month": 3,
                "completed": "2026-03-13",
                "periode": "2026-03-01",
                "tonase_po": 900,
                "total": 9000,
                "_marker": marker,
            },
        ])
        db.coa_reconciliation.insert_many([
            {
                "id": f"{marker}-coa-match",
                "shipment": f"{marker}-SHIP-1",
                "suppliers": supplier,
                "completed_unloading": "2026-03-14",
                "status": "critical",
                "umpire_status": "in_progress",
                "loading_gcv_arb": 4300,
                "unloading_gcv_arb": 4200,
                "internal_gcv_arb": 4100,
                "delta_loading_internal": 200,
                "ds_mt": 100,
                "_marker": marker,
            },
            {
                "id": f"{marker}-coa-other",
                "shipment": f"{marker}-SHIP-2",
                "suppliers": other_supplier,
                "completed_unloading": "2026-03-15",
                "status": "critical",
                "umpire_status": "proposed",
                "loading_gcv_arb": 4300,
                "unloading_gcv_arb": 4200,
                "internal_gcv_arb": 4100,
                "delta_loading_internal": 200,
                "ds_mt": 900,
                "_marker": marker,
            },
        ])

        stock = requests.get(
            f"{base_url}/api/smart-stock",
            headers=admin_headers,
            params={"start_date": "2026-03-01", "end_date": "2026-03-31", "supplier": supplier},
            timeout=15,
        )
        assert stock.status_code == 200, stock.text[:300]
        stock_body = stock.json()
        assert stock_body["total_count"] == 1
        assert stock_body["data"][0]["id"] == f"{marker}-stock-match"
        assert list(stock_body["data"][0]["suppliers"]) == [supplier_key]
        assert stock_body["data"][0]["total_penerimaan"] == 60

        po = requests.get(
            f"{base_url}/api/po-batubara",
            headers=admin_headers,
            params={"year": 2026, "month": 3, "supplier": supplier, "page_size": 50},
            timeout=15,
        )
        assert po.status_code == 200, po.text[:300]
        po_body = po.json()
        assert po_body["total"] == 1
        assert po_body["items"][0]["id"] == f"{marker}-po-match"

        po_years = requests.get(
            f"{base_url}/api/po-batubara/years",
            headers=admin_headers,
            params={"supplier": supplier},
            timeout=15,
        )
        assert po_years.status_code == 200, po_years.text[:300]
        year_2026 = next(item for item in po_years.json() if item["year"] == 2026)
        assert year_2026["months"][str(3)]["count"] == 1

        coa = requests.get(
            f"{base_url}/api/coa-reconciliation",
            headers=admin_headers,
            params={
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
                "supplier": supplier,
                "status": "critical",
                "page_size": 50,
            },
            timeout=15,
        )
        assert coa.status_code == 200, coa.text[:300]
        coa_body = coa.json()
        assert coa_body["total"] == 1
        assert coa_body["items"][0]["id"] == f"{marker}-coa-match"

        kpis = requests.get(
            f"{base_url}/api/coa-reconciliation/kpis",
            headers=admin_headers,
            params={"date_from": "2026-03-01", "date_to": "2026-03-31", "supplier": supplier, "status": "critical"},
            timeout=15,
        )
        assert kpis.status_code == 200, kpis.text[:300]
        kpi_body = kpis.json()
        assert kpi_body["total_records"] == 1
        assert kpi_body["critical_count"] == 1
        assert kpi_body["umpire_status"]["in_progress"] == 1

        trend = requests.get(
            f"{base_url}/api/coa-reconciliation/trend",
            headers=admin_headers,
            params={"months": 6, "date_from": "2026-03-01", "date_to": "2026-03-31", "supplier": supplier},
            timeout=15,
        )
        assert trend.status_code == 200, trend.text[:300]
        assert isinstance(trend.json(), list)

        dispute = requests.get(
            f"{base_url}/api/coa-reconciliation/dispute-monitor",
            headers=admin_headers,
            params={
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
                "supplier": supplier,
                "umpire_status": "in_progress",
                "page_size": 50,
            },
            timeout=15,
        )
        assert dispute.status_code == 200, dispute.text[:300]
        dispute_body = dispute.json()
        assert dispute_body["total"] == 1
        assert dispute_body["items"][0]["id"] == f"{marker}-coa-match"
        assert dispute_body["summary"]["total"] == 1
        assert dispute_body["summary"]["in_progress"] == 1
    finally:
        for collection in ["smartstock", "po_batubara", "coa_reconciliation"]:
            db[collection].delete_many({"_marker": marker})
        client.close()

