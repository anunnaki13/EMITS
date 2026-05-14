<!-- BEGIN HAND-CURATED: header -->
# API Reference

Live FastAPI surface for the **PLTU Tenayan Fuel Management System**. The
endpoint inventory below is generated from `/openapi.json` by
`scripts/regenerate_api_reference.py` — re-run after any backend route change
and `git diff --exit-code API_REFERENCE.md` will surface drift.

Hand-curated narrative sections live between
`<!-- BEGIN HAND-CURATED: <name> -->` markers and are preserved across
regeneration. Sections in this file:

- Auth Contract — operational restatement of ADR-004
- Pagination Contract — operational restatement of ADR-008
- Error Code Map — semantic 4xx/5xx mapping per CONS-auth-header
- Endpoint Inventory — auto-generated from `/openapi.json`
- Per-Module Call Examples — hand-curated curl recipes (env-var sourced)

Source-of-truth for the live schema: the deployed FastAPI app exposes
`/openapi.json` on the same port as the API surface. Fetch order: env var
`OPENAPI_URL`, then `http://localhost:8013`, then `http://103.150.197.225:8013`.

> Note: the previous hand-edited 778-line API_REFERENCE.md (which inlined
> the admin password literal and was on the credential-scanner exemption
> list) was replaced by this regenerator on 2026-05-10 (Phase-3 plan 03-03).
<!-- END HAND-CURATED: header -->

<!-- BEGIN HAND-CURATED: auth -->
## Auth Contract

See `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md` (locked
2026-05-10) for the architectural decision; this section restates the
operational contract for API consumers and points at
`docs/audit/AUTH_CONTRACT.md` for the Phase-2 reconciliation record
(D-AUTH-01 422→400 remap; D-AUTH-02 403-on-missing-Authorization).

- **Token type:** JWT (HS256), issued by `POST /api/auth/login`.
- **Header:** `Authorization: Bearer <JWT>` on every protected endpoint.
- **Roles:** `admin`, `operator`, `viewer`. Role enforcement is server-side
  via the `require_role(...)` dependency in `backend/server.py`. FastAPI
  does NOT surface `require_role()` in `/openapi.json`, so the auto-generated
  table marks every secured endpoint as `Bearer`. Per-role authorization is
  cross-walked module-by-module in `docs/audit/AUTH_CONTRACT.md`.
- **Login error mapping (D-AUTH-01):** invalid credentials → `401`;
  malformed body on `/api/auth/*` → `400` (remapped from FastAPI's default
  `422` to satisfy the historical contract). Non-auth routes keep `422`.
- **Missing Authorization header (D-AUTH-02):** HTTPBearer dependency
  defaults to `403` (NOT `401`). Documented and accepted as the contract.
- **Public endpoints (no Bearer required):** `/api/auth/login`,
  `/api/auth/register`, `/api/`, `/api/health`. All other endpoints require
  an Authorization header.

### Per-role module cross-walk

The following table cross-walks every backend module to its required role for
each operation class (`R` = read / list / get-by-id, `W` = write / create /
update, `D` = delete-by-id, `D*` = collection-level destructive delete-all,
`U` = upload). Roles use first-letter shorthand: `A` = admin, `O` = operator,
`V` = viewer. Source-of-truth is the `require_role([...])` decorators in
`backend/server.py`; for module-by-module narrative, see
`docs/audit/AUTH_CONTRACT.md`.

