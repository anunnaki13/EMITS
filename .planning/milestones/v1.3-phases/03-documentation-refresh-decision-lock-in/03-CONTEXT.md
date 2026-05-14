# Phase 03: Documentation Refresh & Decision Lock-In - Context

**Gathered:** 2026-05-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Reconcile every committed doc against the live VPS install, formalize IMPLICIT-001..008 as locked ADRs, and surface current operational reality in a Known Issues section. Output: regenerated/audited docs (README, documentation.md, API_REFERENCE, DATABASE_SCHEMA, DEPLOYMENT_GUIDE, Smart_Blending_AI_Formula, LOCAL_SETUP), 8 ADR files under `.planning/decisions/`, and a Known Issues section that reflects login-mitigated / Smart Blending budget / parser pending status.

**In scope:** DOCS-01..05, STAB-04 (ADR promotion), Phase-2 doc carry-forwards (VPS recovery runbook, AUTH_CONTRACT cross-link, ROADMAP wording fix for AUTHFIX-03).

**Out of scope:** Code changes (server.py, frontend) beyond what's needed to fix verifiable doc-vs-code drift; new architectural decisions (this phase only locks already-implicit ones); test coverage expansion (Phase 4 owns).

</domain>

<decisions>
## Implementation Decisions

### ADR format
- **D-01:** Full MADR per file. 8 files at `.planning/decisions/ADR-001-mongodb-datastore.md` through `ADR-008-pagination-shape.md`. Each ADR contains: Status / Context / Decision / Consequences / Alternatives Considered / References. Promoted IMPLICIT-001..008 mapping is preserved in the References section of each.
- **D-02:** Status field uses `Accepted (locked, YYYY-MM-DD) — promoted from IMPLICIT-NNN`. Future ADRs added later in the project use the same format.
- **D-03:** Each ADR's References section MUST cite (a) the source IMPLICIT line in PROJECT.md, (b) at least one code anchor (file:line) proving the decision is in effect, and (c) any related CONS-* constraint.

### API_REFERENCE source-of-truth
- **D-04:** Generate API_REFERENCE.md from FastAPI's `/openapi.json` (canonical machine-truth) plus hand-curated narrative sections. Schema snapshot taken from production VPS at `http://103.150.197.225:8013/openapi.json` (read-only GET; no mutation).
- **D-05:** Hand-curated sections layered on top of generated tables: (1) Auth Contract — pulls from existing `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` (Phase 2 deliverable); (2) Pagination Contract — from CONS-pagination-shape; (3) Error Code Map — 400/401/403/404/422/500 with semantic meaning per CONS-auth-header.
- **D-06:** API_REFERENCE.md generation script lives at `pltu-tenayan-full-backup/scripts/regenerate_api_reference.py` so future drift can be caught with a single command. Output is hand-edited only in the narrative sections, never in the generated tables.

### Spot-check method (Claude's Discretion — sensible default)
- **D-07:** Behavior verification (per-endpoint): use Phase 2 pattern — local uvicorn on test DB (the conftest.py + isolated `pltu_tenayan_test_*` fixtures established in plan 02-02). NO writes to live `pltu_tenayan` collection. Only read-only curl to live VPS for `/openapi.json` schema fetch and `/api/health` ping.
- **D-08:** Endpoints that cannot be exercised locally without external services (e.g., AI endpoints requiring LLM key) are marked `verified: schema-only` in the audit log. Their behavior validation is deferred to Phase 6.

### Known Issues placement (Claude's Discretion — sensible default)
- **D-09:** Known Issues lives as a new H2 section in `pltu-tenayan-full-backup/documentation.md` (the canonical operator-facing doc per ROADMAP success criterion 1). Format: bulleted list with status badge (mitigated / pending-Phase-N / accepted) + cite-to file path. README.md gets a one-line pointer to documentation.md#known-issues.
- **D-10:** Initial Known Issues entries (Phase-3 must include): (a) Login bug — mitigated via ResizeObserver suppressor (cite LOGIN_BUG_RESOLUTION.md, regression test in test_auth_session.py); (b) Smart Blending budget exhausted — Phase 6 unblocks; (c) Excel parser verification pending — Phase 6; (d) Collection naming debt — Phase 5; (e) audit-probe-* synthetic users in production — already cleaned, kept as record.

