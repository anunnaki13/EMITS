# Endpoint Audit — Live Surface vs Committed API_REFERENCE

**Live host:** http://103.150.197.225:8013
**OpenAPI source:** http://103.150.197.225:8013/openapi.json (captured 2026-05-10T11:14Z)
**API_REFERENCE source:** pltu-tenayan-full-backup/API_REFERENCE.md
**Probe method:** GET no-path-param endpoints probed live with bearer token from memory/test_credentials.md (gitignored). Mutating endpoints (POST/PUT/DELETE) and path-parameterized GETs are not exercised live — OpenAPI presence is the existence signal. Unauthenticated probes are run only against the documented public set (`/api/`, `/api/health`, `/api/auth/login`, `/api/auth/register`).
**Login probe:** SUCCEEDED — bearer token obtained from POST /api/auth/login; all auth-required GETs probed authenticated.
**Auth gate observation:** Live server returns **HTTP 403** (not 401) for unauthenticated requests against auth-required routes. CONS-auth-header documents 401 for "invalid/expired token"; behavior is still correct — request is denied — but the code mapping in this audit treats 403 from a no-token request as `working-auth-required` because the gate is functioning. Phase 2 / Phase 3 should reconcile whether the 401-vs-403 split is intentional FastAPI default behavior (the HTTPBearer security class raises 403 when no credentials are present, 401 when credentials are invalid).

## Counts

- Live `/api/*` paths: **64**
- Documented `/api/*` paths in API_REFERENCE.md: **63**
- Intersection (documented AND live): **63**
- Live but undocumented: **1**
- Documented but missing live: **0**

## Inventory

Status legend:
- `working` — live GET probe returned 200/201/204
- `working-auth-required` — live GET probe returned 401 (or 403 from missing-credentials gate) on an auth-required path
- `working-role-gated` — 403 returned when the authenticated user lacks role
- `broken-not-found` — 404 against a path the OpenAPI claims exists
- `broken-5xx` — server error on a documented path
- `broken-unreachable` — connection error
- `broken-auth-leak` — auth-required path responded 200 to anonymous request
- `not-probed-path-param` — GET requires `{id}`/`{record_id}`/etc.; not probed (OpenAPI presence used as existence signal)
- `not-probed-mutating` — POST/PUT/DELETE; not exercised live to avoid mutating production data
- `unverified-auth` — auth-required path that could not be probed because login failed

