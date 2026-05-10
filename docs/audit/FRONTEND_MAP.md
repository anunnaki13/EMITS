# Frontend Map — Routes, Pages, Endpoints, Auth Boundary

**Source tree:** pltu-tenayan-full-backup/frontend/src/
**Captured:** 2026-05-10T11:31:23Z
**Scope:** read-only audit. No frontend source file was modified.

## Route → Page → Endpoints

| Route | Page component | Source file | Protected? | Endpoints consumed |
|-------|----------------|-------------|------------|--------------------|
| /login | Login | frontend/src/pages/Login.js | false | POST /api/auth/login, POST /api/auth/register (delegated to AuthContext.login / AuthContext.register) |
| / | (redirect) | App.js:50 — `<Navigate to="/dashboard" replace />` | false | — |
| /dashboard | Dashboard | frontend/src/pages/Dashboard.js | true | GET /api/dashboard/stats, GET /api/dashboard/advanced |
| /vessel | VesselPage | frontend/src/pages/VesselPage.js | true | GET /api/vessels, POST /api/vessels, PUT /api/vessels/{vessel_id}, DELETE /api/vessels/{vessel_id}, DELETE /api/vessels, POST /api/upload/vessel |
| /barge | BargePage | frontend/src/pages/BargePage.js | true | GET /api/barges, POST /api/barges, PUT /api/barges/{barge_id}, DELETE /api/barges/{barge_id}, DELETE /api/barges, POST /api/upload/barge |
| /trucking | TruckingPage | frontend/src/pages/TruckingPage.js | true | GET /api/trucking, POST /api/trucking, PUT /api/trucking/{trucking_id}, DELETE /api/trucking/{trucking_id}, DELETE /api/trucking, POST /api/upload/trucking |
| /biomassa | BiomassaPage | frontend/src/pages/BiomassaPage.js | true | GET /api/biomassa, POST /api/biomassa, PUT /api/biomassa/{biomassa_id}, DELETE /api/biomassa/{biomassa_id}, DELETE /api/biomassa, POST /api/upload/biomassa |
| /po-batubara | POBatubaraPage | frontend/src/pages/POBatubaraPage.js | true | GET /api/po-batubara, GET /api/po-batubara/years, POST /api/po-batubara, PUT /api/po-batubara/{po_id}, DELETE /api/po-batubara/{po_id}, DELETE /api/po-batubara, POST /api/upload/po-batubara |
| /merit-order | MeritOrderPage | frontend/src/pages/MeritOrderPage.js | true | GET /api/merit-order, POST /api/merit-order, PUT /api/merit-order/{mo_id}, DELETE /api/merit-order/{mo_id}, DELETE /api/merit-order, POST /api/upload/merit-order |
| /smart-stock/sumber-penerimaan | SmartStockPage | frontend/src/pages/SmartStockPage.js | true | GET /api/smart-stock, POST /api/smart-stock/entry, POST /api/smart-stock/upload, DELETE /api/smart-stock |
| /smart-stock/sumber-pemakaian | SumberPemakaianPage | frontend/src/pages/SumberPemakaianPage.js | true | GET /api/sumber-pemakaian, POST /api/sumber-pemakaian/entry, POST /api/sumber-pemakaian/upload, DELETE /api/sumber-pemakaian |
| /smart-stock/smart-blending | SmartBlendingPage | frontend/src/pages/SmartBlendingPage.js | true | POST /api/smart-blending/recommend |
| /ai-intelligence | AIIntelligencePage | frontend/src/pages/AIIntelligencePage.js | true | GET /api/ai/history, DELETE /api/ai/history, POST /api/ai/query, GET /api/ai/quick/blending-suggestion, GET /api/ai/quick/boiler-alerts, GET /api/ai/quick/contract-status, GET /api/ai/quick/logistics-losses, GET /api/ai/quick/smart-stock, GET /api/ai/quick/coa-alerts |
| /laporan | LaporanPage | frontend/src/pages/LaporanPage.js | true | GET /api/suppliers (+ dynamic call(s) — see Notes) |
| /coa-reconciliation | COAReconciliationPage | frontend/src/pages/COAReconciliationPage.js | true | GET /api/coa-reconciliation, GET /api/coa-reconciliation/kpis, GET /api/coa-reconciliation/trend, GET /api/coa-reconciliation/supplier-consistency, GET /api/coa-reconciliation/{record_id}, POST /api/coa-reconciliation/upload, POST /api/coa-reconciliation/manual, POST /api/coa-reconciliation/propose-umpire, DELETE /api/coa-reconciliation, GET /api/coa-reconciliation/export/excel, GET /api/coa-reconciliation/export/pdf |
| /dispute-monitor | DisputeMonitorPage | frontend/src/pages/DisputeMonitorPage.js | true | GET /api/coa-reconciliation/dispute-monitor, GET /api/coa-reconciliation/{record_id}, POST /api/coa-reconciliation/update-umpire-status/{record_id}, POST /api/coa-reconciliation/submit-umpire-result |
| /settings | SettingsPage | frontend/src/pages/SettingsPage.js | true (admin only) | GET /api/settings/coa, PUT /api/settings/coa, GET /api/ai/settings, PUT /api/ai/settings, GET /api/users, POST /api/auth/register |

