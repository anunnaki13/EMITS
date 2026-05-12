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


def test_contextual_ai_prompts_and_response_citations(base_url, admin_headers):
    client, db = _db()
    marker = f"aictx-{uuid.uuid4().hex[:8]}"
    try:
        db.smartstock.insert_one({
            "id": f"{marker}-stock",
            "date": "2026-05-12",
            "stock_akhir": 1500,
            "total_penerimaan": 500,
            "_marker": marker,
        })
        db.sumberpemakaian.insert_one({
            "id": f"{marker}-usage",
            "date": "2026-05-12",
            "total_pemakaian": 300,
            "_marker": marker,
        })
        db.coa_reconciliation.insert_one({
            "id": f"{marker}-coa",
            "shipment": f"{marker}-SHIP",
            "suppliers": "PT AICTX TEST",
            "completed_unloading": "2026-05-12",
            "status": "critical",
            "umpire_status": "in_progress",
            "delta_loading_internal": 180,
            "ds_mt": 1000,
            "_marker": marker,
        })

        prompts = requests.get(f"{base_url}/api/ai/quick/contextual-prompts", headers=admin_headers, timeout=15)
        assert prompts.status_code == 200, prompts.text[:300]
        prompt_ids = {item["id"] for item in prompts.json()["items"]}
        assert {"daily-summary", "seven-day-stock-risk", "supplier-dispute-pattern", "weekly-report-draft"} <= prompt_ids

        response = requests.post(
            f"{base_url}/api/ai/query",
            headers=admin_headers,
            json={"query": "Buat ringkasan harian", "module": "general"},
            timeout=20,
        )
        assert response.status_code == 200, response.text[:300]
        body = response.json()
        assert "Phase 4 fake" in body["response"]
        slice_names = {item["name"] for item in body["context_slices"]}
        assert "stock_summary" in slice_names
        assert "coa_dispute_summary" in slice_names
        assert "context_limit" in body
    finally:
        for collection in ["smartstock", "sumberpemakaian", "coa_reconciliation"]:
            db[collection].delete_many({"_marker": marker})
        client.close()
