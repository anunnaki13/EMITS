# Phase-4 Test Suite Runner

**Canonical command:** `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q`

## One-time setup

Test credentials live in `pltu-tenayan-full-backup/memory/test_credentials.md` (gitignored).
Source them before running pytest:

```bash
cd pltu-tenayan-full-backup
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_OPERATOR_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | sed -n '2p' | awk '{print $3}')"
export TEST_OPERATOR_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | sed -n '2p' | awk '{print $3}')"
export TEST_VIEWER_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | sed -n '3p' | awk '{print $3}')"
export TEST_VIEWER_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | sed -n '3p' | awk '{print $3}')"
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="pltu_tenayan"
export JWT_SECRET="$(grep '^JWT_SECRET=' backend/.env | cut -d= -f2-)"
```

## Run the suite

```bash
cd pltu-tenayan-full-backup/backend
.venv/bin/pytest tests/ -q
```

Expected: all tests green, ~30-60 s wall-clock, exit 0.

## Important: Phase-4 spawns its OWN backend on port 18013

The session-scoped `_backend_lifecycle` fixture in `tests/conftest.py`
spawns `uvicorn server:app --host 127.0.0.1 --port 18013` with:
- `AI_FAKE=1` (FakeAIClient stub, no LLM budget consumed)
- `MONGO_TEST_DB_NAME=pltu_tenayan_test_<sessionid>` (isolated test DB, dropped at teardown)

The live production backend on port 8013 is NEVER touched. If port 18013
is in use, set `PHASE4_TEST_PORT` env var to another free port before
running pytest.

## Skip destructive tests (default)

Destructive tests (delete-all role gates) are gated by
`RUN_DESTRUCTIVE_TESTS=1`. The default invocation skips them. To
include them:

```bash
RUN_DESTRUCTIVE_TESTS=1 .venv/bin/pytest tests/ -q
```

## Troubleshooting

- **`tests/.backend.pid` exists but backend is dead** → unlink the file and re-run.
- **Port 18013 in use** → `lsof -i :18013` to find the owner; kill or set `PHASE4_TEST_PORT`.
- **Tests skipped: "TEST_ADMIN_PASSWORD is required"** → source env vars per "One-time setup" above.
- **`/api/health` 30 s timeout** → check `/tmp/emits-test-server.log` for uvicorn startup errors.
- **`pltu_tenayan_test_*` databases linger in mongod** → manual drop:
  `mongo --eval "db.adminCommand({listDatabases:1}).databases.filter(d=>d.name.startsWith('pltu_tenayan_test_')).forEach(d=>db.getSiblingDB(d.name).dropDatabase())"`

## What the suite covers (Phase 4 close-out)

- TEST-01: structural acceptance gate (test_clean_checkout_gate.py)
- TEST-02: auth (test_auth_session.py + test_auth_roles.py)
- TEST-03: pagination (test_pagination_shape.py)
- TEST-04: Excel upload (test_upload_excel.py + xlsx fixtures)
- TEST-05: COA reconciliation (test_coa_reconciliation.py)
- TEST-06: AI mocked (test_ai_endpoints.py)
- TEST-07: dashboard (test_dashboard_advanced.py)

See `.planning/phases/04-test-suite-stabilization/` for plan-level details.
