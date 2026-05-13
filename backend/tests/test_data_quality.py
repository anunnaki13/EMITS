import asyncio
import io
import os
import uuid

import pandas as pd
import pymongo
import requests


def _db():
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError("MONGO_TEST_DB_NAME unset")
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
    return client, client[name]


def _xlsx_bytes(rows):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()


async def _service_report(module: str):
    from services.data_quality import build_data_quality_report

    return await build_data_quality_report(module=module, limit=50)


def test_data_quality_service_clean_warning_and_critical_cases():
    client, db = _db()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    marker = f"dq-svc-{uuid.uuid4().hex[:8]}"
    try:
        db.po_batubara.insert_one({
            "id": f"{marker}-po-clean",
            "po_number": f"{marker}-PO-CLEAN",
            "no_jadwal": f"{marker}-JADWAL-CLEAN",
            "supplier_name": "PT DQ CLEAN",
            "time_arrival": "2026-05-13",
            "tonase_po": 1000,
            "_marker": marker,
        })
        clean_report = loop.run_until_complete(_service_report("po_batubara"))
        assert clean_report["counts"]["critical"] == 0
        assert not any(issue["source_record_id"] == f"{marker}-po-clean" for issue in clean_report["issues"])

        db.po_batubara.insert_one({
            "id": f"{marker}-po-warning",
            "po_number": f"{marker}-PO-WARN",
            "no_jadwal": f"{marker}-JADWAL-WARN",
            "supplier_name": "PT DQ WARNING",
            "time_arrival": "",
            "tonase_po": 900,
            "_marker": marker,
        })
        warning_report = loop.run_until_complete(_service_report("po_batubara"))
        assert any(issue["type"] == "missing_date" and issue["source_record_id"] == f"{marker}-po-warning" for issue in warning_report["issues"])

        db.coa_reconciliation.insert_one({
            "id": f"{marker}-coa-critical",
            "shipment": f"{marker}-LOT-1",
            "suppliers": "PT DQ CRITICAL",
            "completed_unloading": "2026-05-10",
            "ds_mt": 1000,
            "delta_loading_internal": 175,
            "_marker": marker,
        })
        critical_report = loop.run_until_complete(_service_report("coa_reconciliation"))
        assert critical_report["status"] == "critical"
        assert any(issue["type"] == "coa_outlier_delta" and issue["severity"] == "critical" for issue in critical_report["issues"])
    finally:
        db.po_batubara.delete_many({"_marker": marker})
        db.coa_reconciliation.delete_many({"_marker": marker})
        loop.close()
        client.close()


def test_data_quality_api_export_and_report_caveats(base_url, admin_headers):
    client, db = _db()
    marker = f"dq-api-{uuid.uuid4().hex[:8]}"
    try:
        db.po_batubara.insert_one({
            "id": f"{marker}-po",
            "po_number": f"{marker}-PO",
            "no_jadwal": f"{marker}-JADWAL",
            "supplier_name": "PT DQ API",
            "time_arrival": "2026-05-12",
            "tonase_po": -10,
            "_marker": marker,
        })
        summary = requests.get(
            f"{base_url}/api/data-quality/summary",
            headers=admin_headers,
            params={"module": "po_batubara"},
            timeout=20,
        )
        assert summary.status_code == 200, summary.text[:300]
        body = summary.json()
        assert body["status"] == "critical"
        assert body["counts"]["critical"] >= 1
        assert any(issue["source_record_id"] == f"{marker}-po" for issue in body["issues"])

        issues = requests.get(
            f"{base_url}/api/data-quality/issues",
            headers=admin_headers,
            params={"module": "po_batubara", "severity": "critical"},
            timeout=20,
        )
        assert issues.status_code == 200, issues.text[:300]
        assert issues.json()["total"] >= 1

        export = requests.get(
            f"{base_url}/api/data-quality/export",
            headers=admin_headers,
            params={"module": "po_batubara", "severity": "critical"},
            timeout=20,
        )
        assert export.status_code == 200, export.text[:300]
        assert "text/csv" in export.headers["content-type"]
        assert "negative_or_unrealistic_value" in export.text

        dashboard = requests.get(
            f"{base_url}/api/dashboard/operational",
            headers=admin_headers,
            params={"period": "2026-05"},
            timeout=20,
        )
        assert dashboard.status_code == 200, dashboard.text[:300]
        assert "data_quality" in dashboard.json()

        report = requests.get(
            f"{base_url}/api/reports/management",
            headers=admin_headers,
            params={"period": "2026-05"},
            timeout=20,
        )
        assert report.status_code == 200, report.text[:300]
        assert "data_quality" in report.json()
    finally:
        db.po_batubara.delete_many({"_marker": marker})
        client.close()


def test_import_preview_includes_data_quality_impact(base_url, admin_headers):
    client, db = _db()
    marker = f"dq-import-{uuid.uuid4().hex[:8]}"
    rows = [
        {
            "PO Number": f"{marker}-PO-1",
            "Supplier Name": "PT DQ IMPORT",
            "No Jadwal": f"{marker}-JADWAL-1",
            "Completed": "2026-05-12",
            "Tonase PO": -100,
            "Total": 123,
        }
    ]
    try:
        files = {"file": ("dq-po.xlsx", _xlsx_bytes(rows), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        preview = requests.post(f"{base_url}/api/import-preview/po-batubara", headers=admin_headers, files=files, timeout=20)
        assert preview.status_code == 200, preview.text[:300]
        body = preview.json()
        assert "data_quality" in body
        assert body["data_quality"]["status"] == "critical"
        assert any(issue["type"] == "negative_or_unrealistic_value" for issue in body["data_quality"]["issues"])
    finally:
        db.import_previews.delete_many({"filename": "dq-po.xlsx"})
        client.close()
