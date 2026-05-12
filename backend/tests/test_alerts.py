import os
import uuid
from datetime import date, timedelta

import pymongo
import requests


def _db():
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError("MONGO_TEST_DB_NAME unset")
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
    return client, client[name]


def test_alert_generation_idempotent_and_lifecycle(base_url, admin_headers):
    client, db = _db()
    marker = f"alerts-{uuid.uuid4().hex[:8]}"
    old_date = (date.today() - timedelta(days=10)).isoformat()
    try:
        db.po_batubara.insert_one({
            "id": f"{marker}-po",
            "no_jadwal": f"{marker}-JADWAL",
            "supplier_name": "PT ALERT TEST",
            "time_arrival": f"{old_date} 08:00",
            "tonase_po": 1000,
            "_marker": marker,
        })
        db.coa_reconciliation.insert_one({
            "id": f"{marker}-coa",
            "shipment": f"{marker}-SHIP",
            "suppliers": "PT ALERT TEST",
            "completed_unloading": old_date,
            "status": "critical",
            "umpire_status": "in_progress",
            "delta_loading_internal": 150,
            "_marker": marker,
        })

        first = requests.post(f"{base_url}/api/alerts/recompute", headers=admin_headers, timeout=15)
        second = requests.post(f"{base_url}/api/alerts/recompute", headers=admin_headers, timeout=15)
        assert first.status_code == 200, first.text[:300]
        assert second.status_code == 200, second.text[:300]

        list_response = requests.get(f"{base_url}/api/alerts?status=open", headers=admin_headers, timeout=15)
        assert list_response.status_code == 200, list_response.text[:300]
        body = list_response.json()
        items = [item for item in body["items"] if marker in item["key"] or marker in item.get("message", "")]
        keys = [item["key"] for item in items]
        assert len(keys) == len(set(keys))
        assert any(item["type"] == "delayed_arrival" for item in items)
        assert any(item["type"] == "high_coa_delta" for item in items)
        assert "rule_config" in body

        target = items[0]
        ack = requests.post(f"{base_url}/api/alerts/{target['id']}/acknowledge", headers=admin_headers, timeout=15)
        assert ack.status_code == 200, ack.text[:300]
        resolved = requests.post(f"{base_url}/api/alerts/{target['id']}/resolve", headers=admin_headers, timeout=15)
        assert resolved.status_code == 200, resolved.text[:300]

        saved = db.alerts.find_one({"id": target["id"]}, {"_id": 0})
        assert saved["status"] == "resolved"
        assert saved.get("acknowledged_at")
        assert saved.get("resolved_at")
    finally:
        db.po_batubara.delete_many({"_marker": marker})
        db.coa_reconciliation.delete_many({"_marker": marker})
        db.alerts.delete_many({"key": {"$regex": marker}})
        client.close()