Notes:
- All protected routes are wrapped in `<ProtectedRoute>` declared in App.js:22-44. `/settings` is the only route with an explicit role gate (`allowedRoles={["admin"]}`); all other protected routes are `any-authenticated`.
- The `/` route is a `<Navigate to="/dashboard" replace />` — not a page. Treated as not-protected here because the redirect happens before any auth check; effective protection comes from the destination `/dashboard`.
- LaporanPage carries one dynamic call (LaporanPage.js:105) where `endpoint` is a runtime variable resolving to one of `vessels` / `barges` / `trucking` / `biomassa` / `po-batubara` / `merit-order`. Documented in Per-page detail.

## Per-page detail

### Login
- Route(s): /login
- Source: frontend/src/pages/Login.js
- Protected: no
- Endpoints called (with method):
  - POST /api/auth/login (Login.js:33 via AuthContext.login)
  - POST /api/auth/register (Login.js:47 via AuthContext.register)
- Dynamic calls: none
- Note: Login.js does NOT call axios directly. It invokes `login()` and `register()` from useAuth(); the actual HTTP calls live in AuthContext.js (login → AuthContext.js:35; register → AuthContext.js:44).

### Dashboard
- Route(s): /dashboard (also reached via `/` redirect)
- Source: frontend/src/pages/Dashboard.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/dashboard/stats (Dashboard.js:119)
  - GET /api/dashboard/advanced (Dashboard.js:120)
- Dynamic calls: none

### VesselPage
- Route(s): /vessel
- Source: frontend/src/pages/VesselPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/vessels (VesselPage.js:61)
  - PUT /api/vessels/{vessel_id} (VesselPage.js:116)
  - POST /api/vessels (VesselPage.js:119)
  - DELETE /api/vessels/{vessel_id} (VesselPage.js:151)
  - DELETE /api/vessels (VesselPage.js:162) — bulk delete-all (admin only per ENDPOINT_AUDIT)
  - POST /api/upload/vessel (VesselPage.js:179) — multipart Excel upload
- Dynamic calls: none

### BargePage
- Route(s): /barge
- Source: frontend/src/pages/BargePage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/barges (BargePage.js:60)
  - PUT /api/barges/{barge_id} (BargePage.js:94)
  - POST /api/barges (BargePage.js:97)
  - DELETE /api/barges/{barge_id} (BargePage.js:129)
  - DELETE /api/barges (BargePage.js:140)
  - POST /api/upload/barge (BargePage.js:157)
- Dynamic calls: none

