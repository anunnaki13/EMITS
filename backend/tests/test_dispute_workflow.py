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


def test_dispute_workflow_history_notes_attachments_and_closure(base_url, admin_headers):
    client, db = _db()
    marker = f"dispute-{uuid.uuid4().hex[:8]}"
    record_id = f"{marker}-coa"
    try:
        db.coa_reconciliation.insert_one({
            "id": record_id,
            "shipment": f"{marker}-SHIP",
            "suppliers": "PT DISPUTE TEST",
            "completed_unloading": "2026-05-10",
            "status": "critical",
            "umpire_status": "none",
            "loading_gcv_arb": 4300,
            "unloading_gcv_arb": 4200,
            "internal_gcv_arb": 4100,
            "delta_loading_internal": 200,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "_marker": marker,
        })

        propose = requests.post(
            f"{base_url}/api/coa-reconciliation/propose-umpire",
            headers=admin_headers,
            json={"reconciliation_id": record_id, "sample_number": f"{marker}-SAMPLE", "notes": "Ajukan umpire"},
            timeout=15,
        )
        assert propose.status_code == 200, propose.text[:300]

        start = requests.post(
            f"{base_url}/api/coa-reconciliation/update-umpire-status/{record_id}?status=in_progress",
            headers=admin_headers,
            timeout=15,
        )
        assert start.status_code == 200, start.text[:300]

        note = requests.post(
            f"{base_url}/api/coa-reconciliation/{record_id}/dispute-notes",
            headers=admin_headers,
            json={"note": "Dokumen dikirim ke lab", "visibility": "internal"},
            timeout=15,
        )
        assert note.status_code == 200, note.text[:300]

        attachment = requests.post(
            f"{base_url}/api/coa-reconciliation/{record_id}/dispute-attachments",
            headers=admin_headers,
            json={"filename": "ba-umpire.pdf", "url": "https://example.invalid/ba-umpire.pdf", "description": "BA sample"},
            timeout=15,
        )
        assert attachment.status_code == 200, attachment.text[:300]

        result = requests.post(
            f"{base_url}/api/coa-reconciliation/submit-umpire-result",
            headers=admin_headers,
            json={
                "reconciliation_id": record_id,
                "umpire_gcv_arb": 4150,
                "umpire_tm_arb": 30,
                "umpire_ash_arb": 5,
                "umpire_ts_arb": 0.4,
                "umpire_lab_name": "Lab Umpire Test",
                "umpire_result_date": "2026-05-12",
                "notes": "Hasil diterima",
            },
            timeout=15,
        )
        assert result.status_code == 200, result.text[:300]

        close = requests.post(
            f"{base_url}/api/coa-reconciliation/{record_id}/close-dispute",
            headers=admin_headers,
            json={"resolution": "accepted_umpire", "closure_notes": "Dispute ditutup dengan hasil umpire"},
            timeout=15,
        )
        assert close.status_code == 200, close.text[:300]

        detail = requests.get(f"{base_url}/api/coa-reconciliation/{record_id}", headers=admin_headers, timeout=15)
        assert detail.status_code == 200, detail.text[:300]
        record = detail.json()["record"]
        workflow = record["dispute_workflow"]

        assert record["umpire_status"] == "completed"
        assert workflow["resolution"] == "accepted_umpire"
        assert workflow["note_count"] == 1
        assert workflow["attachment_count"] == 1
        assert workflow["history_count"] >= 6
        assert [event["action"] for event in workflow["history"]][-1] == "close"

        monitor = requests.get(
            f"{base_url}/api/coa-reconciliation/dispute-monitor?umpire_status=completed",
            headers=admin_headers,
            timeout=15,
        )
        assert monitor.status_code == 200, monitor.text[:300]
        matching = [item for item in monitor.json()["items"] if item["id"] == record_id]
        assert matching
        assert matching[0]["dispute_workflow"]["resolution"] == "accepted_umpire"
    finally:
        db.coa_reconciliation.delete_many({"_marker": marker})
        client.close()
