"""
Phase-2 auth regression suite.

Covers:
  - AUTHFIX-01: session persists via GET /api/auth/me rehydrate
  - AUTHFIX-02: HTTP error codes match CONS-auth-header
                (400 validation, 401 invalid/expired, 403 missing-credentials FastAPI default)

TEST-02 coverage (five paths required by REQUIREMENTS.md + ROADMAP SC-2):
  1. Login success — valid creds → 200 with access_token (test_login_then_me_rehydrates_same_user)
  2. Login failure — invalid password → 401 (test_login_with_invalid_password_returns_401)
  3. Role-denied — operator/viewer attempting admin-only op → 403 (covered in test_auth_roles.py)
  4. Token-expired — forged JWT with past exp → 401 on GET /api/auth/me (test_me_with_expired_token_returns_401)
  5. /api/auth/me rehydrate — valid token returns same user record (test_login_then_me_rehydrates_same_user)

Contract source: .planning/intel/constraints.md CONS-auth-header
Decision record:  pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md

Runbook (operator playbook for re-execution): see AUTH_CONTRACT.md "Test runbook"
section. All credentials are sourced from environment variables — no inline
literals are committed to this file (CREDENTIAL_HYGIENE.md gate enforces this).
"""
import pytest
import requests

from tests.helpers.jwt import mint_expired_token


# ---------------------------------------------------------------------------
# AUTHFIX-01: session persistence via /api/auth/me rehydrate
# ---------------------------------------------------------------------------

def test_login_then_me_rehydrates_same_user(base_url, admin_credentials):
    """
    AUTHFIX-01: After login, the issued JWT MUST authenticate /api/auth/me
    and return the same user identity. This is the rehydrate path
    AuthContext.js:13-32 exercises on every page load.

    Asserts both the 200 happy path AND that the same user identity round-trips
    through /me — proving the SPA can rehydrate session state from a stored
    JWT without forcing a re-login.
    """
    login = requests.post(f"{base_url}/api/auth/login", json=admin_credentials, timeout=10)
    assert login.status_code == 200, login.text

    body = login.json()
    assert "access_token" in body
    assert "user" in body
    assert body["user"]["email"] == admin_credentials["email"]
    token = body["access_token"]
    login_user_id = body["user"]["id"]

    me = requests.get(
        f"{base_url}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert me.status_code == 200, me.text
    me_body = me.json()
    # Same user identity round-trips through the rehydrate path
    assert me_body["id"] == login_user_id
    assert me_body["email"] == admin_credentials["email"]
    assert me_body["role"] in {"admin", "operator", "viewer"}


# ---------------------------------------------------------------------------
# AUTHFIX-02: HTTP error codes match CONS-auth-header
# ---------------------------------------------------------------------------

def test_login_with_invalid_password_returns_401(base_url, admin_credentials):
    """
    CONS-auth-header: 401 for invalid/expired token. Applies to login with bad creds.
    Backend at server.py:619 raises HTTPException(401, "Email atau password salah").
    """
    bad = dict(admin_credentials)
    bad["password"] = "definitely-not-the-real-password-xyz-12345"
    r = requests.post(f"{base_url}/api/auth/login", json=bad, timeout=10)
    assert r.status_code == 401, r.text
    assert "detail" in r.json()


def test_login_with_malformed_body_returns_400(base_url):
    """
    AUTHFIX-02: CONS-auth-header locks 400 for validation failures.
    Plan 02-02 Task 1 added a custom RequestValidationError handler that
    re-emits 400 (not 422) for /api/auth/* paths. This test pins that
    contract for three concrete malformed-body shapes.
    """
    # Missing password field entirely
    r = requests.post(f"{base_url}/api/auth/login", json={"email": "x@y.com"}, timeout=10)
    assert r.status_code == 400, f"expected 400 (CONS-auth-header), got {r.status_code}: {r.text}"

    # Invalid email format
    r2 = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": "not-an-email", "password": "anything"},
        timeout=10,
    )
    assert r2.status_code == 400, f"expected 400, got {r2.status_code}: {r2.text}"

    # Empty body
    r3 = requests.post(f"{base_url}/api/auth/login", json={}, timeout=10)
    assert r3.status_code == 400, r3.text


def test_me_without_token_returns_403(base_url):
    """
    AUTHFIX-02: FastAPI HTTPBearer default raises 403 when NO Authorization
    header is present. AUTH_CONTRACT.md records this as the explicit accepted
    contract (CONS-auth-header's 401 covers invalid/expired token, not the
    missing-header path).
    """
    r = requests.get(f"{base_url}/api/auth/me", timeout=10)
    assert r.status_code == 403, f"expected 403 (FastAPI HTTPBearer default), got {r.status_code}"


def test_me_with_expired_token_returns_401(base_url):
    """
    TEST-02 Path 4 (token-expired): CONS-auth-header 401 for expired token.

    Uses tests/helpers/jwt.py::mint_expired_token() — no inline secret or JWT
    minting. The helper forges a token whose exp is 5 minutes in the past, using
    the same JWT_SECRET the backend reads (env var, or the known default).
    Assert /api/auth/me rejects it with 401 (not 403 — the token IS present,
    it is merely expired per CONS-auth-header ADR-004).

    Phase-04 plan 02-02 refactored: replaced inline jwt.encode block with
    mint_expired_token() helper (tests/helpers/jwt.py) for DRY + no-import bloat.
    """
    expired_token = mint_expired_token(role="viewer", ago_minutes=5)
    r = requests.get(
        f"{base_url}/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
        timeout=10,
    )
    assert r.status_code == 401, f"expected 401 (expired token), got {r.status_code}: {r.text[:200]}"
