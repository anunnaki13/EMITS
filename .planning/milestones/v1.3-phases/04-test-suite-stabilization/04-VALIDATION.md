---
phase: 04
slug: test-suite-stabilization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-11
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 04-RESEARCH.md §"Validation Architecture (Nyquist Dimension 8)".

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (already installed in `pltu-tenayan-full-backup/backend/.venv`) |
| **Config file** | `pltu-tenayan-full-backup/backend/pytest.ini` (Wave-1 deliverable; Plan 04-01) |
| **Quick run command** | `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q -m "not destructive"` |
| **Full suite command** | `cd pltu-tenayan-full-backup/backend && RUN_DESTRUCTIVE_TESTS=1 .venv/bin/pytest tests/ -q` |
| **Estimated runtime** | quick: ~30 s · full: ~60 s (target — must beat the 90 s budget so feedback stays warm) |

---

## Sampling Rate

- **After every task commit:** Run quick command (skip-destructive). If a task touches conftest, factories, or fixtures, run the affected domain test file alone first (`pytest tests/test_<domain>.py -q`).
- **After every plan wave:** Run full suite command.
- **Before `/gsd-verify-work`:** Full suite must be green AND `pytest backend/tests -q` from a clean checkout (no env vars exported beyond `memory/test_credentials.md` source) must exit 0 — TEST-01 acceptance gate.
- **Max feedback latency:** 90 s.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | TEST-01 (infra) | — | Conftest spawns/reuses uvicorn; teardown drops test DB; PID file cleanup | integration | `pytest tests/test_conftest_lifecycle.py -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | TEST-01 / TEST-06 | — | server.py reads MONGO_TEST_DB_NAME override; AI_FAKE=1 env var swaps to FakeAIClient | integration | `MONGO_TEST_DB_NAME=pltu_tenayan_test_probe AI_FAKE=1 python -c "from server import db; print(db.name)"` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | TEST-04 (fixtures) | — | 4 sanitized synthetic xlsx exist + parse-able by openpyxl | unit | `pytest tests/fixtures/excel/test_fixtures_valid.py -q` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | STAB-03 tail | T-cred-leak-01 / mitigated | No inline `<TEST_ADMIN_PASSWORD>` in test files; CREDENTIAL_HYGIENE.md exemptions removed | static | `bash scripts/check_credentials.sh` | ✅ | ⬜ pending |
| 04-02-01 | 02 | 2 | TEST-02 | T-auth-bypass-01 | Login success returns access_token; failure returns 401 with CONS-auth-header semantics | integration | `pytest tests/test_auth_session.py tests/test_auth_roles.py -q` | ✅ | ⬜ pending |
| 04-02-02 | 02 | 2 | TEST-02 (token-expired) | T-token-replay-01 | Expired JWT (past `exp`) rejected with 401 by `/api/auth/me` | integration | `pytest tests/test_auth_session.py::test_expired_token -q` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 2 | TEST-03 | — | Pagination shape `{items,total,page,page_size,total_pages}` asserted on 7 list endpoints (vessels/barges/trucking/biomassa/po-batubara/merit-order/coa-reconciliation) | integration | `pytest tests/test_pagination_shape.py -q` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | TEST-04 | T-upload-traverse-01 | Excel upload happy-path returns 200/201 + a deterministic row round-trips into the canonical MongoDB collection | integration | `pytest tests/test_upload_excel.py -q` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 2 | TEST-05 | — | COA reconciliation KPI / trend / supplier-consistency / export each return 200 with the documented response shape | integration | `pytest tests/test_coa_reconciliation.py -q` | ✅ | ⬜ pending |
| 04-04-01 | 04 | 2 | TEST-06 | T-llm-budget-leak-01 / mitigated | `/api/ai/query` and `/api/smart-blending/recommend` return canned shapes via FakeAIClient (AI_FAKE=1); ZERO outbound LLM calls observed in run | integration | `AI_FAKE=1 pytest tests/test_ai_endpoints.py -q && grep -c 'legacy-ai.*api' tests/.run.log == 0` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 2 | TEST-07 | — | `/api/dashboard/stats` and `/api/dashboard/advanced` happy-path each return 200 + documented shape | integration | `pytest tests/test_dashboard_advanced.py::test_stats tests/test_dashboard_advanced.py::test_advanced -q` | ✅ | ⬜ pending |
| 04-04-03 | 04 | 2 | TEST-01 (structural gate) | — | `test_clean_checkout_gate.py` runs `pytest --collect-only -q` in subprocess (no import errors) + verifies 4 phase-4 test files exist non-empty | structural | `pytest tests/test_clean_checkout_gate.py -q` | ❌ W0 | ⬜ pending |
| 04-04-03b | 04 | 2 | TEST-01 (literal SC-1 — operator-verified) | — | `pytest backend/tests -q` from clean checkout exits 0 (operator runs per tests/TEST-RUNNER.md procedure) | manual | (see Manual-Only Verifications below) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 = the prerequisite scaffolding installed by Plan 04-01 BEFORE any per-domain test is written. Plans 04-02..04-04 cannot start until 04-01 lands.

- [ ] `pltu-tenayan-full-backup/backend/pytest.ini` — pytest config (markers, paths, asyncio mode if needed)
- [ ] `pltu-tenayan-full-backup/backend/tests/conftest.py` — extended with `_backend_lifecycle`, `_test_db_lifecycle`, `_ai_fake_env` session-scoped fixtures (extends, does not replace, the existing 93-line file)
- [ ] `pltu-tenayan-full-backup/backend/tests/factories/` — factories for vessel/barge/trucking/biomassa/po_batubara/merit_order/coa/user
- [ ] `pltu-tenayan-full-backup/backend/tests/fakes/ai_client.py` — `FakeAIClient` returning canned response shapes per endpoint
- [ ] `pltu-tenayan-full-backup/backend/app/ai/client.py` (or equivalent) — `AIClient` Protocol + `get_ai_client()` provider that branches on `AI_FAKE=1` env var
- [ ] `pltu-tenayan-full-backup/backend/server.py` — 1-line patch: `_db_name = os.environ.get("MONGO_TEST_DB_NAME") or os.environ['DB_NAME']`
- [ ] `pltu-tenayan-full-backup/backend/tests/fixtures/excel/{vessel,barge,trucking,biomassa}_minimal.xlsx` — 4 sanitized synthetic xlsx files (≤15 KB each)
- [ ] `pltu-tenayan-full-backup/backend/tests/fixtures/excel/HEADER_VARIANTS.md` — note pointing to Phase 6 OPS-02 for header-variant edge cases
- [ ] `pltu-tenayan-full-backup/backend/tests/helpers/pagination.py` — `assert_pagination_shape(resp_json)` per ADR-008
- [ ] `pltu-tenayan-full-backup/backend/tests/helpers/jwt.py` — `mint_expired_token(secret)` using the same library `server.py` uses
- [ ] STAB-03 credential sanitization — remove `<TEST_ADMIN_PASSWORD>` literals from existing tests; remove their entries from CREDENTIAL_HYGIENE.md exemptions

*Existing infrastructure that Wave 0 builds on (do NOT replace):*
- `pltu-tenayan-full-backup/backend/tests/conftest.py` 93 lines (Phase-2 plan 02-02)
- `pltu-tenayan-full-backup/backend/tests/test_auth_session.py` (Phase-2 plan 02-02)
- `pltu-tenayan-full-backup/backend/tests/test_auth_roles.py` (Phase-2 plan 02-03)
- `pltu-tenayan-full-backup/backend/tests/test_coa_reconciliation.py`, `test_dashboard_advanced.py`, `test_merit_order.py`, `test_po_batubara.py` (Phase-1/2 carry-forward; preserve verbatim, only ADD new tests)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator-runbook adherence (LOCAL_SETUP §VPS Service Recovery) | TEST-01 (operator UX) | Documentation accuracy is humans-only | Run `pytest backend/tests -q` step-by-step from the runbook on a fresh shell; confirm exit 0 and no surprises |
| Literal SC-1 — `pytest backend/tests -q exit 0` from clean checkout | TEST-01 (literal acceptance bar) | Recursive in-suite pytest invocation has reentrancy / lifecycle-fixture re-spawn risk; operator-verified is more reliable than nested-pytest automation | Operator follows tests/TEST-RUNNER.md: source env vars from `memory/test_credentials.md`, ensure mongod running, ensure `:8013` is free OR set `PHASE4_TEST_PORT` to a free port, run `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q`, confirm exit 0 |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (verified — every task above is verifiable)
- [ ] Wave 0 covers all MISSING references (10 items in §Wave 0 Requirements)
- [ ] No watch-mode flags (every command above is one-shot)
- [ ] Feedback latency < 90 s
- [ ] `nyquist_compliant: true` set in frontmatter (flip after planner produces PLAN.md files that satisfy §Per-Task Verification Map)

**Approval:** pending
