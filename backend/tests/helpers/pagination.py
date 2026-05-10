"""Pagination assertion helper for Phase 4 tests.

Verifies the ADR-008 pagination envelope:
  {"items": [...], "total": int, "page": int, "page_size": int, "total_pages": int}

total_pages formula:
  - if total == 0: total_pages == 0
  - else: total_pages == ceil(total / page_size) == (total + page_size - 1) // page_size
"""


def assert_pagination_shape(body: dict, expected_page: int = 1, expected_page_size: int = None):
    """Assert that `body` satisfies ADR-008 pagination envelope contract.

    Raises AssertionError with a descriptive message on failure.
    """
    for key in ("items", "total", "page", "page_size", "total_pages"):
        assert key in body, f"Pagination envelope missing key '{key}': {body}"

    assert isinstance(body["items"], list), (
        f"'items' must be a list, got {type(body['items'])}"
    )
    assert isinstance(body["total"], int), (
        f"'total' must be int, got {type(body['total'])}"
    )
    assert body["total"] >= 0, f"'total' must be non-negative, got {body['total']}"
    assert body["page"] == expected_page, (
        f"'page' expected {expected_page}, got {body['page']}"
    )
    if expected_page_size is not None:
        assert body["page_size"] == expected_page_size, (
            f"'page_size' expected {expected_page_size}, got {body['page_size']}"
        )
    # total_pages formula check
    if body["total"] == 0:
        assert body["total_pages"] == 0, (
            f"total_pages must be 0 when total==0, got {body['total_pages']}"
        )
    else:
        expected_total_pages = (body["total"] + body["page_size"] - 1) // body["page_size"]
        assert body["total_pages"] == expected_total_pages, (
            f"total_pages formula mismatch: total={body['total']}, "
            f"page_size={body['page_size']}, expected {expected_total_pages}, "
            f"got {body['total_pages']}"
        )
