# Decisions (ADR Intel)

This file aggregates architectural decisions extracted from ingested ADR-class documents.

## Summary

No ADR-class documents were ingested. The document set contains only PRD, SPEC, and DOC artifacts.

The roadmapper will need to derive decisions from the PRD's tech-stack section and the implicit architectural choices recorded in `documentation.md` and `readme.md`. None of those choices are presently formalized as locked ADRs.

## Implicit Decisions Surfaced From Lower-Precedence Sources

These are NOT locked ADR decisions. They are derived from PRD/DOC content and should be lifted to ADR status during the roadmapping phase if they are intended to be load-bearing.

### IMPLICIT-001: MongoDB as primary datastore
- source: pltu-tenayan-full-backup/memory/PRD.md (PRD)
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md (SPEC)
- source: pltu-tenayan-full-backup/readme.md (DOC)
- status: implicit (not locked)
- statement: MongoDB (accessed via Motor async driver) is used as the application database.
- scope: persistence layer

### IMPLICIT-002: FastAPI backend
- source: pltu-tenayan-full-backup/memory/PRD.md (PRD)
- source: pltu-tenayan-full-backup/readme.md (DOC)
- source: pltu-tenayan-full-backup/documentation.md (DOC)
- status: implicit (not locked)
- statement: Backend is FastAPI with async patterns; entrypoint `server.py` currently monolithic.
- scope: backend framework

### IMPLICIT-003: React 19 frontend
- source: pltu-tenayan-full-backup/memory/PRD.md (PRD)
- source: pltu-tenayan-full-backup/readme.md (DOC)
- status: implicit (not locked)
- statement: Frontend is React 19 with Tailwind CSS, Shadcn/UI, Recharts. Bundler/runtime via Yarn.
- scope: frontend framework

### IMPLICIT-004: JWT authentication with role-based access
- source: pltu-tenayan-full-backup/memory/PRD.md (PRD)
- source: pltu-tenayan-full-backup/API_REFERENCE.md (SPEC)
- status: implicit (not locked)
- statement: JWT bearer tokens; three roles `admin`, `operator`, `viewer`; bcrypt password hashing.
- scope: authn/authz

### IMPLICIT-005: LLM provider — Google Gemini via Emergent Integrations
- source: pltu-tenayan-full-backup/memory/PRD.md (PRD)
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md (SPEC)
- source: pltu-tenayan-full-backup/documentation.md (DOC)
- status: implicit (not locked)
- statement: AI calls flow through `emergentintegrations`; default model `gemini-2.5-flash`. Falls back to `EMERGENT_LLM_KEY` if no per-user custom key.
- scope: AI integration
- known issue: requests fail with `BudgetExceededError` when key budget exhausted — not a code defect.

### IMPLICIT-006: API path prefix `/api/*`
- source: pltu-tenayan-full-backup/API_REFERENCE.md (SPEC)
- source: pltu-tenayan-full-backup/documentation.md (DOC)
- status: implicit (not locked)
- statement: All backend HTTP routes live under `/api`; frontend resolves base via `REACT_APP_BACKEND_URL`.
- scope: routing convention

### IMPLICIT-007: MongoDB projection contract `{"_id": 0}`
- source: pltu-tenayan-full-backup/documentation.md (DOC)
- source: pltu-tenayan-full-backup/API_REFERENCE.md (SPEC)
- status: implicit (not locked)
- statement: Backend MUST use projection `{"_id": 0}` and surface a UUID `id` field instead of MongoDB `_id` to clients.
- scope: persistence/serialization convention

### IMPLICIT-008: Pagination response shape
- source: pltu-tenayan-full-backup/API_REFERENCE.md (SPEC)
- status: implicit (not locked)
- statement: Paginated list endpoints return `{ items, total, page, page_size, total_pages }`. Frontend MUST read `response.data.items`.
- scope: API contract

## Notes For Roadmapper

- No `locked: true` ADRs were detected. Therefore no LOCKED-vs-LOCKED conflicts exist.
- During roadmapping, consider lifting IMPLICIT-001 through IMPLICIT-008 into formal ADRs so future planners have authoritative decisions to honor.
