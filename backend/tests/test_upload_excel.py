"""TEST-04: Excel upload parser-path coverage with round-trip assertions.

Source of truth:
- D-08: 4 synthetic fixtures at tests/fixtures/excel/
- D-09: assert 200/201 + deterministic round-trip; no production totals
- ROADMAP Phase-2 SC-3: admin/operator allowed, viewer denied (role gate)
- server.py: upload endpoints return {"message": ..., "count": ...} on success
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
