# Login Frontend Repro Worksheet

**Status:** automation-not-available: see Operator playbook below.

This file is a structured worksheet capturing the frontend repro **structure**. The agent producing it does not have a headless browser available on this VPS (no chromium/playwright/puppeteer in the running environment), so the OBSERVED rows for steps that require a real browser are marked deferred. The Operator playbook at the bottom lets a human re-verify in roughly 5 minutes.

Read the Login.js component and AuthContext.js — together they define the exact UI flow, state transitions, and network calls. File:line citations are based on:

- `pltu-tenayan-full-backup/frontend/src/pages/Login.js` (228 lines)
- `pltu-tenayan-full-backup/frontend/src/contexts/AuthContext.js` (76 lines)
- `pltu-tenayan-full-backup/frontend/public/index.html` ResizeObserver suppressor at lines 49–65

## UI element inventory

Login form (visible under the **Masuk** tab; tabs at Login.js:78–85):

- Email input — Login.js:93–102, `data-testid="login-email-input"`, `<Input id="login-email" type="email">` bound to `loginEmail` state (Login.js:20).
- Password input — Login.js:107–116, `data-testid="login-password-input"`, bound to `loginPassword` state (Login.js:21). Show/hide toggle Login.js:117–123.
- Submit button — Login.js:126–140, `data-testid="login-submit-btn"`, calls `handleLogin` (Login.js:29–41).

Register form (visible under the **Daftar** tab):

- Name input — Login.js:147–158, `data-testid="register-name-input"`, bound to `regName` state (Login.js:24).
- Email input — Login.js:161–170, `data-testid="register-email-input"`, bound to `regEmail` (Login.js:25).
- Password input — Login.js:173–183, `data-testid="register-password-input"`, bound to `regPassword` (Login.js:26).
- **Role select (Radix combobox) — Login.js:186–197**, `data-testid="register-role-select"`. JSX block:
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
  Imports come from `@/components/ui/select` (Login.js:10) which wraps `@radix-ui/react-select`. State setter `setRegRole` is at Login.js:27 with default `"operator"`.
- Submit button — Login.js:198–212, `data-testid="register-submit-btn"`, calls `handleRegister` (Login.js:43–55).

Note: the role-select component appears **only under the Register tab**, not the Login tab. The reported "ResizeObserver loop completed with undelivered notifications" symptom is therefore tied to the **registration** UI flow, not the login UI flow. The login form has no Radix Select / Popover. This is an important refinement of the reported symptom.

## Repro click path

### Path A1 — UI login (no Radix Select on this surface)

1. Open `http://103.150.197.225:3013/login` in a fresh incognito window with DevTools (Console + Network) open.
2. The "Masuk" tab is selected by default (Login.js:76 `defaultValue="login"`).
3. Type the test admin email into `#login-email`.
4. Type the test admin password into `#login-password`.
5. Click `[data-testid="login-submit-btn"]`.

### Path A2 — UI register (where the ResizeObserver symptom is reported)

1. Open `http://103.150.197.225:3013/login`.
2. Click the "Daftar" tab (`<TabsTrigger value="register">` at Login.js:82).
3. Type a name into `[data-testid="register-name-input"]`.
4. Type a synthetic email into `[data-testid="register-email-input"]` (avoid `.invalid` TLD — the backend rejects it; see register-backend.txt).
5. Type a password into `[data-testid="register-password-input"]`.
6. **Open the role select** at `[data-testid="register-role-select"]` (this is the Radix combobox).
7. Click one of: "Viewer" / "Operator" / "Admin".
8. Click `[data-testid="register-submit-btn"]`.

The Radix Select in step 6 internally uses ResizeObserver to position its popover relative to the trigger. CRA's webpack-dev-server overlay surfaces the loop warning as a runtime error, which is what the user reported. The suppressor in `frontend/public/index.html:49–65` swallows it for `window.error` and `unhandledrejection` events.

## Expected vs observed

### Path A1 — UI login

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open /login | Page renders, no console errors | browser-driven verification deferred to operator |
| 2 | Default tab | "Masuk" tab active | browser-driven verification deferred to operator |
| 3–4 | Type creds | Inputs bind to state, no network call | browser-driven verification deferred to operator |
| 5 | Click submit | `POST /api/auth/login` → 200, `localStorage.token` set, navigate to `/dashboard`, toast "Login berhasil!" | browser-driven verification deferred to operator. **Backend confirmed working: see Path B (login-backend.txt) — POST /api/auth/login with valid creds returns 200 with `{access_token, token_type:"bearer", user}` body.** |

### Path A2 — UI register (with role-select Radix interaction)

| Step | Action | Expected | Observed |
|------|--------|----------|----------|
| 1 | Open /login | Page renders | deferred — operator |
| 2 | Click Daftar tab | Register form visible | deferred — operator |
| 3–5 | Fill name/email/password | State binds | deferred — operator |
| 6 | Open role select | Popover opens with Viewer/Operator/Admin items | deferred — operator. **Hypothesis:** ResizeObserver loop warning fires here in dev (Radix Select + flex layout reflow). The suppressor in index.html:49–65 prevents the CRA dev overlay from surfacing it as a runtime error. Functional behavior should be unaffected. |
| 7 | Pick role | `setRegRole(value)` updates state (Login.js:27) | deferred — operator |
| 8 | Click submit | `POST /api/auth/register` → 200, `localStorage.token` set, navigate to `/dashboard`, toast "Registrasi berhasil!" | deferred — operator. **Backend confirmed working: see Path C (register-backend.txt) — all three roles return 200 when domain is non-reserved; duplicate email returns 400.** |

