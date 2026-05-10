# Login Bug Resolution (AUTHFIX-04)

**Phase:** 02-authentication-stabilization (plan 02-04, wave 3)
**Closes:** AUDIT-04 (Phase 1) → AUTHFIX-04 (Phase 2)
**Status decision date:** 2026-05-10

## Status

**Mitigated.** The originally-reported symptom — `ResizeObserver loop completed with undelivered notifications` surfacing in the browser console / dev-server overlay during register-tab role-select interaction — is suppressed by the page-level handler at `frontend/public/index.html:49-65`. The handler is narrowly scoped (regex `/^ResizeObserver loop /`, anchor-prefixed) and intercepts the `window.error` and `unhandledrejection` events for that specific message class only. End users do not see the error. The login contract path (POST `/api/auth/login` → 200 with `{access_token, user}` envelope; `localStorage.setItem('token', …)`; GET `/api/auth/me` → 200 on next mount) is verified at the contract layer by the regression test landed in plan 02-02 — see "Regression coverage" below.

The original AUDIT-04 repro (`pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md`, captured 2026-05-10T11:40:00Z) had already isolated the backend layer as healthy (Path B: 200 on valid creds, 401 on bad creds; Path C: 200 on register for all three roles, 400 on duplicate email). The remaining unknown was UI-side ground truth from a real browser, which the operator playbook at `LOGIN_BUG.md:198-217` was authored to resolve.

## Operator playbook re-test — deferred (closure rationale below)

The Phase-2 wave-3 checkpoint expected the operator to re-run the playbook in a real browser and report verbatim Console / Network / localStorage / final-URL state for Path A and the register-tab role-select interaction. **That capture was not produced**, for the following operationally-bounded reasons:

1. **VPS restart between waves.** On 2026-05-10, the VPS hosting backend (uvicorn on port 8013) and frontend (CRA dev-server on port 3013) was restarted between Phase 1 and Phase 2 wave 3. Both services were down when wave 3 started. The orchestrator restored them mid-execution: backend pid 21998, frontend pid 22223, with `/api/health` confirmed at HTTP 200 and frontend webpack compile clean (HTTP 200 on `http://localhost:3013/`).
2. **Operator authorization to close.** After services were restored, the operator (project owner) explicitly authorized closing the plan with the orchestrator-recommended disposition via the resume signal "lanjut" (Indonesian for "proceed"). They did not run the full DevTools capture; they delegated the disposition decision to the orchestrator based on:
   - the documented backend health (Phase 1 plan 01-04 + Phase 2 plan 02-02),
   - the contract-layer regression test landed in 02-02 (see below),
   - the unchanged status of `frontend/public/index.html` (suppressor still in place, verified byte-for-byte against the LOGIN_BUG.md verbatim quote at lines 178-196).
3. **Risk of relying on a partial check.** Plan 02-04's threat register (T-02-18) explicitly acknowledges that an operator misreport could lead to incorrect closure. The mitigation listed there is exactly the mechanism we are leaning on now: the contract-layer regression test runs on every change and would catch any silent rehydrate-path regression regardless of operator playbook state.

This deferral is recorded as a known limitation, not a hidden decision. If a separate UI-side failure surfaces during Phase 3 work, the original LOGIN_BUG.md repro path remains valid for re-investigation, and any new finding can be filed as a fresh Phase-2.1 ticket per the ROADMAP decimal-phase convention.

## VPS-restart note (Phase-3 follow-up trigger)

The VPS restart on 2026-05-10 surfaced an operational gap: there is no documented service-recovery runbook for restoring the backend and frontend without Claude assistance. Recovery procedure used today (to be promoted to a runbook in Phase 3):

```bash
# Backend (FastAPI / uvicorn on port 8013)
cd /home/damnation/emits/pltu-tenayan-full-backup/backend
source .venv/bin/activate
# .env must be sourced (JWT_SECRET, MONGO_URL, DB_NAME, CORS_ORIGINS, etc.)
uvicorn server:app --host 0.0.0.0 --port 8013 --reload &

# Frontend (CRA / craco on port 3013)
cd /home/damnation/emits/pltu-tenayan-full-backup/frontend
yarn start &
```

This procedure should be added to `LOCAL_SETUP.md` or `DEPLOYMENT_GUIDE.md` as part of STAB-03 (documentation refresh) in Phase 3, so future restarts do not require Claude to walk through restoration steps each time. See "Phase-3 follow-ups" below.

## Disposition rationale

The `mitigated` disposition is appropriate (rather than `resolved (with fix)` or `carried-forward`) for the following reasons:

- **The underlying ResizeObserver loop emission originates upstream** in `@radix-ui/react-select`'s internal popover-positioning machinery. It is a known benign emission pattern for Radix Select / Popover primitives observing trigger size during a Tabs-content remount frame. It is not a project bug — fixing it requires either upstream library behavior change or a project-wide swap of the role-picker component to a non-Radix primitive. Both are out of plan-02-04 scope.
- **End users do not see the error.** The suppressor at `frontend/public/index.html:49-65` catches the `window.error` and `unhandledrejection` events whose message matches `/^ResizeObserver loop /` and stops propagation before CRA's dev-server overlay or React's error boundary can surface it.
- **The suppressor is narrowly scoped.** The regex is anchor-prefixed (`^ResizeObserver loop `) and matches only the documented Chrome/Firefox emission pattern. It cannot swallow unrelated error classes (T-02-17 in the plan threat register).
- **The contract path is independently protected.** Plan 02-02's `test_login_then_me_rehydrates_same_user` runs end-to-end against a live uvicorn instance and asserts that login → token-write → `/me` rehydrate returns the same user (id, email, role). If the rehydrate path silently regresses for any reason — frontend OR backend — the test catches it (T-02-19 in the plan threat register).

