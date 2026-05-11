"""TEST-04: Excel upload parser-path coverage with round-trip assertions.

Source of truth:
- D-08: 4 synthetic fixtures at tests/fixtures/excel/
- D-09: assert 200/201 + deterministic round-trip; no production totals
- ROADMAP Phase-2 SC-3: admin/operator allowed, viewer denied (role gate)
- server.py: upload endpoints return {"message": ..., "count": ...} on success

OPS-03 COA regression tests (06-03):
- 3 sanitized production-proxy fixtures at tests/fixtures/excel/regression/
- Direct unit tests of parse_coa_excel() — no live server needed
- Deterministic anchor: Shipment 555, DS_MT 5626.021 (present in all 3 files)
"""
import os
from pathlib import Path
import pytest
import requests


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "excel"

# (mode, upload_path, list_path)
UPLOAD_CASES = [
    ("vessel",   "/api/upload/vessel",   "/api/vessels"),
    ("barge",    "/api/upload/barge",    "/api/barges"),
    ("trucking", "/api/upload/trucking", "/api/trucking"),
    ("biomassa", "/api/upload/biomassa", "/api/biomassa"),
]

# Deterministic GCV ARB values for the first row of each fixture (SHP-TEST-001).
# vessel/barge/trucking: 4250.0 (coal); biomassa: 3050.0 (biomass — lower calorific value).
# Rule 1 fix: the plan hypothesised 4250.0 for all modes, but the biomassa fixture was
# generated with biomass-realistic values. Use actual fixture values for deterministic assertions.
EXPECTED_GCV_ARB = {
    "vessel":   4250.0,
    "barge":    4250.0,
    "trucking": 4250.0,
    "biomassa": 3050.0,
}