## Console error excerpt

deferred — Operator playbook. Expected pattern (from prior session intel):

```
ResizeObserver loop completed with undelivered notifications.
```

Source: Radix UI Select / Popover positioning. The suppressor in `frontend/public/index.html:49–65` matches `/^ResizeObserver loop /` and calls `e.stopImmediatePropagation()` on both `window.error` and `window.unhandledrejection` to keep the CRA dev-server overlay from firing.

## Network observations

POST `/api/auth/login` request shape (from AuthContext.js:35):

```jsonc
// Request
POST {REACT_APP_BACKEND_URL}/api/auth/login
Content-Type: application/json
{ "email": "<entered>", "password": "<REDACTED>" }
```

Response (confirmed against live backend, see login-backend.txt):

```jsonc
// 200
{ "access_token": "<REDACTED-JWT>", "token_type": "bearer",
  "user": { "id": "...", "email": "...", "name": "...", "role": "admin", "created_at": "..." } }
// 401 (invalid password)
{ "detail": "Email atau password salah" }
// 422 (malformed body — note: 422, not 400, because Pydantic validates email format before reaching the handler)
{ "detail": [ { "type": "value_error", "loc": ["body","email"], ... } ] }
```

POST `/api/auth/register` request shape (from AuthContext.js:44):

```jsonc
POST {REACT_APP_BACKEND_URL}/api/auth/register
Content-Type: application/json
{ "email": "...", "password": "<REDACTED>", "name": "...", "role": "viewer|operator|admin" }
```

Response (confirmed against live backend, see register-backend.txt):

```jsonc
// 200 — for all three roles with a non-reserved synthetic domain
{ "access_token": "<REDACTED-JWT>", "token_type": "bearer",
  "user": { "id": "...", "email": "...", "name": "...", "role": "...", "created_at": "..." } }
// 400 — duplicate email
{ "detail": "Email sudah terdaftar" }
// 422 — RFC 6761 reserved TLD (.invalid, .test, .local, .example) rejected by Pydantic email-validator
{ "detail": [ { ..., "msg": "value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email." } ] }
```

After login or register, AuthContext writes the token to `localStorage.token` (AuthContext.js:37 / :47) and the next mount calls `GET /api/auth/me` with `Authorization: Bearer <JWT>` (AuthContext.js:18–20).

## Operator playbook

Five-minute manual re-verification on a workstation with a real browser.

### Path A1 (UI login)

1. Open Chrome / Firefox in **Incognito** with DevTools (Console + Network tabs).
2. Visit `http://103.150.197.225:3013/login`.
3. Enter `admin@example.com` and the test password (from `pltu-tenayan-full-backup/memory/test_credentials.md`).
4. Click "Masuk".
5. Record:
   - **Console:** any errors? Capture verbatim.
   - **Network:** filter on `/api/auth/`. The `POST /api/auth/login` row should be 200; `GET /api/auth/me` should follow on the dashboard mount.
   - **Application → Local Storage → http://103.150.197.225:3013:** `token` key should hold the JWT.
   - **Final URL:** should be `/dashboard` (or first protected route).
6. Report any divergence (still on /login? toast error? token missing? me/auth 401 even though login succeeded?).

### Path A2 (UI register, exercises the Radix Select)

1. Same setup.
2. Visit `/login`, click the "Daftar" tab.
3. Fill name / email / password. Use a synthetic email like `qa-probe-<timestamp>@qa-probes-2026.com` (do **not** use a `.invalid` / `.test` / `.local` / `.example` TLD — the backend rejects those with 422).
4. **Open the role dropdown.** Watch the Console.
   - If you see no errors → the suppressor is doing its job for ResizeObserver.
   - If you see "ResizeObserver loop completed with undelivered notifications" → the suppressor is missing or the dev-server overlay is intercepting the event before our handler.
   - If you see a *different* error (TypeError, unhandled promise, focus trap warning, etc.) → that is the real bug Phase 2 should chase. The suppressor only matches `/^ResizeObserver loop /`.
5. Pick a role, click "Daftar".
6. Same recording as Path A1.

### Path B (API login bypass)

```bash
curl -i -X POST http://103.150.197.225:8013/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"<see test_credentials.md>"}'
```

Already captured against this VPS — see `.work/login-backend.txt`. Operator may re-run to confirm.

### Path C (API register bypass)

```bash
curl -i -X POST http://103.150.197.225:8013/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"qa-probe-1@qa-probes-2026.com","password":"throwaway","name":"QA","role":"viewer"}'
```

Already captured — see `.work/register-backend.txt`.

## Key takeaway

The reported "login bug" is *not* a backend authentication failure. The backend returns 200 for valid creds against both `/api/auth/login` and `/api/auth/register`. The ResizeObserver console noise is tied to the **register tab's role-select Radix combobox** (Login.js:186–197), not to the login form. The login form has no Radix Select, no Popover, and no ResizeObserver-using primitive at all. Phase 2 needs to:

1. Confirm via a real browser whether the UI flow actually fails (does login submit, does it navigate, does the token persist) or whether the user's reported "login bug" was actually the register-flow ResizeObserver noise being misattributed.
2. If the UI flow does fail, capture what the *actual* failure is (some network error, some token-write race, some `/api/auth/me` 401, some routing redirect race) — distinct from the benign ResizeObserver console noise.
