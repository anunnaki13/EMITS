# ADR-006: /api/* Backend Route Prefix + REACT_APP_BACKEND_URL Frontend Base

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-006.

## Context

EMITS deploys as one VPS host that serves both the React static build and the FastAPI backend. The React build occupies `/` (and arbitrary `/<route>` paths via React Router 7's client-side routing); the backend must own a non-overlapping URL space so the frontend's deep-link routes never collide with backend endpoints.

The convention — locked since project genesis — is that **every** backend HTTP route lives under `/api/`. The frontend resolves its API base URL from the `REACT_APP_BACKEND_URL` build-time env var (CRA convention: `process.env.REACT_APP_*` is inlined at build). Production points at `http://103.150.197.225:8013`; local dev points at `http://localhost:8013`. Behind nginx in production, the same `/api/*` prefix is used to reverse-proxy to uvicorn.

This ADR locks both halves of the contract — the backend prefix AND the frontend env-var name — so future plans cite it directly. CONS-api-base is the locked SPEC source.

## Decision

**Backend:** All HTTP routes the EMITS backend exposes are mounted under the `/api` prefix. Concretely, every endpoint is registered on a single `APIRouter(prefix="/api")` instance, and that router is included on the `FastAPI()` app. There are no exceptions — health, auth, AI, every CRUD verb, every export route — all under `/api/`.

**Frontend:** The React frontend resolves its base URL exclusively via the `REACT_APP_BACKEND_URL` build-time env var. Code reads `process.env.REACT_APP_BACKEND_URL` and concatenates `/api/<resource>` paths against it. There is no fallback to `window.location.origin` in production code paths.

Locked clauses:

- **Prefix:** literal `/api` (no `/api/v1` versioning in v1; no per-resource prefixes like `/api/coa-reconciliation/v2`).
- **Env var name:** `REACT_APP_BACKEND_URL` (CRA inlining convention; renaming would break every deployment env file).
- **Production base:** `http://103.150.197.225:8013` (or fronted by nginx with the same `/api/*` rewrite when applicable).
- **Dev base:** `http://localhost:8013` (uvicorn default test port for the project).
- **Public, no-auth endpoints under the prefix:** `/api/`, `/api/health`, `/api/auth/register`, `/api/auth/login` (per CONS-auth-header). All other `/api/*` routes require Bearer JWT (ADR-004).

## Consequences

**Positive:**

- Single-host deployment is collision-free: React Router owns `/<anything-else>` and FastAPI owns `/api/*`. nginx reverse-proxy config is one rule.
- API surface is grep-able: any `api_router.<verb>("/...")` line in `server.py` is a public route; nothing leaks from another router.
- Frontend dev/prod parity is one env var change in `frontend/.env`; no per-environment code branching.
- nginx config is portable: rewriting `/api/*` to backend port is a one-liner regardless of host.
- API_REFERENCE generation (Phase 3, plan 03; D-04, D-06) can scrape `/openapi.json` and assume every documented path starts with `/api/`.

**Negative / accepted tradeoffs:**

- No URL versioning — when v2 of an endpoint is needed, the choice is either body-shape evolution with a feature flag, a sibling endpoint (`/api/coa-reconciliation-v2`), or eventually adopting a `/api/v1`/`/api/v2` split in a future ADR. Today there is no v2 surface, so this is hypothetical.
- `REACT_APP_BACKEND_URL` is build-time, not runtime — switching base requires a fresh `yarn build`. For the single-host VPS deployment this is fine; runtime configuration would require a separate `/config.json` fetch on app load (deferred until multi-environment runtime ever lands).
- The prefix is hardcoded at `APIRouter(prefix="/api")` — refactoring to per-router files (DEBT-02) must preserve the prefix at the include site, not redeclare it on each sub-router.

## Alternatives Considered

- **No prefix (mount routes directly under `/`)** — rejected. Same-host serving of `/` for the React build would collide with backend routes; the frontend would need a separate origin for the API, and CORS + the frontend dev-vs-prod base-URL story would get complicated.
- **`/api/v1` prefix from day one** — rejected. Single-version v1 today; adding `/v1` now reserves the namespace but creates the obligation of a parallel `/v2` whenever any breaking change happens. Deferred — when the first breaking change is needed, a new ADR can introduce versioning at that time.
- **Per-resource prefixes (`/vessels/api`, `/coa/api`, …)** — rejected. Defeats the single-prefix grep-ability; awkward nginx config; no benefit.
- **nginx-rewrite-only (backend mounts at `/`, nginx rewrites `/api/*` → `<backend>/`)** — rejected. Backend ownership of the prefix is more portable than relying on a reverse-proxy rule that has to ship with the deployment; `uvicorn server:app` runs identically with or without nginx.
- **Runtime base via `/config.json` fetch on boot** — rejected for v1. CRA's build-time inlining is simpler and matches the single-host deployment reality; runtime config is a multi-environment concern that hasn't materialized yet.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-006 row (line 91: "Routing (LOCKED, implicit/inherited): All HTTP routes under `/api/*`; frontend resolves base via `REACT_APP_BACKEND_URL`. Per IMPLICIT-006 + CONS-api-base.").
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/backend/server.py:60` — `api_router = APIRouter(prefix="/api")`
  - `pltu-tenayan-full-backup/backend/server.py:608` — `@api_router.post("/auth/register", ...)` (sample endpoint mount)
  - `pltu-tenayan-full-backup/backend/server.py:685` — `@api_router.get("/vessels")` (CRUD list endpoint mount)
  - `pltu-tenayan-full-backup/backend/server.py:2619` — `@api_router.post("/ai/query")` (AI endpoint mount)
  - `pltu-tenayan-full-backup/backend/server.py:2714` — `@api_router.get("/ai/settings")`
  - `pltu-tenayan-full-backup/frontend/.env.example` — declares `REACT_APP_BACKEND_URL` as required env var
  - `pltu-tenayan-full-backup/frontend/.env` — production-shaped concrete value for the live deployment
  - `pltu-tenayan-full-backup/frontend/src/contexts/AuthContext.js:6` — `const API_URL = process.env.REACT_APP_BACKEND_URL;` (single source of truth for axios base)
- **Related constraints:** `.planning/intel/constraints.md` → CONS-api-base (the locked SPEC contract this ADR formalizes).
- **Sibling docs:** `pltu-tenayan-full-backup/API_REFERENCE.md` (consumes the prefix in every endpoint table), `pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md` (nginx reverse-proxy rule for `/api/*`).
