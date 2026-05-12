import time
import uuid

import requests


def _audit_items(base_url, admin_headers):
    response = requests.get(f"{base_url}/api/admin/audit-logs?page_size=100", headers=admin_headers, timeout=20)
    assert response.status_code == 200, response.text[:300]
    return response.json()["items"]


def test_audit_logs_rekap_coa_settings_and_user_mutations(base_url, admin_headers):
    marker = f"audit-{uuid.uuid4().hex[:8]}"

    smart_stock_response = requests.post(
        f"{base_url}/api/smart-stock/entry",
        headers=admin_headers,
        json={
            "date": "2026-05-11",
            "stock_awal": 1000,
            "suppliers": {marker: {"zone_1": 25}},
        },
        timeout=20,
    )
    assert smart_stock_response.status_code == 200, smart_stock_response.text[:300]

    coa_response = requests.post(
        f"{base_url}/api/coa-reconciliation/manual",
        headers=admin_headers,
        json={
            "shipment": marker,
            "suppliers": "PT AUDIT TEST",
            "periode": "2026-05",
            "ds_mt": 500,
            "completed_unloading": "2026-05-11",
            "loading_gcv_arb": 4300,
            "unloading_gcv_arb": 4250,
            "internal_gcv_arb": 4200,
        },
        timeout=20,
    )
    assert coa_response.status_code == 200, coa_response.text[:300]

    settings_response = requests.put(
        f"{base_url}/api/settings/coa",
        headers=admin_headers,
        json={"price_per_kcal_per_ton": 150},
        timeout=20,
    )
    assert settings_response.status_code == 200, settings_response.text[:300]

    user_response = requests.post(
        f"{base_url}/api/auth/register",
        headers=admin_headers,
        json={
            "email": f"{marker}@example.com",
            "password": "AuditPass123!",
            "name": "Audit Test User",
            "role": "viewer",
        },
        timeout=20,
    )
    assert user_response.status_code == 200, user_response.text[:300]

    # The middleware writes after the handler completes. A short poll avoids timing flakes.
    expected = {("rekap", "create"), ("coa", "create"), ("settings", "update"), ("users", "create")}
    deadline = time.monotonic() + 5
    observed = set()
    items = []
    while time.monotonic() < deadline:
        items = _audit_items(base_url, admin_headers)
        observed = {(item["category"], item["action"]) for item in items}
        if expected.issubset(observed):
            break
        time.sleep(0.25)

    assert expected.issubset(observed)
    assert all("_id" not in item for item in items)
    assert any(item["path"] == "/api/smart-stock/entry" for item in items)
    assert any(item["path"] == "/api/coa-reconciliation/manual" for item in items)


def test_audit_logs_filters_diff_severity_and_export(base_url, admin_headers):
    marker = f"audit-v2-{uuid.uuid4().hex[:8]}"
    create = requests.post(
        f"{base_url}/api/po-batubara",
        headers=admin_headers,
        json={
            "district_code": "D1",
            "district_name": "Tenayan",
            "periode": "2026-05",
            "stock_code": 1,
            "warehouse": 1,
            "po_number": marker,
            "supplier_code": "SUP",
            "supplier_name": "PT AUDIT V2",
            "spec": "GAR",
            "vessel_tugboat": "TB",
            "barge": "BG",
            "no_jadwal": marker,
            "id_bbo_no_pengiriman": marker,
            "id_bbo_trans": marker,
            "no_shipment": marker,
            "time_arrival": "2026-05-12",
            "completed": "2026-05-12",
            "completed_year": 2026,
            "completed_month": 5,
            "tonase_po": 1000,
            "tonase_po_1000": 1000000,
            "inventory_price": 10,
            "freight_inventory_fob": 1,
            "total": 100,
        },
        timeout=20,
    )
    assert create.status_code == 200, create.text[:300]
    po_id = create.json()["id"]

    update_payload = create.json()
    update_payload["supplier_name"] = "PT AUDIT V2 UPDATED"
    update = requests.put(f"{base_url}/api/po-batubara/{po_id}", headers=admin_headers, json=update_payload, timeout=20)
    assert update.status_code == 200, update.text[:300]

    deadline = time.monotonic() + 5
    update_log = None
    while time.monotonic() < deadline:
        response = requests.get(
            f"{base_url}/api/admin/audit-logs?action=update&resource=po-batubara&record_id={po_id}&page_size=10",
            headers=admin_headers,
            timeout=20,
        )
        assert response.status_code == 200, response.text[:300]
        items = response.json()["items"]
        update_log = next((item for item in items if item.get("record_id") == po_id), None)
        if update_log:
            break
        time.sleep(0.25)

    assert update_log
    assert update_log["severity"] == "medium"
    assert update_log["diff"]["supplier_name"]["before"] == "PT AUDIT V2"
    assert update_log["diff"]["supplier_name"]["after"] == "PT AUDIT V2 UPDATED"

    export = requests.get(
        f"{base_url}/api/admin/audit-logs/export?resource=po-batubara&record_id={po_id}",
        headers=admin_headers,
        timeout=20,
    )
    assert export.status_code == 200, export.text[:300]
    assert "text/csv" in export.headers["content-type"]
    assert "po-batubara" in export.text

    delete = requests.delete(f"{base_url}/api/po-batubara/{po_id}", headers=admin_headers, timeout=20)
    assert delete.status_code == 200, delete.text[:300]