| Module                  | R     | W     | D     | D\*  | U     |
|-------------------------|-------|-------|-------|------|-------|
| auth (login/me/register)| any   | n/a   | n/a   | n/a  | n/a   |
| users                   | A     | n/a   | n/a   | n/a  | n/a   |
| vessels                 | A,O,V | A,O   | A     | A    | A,O   |
| barges                  | A,O,V | A,O   | A     | A    | A,O   |
| trucking                | A,O,V | A,O   | A     | A    | A,O   |
| biomassa                | A,O,V | A,O   | A     | A    | A,O   |
| po-batubara             | A,O,V | A,O   | A     | A    | A,O   |
| merit-order             | A,O,V | A,O   | A     | A    | A,O   |
| smart-stock             | A,O,V | A,O   | A     | A    | A,O   |
| sumber-pemakaian        | A,O,V | A,O   | n/a   | A    | A,O   |
| coa-reconciliation      | A,O,V | A,O   | n/a   | A    | A,O   |
| coa-reconciliation/manual+umpire | A,O,V | A,O | n/a | n/a  | n/a |
| settings/coa            | A,O,V | A     | n/a   | n/a  | n/a   |
| dashboard               | A,O,V | n/a   | n/a   | n/a  | n/a   |
| ai/* (sessions/query/quick) | A,O,V | A,O,V | A | n/a  | n/a   |
| ai/settings             | A,O,V | A     | n/a   | n/a  | n/a   |
| smart-blending          | A,O,V | A,O,V | n/a   | n/a  | n/a   |

Notes:

- "any" auth class applies only to the public endpoints listed above; every
  role-marked cell here implies `Authorization: Bearer <JWT>` is required.
- The Phase-2 hardening pass confirmed each cell against
  `backend/server.py` directly. If a cell drifts (a `require_role` is added
  or removed), regenerate this file and update the table — the auto-generated
  table below will not reflect the change because FastAPI does not surface
  `require_role()` in `/openapi.json`.
- Viewer-tier reads are non-mutating but include `dashboard/advanced` and
  the entire `coa-reconciliation` read surface — viewers can audit but not
  edit.
- `/api/users` is admin-only (the only module-level R restriction). All
  other reads are tri-role.
- Collection-level deletes (`DELETE /api/<collection>`) are admin-only AND
  destructive — they truncate every record under the collection. Treat as
  break-glass operations; the spot-check log
  (`docs/audit/API_REFERENCE_SPOTCHECK.md`) marks them `verified: schema-only`
  to keep them out of the live probe set.

### Token lifetime + refresh

- **Lifetime:** 24h (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440` in
  `backend/server.py`). Tokens carry `sub` (email), `role`, and `exp`.
- **No refresh endpoint:** clients re-login on expiry. The frontend's
  `AuthContext` handles 401 → redirect-to-login transparently; see
  `frontend/src/context/AuthContext.tsx`.
- **JWT secret:** `JWT_SECRET` env var on backend; HS256. Never embedded in
  client code. Rotation = restart backend + force re-login (acceptable for
  the current single-tenant deployment; a refresh-token model is deferred to
  Phase 6 if multi-tenant becomes a requirement).
<!-- END HAND-CURATED: auth -->

<!-- BEGIN HAND-CURATED: pagination -->
## Pagination Contract

See `.planning/decisions/ADR-008-pagination-shape.md` for the locked envelope
(CONS-pagination-shape).

Every paginated list endpoint returns:

```json
{
  "items": [ /* records */ ],
  "total": 461,
  "page": 1,
  "page_size": 50,
  "total_pages": 10
}
```

- **Query params:** `page` (default `1`), `page_size` (default `50`).
- **Operational caps:** most list endpoints `page_size <= 500`. The
  smart-stock list (`GET /api/smart-stock`) caps at `limit=50000`.
- **Frontend contract:** read `response.data.items`; never assume the
  response is a bare JSON array.
- **Counting:** `total` is the unfiltered-by-page count; `total_pages` is
  `ceil(total / page_size)`.

### Per-endpoint pagination cap matrix

| List endpoint                          | Default page_size | Max page_size | Notes |
|----------------------------------------|-------------------|---------------|-------|
| `GET /api/vessels`                     | 50                | 500           | filtered by year/month query params |
| `GET /api/barges`                      | 50                | 500           | filtered by vessel_id, year, month |
| `GET /api/trucking`                    | 50                | 500           | filtered by date range |
| `GET /api/biomassa`                    | 50                | 500           | filtered by date range, supplier |
| `GET /api/po-batubara`                 | 50                | 500           | filtered by year, status |
| `GET /api/merit-order`                 | 50                | 500           | filtered by period |
| `GET /api/coa-reconciliation`          | 50                | 500           | filtered by shipment, year |
| `GET /api/sumber-pemakaian`            | 50                | 500           | filtered by date range, source |
| `GET /api/smart-stock`                 | uses `limit` not `page_size` | `limit=50000` | NOT envelope-shaped (legacy bare-array contract; see ADR-008 for the documented exception) |
| `GET /api/users`                       | bare list         | n/a           | admin-only; small N, returns plain array |
| `GET /api/po-batubara/years`           | bare list         | n/a           | helper endpoint, returns `["2024","2025",...]` |
| `GET /api/merit-order/periods`         | bare list         | n/a           | helper endpoint, returns period strings |
| `GET /api/suppliers`                   | bare list         | n/a           | helper endpoint, returns supplier names |
| `GET /api/coa-reconciliation/kpis`     | not paginated     | n/a           | dashboard summary endpoint |
| `GET /api/dashboard/stats`             | not paginated     | n/a           | dashboard summary |
| `GET /api/dashboard/advanced`          | not paginated     | n/a           | extended dashboard summary |

### Frontend integration recipe

```typescript
// React + axios pattern (see frontend/src/services/api.ts)
const { data } = await api.get('/api/vessels', {
  params: { page: 1, page_size: 50, year: 2025 }
});
// data.items is the array; data.total is the unfiltered count
setRows(data.items);
setTotalPages(data.total_pages);
```

Common bug to avoid: treating the response as a bare array. The frontend
codebase had a multi-week incident in Phase-2 where vessels-list rendering
broke because `response.data` was assumed to be `Array<Vessel>` when it had
already migrated to the envelope shape. Always destructure
`{ items, total, page, page_size, total_pages }`.
<!-- END HAND-CURATED: pagination -->

<!-- BEGIN HAND-CURATED: errors -->
## Error Code Map

See `.planning/intel/constraints.md` → CONS-auth-header for the locked
semantic mapping. The `/api/auth/*` surface returns `400` for malformed
request bodies (Phase-2 D-AUTH-01 remap from FastAPI's default `422`);
non-auth routes keep the FastAPI `422` default.

| Code | Used by                                   | Semantic meaning |
|------|-------------------------------------------|-------------------------------------------------------------|
| 200  | all successful reads/writes               | success (request accepted, response body present)            |
| 400  | `/api/auth/*`                             | malformed request body (validation failure; D-AUTH-01)       |
| 401  | `/api/auth/login`, `/api/auth/me`         | invalid credentials OR invalid/expired token                 |
| 403  | any protected endpoint                    | role denied OR missing Authorization header (HTTPBearer; D-AUTH-02) |
| 404  | `*/{id}` lookups                          | record not found                                             |
| 422  | non-auth `POST/PUT/PATCH` endpoints       | malformed request body (FastAPI default — backwards compat)  |
| 500  | AI endpoints / LLM-integration paths      | internal error (e.g., `BudgetExceededError`, upstream LLM)   |

See `docs/audit/AUTH_CONTRACT.md` for the full Phase-2 reconciliation.

### Why two different "malformed body" codes?

`/api/auth/*` returns `400` and every other route returns `422` for the same
class of error (validation failure on `requestBody`). This split is
intentional and locked under D-AUTH-01:

- **Historical contract:** the frontend's auth flow was originally written
  against an early backend that returned `400` for malformed login bodies.
  When FastAPI was upgraded mid-development, the default became `422`, and
  three weeks of intermittent "Login failed but no error shown" tickets
  followed. Phase-2 added a custom `RequestValidationError` handler scoped
  to the `/api/auth/*` prefix that re-maps `422 → 400` to restore the
  original contract.
- **Non-auth routes:** kept on `422` because the frontend's data-entry forms
  already handle `422` correctly (the validation error payload includes
  field-level detail FastAPI emits, which the form layer surfaces in
  inline error UI).
- **Cost of unifying:** rewriting every form to also accept `400` is in
  scope but not needed for Phase-3. Tracked as a Phase-6 cleanup if the
  inconsistency causes drift.

### Body shape per error code

```json
// 400 (auth) — minimal shape, frontend reads .detail as a single message
{ "detail": "Email tidak terdaftar" }

// 422 (non-auth) — FastAPI default, frontend reads .detail as an array
{
  "detail": [
    {
      "loc": ["body", "tanggal_pemakaian"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

// 401
{ "detail": "Invalid credentials" }
// or
{ "detail": "Could not validate credentials" }

// 403 (missing Authorization header — D-AUTH-02)
{ "detail": "Not authenticated" }
// 403 (role denied)
{ "detail": "Insufficient permissions" }

// 404
{ "detail": "Vessel not found" }

// 500 (AI / LLM)
{ "detail": "Budget exceeded" }
// or
{ "detail": "Internal server error" }
```

Frontend error-display layer must branch on `Array.isArray(error.detail)`
to render `422` field-level errors vs the simple-string `400/401/403/404/500`
shape.
<!-- END HAND-CURATED: errors -->

## Endpoint Inventory (auto-generated)

_95 method/path pairs discovered in `/openapi.json`. Re-run `scripts/regenerate_api_reference.py` to refresh._


<!-- BEGIN GENERATED -->

| Method | Path | Auth | Request schema | Responses | Verified |
|--------|------|------|----------------|-----------|----------|
| GET | `/api/` | public | — | 200 | live |
| DELETE | `/api/ai/history` | Bearer | — | 200 | schema-only |
| GET | `/api/ai/history` | Bearer | — | 200,422 | schema-only |
| POST | `/api/ai/query` | Bearer | `AIQueryRequest` | 200,422 | schema-only |
| GET | `/api/ai/quick/blending-suggestion` | Bearer | — | 200,422 | schema-only |
| GET | `/api/ai/quick/boiler-alerts` | Bearer | — | 200 | schema-only |
| GET | `/api/ai/quick/coa-alerts` | Bearer | — | 200 | schema-only |
| GET | `/api/ai/quick/contract-status` | Bearer | — | 200 | schema-only |
| GET | `/api/ai/quick/logistics-losses` | Bearer | — | 200 | schema-only |
| GET | `/api/ai/quick/smart-stock` | Bearer | — | 200 | schema-only |
| GET | `/api/ai/sessions` | Bearer | — | 200,422 | schema-only |
| POST | `/api/ai/sessions/new` | Bearer | — | 200,422 | schema-only |
| DELETE | `/api/ai/sessions/{session_id}` | Bearer | — | 200,422 | schema-only |
| GET | `/api/ai/sessions/{session_id}` | Bearer | — | 200,422 | schema-only |
| GET | `/api/ai/settings` | Bearer | — | 200 | schema-only |
| PUT | `/api/ai/settings` | Bearer | `AISettingsUpdate` | 200,422 | schema-only |
| POST | `/api/auth/login` | public | `UserLogin` | 200,422 | live |
| GET | `/api/auth/me` | Bearer | — | 200 | live |
| POST | `/api/auth/register` | public | `UserCreate` | 200,422 | live |
| DELETE | `/api/barges` | Bearer | — | 200 | schema-only |
| GET | `/api/barges` | Bearer | — | 200,422 | live |
| POST | `/api/barges` | Bearer | `BargeTNYCreate` | 200,422 | live |
| DELETE | `/api/barges/{barge_id}` | Bearer | — | 200,422 | live |
| GET | `/api/barges/{barge_id}` | Bearer | — | 200,422 | live |
| PUT | `/api/barges/{barge_id}` | Bearer | `BargeTNYCreate` | 200,422 | live |
| DELETE | `/api/biomassa` | Bearer | — | 200 | schema-only |
| GET | `/api/biomassa` | Bearer | — | 200,422 | live |
| POST | `/api/biomassa` | Bearer | `BiomassaTNYCreate` | 200,422 | live |
| DELETE | `/api/biomassa/{biomassa_id}` | Bearer | — | 200,422 | live |
| GET | `/api/biomassa/{biomassa_id}` | Bearer | — | 200,422 | live |
| PUT | `/api/biomassa/{biomassa_id}` | Bearer | `BiomassaTNYCreate` | 200,422 | live |
| DELETE | `/api/coa-reconciliation` | Bearer | — | 200 | schema-only |
| GET | `/api/coa-reconciliation` | Bearer | — | 200,422 | live |
| GET | `/api/coa-reconciliation/dispute-monitor` | Bearer | — | 200,422 | live |
| GET | `/api/coa-reconciliation/export/excel` | Bearer | — | 200,422 | live |
| GET | `/api/coa-reconciliation/export/pdf` | Bearer | — | 200,422 | live |
| GET | `/api/coa-reconciliation/kpis` | Bearer | — | 200 | live |
| POST | `/api/coa-reconciliation/manual` | Bearer | `COAManualInput` | 200,422 | live |
| POST | `/api/coa-reconciliation/propose-umpire` | Bearer | `UmpireProposal` | 200,422 | live |
| GET | `/api/coa-reconciliation/shipment/{shipment}` | Bearer | — | 200,422 | live |
| POST | `/api/coa-reconciliation/submit-umpire-result` | Bearer | `UmpireResultInput` | 200,422 | live |
| GET | `/api/coa-reconciliation/supplier-consistency` | Bearer | — | 200 | live |
| GET | `/api/coa-reconciliation/trend` | Bearer | — | 200,422 | live |
| POST | `/api/coa-reconciliation/update-umpire-status/{record_id}` | Bearer | — | 200,422 | live |
| POST | `/api/coa-reconciliation/upload` | Bearer | — | 200,422 | live |
| GET | `/api/coa-reconciliation/{record_id}` | Bearer | — | 200,422 | live |
| GET | `/api/dashboard/advanced` | Bearer | — | 200,422 | live |
| GET | `/api/dashboard/stats` | Bearer | — | 200 | live |
| GET | `/api/health` | public | — | 200 | live |
| DELETE | `/api/merit-order` | Bearer | — | 200 | schema-only |
| GET | `/api/merit-order` | Bearer | — | 200,422 | live |
| POST | `/api/merit-order` | Bearer | `MeritOrderCreate` | 200,422 | live |
| GET | `/api/merit-order/periods` | Bearer | — | 200 | live |
| DELETE | `/api/merit-order/{mo_id}` | Bearer | — | 200,422 | live |
| GET | `/api/merit-order/{mo_id}` | Bearer | — | 200,422 | live |
| PUT | `/api/merit-order/{mo_id}` | Bearer | `MeritOrderCreate` | 200,422 | live |
| DELETE | `/api/po-batubara` | Bearer | — | 200 | schema-only |
| GET | `/api/po-batubara` | Bearer | — | 200,422 | live |
| POST | `/api/po-batubara` | Bearer | `POBatubaraCreate` | 200,422 | live |
| GET | `/api/po-batubara/years` | Bearer | — | 200 | live |
| DELETE | `/api/po-batubara/{po_id}` | Bearer | — | 200,422 | live |
| GET | `/api/po-batubara/{po_id}` | Bearer | — | 200,422 | live |
| PUT | `/api/po-batubara/{po_id}` | Bearer | `POBatubaraCreate` | 200,422 | live |
| GET | `/api/settings/coa` | Bearer | — | 200 | live |
| PUT | `/api/settings/coa` | Bearer | `COASettingsUpdate` | 200,422 | live |
| POST | `/api/smart-blending/recommend` | Bearer | `SmartBlendingRequest` | 200,422 | schema-only |
| DELETE | `/api/smart-stock` | Bearer | — | 200 | schema-only |
| GET | `/api/smart-stock` | Bearer | — | 200,422 | live |
| POST | `/api/smart-stock/entry` | Bearer | `SmartStockEntry` | 200,422 | live |
| POST | `/api/smart-stock/upload` | Bearer | — | 200,422 | live |
| DELETE | `/api/smart-stock/{entry_id}` | Bearer | — | 200,422 | live |
| DELETE | `/api/sumber-pemakaian` | Bearer | — | 200 | schema-only |
| GET | `/api/sumber-pemakaian` | Bearer | — | 200,422 | live |
| POST | `/api/sumber-pemakaian/entry` | Bearer | `SumberPemakaianEntry` | 200,422 | live |
| POST | `/api/sumber-pemakaian/upload` | Bearer | — | 200,422 | live |
| GET | `/api/suppliers` | Bearer | — | 200 | live |
| DELETE | `/api/trucking` | Bearer | — | 200 | schema-only |
| GET | `/api/trucking` | Bearer | — | 200,422 | live |
| POST | `/api/trucking` | Bearer | `TruckingTNYCreate` | 200,422 | live |
| DELETE | `/api/trucking/{trucking_id}` | Bearer | — | 200,422 | live |
| GET | `/api/trucking/{trucking_id}` | Bearer | — | 200,422 | live |
| PUT | `/api/trucking/{trucking_id}` | Bearer | `TruckingTNYCreate` | 200,422 | live |
| POST | `/api/upload/barge` | Bearer | — | 200,422 | schema-only |
| POST | `/api/upload/biomassa` | Bearer | — | 200,422 | schema-only |
| POST | `/api/upload/merit-order` | Bearer | — | 200,422 | schema-only |
| POST | `/api/upload/po-batubara` | Bearer | — | 200,422 | schema-only |
| POST | `/api/upload/trucking` | Bearer | — | 200,422 | schema-only |
| POST | `/api/upload/vessel` | Bearer | — | 200,422 | schema-only |
| GET | `/api/users` | Bearer | — | 200 | live |
| DELETE | `/api/vessels` | Bearer | — | 200 | schema-only |
| GET | `/api/vessels` | Bearer | — | 200,422 | live |
| POST | `/api/vessels` | Bearer | `VesselTNYCreate` | 200,422 | live |
| DELETE | `/api/vessels/{vessel_id}` | Bearer | — | 200,422 | live |
| GET | `/api/vessels/{vessel_id}` | Bearer | — | 200,422 | live |
| PUT | `/api/vessels/{vessel_id}` | Bearer | `VesselTNYCreate` | 200,422 | live |

<!-- END GENERATED -->

<!-- BEGIN HAND-CURATED: examples -->
## Per-Module Call Examples

> **Credential hygiene:** The examples below source admin credentials from
> `memory/test_credentials.md` (gitignored, local-only). They never inline
> a password literal — `scripts/check_credentials.sh` is wired as the
> pre-commit hook and rejects literals on commit. Set
> `${TEST_ADMIN_EMAIL}` and `${TEST_ADMIN_PASSWORD}` in your shell before
> running these recipes.

```bash
cd pltu-tenayan-full-backup

# Source admin credentials from local memory/test_credentials.md (gitignored)
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"

# Login (returns access_token + user envelope)
TOKEN="$(curl -fsS -X POST http://103.150.197.225:8013/api/auth/login \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c 'import json,os;print(json.dumps({"email":os.environ["TEST_ADMIN_EMAIL"],"password":os.environ["TEST_ADMIN_PASSWORD"]}))')" \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')"

# /me — Bearer-token rehydrate
curl -fsS http://103.150.197.225:8013/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Vessels list (paginated; verifies the {items,total,page,page_size,total_pages} envelope)
curl -fsS "http://103.150.197.225:8013/api/vessels?page=1&page_size=2" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

# Health probe (public — no Bearer)
curl -fsS http://103.150.197.225:8013/api/health

# Cleanup
unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD TOKEN
```

For per-endpoint behavior verification (status codes / payload shape), see
`docs/audit/API_REFERENCE_SPOTCHECK.md`.

### Per-module recipes

All examples assume `$TOKEN` was obtained via the login block above and
that `${TEST_ADMIN_PASSWORD}` was sourced from `memory/test_credentials.md`
(never inlined). Replace the `103.150.197.225:8013` host with `localhost:8013`
when running on the VPS itself.

#### Vessels (admin/operator write; tri-role read)

```bash
# List with pagination + filter
curl -fsS "http://103.150.197.225:8013/api/vessels?page=1&page_size=10&year=2025" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30

# Get by id
curl -fsS "http://103.150.197.225:8013/api/vessels/<vessel_id>" \
  -H "Authorization: Bearer $TOKEN"

# Create (admin/operator only)
curl -fsS -X POST http://103.150.197.225:8013/api/vessels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nama_vessel":"MV CONTOH","tanggal_kedatangan":"2025-05-10","supplier":"PT Contoh"}'
```

#### COA Reconciliation (tri-role read; admin/operator write; admin-only delete-all)

```bash
# KPIs (dashboard summary)
curl -fsS "http://103.150.197.225:8013/api/coa-reconciliation/kpis" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Trend (year-month series)
curl -fsS "http://103.150.197.225:8013/api/coa-reconciliation/trend?year=2025" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

# Per-shipment detail
curl -fsS "http://103.150.197.225:8013/api/coa-reconciliation/shipment/<shipment_id>" \
  -H "Authorization: Bearer $TOKEN"

# Propose umpire (admin/operator)
curl -fsS -X POST http://103.150.197.225:8013/api/coa-reconciliation/propose-umpire \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"shipment":"<id>","reason":"GCV gap > tolerance"}'
```

#### Smart Stock (legacy bare-array list — does NOT use envelope)

```bash
# Smart-stock list — note `limit` not `page_size`, and bare-array response
curl -fsS "http://103.150.197.225:8013/api/smart-stock?limit=100" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys;d=json.load(sys.stdin);print(type(d).__name__, len(d) if isinstance(d,list) else 'envelope')"
# Expect: list 100  (bare array, NOT envelope)

# Manual entry (admin/operator)
curl -fsS -X POST http://103.150.197.225:8013/api/smart-stock/entry \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tanggal":"2025-05-10","stockpile":"SP-A","tonase":1500.0,"GCV_ar":3800}'
```

#### Dashboard (read-only; tri-role)

```bash
curl -fsS "http://103.150.197.225:8013/api/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

curl -fsS "http://103.150.197.225:8013/api/dashboard/advanced?year=2025&month=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40
```

#### Excel uploads (admin/operator; verified `schema-only` per D-08)

```bash
# These require a real .xlsx fixture and depend on column-shape validation
# inside the backend's pandas pipeline. Schema is verified against
# /openapi.json; behavioral validation lands in Phase-4 TEST-04 with
# canonical fixtures.
curl -fsS -X POST http://103.150.197.225:8013/api/upload/vessel \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/vessels.xlsx"
```

#### AI / Smart-Blending (verified `schema-only` per D-08)

```bash
# AI session bootstrap — LLM-key dependent, will return 200 only when
# OPENAI_API_KEY (or equivalent) is set on the backend.
curl -fsS -X POST http://103.150.197.225:8013/api/ai/sessions/new \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{}'

curl -fsS -X POST http://103.150.197.225:8013/api/ai/query \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"session_id":"<id>","question":"vessels arriving in May 2025?"}'
```

### Cleanup
Always `unset TOKEN TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD` before exiting the
shell session. The credential scanner only blocks committed literals; it
cannot scrub your shell history. Use a sub-shell (`bash -c`) or `unset` after
each run.
<!-- END HAND-CURATED: examples -->
