# Context (DOC Intel)

Lower-precedence narrative content from DOC-class sources. Used for orientation, runbook recall, and historical color. Does NOT override SPEC or PRD claims.

---

## TOPIC: Project Identity

source: pltu-tenayan-full-backup/readme.md

PLTU Tenayan Fuel Management System — full-stack application for managing coal/biomass receipts, monitoring fuel quality, COA reconciliation, operational reporting, and AI analytics at the PLTU Tenayan power plant.

Audience: operations team, admins, developers. Built for managing fuel-receipt data across logistics modes, monitoring fuel quality, generating reports, and running AI analyses across stock, blending, contract, boiler, and dispute QC.

---

## TOPIC: Tech Stack (narrative)

source: pltu-tenayan-full-backup/readme.md
source: pltu-tenayan-full-backup/documentation.md
source: pltu-tenayan-full-backup/memory/PRD.md

Frontend: React 19, React Router 7, Tailwind CSS, Shadcn/UI, Axios, Recharts, jsPDF, xlsx.

Backend: FastAPI, Motor (MongoDB async), Pandas, OpenPyXL/xlrd, ReportLab, JWT (python-jose / PyJWT + bcrypt), OpenRouter-backed LLM integration.

Database: MongoDB.

AI: OpenRouter via `OPENROUTER_API_KEY` and `OPENROUTER_DEFAULT_MODEL`.

---

## TOPIC: Project Structure

source: pltu-tenayan-full-backup/readme.md
source: pltu-tenayan-full-backup/documentation.md

```
/app
├── backend
│   ├── server.py                # Monolithic FastAPI entrypoint, holds majority of routes
│   ├── routers/                 # auth.py, ai.py, data.py — partial modular extraction
│   ├── services/                # excel_parser.py, coa_reconciliation.py
│   ├── utils/                   # auth.py, database.py
│   └── tests/                   # test_coa_reconciliation, test_dashboard_advanced, test_merit_order, test_po_batubara
├── frontend
│   ├── public/                  # docs/Smart_Blending_AI_Formula.md
│   └── src/
│       ├── App.js               # main router
│       ├── components/Layout.js # shell + sidebar
│       ├── contexts/AuthContext.js
│       └── pages/               # one page per domain (Vessel, Barge, Trucking, Biomassa, POBatubara, MeritOrder, SmartStock, SumberPemakaian, SmartBlending, AIIntelligence, Laporan, COAReconciliation, DisputeMonitor, Settings, Login, Dashboard)
├── memory/                      # PRD, internal notes, test credentials
├── README.md
└── documentation.md
```

---

## TOPIC: Environment Variables

source: pltu-tenayan-full-backup/readme.md
source: pltu-tenayan-full-backup/documentation.md
source: pltu-tenayan-full-backup/LOCAL_SETUP.md

Frontend:
- `REACT_APP_BACKEND_URL` — base URL of the backend API.

Backend:
- `MONGO_URL` — MongoDB connection string.
- `DB_NAME` — database name.
- `JWT_SECRET` — JWT signing secret.
- `CORS_ORIGINS` — comma-separated allowed origins.
- `OPENROUTER_API_KEY` — default LLM key when user has no custom key configured.
- `OPENROUTER_DEFAULT_MODEL` — default LLM model.

---

## TOPIC: Local Development Runbook

source: pltu-tenayan-full-backup/LOCAL_SETUP.md
source: pltu-tenayan-full-backup/readme.md
source: pltu-tenayan-full-backup/documentation.md

Prerequisites: Python 3.11+, Node.js LTS, Yarn, MongoDB Community Edition, mongorestore/mongosh.

Backend:
```
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Frontend:
```
cd /app/frontend
yarn install
yarn start
```

Tests:
```
cd /app/backend
pytest tests -q
```

Database restore from backup:
```
unzip database_backup.zip -d database_backup
mongorestore --drop --db <local_db> ./database_backup/mongodump/<source_db>
```

The original database name can be found in `database_backup/metadata/summary.json` or `backend/.env`.

Test credentials (from PRD) live in `pltu-tenayan-full-backup/memory/test_credentials.md` — do not inline them in committed planning files.

---

## TOPIC: VPS Deployment Architecture

source: pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md

Recommended production layout:

```
Internet
   |
   v