### TruckingPage
- Route(s): /trucking
- Source: frontend/src/pages/TruckingPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/trucking (TruckingPage.js:60)
  - PUT /api/trucking/{trucking_id} (TruckingPage.js:95)
  - POST /api/trucking (TruckingPage.js:98)
  - DELETE /api/trucking/{trucking_id} (TruckingPage.js:130)
  - DELETE /api/trucking (TruckingPage.js:141)
  - POST /api/upload/trucking (TruckingPage.js:158)
- Dynamic calls: none

### BiomassaPage
- Route(s): /biomassa
- Source: frontend/src/pages/BiomassaPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/biomassa (BiomassaPage.js:117)
  - PUT /api/biomassa/{biomassa_id} (BiomassaPage.js:154)
  - POST /api/biomassa (BiomassaPage.js:157)
  - DELETE /api/biomassa/{biomassa_id} (BiomassaPage.js:189)
  - DELETE /api/biomassa (BiomassaPage.js:200)
  - POST /api/upload/biomassa (BiomassaPage.js:217)
- Dynamic calls: none

### POBatubaraPage
- Route(s): /po-batubara
- Source: frontend/src/pages/POBatubaraPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/po-batubara/years (POBatubaraPage.js:121)
  - GET /api/po-batubara (POBatubaraPage.js:138)
  - PUT /api/po-batubara/{po_id} (POBatubaraPage.js:194)
  - POST /api/po-batubara (POBatubaraPage.js:197)
  - DELETE /api/po-batubara/{po_id} (POBatubaraPage.js:231)
  - DELETE /api/po-batubara (POBatubaraPage.js:244)
  - POST /api/upload/po-batubara (POBatubaraPage.js:263)
- Dynamic calls: none

### MeritOrderPage
- Route(s): /merit-order
- Source: frontend/src/pages/MeritOrderPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/merit-order (MeritOrderPage.js:103) — note: page calls with `page_size=10000`, exceeding the documented operational cap of 500. ENDPOINT_AUDIT marks merit-order as paginated; the backend cap behavior on this oversized page_size is unverified by this audit. Phase 2/6 input.
  - PUT /api/merit-order/{mo_id} (MeritOrderPage.js:142)
  - POST /api/merit-order (MeritOrderPage.js:145)
  - DELETE /api/merit-order/{mo_id} (MeritOrderPage.js:177)
  - DELETE /api/merit-order (MeritOrderPage.js:188)
  - POST /api/upload/merit-order (MeritOrderPage.js:205)
- Dynamic calls: none
- Note: This page does NOT call /api/merit-order/periods, although that endpoint exists in the live OpenAPI surface (ENDPOINT_AUDIT.md row). Possibly used elsewhere or unused; flagged for Phase 2/3 reconciliation.

### SmartStockPage
- Route(s): /smart-stock/sumber-penerimaan
- Source: frontend/src/pages/SmartStockPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/smart-stock (SmartStockPage.js:108) — bespoke (non-paginated) shape per CONS-smart-stock-endpoint
  - POST /api/smart-stock/entry (SmartStockPage.js:155)
  - POST /api/smart-stock/upload (SmartStockPage.js:189)
  - DELETE /api/smart-stock (SmartStockPage.js:295)
- Dynamic calls: none
- Note: /api/smart-stock/{entry_id} (DELETE single) exists in ENDPOINT_AUDIT but is NOT consumed by this page in the grepped view — only the bulk DELETE at line 295 is wired. Phase 2 should confirm whether per-entry delete is reachable from any UI control.

### SumberPemakaianPage
- Route(s): /smart-stock/sumber-pemakaian
- Source: frontend/src/pages/SumberPemakaianPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/sumber-pemakaian (SumberPemakaianPage.js:81) — bespoke shape (mirrors smart-stock)
  - POST /api/sumber-pemakaian/entry (SumberPemakaianPage.js:135)
  - POST /api/sumber-pemakaian/upload (SumberPemakaianPage.js:169)
  - DELETE /api/sumber-pemakaian (SumberPemakaianPage.js:271)