| Path | Methods | Auth | Role tier | Live status | In API_REFERENCE? | Notes |
|------|---------|------|-----------|-------------|-------------------|-------|
| /api/ | GET | public | n/a | working | no | Root marker; the loose grep on API_REFERENCE.md captures `/api/auth/...` etc. but never the bare prefix `/api/`. Documented in section 4 prose ("GET `/api/`") but not as a typeable token; flagged below as live-only. |
| /api/health | GET | public | n/a | working | yes | Health check. |
| /api/auth/login | POST | public | n/a | not-probed-mutating | yes | POST with empty body returned 422 (validation) — confirms public access + body validation gate. |
| /api/auth/register | POST | public | n/a | not-probed-mutating | yes | POST with empty body returned 422 (validation) — confirms public access. |
| /api/auth/me | GET | required | any-authenticated | working | yes | Returns active user profile. |
| /api/users | GET | required | admin | working | yes | API_REFERENCE marks Role: Admin. Response is a bare array (8 users) — not paginated. |
| /api/suppliers | GET | required | any-authenticated | working | yes | Lookup. Response shape `{ suppliers, total }` — aggregation, not paginated. |
| /api/dashboard/stats | GET | required | any-authenticated | working | yes | Dashboard aggregation. |
| /api/dashboard/advanced | GET | required | any-authenticated | working | yes | Advanced visualizations payload. |
| /api/vessels | GET, POST, DELETE | required | any-authenticated (GET); admin/operator (POST); admin (DELETE-all) | working | yes | List paginated; CONS-pagination-shape verified. |
| /api/vessels/{vessel_id} | GET, PUT, DELETE | required | any-authenticated (GET); admin/operator (PUT); admin (DELETE) | not-probed-path-param | yes | Path param — OpenAPI presence is existence signal. |
| /api/upload/vessel | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/barges | GET, POST, DELETE | required | any-authenticated (GET); admin/operator (POST); admin (DELETE-all) | working | yes | CONS-pagination-shape verified. |
| /api/barges/{barge_id} | GET, PUT, DELETE | required | inferred-any-authenticated (GET); admin/operator (PUT); admin (DELETE) | not-probed-path-param | yes | Path param. |
| /api/upload/barge | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/trucking | GET, POST, DELETE | required | any-authenticated (GET); admin/operator (POST); admin (DELETE-all) | working | yes | CONS-pagination-shape verified. |
| /api/trucking/{trucking_id} | GET, PUT, DELETE | required | inferred-any-authenticated (GET); admin/operator (PUT); admin (DELETE) | not-probed-path-param | yes | Path param. |
| /api/upload/trucking | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/biomassa | GET, POST, DELETE | required | any-authenticated (GET); admin/operator (POST); admin (DELETE-all) | working | yes | CONS-pagination-shape verified. |
| /api/biomassa/{biomassa_id} | GET, PUT, DELETE | required | inferred-any-authenticated (GET); admin/operator (PUT); admin (DELETE) | not-probed-path-param | yes | Path param. |
| /api/upload/biomassa | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/po-batubara | GET, POST, DELETE | required | any-authenticated (GET); admin/operator (POST); admin (DELETE-all) | working | yes | CONS-pagination-shape verified. |
| /api/po-batubara/years | GET | required | any-authenticated | working | yes | Returns array of year aggregations (3 years observed). |
| /api/po-batubara/{po_id} | GET, PUT, DELETE | required | inferred-any-authenticated (GET); admin/operator (PUT); admin (DELETE) | not-probed-path-param | yes | Path param. |
| /api/upload/po-batubara | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/merit-order | GET, POST, DELETE | required | any-authenticated (GET); admin/operator (POST); admin (DELETE-all) | working | yes | CONS-pagination-shape verified. |
| /api/merit-order/periods | GET | required | any-authenticated | working | yes | Array of period aggregations (1 year observed). |
| /api/merit-order/{mo_id} | GET, PUT, DELETE | required | inferred-any-authenticated (GET); admin/operator (PUT); admin (DELETE) | not-probed-path-param | yes | Path param. |
| /api/upload/merit-order | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/coa-reconciliation | GET, DELETE | required | any-authenticated (GET); admin (DELETE-all) | working | yes | CONS-pagination-shape verified. |
| /api/coa-reconciliation/kpis | GET | required | any-authenticated | working | yes | KPI aggregation. |
| /api/coa-reconciliation/trend | GET | required | any-authenticated | working | yes | GCV trend (months query param). |
| /api/coa-reconciliation/supplier-consistency | GET | required | any-authenticated | working | yes | Chart aggregation. |
| /api/coa-reconciliation/dispute-monitor | GET | required | any-authenticated | working | yes | Paginated dispute list (CONS-pagination-shape verified). |
| /api/coa-reconciliation/{record_id} | GET | required | any-authenticated | not-probed-path-param | yes | Path param. |
| /api/coa-reconciliation/shipment/{shipment} | GET | required | any-authenticated | not-probed-path-param | yes | Path param. |
| /api/coa-reconciliation/propose-umpire | POST | required | admin/operator | not-probed-mutating | yes | Umpire workflow start. |
| /api/coa-reconciliation/update-umpire-status/{record_id} | POST | required | admin/operator | not-probed-mutating | yes | Path param + mutating. |
| /api/coa-reconciliation/submit-umpire-result | POST | required | admin/operator | not-probed-mutating | yes | Final umpire result. |
| /api/coa-reconciliation/upload | POST | required | admin/operator | not-probed-mutating | yes | multipart 3-file upload. Drops old data. |
| /api/coa-reconciliation/manual | POST | required | admin/operator | not-probed-mutating | yes | Manual single record. |
| /api/coa-reconciliation/export/excel | GET | required | any-authenticated | working | yes | Returns Excel binary. |
| /api/coa-reconciliation/export/pdf | GET | required | any-authenticated | working | yes | Returns PDF binary. |
| /api/smart-stock | GET, DELETE | required | any-authenticated (GET); admin (DELETE-all) | working | yes | Non-paginated bespoke shape `{ data, recent_30_days, supplier_totals, total_count }` — does NOT match CONS-pagination-shape (intentional per CONS-smart-stock-endpoint). |
| /api/smart-stock/entry | POST | required | admin/operator | not-probed-mutating | yes | Manual entry. |
| /api/smart-stock/upload | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/smart-stock/{entry_id} | DELETE | required | admin/operator | not-probed-mutating | yes | Path param + mutating. |
| /api/sumber-pemakaian | GET, DELETE | required | any-authenticated (GET); admin (DELETE-all) | working | yes | Non-paginated bespoke shape `{ data, recent_30_days, stats, total_count }` — does NOT match CONS-pagination-shape (intentional per CONS-smart-stock-endpoint). |
| /api/sumber-pemakaian/entry | POST | required | admin/operator | not-probed-mutating | yes | Manual entry. |
| /api/sumber-pemakaian/upload | POST | required | admin/operator | not-probed-mutating | yes | multipart Excel upload. |
| /api/smart-blending/recommend | POST | required | inferred-any-authenticated | not-probed-mutating | yes | LLM-backed; Smart Blending AI is operationally degraded (Universal LLM Key budget exhausted) — code path unverified live, presence verified via OpenAPI. |
| /api/settings/coa | GET, PUT | required | any-authenticated (GET); admin (PUT) | working | yes | GET returns settings; PUT writes (admin only). |
| /api/ai/query | POST | required | inferred-any-authenticated | not-probed-mutating | yes | AI main entry. |
| /api/ai/history | GET, DELETE | required | inferred-any-authenticated | working | yes | Returns array (3 conversations observed) — legacy endpoint per CONS-collection-naming-debt (`ai_chat_history` collection). |
| /api/ai/sessions | GET | required | inferred-any-authenticated | working | yes | Paginated session list (CONS-pagination-shape verified). |
| /api/ai/sessions/new | POST | required | inferred-any-authenticated | not-probed-mutating | yes | New session. |
| /api/ai/sessions/{session_id} | GET, DELETE | required | inferred-any-authenticated | not-probed-path-param | yes | Path param. |
| /api/ai/settings | GET, PUT | required | inferred-any-authenticated | working | yes | Per-user AI settings. |
| /api/ai/quick/blending-suggestion | GET | required | inferred-any-authenticated | working | yes | Quick insight. |
| /api/ai/quick/boiler-alerts | GET | required | inferred-any-authenticated | working | yes | Quick insight. |
| /api/ai/quick/contract-status | GET | required | inferred-any-authenticated | working | yes | Quick insight. |
| /api/ai/quick/logistics-losses | GET | required | inferred-any-authenticated | working | yes | Quick insight. |
| /api/ai/quick/smart-stock | GET | required | inferred-any-authenticated | working | yes | Quick insight. |
| /api/ai/quick/coa-alerts | GET | required | inferred-any-authenticated | working | yes | Quick insight. |

