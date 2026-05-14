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

# Phase 4: default the test port to 18013 (NOT 8013 — that is the live production backend).
# This must happen BEFORE BASE_URL is set, so all tests inherit the test port.
os.environ.setdefault("REACT_APP_BACKEND_URL", "http://127.0.0.1:18013")
# Re-export so subprocess and downstream tests inherit.
os.environ["REACT_APP_BACKEND_URL"] = os.environ["REACT_APP_BACKEND_URL"]

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:18013").rstrip("/")
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


def _base_url() -> str:
    """Return the current test backend URL (may be updated by _backend_lifecycle)."""
    return os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:18013").rstrip("/")


@pytest.fixture(scope="session")
def base_url() -> str:
    return _base_url()


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


# ==================== Phase 4: Backend Lifecycle + DB Isolation ====================
# D-11 / D-12: session-scoped autouse fixture that spawns the test backend on port 18013
# (NOT 8013 — the live production backend stays untouched) with AI_FAKE=1 and
# MONGO_TEST_DB_NAME injected. Drops the per-session test DB at teardown.

import subprocess
import time
import signal
import uuid
import sys
import tempfile
from pathlib import Path
import pymongo

PHASE4_TEST_PORT = int(os.environ.get("PHASE4_TEST_PORT", "18013"))
SESSION_ID = f"{os.getpid()}{uuid.uuid4().hex[:6]}"
TEST_DB_NAME = f"pltu_tenayan_test_{SESSION_ID}"
PID_FILE = Path(__file__).parent / ".backend.pid"
BACKEND_DIR = Path(__file__).parent.parent  # pltu-tenayan-full-backup/backend/
VENV_UVICORN = BACKEND_DIR / ".venv" / "bin" / "uvicorn"
HEALTH_URL = f"http://127.0.0.1:{PHASE4_TEST_PORT}/api/health"

# Export TEST_DB_NAME so factories and test code can read it.
os.environ["MONGO_TEST_DB_NAME"] = TEST_DB_NAME


