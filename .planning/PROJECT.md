# EMITS — PLTU Tenayan Fuel Management

## What This Is

EMITS is the in-production Fuel Management System for PLTU Tenayan: a full-stack application (FastAPI + MongoDB + React 19) used by the operations team and admins to manage coal/biomass receipts across vessel/barge/trucking/biomassa/PO Batubara/merit-order modes, monitor fuel quality, run COA reconciliation with umpire dispute workflow, generate operational reports, and run AI analyses (general, blending, boiler, contract, logistics, smart-stock, COA). The system currently runs on a single VPS with real production data. Milestones v1.1 and v1.2 are shipped; v1.3 focuses on production operations, backend maintainability, and decision intelligence.

## Current State

**Shipped version:** v1.2, completed 2026-05-13.
**Current milestone:** v1.3 - Production Operations & Decision Intelligence.

v1.1 delivered production audit/onboarding, authentication stabilization, documentation/test stabilization, collection naming cleanup, OpenRouter/AI chat operational unblocks, backend refactor foundation, advanced filters, dashboard control room, alerts, formal dispute/umpire workflow, Excel import preview, audit trail v2, management reports, and contextual AI.

v1.2 delivered backup automation, COA import governance, production deployment hardening, dashboard command center v3, management report v2, supplier scorecards, source-traceable exports, and deterministic AI advisor recommendations with Indonesian memo drafting.

**Audit status:** v1.2 closed with `tech_debt` status only. See `.planning/milestones/v1.2-MILESTONE-AUDIT.md`.

## Current Milestone: v1.3 Production Operations & Decision Intelligence

**Goal:** Move EMITS from "feature-complete enough" toward a more operable, maintainable, decision-oriented production system: static nginx deployment, real drilldowns, cleaner backend service boundaries, data quality monitoring, trend analytics, safer AI advice, and stronger operator UI polish.

**Target features:**
- Production VPS cutover to static nginx frontend with visible service/smoke status.
- Dashboard drilldowns that carry filters into stock, arrivals, COA, dispute, and reporting pages.
- Backend refactor of shared dashboard/report/advisor calculations into tested service boundaries.
- Data quality monitoring for stale, duplicate, missing, outlier, and inconsistent operational records.
- Multi-period trend analytics for stock, arrivals, supplier quality, COA deltas, and disputes.
- AI advisor v3 that can explain trend/data-quality context while preserving deterministic fallback and source limits.
- UI/UX polish across dashboard, reports, filters, states, and common operator workflows.

## Latest Milestone: v1.2 Operational Reliability & Data Governance

**Goal delivered:** Make EMITS safer to operate as production software by automating backups, hardening deployment, making COA data imports reversible/validated, and polishing the control-room experience.

**Delivered features:**
- Scheduled database/application backup with retention, history, restore validation, and operator-visible status.
- COA workbook import governance with preview, validation, duplicate detection, import history, and rollback-safe behavior.
- Production deployment hardening for repeatable service restart, env/secret handling, health checks, and smoke verification.
- Dashboard command center v3 with clearer stock risk, arrival realization, dispute/umpire, and supplier quality signals.
- Management report and AI advisor v2 with source-backed executive summaries, supplier scorecards, and recommended next actions.
- Engineering cleanup for React hook warnings, focused test credential loading, and repository layout hygiene.

**Carried forward into v1.3:**
- Production VPS cutover to nginx static frontend and service monitoring.
- Deeper drilldown adoption of dashboard query filters inside destination pages.
- LLM-polished advisor narrative on top of the current bounded, deterministic report payload.
- Multi-month trend analytics and forecasting beyond current rule-based projections.

## Core Value

Operators and admins at PLTU Tenayan can trust the system as the single source of truth for fuel-receipt data, COA reconciliation, and AI-assisted decision support — every record they enter or upload survives reliably, every report exports cleanly, and login/auth never gets in the way.

## Requirements

### Validated

<!-- Shipped and confirmed in production per PRD checklist. Locked unless explicit re-scoping. -->