Nginx (80/443)
   |---- /api/*  -> FastAPI Uvicorn (127.0.0.1:8001)
   ---- /*       -> React build static (/var/www/pltu-tenayan/frontend/build)

FastAPI -> MongoDB
```

Minimum VPS spec: Ubuntu 22.04/24.04 LTS, 2 vCPU, 4 GB RAM, 40 GB SSD, 1 public domain. Larger workloads benefit from 4 vCPU / 8 GB RAM and split MongoDB.

Required components: nginx, python3 + venv + pip, nodejs + yarn, git, mongodb (or external), certbot + nginx plugin.

Recommended directory layout:
```
/opt/pltu-tenayan/app/{backend,frontend}
/opt/pltu-tenayan/venv/
/opt/pltu-tenayan/logs/
/var/www/pltu-tenayan/frontend-build/
```

Deployment topology: FastAPI runs as a systemd service on internal port 8001; Nginx terminates TLS via Certbot and reverse-proxies `/api/*` to FastAPI; frontend served as static React build.

---

## TOPIC: Backup Manifest

source: pltu-tenayan-full-backup/BACKUP_MANIFEST.md

Backup type: full application snapshot.

Included:
- frontend and backend source
- `backend/.env` (original, from environment at backup time)
- `frontend/.env.example`
- dependency / cache / build artifacts present at backup time
- `database_backup.zip` (mongodump BSON + JSON-per-collection export + metadata)
- project documentation
- `LOCAL_SETUP.md`

Excluded:
- `frontend/.env` (original)
- legacy public download folders (avoids recursive packaging)
- legacy generated development metadata folders

---

## TOPIC: Backend Conventions

source: pltu-tenayan-full-backup/documentation.md

- Use projection `{"_id": 0}` on MongoDB reads.
- Persist datetimes via `datetime.now(timezone.utc)`; serialize as ISO strings.
- Never return raw ObjectId.
- Separate parsing, business rules, and route handlers when refactoring.
- All external routes under `/api`.

Recommended modularization order: extract auth + role dependency → laporan/dashboard routes → COA reconciliation → smart stock → Pydantic models to `models/` → service/repository layer.

When adding a new module: define use case, pick collection + response model, build endpoint with safe projection, build frontend page + auth header wiring, add navigation entry, add export/filter if relevant, add backend or e2e tests, document.

---

## TOPIC: Frontend Conventions

source: pltu-tenayan-full-backup/documentation.md

- All API calls MUST go through `process.env.REACT_APP_BACKEND_URL` and use the `/api` prefix.
- UI components from Shadcn/UI by default.
- Add `data-testid` to interactive and critical-information elements when changing UI.
- Keep `App.js` as the routing center; use `ProtectedRoute` for gated paths.
- Auth state lives in `AuthContext.js` (reads token from `localStorage`, validates via `/api/auth/me`, exposes `getAuthHeader()`).
- Long-term goal: shrink page files into reusable components.

---

## TOPIC: Critical Business Flows

source: pltu-tenayan-full-backup/documentation.md

Login: frontend POSTs `/api/auth/login` → backend validates bcrypt → returns JWT → frontend stores in `localStorage` → on reload, frontend rehydrates session via `GET /api/auth/me`.

CRUD: frontend fetches paginated list (must read `response.data.items`), then create/update/delete with bearer token.

Excel upload: frontend sends multipart/form-data → backend parses bytes → service maps complex headers to row values → persisted to MongoDB.

Smart Blending AI: frontend submits parameters → backend gathers context (6-month quality, smartstock, merit_order) → builds prompt → calls OpenRouter → returns JSON. Risk: provider quota or model availability can fail even when code is correct.

AI Intelligence with memory: frontend sends query + optional `session_id` → backend creates session if absent → backend pulls last messages from MongoDB → builds final prompt → model responds → user/assistant messages persisted to `ai_conversations`.

COA Reconciliation: data ingested via batch upload (3 files) or manual entry → backend computes deviation indicators → main page renders KPIs/table/chart/detail → anomalies trigger Propose Umpire → Dispute Monitor tracks state until umpire result lands → final data exportable to PDF/Excel.

---

## TOPIC: Known Issues and Technical Debt

source: pltu-tenayan-full-backup/documentation.md
source: pltu-tenayan-full-backup/readme.md
source: pltu-tenayan-full-backup/memory/PRD.md

- `server.py` is too large; modular routing is partially done but stalled.
- Several frontend pages still mix fetch/form/render in one file.
- Pagination shape is not fully uniform across older domains.
- Test coverage uneven across modules.
- Smart Blending AI can fail when the configured LLM provider quota or model is unavailable — environmental, not a code bug.
- Excel parser verification with `total penerimaan.xlsx` is pending a real sample file.
- Refactor regression risk areas: auth/role dependencies, pagination `items` shape, export endpoints, multipart upload, MongoDB serialization.

---

## TOPIC: Recommended Test Strategy

source: pltu-tenayan-full-backup/documentation.md

Backend priority: auth flow, pagination shape, Excel upload, COA reconciliation KPI/export, AI endpoints that can be mocked safely.

Frontend priority: login, large data-page loads, create/edit form submit, export buttons, supplier filter on Laporan, COA + Dispute Monitor pages.

Manual regression checklist: login OK; vessel/barge/trucking/biomassa pages not blank; pagination reads `response.data.items`; Laporan supplier filter works; COA PDF/Excel export succeeds; AI quick insight loads.

---

## TOPIC: AI Intelligence Module Surface

source: pltu-tenayan-full-backup/documentation.md
source: pltu-tenayan-full-backup/readme.md

Modules supported: general, blending, boiler, contract, logistics, smart stock, COA reconciliation. Each module has dedicated quick-insight endpoints in addition to the chat surface, and each persists conversation history through `ai_conversations`.

---

## TOPIC: Test Result Protocol Template

source: pltu-tenayan-full-backup/test_result.md

`test_result.md` is a YAML-structured communication template between main agent and testing agent. It defines block schemas for backend/frontend tasks (task name, implemented, working, file, stuck_count, priority, needs_retesting, status_history). The file as ingested contains only protocol instructions, no actual test results.

This file is operationally protocol-only; downstream planners should treat it as a runbook artifact, not a project requirement.

---

## TOPIC: Roadmap Hints (DOC-level — not authoritative)

source: pltu-tenayan-full-backup/documentation.md

P0: stabilize operational + COA modules; communicate AI budget dependency.
P1: modularize `server.py`; expand test coverage for auth, laporan, smart stock, AI sessions; break large frontend pages.
P2: standardize cross-domain DTO/schema; rework service layer for large domains; improve observability + domain error logging.
P3: backup & restore; dark/light mode toggle; richer activity log / audit trail.

NOTE: These are DOC-level roadmap hints. The roadmapper should reconcile these against the PRD prioritized backlog (which is canonical) before producing ROADMAP.md.
