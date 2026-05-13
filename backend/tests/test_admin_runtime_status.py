import json

import requests


FORBIDDEN_RUNTIME_TOKENS = [
    "MONGO_URL",
    "JWT_SECRET",
    "password",
    "api_key",
    "secret",
]


def _assert_secret_free(payload):
    text = json.dumps(payload, sort_keys=True).lower()
    for token in FORBIDDEN_RUNTIME_TOKENS:
        assert token.lower() not in text


def _assert_no_mongo_id_key(payload):
    if isinstance(payload, dict):
        assert "_id" not in payload
        for value in payload.values():
            _assert_no_mongo_id_key(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_mongo_id_key(item)


def test_admin_runtime_status_shape_and_secret_free(base_url, admin_headers):
    response = requests.get(f"{base_url}/api/admin/runtime/status", headers=admin_headers, timeout=20)
    assert response.status_code == 200, response.text[:300]

    body = response.json()
    assert body["status"] in {"healthy", "warning", "critical"}
    assert set(body.keys()) >= {
        "status",
        "generated_at",
        "version",
        "backend",
        "database",
        "frontend",
        "backup",
        "smoke",
        "disk",
    }
    assert body["backend"]["api_prefix"] == "/api"
    assert body["database"]["status"] in {"healthy", "critical"}
    assert isinstance(body["database"]["collections"], int)
    assert body["frontend"]["status"] in {"healthy", "warning", "unknown"}
    assert body["smoke"]["status"] in {"pass", "fail", "unknown"}
    assert body["disk"]["status"] in {"healthy", "warning", "critical"}
    _assert_secret_free(body)


def test_runtime_status_requires_admin_auth(base_url):
    response = requests.get(f"{base_url}/api/admin/runtime/status", timeout=20)
    assert response.status_code in {401, 403}


def test_admin_smoke_report_persists_and_appears_in_runtime_status(base_url, admin_headers):
    payload = {
        "started_at": "2026-05-13T09:00:00+00:00",
        "finished_at": "2026-05-13T09:01:00+00:00",
        "base_url": "http://127.0.0.1:18013",
        "frontend_url": "http://127.0.0.1:3000",
        "results": [
            {"name": "backend health", "ok": True, "detail": "HTTP 200"},
            {"name": "frontend", "ok": True, "detail": "HTTP 200"},
        ],
    }
    post_response = requests.post(
        f"{base_url}/api/admin/runtime/smoke-report",
        headers=admin_headers,
        json=payload,
        timeout=20,
    )
    assert post_response.status_code == 200, post_response.text[:300]
    post_body = post_response.json()
    assert post_body["report"]["status"] == "pass"
    assert post_body["report"]["passed"] == 2
    assert post_body["report"]["failed"] == 0
    _assert_no_mongo_id_key(post_body)
    _assert_secret_free(post_body)

    status_response = requests.get(f"{base_url}/api/admin/runtime/status", headers=admin_headers, timeout=20)
    assert status_response.status_code == 200, status_response.text[:300]
    status_body = status_response.json()
    assert status_body["smoke"]["status"] == "pass"
    assert status_body["smoke"]["passed"] == 2
    assert status_body["smoke"]["failed"] == 0
    _assert_no_mongo_id_key(status_body)
    _assert_secret_free(status_body)