- ✓ REQ-auth-rbac (admin/operator/viewer enforced server-side)
- ✓ REQ-rekap-penerimaan-bb (vessels=111, barges, trucking=461, biomassa=45, po_batubara=301, merit_order=58)
- ✓ REQ-dashboard-advanced (basic + advanced visualizations)
- ✓ REQ-export-pdf-excel (laporan + COA reconciliation export)
- ✓ REQ-ai-intelligence-agent (7 modules + session memory)
- ✓ REQ-smart-stock (smartstock=207, sumberpemakaian=208)
- ✓ REQ-smart-blending-ai (functional; degraded operationally on LLM budget)
- ✓ REQ-coa-reconciliation (coa=721, umpire workflow live)
- ✓ REQ-i18n-indonesian-ui
- ✓ REQ-dark-saas-ui
- ✓ REQ-pagination-server-side
- ✓ REQ-coa-export
- ✓ REQ-laporan-supplier-filter
- ✓ REQ-developer-docs-suite (initial generation; due for refresh)
- ✓ BACKUP2-01..05: Scheduled backup automation, retention, history, restore validation, and backup health visibility — v1.2
- ✓ COAIMP-01..06: Safe COA workbook import preview, validation, diff/duplicate detection, history, rollback, and preservation of dispute workflow state — v1.2
- ✓ DEPLOY-01..05: Production service hardening, env/secret runbook, health/smoke checks, repeatable deploy, and repository hygiene — v1.2
- ✓ DASH3-01..05: Dashboard command center v3 for stock risk, arrival realization, COA dispute/umpire, supplier quality, and drilldowns — v1.2
- ✓ REPORT2-01..04: Management reporting v2 with monthly executive summary, supplier scorecard, PDF/Excel export, and source traceability — v1.2
- ✓ AI2-01..04: AI advisor v2 with bounded source citations, recommended next actions, draft memo support, and guardrails — v1.2
- ✓ CLEANUP-01..03: React hook warning register, focused pytest credential loading, and local artifact hygiene — v1.2

### Active

- [x] OPS3-01..05: Static nginx frontend cutover, runtime health/status visibility, deploy smoke evidence, and production runbook completion.
- [x] DRILL3-01..05: Dashboard drilldowns consume filters on destination pages, show active context, preserve back navigation, and handle empty states.
- [x] REF3-01..06: Backend service-boundary refactor for shared dashboard/report/advisor calculations, normalization helpers, tests, and response compatibility.
- [x] DQ3-01..06: Data quality monitor for stale, missing, duplicate, outlier, and inconsistent records with visible/exportable issue evidence.
- [x] TREND3-01..05: Multi-period trend analytics and forecasting for stock, arrivals, suppliers, COA deltas, disputes, and exports.
- [x] AI3-01..05: AI advisor v3 with trend/data-quality explanations, optional LLM narrative, deterministic fallback, limitations, and guardrail tests.
- [ ] UX3-01..05: Operator UI/UX polish for dashboard/report layouts, workflow click reduction, responsive stability, states, and hook-warning cleanup.

### Out of Scope

- Multi-tenant or multi-plant deployment — single-plant scope (PLTU Tenayan only).
- Replacing MongoDB with another datastore — IMPLICIT-001 holds; migration is not on the table this round.
- Replacing FastAPI/React stacks — incremental refactor only (IMPLICIT-002, IMPLICIT-003).
- Switching LLM provider away from Gemini via emergentintegrations — IMPLICIT-005 holds; multi-provider abstraction deferred.
- Mobile app — web-first remains the policy.
- Real-time websockets / live collaboration — not part of operational workflow.
- Inline test credentials in committed artifacts — see local memory/test_credentials.md (NOT committed) instead.

## Context

Production deployment: VPS `103.150.197.225`, Ubuntu Linux, single-host topology — nginx terminates HTTP and reverse-proxies `/api/*` to FastAPI (uvicorn on internal port 8001), serving the React build as static. MongoDB lives on the same host on the internal network.

Live data inventory (snapshot at planning time):

| Collection           | Records | Notes                                  |
|----------------------|---------|----------------------------------------|
| vessels              | 111     |                                        |
| trucking             | 461     | largest receipt collection             |
| coa_reconciliation   | 754     | updated via combined COA workbook import through 2026-04-27 |
| biomassa             | 45      |                                        |
| smartstock           | 207     | active read target (legacy: smart_stock)|
| po_batubara          | 301     |                                        |
| merit_order          | 58      |                                        |
| sumberpemakaian      | 208     | (legacy: sumber_pemakaian)             |
| ai_chat_history      | 10      | (legacy of: ai_conversations)          |
| users                | 7       | admin/operator/viewer mix              |

