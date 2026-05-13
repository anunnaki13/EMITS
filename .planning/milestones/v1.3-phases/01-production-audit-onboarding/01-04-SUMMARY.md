---
phase: 01-production-audit-onboarding
plan: 04
subsystem: auth
tags: [audit, auth, login, register, repro, read-only]
requires:
  - .planning/PROJECT.md
  - pltu-tenayan-full-backup/frontend/src/pages/Login.js
  - pltu-tenayan-full-backup/frontend/src/contexts/AuthContext.js
  - pltu-tenayan-full-backup/frontend/public/index.html
  - pltu-tenayan-full-backup/memory/test_credentials.md
  - pltu-tenayan-full-backup/docs/audit/ENDPOINT_AUDIT.md
  - pltu-tenayan-full-backup/docs/audit/FRONTEND_MAP.md
provides:
  - pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md
affects:
  - phase:02-authentication-stabilization (LOGIN_BUG.md is the canonical input that drives AUTHFIX-01..04 — repro + named suspect + backend baseline)
  - phase:05-tech-debt (audit-probe-* synthetic users in users collection await cleanup)
  - phase:03-documentation-refresh (CONS-auth-header divergence noted: malformed body returns 422 not 400 — doc must align with actual behavior or backend must add a custom validation handler)
key-files:
  created:
    - pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md
    - pltu-tenayan-full-backup/docs/audit/.work/login-backend.txt
    - pltu-tenayan-full-backup/docs/audit/.work/register-backend.txt
    - pltu-tenayan-full-backup/docs/audit/.work/login-frontend-evidence.md
  modified: []
decisions:
  - Reserve-TLD probe deviation: .invalid emails are rejected by Pydantic email-validator (RFC 6761 reserved); re-probed Path C with a non-reserved synthetic domain (audit-probes-2026.com) so register success/failure could be captured against the live backend.
  - Frontend repro deferred to operator playbook because no headless browser is available on this VPS; structure (UI inventory, click path, expected vs observed table) was still produced so the operator can fill it in mechanically in 5 minutes.
  - Refined symptom: ResizeObserver console noise is bound to the register-tab Radix role-select (Login.js:186-197), NOT the login form (which has zero Radix Select / Popover primitives). Phase 2 should disambiguate "login bug" from "register-tab console noise" before fixing.
metrics:
  tasks_total: 2
  tasks_completed: 2
  files_created: 4
  files_modified: 0
  commits: 2
  duration_minutes: ~10
  completed_date: 2026-05-10
---

# Phase 1 Plan 4: Login Bug Repro Summary

**One-liner:** LOGIN_BUG.md captures three reproduction paths (UI login, API login, API register) against the live VPS at 103.150.197.225, with backend baseline confirmed (200/401/422), all three roles registering cleanly via API (200), the suspect role-select Radix combobox named at Login.js:186-197, and the ResizeObserver suppressor at index.html:49-65 documented as a temporary mitigation — Phase 2 inherits a complete written repro plus a 5-minute operator playbook for the deferred browser-side verification.

## What Was Built

Four artifacts on disk:

1. **pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md** (224 lines) — the deliverable. Structure:
   - Symptom (as reported) + refinement noting Radix Select is on the register tab, not login.
   - Path A: UI login repro structure with operator playbook.
   - Path B: API login repro (curl-driven) with the actual status codes captured.
   - Path C: API register repro for all three roles + duplicate-email check + RFC 6761 reserved-TLD discovery.
   - Suspected component: Login.js:186-197 with import line (Login.js:10), state setter (Login.js:27), submit-handler read (Login.js:47).
   - Mitigation status: index.html:49-65 verbatim suppressor block.
   - Operator playbook: 5-minute manual re-verification.
   - Methodology + redaction note.
2. **.work/login-backend.txt** — raw redacted curl captures for `/api/auth/login` (valid creds against VPS endpoint, valid creds against localhost, invalid creds, malformed body).
3. **.work/register-backend.txt** — raw redacted curl captures for `/api/auth/register` (three roles × two probe rounds: `.invalid` TLD round all 422, non-reserved domain round all 200, plus duplicate-email 400, plus cleanup note).
4. **.work/login-frontend-evidence.md** — structured worksheet with UI element inventory, two-variant click path (login form + register form with Radix Select), expected-vs-observed tables (OBSERVED rows deferred), console-error excerpt placeholder, network observations (request/response shapes from AuthContext.js), and operator playbook.

## Path B (API login) — observed per-probe

- **Step 1 (valid creds):** HTTP 200 with `{access_token, token_type:"bearer", user:{id, email, name, role:"admin", created_at}}` — matches CONS-auth-header. Confirmed against both VPS (`103.150.197.225:8013`) and localhost endpoints (same backend).
- **Step 2 (invalid password):** HTTP 401 with `{"detail":"Email atau password salah"}` — matches CONS-auth-header.
- **Step 3 (malformed body, missing password + invalid email):** HTTP 422 with Pydantic validation detail array. **Divergence flagged:** CONS-auth-header specifies 400 for validation; FastAPI/Pydantic default is 422. No functional impact on login flow; Phase 2 must decide between custom RequestValidationError handler vs updating the spec.

## Path C (API register) — observed per role

Two probe rounds:

- **Round 1 (`.invalid` TLD per the plan's safety guidance):** all three roles returned **HTTP 422** with `"value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email."` — Pydantic's `email-validator` rejects RFC 6761 reserved TLDs. **No documents inserted.** This is a useful discovery for Phase 2 regression-test fixture choice.
- **Round 2 (non-reserved synthetic domain `audit-probes-2026.com`):**
  - role=admin → **HTTP 200** with `{access_token, user:{id:f1a6c24d-..., role:"admin"}}`
  - role=operator → **HTTP 200** with `{access_token, user:{id:f658bd62-..., role:"operator"}}`
  - role=viewer → **HTTP 200** with `{access_token, user:{id:d713d9b1-..., role:"viewer"}}`
  - duplicate email re-submit → **HTTP 400** with `{"detail":"Email sudah terdaftar"}` (matches expected — not 500).

No divergence at the API layer for the happy path. Register response shape is identical to login (`{access_token, token_type, user}`), consistent with `AuthContext.register` at AuthContext.js:43-50.

## Suspect component for Phase 2

**Primary:** Radix-based `<Select>` for the register-form role picker — `frontend/src/pages/Login.js:186-197`. Imports from `@/components/ui/select` (Login.js:10) which wraps `@radix-ui/react-select`. `setRegRole` setter at Login.js:27 (default `"operator"`); value flows into `AuthContext.register` (AuthContext.js:43-50) via the submit handler at Login.js:47.

**Secondaries (Phase 2 to rule out):**

- `AuthContext.login` at AuthContext.js:34-41 — synchronous-looking state writes inside async; React 19 batched-update behavior to confirm.
- `AuthContext` initial-mount race at AuthContext.js:13-32 — no guard against login firing while `initAuth` is in flight.
- `index.html:49-65` suppressor regex `/^ResizeObserver loop /` — verify breadth (browser-variant phrasing).

## Side effects on live system

Three `audit-probe-*` synthetic users were inserted into the live `users` collection:

| Email | id | role |
|-------|----|----|
| `audit-probe-admin-1778413168@audit-probes-2026.com` | `f1a6c24d-2de8-4e93-8487-ca4f405bf880` | admin |
| `audit-probe-operator-1778413168@audit-probes-2026.com` | `f658bd62-cfad-424f-a588-e0663d86a797` | operator |
| `audit-probe-viewer-1778413168@audit-probes-2026.com` | `d713d9b1-502e-4551-a525-5ec6fc8b60be` | viewer |

Cleanup filter (Phase 2 regression test setup or Phase 5 cleanup):

```js
db.users.deleteMany({ email: /^audit-probe-/ })
```

The `.invalid` round inserted nothing (all 422).

## Open questions Phase 2 inherits

1. **Browser-side verification of Path A is deferred** to the operator playbook because no headless browser is available on this VPS. Phase 2's first task is to confirm whether the user-reported "login bug" is (a) the benign register-tab ResizeObserver console noise misattributed to login, or (b) a separate UI-side failure on the login flow distinct from the suppressed warning.
2. **CONS-auth-header divergence on validation status code** — backend returns 422 for malformed body, spec says 400. Decide: custom handler vs spec update vs document-and-accept.
3. **email-validator RFC 6761 enforcement** — Phase 2 regression test fixtures must avoid `.invalid`/`.test`/`.local`/`.example`. Decide whether to relax this for tests via a validator override or just use non-reserved synthetic domains.
4. **Suppressor coverage** — verify the regex `/^ResizeObserver loop /` matches all browser-variant phrasings; verify both `error` and `unhandledrejection` event paths are exercised (the suppressor handles both, but it's untested at the integration level).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Path C `.invalid` TLD rejected by Pydantic email-validator (422)**

- **Found during:** Task 1 step 3 (register probes).
- **Issue:** The plan deliberately specified `@example.invalid` (RFC 6761) for synthetic register emails, with the documented expectation that the synthetic users would be inserted. The live backend rejects them with 422 because Pydantic's `email-validator` library treats `.invalid` (and `.test`, `.local`, `.example`) as "special-use or reserved" names and refuses to validate them as email addresses.
- **Fix:** Added a `--- DEVIATION NOTE ---` section to register-backend.txt documenting the cause, then re-probed all three roles using a non-reserved synthetic domain (`audit-probes-2026.com`) so Path C in LOGIN_BUG.md has real success-path evidence (200 for admin/operator/viewer, 400 for duplicate). The synthetic prefix `audit-probe-` is preserved for the cleanup filter. Updated the CLEANUP-NOTE row accordingly.
- **Files modified:** `pltu-tenayan-full-backup/docs/audit/.work/register-backend.txt` only (no source code touched).
- **Commit:** `b578871` (inner repo).

No other deviations. ResizeObserver suppressor at index.html:49-65 left untouched as required. Login.js, AuthContext.js, and all other source files left unmodified.

## Authentication Gates

None. Test credentials read from `pltu-tenayan-full-backup/memory/test_credentials.md` (gitignored, present locally) and the credentials worked on first probe (login returned 200).

## Self-Check: PASSED

- pltu-tenayan-full-backup/docs/audit/LOGIN_BUG.md → FOUND (224 lines, all required sections present, no JWT, no cleartext password, no diff/patch markers)
- pltu-tenayan-full-backup/docs/audit/.work/login-backend.txt → FOUND (redacted)
- pltu-tenayan-full-backup/docs/audit/.work/register-backend.txt → FOUND (redacted, two probe rounds + cleanup note)
- pltu-tenayan-full-backup/docs/audit/.work/login-frontend-evidence.md → FOUND (5 required sections + operator playbook)
- inner-repo commit `b578871` (Task 1 evidence) → FOUND in `git -C pltu-tenayan-full-backup log`
- inner-repo commit `5b5ba8f` (Task 2 LOGIN_BUG.md) → FOUND in `git -C pltu-tenayan-full-backup log`
- ResizeObserver suppressor at frontend/public/index.html:49-65 → STILL PRESENT (verified by grep)
- Frontend/backend source files → NOT MODIFIED by this plan (pre-existing diffs are from prior planning sessions; this plan touched only `docs/audit/.work/*` and `docs/audit/LOGIN_BUG.md`)