- Dynamic calls: none

### SmartBlendingPage
- Route(s): /smart-stock/smart-blending
- Source: frontend/src/pages/SmartBlendingPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - POST /api/smart-blending/recommend (SmartBlendingPage.js:55)
- Dynamic calls: none
- Note: This is the page operationally degraded by Smart Blending AI (Universal LLM Key budget exhausted). The frontend call is correct; backend returns BudgetExceededError. Phase 6 OPS-01.

### AIIntelligencePage
- Route(s): /ai-intelligence
- Source: frontend/src/pages/AIIntelligencePage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/ai/history (AIIntelligencePage.js:106)
  - GET /api/ai/quick/blending-suggestion (AIIntelligencePage.js:121)
  - GET /api/ai/quick/boiler-alerts (AIIntelligencePage.js:122)
  - GET /api/ai/quick/contract-status (AIIntelligencePage.js:123)
  - GET /api/ai/quick/logistics-losses (AIIntelligencePage.js:124)
  - GET /api/ai/quick/smart-stock (AIIntelligencePage.js:125)
  - GET /api/ai/quick/coa-alerts (AIIntelligencePage.js:126)
  - POST /api/ai/query (AIIntelligencePage.js:162)
  - DELETE /api/ai/history (AIIntelligencePage.js:193)
- Dynamic calls: none
- Note: Page does NOT consume /api/ai/sessions, /api/ai/sessions/new, /api/ai/sessions/{session_id} — those endpoints exist live but are not wired. Aligns with STAB-06 ("AI conversation memory frontend integration completed (REQ-ai-conversation-memory tail)") — Phase 6 work item.

### LaporanPage
- Route(s): /laporan
- Source: frontend/src/pages/LaporanPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/suppliers (LaporanPage.js:84)
  - GET (dynamic) — see below
- Dynamic calls (could not statically resolve):
  - LaporanPage.js:105 — `axios.get(\`${API_URL}/api/${endpoint}\`, ...)` where `endpoint` is a runtime ternary chain over `activeTab` resolving to one of `vessels`, `barges`, `trucking`, `biomassa`, `po-batubara`, `merit-order`. Effectively this page proxies the six rekap-receipt list endpoints. Phase 2/4 should treat all six as transitively consumed.

### COAReconciliationPage
- Route(s): /coa-reconciliation
- Source: frontend/src/pages/COAReconciliationPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/coa-reconciliation (COAReconciliationPage.js:141)
  - GET /api/coa-reconciliation/kpis (COAReconciliationPage.js:163)
  - GET /api/coa-reconciliation/trend (COAReconciliationPage.js:174)
  - GET /api/coa-reconciliation/supplier-consistency (COAReconciliationPage.js:186)
  - POST /api/coa-reconciliation/upload (COAReconciliationPage.js:268)
  - GET /api/coa-reconciliation/{record_id} (COAReconciliationPage.js:294)
  - POST /api/coa-reconciliation/propose-umpire (COAReconciliationPage.js:319)
  - POST /api/coa-reconciliation/manual (COAReconciliationPage.js:389)
  - DELETE /api/coa-reconciliation (COAReconciliationPage.js:407)
  - GET /api/coa-reconciliation/export/excel (COAReconciliationPage.js:527)
  - GET /api/coa-reconciliation/export/pdf (COAReconciliationPage.js:539)
- Dynamic calls: none
- Note: Page does NOT call /api/coa-reconciliation/shipment/{shipment} (live but unwired here; possibly invoked elsewhere or reserved for future surface). Phase 2/3 input.

### DisputeMonitorPage
- Route(s): /dispute-monitor
- Source: frontend/src/pages/DisputeMonitorPage.js
- Protected: yes (ProtectedRoute, any-authenticated)
- Endpoints called (with method):
  - GET /api/coa-reconciliation/dispute-monitor (DisputeMonitorPage.js:91)
  - GET /api/coa-reconciliation/{record_id} (DisputeMonitorPage.js:118)
  - POST /api/coa-reconciliation/update-umpire-status/{record_id} (DisputeMonitorPage.js:132)
  - POST /api/coa-reconciliation/submit-umpire-result (DisputeMonitorPage.js:166)