### VPS service-recovery runbook (Phase-2 carry-forward)
- **D-11:** Recovery runbook lives in `pltu-tenayan-full-backup/LOCAL_SETUP.md` under new H2 "VPS Service Recovery (post-restart)". DEPLOYMENT_GUIDE.md gets a one-line pointer back. Content: exact `uvicorn` command (with venv path) + `yarn start` command + how to verify (`curl /api/health`).
- **D-12:** Optional pm2/systemd auto-restart units are documented as a Phase-3 deliverable comment but the actual unit files are deferred — flagged for a future Phase 3.1 INSERTED phase if the user wants it.

### ROADMAP wording fix (Phase-2 carry-forward)
- **D-13:** Phase-3 must amend ROADMAP.md Phase 2 success criterion 3 from "operator-only upload" to "admin+operator upload (no truly operator-exclusive endpoint exists in current codebase)". Cite test_auth_roles.py as proof. This is a one-line doc edit, not a re-execution of Phase 2.

### Claude's Discretion
- ADR file naming detail: kebab-case slugs derived from IMPLICIT subject (e.g., `ADR-001-mongodb-datastore.md`). Planner finalizes exact slugs.
- Smart_Blending_AI_Formula doc location and audit depth: planner picks based on what the file actually contains today.
- Whether to update `pltu-tenayan-full-backup/readme.md` vs replace it: planner decides after reading current state.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project anchors
- `.planning/PROJECT.md` §"Tech stack — backend / frontend", §"Auth contract", §"Persistence contract", §"Pagination contract" — IMPLICIT-001..008 source rows that become ADRs.
- `.planning/REQUIREMENTS.md` §DOCS-01..05, §STAB-04 — phase requirements (DOCS-01..05) plus implicit-promotion stab item.
- `.planning/ROADMAP.md` §"Phase 3" — success criteria 1..5.

### Phase-2 deliverables (must reconcile against, must not duplicate)
- `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` — auth-contract decision record (D-AUTH-01, D-AUTH-02). Source for the API_REFERENCE auth section.
- `pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md` — credential rules. Doc audit must NOT reintroduce credentials.
- `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG_RESOLUTION.md` — Known Issues entry source.
- `.planning/phases/02-authentication-stabilization/VERIFICATION.md` §"phase_3_carryforwards" — 7 explicit carry-forward items.

### Existing docs to audit/regenerate
- `pltu-tenayan-full-backup/readme.md` — top-level entry, currently brief.
- `pltu-tenayan-full-backup/documentation.md` — operator-facing canonical doc; receives Known Issues section.
- `pltu-tenayan-full-backup/API_REFERENCE.md` — to be regenerated from /openapi.json + narrative.
- `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` — must identify active read target per duplicate-pair (Phase 5 owns the rename, Phase 3 just documents reality).
- `pltu-tenayan-full-backup/DEPLOYMENT_GUIDE.md` — VPS recovery pointer + actual deploy.
- `pltu-tenayan-full-backup/LOCAL_SETUP.md` — VPS recovery runbook destination.
- `pltu-tenayan-full-backup/Smart_Blending_AI_Formula.md` (if exists; planner verifies path) — formula reconciliation per CONS-blending-formula.

### Live system anchors (read-only)
- Live OpenAPI schema: `http://103.150.197.225:8013/openapi.json` (or local `http://localhost:8013/openapi.json` after `uvicorn ... --port 8013`).
- Live health: `http://103.150.197.225:8013/api/health`.
- MongoDB collections (read-only inspection): connect via `MONGO_URL` from `pltu-tenayan-full-backup/backend/.env`; never write.

