# Phase 24 Context - Backend Service Boundary Refactor

Date: 2026-05-14
Status: planning

## Phase Goal

Move shared dashboard, report, and AI advisor calculations into service-layer functions with explicit inputs and outputs, while keeping public API response contracts backward compatible.

## Requirements Covered

- `REF3-01`: Shared dashboard, report, and AI advisor calculations move into service-layer functions with explicit inputs and outputs.
- `REF3-02`: Duplicate date, number, period, supplier, and mode normalization helpers are consolidated and tested.
- `REF3-03`: Router handlers stay thin: auth/role gate, request validation, service call, and response mapping.
- `REF3-04`: Service-layer functions have focused unit tests that do not require committed secrets or live LLM calls.
- `REF3-05`: Public API response contracts remain backward compatible unless a requirement explicitly documents a change.
- `REF3-06`: Common backend errors use the existing Indonesian error taxonomy consistently across touched routes.

## Current Problem

The backend already has service modules for COA reconciliation, backup, runtime health, and Excel parsing. However, large calculation blocks still live in routers:

- `backend/routers/dashboard.py`
- `backend/routers/reports.py`
- `backend/routers/ai_intelligence.py`

This makes later data-quality, trend, and AI-advisor phases harder because dashboard/report/advisor calculations are duplicated or router-coupled.

## Boundary

In scope:

- Extract reusable filter/math helpers into service-layer code.
- Move management report calculations out of `routers/reports.py`.
- Move operational dashboard calculations out of `routers/dashboard.py`.
- Move operational advisor recommendation/memo generation out of `routers/ai_intelligence.py`.
- Add direct service tests and preserve route-level regression tests.

Out of scope:

- Changing API response shapes.
- Adding new analytics, trend, forecast, or AI behaviors.
- Reworking auth, Mongo schema, imports, or frontend behavior.
- Rewriting every legacy endpoint in `server.py`.

## Service Targets

Expected service modules:

- `backend/services/query_filters.py`
- `backend/services/management_reports.py`
- `backend/services/dashboard_metrics.py`
- `backend/services/operational_advisor.py`

Routers should keep auth and request concerns, then call services:

- `/api/reports/management` -> `build_management_report(...)`
- `/api/dashboard/operational` -> `build_dashboard_operational(...)`
- `/api/dashboard/stats` -> `build_dashboard_stats(...)`
- `/api/dashboard/advanced` -> `build_dashboard_advanced(...)`
- `/api/ai/advisor/operational` -> `build_operational_advisor(...)`

## Compatibility Contract

The following tests remain route-contract anchors:

- `backend/tests/test_dashboard_operational.py`
- `backend/tests/test_dashboard_advanced.py`
- `backend/tests/test_management_reports.py`
- `backend/tests/test_ai_endpoints.py`

Phase 24 may add tests, but existing route tests must continue to pass.