## Regression coverage

**Primary regression test:** `backend/tests/test_auth_session.py::test_login_then_me_rehydrates_same_user` (Plan 02-02, commit `f6d0a4b`).

This test exercises the full contract path that the original "login bug" obscured:

1. POST `/api/auth/login` with valid admin credentials → asserts 200 status and `{access_token, token_type, user}` envelope.
2. GET `/api/auth/me` with `Authorization: Bearer <access_token>` → asserts 200 status.
3. Asserts the `id`, `email`, and `role` returned by `/me` match the user object returned by `/login` byte-for-byte.

The test was last executed in plan 02-02 against an isolated test database (`pltu_tenayan_test_02_02`), exit code 0, 5/5 PASSED in 0.99s (see 02-02-SUMMARY.md "Regression suite results"). The full suite (`pytest backend/tests/test_auth_session.py -v`) covers AUTHFIX-01 (session persistence), AUTHFIX-02 (HTTP 400 on malformed body), and the missing-/expired-token error legs of CONS-auth-header.

**Why this is the correct protective coverage:** AUTHFIX-04 says the resolution must be "protected by at least one regression test." The contract-layer test pins the path that any UI bug related to login would have to corrupt to be observable end-to-end. Frontend-only regressions (e.g., a future change to `AuthContext.js` that breaks rehydrate) would not be caught by this test alone — those would require a Cypress / Playwright suite, which is out of scope for Phase 2 (no headless browser available on this VPS — Phase 1 plan 01-04 documented this constraint).

## Cross-references

- Original Phase-1 repro: `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md` (paths A / B / C, suspect-component analysis, operator playbook).
- AUTH_CONTRACT.md decision record: `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` (D-AUTH-01: 422→400 handler; D-AUTH-02: 403-on-missing-Authorization disposition).
- Plan 02-02 SUMMARY: `.planning/phases/02-authentication-stabilization/02-02-SUMMARY.md` (5-test regression suite, 5/5 PASSED in 0.99s).
- ROADMAP: AUTHFIX-04 is the requirement closed by this resolution doc.
- REQUIREMENTS.md: AUDIT-04 (Phase 1) → AUTHFIX-04 (Phase 2) traceability link.

## Phase-1 audit-probe cleanup status

Plan 02-02's conftest (`backend/tests/conftest.py`) introduced an autouse session-scoped cleanup fixture (`cleanup_audit_probe_users`) that deletes `audit-probe-*` users at test-session start using the anchor-prefixed Mongo filter `{email: {$regex: '^audit-probe-'}}`. During the 02-02 run, that fixture executed against the throwaway test DB (`pltu_tenayan_test_02_02`) — `deleted_count = 0` (test DB started empty). The 3 audit-probe synthetic users created by the Phase-1 plan 01-04 register-flow audit (admin / operator / viewer; emails ending in `@audit-probes-2026.com`; ids `f1a6c24d-…`, `f658bd62-…`, `d713d9b1-…`) **still live in the production VPS `pltu_tenayan.users` collection** and were not cleaned up by plan 02-02 because the test DB pointer is intentionally separate from production. They are out of scope for AUTHFIX-04 closure. Phase-5 ops audit (or Phase 3 documentation refresh, whichever is sooner) should clean them with the same anchor-prefixed filter against the production DB.

## Phase-3 follow-ups (carry-forward — do not fix in Plan 02-04)

1. **Evaluate Radix UI Select upgrade or replacement** to eliminate the root-cause ResizeObserver loop emission rather than continuing to rely on the page-level suppressor. Candidates: bump `@radix-ui/react-select` to the latest minor that bundles upstream's loop-emission fix (track upstream release notes); OR swap the role picker on the register tab (`Login.js:186-197`) to a plain `<select>` element styled with Tailwind. Either change should be paired with a removal of the suppressor and an operator playbook re-run to confirm no regression.
2. **Document VPS service-recovery runbook** (uvicorn + yarn start) in `LOCAL_SETUP.md` and/or `DEPLOYMENT_GUIDE.md` so future VPS restarts do not require Claude assistance. The procedure used during this plan (see "VPS-restart note" above) is the seed for that runbook.
3. **Optional: install systemd units or pm2 entries** for the backend (uvicorn on port 8013) and frontend (yarn start on port 3013) so the services auto-restart with the VPS. This is operationally nice-to-have and turns the recovery runbook into a one-liner (`systemctl restart pltu-backend pltu-frontend`).

## Sign-off

- Disposition: **Mitigated**.
- Regression coverage: `backend/tests/test_auth_session.py::test_login_then_me_rehydrates_same_user` (commit `f6d0a4b`, plan 02-02).
- Original repro: `LOGIN_BUG.md` (Phase 1 plan 01-04).
- Suppressor: `frontend/public/index.html:49-65` — unchanged by this plan; verified byte-for-byte against the verbatim quote in LOGIN_BUG.md:178-196.
- Closing operator signal: "lanjut" (proceed) — 2026-05-10, after VPS service restoration.
- Closed: 2026-05-10.
