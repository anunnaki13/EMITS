---
phase: 24
slug: backend-service-boundary-refactor
status: archived
nyquist_status: legacy_exception
nyquist_exception: "Archived before v1.4 metadata standard; validation evidence preserved in this file and phase verification."
metadata_reviewed: "2026-05-14"
---

# Phase 24 Validation Plan - Backend Service Boundary Refactor

Date: 2026-05-14
Status: planned

## Static Checks

```bash
python3 -m py_compile backend/services/query_filters.py backend/services/management_reports.py backend/services/dashboard_metrics.py backend/services/operational_advisor.py backend/routers/dashboard.py backend/routers/reports.py backend/routers/ai_intelligence.py
```

## Focused Tests

```bash
ops/scripts/pytest_with_local_credentials.sh tests/test_service_boundaries.py tests/test_dashboard_operational.py tests/test_dashboard_advanced.py tests/test_management_reports.py tests/test_ai_endpoints.py -q
```

## Acceptance

- Dashboard/report/advisor route tests pass with unchanged response shapes.
- Direct service tests pass.
- Routers are visibly thinner and import service builders.
- No live LLM calls are required.
- No committed secrets are added.
