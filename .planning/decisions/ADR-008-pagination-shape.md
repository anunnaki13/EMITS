# ADR-008: Paginated List Response Envelope `{items, total, page, page_size, total_pages}`

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-008.

## Context

Every list endpoint in EMITS — vessels, barges, trucking, biomassa, PO Batubara, merit-order, COA reconciliation, smart-stock, sumber-pemakaian, AI session list, AI history — returns a **paginated** response. The shape is locked SPEC (CONS-pagination-shape) and is currently in effect across every list route in `backend/server.py`. The frontend's list views (operator data-entry tabs, COA dispute monitor, AI session selector) ALL read `response.data.items` and assume the envelope shape; changing it would break every list page in the UI.

`REQ-pagination-server-side` is validated/shipped. The default page size is 50, the operational cap is 500 for most modules, and smart-stock's cap is 50000 (because the smart-stock dashboard pulls a wider window per CONS-smart-stock-endpoint). Frontend pagination controls are page-number-based, not cursor-based.

This ADR locks the shape so future plans cite the envelope directly instead of re-reading PROJECT.md or the API_REFERENCE every time.

## Decision

Every paginated list endpoint in EMITS returns the JSON envelope:

```json
{
  "items": [...],
  "total": <int>,
  "page": <int>,
  "page_size": <int>,
  "total_pages": <int>
}
```

Locked clauses:

- **Field names:** literal `items`, `total`, `page`, `page_size`, `total_pages`. No aliasing (e.g., never `data`, `count`, `pageSize`, `totalPages`).
- **Default page:** `page=1` (1-indexed, not 0-indexed).
- **Default page_size:** `page_size=50`.
- **Operational caps:**
  - Most list endpoints (vessels, barges, trucking, biomassa, PO Batubara, merit-order, COA reconciliation): `page_size <= 500`.
  - Smart-stock list: `page_size <= 50000` (CONS-smart-stock-endpoint — wider window justified by dashboard aggregations).
- **`total_pages` formula:** `ceil(total / page_size)` — implemented as `(total + page_size - 1) // page_size` in Python.
- **Frontend rule:** the React frontend MUST read `response.data.items` and never assume the response is a bare array. Every existing list view follows this; new list views inherit the rule.
- **Empty-result behavior:** when there are zero rows, the envelope is `{"items": [], "total": 0, "page": 1, "page_size": 50, "total_pages": 0}` — `items` is an empty array, NOT `null`.

## Consequences

**Positive:**

- Every list view in the frontend uses the same data-extraction code (`response.data.items` + `response.data.total_pages` for the paginator); zero per-endpoint customization.
- `total_pages` is computed server-side, so frontend pagination controls don't reimplement the ceiling math.
- Backend tests can assert the envelope shape uniformly (`assert "items" in body and "total" in body`).
- API_REFERENCE generation (Phase 3, plan 03) documents one shared shape under "Pagination Contract" (D-05) and references it from each list endpoint table.
- Operationally consistent caps (500 for most, 50000 for smart-stock) are documented and enforceable via `Query(50, ge=1, le=50000)` style guards on the `page_size` query parameter.

**Negative / accepted tradeoffs:**

- Offset-based pagination (`skip = (page - 1) * page_size`) means deep pages are O(skip) — at smart-stock's cap of 50000 this is meaningful, but the smart-stock view typically paginates via `start_date`/`end_date` rather than deep page indexes, so the worst-case scan is bounded by date range.
- No cursor-based pagination — moving to cursor (e.g., `next_cursor`) would break every list view and is deferred until row counts make offset-pagination painful (largest collection today is 721 rows; not painful).
- `total` requires a second `count_documents(query)` call alongside the `find(...)` — adds one round-trip per list request. Acceptable at current load; could be skipped under an opt-in `Skip-Count: 1` header if scale ever demands.
- Frontends that try to render the bare `items` array without checking the envelope will silently break; mitigated by the locked rule and by reviewer vigilance.

## Alternatives Considered

- **Cursor-based pagination with `next_cursor` token** — rejected. UI uses page-number paginators; offset-based is fine at current row counts (largest collection 721 rows). Cursor pagination is harder for "jump to page 5" UI.
- **Bare array + `X-Total-Count` header** — rejected. Frontend already reads from `response.data.items` everywhere; changing the contract would break every list view in the React UI for no benefit.
- **GraphQL connection pattern (`{ edges, pageInfo }`)** — rejected. REST contract is locked; GraphQL is not on the v1 or v2 roadmap; introducing GraphQL just for pagination shape is massive scope creep.
- **Different per-resource shapes (e.g., COA returning `{rows, count}` while vessels returns `{items, total}`)** — rejected. Heterogeneity for no operational benefit; uniformity is the dominant design constraint.
- **`page_size = 0` meaning "all"** — rejected. Footgun for large collections; dedicated wider-cap endpoints (smart-stock at 50000) handle the legitimate "all" cases without an unbounded escape hatch.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-008 row (line 93: "Pagination contract (LOCKED, SPEC): Paginated list endpoints MUST return `{ items, total, page, page_size, total_pages }`; default page=1, page_size=50; cap 500 (operational) / 50000 (smart-stock). Frontend MUST read `response.data.items`. Per CONS-pagination-shape + IMPLICIT-008.").
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/backend/server.py:685-722` — canonical `GET /api/vessels` list endpoint; shows the page/page_size Query params, count_documents + projection-find pattern, and the envelope return shape. Verbatim return statement (lines 716-722):

    ```python
    return {
        "items": vessels,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
    ```

  - `pltu-tenayan-full-backup/backend/server.py:687-688` — `page: int = Query(1, ge=1)` + `page_size: int = Query(50, ge=1, le=50000)` (the locked default + cap pattern).
  - `pltu-tenayan-full-backup/backend/server.py:712-714` — `skip = (page - 1) * page_size; total = await db.vessels.count_documents(query); vessels = await db.vessels.find(query, {"_id": 0}).sort(...).skip(skip).limit(page_size).to_list(page_size)` (the offset-pagination + projection idiom; see also ADR-007).
- **Related constraints:** `.planning/intel/constraints.md` → CONS-pagination-shape (the locked SPEC contract this ADR formalizes); CONS-smart-stock-endpoint (wider 50000 cap rationale); CONS-coa-reconciliation-endpoint (50000 cap also applied for COA list per the constraint text).
- **Sibling docs:** `pltu-tenayan-full-backup/API_REFERENCE.md` "Pagination Contract" section (D-05; consumes this ADR as the canonical shape definition).
