# Phase 04: Test Suite Stabilization - Research

**Researched:** 2026-05-11
**Domain:** pytest / FastAPI / MongoDB / Python test infrastructure
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Test database lifecycle**
- D-01: All Phase 4 tests run against `pltu_tenayan_test_<sessionid>`. Session-scoped fixture creates DB, seeds via factory helpers, drops at teardown. Live `pltu_tenayan` NEVER touched.
- D-02: Seed data uses small Python factory helpers in `tests/factories/` (vessel, barge, trucking, biomassa, po_batubara, merit_order, coa, user). Deterministic fixed seeds where needed.
- D-03: Session-scoped fixture passes test DB name via `MONGO_TEST_DB_NAME` env var that the backend's startup config reads when present (overrides `DB_NAME`).

**AI mock seam**
- D-04: Phase 4 introduces an `AIClient` Protocol (or ABC) in `app/ai/client.py`. Existing `EmergentLLMClient` wrapped behind the interface — NO rename, NO rewrite.
- D-05: `FakeAIClient` in `tests/fakes/ai_client.py`. Returns canned response shapes. No external HTTP, no LLM budget consumed.
- D-06: Production wiring: `Depends(get_ai_client)` returning `EmergentLLMClient`. Conftest overrides `get_ai_client` to return `FakeAIClient` for test session.
- D-07: Provider migration (Gemini → OpenRouter) NOT done in Phase 4.

**Excel fixture provenance**
- D-08: Four committed synthetic xlsx fixtures at `backend/tests/fixtures/excel/`: `vessel_minimal.xlsx`, `barge_minimal.xlsx`, `trucking_minimal.xlsx`, `biomassa_minimal.xlsx`. 5-10 dummy rows, headers identical to production format, no real PT names/contract numbers. Total <50 KB.
- D-09: Upload tests assert 200/201 response + that at least one deterministic field round-trips into MongoDB. No production numerical totals asserted.
- D-10: Header-variant edge cases deferred to Phase 6 OPS-02. `tests/fixtures/excel/HEADER_VARIANTS.md` note created pointing forward.

**Test runner posture**
- D-11: `pytest backend/tests -q` canonical command. Session-scoped autouse fixture `_backend_lifecycle`: (1) probes `http://localhost:8013/api/health` → 200 = reuse, (2) connection-refused = spawn uvicorn subprocess with `MONGO_TEST_DB_NAME`, poll health 30s, (3) write PID to `tests/.backend.pid`, (4) teardown: kill spawned PID only (not pre-existing), drop test DB.
- D-12: Existing 7 test files (1634 lines) NOT refactored to TestClient. New Phase-4 tests follow same `requests`-against-HTTP pattern.
- D-13: `RUN_DESTRUCTIVE_TESTS=1` gate unchanged. Does not default-apply to new tests.

### Claude's Discretion
- `pytest.ini`/`pyproject.toml` placement (under `pltu-tenayan-full-backup/` or `backend/`)
- Whether `tests/factories/` and `tests/fakes/` are flat modules or sub-packages
- Specific assertion helper signatures for pagination contract
- Exact mechanism for `MONGO_TEST_DB_NAME` override in `server.py`

### Deferred Ideas (OUT OF SCOPE)
- LLM provider migration (Gemini → OpenRouter) + `EmergentLLMClient` rename
- Excel header-variant edge cases (Phase 6 OPS-02)
- `pytest --cov-fail-under` coverage threshold enforcement
- Frontend test surface (Jest / RTL)
- CI / GitHub Actions
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | `pytest backend/tests -q` runs to completion and exits zero on a clean checkout against a snapshot of production-shaped data | Sections 3 (subprocess lifecycle), 4 (DB isolation), conftest extension pattern |
| TEST-02 | Auth flow has explicit test coverage: login success, login failure, role-denied, token-expired, `/api/auth/me` rehydrate | Already implemented in test_auth_session.py; Phase 4 sanitizes inline credentials and extends to cover all 5 paths cleanly |
| TEST-03 | Pagination contract `{ items, total, page, page_size, total_pages }` asserted on at least 7 list endpoints | Section 8 (pagination helper), factory seeding pattern |
| TEST-04 | Excel upload tests cover at least one parser path per receipt mode with a fixture file checked into the repo | Section 6 (xlsx fixture generation), section 7 (upload cleanup) |
| TEST-05 | COA reconciliation KPI, trend, supplier-consistency, export endpoints covered by tests | COA factory pattern, endpoint survey in server.py |
| TEST-06 | AI endpoints have mock-based tests that pass without consuming LLM budget | Sections 1-2 (FastAPI override + Protocol), section 7 (AI endpoint survey) |
| TEST-07 | Dashboard `/stats` and `/advanced` each have at least one happy-path test | Dashboard seeding strategy, factory-driven assertions |
</phase_requirements>

---

## Summary

Phase 4 must transform a test suite that depends on a hand-spun backend and inline credentials into one that is fully self-contained: the session-scoped conftest fixture auto-spawns (or reuses) the backend, injects a throwaway database name, seeds collections via factory helpers, stubs the AI layer so no LLM budget is consumed, and drops the test DB on teardown. All 7 new TEST-NN requirements are closed by writing new test files that follow the established `requests`-against-HTTP pattern from Phase 2.

The two central technical challenges are the AI mock seam and the backend lifecycle fixture. The AI mock seam requires introducing a `Protocol`-typed interface around `EmergentLLMClient` and using FastAPI's `app.dependency_overrides` to substitute `FakeAIClient` before any test runs. The backend lifecycle fixture must safely detect and probe a pre-existing backend (using the `/api/health` endpoint), or spawn a fresh uvicorn subprocess with the test DB env var injected, kill only what it spawned, and drop the isolated DB on teardown.

An important codebase discovery: four existing test files (test_dashboard_advanced.py, test_coa_reconciliation.py, test_merit_order.py, test_po_batubara.py) contain inline `"<TEST_ADMIN_PASSWORD>"` literals that are currently exempted from the credential scanner. CREDENTIAL_HYGIENE.md explicitly names these as "TODO Phase 4 TEST-02". Phase 4 must sanitize these files as part of closing TEST-02, removing scanner exemptions as it goes. This is load-bearing work that is not explicitly called out in CONTEXT.md's in-scope list but is required by the CREDENTIAL_HYGIENE.md contract.

**Primary recommendation:** Wave 1 builds the infrastructure (conftest extension, AIClient Protocol, factories, xlsx fixtures, credential sanitization of existing files) before any new test file is written. Wave 2 tests build on that infrastructure in parallel; no wave-2 file should block another.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Test DB lifecycle management | Test conftest (Python) | server.py startup config | conftest creates/drops; server reads env var at startup |
| Backend process lifecycle | Test conftest (Python) | OS process table | conftest spawns/polls/kills uvicorn subprocess |
| AI stubbing | FastAPI dependency override | FakeAIClient in tests/ | Override injected at app level before session; no import-time patching needed |
| Excel fixture generation | Static committed files | openpyxl generation script | Committed blobs are reproducible; no runtime generation needed |
| Credential hygiene | env vars + _require_env() | pre-commit scanner | Tests read from env; scanner blocks literal commits |
| Pagination assertion | Shared helper function | Per-test inline assertion | Helper in conftest or tests/helpers/ reduces duplication |

---

## Research Focus 1: FastAPI Dependency Override Pattern for Testing

### What it is
FastAPI exposes `app.dependency_overrides: dict` — a mapping from a dependency callable to a replacement callable. When a request arrives, FastAPI checks this dict first and calls the override instead of the original. It is the canonical mechanism for stubbing dependencies in tests.

### Recommended approach
Use `app.dependency_overrides` at the **session** scope, not per-test. This matches D-11/D-12's session-scoped lifecycle. The override must be set after importing `app` but before any request is sent through the running subprocess.

**Critical insight:** Because Phase 4 uses a real subprocess (not TestClient), `app.dependency_overrides` in the conftest process does NOT propagate to the subprocess's `app` instance. This changes the strategy entirely.

**Resolution:** `app.dependency_overrides` is only useful with `TestClient`-in-process testing. Since Phase 4 uses a real subprocess backend (D-12), the AI stub must be achieved **inside the subprocess** — i.e., the backend must read the `MONGO_TEST_DB_NAME` env var at startup and also check a test-mode flag to swap in `FakeAIClient`. The simplest mechanism: if `MONGO_TEST_DB_NAME` is set, the `get_ai_client()` provider returns a `FakeAIClient` instead of instantiating `EmergentLLMClient`.