def _probe_health(url: str = HEALTH_URL, timeout: int = 2) -> bool:
    """Return True if the health endpoint responds 200."""
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _wait_for_health(url: str = HEALTH_URL, timeout: int = 30) -> bool:
    """Poll health endpoint until 200 or timeout. Returns True if healthy."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _probe_health(url):
            return True
        time.sleep(0.5)
    return False


def _drop_test_db() -> None:
    """Drop the per-session test database.

    Safety guard: returns immediately if TEST_DB_NAME does not start with
    'pltu_tenayan_test_' — this prevents accidentally dropping the production DB
    under any circumstances (T-test-db-cross-contam-01 mitigation).
    """
    if not TEST_DB_NAME.startswith("pltu_tenayan_test_"):
        return
    try:
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        mongo_client.drop_database(TEST_DB_NAME)
        mongo_client.close()
        print(f"[conftest] Dropped test DB: {TEST_DB_NAME}")
    except Exception as e:
        print(f"[conftest] _drop_test_db failed (non-fatal): {e}")


def _kill_stale_pid() -> None:
    """Read PID_FILE and kill the stale process if still running."""
    if not PID_FILE.exists():
        return
    try:
        old_pid = int(PID_FILE.read_text().strip())
        os.kill(old_pid, 0)  # test if alive
        os.kill(old_pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.kill(old_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except (ValueError, ProcessLookupError):
        pass  # Stale PID file but process already gone
    PID_FILE.unlink(missing_ok=True)


@pytest.fixture(scope="session", autouse=True)
def _backend_lifecycle():
    """D-11: Spawn uvicorn on PHASE4_TEST_PORT (default 18013) with AI_FAKE=1 and
    per-session MONGO_TEST_DB_NAME. Teardown kills spawned process and drops test DB.

    This fixture MUST write /tmp/emits-test-server.log on EVERY session (including
    reuse paths) because Plan 04-04 test_no_outbound_llm_calls_observed greps that
    file — no skip path is allowed (T-llm-budget-leak-01 invariant).

    Port isolation: PHASE4_TEST_PORT defaults to 18013. The live production backend
    on :8013 is NOT touched (T-prod-backend-clobber-01 mitigation).
    """
    sentinel_log = Path(tempfile.gettempdir()) / "emits-test-server.log"

    # Update REACT_APP_BACKEND_URL to the test port so all fixtures use it.
    os.environ["REACT_APP_BACKEND_URL"] = f"http://127.0.0.1:{PHASE4_TEST_PORT}"

    # Clean up any stale PID from a previous crashed run.
    _kill_stale_pid()

    env = {
        **os.environ,
        "AI_FAKE": "1",
        "MONGO_TEST_DB_NAME": TEST_DB_NAME,
        "MONGO_URL": os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
        "DB_NAME": os.environ.get("DB_NAME", "pltu_tenayan"),
        "JWT_SECRET": os.environ.get("JWT_SECRET", "tenayan-fuel-management-secret-key-2024"),
        "CORS_ORIGINS": os.environ.get("CORS_ORIGINS", "*"),
        # PYTHONPATH must include BACKEND_DIR so `from tests.fakes.ai_client import FakeAIClient`
        # resolves inside the spawned subprocess (lazy import in get_ai_client()).
        "PYTHONPATH": str(BACKEND_DIR),
    }

    log_fh = open(sentinel_log, "w")
    proc = subprocess.Popen(
        [str(VENV_UVICORN), "server:app", "--host", "127.0.0.1", "--port", str(PHASE4_TEST_PORT)],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
    )
    spawned_pid = proc.pid
    PID_FILE.write_text(str(spawned_pid))

    health_url = f"http://127.0.0.1:{PHASE4_TEST_PORT}/api/health"
    if not _wait_for_health(health_url, timeout=30):
        proc.terminate()
        log_fh.close()
        PID_FILE.unlink(missing_ok=True)
        pytest.fail(
            f"Test backend (PID={spawned_pid}) did not start within 30s on port {PHASE4_TEST_PORT}. "
            f"Check {sentinel_log} for details."
        )

    print(f"[conftest] Test backend started (PID={spawned_pid}) on port {PHASE4_TEST_PORT}, DB={TEST_DB_NAME}")

    yield  # All tests run here

    # Teardown: kill spawned process, close log, drop test DB.
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_fh.close()
    PID_FILE.unlink(missing_ok=True)
    _drop_test_db()


@pytest.fixture(scope="session", autouse=True)
def _seed_baseline_data(_backend_lifecycle):
    """Seed baseline data required by auth and merit_order tests into the test DB.

    1. Admin user — registered via /api/auth/register on the test backend (port 18013)
       using TEST_ADMIN_EMAIL / TEST_ADMIN_PASSWORD env vars. Auth tests (test_auth_session.py,
       test_auth_roles.py) require a valid admin account to exist in the test DB.
       Idempotent: skips if a user with TEST_ADMIN_EMAIL already exists (HTTP 400 = already registered).

    2. Merit order docs — seeds 3 deterministic documents (months 1-3, 2024) to satisfy
       test_merit_order.py:71 (assert len(data) > 0) and :314 (assert len(data) >= 1).
       Idempotent: skips if collection already non-empty.

    Rule 1 auto-fix (04-02): the test backend starts with a fresh isolated DB; without an admin
    user the login-dependent auth tests all fail with 401 "Email atau password salah".
    """
    from tests.factories.merit_order import make_merit_order

    backend_url = os.environ.get("REACT_APP_BACKEND_URL", f"http://127.0.0.1:{PHASE4_TEST_PORT}")
    admin_email = os.environ.get("TEST_ADMIN_EMAIL", "")
    admin_password = os.environ.get("TEST_ADMIN_PASSWORD", "")

    # --- 1. Seed role users via /api/auth/register ---
    role_users = [
        ("admin", admin_email, admin_password, "Test Admin"),
        ("operator", os.environ.get("TEST_OPERATOR_EMAIL", ""), os.environ.get("TEST_OPERATOR_PASSWORD", ""), "Test Operator"),
        ("viewer", os.environ.get("TEST_VIEWER_EMAIL", ""), os.environ.get("TEST_VIEWER_PASSWORD", ""), "Test Viewer"),
    ]
    if admin_email and admin_password:
        for role, email, password, name in role_users:
            if not email or not password:
                print(f"[conftest] _seed_baseline_data: TEST_{role.upper()}_EMAIL/PASSWORD not set, skipping {role} seed")
                continue
            try:
                r = requests.post(
                    f"{backend_url}/api/auth/register",
                    json={
                        "email": email,
                        "password": password,
                        "name": name,
                        "role": role,
                    },
                    timeout=10,
                )
                if r.status_code == 200:
                    print(f"[conftest] _seed_baseline_data: registered {role} user {email}")
                elif r.status_code == 400:
                    # Already registered — idempotent
                    print(f"[conftest] _seed_baseline_data: {role} user {email} already exists")
                else:
                    print(f"[conftest] _seed_baseline_data: {role} register returned {r.status_code}: {r.text[:200]}")
            except Exception as e:
                print(f"[conftest] _seed_baseline_data: {role} register failed (non-fatal): {e}")
    else:
        print("[conftest] _seed_baseline_data: TEST_ADMIN_EMAIL/PASSWORD not set, skipping admin seed")

    # --- 2. Seed merit_order documents ---
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    # T-test-data-leak-01: assert TEST_DB_NAME is correctly namespaced before ANY factory insert.
    assert TEST_DB_NAME.startswith("pltu_tenayan_test_"), (
        f"T-test-data-leak-01: TEST_DB_NAME must start with 'pltu_tenayan_test_', got {TEST_DB_NAME!r}"
    )
    # Re-assert MONGO_TEST_DB_NAME in the parent-process env so factory functions
    # (which read os.environ["MONGO_TEST_DB_NAME"]) write to the same DB the server uses.
    # Guard against double-import drift: conftest.py may be loaded by both pytest's
    # internal machinery (as "conftest") and by test files that do
    # `from tests.conftest import _require_env` (as "tests.conftest"), producing two
    # different TEST_DB_NAME values from two uuid4() calls at module level. The subprocess
    # env is set correctly in _backend_lifecycle (explicit "MONGO_TEST_DB_NAME": TEST_DB_NAME),
    # but os.environ in the parent process may have been overridden by the second import.
    os.environ["MONGO_TEST_DB_NAME"] = TEST_DB_NAME  # re-assert to fix double-import drift
    try:
        mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        existing = mongo_client[TEST_DB_NAME].merit_order.count_documents({})
        if existing == 0:
            for month in [1, 2, 3]:
                make_merit_order(year=2024, month=month)
            print(f"[conftest] _seed_baseline_data: seeded 3 merit_order docs into {TEST_DB_NAME}")
        else:
            print(f"[conftest] _seed_baseline_data: merit_order non-empty ({existing} docs), skipping seed")
        mongo_client.close()
    except Exception as e:
        print(f"[conftest] _seed_baseline_data failed (non-fatal): {e}")

    yield
