# Login + Register Bug Repro

**Live frontend:** http://103.150.197.225:3013
**Live backend:** http://103.150.197.225:8013
**Captured:** 2026-05-10T11:40:00Z
**Scope:** Phase 1 (AUDIT-04) — read-only repro. Fix lives in Phase 2 (AUTHFIX-01..04).

## Symptom (as reported)

Runtime error in the browser console when interacting with the role-select dropdown on the Login page:

> ResizeObserver loop completed with undelivered notifications.

A benign suppressor was applied at `frontend/public/index.html` (lines 49–65) as a temporary mitigation. The suppressor masks the console error but does not address the underlying interaction. Registration flow has not been validated end-to-end.

**Refinement from this repro:** the role-select Radix combobox lives on the **register tab**, not the login tab. The login form (Login.js:90–141) is built only from `Input` and `Button` primitives — it has no Radix Select, Popover, or other ResizeObserver-using element. The reported "login bug" is therefore most likely register-flow noise being attributed to login, OR a separate UI failure on the login flow that was conflated with the register-tab console error. Path B below proves the backend login endpoint itself returns 200, so any remaining UI failure is purely frontend-side.

## Reproduction

### Path A — Existing user login via UI

Preconditions:

- Live frontend reachable at `http://103.150.197.225:3013/login`.
- Test credentials from `pltu-tenayan-full-backup/memory/test_credentials.md` (gitignored — credentials NOT inlined here).

Steps:

1. Open `http://103.150.197.225:3013/login` in a fresh incognito window with DevTools open (Console + Network tabs).
2. The "Masuk" tab is selected by default (`<Tabs defaultValue="login">` at Login.js:76).
3. Enter the test admin email in `[data-testid="login-email-input"]` (Login.js:93–102).
4. Enter the test admin password in `[data-testid="login-password-input"]` (Login.js:107–116). Note: the login form has **no role select** — the Radix Select component appears only on the register tab.
5. Click `[data-testid="login-submit-btn"]` (Login.js:126–140), which invokes `handleLogin` at Login.js:29–41 → `AuthContext.login` at AuthContext.js:34–41.

Expected:

- Console: no errors.
- Network: `POST /api/auth/login` → 200 with body `{ access_token, token_type: "bearer", user: { id, email, name, role, created_at } }` (per CONS-auth-header and the `AuthContext.login` consumer at AuthContext.js:36 which reads `access_token`).
- localStorage: token written under key `token` (AuthContext.js:37 `localStorage.setItem("token", access_token)`).
- Navigation: `navigate("/dashboard")` (Login.js:35) — redirect to /dashboard.
- On next mount: `GET /api/auth/me` with `Authorization: Bearer <JWT>` (AuthContext.js:18–20) → 200 with same user.

Observed:

| Step | Observed |
|------|----------|
| 1 (open /login) | browser-driven verification deferred to operator (no headless browser available on this VPS) |
| 2 (default tab) | deferred — operator |
| 3–4 (type creds) | deferred — operator |
| 5 (click submit) | **Backend confirmed working: see Path B — `POST /api/auth/login` with valid creds returns 200 with the documented body shape.** UI-side outcome (toast, navigate, localStorage write) deferred to operator playbook. |

See "Operator playbook" at the bottom of this document for the 5-minute manual re-verification.

### Path B — Existing user login via API (UI bypass)

Steps:

1. POST `http://103.150.197.225:8013/api/auth/login` with valid creds.
2. POST same with valid email + invalid password.
3. POST same with malformed body (missing password, invalid email).

Expected per CONS-auth-header:

- Step 1 → 200 with `{ access_token, token_type, user }`
- Step 2 → 401
- Step 3 → 400 (validation)

Observed (from `.work/login-backend.txt`, JWT and password redacted at capture time):