- Dynamic calls: none

### SettingsPage
- Route(s): /settings
- Source: frontend/src/pages/SettingsPage.js
- Protected: yes (ProtectedRoute allowedRoles=["admin"])
- Endpoints called (with method):
  - GET /api/settings/coa (SettingsPage.js:86)
  - PUT /api/settings/coa (SettingsPage.js:102)
  - GET /api/ai/settings (SettingsPage.js:116)
  - PUT /api/ai/settings (SettingsPage.js:131)
  - GET /api/users (SettingsPage.js:148)
  - POST /api/auth/register (SettingsPage.js:162)
- Dynamic calls: none
- Note: `/api/auth/register` is documented as public per CONS-auth-header but is also reused here for admin "create user" flow. Behavior: anyone-with-no-token can register a new user; SettingsPage just calls it with the admin's bearer attached as well. This is a known surface ambiguity (open registration vs admin-creates-user) — Phase 2 reconciliation candidate.

## Auth boundary

The auth surface that every protected page depends on lives in two files:

- **frontend/src/contexts/AuthContext.js** — provider, state, all auth-related HTTP.
- **frontend/src/App.js** — `ProtectedRoute` wrapper component (declared in-file, App.js:22-44).

The named surface elements:

1. **Login submission** — `login(email, password)` defined in AuthContext.js:34. Issues `axios.post` to `${API_URL}/api/auth/login` (AuthContext.js:35), receives `{ access_token, user }`, stores token in `localStorage` (AuthContext.js:37), sets in-memory `token` and `user` state, returns `userData`.
2. **Token storage** — `localStorage` key name **`"token"`** (the literal string). Set at AuthContext.js:37 (post-login) and AuthContext.js:48 (post-register). Read at AuthContext.js:10 (initial state) and AuthContext.js:15 (rehydrate effect). Cleared at AuthContext.js:24 (failed rehydrate) and AuthContext.js:53 (logout).
3. **Session rehydrate** — `initAuth()` inside the `useEffect` at AuthContext.js:13-32. On mount: reads `"token"` from localStorage; if present, calls `axios.get(\`${API_URL}/api/auth/me\`, { headers: { Authorization: \`Bearer ${savedToken}\` } })` (AuthContext.js:18-20). On success, sets `user` and `token` state. On error (401/403/network), removes the token and clears state (AuthContext.js:23-27). Always sets `loading=false` at the end (AuthContext.js:29).
4. **getAuthHeader** — `getAuthHeader` defined at AuthContext.js:58-60. Returns `{ Authorization: \`Bearer ${token}\` }` when an in-memory token exists, otherwise `{}`. Pages consume it as `headers: getAuthHeader()` on every axios call against an auth-required endpoint. Sourcing the token from in-memory state (not localStorage) means logout immediately invalidates all subsequent calls without a page reload.
5. **Logout** — `logout()` at AuthContext.js:52-56. Removes `"token"` from localStorage, clears `token` and `user` state. Does NOT call any backend endpoint — JWT is stateless server-side; logout is purely client-side state reset. Layout.js:50-53 (`handleLogout`) wraps it with a navigate-to-/login redirect.
6. **ProtectedRoute** — declared in **frontend/src/App.js:22-44** (sibling to the route table, not a separate file). Behavior:
   - While `loading` is true (rehydrate in flight), renders a centered cyan pulse-glow loader (App.js:25-33). This is the gate that prevents a brief unauthenticated flash on hard refresh.
   - When `loading=false` and `!user`, renders `<Navigate to="/login" replace />` (App.js:35-37). Triggered when no token was in localStorage, OR rehydrate failed (AuthContext.js:23-27 cleared user).
   - When `loading=false`, `user` set, and `allowedRoles` is provided, checks `allowedRoles.includes(user.role)`. On role mismatch, redirects to `/dashboard` (App.js:39-41) — soft denial back to the home dashboard, no error toast.
   - When all checks pass, renders `children`.

