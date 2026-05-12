# ADR-004: JWT (Bearer) + bcrypt + Three-Role Authorization Model

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-004.

## Context

EMITS authentication is the gate every operator and admin passes through to reach vessel/barge/trucking/biomassa/PO Batubara/merit-order CRUD, COA reconciliation with umpire workflow, smart-stock and sumber-pemakaian entry, AI Intelligence Agent chat, and report exports. The authentication contract is locked SPEC (CONS-auth-header) and is currently in production on the live VPS with seven users: a mix of `admin`, `operator`, and `viewer` roles.

Phase 1 (plan 01-04) flagged two divergences between the SPEC contract and the live backend behavior:

1. Malformed `/api/auth/*` body returned **422** (FastAPI Pydantic default) but CONS-auth-header locks **400**.
2. Missing `Authorization` header returned **403** but the SPEC text suggested **401**.

Phase 2 (plan 02-02, AUTHFIX-01 + AUTHFIX-02) reconciled both:

- **D-AUTH-01:** A path-scoped `RequestValidationError` handler at `backend/server.py:45-56` re-emits 400 for `/api/auth/*` only. Other routes keep FastAPI's standard 422.
- **D-AUTH-02:** The 403 for missing-header is accepted as the documented contract (FastAPI `HTTPBearer()` default; changing it has cross-route blast radius). 401 is reserved for "invalid/expired token".

The Phase-2 reconciliation is captured in full at `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md`. **5/5 regression tests** in `backend/tests/test_auth_session.py` lock both decisions in place. This ADR promotes IMPLICIT-004 to formal locked status and cross-links the AUTH_CONTRACT decision record.

## Decision

EMITS authentication is **JWT (HS256) bearer tokens** issued by `/api/auth/login`, consumed by every protected route via the `Authorization: Bearer <JWT>` header, with passwords stored at rest as **bcrypt** hashes. Authorization uses **three roles** — `admin`, `operator`, `viewer` — enforced server-side via a `require_role(...)` dependency.

Locked clauses:

- **JWT details:** algorithm `HS256`, expiration **24 hours**, payload `{ user_id, email, role, exp }`. Secret in `JWT_SECRET` env var.
- **Password hashing:** `bcrypt` with library default cost; never log or echo back hashes.
- **Public endpoints (no auth):** `/api/auth/register`, `/api/auth/login`, `/api/`, `/api/health`. Every other endpoint requires the bearer header.
- **Roles & permissions:** `admin` (all CRUD + delete-all + user mgmt), `operator` (CRUD + upload on their data), `viewer` (read-only).
- **HTTP error map (per CONS-auth-header + Phase-2 reconciliation):**
  - **400** — validation failure on `/api/auth/*` body (path-scoped via `auth_validation_handler` per D-AUTH-01).
  - **401** — invalid/expired token (Phase-2 test `test_me_with_expired_token_returns_401`).
  - **403** — role denied OR missing `Authorization` header (FastAPI `HTTPBearer()` default per D-AUTH-02).
  - **404** — resource not found.
  - **500** — internal/AI integration error.
- **Frontend rehydrate path:** `frontend/src/contexts/AuthContext.js:13-32` calls `GET /api/auth/me` on every page load with the stored token; bearer is the only mechanism (no cookies).

## Consequences

**Positive:**

- Stateless — no server-side session store; horizontal-scale-ready (not currently needed; single VPS).
- Frontend AuthContext rehydrate is a pure GET-with-bearer; works identically dev / prod / VPS.
- Path-scoped 400 remap (D-AUTH-01) keeps non-auth routes' standard 422 untouched — zero blast radius for vessels/COA/etc.
- Three-role model maps cleanly onto the operational reality at PLTU Tenayan (operator = data entry; admin = upload + destructive ops; viewer = read-only stakeholders).
- bcrypt at library default cost is fine for the user count (7 users, no high-frequency auth churn).

**Negative / accepted tradeoffs:**

- 24h expiration means a stolen token is valid for up to 24h. No refresh-token rotation today; deferred to v2 if multi-tenant lands.
- 403-vs-401-on-missing-header divergence (D-AUTH-02) is permanently documented rather than fixed — overriding `HTTPBearer` security default for 401 has cross-route blast radius. Documented in API_REFERENCE.md (Phase-3 plan 03 follow-up).
- `JWT_SECRET` must be set in env; rotation requires invalidating all live tokens (deferred to v2 ops tooling).
- No 2FA / SSO; single-tenant scope assumes plant-internal trust model.
- 422-vs-400 path-scoping introduces a single conditional in the validation handler — minor cognitive cost but tested by `test_login_with_malformed_body_returns_400`.

## Alternatives Considered

- **Session cookies + CSRF tokens** — rejected. `REACT_APP_BACKEND_URL` may point at a different origin than the frontend dev server in some setups; bearer tokens sidestep the CORS-credentials dance. Cookie-based auth would force `withCredentials: true` everywhere and additional CORS config.
- **OAuth2 / external IdP (Keycloak / Auth0)** — rejected for v1. Single-plant scope, no SSO requirement; the user count is 7. v2 if multi-tenant lands.
- **API keys (per-user static)** — rejected. No role granularity, no expiration, awkward UX for human operators (they would need to paste a key into the login UI on every device).
- **JWT with RS256 (asymmetric)** — rejected for v1. HS256 + a single shared secret is operationally simpler at single-host scale; RS256 only matters when verifiers and signers are separate services.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-004 row (line 90: "Auth contract (LOCKED, implicit/inherited): JWT bearer; three roles admin/operator/viewer; bcrypt password hashing; auth header Authorization: Bearer <JWT>; HTTP errors 400/401/403/404/500 per SPEC").
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/backend/server.py:15-16` — `import jwt` + `import bcrypt`
  - `pltu-tenayan-full-backup/backend/server.py:45-56` — `auth_validation_handler` (D-AUTH-01: 422→400 remap, scoped to `/api/auth/*`)
  - `pltu-tenayan-full-backup/backend/server.py:577` — `def create_token(user_id: str, email: str, role: str) -> str:`
  - `pltu-tenayan-full-backup/backend/server.py:586-597` — `get_current_user` (decodes JWT, raises 401 on `ExpiredSignatureError`/`InvalidTokenError`)
  - `pltu-tenayan-full-backup/backend/server.py:599-604` — `def require_role(allowed_roles: List[str])` (raises 403 on role denied)
  - `pltu-tenayan-full-backup/backend/server.py:571-575` — `hash_password` + `verify_password` (bcrypt)
  - `pltu-tenayan-full-backup/frontend/src/contexts/AuthContext.js:13-32` — rehydrate path on page load
- **Related constraints:** `.planning/intel/constraints.md` → CONS-auth-header (the locked SPEC contract this ADR formalizes).
- **Sibling docs:**
  - `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` — Phase-2 reconciliation record (D-AUTH-01, D-AUTH-02, 5/5 regression tests)
  - `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG_RESOLUTION.md` — Phase-1 / Phase-2 login-bug investigation thread
  - `pltu-tenayan-full-backup/backend/tests/test_auth_session.py` — locking tests (`test_login_with_malformed_body_returns_400`, `test_me_with_expired_token_returns_401`, `test_me_without_token_returns_403`, etc.)
