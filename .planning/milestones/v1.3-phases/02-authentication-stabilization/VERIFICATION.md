---
phase: 02-authentication-stabilization
verified: 2026-05-10T14:05:13Z
status: human_needed
score: 5/5 must-haves verified (with soft-spots requiring decisions)
overrides_applied: 0
authfix_verdicts:
  AUTHFIX-01: CLOSED
  AUTHFIX-02: CLOSED
  AUTHFIX-03: CLOSED (with intent-deviation noted: ROADMAP "operator-only upload" verified as "operator+admin upload + viewer-blocked")
  AUTHFIX-04: SOFT (mitigated; operator playbook re-test deferred; suppressor uncommitted)
  AUTHFIX-05: CLOSED
test_runs:
  - command: "pytest backend/tests/test_auth_session.py -v"
    db: "live pltu_tenayan @ http://localhost:8013"
    exit_code: 0
    result: "5 passed in 0.98s"
  - command: "pytest backend/tests/test_auth_session.py backend/tests/test_auth_roles.py -v"
    db: "isolated pltu_tenayan_test_verify @ http://127.0.0.1:8113 (uvicorn spun + torn down by verifier)"
    exit_code: 0
    result: "16 passed, 1 skipped in 2.37s (1 destructive admin-DELETE-vessels test skipped by design)"
  - command: "bash scripts/check_credentials.sh"
    exit_code: 0
    result: "OK: no tracked credential patterns found in 169 files (after 16 exemptions)"
  - command: "bash .git/hooks/pre-commit"
    exit_code: 0
    result: "OK: chained hook (large-file guard + scanner) exits clean"
soft_spots:
  - id: SS-01
    severity: warning
    item: "AUTHFIX-04 mitigation (frontend/public/index.html ResizeObserver suppressor) is uncommitted in inner repo"
    evidence: "git -C pltu-tenayan-full-backup log --all -- frontend/public/index.html shows only auto-commit ancestors; HEAD:frontend/public/index.html does NOT contain the RO_RE suppressor; the suppressor exists only as a working-tree modification"
    impact: "If the inner repo working tree is reset / checked out clean, the AUTHFIX-04 mitigation disappears. The plan SUMMARYs claim the file is 'unchanged byte-for-byte from LOGIN_BUG.md verbatim quote' — the file content matches, but the bytes live in the working tree, not in git history."
    recommendation: "Commit frontend/public/index.html to lock in the mitigation, OR explicitly document in LOGIN_BUG_RESOLUTION.md that the suppressor is local-only and must be re-applied if the inner tree is reset."
  - id: SS-02
    severity: warning
    item: "AUTHFIX-04 closed without operator browser-capture; closure relied on operator-by-proceed authorization (\"lanjut\")"
    evidence: "LOGIN_BUG_RESOLUTION.md line 13-24 explicitly documents that the operator playbook re-test was deferred. Closure rationale rests on (a) backend health, (b) the contract-layer regression test, (c) unchanged suppressor. The SUMMARY 02-04-SUMMARY.md is honest about this; not hidden."
    impact: "AUTHFIX-04 truth #1 (operator has re-run AUDIT-04 repro) is FAILED at the literal level. Truth #5 (LOGIN_BUG_RESOLUTION.md exists and cites disposition + regression test) is VERIFIED. The deferral is documented honestly, but the human checkpoint specified in plan 02-04 Task 1 was not executed."
    recommendation: "Project owner should accept the deferral as-is (already implicitly accepted via 'lanjut' on 2026-05-10) and explicitly close the gap during Phase-3 DOCS-01 work, OR run the operator playbook now and append the capture to LOGIN_BUG_RESOLUTION.md."
  - id: SS-03
    severity: warning
    item: "ROADMAP \"operator-only upload\" was substituted with \"admin+operator upload\" + viewer-blocked because no operator-exclusive endpoint exists"
    evidence: "02-03-SUMMARY.md line 56-57 explicitly notes 'admin always shadows operator; the test still proves operator passes the gate and viewer is blocked, which is the observable property the criterion targets'. Test test_upload_vessel_role_gate parametrize cases: admin→400, operator→400 (both pass role gate; parser fails on empty payload), viewer→403 (gate blocks)."
    impact: "ROADMAP success criterion 3 wording ('operator-only upload') is not literally testable in the codebase, since admin can upload anywhere operator can. Substitution preserves the underlying intent (operator can; viewer cannot) but the literal phrasing is unmet."
    recommendation: "Acceptable substitution; ROADMAP wording could be amended to 'admin+operator upload (viewer denied)' for accuracy."
  - id: SS-04
    severity: info
    item: "ROADMAP and REQUIREMENTS traceability tables not updated to reflect Phase 2 closure"
    evidence: "REQUIREMENTS.md lines 19-23 still mark AUTHFIX-01/02/04/05 as '[ ]' (Pending); only AUTHFIX-03 is '[x]'. Traceability table lines 118-122: AUTHFIX-01/02/04/05 status='Pending'. ROADMAP.md Progress table line 141 shows 'Phase 2 ... 0/4 ... Not started'. Plan checkboxes for 02-01..02-04 ARE ticked at ROADMAP line 52-55."
    impact: "Documentation-state vs. delivered-state drift; not a goal failure. Same pattern occurred in Phase 1 (per ROADMAP line 15 note about Phase 1 checkbox sync deferred)."
    recommendation: "Tick AUTHFIX-01/02/04/05 boxes and flip traceability statuses + Progress table during Phase 3 documentation refresh, OR as a small chore commit now."
  - id: SS-05
    severity: info
    item: "3 audit-probe-* synthetic users from Phase 1 plan 01-04 not yet cleaned from production VPS users collection"
    evidence: "LOGIN_BUG_RESOLUTION.md line 77 documents this; 02-02-SUMMARY.md line 180 documents that conftest cleanup ran against test DB only. Live MongoDB inspection by verifier confirms 0 audit-probe-* in current pltu_tenayan.users (8 total users), suggesting they may have been cleaned already by an earlier run or never landed in this DB. Either way: NO active leak exists today."
    impact: "Resolved-by-side-effect; no further action required."
    recommendation: "None — verified clean."