The `useAuth()` hook (AuthContext.js:69-75) is the auth-consumption guard. It throws `"useAuth must be used within AuthProvider"` if invoked outside the provider tree — this is the import-level invariant that proves the auth boundary is referenced from a single source.

### Auth boundary diagram

```
Page (e.g., VesselPage.js)
   ↓ uses getAuthHeader() from useAuth()
AuthContext (token from in-memory state, sourced from localStorage["token"])
   ↓ Authorization: Bearer <JWT>
/api/* (FastAPI; bcrypt+JWT per IMPLICIT-004; 401 expected for invalid token,
        403 observed for missing-credentials per HTTPBearer default)
```

Initial-load path (per refresh / first paint):

```
Page mount
   → AuthProvider useEffect → initAuth()
        → reads localStorage["token"]
        → GET /api/auth/me (Authorization: Bearer <token>)
            ├─ 200 → setUser, setToken, loading=false → ProtectedRoute renders children
            └─ 4xx/error → localStorage.removeItem("token"), setUser(null), loading=false
                            → ProtectedRoute redirects to /login
```

## Sidebar / nav cross-check

| Nav label | Nav href | Route exists? | Page component | Notes |
|-----------|----------|---------------|----------------|-------|
| Dashboard | /dashboard | yes | Dashboard | top-level |
| Vessel TNY | /vessel | yes | VesselPage | section: Rekap Penerimaan BB |
| Barge TNY | /barge | yes | BargePage | section: Rekap Penerimaan BB |
| Trucking TNY | /trucking | yes | TruckingPage | section: Rekap Penerimaan BB |
| Biomassa TNY | /biomassa | yes | BiomassaPage | section: Rekap Penerimaan BB |
| Purchase Order Batubara | /po-batubara | yes | POBatubaraPage | section: Rekap Penerimaan BB |
| Merit Order | /merit-order | yes | MeritOrderPage | section: Rekap Penerimaan BB |
| Sumber Penerimaan | /smart-stock/sumber-penerimaan | yes | SmartStockPage | section: Smart Stock |
| Sumber Pemakaian | /smart-stock/sumber-pemakaian | yes | SumberPemakaianPage | section: Smart Stock |
| Smart Blending AI | /smart-stock/smart-blending | yes | SmartBlendingPage | section: Smart Stock |
| Laporan | /laporan | yes | LaporanPage | top-level |
| Triple Check | /coa-reconciliation | yes | COAReconciliationPage | section: COA Reconciliation |
| Dispute Monitor | /dispute-monitor | yes | DisputeMonitorPage | section: COA Reconciliation |
| AI Intelligence | /ai-intelligence | yes | AIIntelligencePage | top-level |
| Pengaturan | /settings | yes | SettingsPage | role-gated render: only when user.role==="admin" — matches the route's allowedRoles=["admin"] |

### Routes WITHOUT a corresponding nav entry (declared but not surfaced in the sidebar)

