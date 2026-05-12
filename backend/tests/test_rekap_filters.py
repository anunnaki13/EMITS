import uuid

import pytest
import requests

from tests.helpers.pagination import assert_pagination_shape


REKAP_CASES = [
    {
        "path": "/api/vessels",
        "factory": "tests.factories.vessel.make_vessel",
        "date_field": "time_arrival",
        "search_field": "shipment_code",
    },
    {
        "path": "/api/barges",
        "factory": "tests.factories.barge.make_barge",
        "date_field": "ta",
        "search_field": "shipment_code",
    },
    {
        "path": "/api/trucking",
        "factory": "tests.factories.trucking.make_trucking",
        "date_field": "ta",
        "search_field": "shipment_code",
    },
    {
        "path": "/api/biomassa",
        "factory": "tests.factories.biomassa.make_biomassa",
        "date_field": "periode",
        "search_field": "shipment_code",
    },
]


def _load_factory(path: str):
    module_name, func_name = path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[func_name])
    return getattr(module, func_name)


@pytest.mark.parametrize("case", REKAP_CASES)
def test_rekap_date_range_and_supplier_filters_preserve_pagination(case, base_url, admin_headers):
    marker = f"PT FILTER {uuid.uuid4().hex[:10].upper()}"
    make_doc = _load_factory(case["factory"])

    in_range = make_doc(
        suppliers=marker,
        **{
            case["date_field"]: "2026-03-15 08:00",
            case["search_field"]: f"FILTER-IN-{uuid.uuid4().hex[:8]}",
        },
    )
    make_doc(
        suppliers=marker,
        **{
            case["date_field"]: "2026-02-15 08:00",
            case["search_field"]: f"FILTER-OUT-{uuid.uuid4().hex[:8]}",
        },
    )
    make_doc(
        suppliers=f"PT OTHER {uuid.uuid4().hex[:10].upper()}",
        **{
            case["date_field"]: "2026-03-18 08:00",
            case["search_field"]: f"FILTER-OTHER-{uuid.uuid4().hex[:8]}",
        },
    )

    r = requests.get(
        f"{base_url}{case['path']}",
        headers=admin_headers,
        params={
            "page": 1,
            "page_size": 10,
            "supplier": marker,
            "date_from": "2026-03-01",
            "date_to": "2026-03-31",
        },
        timeout=10,
    )

    assert r.status_code == 200, f"{case['path']}: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert_pagination_shape(body, expected_page=1, expected_page_size=10)
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [in_range["id"]]


def test_rekap_combines_search_supplier_and_date_filters(base_url, admin_headers):
    from tests.factories.vessel import make_vessel

    marker = f"PT COMBINED {uuid.uuid4().hex[:10].upper()}"
    search_token = f"SHP-COMBO-{uuid.uuid4().hex[:8].upper()}"
    expected = make_vessel(
        suppliers=marker,
        shipment_code=search_token,
        time_arrival="2026-04-12 08:00",
    )
    make_vessel(
        suppliers=marker,
        shipment_code=f"{search_token}-OLD",
        time_arrival="2026-01-12 08:00",
    )
    make_vessel(
        suppliers=f"PT OTHER {uuid.uuid4().hex[:10].upper()}",
        shipment_code=search_token,
        time_arrival="2026-04-13 08:00",
    )

    r = requests.get(
        f"{base_url}/api/vessels",
        headers=admin_headers,
        params={
            "page": 1,
            "page_size": 5,
            "search": search_token,
            "supplier": marker,
            "date_from": "2026-04-01",
            "date_to": "2026-04-30",
        },
        timeout=10,
    )

    assert r.status_code == 200, f"/api/vessels: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert_pagination_shape(body, expected_page=1, expected_page_size=5)
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [expected["id"]]
