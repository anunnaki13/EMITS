---
phase: 07
slug: upgrade-backlog-foundation
status: archived
nyquist_status: legacy_exception
nyquist_exception: "Archived before v1.4 metadata standard; validation evidence preserved in this file and phase verification."
metadata_reviewed: "2026-05-14"
---

# Phase 07: Upgrade Backlog Foundation - Validation

**Created:** 2026-05-11

## Required Gates

| Gate | Command | Purpose |
|------|---------|---------|
| Auth contract | `AI_FAKE=1 ./.venv/bin/pytest tests/test_auth_session.py tests/test_auth_roles.py -q` | Auth extraction preserves login/RBAC/error codes |
| COA contract | `AI_FAKE=1 ./.venv/bin/pytest tests/test_coa_reconciliation.py -q` | COA router extraction preserves business endpoints |
| Dashboard guard | `AI_FAKE=1 ./.venv/bin/pytest tests/test_dashboard_advanced.py -q` | Dashboard/laporan extraction preserves current backend shape |
| Canonical collections | `AI_FAKE=1 ./.venv/bin/pytest tests/test_migrate_collection_names.py -q` | No legacy collection reads reintroduced |
| Rekap filters | `AI_FAKE=1 ./.venv/bin/pytest tests/test_rekap_filters.py tests/test_pagination_shape.py -q` | Date/supplier filters preserve pagination envelope |
| AI guards | `AI_FAKE=1 ./.venv/bin/pytest tests/test_smart_blending_data.py tests/test_ai_chat_endpoints.py -q` | Phase 6 AI work survives refactor |
| Frontend build | `yarn build` from `frontend/` | Filter UI compiles |

## Manual Review Gates

- Confirm `server.py` is meaningfully smaller after plans 01-03.
- Confirm stale `routers/ai.py` is not mounted while it still contains `emergentintegrations` or `ai_conversations`.
- Confirm UI filter controls do not overlap on mobile width.
- Confirm dashboard redesign is not accidentally implemented in Phase 7; keep it for Phase 8/dedicated dashboard phase.