phase_3_carryforwards:
  - "Evaluate @radix-ui/react-select upgrade or swap to non-Radix role picker; remove suppressor and re-run operator playbook (LOGIN_BUG_RESOLUTION.md line 81)"
  - "Document VPS service-recovery runbook (uvicorn + yarn start) in LOCAL_SETUP.md / DEPLOYMENT_GUIDE.md (LOGIN_BUG_RESOLUTION.md line 82)"
  - "Optional: install systemd / pm2 units for backend (8013) and frontend (3013) for VPS-restart auto-recovery (LOGIN_BUG_RESOLUTION.md line 83)"
  - "DOCS-01: update API_REFERENCE.md to reflect 400-not-422 for /api/auth/* validation failures and document explicit 401-vs-403 split (AUTH_CONTRACT.md Phase-3 follow-ups)"
  - "Phase-4 TEST-02: replace inline '<TEST_ADMIN_PASSWORD>' literals in 4 test files (test_dashboard_advanced.py, test_coa_reconciliation.py, test_merit_order.py, test_po_batubara.py) and 4 test_reports/iteration_*.json with env-var sourcing; remove from scanner EXCLUDE allowlist"
  - "Phase-3 STAB-03: replace inline admin password in API_REFERENCE.md / DEPLOYMENT_GUIDE.md / frontend/public/docs/* / memory/PRD.md with redacted/example values"
  - "Phase 5 ops or Phase 3: clean 3 audit-probe-* synthetic users from production VPS pltu_tenayan.users with anchor-prefixed filter (informational — current live DB shows none)"