### Code anchors for ADR proofs
- `pltu-tenayan-full-backup/backend/server.py` — Motor client init (IMPLICIT-001 proof), JWT/role decorators (IMPLICIT-004), `/api/*` router prefix (IMPLICIT-006).
- `pltu-tenayan-full-backup/backend/requirements.txt` — Python dep stack (IMPLICIT-002 proof).
- `pltu-tenayan-full-backup/frontend/package.json` — JS dep stack (IMPLICIT-003 proof).
- `pltu-tenayan-full-backup/backend/services/` — legacy-ai-sdk / Gemini wiring (IMPLICIT-005).
- Pagination shape sample sites: any list endpoint in server.py returning `{ items, total, page, page_size, total_pages }` (IMPLICIT-008).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase-2 conftest.py + test DB pattern**: `pltu-tenayan-full-backup/backend/tests/conftest.py` provides isolated test DB fixtures that Phase 3 endpoint spot-checks reuse without writing to prod.
- **Pre-commit credential scanner**: `pltu-tenayan-full-backup/scripts/check_credentials.sh` (Phase 2) automatically guards new docs against accidental credential leak. No additional doc-side hygiene scaffolding needed.
- **FastAPI built-in /openapi.json**: zero-effort canonical schema source — already running on live VPS and locally.
- **Existing audit/ directory**: `pltu-tenayan-full-backup/docs/audit/` already holds Phase-1/2 audit artifacts — pattern is established for placing Phase-3 doc-audit byproducts.

### Established Patterns
- **Sequential-on-main-tree execution**: All Phase-3 plans should follow Phase-2's no-worktree-isolation rule because target docs live in the untracked nested `pltu-tenayan-full-backup/` directory. Worktree isolation will not include those files.
- **Inner-vs-outer repo split**: Doc edits → inner repo (`git -C pltu-tenayan-full-backup ...`). ADR files in `.planning/decisions/` and SUMMARY.md → outer repo. ROADMAP/REQUIREMENTS edits → outer repo.
- **Atomic per-task commits**: One logical doc/ADR change per commit; Phase 2 normalized this.

### Integration Points
- ADRs at `.planning/decisions/` are referenced from PROJECT.md once Phase 3 lands. PROJECT.md "Key Decisions" table gets new column or replacement linking to ADR files.
- Generated API_REFERENCE.md script lives in `pltu-tenayan-full-backup/scripts/` (alongside check_credentials.sh).
- documentation.md Known Issues section becomes the single canonical surface — README.md and other docs link there rather than duplicating.

</code_context>

<specifics>
## Specific Ideas

- ADR-001..008 mapping (planner pin down):
  1. ADR-001: MongoDB as primary datastore (← IMPLICIT-001)
  2. ADR-002: FastAPI/Python backend stack (← IMPLICIT-002)
  3. ADR-003: React 19 + Tailwind + Shadcn frontend stack (← IMPLICIT-003)
  4. ADR-004: JWT + bcrypt + 3-role auth model (← IMPLICIT-004; cross-link AUTH_CONTRACT.md)
  5. ADR-005: Gemini via legacy-ai-sdk as AI provider (← IMPLICIT-005)
  6. ADR-006: `/api/*` route prefix + REACT_APP_BACKEND_URL frontend resolution (← IMPLICIT-006)
  7. ADR-007: Persistence contract — `_id` projection, application-level UUID, ISO 8601 datetimes (← IMPLICIT-007 + CONS-projection-id-contract)
  8. ADR-008: Pagination shape `{items,total,page,page_size,total_pages}` (← IMPLICIT-008 + CONS-pagination-shape)
- API_REFERENCE generated table columns: Method | Path | Auth (public/role-required) | Request schema | Response 2xx | Errors observed.
- Known Issues entries written as: `**[Status]** Title — short desc. (Cite: file path)`. Status badges: `[mitigated]`, `[pending-PhaseN]`, `[accepted]`.

</specifics>

<deferred>
## Deferred Ideas

- **pm2 / systemd auto-restart units for backend+frontend** — captured in D-12 as comment; actual unit files belong in a future Phase 3.1 INSERTED phase if user wants persistence beyond the runbook.
- **Multi-provider AI abstraction** — already deferred per PROJECT.md "Out-of-scope"; ADR-005 just locks current Gemini choice.
- **Doc translation (EN↔ID)** — out of scope; docs stay in current language mix (operator-facing Bahasa, technical English).
- **OpenAPI JSON snapshot versioning** — only current snapshot is documented; historical drift tracking is a Phase 4 (test) or Phase 8 (polish) topic.
- **Live MongoDB ER diagram** — not in DOCS-01..05 list; Phase 5 (collection naming debt) is a more natural home.

</deferred>

---

*Phase: 03-documentation-refresh-decision-lock-in*
*Context gathered: 2026-05-10*
