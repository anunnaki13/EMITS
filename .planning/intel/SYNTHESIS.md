# Synthesis Summary

Entry point for downstream consumers (notably `gsd-roadmapper`). This file summarizes the per-doc intel files in this directory and the conflict report at `.planning/INGEST-CONFLICTS.md`.

Mode: `new` (fresh bootstrap; no prior `.planning/` artifacts to merge against)
Precedence applied: `ADR > SPEC > PRD > DOC`

---

## Doc Counts

Total classified docs ingested: **10**

Breakdown by type:
- ADR: **0**
- PRD: **1** (`pltu-tenayan-full-backup/memory/PRD.md`)
- SPEC: **3**
  - `pltu-tenayan-full-backup/API_REFERENCE.md`
  - `pltu-tenayan-full-backup/DATABASE_SCHEMA.md`
  - `pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md` (medium confidence)
- DOC: **6**
  - `pltu-tenayan-full-backup/readme.md`
  - `pltu-tenayan-full-backup/documentation.md` (medium confidence)
  - `pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md`
  - `pltu-tenayan-full-backup/LOCAL_SETUP.md`
  - `pltu-tenayan-full-backup/BACKUP_MANIFEST.md`
  - `pltu-tenayan-full-backup/test_result.md` (medium confidence — protocol template, no payload)
- UNKNOWN-low: **0**

---

## Decisions

Locked decisions: **0** (no `locked: true` ADR was ingested)

Implicit decisions surfaced from PRD/SPEC/DOC for the roadmapper to consider lifting to formal ADRs: **8** (recorded as IMPLICIT-001 through IMPLICIT-008 in `decisions.md`):

- IMPLICIT-001: MongoDB as primary datastore (Motor async)
- IMPLICIT-002: FastAPI backend (uvicorn, monolithic `server.py`)
- IMPLICIT-003: React 19 frontend (Tailwind + Shadcn/UI + Recharts)
- IMPLICIT-004: JWT authentication with `admin` / `operator` / `viewer` roles
- IMPLICIT-005: LLM provider — Google Gemini (`gemini-2.5-flash`) via emergentintegrations
- IMPLICIT-006: All HTTP routes under `/api/*`
- IMPLICIT-007: MongoDB projection `{"_id": 0}` and UUID `id` contract
- IMPLICIT-008: Paginated list response shape `{ items, total, page, page_size, total_pages }`

Source: `intel/decisions.md`

---

## Requirements

PRD-derived requirement entries: **20** (16 actively scoped + 4 P2/P3 backlog hints; full IDs and acceptance criteria in `intel/requirements.md`):

Active scope:
- REQ-auth-rbac
- REQ-rekap-penerimaan-bb
- REQ-dashboard-advanced
- REQ-export-pdf-excel
- REQ-ai-intelligence-agent
- REQ-smart-stock
- REQ-smart-blending-ai
- REQ-coa-reconciliation
- REQ-i18n-indonesian-ui
- REQ-dark-saas-ui
- REQ-pagination-server-side
- REQ-coa-export
- REQ-laporan-supplier-filter
- REQ-ai-conversation-memory
- REQ-developer-docs-suite
- REQ-fix-smart-blending-timeout (P1; BLOCKED on LLM budget)
- REQ-verify-excel-parser-total-penerimaan (P1; BLOCKED awaiting sample)

Backlog hints:
- REQ-refactor-server-py (P2)
- REQ-advanced-filtering-date-range (P2)
- REQ-dashboard-period-filter (P3)
- REQ-dark-light-mode-toggle (P3)
- REQ-data-backup-restore (P3)
- REQ-audit-trail (P3)

Source: `intel/requirements.md`

---

## Constraints

SPEC-derived constraint entries: **26** in `intel/constraints.md`.

Type breakdown:
- api-contract: 11 (base URL, auth header, pagination shape, vessel/barge/trucking/biomassa, po-batubara, merit-order, AI query, smart-stock, smart-blending, settings COA, COA reconciliation)
- schema: 12 (projection contract, collection inventory, naming-debt, users, vessels, barges, trucking, biomassa, po_batubara, merit_order, smartstock, sumber_pemakaian, coa_reconciliation, app_settings, ai_conversations, logical relations)
- protocol: 6 (Smart Blending math, parameter ranges, constraint validation, data sources, AI JSON output, classification, measurement-basis)
- nfr: 1 (Smart Blending ±5% prediction tolerance)

Source: `intel/constraints.md`

---

## Context Topics

DOC-derived narrative topics: **12** in `intel/context.md`:

- Project Identity
- Tech Stack (narrative)
- Project Structure
- Environment Variables
- Local Development Runbook
- VPS Deployment Architecture
- Backup Manifest
- Backend Conventions
- Frontend Conventions
- Critical Business Flows
- Known Issues and Technical Debt
- Recommended Test Strategy
- AI Intelligence Module Surface
- Test Result Protocol Template
- Roadmap Hints (DOC-level — not authoritative)

Source: `intel/context.md`

---

## Conflicts

- BLOCKERS: **0**
- WARNINGS: **1** (cross-reference citation cycle between PRD and DOC — citation, not synthesis loop; documented for downstream awareness)
- INFO: **5** (no ADR layer; SPEC > DOC on API; SPEC > DOC on Smart Blending math; collection naming debt; PRD ships test credentials inline)

Detail: `.planning/INGEST-CONFLICTS.md`

---

## Pointers

- Decisions intel: `.planning/intel/decisions.md`
- Requirements intel: `.planning/intel/requirements.md`
- Constraints intel: `.planning/intel/constraints.md`
- Context intel: `.planning/intel/context.md`
- Conflicts report: `.planning/INGEST-CONFLICTS.md`
- Per-doc classifications: `.planning/intel/classifications/*.json`

---

## Notes for Roadmapper

1. No locked ADRs exist yet. Consider promoting IMPLICIT-001..008 (or a subset) to formal locked ADRs so future ingests have authoritative anchors that survive merge passes.
2. The PRD is the only authoritative product source; its prioritized backlog (P0..P3) is canonical and supersedes the DOC-level roadmap hints in `documentation.md`.
3. Smart Blending AI is functional but blocked operationally on LLM budget — not a code-level blocker. Ensure the roadmap distinguishes operational vs engineering items.
4. Collection naming debt (smartstock vs smart_stock, sumber_pemakaian vs sumberpemakaian, app_settings vs settings, ai_chat_history vs ai_conversations) is flagged in the SPEC itself and should appear in any "Tech Debt" track.
5. Test credentials are present in the PRD; sanitize before reflecting in any committed PROJECT.md.
6. The cross-reference cycle warning is informational; recommended remediation is to trim the DOC → PRD back-reference rather than altering content.
