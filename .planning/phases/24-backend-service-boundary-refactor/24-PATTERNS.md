# Phase 24 Patterns - Backend Service Boundary Refactor

Date: 2026-05-14
Status: complete

## Service Pattern

Use the existing service style from:

- `backend/services/coa_reconciliation.py`
- `backend/services/runtime_status.py`
- `backend/services/backup_service.py`

Pattern:

- service functions accept explicit primitive inputs and optional `user` dict only when needed for existing return metadata
- service functions return plain dictionaries/lists/models
- routers handle FastAPI dependencies, `Query(...)`, auth, and response wrapping

## Router Pattern

Target router shape:

```python
@router.get("/management")
async def get_management_report(..., user: dict = Depends(get_current_user)):
    return await build_management_report(period, supplier, date_from, date_to, user)
```

Routers should not own aggregation pipelines unless they are endpoint-specific and trivial.

## Helper Pattern

Centralize repeated helpers in `services/query_filters.py`:

- `period_bounds`
- `period_match`
- `date_match`
- `supplier_match`
- `mode_match`
- `merge_match`
- `and_match`
- `sum_collection`
- `avg_collection`
- `safe_float`
- `aging_days`
- `source_slice`

Use escaped supplier regexes. Do not interpolate raw query strings into regexes.

## Test Pattern

Follow existing integration style:

- use `base_url` and `admin_headers` for route compatibility tests
- use `MONGO_TEST_DB_NAME` and `pymongo` for direct seeding
- use unique `_marker` values and cleanup in `finally`
- no committed credentials

