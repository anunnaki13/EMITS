# ADR-002: FastAPI on Python 3.11+ as Backend Stack

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-002.

## Context

The EMITS backend is the single process that owns every server-side responsibility: HTTP routing, JWT auth, MongoDB I/O via Motor (ADR-001), Excel parsing and PDF rendering for operational reports, and LLM integration for the AI Intelligence Agent (ADR-005). All of it lives today in `pltu-tenayan-full-backup/backend/server.py`, served by `uvicorn` against a single VPS host.

The deployment is in production with real data; there is no operational complaint pointing at the framework choice. FastAPI's built-in OpenAPI generation (`/openapi.json`) is the canonical schema source for the regenerated `API_REFERENCE.md` (Phase 3, plan 03 — D-04). Async-first request handling pairs cleanly with `motor`'s async Mongo driver. The existing dependency set in `backend/requirements.txt` is already battle-tested across the eight Excel ingest paths (vessels, barges, trucking, biomassa, PO Batubara, merit-order, smart-stock, COA reconciliation), the COA reconciliation workflow, the laporan/dashboard endpoints, and the AI query endpoints.

This ADR locks the backend framework + supporting library set so future plans cite it directly instead of re-deriving from PROJECT.md every time. It does not pretend the modular refactor (DEBT-02 in PROJECT.md) is finished — `server.py` is still monolithic — but the framework choice itself is settled.

## Decision

Use **FastAPI 0.110.x on Python 3.11+** as the EMITS backend framework, served by **uvicorn 0.25.x**.

Locked supporting libraries (pinned in `backend/requirements.txt`):

- **Mongo driver:** `motor==3.3.1` + `pymongo==4.5.0` (per ADR-001).
- **Auth:** `bcrypt==4.1.3` for password hashing, `PyJWT==2.10.1` for JWT encode/decode (also `python-jose==3.5.0` for legacy compatibility); see ADR-004.
- **Excel ingestion:** `pandas==2.3.3`, `openpyxl==3.1.5`, `xlrd==2.0.2` for `.xls` legacy support, `python-multipart==0.0.21` for upload form handling.
- **PDF rendering:** `reportlab==4.4.9` for COA / laporan / dashboard PDF exports.
- **LLM integration:** OpenRouter via `backend/app/ai/openrouter_client.py`; see ADR-005.
- **Validation:** `pydantic==2.12.5` for request/response models, `email-validator==2.3.0` for `EmailStr`.
- **Cross-cutting:** `python-dotenv==1.2.1` for env loading, `httpx==0.28.1` for outbound HTTP, `aiohttp==3.13.3` for streaming.

The full pin list is `backend/requirements.txt` and is the single source of truth — this ADR captures the *role* each library plays, not version drift.

## Consequences

**Positive:**

- `/openapi.json` is generated for free and is the canonical schema source for `API_REFERENCE.md` regeneration (Phase 3, plan 03; D-04, D-06).
- Pydantic v2 request/response models give automatic input validation; CONS-auth-header's "400 validation" error is honored via the path-scoped `auth_validation_handler` (D-AUTH-01) without bespoke validation code.
- Async request handlers + `motor` async driver eliminate thread-pool overhead for Mongo I/O.
- One process serves every concern (auth, CRUD, uploads, AI, reports), keeping the deployment surface small and the runbook (LOCAL_SETUP.md "VPS Service Recovery") simple — one `uvicorn` command brings everything back.
- Python ecosystem covers Excel + PDF + Pandas data manipulation natively, which matches the operational reality of an Indonesian fuel-management plant where reports come from `.xlsx` and `.xls` files daily.

**Negative / accepted tradeoffs:**

- `server.py` is monolithic today (DEBT-02 in PROJECT.md tracks the modular split). This ADR does NOT mandate the refactor; it just locks the framework underneath.
- Python's GIL caps single-process CPU parallelism; if AI / report rendering ever becomes CPU-bound at scale, scaling is process-fan-out (uvicorn workers), not in-process threads. Not a current bottleneck.
- Dependency set is wide (Pandas + ReportLab + Mongo + LLM client dependencies all in one venv); install time is non-trivial. Mitigated by pinning every version in `requirements.txt` and committing the pin file.

## Alternatives Considered

- **Flask** — rejected. No built-in OpenAPI generation; we rely on `/openapi.json` as the API_REFERENCE source-of-truth. Async story weaker than FastAPI's. Switching would force a hand-curated OpenAPI spec, which is exactly the doc-drift risk the ingest already flagged.
- **Django + DRF** — rejected. ORM/admin overhead unneeded with Mongo (ADR-001); the REST routes are intentionally simple `/api/*` (ADR-006); migration tooling adds work without solving a current problem.
- **Node.js / Express** — rejected. Would require rewriting the eight Excel-ingest pipelines and ReportLab-equivalent PDF generation in the JS ecosystem; Pandas + openpyxl + xlrd parity in JS is poor. Cost-of-rewrite far exceeds any latency benefit at current load.
- **Go (Gin / Echo)** — rejected. Same Excel/PDF parity problem; team skill set and existing service code are Python.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-002 row for FastAPI on Python with Motor, JWT, Excel ingestion, PDF export, and OpenRouter-backed LLM integration.
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/backend/server.py:1` — `from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, Response, Request`
  - `pltu-tenayan-full-backup/backend/server.py:37` — `app = FastAPI(title="PLTU Tenayan Fuel Management System")`
  - `pltu-tenayan-full-backup/backend/requirements.txt:22` — `fastapi==0.110.1`
  - `pltu-tenayan-full-backup/backend/requirements.txt:7` — `bcrypt==4.1.3`
  - `pltu-tenayan-full-backup/backend/requirements.txt:60` — `motor==3.3.1`
  - `pltu-tenayan-full-backup/backend/requirements.txt:69` — `pandas==2.3.3`
  - `pltu-tenayan-full-backup/backend/requirements.txt:67` — `openpyxl==3.1.5`
  - `pltu-tenayan-full-backup/backend/requirements.txt:125` — `xlrd==2.0.2`
  - `pltu-tenayan-full-backup/backend/requirements.txt:128` — `reportlab==4.4.9`
  - `pltu-tenayan-full-backup/backend/requirements.txt:122` — `uvicorn==0.25.0`
- **Related constraints:** none direct (ADR-006 covers `/api` routing; ADR-004 covers auth library choices; ADR-005 covers LLM library).
- **Sibling docs:** `pltu-tenayan-full-backup/LOCAL_SETUP.md` (uvicorn invocation), `pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md` (production deploy).