- **/login** — public route; no nav entry expected (users on /login are not yet logged in and the sidebar is part of the protected `<Layout>`). Not an accessibility gap; documented behavior.
- **/** — bare root; redirects to /dashboard via `<Navigate replace />`. Not a destination route; no nav entry needed.

Result: zero unexpected accessibility gaps. Every route that renders a real page is surfaced in Layout.js navigation (modulo the role-gated /settings entry).

### Nav entries WITHOUT a corresponding route — dead links

(None. Every Link href in Layout.js maps 1:1 to a path declared in App.js.)

## Cross-check vs ENDPOINT_AUDIT.md

ENDPOINT_AUDIT.md is present at write time (captured 2026-05-10T11:14Z, 64 live `/api/*` paths). Cross-check rendered below.

| Endpoint | Page(s) consuming | In live OpenAPI? | Live status |
|----------|-------------------|------------------|-------------|
| /api/auth/login | Login (via AuthContext) | yes | not-probed-mutating (validation gate confirmed public) |
| /api/auth/register | Login (via AuthContext), SettingsPage | yes | not-probed-mutating (validation gate confirmed public) |
| /api/auth/me | (AuthContext rehydrate; not page-level) | yes | working |
| /api/users | SettingsPage | yes | working (admin-only) |
| /api/suppliers | LaporanPage | yes | working |
| /api/dashboard/stats | Dashboard | yes | working |
| /api/dashboard/advanced | Dashboard | yes | working |
| /api/vessels | VesselPage, LaporanPage (dynamic) | yes | working |
| /api/vessels/{vessel_id} | VesselPage | yes | not-probed-path-param |
| /api/upload/vessel | VesselPage | yes | not-probed-mutating |
| /api/barges | BargePage, LaporanPage (dynamic) | yes | working |
| /api/barges/{barge_id} | BargePage | yes | not-probed-path-param |
| /api/upload/barge | BargePage | yes | not-probed-mutating |
| /api/trucking | TruckingPage, LaporanPage (dynamic) | yes | working |
| /api/trucking/{trucking_id} | TruckingPage | yes | not-probed-path-param |
| /api/upload/trucking | TruckingPage | yes | not-probed-mutating |
| /api/biomassa | BiomassaPage, LaporanPage (dynamic) | yes | working |
| /api/biomassa/{biomassa_id} | BiomassaPage | yes | not-probed-path-param |
| /api/upload/biomassa | BiomassaPage | yes | not-probed-mutating |
| /api/po-batubara | POBatubaraPage, LaporanPage (dynamic) | yes | working |
| /api/po-batubara/years | POBatubaraPage | yes | working |
| /api/po-batubara/{po_id} | POBatubaraPage | yes | not-probed-path-param |
| /api/upload/po-batubara | POBatubaraPage | yes | not-probed-mutating |
| /api/merit-order | MeritOrderPage, LaporanPage (dynamic) | yes | working |
| /api/merit-order/{mo_id} | MeritOrderPage | yes | not-probed-path-param |
| /api/upload/merit-order | MeritOrderPage | yes | not-probed-mutating |
| /api/coa-reconciliation | COAReconciliationPage | yes | working |
| /api/coa-reconciliation/kpis | COAReconciliationPage | yes | working |
| /api/coa-reconciliation/trend | COAReconciliationPage | yes | working |
| /api/coa-reconciliation/supplier-consistency | COAReconciliationPage | yes | working |
| /api/coa-reconciliation/dispute-monitor | DisputeMonitorPage | yes | working |
| /api/coa-reconciliation/{record_id} | COAReconciliationPage, DisputeMonitorPage | yes | not-probed-path-param |
| /api/coa-reconciliation/upload | COAReconciliationPage | yes | not-probed-mutating |
| /api/coa-reconciliation/manual | COAReconciliationPage | yes | not-probed-mutating |
| /api/coa-reconciliation/propose-umpire | COAReconciliationPage | yes | not-probed-mutating |
| /api/coa-reconciliation/update-umpire-status/{record_id} | DisputeMonitorPage | yes | not-probed-mutating |
| /api/coa-reconciliation/submit-umpire-result | DisputeMonitorPage | yes | not-probed-mutating |
| /api/coa-reconciliation/export/excel | COAReconciliationPage | yes | working |
| /api/coa-reconciliation/export/pdf | COAReconciliationPage | yes | working |
| /api/smart-stock | SmartStockPage | yes | working (bespoke shape per CONS-smart-stock-endpoint) |
| /api/smart-stock/entry | SmartStockPage | yes | not-probed-mutating |
| /api/smart-stock/upload | SmartStockPage | yes | not-probed-mutating |
| /api/sumber-pemakaian | SumberPemakaianPage | yes | working (bespoke shape) |
| /api/sumber-pemakaian/entry | SumberPemakaianPage | yes | not-probed-mutating |
| /api/sumber-pemakaian/upload | SumberPemakaianPage | yes | not-probed-mutating |
| /api/smart-blending/recommend | SmartBlendingPage | yes | not-probed-mutating (operationally degraded — Universal LLM Key budget) |
| /api/settings/coa | SettingsPage | yes | working |
| /api/ai/settings | SettingsPage | yes | working |
| /api/ai/query | AIIntelligencePage | yes | not-probed-mutating |
| /api/ai/history | AIIntelligencePage | yes | working |
| /api/ai/quick/blending-suggestion | AIIntelligencePage | yes | working |
| /api/ai/quick/boiler-alerts | AIIntelligencePage | yes | working |
| /api/ai/quick/contract-status | AIIntelligencePage | yes | working |
| /api/ai/quick/logistics-losses | AIIntelligencePage | yes | working |
| /api/ai/quick/smart-stock | AIIntelligencePage | yes | working |
| /api/ai/quick/coa-alerts | AIIntelligencePage | yes | working |

### Flag summary

- **frontend-references-dead-endpoint**: 0. Every page-consumed endpoint is present in the live OpenAPI surface.
- **frontend-uses-broken-endpoint**: 0. No page consumes an endpoint with status `broken-*`.
- **Operational degradation (not a flag, but tracked)**: SmartBlendingPage's only call (POST /api/smart-blending/recommend) is the Universal LLM Key budget-exhausted endpoint. Phase 6 OPS-01.

### Live endpoints NOT consumed by any page (server-side surface that the frontend does not reach)

These are documented for Phase 2/3 reconciliation — they exist but no page in the audited frontend uses them:

- /api/ — bare-prefix root; informational only.
- /api/health — health check; presumably consumed by uptime monitoring, not the React app.
- /api/merit-order/periods — not wired in MeritOrderPage; reserved or used by a non-rendered surface.
- /api/coa-reconciliation/shipment/{shipment} — not wired in COAReconciliationPage or DisputeMonitorPage.
- /api/smart-stock/{entry_id} (DELETE single) — page wires only the bulk DELETE.
- /api/ai/sessions, /api/ai/sessions/new, /api/ai/sessions/{session_id} — STAB-06 frontend integration tail; Phase 6 work item.

## Methodology

- Inputs in `pltu-tenayan-full-backup/docs/audit/.work/`:
  - `routes.txt` — TSV: path, component, protected (true/false/unknown), notes.
  - `page-endpoints.txt` — TSV: page, method, endpoint, source-line.
  - `sidebar-links.txt` — TSV: label, href, icon-or-other-note.
- Endpoint extraction grep pattern (run against each page in `frontend/src/pages/*.js`):
  ```
  grep -nE '`\$\{[A-Z_]*BACKEND_URL\}/api/|`\$\{API_URL\}/api/|`\$\{API\}/api/|"/api/|'\''/api/'
  ```
  Matched against the project's actual idiom (axios with `${API_URL}/api/...` template literal). Method (`GET`/`POST`/`PUT`/`DELETE`) determined from the surrounding `axios.<verb>` call site (verified by visual inspection of each line).
- Path-parameter normalization: concrete IDs in URLs replaced with `{vessel_id}` / `{barge_id}` / `{trucking_id}` / `{biomassa_id}` / `{po_id}` / `{mo_id}` / `{record_id}` / `{entry_id}` to match the OpenAPI path-template style used in ENDPOINT_AUDIT.md.
- Login.js does not call axios directly — it routes login/register through AuthContext. Documented as transitive dependency (resolves to /api/auth/login, /api/auth/register).
- Cross-check uses ENDPOINT_AUDIT.md inventory as the source of truth for live status. ENDPOINT_AUDIT was already on disk at write time of this file.
- No mutation, no service restart, no source file under `frontend/` modified.