Alternatively, `FakeAIClient` can be wired as the default when `EMERGENT_LLM_KEY` is absent or when `AI_FAKE=1` env var is set. The conftest sets `AI_FAKE=1` in the subprocess environment at spawn time.

### Code/config example

```python
# backend/app/ai/client.py — NEW FILE (D-04)
from typing import Protocol, runtime_checkable

@runtime_checkable
class AIClient(Protocol):
    async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
        ...

# backend/server.py — MODIFIED (D-06)
import os
from app.ai.client import AIClient

def get_ai_client() -> AIClient:
    if os.environ.get("AI_FAKE") == "1" or not os.environ.get("EMERGENT_LLM_KEY"):
        from tests.fakes.ai_client import FakeAIClient  # only imported in test mode
        return FakeAIClient()
    from emergentintegrations.llm.chat import LlmChat
    from backend_wrappers import EmergentLLMClientWrapper  # D-04 wrapper
    return EmergentLLMClientWrapper(api_key=os.environ["EMERGENT_LLM_KEY"])

# Each AI endpoint that currently calls LlmChat directly becomes:
@api_router.post("/ai/query")
async def ai_query(request: AIQueryRequest, user=Depends(get_current_user), ai: AIClient = Depends(get_ai_client)):
    ...
    response = await ai.send_message(session_id, system_prompt, full_query)
    ...
```

If the production wiring is too risky to change (blast radius), an alternative is to spawn the subprocess with `AI_FAKE=1` injected into the environment dict (using `subprocess.Popen(env={**os.environ, "AI_FAKE": "1", "MONGO_TEST_DB_NAME": ...})`). The `get_ai_client()` function checks this flag. Zero change to existing endpoint code except adding `Depends(get_ai_client)` parameter.

### Pitfalls / landmines
- `app.dependency_overrides` does NOT work across process boundaries. It only works when the same Python process serves requests (TestClient). Never assume otherwise.
- Sub-dependencies: if `ai_query()` endpoint calls `get_database_context()` which itself calls `get_ai_client()`, the override must be on the same dependency that is declared in the `Depends()` chain — not the inner function.
- Import ordering: `FakeAIClient` must not be imported at module load time in production code. Use lazy import inside the `if AI_FAKE` branch.
- Cleanup: if using `app.dependency_overrides` in any TestClient-based helper tests, always clean up: `app.dependency_overrides.clear()` in a fixture teardown.

### Source citations
- `[VERIFIED: server.py:2619-2689]` — `ai_query()` endpoint currently instantiates `LlmChat` inline; no `Depends()` injection exists yet.
- `[CITED: FastAPI docs - Testing Dependencies with Overrides]` — https://fastapi.tiangolo.com/advanced/testing-dependencies/
- `[ASSUMED]` — The subprocess env-var approach (`AI_FAKE=1`) is the correct strategy for subprocess-based test suites; TestClient `dependency_overrides` is in-process only.

---

## Research Focus 2: Python Protocol vs ABC for AIClient

### What it is
Both `Protocol` (from `typing`) and `ABC` (from `abc`) allow defining an interface that concrete classes must satisfy. The distinction is structural typing (Protocol) vs nominal typing (ABC).

### Recommended approach
**Use `typing.Protocol` with `@runtime_checkable`.** Rationale:
1. `EmergentLLMClient` from `emergentintegrations` is a third-party class that cannot be subclassed for inheritance without risk of breaking its internal behavior.
2. Protocol's structural typing means `EmergentLLMClientWrapper` and `FakeAIClient` are both `AIClient`-compatible as long as they implement the declared methods — no `class EmergentLLMClientWrapper(AIClient)` declaration needed.
3. `@runtime_checkable` enables `isinstance(client, AIClient)` checks if needed.
4. Protocol is mypy-friendly and the codebase already has mypy in `requirements.txt` (`mypy==1.19.1`).

### Minimal correct Protocol based on server.py actual usage
Reading server.py:2619-2689 (`ai_query()`) and server.py:3617-3843 (`get_smart_blending_recommendation()`), the backend calls `LlmChat` as follows:

```python
chat = LlmChat(api_key=..., session_id=..., system_message=...).with_model(provider, model)
response = await chat.send_message(UserMessage(text=full_query))
# response is a plain str
```

The `send_message` call is the only method tested; `with_model` is constructor chaining. The minimal AIClient Protocol:

```python
# backend/app/ai/client.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class AIClient(Protocol):
    async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
        """Send a message and return the text response."""
        ...
```

The wrapper that adapts `LlmChat` to this interface:

```python
# backend/app/ai/emergent_wrapper.py
from emergentintegrations.llm.chat import LlmChat, UserMessage
from .client import AIClient

class EmergentLLMClientWrapper:
    """Wraps EmergentLLMClient (LlmChat) behind AIClient. No rename per D-07."""

    def __init__(self, api_key: str, provider: str = "gemini", model: str = "gemini-2.5-flash"):
        self._api_key = api_key
        self._provider = provider
        self._model = model

    async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
        chat = LlmChat(
            api_key=self._api_key,
            session_id=session_id,
            system_message=system_prompt
        ).with_model(self._provider, self._model)
        return await chat.send_message(UserMessage(text=user_message))
```

### FakeAIClient for tests

```python
# backend/tests/fakes/ai_client.py
class FakeAIClient:
    """Canned response stub. No LLM budget consumed."""

    CANNED = {
        "general":          '{"response": "Analisis umum: data tersedia di sistem."}',
        "blending":         '{"recommendation": [], "predicted_quality": {"gcv": 4000, "ash": 5.0, "sulphur": 0.3, "total_moisture": 35.0, "inherent_moisture": 18.0, "volatile_matter": 35.0, "fixed_carbon": 25.0}, "meets_target": true, "reasoning": "Fake blending response for test."}',
        "boiler_risk":      "Tidak ada risiko slagging terdeteksi pada data uji.",
        "contract":         "Status kontrak: semua PO dalam batas normal.",
        "logistics":        "Tidak ada anomali logistik pada data uji.",
        "smart_stock":      "Stok batubara dalam kondisi normal.",
        "coa_reconciliation": "Tidak ada deviasi signifikan pada data uji COA.",
    }

    async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
        # Detect module from system_prompt keywords
        for module, response in self.CANNED.items():
            if module.upper() in system_prompt.upper() or module in session_id:
                return response
        return self.CANNED["general"]
```

### Pitfalls
- The `LlmChat` constructor pattern is `LlmChat(...).with_model(...)` — NOT a separate `connect()` call. The wrapper must chain these inside `send_message`, not in `__init__`, to keep the wrapper stateless per-session.
- `smart_blending` endpoint (server.py:3617-3843) calls `LlmChat` directly with a JSON format requirement (`response = await chat.send_message(...)` then `json.loads(response)`). The FakeAIClient for this path MUST return a valid JSON string matching the expected schema (see CONS-blending-ai-output). The blending canned response above satisfies this.

### Source citations
- `[VERIFIED: server.py:2648-2666]` — LlmChat instantiation + send_message pattern confirmed.
- `[VERIFIED: server.py:3801-3828]` — Smart blending path also calls LlmChat + json.loads the response.
- `[ASSUMED]` — Protocol is preferable to ABC for third-party wrapping; the wrapper's duck-typed compatibility is sufficient.

---

## Research Focus 3: pytest Session-Scoped Subprocess Management

### What it is
D-11 requires a session-scoped autouse fixture that probes port 8013, spawns uvicorn if idle, waits for it to be ready, tracks the PID, and kills it on teardown.

### Recommended approach

