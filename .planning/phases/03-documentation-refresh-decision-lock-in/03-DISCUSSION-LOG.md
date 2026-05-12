# Phase 03: Documentation Refresh & Decision Lock-In - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-10
**Phase:** 03-documentation-refresh-decision-lock-in
**Areas discussed:** ADR format, API_REFERENCE source-of-truth
**Areas deferred to Claude's discretion:** Spot-check method, Known Issues placement, VPS recovery runbook destination

---

## ADR Format

| Option | Description | Selected |
|--------|-------------|----------|
| MADR penuh per file | 8 files (ADR-001..008), each with Status / Context / Decision / Consequences / Alternatives Considered / References (~40-80 lines) | ✓ |
| Y-statement single-line | "In context of X, facing Y, we chose Z to achieve W, accepting V." Padat tapi minim ruang untuk alternatives/consequences. | |
| Nygard ringan | Title / Status / Context / Decision / Consequences. Tanpa Alternatives. ~20-40 lines/file. | |

**User's choice:** MADR penuh per file (Recommended option, accepted with preview)
**Notes:** User reviewed the ADR-001 preview (MongoDB datastore example) and accepted. References section will cite (a) source IMPLICIT line in PROJECT.md, (b) ≥1 code anchor (file:line), (c) related CONS-* constraint. Captured as D-01..D-03 in CONTEXT.md.

---

## API_REFERENCE Source-of-Truth

| Option | Description | Selected |
|--------|-------------|----------|
| Generate from /openapi.json + komentar manusia | OpenAPI as canonical machine-truth, layered narrative for auth/pagination/error-codes | ✓ |
| Hand-curate, reconcile vs live | Pertahankan API_REFERENCE.md, audit endpoint manual + curl spot-check | |
| Static review only | Audit hanya vs source code, tanpa live calls | |

**User's choice:** Generate from /openapi.json + komentar manusia (Recommended option, accepted with preview)
**Notes:** Schema fetched read-only from production VPS at `http://103.150.197.225:8013/openapi.json` or local `localhost:8013` mirror. Hand-curated sections layered on top: Auth Contract (sourced from Phase-2 AUTH_CONTRACT.md), Pagination Contract (CONS-pagination-shape), Error Code Map (CONS-auth-header). Regeneration script lives at `pltu-tenayan-full-backup/scripts/regenerate_api_reference.py` for future drift detection. Captured as D-04..D-06 in CONTEXT.md.

---

## Claude's Discretion

User skipped these gray areas; sensible defaults applied and recorded as D-07..D-12 in CONTEXT.md:

- **Spot-check method (D-07, D-08):** Reuse Phase-2 conftest pattern (local uvicorn + isolated test DB). NO live-DB writes. Live VPS only touched read-only for `/openapi.json` and `/api/health`. AI endpoints needing LLM key marked `verified: schema-only` and deferred to Phase 6.
- **Known Issues placement (D-09, D-10):** New H2 in `pltu-tenayan-full-backup/documentation.md`. README gets a one-line pointer. Initial entries: login-mitigated, Smart Blending budget, Excel parser pending, collection naming debt, audit-probe synthetic-users record.
- **VPS recovery runbook (D-11, D-12):** Lives in `LOCAL_SETUP.md` under new H2 "VPS Service Recovery (post-restart)". DEPLOYMENT_GUIDE.md gets one-line pointer. Optional pm2/systemd units flagged for potential Phase 3.1 INSERTED.
- **ROADMAP wording fix (D-13):** Phase 3 must amend ROADMAP success criterion 3 wording (operator-only → admin+operator) per Phase-2 verifier soft-spot SS-03.

## Deferred Ideas

- pm2 / systemd auto-restart units → potential Phase 3.1 INSERTED if user wants persistence beyond the runbook
- Multi-provider AI abstraction → already deferred per PROJECT.md out-of-scope; ADR-005 just locks current Gemini choice
- Doc translation (EN↔ID) → out of scope; docs stay in current language mix
- OpenAPI JSON snapshot versioning → Phase 4 (test) or Phase 8 (polish) topic
- Live MongoDB ER diagram → Phase 5 (collection naming debt) more natural home
