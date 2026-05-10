"""
Shared pytest fixtures for Phase-2 auth regression tests.

All credentials sourced from environment variables per
docs/audit/CREDENTIAL_HYGIENE.md. NO inline literals.

Source the env vars from memory/test_credentials.md (gitignored) before invoking
pytest. See docs/audit/AUTH_CONTRACT.md "Test runbook" for the exact export block.
"""
import os
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8013").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "pltu_tenayan")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(
            f"{name} is required. Source from memory/test_credentials.md and export "
            f"before running pytest. See docs/audit/CREDENTIAL_HYGIENE.md."
        )
    return value


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def admin_credentials() -> dict:
    return {
        "email": _require_env("TEST_ADMIN_EMAIL"),
        "password": _require_env("TEST_ADMIN_PASSWORD"),
    }


@pytest.fixture(scope="session")
def operator_credentials() -> dict:
    return {
        "email": _require_env("TEST_OPERATOR_EMAIL"),
        "password": _require_env("TEST_OPERATOR_PASSWORD"),
    }


@pytest.fixture(scope="session")
def viewer_credentials() -> dict:
    return {
        "email": _require_env("TEST_VIEWER_EMAIL"),
        "password": _require_env("TEST_VIEWER_PASSWORD"),
    }


@pytest.fixture(scope="session")
def admin_token(base_url: str, admin_credentials: dict) -> str:
    r = requests.post(f"{base_url}/api/auth/login", json=admin_credentials, timeout=10)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session", autouse=True)
def cleanup_audit_probe_users():
    """
    Remove the 3 audit-probe-* synthetic users inserted during Phase 1 plan 01-04
    before the auth regression suite runs. Idempotent.

    Filter is anchor-prefixed (^audit-probe-) so it CANNOT match real users.
    Tolerates Mongo being unreachable (degrades to a print) so unit tests that
    don't need DB still pass on environments without Mongo.
    """
    deleted = 0
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2000)
        try:
            result = client[DB_NAME].users.delete_many({"email": {"$regex": "^audit-probe-"}})
            deleted = result.deleted_count
            print(f"[conftest] cleanup_audit_probe_users: deleted {deleted}")
        finally:
            client.close()
    except Exception as e:  # pragma: no cover — defensive degradation
        print(f"[conftest] cleanup_audit_probe_users skipped: {e}")
    yield deleted
    # No teardown — tests do not insert audit-probe-* users.
