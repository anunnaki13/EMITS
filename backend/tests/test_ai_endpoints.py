"""TEST-06: AI endpoint coverage.

Two clusters:
1. LLM-calling endpoints (use FakeAIClient via AI_FAKE=1):
   - POST /api/ai/query (general module -> canned string)
   - POST /api/smart-blending/recommend (blending module -> canned JSON)
2. DB-only quick endpoints (no AI stub; RESEARCH §Focus 7):
   - GET /api/ai/quick/{blending-suggestion,boiler-alerts,contract-status,
                         logistics-losses,smart-stock,coa-alerts}

Plus: structural guard that ZERO outbound LLM calls occur during the test run.

Note on smart-blending response shape: the handler wraps the AI JSON in
``ai_recommendation`` key (not top-level):
  body = {
    "request": {...},
    "ai_recommendation": {"recommendation": [...], "predicted_quality": {...}, ...},
    "data_sources": {...},
  }
CONS-blending-ai-output keys are asserted under ``body["ai_recommendation"]``.
"""
import pytest
import requests
from pathlib import Path


SERVER_LOG = Path("/tmp/emits-test-server.log")


def test_ai_query_with_fake_client(base_url, admin_headers):
    """TEST-06: POST /api/ai/query with AI_FAKE=1 returns canned string."""
    r = requests.post(
        f"{base_url}/api/ai/query",
        json={"query": "halo", "module": "general"},
        headers=admin_headers,
        timeout=15,
    )
    assert r.status_code == 200, f"/api/ai/query: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert "response" in body, f"missing 'response' key: {body}"
    # FakeAIClient.GENERAL_RESPONSE is hard-coded:
    assert "Phase 4 fake" in body["response"], (
        f"expected fake-marker in response, got: {body['response'][:200]}"
    )


def test_smart_blending_with_fake_client(base_url, admin_headers):
    """TEST-06: POST /api/smart-blending/recommend returns canned JSON shape.

    SmartBlendingRequest requires: target_gcv, max_ash, max_sulphur, target_quantity.
    Optional fields with defaults: max_total_moisture=35.0, max_inherent_moisture=18.0,
    min_volatile_matter=35.0, min_fixed_carbon=25.0.

    The handler builds session_id = f"smart-blending-{uuid4()}" which contains
    "blend" — so FakeAIClient routes to BLENDING_JSON automatically (D-05 routing).

    Response structure:
    {
      "request": {...},
      "ai_recommendation": {"recommendation": [...], "predicted_quality": {...},
                             "meets_target": bool, "reasoning": str},
      "data_sources": {...}
    }
    The CONS-blending-ai-output keys are under body["ai_recommendation"].
    """
    payload = {
        "target_gcv": 4200,
        "max_ash": 7.0,
        "max_sulphur": 0.5,
        "target_quantity": 10000,
    }
    r = requests.post(
        f"{base_url}/api/smart-blending/recommend",
        json=payload,
        headers=admin_headers,
        timeout=30,
    )
    assert r.status_code == 200, (
        f"/api/smart-blending/recommend: {r.status_code} {r.text[:400]}"
    )
    body = r.json()
    # Top-level keys from handler return statement
    assert "ai_recommendation" in body, (
        f"missing 'ai_recommendation' wrapper key: {list(body.keys())}"
    )
    ai = body["ai_recommendation"]
    # CONS-blending-ai-output keys — inside ai_recommendation:
    for key in ("recommendation", "predicted_quality", "meets_target", "reasoning"):
        assert key in ai, f"missing {key!r} in ai_recommendation keys: {list(ai.keys())}"
    assert isinstance(ai["recommendation"], list), (
        f"recommendation must be list, got {type(ai['recommendation'])}"
    )
    assert isinstance(ai["predicted_quality"], dict), (
        f"predicted_quality must be dict, got {type(ai['predicted_quality'])}"
    )
    assert isinstance(ai["meets_target"], bool), (
        f"meets_target must be bool, got {type(ai['meets_target'])}"
    )
    assert isinstance(ai["reasoning"], str), (
        f"reasoning must be str, got {type(ai['reasoning'])}"
    )
    # FakeAIClient marker — BLENDING_JSON.reasoning = "Fake blending response for Phase 4 testing."
    assert "Phase 4" in ai["reasoning"], (
        f"expected fake marker in reasoning: {ai['reasoning'][:200]}"
    )


QUICK_ENDPOINTS = [
    "/api/ai/quick/blending-suggestion",
    "/api/ai/quick/boiler-alerts",
    "/api/ai/quick/contract-status",
    "/api/ai/quick/logistics-losses",
    "/api/ai/quick/smart-stock",
    "/api/ai/quick/coa-alerts",
]


@pytest.mark.parametrize("path", QUICK_ENDPOINTS)
def test_ai_quick_endpoint_happy_path(path, base_url, admin_headers):
    """TEST-06: GET /api/ai/quick/* DB-only endpoints — happy path."""
    r = requests.get(f"{base_url}{path}", headers=admin_headers, timeout=15)
    assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert isinstance(body, (dict, list)), (
        f"{path}: unexpected response type {type(body)}: {str(body)[:200]}"
    )


def test_no_outbound_llm_calls_observed():
    """T-llm-budget-leak-01: confirm AI_FAKE=1 prevented any real LLM call.

    If the lifecycle fixture reused a pre-existing backend, it MUST have written
    a sentinel line (see conftest.py ``_backend_lifecycle`` end-of-fixture write).
    Absence of the log file = lifecycle invariant broken = FAIL (not skip), to
    prevent silently bypassing this mitigation.
    """
    assert SERVER_LOG.exists(), (
        f"Server log {SERVER_LOG} not found — lifecycle fixture must always "
        f"write a sentinel even when reusing a pre-existing backend. The "
        f"T-llm-budget-leak-01 guard cannot run without log evidence; this "
        f"test fails to prevent silent bypass of the LLM-budget mitigation."
    )
    log = SERVER_LOG.read_text(errors="ignore")
    markers = [
        "generativelanguage.googleapis.com",  # Gemini host
        "openrouter.ai/api",                  # OpenRouter (future-proof)
        # Provider SDK imports are module-load plumbing; only HTTP host markers
        # are reliable indicators of outbound LLM calls.
        # in the wrapper even when AI_FAKE=1, since the import is lazy but
        # the wrapper file exists. Do NOT include this marker; use HTTP-call
        # markers only.
    ]
    found = [m for m in markers if m in log]
    assert not found, (
        f"Outbound LLM call markers detected in server log: {found}\n"
        f"This indicates AI_FAKE=1 wiring is broken; FakeAIClient was bypassed."
    )