human_verification:
  - test: "Decide disposition for SS-01 (uncommitted suppressor) and SS-02 (deferred operator re-test)"
    expected: "Either: (a) commit frontend/public/index.html to lock in the mitigation now and accept the 'lanjut' deferral as the closing operator signal; (b) commit + run operator playbook now; (c) carry both forward as a Phase 2.1 INSERTED phase per ROADMAP decimal-phase convention."
    why_human: "Both items are explicitly documented in 02-04 SUMMARY/RESOLUTION as known limitations awaiting operator decision. Verifier cannot decide on behalf of project owner. Recommended: option (a) — commit the suppressor and proceed; the regression test already protects the contract path."
  - test: "Confirm Phase-3 carry-forward list (above) is captured somewhere durable before Phase 3 planning starts"
    expected: "Phase-3 plan ingest should pick up the 7 carry-forward items (from LOGIN_BUG_RESOLUTION.md, AUTH_CONTRACT.md, and credential scanner EXCLUDE allowlist TODOs)."
    why_human: "STATE.md still says 'Phase 1 complete; Next: Phase 2'. No Phase-3 plan dir exists yet. Verifier flags so the carry-forward list does not get lost between phases."
  - test: "Decide whether to update REQUIREMENTS.md and ROADMAP.md status fields now (SS-04)"
    expected: "Tick AUTHFIX-01/02/04/05 + flip Progress table + traceability table to 'Complete', OR defer to Phase 3 docs refresh as Phase 1 was."
    why_human: "Cosmetic but affects whether Phase 3 starts from accurate documentation state."
overrides: []
gaps: []
deferred:
  - truth: "AUTHFIX-04 truth #1: An operator has re-run the original AUDIT-04 repro path against the live frontend"
    addressed_in: "Operator-authorized closure (\"lanjut\") on 2026-05-10; carry-forward to Phase 3 if Radix upgrade or component swap is undertaken"
    evidence: "LOGIN_BUG_RESOLUTION.md \"Operator playbook re-test — deferred\" section (lines 13-24); 02-04-SUMMARY.md \"Why operator re-test was deferred\" section"
---

# Phase 02 Authentication Stabilization — Verification Report

**Phase Goal:** Login/auth gets out of the user's way — login works, sessions persist, role enforcement is honest, and a regression test guards the fix. (ROADMAP.md line 42)
**Verified:** 2026-05-10T14:05:13Z (UTC)
**Status:** `human_needed` — phase goal substantively achieved; two soft-spots (SS-01, SS-02) require project-owner disposition; documentation drift (SS-04) optional cleanup.

---

## Goal Achievement — AUTHFIX Verdicts

### AUTHFIX-01 — Session persistence verified by /api/auth/me rehydrate → **CLOSED**

| Truth | Status | Evidence |
|-------|--------|----------|
| Login with valid creds → 200 + JWT | VERIFIED | Live curl probe: `POST /api/auth/login` with <TEST_ADMIN_EMAIL> → HTTP 200, body `{"access_token": ..., "user": {...}}`. Verifier-run `pytest test_auth_session.py::test_login_then_me_rehydrates_same_user` PASSED. |
| Same JWT → GET /api/auth/me → 200 with same identity | VERIFIED | Live curl probe: `GET /api/auth/me -H "Authorization: Bearer <token>"` → HTTP 200, body `{"id":"c837...","email":"<TEST_ADMIN_EMAIL>","name":"Admin","role":"admin",...}`. Test asserts byte-for-byte id/email/role match between login and /me. |
| Frontend rehydrate path correct | VERIFIED (by reference) | Phase-1 audit confirmed AuthContext.js:13-32 already calls /me on mount and clears localStorage on failure. No frontend code changed in Phase 2. |

### AUTHFIX-02 — Correct HTTP error codes per CONS-auth-header → **CLOSED**