Operational situation: v1.2 is shipped and archived. The combined COA workbook update has been imported locally and pushed as code/docs support. The system now has safer backup, import governance, deployment, dashboard, reporting, and AI-advisor surfaces. v1.3 should convert those surfaces into stronger production operations and day-to-day decision workflows.

Test credentials: present in upstream PRD but explicitly NOT committed. See local `memory/test_credentials.md` (gitignored).

## Constraints

- **Tech stack — backend (LOCKED, implicit/inherited)**: FastAPI on Python 3.11+ with Motor async MongoDB driver, JWT (python-jose / PyJWT + bcrypt), Pandas/OpenPyXL/xlrd for Excel ingestion, ReportLab for PDF, emergentintegrations for LLM. Per IMPLICIT-001, IMPLICIT-002. Promote to formal ADR in Phase 3.
- **Tech stack — frontend (LOCKED, implicit/inherited)**: React 19 + React Router 7 + Tailwind + Shadcn/UI + Axios + Recharts + jsPDF + xlsx, built via Yarn. Per IMPLICIT-003. Promote to formal ADR in Phase 3.
- **Datastore (LOCKED, implicit/inherited)**: MongoDB as primary datastore via Motor. Per IMPLICIT-001. Promote to formal ADR.
- **Auth contract (LOCKED, implicit/inherited)**: JWT bearer; three roles `admin` / `operator` / `viewer`; bcrypt password hashing; auth header `Authorization: Bearer <JWT>`; HTTP errors 400/401/403/404/500 per SPEC. Per IMPLICIT-004 + CONS-auth-header.
- **Routing (LOCKED, implicit/inherited)**: All HTTP routes under `/api/*`; frontend resolves base via `REACT_APP_BACKEND_URL`. Per IMPLICIT-006 + CONS-api-base.
- **Persistence contract (LOCKED, SPEC)**: MongoDB reads MUST use projection `{"_id": 0}`; public identifier is application-level UUID `id`; datetimes serialized as ISO 8601. Per CONS-projection-id-contract + IMPLICIT-007.
- **Pagination contract (LOCKED, SPEC)**: Paginated list endpoints MUST return `{ items, total, page, page_size, total_pages }`; default page=1, page_size=50; cap 500 (operational) / 50000 (smart-stock). Frontend MUST read `response.data.items`. Per CONS-pagination-shape + IMPLICIT-008.
- **AI provider (LOCKED operationally, implicit/inherited)**: Google Gemini (`gemini-2.5-flash`) via `emergentintegrations`; falls back to `EMERGENT_LLM_KEY` when no per-user key. Per IMPLICIT-005. Operational dependency — not a code defect when budget exhausted.
- **Smart Blending math (LOCKED, SPEC)**: Linear weighted-average blend across GCV/Ash/Sulphur/TM/IM/VM/FC; constraint inequalities GCV_blend ≥ target, Ash/Sulphur/TM/IM ≤ max, VM/FC ≥ min; ±5% prediction tolerance; output JSON shape locked. Per CONS-blending-formula / -input-ranges / -constraint-validation / -ai-output / -tolerance.
- **Hosting**: Self-hosted VPS (Linux, single host) — FastAPI + MongoDB + nginx on internal network at `103.150.197.225`. No managed cloud services in scope.
- **Security**: Test credentials live in local `memory/test_credentials.md` only — must NEVER be committed. CORS controlled via `CORS_ORIGINS` env. JWT secret in `JWT_SECRET` env (not committed).
- **Tech debt — collection naming**: `smartstock` vs `smart_stock`, `sumber_pemakaian` vs `sumberpemakaian`, `app_settings` vs `settings`, `ai_chat_history` vs `ai_conversations` are SPEC-flagged dual names; standardization is tracked work in Phase 5, not silent.
- **Backlog priority**: PRD's P0..P3 backlog is canonical and supersedes DOC-level roadmap hints (`documentation.md` section "Roadmap Hints").

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Stabilize before upgrade | Owner is learning the system on real production data; rushing to refactor risks data/UX regressions on a live plant operation | — Pending (drives Phases 1–5) |
| Promote IMPLICIT-001..008 to locked ADRs | Currently zero locked ADRs; future ingest passes have no authoritative decision anchors | ✓ Applied (Phase 3 plan 03-01, 2026-05-10) |
| Sanitize test credentials out of all committed artifacts | PRD ships test credentials inline (literal values live only in `pltu-tenayan-full-backup/memory/test_credentials.md`); committing replicates a credential leak | ✓ Applied (this PROJECT.md does not include them) |
| Drop DOC→PRD back-reference when regenerating cross_refs | Prevents re-introducing the documented PRD↔DOC citation cycle | ✓ Applied (synthesizer guidance honored) |
| Defer LLM provider abstraction to backlog | Single-provider Gemini-via-emergentintegrations is documented and working; multi-provider is enterprise-tier scope creep | — Pending (out of scope this round) |
| Treat collection naming debt as a tracked phase, not a silent migration | SPEC explicitly flags it; silent migration risks data loss against 721-row COA + 461-row trucking | — Pending (Phase 5) |
| Single-host VPS topology stays | Production is already there with real data; horizontal split is not justified at current load | — Pending (revisit if RAM/IO bottleneck shows up) |
| v1.2 starts with operational reliability over new domain sprawl | EMITS is now live enough that backup, import safety, deployment repeatability, and auditability reduce more risk than adding unrelated modules | ✓ Applied (v1.2 roadmap) |
| Close v1.2 with accepted non-blocking tech debt | Audit found no product or integration blockers; metadata backfill, hook warning register, nginx frontend cutover, and optional LLM polish can be handled later | ✓ Applied (v1.2 archive, 2026-05-13) |
| v1.3 prioritizes operations plus decision intelligence | The app already has core modules; the next leverage is making production status, drilldowns, data quality, trends, and AI advice more actionable and maintainable | — Pending (v1.3 roadmap) |