```python
# backend/tests/conftest.py — EXTENSION (new fixture added below existing code)
import subprocess
import time
import os
import signal
import uuid
import requests as _requests
from pathlib import Path
import pymongo

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8013").rstrip("/")
HEALTH_URL = f"{BACKEND_URL}/api/health"
PID_FILE = Path(__file__).parent / ".backend.pid"
BACKEND_DIR = Path(__file__).parent.parent  # pltu-tenayan-full-backup/backend/
VENV_UVICORN = BACKEND_DIR / ".venv" / "bin" / "uvicorn"

SESSION_ID = uuid.uuid4().hex[:8]
TEST_DB_NAME = f"pltu_tenayan_test_{SESSION_ID}"

def _probe_health(timeout: int = 2) -> bool:
    try:
        r = _requests.get(HEALTH_URL, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False

def _wait_for_health(timeout: int = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _probe_health():
            return True
        time.sleep(0.5)
    return False

@pytest.fixture(scope="session", autouse=True)
def _backend_lifecycle():
    """D-11: Spawn or reuse the backend; inject test DB; teardown on session end."""
    spawned_pid = None

    # Step 1: probe existing backend
    if _probe_health():
        # Pre-existing backend — reuse; DO NOT kill at teardown
        yield
        # Step 4: drop test DB (always)
        _drop_test_db()
        return

    # Step 2: spawn fresh subprocess with test DB env
    # Clean up stale PID file from a previous crashed run
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 0)  # test if process still alive
            # If alive, kill it (stale from previous crashed session)
            os.kill(old_pid, signal.SIGTERM)
            time.sleep(1)
            try:
                os.kill(old_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except (ValueError, ProcessLookupError):
            pass  # PID file stale but process already gone
        PID_FILE.unlink(missing_ok=True)

    env = {
        **os.environ,
        "MONGO_TEST_DB_NAME": TEST_DB_NAME,
        "AI_FAKE": "1",
        # Pass through required vars
        "MONGO_URL": os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
        "DB_NAME": os.environ.get("DB_NAME", "pltu_tenayan"),  # overridden by MONGO_TEST_DB_NAME
        "JWT_SECRET": os.environ.get("JWT_SECRET", "<JWT_SECRET_FALLBACK_REDACTED>"),
        "CORS_ORIGINS": os.environ.get("CORS_ORIGINS", "*"),
    }

    proc = subprocess.Popen(
        [str(VENV_UVICORN), "server:app", "--host", "127.0.0.1", "--port", "8013"],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    spawned_pid = proc.pid
    PID_FILE.write_text(str(spawned_pid))

    # Step 3: wait for health
    if not _wait_for_health(timeout=30):
        proc.terminate()
        PID_FILE.unlink(missing_ok=True)
        pytest.fail(f"Backend did not start within 30s. PID={spawned_pid}")

    yield  # tests run here

    # Step 4a: kill spawned process
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    PID_FILE.unlink(missing_ok=True)

    # Step 4b: drop test DB
    _drop_test_db()


def _drop_test_db():
    """Drop the per-session test database. Failsafe: only drops names matching the prefix."""
    if not TEST_DB_NAME.startswith("pltu_tenayan_test_"):
        return  # Sanity guard
    try:
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        mongo_client.drop_database(TEST_DB_NAME)
        mongo_client.close()
    except Exception as e:
        print(f"[conftest] _drop_test_db failed (non-fatal): {e}")
```

### Detection strategy: `/api/health` vs port probe
**Use `/api/health`** (not a raw port-bind probe). Rationale:
- A port-bind probe (e.g., `socket.connect_ex(("127.0.0.1", 8013))`) returns success the moment the OS binds the port, which can be before uvicorn's workers are ready to serve requests. The health endpoint returns 200 only after the FastAPI app is initialized and routes are registered.
- `GET /api/health` is already implemented in server.py:4487-4489 and returns `{"status": "healthy", ...}`.

### PID file and crash recovery
Write PID file immediately after `Popen()` returns (before polling). On next run, check for stale PID:
1. `os.kill(pid, 0)` — signal 0 tests if process exists without killing it.
2. If exists: SIGTERM → 1s wait → SIGKILL → unlink PID file.
3. If `ProcessLookupError`: process already gone, just unlink.

### SIGTERM/SIGKILL escalation
```python
proc.terminate()           # SIGTERM — graceful
try:
    proc.wait(timeout=5)   # give 5s for uvicorn graceful shutdown
except subprocess.TimeoutExpired:
    proc.kill()            # SIGKILL — force
```

### Linux-only assumptions
- `os.kill(pid, 0)` for process existence check: works on Linux/macOS, NOT on Windows.
- `signal.SIGTERM` / `signal.SIGKILL`: Linux/macOS only. Windows uses `proc.terminate()` = SIGTERM equivalent via `TerminateProcess()`.
- The VPS is Linux (kernel 5.15); macOS local dev will also work since the signal approach is POSIX. Windows is not a concern.

### Pitfalls
- Race condition: spawn subprocess, PID file write, then another test runner (different pytest session) reads the PID file and kills the process. Mitigated by using a test-DB-name that includes `SESSION_ID` (UUID prefix), so two runners targeting the same mongod use distinct databases.
- uvicorn `--reload` flag: DO NOT add `--reload`. Hot-reload forks child processes, causing PID tracking to break.
- Subprocess stdout/stderr: capture with `stdout=subprocess.PIPE` to avoid polluting test output. The pipe must be drained or the process will block when the pipe buffer fills. Either use `stdout=subprocess.DEVNULL` or drain in a separate thread. Simplest: `stdout=open("/tmp/emits-test-server.log", "w"), stderr=subprocess.STDOUT`.
- `EMERGENT_LLM_KEY`: if not present in env and `AI_FAKE` is not set, `get_ai_client()` will raise. Always inject `AI_FAKE=1` when spawning.

### Source citations
- `[VERIFIED: server.py:4487-4489]` — `/api/health` endpoint exists and returns `{"status": "healthy"}`.
- `[VERIFIED: pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md lines 86-89]` — runbook uses `nohup ... uvicorn server:app --host 127.0.0.1 --port 8013`.
- `[ASSUMED]` — subprocess.Popen with env injection is the standard approach for subprocess-based test backends.

---

## Research Focus 4: MongoDB Per-Session Test DB Isolation

### What it is
D-01 requires an isolated `pltu_tenayan_test_<sessionid>` DB created at session start and dropped at teardown. D-03 requires the backend to read `MONGO_TEST_DB_NAME` at startup.

### sessionid generation
Use `uuid.uuid4().hex[:8]` — 8 hex chars give 32 bits of entropy. Combined with the Python process PID for extra safety in multi-runner scenarios:

```python
SESSION_ID = f"{os.getpid()}{uuid.uuid4().hex[:6]}"
TEST_DB_NAME = f"pltu_tenayan_test_{SESSION_ID}"
```

This is safe for multi-CI-runner concurrency: two pytest processes on the same machine will produce distinct `SESSION_ID` values.

### server.py patch for MONGO_TEST_DB_NAME override

The smallest-blast-radius patch is at startup, lines 27-29:

```python
# server.py lines 27-29 — MODIFIED
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
_db_name = os.environ.get("MONGO_TEST_DB_NAME") or os.environ['DB_NAME']
db = client[_db_name]
```

This is a 1-line addition. `MONGO_TEST_DB_NAME` when set overrides `DB_NAME`; when absent, behavior is identical to current. No per-request branching, no new startup lifecycle, no test-only code paths beyond this one override.

**Placement:** immediately after `load_dotenv()` is called, before the `client` and `db` globals are assigned. Because `db` is a module-level global referenced by all async endpoint functions, the override must happen at import/startup time.

### Drop-DB pattern at session teardown
```python
def _drop_test_db():
    if not TEST_DB_NAME.startswith("pltu_tenayan_test_"):
        return  # Safety guard: never drop production DB
    client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    client.drop_database(TEST_DB_NAME)
    client.close()
```

### Multi-developer / multi-CI-runner concurrency
Each pytest session uses a unique `TEST_DB_NAME`. Two runners on the same `mongod` will use `pltu_tenayan_test_12345abc` and `pltu_tenayan_test_67890def` respectively. Since each session creates, uses, and drops its own DB, there is no concurrency hazard. The only shared resource is mongod itself; at current VPS scale (4 GB RAM) two parallel sessions would both fit within memory.