| Step | Status | Body shape |
|------|--------|------------|
| 1 (valid creds, VPS endpoint) | **HTTP 200** | `{ "access_token": "<REDACTED-JWT>", "token_type": "bearer", "user": { "id": "...", "email": "admin@example.com", "name": "Admin", "role": "admin", "created_at": "2026-01-28T21:11:48.388562+00:00" } }` |
| 1' (valid creds, localhost:8013 — same backend, sanity check) | **HTTP 200** | identical shape |
| 2 (invalid password) | **HTTP 401** | `{ "detail": "Email atau password salah" }` |
| 3 (malformed body) | **HTTP 422** | `{ "detail": [ { "type": "value_error", "loc": ["body","email"], "msg": "value is not a valid email address: An email address must have an @-sign.", ... }, { "type": "missing", "loc": ["body","password"], "msg": "Field required", ... } ] }` |

Divergence:

- Steps 1 and 2 match expected (200 / 401) and conform to CONS-auth-header.
- **Step 3 returns 422, not 400.** This is FastAPI's default Pydantic-validation status — Pydantic rejects the malformed body before the handler runs. This is consistent with CONS-auth-header at the semantic level ("validation failure" → 4xx) but the specific status code differs from the locked spec ("400 validation"). Phase 2 should decide whether to (a) add a custom `RequestValidationError` handler that re-emits 400, (b) update CONS-auth-header to align with FastAPI's 422 default, or (c) accept the divergence and document it. **No login functionality is affected by this discrepancy** — clients that distinguish 4xx-as-a-class are unaffected.

### Path C — New user registration via API

Steps:

1. POST `http://103.150.197.225:8013/api/auth/register` with `role=admin` and a synthetic email.
2. Same with `role=operator`.
3. Same with `role=viewer`.
4. Re-submit step 1 to confirm duplicate-email handling.

Expected:

- Each of steps 1–3 → 200 (or 201) with the created user, per CONS-auth-header.
- Step 4 (duplicate email) → 4xx (not 500).
- Side-effect: a row in the `users` collection per successful submission.

First probe round (`.invalid` TLD per RFC 6761) — observed (from `.work/register-backend.txt`):

| Step | Status | Body |
|------|--------|------|
| admin (`audit-probe-admin-...@example.invalid`) | **HTTP 422** | `{ "detail": [ { ..., "msg": "value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email." } ] }` |
| operator (...`@example.invalid`) | **HTTP 422** | same shape |
| viewer (...`@example.invalid`) | **HTTP 422** | same shape |

**Discovery:** Pydantic's `email-validator` library (used transitively by `EmailStr`) explicitly rejects RFC 6761 reserved TLDs (`.invalid`, `.test`, `.local`, `.example`). The plan deliberately specified `.invalid` for safety; the live validator is stricter. **No documents were inserted from this round.** Phase 2 should decide whether to (a) override `email-validator`'s reserved-TLD check (allow `.invalid` + `.test` for test fixtures), or (b) ensure regression-test fixtures use non-reserved synthetic domains.

Second probe round (non-reserved synthetic domain `audit-probes-2026.com`) — observed:

| Step | Status | Body shape |
|------|--------|------------|
| admin (`audit-probe-admin-1778413168@audit-probes-2026.com`) | **HTTP 200** | `{ "access_token": "<REDACTED-JWT>", "token_type": "bearer", "user": { "id": "f1a6c24d-...", "email": "...", "name": "Audit Probe admin", "role": "admin", "created_at": "2026-05-10T11:39:28..." } }` |
| operator | **HTTP 200** | same shape, `role: "operator"`, `id: "f658bd62-..."` |
| viewer | **HTTP 200** | same shape, `role: "viewer"`, `id: "d713d9b1-..."` |
| duplicate (re-submit admin) | **HTTP 400** | `{ "detail": "Email sudah terdaftar" }` |

Divergence:

- Happy-path register: matches expected (200 with `{access_token, user}` shape) for all three roles. No divergence at the API layer.
- Duplicate email: returns 400 (matches expected — not 500).
- The shape is identical to login (`/api/auth/register` returns the same `{access_token, token_type, user}` envelope as `/api/auth/login`). This is consistent with `AuthContext.register` at AuthContext.js:43–50 which reads `access_token` and `user` and writes the token to localStorage immediately, mirroring the login flow.