---
*Last updated: 2026-05-13 after v1.3 milestone start.*


## ADR Cross-Links (Phase-3 lock-in)

Phase-3 (plan 03-01, 2026-05-10) promoted IMPLICIT-001..008 to formal locked
ADR files under `.planning/decisions/`. Future planning rounds and downstream
docs cite the ADR path; the IMPLICIT-NNN rows in the "Constraints" section
above remain intact for backwards-compatible greps but are now superseded
by the locked ADRs.

| IMPLICIT row | ADR file | Subject |
|--------------|----------|---------|
| IMPLICIT-001 | [`.planning/decisions/ADR-001-mongodb-datastore.md`](decisions/ADR-001-mongodb-datastore.md) | MongoDB (via Motor) as primary datastore |
| IMPLICIT-002 | [`.planning/decisions/ADR-002-fastapi-python-backend.md`](decisions/ADR-002-fastapi-python-backend.md) | FastAPI / Python 3.11+ backend stack |
| IMPLICIT-003 | [`.planning/decisions/ADR-003-react-frontend-stack.md`](decisions/ADR-003-react-frontend-stack.md) | React 19 + Tailwind + Shadcn frontend |
| IMPLICIT-004 | [`.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md`](decisions/ADR-004-jwt-bcrypt-three-role-auth.md) | JWT + bcrypt + 3-role auth model |
| IMPLICIT-005 | [`.planning/decisions/ADR-005-gemini-via-emergentintegrations.md`](decisions/ADR-005-gemini-via-emergentintegrations.md) | Gemini via emergentintegrations (v1 LLM) |
| IMPLICIT-006 | [`.planning/decisions/ADR-006-api-prefix-and-frontend-base-url.md`](decisions/ADR-006-api-prefix-and-frontend-base-url.md) | /api/* prefix + REACT_APP_BACKEND_URL |
| IMPLICIT-007 | [`.planning/decisions/ADR-007-persistence-projection-uuid-iso.md`](decisions/ADR-007-persistence-projection-uuid-iso.md) | Mongo projection + UUID id + ISO 8601 |
| IMPLICIT-008 | [`.planning/decisions/ADR-008-pagination-shape.md`](decisions/ADR-008-pagination-shape.md) | Pagination envelope `{items,total,page,page_size,total_pages}` |

Each ADR is locked dated 2026-05-10 and cites at least one code anchor in
`pltu-tenayan-full-backup/...:<line>` proving the decision is in effect today
plus the related CONS-* constraint from `.planning/intel/constraints.md`.
