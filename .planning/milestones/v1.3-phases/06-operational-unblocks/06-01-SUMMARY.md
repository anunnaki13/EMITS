---
phase: 06
plan: 01
subsystem: ai-provider
tags: [openrouter, llm, provider-migration, retry-backoff, env-vars]
dependency_graph:
  requires: []
  provides: [openrouter-client, llm-unavailable-503, openrouter-env-vars]
  affects: [server.py, app/ai/client.py, requirements.txt, 8-doc-files]
tech_stack:
  added: [httpx-async-client]
  patterns: [retry-with-backoff, fastapi-exception-handler, ai-client-protocol]
key_files:
  created:
    - pltu-tenayan-full-backup/backend/app/ai/openrouter_client.py
    - pltu-tenayan-full-backup/backend/tests/test_openrouter_client.py
    - pltu-tenayan-full-backup/backend/.env.example
  modified:
    - pltu-tenayan-full-backup/backend/app/ai/client.py
    - pltu-tenayan-full-backup/backend/server.py
    - pltu-tenayan-full-backup/backend/requirements.txt
    - pltu-tenayan-full-backup/backend/.env
    - pltu-tenayan-full-backup/LOCAL_SETUP.md
    - pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md
    - pltu-tenayan-full-backup/documentation.md
    - pltu-tenayan-full-backup/readme.md
    - pltu-tenayan-full-backup/frontend/public/docs/DEPLOYMENT_GUIDE.md
    - pltu-tenayan-full-backup/frontend/public/docs/documentation.md
    - pltu-tenayan-full-backup/frontend/public/docs/readme.md
decisions:
  - "OpenRouterClient uses httpx.AsyncClient per-call (stateless), 3-retry
     1s/2s/4s backoff for {429, 500, 502, 503}; 401/402 raise immediately"
  - "D-04 LOCKED: OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini hardcoded as
     default throughout; operator overrides via .env"
  - "LLMUnavailableError surfaces Indonesian copy verbatim (D-09); API key
     never appears in exception messages (T-06-01-01 mitigated)"
  - "test_clean_checkout_gate failure confirmed pre-existing (pre-Phase-6);
     deferred to separate remediation plan"
metrics:
  duration: "~12 min"
  completed_date: "2026-05-11"
  tasks: 3
  files_created: 3
  files_modified: 11
---

# Phase 6 Plan 01: OpenRouter Backend Integration Summary

One-liner: Migrated LLM provider from emergentintegrations/Gemini to OpenRouter via httpx with 3-retry backoff, HTTP 503 Indonesian error mapping, and full env-var + doc rename.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 06-01-01 | OpenRouterClient + tests | 3f84aa8 | openrouter_client.py, test_openrouter_client.py, client.py |
| 06-01-02 | Exception handler + server.py cleanup | 2280d1e | server.py |
| 06-01-03 | Env-var rename + requirements + 8 docs | 2957340 | requirements.txt, .env, .env.example, 7 .md files |

## Emergentintegrations Removal Audit

| File | Line | Action |
|------|------|--------|
| server.py | 19 | Removed `from emergentintegrations.llm.chat import LlmChat, UserMessage` |
| server.py | 2273 | Removed second `from emergentintegrations.llm.chat import LlmChat, UserMessage` |
| requirements.txt | 21 | Removed `emergentintegrations==0.1.0` |
| app/ai/emergent_wrapper.py | (kept as file; no longer imported) | EmergentLLMClientWrapper still exists on disk but is unreachable — no plan deletes it (safe carry-forward) |

Grep gate: `grep -c "from emergentintegrations" server.py` == **0** (both sites clean).

## Factory Update Diff

Old `client.py` factory:
```python
from app.ai.emergent_wrapper import EmergentLLMClientWrapper
return EmergentLLMClientWrapper(api_key=os.environ.get("EMERGENT_LLM_KEY", ""))
```

New `client.py` factory:
```python
from app.ai.openrouter_client import OpenRouterClient
return OpenRouterClient(
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    model=os.environ.get("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini"),
)
```
AI_FAKE=1 branch preserved verbatim.

## Env-var Rename Audit

| File | Occurrences replaced |
|------|---------------------|
| backend/.env | 1 (value cleared for operator rotation) |
| LOCAL_SETUP.md | 2 |
| DEPLOYMENT_GUIDE.md | 4 |
| documentation.md | 2 |
| readme.md | 1 |
| frontend/public/docs/DEPLOYMENT_GUIDE.md | 4 |
| frontend/public/docs/documentation.md | 2 |
| frontend/public/docs/readme.md | 1 |

Total: 17 replacements across 8 files. Grep gate: 0 residual `EMERGENT_LLM_KEY` in inner-repo markdown.

## Test Run Output

```
# Task 06-01-01 (unit tests):
4 passed in 9.02s

# Task 06-01-02 regression (test_openrouter_client + test_ai_endpoints):
5 passed, 8 skipped in 3.50s  (skips = credential-guarded, expected)

# D-14 full suite (excluding pre-existing collection errors):
27 passed, 43 skipped, 1 pre-existing failure (test_clean_checkout_gate)
```

## Deviations from Plan

### Pre-existing Issue (Deferred, Out-of-Scope)

**test_clean_checkout_gate::test_pytest_collect_only_succeeds**
- **Found during:** Task 06-01-03 D-14 regression check
- **Root cause:** 4 test files (`test_coa_reconciliation.py`, `test_dashboard_advanced.py`, `test_merit_order.py`, `test_po_batubara.py`) use `pytest.skip()` at module level instead of `pytest.mark.skip` decorator — causes collection error with pytest >=9.x
- **Confirmed pre-existing:** Stash-rollback test showed same failure on commit 4c7d526 (pre-Phase-6)
- **Action:** Logged as deferred item; no change made (out of scope per deviation scope boundary rule)

None — all plan instructions executed exactly as written.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes introduced. The `openrouter_client.py` outbound HTTPS to openrouter.ai is the documented trust boundary in plan's threat model (T-06-01-01 mitigated: api_key never logged; T-06-01-02 mitigated: 503 handler + retry backoff).

## Self-Check: PASSED

- [x] `pltu-tenayan-full-backup/backend/app/ai/openrouter_client.py` exists
- [x] `pltu-tenayan-full-backup/backend/tests/test_openrouter_client.py` exists (4 tests)
- [x] `pltu-tenayan-full-backup/backend/.env.example` exists
- [x] Inner repo commits exist: 3f84aa8, 2280d1e, 2957340
- [x] `grep -c "from emergentintegrations" server.py` == 0
- [x] `grep -c "EMERGENT_LLM_KEY" backend/.env` == 0
- [x] `grep -c "OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini" backend/.env` == 1