Side-effect note:

Three synthetic users with email prefix `audit-probe-` and domain `audit-probes-2026.com` were inserted into the live `users` collection during Path C round 2:

- `audit-probe-admin-1778413168@audit-probes-2026.com` (id: `f1a6c24d-2de8-4e93-8487-ca4f405bf880`, role admin)
- `audit-probe-operator-1778413168@audit-probes-2026.com` (id: `f658bd62-cfad-424f-a588-e0663d86a797`, role operator)
- `audit-probe-viewer-1778413168@audit-probes-2026.com` (id: `d713d9b1-502e-4551-a525-5ec6fc8b60be`, role viewer)

These are documented in `.work/register-backend.txt` under `--- CLEANUP-NOTE (revised) ---`. Phase 2 may remove them as part of regression-test setup; Phase 5 may also clean them up. Cleanup filter:

```js
db.users.deleteMany({ email: /^audit-probe-/ })
```

The `.invalid` round inserted nothing (all 422).

## Suspected component

**Primary suspect:** Radix-based `<Select>` for the register-form role picker — `frontend/src/pages/Login.js:186–197`.

Cited evidence:

- Import (Login.js:10):
  ```jsx
  import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
  ```
  This wraps `@radix-ui/react-select`. Radix Select internally uses `ResizeObserver` to position the popover relative to the trigger.
- JSX block (Login.js:186–197) inside the register form's `<TabsContent value="register">`:
  ```jsx
  <Select value={regRole} onValueChange={setRegRole}>
    <SelectTrigger ... data-testid="register-role-select">
      <SelectValue placeholder="Pilih role" />
    </SelectTrigger>
    <SelectContent ...>
      <SelectItem value="viewer">Viewer</SelectItem>
      <SelectItem value="operator">Operator</SelectItem>
      <SelectItem value="admin">Admin</SelectItem>
    </SelectContent>
  </Select>
  ```
- State setter `setRegRole` (Login.js:27) with default `"operator"`.
- Read in submit handler at Login.js:47 — `await register(regEmail, regPassword, regName, regRole)` — i.e., the value flows into `AuthContext.register` (AuthContext.js:43–50).

Mechanism hypothesis (one paragraph, plain prose):

Radix Select internally observes its trigger's size with ResizeObserver to position the popover. When the popover repositions in the same frame as a layout change (e.g., the page's `min-h-screen` flex layout reflowing on focus, or a tabs-content remount when switching from "Masuk" to "Daftar"), the observer fires recursively and the browser logs the loop warning. The warning is benign for rendering but becomes user-visible because CRA's webpack-dev-server overlay surfaces *any* `window.error` event as a fullscreen runtime error. The suppressor at `index.html:49–65` catches the `error` and `unhandledrejection` events whose message matches `/^ResizeObserver loop /` and calls `e.stopImmediatePropagation()` to prevent the overlay from firing. Phase 2 must distinguish (a) benign console noise that happens to coincide with a form-submit failure caused by a separate root cause, vs (b) a true error-boundary unwind that aborts submit. The Path B + Path C API repros isolate (a): the backend returns 200 for valid login creds and 200 for register across all three roles, so any frontend failure is a UI-only error-boundary issue and not an auth issue.

**Secondary suspects (rule out or confirm in Phase 2):**

