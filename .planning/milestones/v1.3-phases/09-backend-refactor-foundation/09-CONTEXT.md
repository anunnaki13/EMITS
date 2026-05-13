---
phase: 09-backend-refactor-foundation
status: in_progress
created_at: "2026-05-11T23:20:00+07:00"
milestone: v1.1
---

# Phase 09 Context — Backend Refactor Foundation

## User Direction

The user approved continuing backend refactor work and wants the next upgrade set implemented:

- Dashboard control-room v2.
- Alerts and notifications.
- Formal dispute / umpire workflow.
- Import Excel preview and validation.
- Richer audit trail.
- Management reports.
- Contextual AI assistant.

## Refactor Rationale

The feature set above crosses dashboard, reports, import, audit, AI, and operational alerting. Keeping all of that inside `server.py` would increase risk and make future changes harder to verify. Phase 09 therefore continues the backend modularization before larger feature work.

## Current Backend Shape

- `server.py` still owns many route families:
  - rekap CRUD/upload
  - PO Batubara
  - Merit Order
  - suppliers
  - dashboard
  - AI intelligence / conversations / smart blending
  - health
- Existing extracted routers:
  - `routers/auth.py`
  - `routers/coa.py`
  - `routers/smart_stock.py`
  - `routers/admin.py` (created by 09-01)

## Phase Goal

Move coherent backend domains out of `server.py` without changing `/api/*` contracts, so v1.1 features can be added behind smaller routers/services.