| Truth | Status | Evidence |
|-------|--------|----------|
| 400 on malformed /api/auth/* body (was 422) | VERIFIED | server.py:45-56 contains `@app.exception_handler(RequestValidationError)` scoping `request.url.path.startswith("/api/auth/")` to 400. Live curl: empty-body POST /api/auth/login → 400. Test `test_login_with_malformed_body_returns_400` PASSED. |
| 401 on bad creds | VERIFIED | Live curl: bad-password POST /api/auth/login → 401. Test `test_login_with_invalid_password_returns_401` PASSED. |
| 401 on expired token | VERIFIED | Test `test_me_with_expired_token_returns_401` PASSED (verifier ran with JWT_SECRET sourced from backend/.env). |
| 403 on missing-Authorization-header (FastAPI HTTPBearer default) | VERIFIED | Live curl: GET /api/auth/me with no header → 403. Test `test_me_without_token_returns_403` PASSED. Documented in AUTH_CONTRACT.md as D-AUTH-02. |
| Non-auth routes preserve FastAPI 422 default | VERIFIED | Live curl: empty-body POST /api/vessels with valid token → 422 (handler's path-prefix scoping confirmed). |
| AUTH_CONTRACT.md decision record exists | VERIFIED | docs/audit/AUTH_CONTRACT.md = 138 lines, 7 H2 sections, cites D-AUTH-01 + D-AUTH-02, references all 5 test names, includes Phase-3 follow-ups. |

### AUTHFIX-03 — Role enforcement protected by regression tests → **CLOSED (with intent-deviation noted)**

| Truth | Status | Evidence |
|-------|--------|----------|
| Admin can DELETE /api/vessels; operator/viewer 403 | VERIFIED | Test `test_delete_all_vessels_blocks_non_admin[operator|viewer]` both PASSED (403 each). Admin-success destructive path skipped by design (RUN_DESTRUCTIVE_TESTS env-gated). |
| Admin+operator upload to /api/upload/vessel; viewer 403 | VERIFIED (intent) | Test `test_upload_vessel_role_gate[admin]` PASSED 400 (gate passes, parse fails on empty payload), `[operator]` PASSED 400 (same), `[viewer]` PASSED 403 (gate blocks before parse). **Intent-deviation:** ROADMAP says "operator-only upload" but admin can also upload (admin shadows operator). Substitution documented in 02-03-SUMMARY.md line 56-57. See SS-03. |
| Admin/operator/viewer all GET /api/vessels (any-auth read) | VERIFIED | All 3 parametrize cases of `test_get_vessels_succeeds_for_all_roles` PASSED with 200 + pagination contract `{items, total, page}`. |
| Admin can GET /api/users; operator/viewer 403 | VERIFIED | Test `test_get_users_admin_only` parametrize: admin→200, operator→403, viewer→403, all PASSED. |
| Pytest-runnable suite at backend/tests/test_auth_roles.py | VERIFIED | 147 lines, 5 test functions, 4 parametrize blocks → 12 runtime cases, 11 unconditional + 1 destructive-skipped. Verifier re-run confirms 11 passed, 1 skipped. |

### AUTHFIX-04 — Login bug root-caused, fixed/mitigated, regression-protected → **SOFT**

| Truth | Status | Evidence |
|-------|--------|----------|
| Operator re-ran AUDIT-04 repro path | FAILED (deferred) | Operator playbook re-test was NOT executed. Closure relied on operator authorization-by-proceed ("lanjut" on 2026-05-10) after VPS-restart recovery. Documented honestly in LOGIN_BUG_RESOLUTION.md lines 13-24 and 02-04-SUMMARY.md "Why operator re-test was deferred". → SS-02 |
| ResizeObserver error no longer surfaces to user | VERIFIED-BUT-UNCOMMITTED | Suppressor at frontend/public/index.html:49-65 (script tag with regex `/^ResizeObserver loop /` on `window.error` and `unhandledrejection`). **HOWEVER:** the suppressor is uncommitted in inner repo; HEAD:frontend/public/index.html does not contain it. → SS-01 |
| Path A login flow completes (token + /me + /dashboard) | VERIFIED (at contract layer) | Test `test_login_then_me_rehydrates_same_user` PASSED end-to-end. UI-side /dashboard navigation not verified by automated test (no headless browser). |
| Any UI failure beyond ResizeObserver captured or carried forward | VERIFIED | LOGIN_BUG_RESOLUTION.md "Phase-3 follow-ups" lists Radix upgrade evaluation, VPS recovery runbook, systemd/pm2 units. None requires Phase 2.1 INSERTED phase per operator decision. |
| LOGIN_BUG_RESOLUTION.md cites regression test + status | VERIFIED | 92 lines, 9 H2 sections, status="Mitigated", cites `test_login_then_me_rehydrates_same_user` (commit f6d0a4b), cites LOGIN_BUG.md, cites AUTHFIX-04. |

### AUTHFIX-05 — Zero credentials in tracked files; pre-commit gate → **CLOSED**

| Truth | Status | Evidence |
|-------|--------|----------|
| memory/test_credentials.md gitignored AND untracked | VERIFIED | `git ls-files memory/test_credentials.md` empty; `git check-ignore` exits 0 (rule at .gitignore:96); file remains on disk (255 bytes, last modified 2026-04-30). |
| Repeatable scanner exists with JWT/bearer/Mongo/password patterns | VERIFIED | scripts/check_credentials.sh = 98 lines, 4 grep passes (JWT / Bearer-JWT / MongoDB-URI / <TEST_ADMIN_PASSWORD> literal); verifier-run exits 0 with "OK: 169 files (after 16 exemptions)". |
| Pre-commit hook wired to scanner | VERIFIED | .git/hooks/pre-commit = 24 lines, executable, chained (large-file guard at Stage 1 + scanner at Stage 2); verifier-run exits 0. |
| CREDENTIAL_HYGIENE.md contract document | VERIFIED | docs/audit/CREDENTIAL_HYGIENE.md = 149 lines, all 9 mandatory headings present, references TEST_ADMIN_PASSWORD env contract + scripts/check_credentials.sh. |

---

## Test-Suite Run Results (verifier-executed)

```
$ pytest backend/tests/test_auth_session.py -v --tb=short
  (DB: live pltu_tenayan @ http://localhost:8013)
  → 5 passed in 0.98s — exit code 0
  ✓ test_login_then_me_rehydrates_same_user
  ✓ test_login_with_invalid_password_returns_401
  ✓ test_login_with_malformed_body_returns_400
  ✓ test_me_without_token_returns_403
  ✓ test_me_with_expired_token_returns_401  (JWT_SECRET sourced from backend/.env)

$ pytest backend/tests/test_auth_session.py backend/tests/test_auth_roles.py -v
  (DB: isolated pltu_tenayan_test_verify @ http://127.0.0.1:8113;
   uvicorn spun up by verifier, 3 role users registered, DB dropped at end)
  → 16 passed, 1 skipped in 2.37s — exit code 0
  ✓ all 5 session tests
  ✓ test_get_vessels_succeeds_for_all_roles[admin|operator|viewer]
  ✓ test_upload_vessel_role_gate[admin→400|operator→400|viewer→403]
  ✓ test_delete_all_vessels_blocks_non_admin[operator|viewer]
  ⊘ test_delete_all_vessels_admin_success  (RUN_DESTRUCTIVE_TESTS not set — by design)
  ✓ test_get_users_admin_only[admin→200|operator→403|viewer→403]

$ bash scripts/check_credentials.sh
  → exit code 0
  → "OK: no tracked credential patterns found in 169 files (after 16 exemptions)."

$ bash .git/hooks/pre-commit
  → exit code 0
  → chained large-file guard + scanner both clean

Live curl probes (against running uvicorn pid 21998 on port 8013):
  POST /api/auth/login (empty body)                           → 400 ✓
  POST /api/auth/login (bad creds)                            → 401 ✓
  POST /api/auth/login (<TEST_ADMIN_EMAIL> / <TEST_ADMIN_PASSWORD>)    → 200 ✓
  GET  /api/auth/me    (no Authorization header)              → 403 ✓
  GET  /api/auth/me    (Bearer <admin token>)                 → 200 ✓ (id+email+role match)
  POST /api/vessels    (empty body, valid token)              → 422 ✓ (non-auth route preserves default)
```

**Test verdict: all goal-bearing tests PASS against both the live production-shaped backend and an isolated reproducible test DB. The expired-token test executed (not skipped) in both runs.**

---

## Required Artifacts

| Artifact | Expected | Status | Lines | Details |
|----------|----------|--------|-------|---------|
| `pltu-tenayan-full-backup/.gitignore` | memory/test_credentials.md exclusion | ✓ VERIFIED | (line 96) | Untracked + ignored confirmed |
| `pltu-tenayan-full-backup/scripts/check_credentials.sh` | 4-pattern scanner | ✓ VERIFIED | 98 | Executable; exits 0 |
| `pltu-tenayan-full-backup/.git/hooks/pre-commit` | Chained large-file + scanner | ✓ VERIFIED | 24 | Executable; exits 0 |
| `pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md` | 9-section contract | ✓ VERIFIED | 149 | All 9 headings present |
| `pltu-tenayan-full-backup/backend/server.py` (handler) | RequestValidationError handler scoped to /api/auth/* | ✓ VERIFIED | (lines 1-4 imports, 40-56 handler) | Live-tested |
| `pltu-tenayan-full-backup/backend/routers/auth.py` (parity comment) | AUTHFIX-02 NOTE comment | ✓ VERIFIED | (line 2) | Comment present (router still unmounted, by design) |
| `pltu-tenayan-full-backup/backend/tests/conftest.py` | 7 fixtures + audit-probe cleanup | ✓ VERIFIED | 93 | All 7 fixtures defined; autouse cleanup; AST parses |
| `pltu-tenayan-full-backup/backend/tests/test_auth_session.py` | 5-test session suite | ✓ VERIFIED | 140 | 5 def test_; 5/5 pass live |
| `pltu-tenayan-full-backup/backend/tests/test_auth_roles.py` | 5-test role suite (12 parametrize cases) | ✓ VERIFIED | 147 | 5 def test_; 4 parametrize blocks; 11 pass + 1 skip live |
| `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` | D-AUTH-01 + D-AUTH-02 record | ✓ VERIFIED | 138 | 7 H2 sections, both decisions cited |
| `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG_RESOLUTION.md` | Disposition + regression cite | ✓ VERIFIED | 92 | 9 H2 sections; status=Mitigated; cites regression test |
| `pltu-tenayan-full-backup/frontend/public/index.html` (suppressor) | ResizeObserver suppressor block | ⚠️ ORPHANED-FROM-GIT | 17 added | **Suppressor exists in working tree but is NOT committed to inner repo HEAD.** → SS-01 |

---

## Key Link Verification

| From | To | Via | Status |
|------|-----|-----|--------|
| .git/hooks/pre-commit | scripts/check_credentials.sh | shell exec | ✓ WIRED (verifier ran end-to-end) |
| scripts/check_credentials.sh | tracked files | git ls-files \| grep -vxF | ✓ WIRED (169 files scanned) |
| .gitignore | memory/test_credentials.md | gitignore exclusion | ✓ WIRED (check-ignore exit 0) |
| server.py auth_validation_handler | /api/auth/login \| /api/auth/register | @app.exception_handler scoped by request.url.path | ✓ WIRED (live curl 400 confirmed) |
| test_auth_session.py | live backend at REACT_APP_BACKEND_URL | requests.post / requests.get | ✓ WIRED (verifier ran) |
| conftest.py | env vars TEST_*_EMAIL/PASSWORD | os.environ | ✓ WIRED |
| AUTH_CONTRACT.md | constraints.md CONS-auth-header | explicit citation | ✓ WIRED (CONS-auth-header cited 8× in test docstrings + AUTH_CONTRACT.md) |
| LOGIN_BUG_RESOLUTION.md | LOGIN_BUG.md (original repro) | explicit citation | ✓ WIRED (3+ citations) |
| LOGIN_BUG_RESOLUTION.md | test_auth_session.py (regression) | regression-test citation | ✓ WIRED (cites test_login_then_me_rehydrates_same_user by name) |
| frontend/public/index.html suppressor | Login.js:186-197 Radix Select | page-level error handler | ⚠️ PARTIAL — suppressor present in working tree, blocks ResizeObserver loop messages, but NOT committed to git history. → SS-01 |

---

## Anti-Patterns / Soft-Spots

### SS-01 — AUTHFIX-04 mitigation uncommitted in inner repo (WARNING)

`frontend/public/index.html` shows the ResizeObserver suppressor block (17 added lines, regex `/^ResizeObserver loop /`) as a working-tree modification. `git -C pltu-tenayan-full-backup show HEAD:frontend/public/index.html` does not contain `ResizeObserver` or `RO_RE`. The plan-04 SUMMARY claims the file was "left untouched" (true — plan 02-04 did not commit it) and "matches LOGIN_BUG.md byte-for-byte" (true — content matches). But the practical consequence is: **the AUTHFIX-04 mitigation is not durable across `git reset --hard` or a fresh clone of the inner repo**.

Live behavior: the suppressor WORKS today (it's loaded by the running CRA dev-server pid 22223 from disk, not from git). But the gate Phase 2 promised — "regression-protected mitigation" — is partially hollow because git history does not lock it.

**Recommendation:** Commit `frontend/public/index.html` to the inner repo with a `chore(authfix-04): commit ResizeObserver suppressor (carried over from prior local state)` message, after sourcing through the credential scanner. The file does not contain credentials so the hook will pass.

### SS-02 — AUTHFIX-04 closed without operator browser-capture (WARNING)

The plan 02-04 Task 1 "human-verify" checkpoint specified verbatim DevTools capture (Console / Network / localStorage / final URL) for Path A and the register-tab role-select. The capture was not produced. Closure rationale rests on:
1. Backend health verified at contract layer (AUTHFIX-01 + AUTHFIX-02 tests PASS)
2. Suppressor unchanged byte-for-byte from the LOGIN_BUG.md verbatim quote
3. Operator authorization-by-proceed via "lanjut" on 2026-05-10 after VPS-restart recovery

This is documented honestly in both LOGIN_BUG_RESOLUTION.md (lines 13-24) and 02-04-SUMMARY.md ("Why operator re-test was deferred"). It is NOT a hidden deviation. But it does mean **AUTHFIX-04 truth #1 is FAILED at the literal level** — no operator playbook execution happened.

**Disposition options:**
- (a) Accept as already-decided ("lanjut" stands), proceed to Phase 3, file the operator playbook for Phase-3 Radix-upgrade work where the suppressor is removed and the playbook MUST be re-run.
- (b) Run the operator playbook now and append the capture to LOGIN_BUG_RESOLUTION.md.
- (c) Insert Phase 2.1 with operator re-test + suppressor commit + REQUIREMENTS sync as the explicit scope.

Verifier recommendation: **option (a)** — backend regression coverage is solid, mitigation is functionally working (verified live), and Phase 3 will inevitably re-run the playbook when Radix upgrade lands.

### SS-03 — ROADMAP "operator-only upload" substituted with "admin+operator upload" (WARNING)

The plan team correctly identified that no operator-exclusive endpoint exists in `backend/server.py` (admin's role list always includes operator's permissions; admin shadows operator). The substitution preserves the underlying intent — operator can upload, viewer cannot — and the test parametrizes admin/operator/viewer cases proving exactly that. But the literal ROADMAP wording is unmet.

**Disposition:** Either accept the substitution (recommended — codebase reality) or amend ROADMAP success criterion 3 to "admin+operator upload (viewer denied)".

### SS-04 — Documentation drift in REQUIREMENTS.md and ROADMAP.md (INFO)

REQUIREMENTS.md still shows AUTHFIX-01 / 02 / 04 / 05 as `[ ]` (Pending) with traceability table status="Pending"; only AUTHFIX-03 is `[x]` Complete. ROADMAP.md Progress table line 141 still shows "Phase 2 ... 0/4 ... Not started". The same checkbox-sync deferral happened in Phase 1 (per ROADMAP line 15 explicit note). Plan checkboxes for 02-01..02-04 ARE ticked at ROADMAP lines 52-55.

**Disposition:** Cosmetic; tick during Phase 3 doc refresh OR run a small `chore(phase-2): tick AUTHFIX-01/02/04/05 boxes` commit on the outer repo.

### SS-05 — audit-probe-* cleanup status (INFO)

Verifier ran `db.users.count_documents({email: /^audit-probe-/})` against live `pltu_tenayan` and got 0. Either the synthetic users were already cleaned externally OR the live DB never received them OR they were cleaned during ingest. Either way: **NO leak exists today**. The conftest cleanup fixture works against whichever DB is configured at test time.

---

## Phase-3 Carry-Forward List

For Phase-3 planning ingest. All items are documented in their source files; verifier consolidates here so they don't get lost in transition:

1. **Radix UI Select upgrade or replacement** — eliminate ResizeObserver loop emission upstream; pair with suppressor removal and operator playbook re-run. (Source: LOGIN_BUG_RESOLUTION.md line 81.)
2. **VPS service-recovery runbook** — promote the uvicorn + yarn-start procedure to LOCAL_SETUP.md / DEPLOYMENT_GUIDE.md (STAB-03 / DOCS-01). (Source: LOGIN_BUG_RESOLUTION.md line 82.)
3. **systemd / pm2 auto-restart units** — backend (8013) + frontend (3013) auto-recovery on VPS reboot. Optional. (Source: LOGIN_BUG_RESOLUTION.md line 83.)
4. **DOCS-01 API_REFERENCE.md update** — reflect 400-not-422 for /api/auth/* validation; document explicit 401-vs-403 split. (Source: AUTH_CONTRACT.md "Phase-3 follow-ups".)
5. **Phase-4 TEST-02 cleanup** — replace inline "<TEST_ADMIN_PASSWORD>" literals in 4 test files + 4 test_reports/iteration_*.json with env-var sourcing; remove from scanner EXCLUDE allowlist. (Source: 02-01-SUMMARY.md scanner allowlist; CREDENTIAL_HYGIENE.md "Known exemptions".)
6. **Phase-3 STAB-03 cleanup** — replace inline admin password in API_REFERENCE.md / DEPLOYMENT_GUIDE.md / frontend/public/docs/* / memory/PRD.md with redacted examples. (Source: 02-01-SUMMARY.md scanner allowlist.)
7. **REQUIREMENTS.md / ROADMAP.md sync** — tick AUTHFIX-01/02/04/05 + flip Progress table; address Phase-1 deferred checkbox sync (AUDIT-01/02). (Source: SS-04.)

---

## Phase-Level Verdict

**READY for Phase 3 — with two soft-spots requiring project-owner decision before Phase 3 starts:**

- Backend contract is locked (AUTHFIX-01/02): live-verified + regression-tested
- Role enforcement is locked (AUTHFIX-03): 11/12 tests pass + 1 destructive skip-by-design
- Credential hygiene is locked (AUTHFIX-05): scanner + hook + gitignore all green; 169 files scanned, 16 phase-tagged exemptions
- Login-bug closure (AUTHFIX-04) is `mitigated` with documented soft-spots; **the contract path that the bug obscured is regression-protected at the backend layer.** UI-side ground-truth from a real browser was deferred by operator authorization.

The phase goal — "login works, sessions persist, role enforcement is honest, regression tests guard the fix" — is **substantively achieved**. The two soft-spots (SS-01 uncommitted suppressor, SS-02 deferred operator re-test) do not invalidate the closure but should be acknowledged before Phase 3 starts so they don't compound into hidden debt.

**Recommended next actions before Phase 3 planning:**
1. Commit `frontend/public/index.html` to lock SS-01 (one-line chore commit).
2. Project-owner records explicit acceptance of SS-02 ("lanjut" stands; Phase 3 Radix work will subsume the playbook re-run) OR runs the playbook now.
3. Optionally tick AUTHFIX-01/02/04/05 in REQUIREMENTS.md + flip ROADMAP Progress table (SS-04).
4. Ensure the 7 carry-forward items above are visible to whoever ingests Phase 3.

---

_Verified: 2026-05-10T14:05:13Z_
_Verifier: Claude (gsd-verifier, goal-backward verification)_
_Test runs executed against: live pltu_tenayan @ :8013 (admin tier) + isolated pltu_tenayan_test_verify @ :8113 (3-role tier, dropped at teardown)_
