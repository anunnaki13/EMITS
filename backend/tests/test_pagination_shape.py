"""TEST-03: Pagination contract assertion across 7 list endpoints.

Source of truth: .planning/decisions/ADR-008-pagination-shape.md
Helper: tests/helpers/pagination.py::assert_pagination_shape

ADR-008 envelope (required on every list response):
  {"items": [...], "total": int, "page": int, "page_size": int, "total_pages": int}

total_pages formula:
  - if total == 0: total_pages == 0
  - else: total_pages == ceil(total / page_size) == (total + page_size - 1) // page_size

Each endpoint is admin/operator/viewer-readable (GET tier requires any-authenticated);
admin_headers fixture (from conftest.py) provides a valid bearer token sourced from
env-var credentials (TEST_ADMIN_EMAIL / TEST_ADMIN_PASSWORD).

All 7 endpoints confirmed to accept page/page_size Query params per server.py:
  - GET /api/vessels           (server.py line ~688)
  - GET /api/barges            (server.py line ~769)
  - GET /api/trucking          (server.py line ~849)
  - GET /api/biomassa          (server.py line ~929)
  - GET /api/po-batubara       (server.py line ~996)
  - GET /api/merit-order       (server.py line ~1204)
  - GET /api/coa-reconciliation (server.py line ~3853)
"""
import pytest
import requests

from tests.helpers.pagination import assert_pagination_shape


PAGINATED_LIST_ENDPOINTS = [
    "/api/vessels",
    "/api/barges",
    "/api/trucking",
    "/api/biomassa",
    "/api/po-batubara",
    "/api/merit-order",
    "/api/coa-reconciliation",
]


@pytest.mark.parametrize("path", PAGINATED_LIST_ENDPOINTS)
def test_pagination_envelope(path, base_url, admin_headers):
    """TEST-03: Each list endpoint returns the ADR-008 5-key envelope on page=1&page_size=10.

    Asserts:
    - HTTP 200 response
    - All 5 envelope keys present: items, total, page, page_size, total_pages
    - items is a list; total is non-negative int
    - page == 1, page_size == 10
    - total_pages formula matches ADR-008 (ceil(total/page_size) or 0 when total==0)
    """
    r = requests.get(
        f"{base_url}{path}?page=1&page_size=10",
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200, (
        f"{path} expected 200, got {r.status_code}: {r.text[:300]}"
    )
    body = r.json()
    assert_pagination_shape(body, expected_page=1, expected_page_size=10)


@pytest.mark.parametrize("path", PAGINATED_LIST_ENDPOINTS)
def test_empty_envelope_against_fresh_test_db(path, base_url, admin_headers):
    """ADR-008 empty-result behavior: total=0 → total_pages=0, items=[].

    The Phase-4 test DB starts empty (except merit_order which is seeded by conftest
    _seed_baseline_data). Other endpoints may have total=0. If total==0, the envelope
    MUST satisfy the empty-result contract: items==[] and total_pages==0.
    If data was seeded by a prior test in the same session, the total>0 branch is
    skipped (non-zero total is valid — this test is empty-branch focused).
    """
    r = requests.get(
        f"{base_url}{path}?page=1&page_size=10",
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"
    body = r.json()
    # Always validate the full envelope shape first
    assert_pagination_shape(body, expected_page=1, expected_page_size=10)
    # Additional empty-result invariants (only asserted when DB is actually empty)
    if body["total"] == 0:
        assert body["items"] == [], (
            f"{path}: total==0 but items is not empty: {body['items'][:3]}"
        )
        assert body["total_pages"] == 0, (
            f"{path}: total==0 but total_pages={body['total_pages']} (expected 0)"
        )


def test_custom_page_size_round_trips(base_url, admin_headers):
    """ADR-008: page_size query parameter round-trips into the response envelope.

    Sends page_size=25 to /api/vessels and verifies the response contains
    page_size==25. This confirms the server does not silently override the
    client-requested page_size with a fixed default.
    """
    r = requests.get(
        f"{base_url}/api/vessels?page=1&page_size=25",
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["page_size"] == 25, (
        f"page_size expected 25, got {body['page_size']}"
    )
    assert_pagination_shape(body, expected_page=1, expected_page_size=25)


def test_invalid_page_rejected(base_url, admin_headers):
    """FastAPI validation: page=0 violates Query(1, ge=1) — expect HTTP 422.

    ADR-008 cap: page must be >= 1. FastAPI enforces this via the ge=1 constraint
    on the Query parameter and returns 422 Unprocessable Entity before the handler
    logic runs. This test pins the validator as wired correctly.
    """
    r = requests.get(
        f"{base_url}/api/vessels?page=0",
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 422, (
        f"expected 422 for page=0, got {r.status_code}: {r.text[:200]}"
    )