Footnote on `inferred-any-authenticated`: API_REFERENCE.md does not specify a role tier for these endpoints, and the OpenAPI security block does not enumerate scopes. The CONS-auth-header contract states "all endpoints except register/login/root/health require Authorization: Bearer". Without an explicit role gate documented, the inferred tier is "any authenticated user (operator or higher)". Phase 3 documentation refresh should record explicit role tiers per route once the source code review (Phase 1, plan 04) has classified each handler.

## Drift: Live but undocumented

- `/api/` (GET, public) — Live OpenAPI advertises a bare-prefix root. API_REFERENCE.md *describes* the route in section 4 prose, but the audit's grep pattern requires at least one path character after `/api/`. This is a doc-grep artifact, not a true endpoint drift; nevertheless flagged here so Phase 3 can decide whether to add a typeable example (e.g., `GET /api/`) the grep can capture.

## Drift: Documented but not live

(None. Every `/api/*` path captured by the grep against API_REFERENCE.md is present in the live OpenAPI surface.)

## Pagination contract spot-check

CONS-pagination-shape requires `{ items, total, page, page_size, total_pages }` for paginated list endpoints. Probed via `?page=1&page_size=1`:

| Endpoint | Top-level keys | Matches CONS-pagination-shape? |
|----------|----------------|-------------------------------|
| /api/vessels | items,page,page_size,total,total_pages | yes |
| /api/barges | items,page,page_size,total,total_pages | yes |
| /api/trucking | items,page,page_size,total,total_pages | yes |
| /api/biomassa | items,page,page_size,total,total_pages | yes |
| /api/po-batubara | items,page,page_size,total,total_pages | yes |
| /api/merit-order | items,page,page_size,total,total_pages | yes |
| /api/coa-reconciliation | items,page,page_size,total,total_pages | yes |
| /api/coa-reconciliation/dispute-monitor | items,page,page_size,summary,total,total_pages | yes (superset — extra `summary` key) |
| /api/ai/sessions | items,page,page_size,total,total_pages | yes |
| /api/smart-stock | data,recent_30_days,supplier_totals,total_count | no — bespoke shape (intentional per CONS-smart-stock-endpoint; `limit` query param replaces page/page_size) |
| /api/sumber-pemakaian | data,recent_30_days,stats,total_count | no — bespoke shape (intentional, mirrors smart-stock) |

