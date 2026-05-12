from pathlib import Path

import pytest

from services.coa_reconciliation import calculate_kpis, parse_combined_coa_workbook


WORKBOOK = (
    Path(__file__).resolve().parents[2]
    / "Rekapitulasi CoA Loading, Unloading dan Lab Internal 2026 (Upd. Maret).xlsx"
)


def _key(value):
    return str(value).upper().replace(" ", "")


@pytest.mark.skipif(not WORKBOOK.exists(), reason="latest combined COA workbook is not checked out")
def test_parse_latest_combined_coa_workbook_counts_and_latest_rows():
    records, counts = parse_combined_coa_workbook(WORKBOOK.read_bytes())

    assert counts["records"] == 754
    assert counts["completed_unloading_min"] == "2020-08-03"
    assert counts["completed_unloading_max"] == "2026-04-27"
    assert counts["umpire_completed"] == 201
    assert records[0]["shipment"] == "LOT 483"
    assert records[0]["completed_unloading"].startswith("2026-04-27")

    lot_463 = next(record for record in records if _key(record["shipment"]) == "LOT463")
    assert lot_463["completed_unloading"].startswith("2026-01-08")
    assert lot_463["status"] == "critical"
    assert lot_463["umpire_status"] == "completed"
    assert lot_463["umpire_gcv_arb"] == 3873.0


@pytest.mark.skipif(not WORKBOOK.exists(), reason="latest combined COA workbook is not checked out")
def test_parse_latest_combined_coa_workbook_indonesian_period_and_kpi_total():
    records, _ = parse_combined_coa_workbook(WORKBOOK.read_bytes())

    lot_276 = next(record for record in records if _key(record["shipment"]) == "LOT276")
    assert lot_276["periode"] == "2023-05-01"

    kpis = calculate_kpis(records)
    assert kpis["umpire_status"]["completed"] == 201
    assert kpis["umpire_status"]["total"] == 201
