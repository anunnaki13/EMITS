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


def test_po_import_preview_commit_and_history(base_url, admin_headers):
    client, db = _db()
    marker = f"import-po-{uuid.uuid4().hex[:8]}"
    rows = [
        {
            "PO Number": f"{marker}-PO-1",
            "Supplier Name": "PT IMPORT TEST",
            "No Jadwal": f"{marker}-JADWAL-1",
            "Completed": "2026-05-12",
            "Tonase PO": 1000,
            "Total": 123,
        },
        {
            "PO Number": f"{marker}-PO-2",
            "Supplier Name": "PT IMPORT TEST",
            "No Jadwal": f"{marker}-JADWAL-2",
            "Completed": "2026-05-12",
            "Tonase PO": 2000,
            "Total": 456,
        },
    ]
    try:
        files = {"file": ("po.xlsx", _xlsx_bytes(rows), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        preview = requests.post(f"{base_url}/api/import-preview/po-batubara", headers=admin_headers, files=files, timeout=20)
        assert preview.status_code == 200, preview.text[:300]
        body = preview.json()
        assert body["row_count"] == 2
        assert body["preview_rows"][0]["po_number"] == f"{marker}-PO-1"
        assert db.po_batubara.count_documents({"po_number": {"$regex": marker}}) == 0

        commit = requests.post(
            f"{base_url}/api/import-preview/{body['preview_id']}/commit",
            headers=admin_headers,
            json={"mode": "append"},
            timeout=20,
        )
        assert commit.status_code == 200, commit.text[:300]
        assert commit.json()["inserted"] == 2
        assert db.po_batubara.count_documents({"po_number": {"$regex": marker}}) == 2

        history = requests.get(f"{base_url}/api/import-history?dataset=po-batubara", headers=admin_headers, timeout=15)
        assert history.status_code == 200, history.text[:300]
        assert any(item["preview_id"] == body["preview_id"] for item in history.json()["items"])
    finally:
        db.po_batubara.delete_many({"po_number": {"$regex": marker}})
        db.import_previews.delete_many({"filename": "po.xlsx"})
        db.import_history.delete_many({"dataset": "po-batubara", "filename": "po.xlsx"})
        client.close()


def test_merit_order_preview_reports_duplicates(base_url, admin_headers):
    client, db = _db()
    marker = f"import-mo-{uuid.uuid4().hex[:8]}"
    existing = {
        "id": f"{marker}-existing",
        "periode": "2026-05-01",
        "pemasok": f"PT {marker}",
        "moda": "Tongkang",
        "jenis_kontrak": "CIF",
        "rp_kcal": 1.2,
    }
    rows = [
        {"Periode": "2026-05-01", "Pemasok": f"PT {marker}", "Moda": "Tongkang", "Jenis Kontrak": "CIF", "RP/Kcal": 1.3},
        {"Periode": "2026-05-01", "Pemasok": f"PT {marker}", "Moda": "Tongkang", "Jenis Kontrak": "CIF", "RP/Kcal": 1.4},
    ]
    try:
        db.merit_order.insert_one(existing)
        files = {"file": ("mo.xlsx", _xlsx_bytes(rows), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        preview = requests.post(f"{base_url}/api/import-preview/merit-order", headers=admin_headers, files=files, timeout=20)
        assert preview.status_code == 200, preview.text[:300]
        issues = preview.json()["issues"]
        assert any(issue["type"] == "duplicate_in_file" for issue in issues)
        assert any(issue["type"] == "duplicate_existing" for issue in issues)
        assert db.merit_order.count_documents({"pemasok": f"PT {marker}"}) == 1
    finally:
        db.merit_order.delete_many({"pemasok": f"PT {marker}"})
        db.import_previews.delete_many({"filename": "mo.xlsx"})
        client.close()