Result: 9 of 9 paginated list endpoints satisfy CONS-pagination-shape. Smart-stock and sumber-pemakaian intentionally diverge (documented in CONS-smart-stock-endpoint).

## Public endpoint set

CONS-auth-header lists `/api/auth/register`, `/api/auth/login`, `/api/`, `/api/health` as the public set. Probed unauthenticated:

| Endpoint | Method | Anon response | Expected | Match |
|----------|--------|---------------|----------|-------|
| /api/ | GET | 200 | 200 | yes |
| /api/health | GET | 200 | 200 | yes |
| /api/auth/login | POST (empty JSON body) | 422 | 200/422 (validation gate before auth gate) | yes |
| /api/auth/register | POST (empty JSON body) | 422 | 200/422 (validation gate before auth gate) | yes |

Sample anonymous probes against auth-required routes (confirms gate is enforced):

| Endpoint | Method | Anon response | Expected | Notes |
|----------|--------|---------------|----------|-------|
| /api/vessels | GET | 403 | 401 (per CONS-auth-header) | Live returns 403; CONS-auth-header maps 401 to "invalid/expired token". FastAPI's HTTPBearer security class raises 403 when no credentials are present (default behavior). The gate denies access correctly; the 401-vs-403 mismatch is a documentation/contract-clarity issue for Phase 2/3, not a security defect. |
| /api/dashboard/stats | GET | 403 | 401 | same as above |
| /api/auth/me | GET | 403 | 401 | same as above |
| /api/users | GET | 403 | 401 | same as above |

No auth leaks detected: zero auth-required GETs returned 200 to anonymous requests in the spot-check.

## Methodology

- Reproducible probe script: `pltu-tenayan-full-backup/docs/audit/.work/probe.sh`
- Token sourced from `pltu-tenayan-full-backup/memory/test_credentials.md` at probe time and never written to this file or to git.
- Live OpenAPI document pinned at `pltu-tenayan-full-backup/docs/audit/.work/openapi.json` (captured 2026-05-10T11:14Z).
- Path lists (`openapi-paths.txt`, `api_reference-paths.txt`) and drift sets (`drift-live-only.txt`, `drift-doc-only.txt`, `intersection.txt`) live alongside the script.
- Probe outputs (`inventory.csv`, `pagination.csv`, `public-probes.csv`) regenerable via `bash docs/audit/.work/probe.sh` from the inner repo root.
- No source files under `pltu-tenayan-full-backup/{backend,frontend}/` were modified. No live data was mutated.