### Factory helpers and seeding
Factories create the minimum documents needed per test class, not a full fixture dump. They seed into `TEST_DB_NAME` by:
1. Accepting a `db` parameter (the Motor async client's test database).
2. Being called from a session-scoped or function-scoped fixture that has access to the test DB name.

Since tests run against the subprocess backend, the conftest cannot pass the Motor `db` object directly to endpoint tests — the test process and the server process are separate. Instead, seed data is inserted directly via pymongo (sync client) in fixtures, then verified via HTTP in the test itself.

```python
# tests/factories/vessel.py
import uuid
from datetime import datetime, timezone

def make_vessel(db, **overrides) -> dict:
    """Insert one minimal vessel document. Returns the doc dict with 'id'."""
    import pymongo
    doc = {
        "id": str(uuid.uuid4()),
        "periode_ta": "Jan-2026", "periode_realisasi": "Jan-2026",
        "shipment_code": "SHP-TEST-001", "voyage_code": "VYG-001",
        "suppliers": "PT TEST SUPPLIER", "voyage": "V001",
        "name_of_vessel": "MV TEST VESSEL", "coal_from": "Kalimantan",
        "gcv_arb": 4200.0, "bl_mt": 5000.0, "ds_mt": 4950.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "test-factory",
        **overrides,
    }
    mongo_client = pymongo.MongoClient(
        os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
        serverSelectionTimeoutMS=3000
    )
    mongo_client[TEST_DB_NAME].vessels.insert_one(doc)
    mongo_client.close()
    return doc
```

### Source citations
- `[VERIFIED: server.py:26-29]` — `db = client[os.environ['DB_NAME']]` — module-level global; override must be at startup.
- `[VERIFIED: pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md lines 83-88]` — Phase 2 runbook injected `DB_NAME=${TEST_DB}` on the uvicorn command line; D-03 formalizes this as `MONGO_TEST_DB_NAME`.
- `[ASSUMED]` — uuid4 hex prefix is sufficient for session uniqueness at single-VPS scale.

---

## Research Focus 5: AsgiTestClient / TestClient Hybrid Possibilities

### What it is
FastAPI's `TestClient` (from starlette) runs the ASGI app in-process, eliminating the subprocess dependency. The existing 1634-line test suite uses `requests` against a live HTTP server.

### Decision: Stay 100% `requests`-against-subprocess

D-12 explicitly locks this decision: existing tests are NOT refactored. New Phase-4 tests follow the same pattern for consistency. The research confirms this is the right call for these additional reasons:

1. **AI stub integration:** The subprocess approach allows `AI_FAKE=1` env-var injection at spawn time, which is simpler than the `app.dependency_overrides` dance required for TestClient.
2. **Middleware fidelity:** The subprocess exercises CORS middleware, startup events (`motor_asyncio` connection), and the `RequestValidationError` handler exactly as in production. TestClient can miss middleware interactions.
3. **Fixture reuse:** All 7 existing test files use `requests.post(f"{BASE_URL}/api/...")` — consistent pattern with zero friction.

**Value-add verdict:** There is no compelling reason to introduce TestClient for new Phase-4 test files. The subprocess lifecycle fixture makes `requests` work cleanly.

### Source citations
- `[VERIFIED: pltu-tenayan-full-backup/backend/tests/test_auth_session.py:37]` — `requests.post(f"{base_url}/api/auth/login", ...)` — established pattern.
- `[CITED: FastAPI docs - Testing]` — https://fastapi.tiangolo.com/tutorial/testing/

---

## Research Focus 6: Excel Synthetic Fixture Generation

### What it is
D-08 requires four committed xlsx files under `backend/tests/fixtures/excel/`. The files must have headers identical to what the production parsers expect, contain 5-10 dummy rows, and be <15 KB each.

### Production header mappings (from server.py parser code)

**vessel_minimal.xlsx** — parser at server.py:1403-1492 reads:
```
Required headers (row.get() calls, exact strings):
"Periode TA (Rakor)", "Periode Realisasi", "Shipment Code", "Voyage Code",
"Suppliers", "Voyage", "Name Of Vessel", "Coal From", "Time Arrival",
"Berthed Time", "Commenced Unloading", "Completed Unloading",
"Durasi Pembongkaran (Hari)", "Durasi Pembongkaran (Jam)",
"waktu tunggu (Jam)", "B/L (MT)", "DS (MT)", "NO.COW",
"Tgl Terbit COW",
"GCV (Kcal/Kg)\nARB" (fallback: "GCV (Kcal/Kg) ARB"),
"TM (%wt)\nARB" (fallback: "TM (%wt) ARB"),
"Ash \nContent (%wt) \nARB" (fallback: "Ash Content (%wt) ARB"),
"Total Sulphur (%wt)\nARB",
"NO. COA", "Tgl Terbit COA", "DURASI TERBIT COA"
```
**Key insight:** The parser uses fallback `row.get("GCV (Kcal/Kg)\nARB", row.get("GCV (Kcal/Kg) ARB"))`. Using the simple non-newline header variant avoids multi-line cell encoding complexity in openpyxl. Use plain headers (`"GCV (Kcal/Kg) ARB"` etc.) in synthetic fixtures.

**barge_minimal.xlsx** — parser at server.py:1521-1598 reads:
```
"Periode", "Shipment Code", "Voyage Code", "Shipment", "Suppliers",
"Voyage", "TB", "BG", "Coal From", "TA", "Berthed Time",
"Commenced Unloading", "Completed Unloading",
"Durasi Pembongkaran (Hari)", "Durasi Pembongkaran (Jam)",
"waktu tunggu (Jam)", "B/L (MT)", "DS (MT)", "NO.COW",
"Tgl Terbit COW", "GCV (Kcal/Kg) ARB", "TM (%wt) ARB",
"Ash Content (%wt) ARB", "Total Sulphur (%wt) ARB",
"NO. COA", "Tgl Terbit COA", "DURASI TERBIT COA"
```

**trucking_minimal.xlsx** — parser at server.py:1635-1710 reads:
```
"Periode TA (Rakor)", "Periode Realisasi", "Shipment Code", "Voyage Code",
"Shipment", "Suppliers", "Transportasi", "Coal From", "TA",
"Berthed Time", "Commenced Unloading", "Completed Unloading",
"Durasi Pembongkaran (Hari)", "Durasi Pembongkaran (Jam)",
"B/L (MT)", "DS (MT)", "RIT", "NO.COW", "Tgl Terbit COW",
"GCV (Kcal/Kg) ARB", "TM (%wt) ARB", "NO. COA", "Tgl Terbit COA"
```

**biomassa_minimal.xlsx** — parser at server.py:1743-1786 uses `df.columns.str.replace('\n', ' ').str.strip()` first, so all multi-line headers are normalized to single-line:
```
"Periode", "Shipment Code", "Voyage Code", "Lot", "Suppliers",
"Shipper", "Lot.1", "TB", "BG", "Biomass" (or "Biomass "),
"TA", "Berthed Time", "Commenced Unloading", "Completed Unloading",
"Durasi Pembongkaran (Hari)", "B/L (MT)", "Jembatan Timbang (MT)",
"Surveyor Unloading", "NO.COW / ROW", "Tgl Terbit COW",
"GCV (Kcal/Kg) ARB", "GCV (Kcal/Kg) ADB", "TM (%wt) ARB",
"IM (%wt) ADB", "NO. COA", "Tgl Terbit COA"
```

### Generation approach
Use `openpyxl` (already in requirements: `openpyxl==3.1.5`). Generate fixtures once via a standalone script, commit the binary blobs, and never regenerate at test time.

```python
# scripts/generate_test_fixtures.py — ONE-TIME SCRIPT
from openpyxl import Workbook
from pathlib import Path

FIXTURE_DIR = Path("backend/tests/fixtures/excel")
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

def write_vessel():
    wb = Workbook()
    ws = wb.active
    headers = [
        "Periode TA (Rakor)", "Periode Realisasi", "Shipment Code", "Voyage Code",
        "Suppliers", "Voyage", "Name Of Vessel", "Coal From",
        "Time Arrival", "Berthed Time", "Commenced Unloading", "Completed Unloading",
        "Durasi Pembongkaran (Hari)", "Durasi Pembongkaran (Jam)", "waktu tunggu (Jam)",
        "B/L (MT)", "DS (MT)", "NO.COW", "Tgl Terbit COW",
        "GCV (Kcal/Kg) ARB", "TM (%wt) ARB", "Ash Content (%wt) ARB",
        "Total Sulphur (%wt) ARB", "NO. COA", "Tgl Terbit COA", "DURASI TERBIT COA",
    ]
    ws.append(headers)
    # 5 deterministic rows — use fixed values for round-trip assertion
    for i in range(1, 6):
        ws.append([
            f"Jan-2026", f"Jan-2026", f"SHP-TEST-{i:03d}", f"VYG-{i:03d}",
            "PT TEST SUPPLIER", f"V{i:03d}", f"MV TEST VESSEL {i}", "Kalimantan",
            "2026-01-15 08:00", "2026-01-15 10:00", "2026-01-15 11:00", "2026-01-16 10:00",
            1.0, 23.0, 2.5, 5000.0 + i * 100, 4950.0 + i * 100,
            f"COW-{i:03d}", "2026-01-17",
            4200.0, 30.5, 5.0, 0.3, f"COA-{i:03d}", "2026-01-18", "3 days",
        ])
    wb.save(FIXTURE_DIR / "vessel_minimal.xlsx")
```

**Deterministic round-trip assertion:** The test uploads `vessel_minimal.xlsx` and then GETs `/api/vessels?search=SHP-TEST-001`. It asserts `items[0]["shipment_code"] == "SHP-TEST-001"` and `items[0]["gcv_arb"] == 4200.0`. This satisfies D-09.

### Commit workflow
The .xlsx files are committed as binary blobs. To regenerate: run `python scripts/generate_test_fixtures.py` from the `pltu-tenayan-full-backup/` directory and commit the updated files. A comment at the top of the script documents this. The `HEADER_VARIANTS.md` file in the same directory notes that multi-line headers and column ordering variants are deferred to Phase 6 OPS-02.

### Source citations
- `[VERIFIED: server.py:1383-1500]` — vessel upload parser column mapping (exact header strings).
- `[VERIFIED: server.py:1502-1606]` — barge upload parser.
- `[VERIFIED: server.py:1608-1718]` — trucking upload parser.
- `[VERIFIED: server.py:1720-1795]` — biomassa upload parser (with normalize-column-names step).
- `[VERIFIED: requirements.txt:68]` — `openpyxl==3.1.5` already present.

---

## Research Focus 7: AI Mock Library Choice and Endpoint Survey

### What it is
D-05 says stub the interface. This section surveys all AI endpoints to determine what shapes `FakeAIClient` must return.

### AI endpoint inventory (from server.py)

| Endpoint | Method | AI path | Response shape | FakeAIClient need |
|----------|--------|---------|----------------|-------------------|
| `POST /api/ai/query` | Uses `LlmChat.send_message()` | Returns `str` | `{"response": str, "session_id": str, "module": str}` | Yes — needs plain str |
| `GET /api/ai/history` | No AI call | Returns list | Not AI-dependent | No |
| `DELETE /api/ai/history` | No AI call | Returns message | Not AI-dependent | No |
| `GET /api/ai/settings` | No AI call | Returns settings dict | Not AI-dependent | No |
| `PUT /api/ai/settings` | No AI call | Returns message | Not AI-dependent | No |
| `GET /api/ai/sessions` | No AI call | Paginated sessions | Not AI-dependent | No |
| `GET /api/ai/sessions/{id}` | No AI call | Session messages | Not AI-dependent | No |
| `DELETE /api/ai/sessions/{id}` | No AI call | Returns message | Not AI-dependent | No |
| `POST /api/ai/sessions/new` | No AI call | Returns session_id | Not AI-dependent | No |
| `GET /api/ai/quick/blending-suggestion` | No LLM call (DB only) | Returns coal stock data | Not AI-dependent | No |
| `GET /api/ai/quick/boiler-alerts` | No LLM call (DB only) | Returns alert list | Not AI-dependent | No |
| `GET /api/ai/quick/contract-status` | No LLM call (DB only) | Returns contract list | Not AI-dependent | No |
| `GET /api/ai/quick/logistics-losses` | No LLM call (DB only) | Returns losses list | Not AI-dependent | No |
| `GET /api/ai/quick/smart-stock` | No LLM call (DB only) | Returns stock summary | Not AI-dependent | No |
| `GET /api/ai/quick/coa-alerts` | No LLM call (DB only) | Returns COA alerts | Not AI-dependent | No |
| `POST /api/smart-blending/recommend` | Uses `LlmChat.send_message()` | Returns JSON-parsed blending rec | Yes — needs valid JSON str |

**Key finding:** Only TWO endpoints make actual LLM calls: `POST /api/ai/query` and `POST /api/smart-blending/recommend`. All `/api/ai/quick/*` endpoints are pure database aggregations — no LLM call. Phase 4 AI tests need to:
1. Test `POST /api/ai/query` with `FakeAIClient` returning a plain string.
2. Test `POST /api/smart-blending/recommend` with `FakeAIClient` returning the expected JSON structure.
3. Test all `GET /api/ai/quick/*` endpoints as regular DB-query tests (no AI stub needed).

### Streaming check
**No streaming responses.** The `LlmChat.send_message()` call is `await chat.send_message(UserMessage(text=...))` returning a plain `str`. No `StreamingResponse`, no async generator, no SSE. The `FakeAIClient.send_message()` is a simple `async def` returning a canned string. No complexity here.

### Smart Blending canned response
The `smart_blending/recommend` endpoint calls `json.loads(response)` on the AI output (server.py:3811-3828). The FakeAIClient must return valid JSON matching the schema from CONS-blending-ai-output:

```json
{
  "recommendation": [
    {
      "supplier": "PT TEST SUPPLIER",
      "source": "Vessel",
      "type": "LRC",
      "percentage": 100.0,
      "tonnage": 10000.0,
      "gcv": 4200,
      "ash": 5.0,
      "sulphur": 0.3,
      "total_moisture": 30.5,
      "inherent_moisture": 15.0,
      "volatile_matter": 35.0,
      "fixed_carbon": 25.0
    }
  ],
  "predicted_quality": {
    "gcv": 4200, "ash": 5.0, "sulphur": 0.3,
    "total_moisture": 30.5, "inherent_moisture": 15.0,
    "volatile_matter": 35.0, "fixed_carbon": 25.0
  },
  "meets_target": true,
  "reasoning": "Fake blending response for Phase 4 testing."
}
```

### Source citations
- `[VERIFIED: server.py:2619-2689]` — `ai_query` endpoint pattern.
- `[VERIFIED: server.py:2754-2982]` — All `quick/` endpoints are DB-only, no LLM calls.
- `[VERIFIED: server.py:3617-3843]` — `smart_blending/recommend` calls `LlmChat` + `json.loads`.
- `[VERIFIED: server.py:2666]` — `response = await chat.send_message(user_message)` returns plain `str`.

---

## Research Focus 8: Pagination Contract Assertion Helper

### What it is
TEST-03 requires asserting the `{items, total, page, page_size, total_pages}` shape on 7 list endpoints. A shared helper eliminates duplication.

### Recommended approach

```python
# backend/tests/helpers/pagination.py  — NEW FILE
def assert_pagination_shape(body: dict, expected_page: int = 1, expected_page_size: int = None):
    """
    Assert that `body` satisfies ADR-008 pagination envelope contract.
    Raises AssertionError with descriptive message on failure.
    """
    for key in ("items", "total", "page", "page_size", "total_pages"):
        assert key in body, f"Pagination envelope missing key '{key}': {body}"
    assert isinstance(body["items"], list), f"'items' must be a list, got {type(body['items'])}"
    assert isinstance(body["total"], int), f"'total' must be int, got {type(body['total'])}"
    assert body["total"] >= 0, f"'total' must be non-negative, got {body['total']}"
    assert body["page"] == expected_page, f"'page' expected {expected_page}, got {body['page']}"
    if expected_page_size is not None:
        assert body["page_size"] == expected_page_size
    # total_pages formula check
    if body["total"] == 0:
        assert body["total_pages"] == 0
    else:
        assert body["total_pages"] == ((body["total"] + body["page_size"] - 1) // body["page_size"]), \
            f"total_pages formula mismatch: total={body['total']}, page_size={body['page_size']}, got {body['total_pages']}"
```

**Location:** `backend/tests/helpers/pagination.py` with a corresponding `backend/tests/helpers/__init__.py`. Import in test files as `from tests.helpers.pagination import assert_pagination_shape`.

Alternatively, add to conftest.py if the helper count stays at one. The `tests/helpers/` package is the better choice for discoverability as Phase 7 adds more helpers.

### Usage in TEST-03 test file

```python
# backend/tests/test_pagination_contract.py
import requests, os
from tests.helpers.pagination import assert_pagination_shape

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8013").rstrip("/")

@pytest.mark.parametrize("path", [
    "/api/vessels",
    "/api/barges",
    "/api/trucking",
    "/api/biomassa",
    "/api/po-batubara",
    "/api/merit-order",
    "/api/coa-reconciliation",
])
def test_pagination_contract(path, admin_headers):
    r = requests.get(f"{BASE_URL}{path}?page=1&page_size=10", headers=admin_headers, timeout=10)
    assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"
    assert_pagination_shape(r.json(), expected_page=1, expected_page_size=10)
```

### Source citations
- `[VERIFIED: ADR-008-pagination-shape.md]` — envelope fields, formula, empty-result behavior.
- `[VERIFIED: server.py:716-722]` — canonical return shape from `get_vessels()`.

---

## Research Focus 9: Auth-Test Patterns for Token-Expired (TEST-02)

### What it is
TEST-02 requires testing the expired-token path without waiting for the actual 24-hour expiry. The solution is to mint a JWT with a past `exp` using the same secret.

### Recommended approach
**Already implemented.** `test_auth_session.py:111-140` contains `test_me_with_expired_token_returns_401()` which:
1. Reads `JWT_SECRET` from env (skips if not set).
2. Uses `jwt.encode()` from `PyJWT` (not `python-jose`) with `exp = datetime.now(timezone.utc) - timedelta(minutes=5)`.
3. Sends `GET /api/auth/me` with the forged expired token.
4. Asserts `r.status_code == 401`.

**Phase 4 action:** This test is already correct. The only action is to ensure `JWT_SECRET` is properly exported in the test environment (it is passed as an env var to the subprocess, and the conftest also exports it for the test process).

**CRITICAL: The backend at server.py:32** has `JWT_SECRET = os.environ.get('JWT_SECRET', '<JWT_SECRET_FALLBACK_REDACTED>')` — it has a hardcoded fallback default. If `JWT_SECRET` is not set in the environment, the backend uses the default, and a test that doesn't know this default will get a signature mismatch and receive a 401 for the wrong reason (invalid signature, not expired token). The conftest must ensure `JWT_SECRET` is set in both the subprocess env AND the test process env, sourced from `backend/.env`.

### PyJWT vs python-jose
`requirements.txt` has BOTH `PyJWT==2.10.1` (line 88) AND `python-jose==3.5.0` (line 94). The existing test (test_auth_session.py:18) imports `import jwt` which resolves to `PyJWT`. The server (server.py:16) also imports `import jwt` = PyJWT. Using PyJWT in tests is correct and consistent.

### Exact pattern

```python
# In test_auth_session.py (already exists and is correct)
import jwt
from datetime import datetime, timedelta, timezone

secret = os.environ.get("JWT_SECRET", "<JWT_SECRET_FALLBACK_REDACTED>")
algo = os.environ.get("JWT_ALGORITHM", "HS256")
payload = {
    "user_id": "expired-test-uuid",
    "email": "expired@example.com",
    "role": "viewer",
    "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
}
expired_token = jwt.encode(payload, secret, algorithm=algo)
```

### Source citations
- `[VERIFIED: backend/tests/test_auth_session.py:111-140]` — existing expired-token test is correct.
- `[VERIFIED: server.py:32]` — JWT_SECRET has hardcoded fallback default.
- `[VERIFIED: requirements.txt:88,94]` — both PyJWT and python-jose present; server and tests use PyJWT.

---

## Research Focus 10: Credential Sanitization (Hidden Phase 4 Obligation)

### What it is
CREDENTIAL_HYGIENE.md explicitly lists these files as containing inline `"<TEST_ADMIN_PASSWORD>"` literals exempted from the scanner with "TODO Phase 4 TEST-02":
- `backend/tests/test_dashboard_advanced.py` (lines 18, 28)
- `backend/tests/test_coa_reconciliation.py` (multiple call sites)
- `backend/tests/test_merit_order.py`
- `backend/tests/test_po_batubara.py`
- `test_reports/iteration_3.json` through `iteration_6.json`

Phase 4 MUST sanitize these before any plan is considered complete (TEST-02 cannot be marked done with the scanner exemption still in place).

### Sanitization pattern

Replace inline credential call sites:
```python
# BEFORE (forbidden)
response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "<TEST_ADMIN_EMAIL>",
    "password": "<TEST_ADMIN_PASSWORD>"
})

# AFTER (compliant)
def _login_as_admin(base_url: str) -> str:
    r = requests.post(f"{base_url}/api/auth/login", json={
        "email": os.environ.get("TEST_ADMIN_EMAIL", "<TEST_ADMIN_EMAIL>"),
        "password": _require_env("TEST_ADMIN_PASSWORD"),
    }, timeout=10)
    assert r.status_code == 200
    return r.json()["access_token"]
```

Note: `<TEST_ADMIN_EMAIL>` is explicitly documented as "not itself a credential" in CREDENTIAL_HYGIENE.md and may appear as a literal. Only `<TEST_ADMIN_PASSWORD>` is forbidden.

After sanitizing each file, remove the corresponding exemption entry from `scripts/check_credentials.sh` EXCLUDE array.

For the `test_reports/iteration_*.json` files: either remove them from version control or redact the `<TEST_ADMIN_PASSWORD>` occurrences and update the scanner exemption TODO.

### Source citations
- `[VERIFIED: CREDENTIAL_HYGIENE.md:85-93]` — explicit list of Phase 4 TODO files.
- `[VERIFIED: backend/tests/test_dashboard_advanced.py:18,28]` — `"<TEST_ADMIN_PASSWORD>"` literal confirmed.
- `[VERIFIED: backend/tests/test_coa_reconciliation.py:19,29,47]` — `"<TEST_ADMIN_PASSWORD>"` literal confirmed.

---

## Research Focus 11: Pitfalls / Landmines from server.py

### 11.1 Global `db` singleton
`db = client[os.environ['DB_NAME']]` (line 29) is a module-level global used by ALL async endpoint functions. If `MONGO_TEST_DB_NAME` is not set before the module is imported, `db` will point to `pltu_tenayan` for the entire subprocess lifetime. **The env var MUST be injected at subprocess spawn time, before any import.** This is guaranteed by setting it in the Popen `env` dict.

### 11.2 `ai_chat_collection = db.ai_chat_history` (line 2264)
The AI chat collection uses the module-level `db` reference. When `MONGO_TEST_DB_NAME` is set and `db` points to the test DB, `ai_chat_collection` will also point to the test DB — correctly. No special handling needed.

### 11.3 Smart Blending endpoint: synchronous JSON parse that raises on invalid JSON
`server.py:3811-3828`: `ai_result = json.loads(clean_response)` with a fallback to `{"error": ..., "raw_response": response}` on `json.JSONDecodeError`. The FakeAIClient's blending response MUST be valid JSON. Any test that calls `POST /api/smart-blending/recommend` with `FakeAIClient` returning non-JSON will get a 200 response with `{"error": "Failed to parse AI response"}` — not a test failure, but an incorrect assertion if the test checks `recommendation` field. Use the exact JSON structure from Research Focus 7.

### 11.4 COA reconciliation imports a service module
`server.py:3875`: `from services.coa_reconciliation import parse_coa_excel, merge_coa_data, calculate_kpis, ...`. This means the `services/` package must exist in the `backend/` directory. Tests that hit COA endpoints require this module to be importable. Not a blocker (the running subprocess has it), but if any test tries to import `server.py` directly (e.g., for TestClient), the `services/` package must be on the Python path.

### 11.5 `/api/dashboard/advanced` uses `dateutil.relativedelta` (line 1925)
`from dateutil.relativedelta import relativedelta` is a local import inside the handler. `python-dateutil` is in requirements (`python-dateutil==2.9.0.post0`), so this works. Dashboard tests will get valid data if the test DB has at least one vessel/barge/trucking/biomassa record.

### 11.6 Upload endpoints write to `db.<collection>` directly
Excel upload endpoints (`/api/upload/vessel`, etc.) call `await db.<collection>.insert_many(records)` directly. They have no mechanism to clean up test data after the upload test runs. This is handled by the per-session DB isolation: all data goes to `pltu_tenayan_test_<sessionid>` which is dropped at teardown.

### 11.7 Export endpoints (`/api/coa-reconciliation/export/excel` and `/export/pdf`)
These return `Response` objects with byte-stream content (not JSON). Tests for these endpoints must not call `.json()` — use `r.content` and check `r.status_code == 200` plus `r.headers["content-type"]`.

### 11.8 Existing test files hardcode `BASE_URL` fallbacks pointing to production
`test_coa_reconciliation.py:10`: `BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supply-chain-ai-40.preview.emergentagent.com')`. If `REACT_APP_BACKEND_URL` is not set, this will try to reach a production URL and fail. Phase 4 must ensure `REACT_APP_BACKEND_URL` is always set in the test environment (the conftest can do this via `os.environ.setdefault`).

### 11.9 `test_po_batubara.py` and `test_merit_order.py` may assert on production data counts
Read lines indicate they may check `data["total"] > 0`. In a fresh test DB with no seeded data, these would fail. Phase 4 must seed at least one record of each type into the test DB before the relevant test class runs.

### 11.10 The `cleanup_audit_probe_users` fixture in conftest
The existing `cleanup_audit_probe_users` fixture (conftest.py:71-93) runs against `db[DB_NAME]` — but it uses the module-level `DB_NAME` which is `os.environ.get("DB_NAME", "pltu_tenayan")`. After Phase 4's changes, this should use `TEST_DB_NAME` or be made conditional. If the test DB is isolated, audit-probe users would only exist if the factory inserts them — and it won't. This fixture becomes a no-op against the test DB, which is safe.

---

## Research Focus 12: Plan Decomposition Recommendation

### Proposed 4-Plan Structure

**Wave 1 (must complete before Wave 2 can start):**

**Plan 04-01: Infrastructure — conftest extension, AIClient Protocol, factories, fixtures, credential sanitization**
- Wave: 1
- Depends on: Phase 2 (conftest baseline), Phase 3 (server.py DB_NAME env var pattern)
- Requirements closed: TEST-01 (partially — infrastructure that enables it), TEST-02 (credential sanitization of existing tests)
- Files modified:
  - `backend/tests/conftest.py` — add `_backend_lifecycle`, `TEST_DB_NAME`, `_drop_test_db`
  - `backend/server.py` — add `MONGO_TEST_DB_NAME` override at startup (1 line); add `get_ai_client()` provider; add `AI_FAKE` check; refactor AI endpoint to use `Depends(get_ai_client)`
  - NEW `backend/app/ai/client.py` — `AIClient` Protocol
  - NEW `backend/app/ai/emergent_wrapper.py` — `EmergentLLMClientWrapper`
  - NEW `backend/tests/fakes/__init__.py`
  - NEW `backend/tests/fakes/ai_client.py` — `FakeAIClient`
  - NEW `backend/tests/factories/__init__.py`
  - NEW `backend/tests/factories/user.py`
  - NEW `backend/tests/factories/vessel.py`, `barge.py`, `trucking.py`, `biomassa.py`, `coa.py`
  - NEW `backend/tests/fixtures/excel/vessel_minimal.xlsx` (committed binary)
  - NEW `backend/tests/fixtures/excel/barge_minimal.xlsx`
  - NEW `backend/tests/fixtures/excel/trucking_minimal.xlsx`
  - NEW `backend/tests/fixtures/excel/biomassa_minimal.xlsx`
  - NEW `backend/tests/fixtures/excel/HEADER_VARIANTS.md`
  - NEW `backend/tests/helpers/__init__.py`
  - NEW `backend/tests/helpers/pagination.py`
  - NEW `scripts/generate_test_fixtures.py` (one-time generation script, committed)
  - MODIFIED `backend/tests/test_dashboard_advanced.py` — sanitize <TEST_ADMIN_PASSWORD> literals
  - MODIFIED `backend/tests/test_coa_reconciliation.py` — sanitize <TEST_ADMIN_PASSWORD> literals
  - MODIFIED `backend/tests/test_merit_order.py` — sanitize <TEST_ADMIN_PASSWORD> literals
  - MODIFIED `backend/tests/test_po_batubara.py` — sanitize <TEST_ADMIN_PASSWORD> literals
  - MODIFIED `scripts/check_credentials.sh` — remove exemptions for the 4 sanitized files
  - MODIFIED `backend/.venv/` — none; all deps already present

**Wave 2 (can run in parallel, depend only on Wave 1 output):**

**Plan 04-02: Auth + Pagination tests**
- Wave: 2
- Depends on: Plan 04-01
- Requirements closed: TEST-02 (complete), TEST-03
- Files modified:
  - `backend/tests/conftest.py` — possibly add seeding fixtures for pagination test data
  - NEW `backend/tests/test_pagination_contract.py` — 7 list endpoints × pagination shape
  - `backend/tests/test_auth_session.py` — verify existing 5 tests still pass; add any missing paths (check against AUTH_CONTRACT.md)

**Plan 04-03: Excel upload + COA tests**
- Wave: 2
- Depends on: Plan 04-01
- Requirements closed: TEST-04, TEST-05
- Files modified:
  - NEW `backend/tests/test_excel_upload.py` — vessel/barge/trucking/biomassa upload + round-trip assertion
  - NEW `backend/tests/test_coa_reconciliation_phase4.py` — KPI/trend/supplier-consistency/export happy-path

**Plan 04-04: AI endpoints + Dashboard + TEST-01 integration verification**
- Wave: 2
- Depends on: Plan 04-01
- Requirements closed: TEST-06, TEST-07, TEST-01 (the "exits zero" gate)
- Files modified:
  - NEW `backend/tests/test_ai_endpoints.py` — `POST /ai/query` mocked, all `GET /ai/quick/*` endpoints, `POST /smart-blending/recommend` with FakeAIClient JSON response, session CRUD
  - NEW `backend/tests/test_dashboard.py` — `/stats` and `/advanced` happy path
  - DOCUMENTATION: `backend/tests/TEST-RUNNER.md` — documents `pytest backend/tests -q` command, required env vars, and how to source them from `memory/test_credentials.md`

### Why 4 plans (not 3 or 6)
- Wave 1 is inherently a single plan: all infrastructure changes must land atomically before test files can be written against them.
- Wave 2's 3 plans are independent of each other (no shared files) and logically cluster by domain: (auth+pagination), (upload+COA), (AI+dashboard).
- 4 plans allows the planner to verify Wave 1 is green before proceeding to Wave 2, which is appropriate given the blast radius of the server.py changes.

---

## Research Focus 13: Anti-Patterns to Avoid

1. **Test interdependency:** Each test function must be independently runnable. Never assume that `test_A` runs before `test_B` in the same file. Factories seed data at fixture scope, not at module scope.

2. **Inline credentials:** Confirmed forbidden by CREDENTIAL_HYGIENE.md. `_require_env()` is the pattern. The `<TEST_ADMIN_PASSWORD>` literal is the specific danger (scanner pattern).

3. **Mocking at the wrong boundary:** The AI stub is at the `get_ai_client()` provider boundary (the FastAPI `Depends()` point), not at `LlmChat.send_message` directly. Don't mock internal LlmChat methods; mock the boundary that FastAPI injects.

4. **Time-based assertions:** The dashboard `/advanced` endpoint uses `dateutil.relativedelta` to calculate 6 months ago. Test data seeded with dates inside the last 6 months will appear in results; data seeded with dates older than 6 months may not. Always use dates within the last 6 months for seeded test data.

5. **Overlapping fixture scopes:** The `_backend_lifecycle` is session-scoped. DB seed fixtures for specific test classes should be function-scoped or module-scoped, not session-scoped, to avoid data pollution between test classes.

6. **Assertion on production data counts:** Test assertions on `total > 0` must be preceded by factory seeding. Never rely on the test DB having pre-existing data.

7. **No test-execution-order dependencies:** pytest does not guarantee execution order across files. Use autouse fixtures with the appropriate scope for setup/teardown.

8. **Upload cleanup:** After `test_excel_upload.py` inserts records, they persist in the test DB for the duration of the session. This is intentional — the test DB is isolated and dropped at session end. Do NOT add cleanup logic after upload tests; it creates interdependency with pagination tests that might run after and see 0 records.

9. **COA export endpoints return bytes, not JSON:** `GET /api/coa-reconciliation/export/excel` returns a binary xlsx file. Call `r.content` not `r.json()`.

10. **Smart blending endpoint requires existing data:** `POST /api/smart-blending/recommend` queries `db.vessels`, `db.barges`, `db.trucking`, and `db.smartstock` to build the AI prompt. If these collections are empty in the test DB, the endpoint calls `FakeAIClient` with an empty context, which still returns the canned blending response — but if any code path checks `if not coal_inventory` before calling the AI, it may return early. Check server.py:3663-3788 for such guards. Factory seeding of at least one vessel record before the smart blending test is required.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None detected — planner to create `backend/pytest.ini` or `pltu-tenayan-full-backup/pytest.ini` |
| Quick run command | `pytest backend/tests -q --tb=short -x` |
| Full suite command | `pytest backend/tests -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | `pytest backend/tests -q` exits zero | Integration (run all) | `pytest backend/tests -q` | ❌ Wave 1 (conftest extension) |
| TEST-02 | Auth: login success/failure/role-denied/token-expired/me-rehydrate | Integration | `pytest backend/tests/test_auth_session.py backend/tests/test_auth_roles.py -v` | ✅ (need credential sanitization) |
| TEST-03 | Pagination shape on 7 list endpoints | Integration | `pytest backend/tests/test_pagination_contract.py -v` | ❌ Wave 2 |
| TEST-04 | Excel upload round-trip per receipt mode | Integration | `pytest backend/tests/test_excel_upload.py -v` | ❌ Wave 2 |
| TEST-05 | COA KPI/trend/supplier-consistency/export | Integration | `pytest backend/tests/test_coa_reconciliation_phase4.py -v` | ❌ Wave 2 |
| TEST-06 | AI endpoints with FakeAIClient | Integration | `pytest backend/tests/test_ai_endpoints.py -v` | ❌ Wave 2 |
| TEST-07 | Dashboard /stats and /advanced happy-path | Integration | `pytest backend/tests/test_dashboard.py -v` | ❌ Wave 2 |

### Validation Surfaces

| Surface | What it validates | Maps to |
|---------|-------------------|---------|
| **Request shape** | HTTP status code 400 for malformed body on auth endpoints | TEST-02 (CONS-auth-header) |
| **Response shape** | Pagination envelope, response fields presence | TEST-03 (ADR-008) |
| **Role enforcement** | 403 for wrong-role requests | TEST-02 (CONS-auth-header) |
| **Persistence round-trip** | Uploaded xlsx row appears in GET list response | TEST-04 |
| **Error code correctness** | 401 for expired/invalid token, 403 for missing token | TEST-02 |
| **Mock shape correctness** | FakeAIClient returns valid JSON for smart blending; valid str for ai/query | TEST-06 |
| **Aggregate correctness** | COA KPI endpoint returns expected fields; dashboard stats are non-null | TEST-05, TEST-07 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_auth_session.py -q` (quick smoke, <3s)
- **Per wave merge:** `pytest backend/tests -q` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/pytest.ini` — test discovery root config (or `pyproject.toml [tool.pytest.ini_options]`)
- [ ] `backend/tests/helpers/__init__.py` — helpers package init
- [ ] `backend/tests/helpers/pagination.py` — shared assertion helper
- [ ] `backend/tests/factories/__init__.py` — factories package init
- [ ] `backend/tests/fakes/__init__.py` — fakes package init
- [ ] `backend/app/__init__.py` — app package init (if `app/ai/client.py` is new sub-package)
- [ ] `backend/app/ai/__init__.py` — ai sub-package init

---

## Security Domain

### Applicable ASVS Categories (Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | JWT via PyJWT; test suite exercises 401/403 paths |
| V3 Session Management | Yes | JWT expiry enforced; test forges expired token |
| V4 Access Control | Yes | role check via `require_role()`; test exercises viewer-403 |
| V5 Input Validation | Yes | Upload tests send malformed xlsx; expect 400 not 500 |
| V6 Cryptography | Yes | bcrypt for passwords (already in production); do NOT hand-roll |

### Phase 4 Test-Specific Security Requirements
- No credentials committed to test files (CREDENTIAL_HYGIENE.md gate enforced by pre-commit hook)
- `FakeAIClient` must NOT make external HTTP calls (no network egress from tests)
- Test DB name must start with `pltu_tenayan_test_` (failsafe in drop logic)
- JWT secret must be sourced from env, never hardcoded in test files (existing `test_auth_session.py` is compliant; the default fallback in server.py is acceptable for local dev but the test should prefer the real secret from `.env`)

---

## Open Questions (RESOLVED 2026-05-11)

All five questions resolved during plan-checker revision pass:

1. **`pytest.ini` placement: RESOLVED — `pltu-tenayan-full-backup/backend/pytest.ini`.** Plan 04-01 places it in the inner directory with `testpaths = tests`. The canonical command `pytest backend/tests -q` runs from `pltu-tenayan-full-backup/` and pytest discovers `backend/pytest.ini` via standard rootdir detection.

2. **`EMERGENT_LLM_KEY` graceful handling under `AI_FAKE=1`: RESOLVED — `get_ai_client()` short-circuits BEFORE any `EMERGENT_LLM_KEY` read.** Plan 04-01 Task 1 wires `get_ai_client()` to check `AI_FAKE` first and return `FakeAIClient()` immediately, never touching `EMERGENT_LLM_KEY`. The two LLM endpoints' inline `api_key = os.environ.get("EMERGENT_LLM_KEY")` reads are moved into the `EmergentLLMClientWrapper` constructor (only instantiated on the production path), so the test subprocess never reads the env var.

3. **`test_po_batubara.py` and `test_merit_order.py` assertions against empty test DB: RESOLVED — A4 partially confirmed. test_po_batubara.py is SAFE (every assertion guarded `if len(data) > 0`); test_merit_order.py is NOT SAFE (`assert len(data) > 0` at line 71 and `assert len(data) >= 1` at line 314 fail against empty DB).** Plan 04-01 Task 3 adds a session-scoped `_seed_baseline_data` fixture that inserts ≥3 deterministic merit_order documents into the test DB at session start using the merit_order factory. This unblocks the existing test_merit_order.py without modifying its assertions. test_po_batubara.py needs no seeding.

4. **Two-repo commit boundary: RESOLVED — same protocol as Phases 1-3.** Backend changes (server.py, conftest.py, new test files, xlsx fixtures) commit to `pltu-tenayan-full-backup/` inner repo. Planning docs (SUMMARY.md, STATE.md, ROADMAP.md updates) commit to outer repo. Each plan's `files_modified` makes the boundary explicit per file path.

5. **`test_coa_reconciliation.py` line 10 fallback URL: RESOLVED — fixed in Plan 04-01.** The hardcoded `'https://supply-chain-ai-40.preview.emergentagent.com'` fallback is replaced with `'http://localhost:18013'` (matching `PHASE4_TEST_PORT`) during the credential sanitization pass (Plan 04-01 Task 3). Listed in Plan 04-01 `files_modified` and called out in the Task 3 action.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `app.dependency_overrides` does not propagate across process boundaries | Focus 1 | If wrong: override pattern would work without AI_FAKE env var; test architecture would be simpler but effectively the same |
| A2 | subprocess env injection with `AI_FAKE=1` is the correct approach for subprocess-based backends | Focus 1 | If wrong: need alternative AI stubbing mechanism; likely a test-mode config file read at startup |
| A3 | uuid4 hex prefix is sufficient uniqueness for per-session DB names | Focus 4 | If wrong: test DB collision possible; mitigated by adding PID prefix |
| A4 | Both test_po_batubara.py and test_merit_order.py require seeded data to pass assertions | Focus 11 | If wrong: tests pass against empty DB; no change needed to factories |

---

## Sources

### Primary (HIGH confidence)
- `[VERIFIED: server.py]` — Complete read of all AI endpoints, upload parsers, pagination patterns, DB startup, health endpoint
- `[VERIFIED: conftest.py]` — Existing 93-line conftest fully read
- `[VERIFIED: test_auth_session.py]` — Existing expired-token test pattern confirmed
- `[VERIFIED: test_auth_roles.py]` — Role enforcement test pattern confirmed
- `[VERIFIED: test_dashboard_advanced.py]` — Inline credential confirmed at lines 18, 28
- `[VERIFIED: test_coa_reconciliation.py]` — Inline credentials + hardcoded URL confirmed
- `[VERIFIED: CREDENTIAL_HYGIENE.md]` — Phase 4 TODO list confirmed
- `[VERIFIED: requirements.txt]` — openpyxl, pytest, PyJWT, python-jose, pymongo all present
- `[VERIFIED: ADR-008-pagination-shape.md]` — Pagination contract fields and formula locked
- `[VERIFIED: constraints.md]` — CONS-auth-header, CONS-pagination-shape locked contracts

### Secondary (MEDIUM confidence)
- `[CITED: FastAPI Testing Dependencies]` — https://fastapi.tiangolo.com/advanced/testing-dependencies/
- `[CITED: FastAPI Testing]` — https://fastapi.tiangolo.com/tutorial/testing/

### Tertiary (LOW confidence)
- `[ASSUMED]` — Subprocess env injection is the correct AI stub mechanism for subprocess-based test suites
- `[ASSUMED]` — Protocol structural typing is preferable to ABC for wrapping third-party classes

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libs in requirements.txt, all patterns in existing test files
- Architecture: HIGH — server.py fully read, all AI endpoints and upload parsers inventoried
- Pitfalls: HIGH — specific line numbers cited for all landmines

**Research date:** 2026-05-11
**Valid until:** 2026-06-11 (stable backend; no LLM migration until Phase AI-Provider)