@pytest.mark.parametrize("mode, upload_path, list_path", UPLOAD_CASES)
def test_upload_then_round_trip(mode, upload_path, list_path, base_url, admin_headers):
    """D-09: upload xlsx fixture → 200 + round-trip → GET list search=SHP-TEST-001 → row appears."""
    fixture = FIXTURE_DIR / f"{mode}_minimal.xlsx"
    assert fixture.exists(), f"Wave-0 missing fixture: {fixture}"

    with open(fixture, "rb") as fh:
        r = requests.post(
            f"{base_url}{upload_path}",
            files={
                "file": (
                    fixture.name,
                    fh,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers=admin_headers,  # no Content-Type override; requests sets multipart boundary
            timeout=30,
        )
    assert r.status_code in (200, 201), (
        f"{upload_path} returned {r.status_code}: {r.text[:400]}"
    )

    # The server returns {"message": ..., "count": ...} — verify count is non-zero
    body = r.json()
    assert body.get("count", 0) > 0, (
        f"{upload_path}: upload succeeded but count=0, response={body}"
    )

    # Round-trip: the SHP-TEST-001 row from the fixture must now be in MongoDB
    r2 = requests.get(
        f"{base_url}{list_path}?search=SHP-TEST-001&page=1&page_size=10",
        headers=admin_headers,
        timeout=10,
    )
    assert r2.status_code == 200, f"{list_path}: {r2.status_code} {r2.text[:200]}"
    body2 = r2.json()
    assert body2["total"] >= 1, (
        f"{mode} upload did not round-trip: total={body2['total']}, "
        f"items={body2.get('items', [])[:2]}"
    )
    hit = body2["items"][0]
    assert hit["shipment_code"] == "SHP-TEST-001", (
        f"{mode} first hit shipment_code={hit.get('shipment_code')!r}, "
        f"expected 'SHP-TEST-001'"
    )
    # T-round-trip-skew-01 mitigation: use tolerance for float comparison.
    # Expected GCV varies by mode — biomassa uses biomass-realistic values (3050.0),
    # vessel/barge/trucking use coal values (4250.0). See EXPECTED_GCV_ARB above.
    gcv = hit.get("gcv_arb")
    if gcv is not None:
        expected_gcv = EXPECTED_GCV_ARB[mode]
        assert abs(gcv - expected_gcv) < 0.01, (
            f"{mode} gcv_arb={gcv} differs from expected {expected_gcv} (tolerance 0.01)"
        )


def test_upload_vessel_role_denied_for_viewer(base_url, viewer_credentials):
    """ROADMAP Phase-2 SC-3 / D-13: viewer role cannot upload — expect 403.

    viewer_credentials fixture skips this test if TEST_VIEWER_EMAIL/PASSWORD
    are not set in the test environment (standard _require_env skip behavior).
    """
    r_login = requests.post(
        f"{base_url}/api/auth/login",
        json=viewer_credentials,
        timeout=10,
    )
    assert r_login.status_code == 200, (
        f"viewer login failed: {r_login.status_code} {r_login.text[:200]}"
    )
    viewer_token = r_login.json()["access_token"]

    fixture = FIXTURE_DIR / "vessel_minimal.xlsx"
    with open(fixture, "rb") as fh:
        r2 = requests.post(
            f"{base_url}/api/upload/vessel",
            files={
                "file": (
                    fixture.name,
                    fh,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
            timeout=30,
        )
    assert r2.status_code == 403, (
        f"expected 403 for viewer upload, got {r2.status_code}: {r2.text[:200]}"
    )


# =============================================================================
# OPS-03: COA Parser Regression Tests (06-03)
# =============================================================================
# Direct unit tests of parse_coa_excel() against sanitized production-proxy
# fixtures.  No live server required — import the function directly.
#
# Deterministic anchor per RESEARCH Focus 8:
#   Shipment 555, DS_MT = 5626.021 (identical across all 3 files)
#   Supplier sanitized to "PT DEMO SUPPLIER 1" (no real PII)
#
# Lab_Internal first-50-row quality values are all NaN in the real production
# file (quality data only starts at Shipment ~725).  Numeric assertions for
# internal mode therefore focus on identity/tonnage fields, not quality columns.
# =============================================================================

COA_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "excel" / "regression"

# Anchor values constant across all 3 modes
ANCHOR_SHIPMENT = "555"
ANCHOR_DS_MT = 5626.021
ANCHOR_SUPPLIER_PREFIX = "PT DEMO SUPPLIER"


def _load_fixture_bytes(fname: str) -> bytes:
    path = COA_FIXTURE_DIR / fname
    assert path.exists(), f"Regression fixture missing: {path}"
    return path.read_bytes()


def test_coa_regression_loading():
    """OPS-03 / 06-03-01: loading_sample.xlsx round-trips through parse_coa_excel.

    Assertions:
    - Returns <= 50 records (fixture is capped at 50 data rows)
    - Anchor row Shipment 555 is present
    - DS_MT = 5626.021 for anchor row (identity field, always populated)
    - Supplier is sanitized (starts with 'PT DEMO SUPPLIER', no real PII)
    - loading-specific fields: surveyor and no_coa keys exist in record
    - Row 556 (index 1) has gcv_arb=4211.0 (Loading has quality from row 2 onward
      except the first row gap; row 3 in xlsx = shipment 556)
    """
    from services.coa_reconciliation import parse_coa_excel

    data = parse_coa_excel(_load_fixture_bytes("loading_sample.xlsx"), "loading")

    assert len(data) <= 50, f"Expected <= 50 records, got {len(data)}"

    anchor_rows = [r for r in data if str(r.get("shipment", "")) == ANCHOR_SHIPMENT]
    assert anchor_rows, f"Anchor Shipment {ANCHOR_SHIPMENT} not found in loading parse output"

    anchor = anchor_rows[0]
    assert abs(anchor["ds_mt"] - ANCHOR_DS_MT) < 0.001, (
        f"loading anchor ds_mt={anchor['ds_mt']!r}, expected {ANCHOR_DS_MT}"
    )
    assert anchor["suppliers"].startswith(ANCHOR_SUPPLIER_PREFIX), (
        f"loading supplier not sanitized: {anchor['suppliers']!r}"
    )
    # loading-specific keys must exist in record schema
    assert "surveyor" in anchor, "loading record missing 'surveyor' key"
    assert "no_coa" in anchor, "loading record missing 'no_coa' key"

    # Shipment 556 (row 3 in fixture) has real loading quality data
    row556 = [r for r in data if str(r.get("shipment", "")) == "556"]
    assert row556, "Shipment 556 not found — fixture may be malformed"
    assert abs((row556[0].get("gcv_arb") or 0) - 4211.0) < 0.5, (
        f"loading shp556 gcv_arb={row556[0].get('gcv_arb')!r}, expected ~4211.0"
    )


def test_coa_regression_unloading():
    """OPS-03 / 06-03-02: unloading_sample.xlsx round-trips through parse_coa_excel.

    Assertions:
    - Returns <= 50 records
    - Anchor row Shipment 555 is present with ds_mt=5626.021
    - Surveyor for anchor row = 'PT GEOSERVICES' (RESEARCH Focus 8 line 704;
      surveyors are organizational identifiers retained per D-13 sanitization rule)
    - unloading-specific keys: no_cow, no_coa, slagging_index, fouling_index
    - gcv_arb for anchor row = 4006.0 (unloading quality data present from row 2)
    """
    from services.coa_reconciliation import parse_coa_excel

    data = parse_coa_excel(_load_fixture_bytes("unloading_sample.xlsx"), "unloading")

    assert len(data) <= 50, f"Expected <= 50 records, got {len(data)}"

    anchor_rows = [r for r in data if str(r.get("shipment", "")) == ANCHOR_SHIPMENT]
    assert anchor_rows, f"Anchor Shipment {ANCHOR_SHIPMENT} not found in unloading parse output"

    anchor = anchor_rows[0]
    assert abs(anchor["ds_mt"] - ANCHOR_DS_MT) < 0.001, (
        f"unloading anchor ds_mt={anchor['ds_mt']!r}, expected {ANCHOR_DS_MT}"
    )
    assert anchor["suppliers"].startswith(ANCHOR_SUPPLIER_PREFIX), (
        f"unloading supplier not sanitized: {anchor['suppliers']!r}"
    )
    # Surveyor is an organizational identifier (not PII per D-13); must be preserved
    assert anchor.get("surveyor") == "PT GEOSERVICES", (
        f"unloading anchor surveyor={anchor.get('surveyor')!r}, expected 'PT GEOSERVICES'"
    )
    # Unloading-specific schema keys
    assert "no_cow" in anchor, "unloading record missing 'no_cow' key"
    assert "slagging_index" in anchor, "unloading record missing 'slagging_index' key"
    assert "fouling_index" in anchor, "unloading record missing 'fouling_index' key"

    # Quality data is present from row 2 for unloading
    assert anchor.get("gcv_arb") is not None, "unloading anchor gcv_arb should not be None"
    assert abs(anchor["gcv_arb"] - 4006.0) < 0.5, (
        f"unloading anchor gcv_arb={anchor['gcv_arb']!r}, expected ~4006.0"
    )


def test_coa_regression_internal():
    """OPS-03 / 06-03-03: lab_internal_sample.xlsx round-trips through parse_coa_excel.

    Assertions:
    - Returns <= 50 records
    - Anchor row Shipment 555 is present with ds_mt=5626.021
    - Supplier sanitized correctly
    - Record schema contains expected keys (gcv_arb, tm_arb, ash_arb, ts_arb)
    - Quality values for first-50-row window are NaN in production data (this is
      expected — lab data only starts at Shipment ~725); assert keys exist, not values
    """
    from services.coa_reconciliation import parse_coa_excel

    data = parse_coa_excel(_load_fixture_bytes("lab_internal_sample.xlsx"), "internal")

    assert len(data) <= 50, f"Expected <= 50 records, got {len(data)}"

    anchor_rows = [r for r in data if str(r.get("shipment", "")) == ANCHOR_SHIPMENT]
    assert anchor_rows, f"Anchor Shipment {ANCHOR_SHIPMENT} not found in internal parse output"

    anchor = anchor_rows[0]
    assert abs(anchor["ds_mt"] - ANCHOR_DS_MT) < 0.001, (
        f"internal anchor ds_mt={anchor['ds_mt']!r}, expected {ANCHOR_DS_MT}"
    )
    assert anchor["suppliers"].startswith(ANCHOR_SUPPLIER_PREFIX), (
        f"internal supplier not sanitized: {anchor['suppliers']!r}"
    )
    # Quality keys must be present in schema (may be None — sparse data in first 50 rows)
    for key in ("gcv_arb", "tm_arb", "ash_arb", "ts_arb"):
        assert key in anchor, (
            f"internal record missing quality key '{key}' — parser schema regression"
        )
    # source_type must be correctly tagged
    assert anchor.get("source_type") == "internal", (
        f"internal anchor source_type={anchor.get('source_type')!r}"
    )
