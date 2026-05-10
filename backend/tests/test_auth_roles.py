"""
Phase-2 role-enforcement regression suite (AUTHFIX-03).

Confirms admin/operator/viewer role gates on representative endpoints:
  - GET  /api/vessels         — any-authenticated   (admin, operator, viewer all 200)
  - POST /api/upload/vessel   — admin OR operator   (viewer 403; admin/operator 400 on empty payload, NOT 403)
  - DELETE /api/vessels       — admin only          (operator/viewer 403; admin-success gated by RUN_DESTRUCTIVE_TESTS=1)
  - GET  /api/users           — admin only          (operator/viewer 403; admin 200)

Credentials sourced from env vars per docs/audit/CREDENTIAL_HYGIENE.md.
Live backend exercised at REACT_APP_BACKEND_URL (default http://localhost:8013).

Endpoints verified at plan-time against backend/server.py:
  - require_role implementation:           server.py:599
  - GET    /api/users  (admin only):       server.py:665
  - DELETE /api/vessels (admin only):      server.py:746
  - POST   /api/upload/vessel (a/op):      server.py:1383
  - GET    /api/vessels (any auth):        server.py:685
"""
import io
import os

import pytest
import requests


# ---------------------------------------------------------------------------
# Local fixtures — keep zero overlap with conftest.py (Plan 02-02 wave-2 parallelism)
# ---------------------------------------------------------------------------

def _login(base_url: str, creds: dict) -> str:
    r = requests.post(f"{base_url}/api/auth/login", json=creds, timeout=10)
    assert r.status_code == 200, f"login failed for {creds.get('email')}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def operator_token(base_url, operator_credentials):
    return _login(base_url, operator_credentials)


@pytest.fixture(scope="module")
def operator_headers(operator_token):
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture(scope="module")
def viewer_token(base_url, viewer_credentials):
    return _login(base_url, viewer_credentials)


@pytest.fixture(scope="module")
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


# ---------------------------------------------------------------------------
# Read tier — any authenticated user can GET /api/vessels
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_name,headers_fixture", [
    ("admin", "admin_headers"),
    ("operator", "operator_headers"),
    ("viewer", "viewer_headers"),
])
def test_get_vessels_succeeds_for_all_roles(request, base_url, role_name, headers_fixture):
    """AUTHFIX-03: GET /api/vessels is the any-authenticated read tier (FRONTEND_MAP confirms)."""
    headers = request.getfixturevalue(headers_fixture)
    r = requests.get(f"{base_url}/api/vessels?page=1&page_size=1", headers=headers, timeout=10)
    assert r.status_code == 200, f"{role_name} GET /api/vessels failed: {r.status_code} {r.text}"
    body = r.json()
    # Pagination contract spot-check (CONS-pagination-shape)
    assert "items" in body and "total" in body and "page" in body


# ---------------------------------------------------------------------------
# Operator+Admin tier — POST /api/upload/vessel
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_name,headers_fixture,expected_status_set", [
    # admin/operator pass the role gate, then Excel parsing fails on empty payload → 400
    ("admin", "admin_headers", {400}),
    ("operator", "operator_headers", {400}),
    # viewer is blocked at the role gate before parsing → 403
    ("viewer", "viewer_headers", {403}),
])
def test_upload_vessel_role_gate(request, base_url, role_name, headers_fixture, expected_status_set):
    """
    AUTHFIX-03: POST /api/upload/vessel is admin/operator only.
    Empty multipart payload → 400 for allowed roles (parser rejects); 403 for viewer (role gate).
    We never send a real Excel file → no production data mutation.
    """
    headers = request.getfixturevalue(headers_fixture)
    # Send a deliberately-empty xlsx so the parser rejects post-gate
    files = {"file": ("empty.xlsx", io.BytesIO(b""), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = requests.post(f"{base_url}/api/upload/vessel", headers=headers, files=files, timeout=15)
    assert r.status_code in expected_status_set, (
        f"{role_name} upload returned {r.status_code} (expected one of {expected_status_set}): {r.text[:200]}"
    )


# ---------------------------------------------------------------------------
# Admin-only tier — DELETE /api/vessels and GET /api/users
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_name,headers_fixture", [
    ("operator", "operator_headers"),
    ("viewer", "viewer_headers"),
])
def test_delete_all_vessels_blocks_non_admin(request, base_url, role_name, headers_fixture):
    """
    AUTHFIX-03: DELETE /api/vessels (delete-all) is admin only.
    Operator and viewer MUST receive 403 from the role gate BEFORE any DB operation.
    Admin-success path is gated separately by RUN_DESTRUCTIVE_TESTS=1 (see test_delete_all_vessels_admin_success).
    """
    headers = request.getfixturevalue(headers_fixture)
    r = requests.delete(f"{base_url}/api/vessels", headers=headers, timeout=10)
    assert r.status_code == 403, f"{role_name} DELETE /api/vessels returned {r.status_code}, expected 403: {r.text}"


@pytest.mark.skipif(
    os.environ.get("RUN_DESTRUCTIVE_TESTS") != "1",
    reason="Destructive: DELETE /api/vessels removes ALL vessel records. "
    "Set RUN_DESTRUCTIVE_TESTS=1 only against a non-production database.",
)
def test_delete_all_vessels_admin_success(base_url, admin_headers):
    """
    AUTHFIX-03: Admin-success path for DELETE /api/vessels.
    Gated to non-prod environments by RUN_DESTRUCTIVE_TESTS=1. Operator runs this once
    (e.g., against a Mongo dump replayed locally) and records the pass in the SUMMARY.
    """
    r = requests.delete(f"{base_url}/api/vessels", headers=admin_headers, timeout=30)
    assert r.status_code in {200, 204}, f"admin DELETE /api/vessels failed: {r.status_code} {r.text}"


@pytest.mark.parametrize("role_name,headers_fixture,expected_status", [
    ("admin", "admin_headers", 200),
    ("operator", "operator_headers", 403),
    ("viewer", "viewer_headers", 403),
])
def test_get_users_admin_only(request, base_url, role_name, headers_fixture, expected_status):
    """AUTHFIX-03: GET /api/users is admin-only (ENDPOINT_AUDIT.md confirms)."""
    headers = request.getfixturevalue(headers_fixture)
    r = requests.get(f"{base_url}/api/users", headers=headers, timeout=10)
    assert r.status_code == expected_status, (
        f"{role_name} GET /api/users returned {r.status_code}, expected {expected_status}: {r.text}"
    )
