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


def _seed_advisor_records(db, marker: str, supplier: str):
    db.smartstock.insert_many([
        {
            "id": f"{marker}-stock-current",
            "date": "2026-04-15",
            "stock_awal": 800,
            "total_penerimaan": 100,
            "stock_akhir": 500,
            "_marker": marker,
        },
        {
            "id": f"{marker}-stock-previous",
            "date": "2026-04-05",
            "stock_awal": 1200,
            "total_penerimaan": 300,
            "stock_akhir": 1000,
            "_marker": marker,
        },
    ])
    db.sumberpemakaian.insert_many([
        {
            "id": f"{marker}-usage-current",
            "date": "2026-04-16",
            "total_pemakaian": 900,
            "_marker": marker,
        },
        {
            "id": f"{marker}-usage-previous",
            "date": "2026-04-06",
            "total_pemakaian": 300,
            "_marker": marker,
        },
    ])
    db.po_batubara.insert_many([
        {
            "id": f"{marker}-po-current",
            "no_jadwal": f"{marker}-JADWAL-CURRENT",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-04-16",
            "tonase_po": 1000,
            "_marker": marker,
        },
        {
            "id": f"{marker}-po-dq",
            "no_jadwal": f"{marker}-JADWAL-DQ",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-04-17",
            "tonase_po": -50,
            "_marker": marker,
        },
        {
            "id": f"{marker}-po-previous",
            "no_jadwal": f"{marker}-JADWAL-PREVIOUS",
            "supplier_name": supplier,
            "moda": "Vessel",
            "time_arrival": "2026-04-04",
            "tonase_po": 700,
            "_marker": marker,
        },
    ])
    db.vessels.insert_many([
        {
            "id": f"{marker}-vessel-current",
            "shipment_code": f"{marker}-VESSEL-CURRENT",
            "suppliers": supplier,
            "completed_unloading": "2026-04-18",
            "time_arrival": "2026-04-17",
            "ds_mt": 500,
            "gcv_arb": 4200,
            "_marker": marker,
        },
        {
            "id": f"{marker}-vessel-previous",
            "shipment_code": f"{marker}-VESSEL-PREVIOUS",
            "suppliers": supplier,
            "completed_unloading": "2026-04-05",
            "time_arrival": "2026-04-04",
            "ds_mt": 700,
            "gcv_arb": 4100,
            "_marker": marker,
        },
    ])
    db.coa_reconciliation.insert_many([
        {
            "id": f"{marker}-coa-current",
            "shipment": f"{marker}-COA-CURRENT",
            "suppliers": supplier,
            "completed_unloading": "2026-04-18",
            "status": "critical",
            "umpire_status": "in_progress",
            "delta_loading_internal": 180,
            "ds_mt": 500,
            "_marker": marker,
        },
        {
            "id": f"{marker}-coa-previous",
            "shipment": f"{marker}-COA-PREVIOUS",
            "suppliers": supplier,
            "completed_unloading": "2026-04-05",
            "status": "warning",
            "umpire_status": "completed",
            "delta_loading_internal": 40,
            "ds_mt": 700,
            "_marker": marker,
        },
    ])


def _cleanup(db, marker: str):
    for collection in ["smartstock", "sumberpemakaian", "po_batubara", "vessels", "coa_reconciliation"]:
        db[collection].delete_many({"_marker": marker})


def test_ai_advisor_v3_context_groups_and_default_no_llm(base_url, admin_headers):
    client, db = _db()
    marker = f"advisor-v3-{uuid.uuid4().hex[:8]}"
    supplier = f"PT ADVISOR {marker.upper()}"
    try:
        _seed_advisor_records(db, marker, supplier)
        response = requests.get(
            f"{base_url}/api/ai/advisor/operational",
            headers=admin_headers,
            params={
                "supplier": supplier,
                "date_from": "2026-04-10",
                "date_to": "2026-04-20",
            },
            timeout=20,
        )
        assert response.status_code == 200, response.text[:300]
        payload = response.json()

        assert payload["trend_context"]["metrics"]
        assert payload["data_quality_context"]["status"] in {"critical", "warning"}
        assert payload["confidence"]["level"] in {"low", "medium"}
        assert payload["limitations"]
        assert payload["recommendation_groups"]
        assert payload["guardrails"]["llm_required"] is False
        assert payload["guardrails"]["llm_enabled"] is False
        assert payload["guardrails"]["llm_used"] is False
        assert any(item["id"] == "data-quality-followup" for item in payload["recommendations"])
        for item in payload["recommendations"]:
            assert item["source_slice"]
            assert item["owner_role"]
            assert item["category"]
            assert item["evidence"]
    finally:
        _cleanup(db, marker)
        client.close()


def test_ai_advisor_default_polish_path_does_not_call_client(monkeypatch):
    import asyncio
    import services.operational_advisor as advisor_module

    monkeypatch.delenv("ADVISOR_LLM_POLISH", raising=False)

    def fail_if_called():
        raise AssertionError("LLM client should not be used when ADVISOR_LLM_POLISH is disabled")

    monkeypatch.setattr(advisor_module, "get_ai_client", fail_if_called)
    memo, guardrails = asyncio.run(advisor_module._maybe_polish_memo("Memo deterministic", {}, [], []))
    assert memo == "Memo deterministic"
    assert guardrails["llm_enabled"] is False
    assert guardrails["llm_used"] is False


def test_ai_advisor_optional_llm_polish_uses_fake_client(monkeypatch):
    import asyncio
    import services.operational_advisor as advisor_module

    class FakePolishClient:
        async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
            assert session_id == "advisor-polish"
            assert "Jangan menambah fakta baru" in system_prompt
            assert "deterministic_memo" in user_message
            return "Memo polish dari fake client."

    monkeypatch.setenv("ADVISOR_LLM_POLISH", "1")
    monkeypatch.setattr(advisor_module, "get_ai_client", lambda: FakePolishClient())
    memo, guardrails = asyncio.run(advisor_module._maybe_polish_memo(
        "Memo deterministic",
        {"source_slices": [{"name": "stock_summary"}], "filter_scope": {"period": "2026-04"}},
        [{"id": "stock-warning", "source_slice": "stock_summary"}],
        ["Data pembanding terbatas."],
    ))

    assert memo == "Memo polish dari fake client."
    assert guardrails["llm_enabled"] is True
    assert guardrails["llm_used"] is True
    assert guardrails["fallback_reason"] is None


def test_ai_advisor_optional_llm_failure_falls_back(monkeypatch):
    import asyncio
    import services.operational_advisor as advisor_module

    class FailingPolishClient:
        async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
            raise RuntimeError("simulated polish failure")

    monkeypatch.setenv("ADVISOR_LLM_POLISH", "1")
    monkeypatch.setattr(advisor_module, "get_ai_client", lambda: FailingPolishClient())
    memo, guardrails = asyncio.run(advisor_module._maybe_polish_memo(
        "Memo Manajemen Bahan Bakar\nDeterministic",
        {"source_slices": [], "filter_scope": {}},
        [],
        [],
    ))

    assert memo.startswith("Memo Manajemen Bahan Bakar")
    assert guardrails["llm_enabled"] is True
    assert guardrails["llm_used"] is False
    assert guardrails["fallback_reason"] == "LLM polish gagal; memo deterministic digunakan."
