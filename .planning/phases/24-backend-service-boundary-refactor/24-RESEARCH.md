# Phase 24 Research - Backend Service Boundary Refactor

Date: 2026-05-14
Status: complete

## Codebase Findings

### Existing Services

Existing backend service layer:

- `backend/services/coa_reconciliation.py`
- `backend/services/runtime_status.py`
- `backend/services/backup_service.py`
- `backend/services/excel_parser.py`

These services demonstrate the local pattern: business logic and data shaping can live outside routers while routers own auth, request validation, and HTTP exceptions.

### Current Router-Coupled Logic

`backend/routers/dashboard.py` currently contains:

- period/mode/supplier helpers
- stock risk logic
- operational dashboard aggregation
- dashboard stats aggregation
- advanced dashboard chart aggregation

`backend/routers/reports.py` currently contains:

- period/date/supplier helpers
- aggregate sum/avg helpers
- stock/report/supplier scorecard calculations
- management report builder

`backend/routers/ai_intelligence.py` currently contains:

- duplicate period and sum helpers
- contextual AI data slicing
- operational advisor recommendations
- management memo generation
- `/api/ai/advisor/operational` endpoint logic

### Duplication To Consolidate

Repeated concepts:

- period bounds for `YYYY` and `YYYY-MM`
- date range match construction
- supplier regex match construction
- mode normalization and mode regexes
- sum/average aggregation helpers
- safe float conversion
- aging-days calculation
- source slice dictionaries

### Recommended Extraction

1. `services/query_filters.py`
   - shared low-level helpers for date/supplier/mode/query aggregation
   - pure functions plus small Mongo aggregate helpers

2. `services/management_reports.py`
   - move report helper functions and `build_management_report`
   - leave `routers/reports.py` as a thin endpoint wrapper

3. `services/dashboard_metrics.py`
   - move operational dashboard, stats, and advanced builders
   - leave response model construction compatible with current route behavior

4. `services/operational_advisor.py`
   - move advisor recommendation and memo generation
   - call management report service internally
   - keep deterministic fallback behavior and no live LLM dependency

## Test Strategy

Add direct service tests:

- `backend/tests/test_service_boundaries.py`

Focused assertions:

- service functions return the same key shapes expected by routes
- routers import and call services rather than owning large calculation blocks
- direct service calls run against the isolated test DB
- no committed secrets or live LLM calls are needed

Reuse existing route tests for response compatibility:

- dashboard operational tests
- dashboard advanced tests
- management reports tests
- AI endpoint tests

## Risks

- Mechanical copy can accidentally change response keys.
  - Mitigation: keep function bodies as close as possible during extraction and run existing route tests.

- Circular imports between routers and services.
  - Mitigation: services must import only `utils.database`, low-level helpers, and other services; routers import services.

- Over-consolidating helpers can create broad blast radius.
  - Mitigation: introduce shared helpers only for duplicated logic used by touched services.