- `AuthContext.login` error handling — `frontend/src/contexts/AuthContext.js:34–41`. `login` does `localStorage.setItem` then `setToken` then `setUser` synchronously inside the same async function. The caller in Login.js:33 awaits `login(...)` before navigating, so the navigate happens after state update. No obvious bug, but Phase 2 should confirm the React 19 batched-update behavior does not surface the navigation before the new token is reflected in the AuthContext consumers (e.g., `ProtectedRoute`).
- `AuthContext` initial-mount race — `AuthContext.js:13–32`. On mount, `initAuth` reads `localStorage.getItem("token")` and calls `GET /api/auth/me`. If the token is absent the user state stays `null` and `loading` flips to `false`. There is no guard against the case where login fires *while* `initAuth` is still in flight. Phase 2 should rule this out (or document it as a non-issue if the login form is only mounted after `loading === false`).
- `frontend/public/index.html:49–65` ResizeObserver suppressor — verify in Phase 2 whether the regex `/^ResizeObserver loop /` is too narrow (misses some browser variants) or too broad (swallows other errors). Both `error` and `unhandledrejection` paths are handled.

## Mitigation status

- `frontend/public/index.html` lines 49–65 contain a benign suppressor that swallows the ResizeObserver console error. This was applied as a temporary mitigation and is **NOT** a Phase-2 substitute. Phase 2 should evaluate whether the suppressor stays after the underlying interaction is fixed (e.g., switching the role picker to a non-Radix component, or upgrading `@radix-ui/react-select` to a version that does not trigger the loop on Tabs-content remount). Verbatim suppressor block:
  ```html
  <script>
      // Suppress benign "ResizeObserver loop completed with undelivered notifications"
      // emitted by Radix UI primitives (Select, Popover) during dev. Functionality is
      // unaffected; CRA's webpack-dev-server overlay surfaces it as a runtime error.
      (function () {
          var RO_RE = /^ResizeObserver loop /;
          window.addEventListener('error', function (e) {
              if (e && e.message && RO_RE.test(e.message)) {
                  e.stopImmediatePropagation();
              }
          });
          window.addEventListener('unhandledrejection', function (e) {
              var msg = e && e.reason && (e.reason.message || String(e.reason));
              if (msg && RO_RE.test(msg)) e.stopImmediatePropagation();
          });
      })();
  </script>
  ```

## Operator playbook (5-minute manual re-verification)

Reproduce Path A with a real browser. Expected console state, expected network state, and expected localStorage state are listed under "Path A → Expected". If any row was marked "browser-driven verification deferred to operator", the operator fills it in and reports back. Pure check; no fixes.

### Steps

1. Open Chrome / Firefox in **Incognito** with DevTools open (Console + Network).
2. Visit `http://103.150.197.225:3013/login`.
3. Enter `admin@example.com` and the test password from `pltu-tenayan-full-backup/memory/test_credentials.md`.
4. Click **Masuk**.
5. Record:
   - **Console:** any errors? Capture verbatim.
   - **Network:** filter on `/api/auth/`. `POST /api/auth/login` should be 200; `GET /api/auth/me` should follow on dashboard mount.
   - **Application → Local Storage → http://103.150.197.225:3013:** `token` key should hold a JWT.
   - **Final URL:** should be `/dashboard` (or first protected route).
6. Now switch to the **Daftar** tab and open the role select. Watch the Console while opening the dropdown.
   - No error → the suppressor is doing its job.
   - "ResizeObserver loop completed with undelivered notifications" → the suppressor is missing or the dev-server overlay is intercepting before our handler.
   - A *different* error → that is the real bug for Phase 2.
7. Report any divergence.

## Methodology

- Backend repros (Paths B and C) captured via `curl` from this VPS into `pltu-tenayan-full-backup/docs/audit/.work/login-backend.txt` and `register-backend.txt`. JWTs (regex `eyJ[A-Za-z0-9._-]{20,}`) and the cleartext admin password were redacted at capture time, with grep confirming no residual matches.
- Frontend repro structure (Path A) captured into `.work/login-frontend-evidence.md` as a worksheet because no headless browser is available on this VPS; OBSERVED rows are deferred to the Operator playbook.
- No source files under `frontend/` or `backend/` were modified by this plan. The pre-existing `ResizeObserver` suppressor at `frontend/public/index.html:49–65` was left untouched.
- This document does NOT propose code changes. Phase 2 (AUTHFIX-01..04) owns the fix.
