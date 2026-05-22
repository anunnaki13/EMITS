from pathlib import Path

import pytest

from services.coa_reconciliation import (
    apply_preserved_coa_fields,
    build_combined_coa_import_preview,
    calculate_kpis,
    parse_combined_coa_workbook,
)


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


def test_calculate_kpis_uses_po_purchase_price_instead_of_manual_coa_price():
    records = [
        {
            "shipment": "LOT 1",
            "suppliers": "PT TDE",
            "completed_unloading": "2025-01-10T00:00:00",
            "loading_gcv_arb": 4000,
            "internal_gcv_arb": 3900,
            "delta_loading_internal": 100,
            "ds_mt": 10,
            "umpire_status": "completed",
            "umpire_gcv_arb": 3900,
            "status": "critical",
        },
        {
            "shipment": "LOT 481",
            "suppliers": "TDE",
            "completed_unloading": "2026-03-01T00:00:00",
            "loading_gcv_arb": 4000,
            "internal_gcv_arb": 3800,
            "delta_loading_internal": 200,
            "ds_mt": 5,
            "umpire_status": "none",
            "status": "critical",
        },
    ]
    po_records = [
        {
            "no_shipment": "LOT 1",
            "supplier_name": "PT. TIGA DAYA ENERGI",
            "time_arrival": "2025-01-08",
            "tonase_po": 10,
            "total": 4_000_000,
        },
        {
            "no_shipment": "LOT 460",
            "supplier_name": "PT. KONS TIGA DAYA ENERGI",
            "time_arrival": "2025-12-20",
            "tonase_po": 10,
            "total": 9_552_270,
        },
    ]

    kpis = calculate_kpis(records, price_per_kcal_per_ton=950000, po_records=po_records)

    assert kpis["potential_loss_rp"] == 338807
    assert kpis["umpire_savings_rp"] == 100000
    assert kpis["potential_loss_price_source_counts"] == {
        "po_shipment": 1,
        "po_supplier_latest": 1,
    }
    assert kpis["potential_loss_priced_count"] == 2
    assert kpis["potential_loss_unpriced_count"] == 0


def test_combined_coa_preview_reports_diff_duplicates_and_preservation():
    records = [
        {
            "id": "incoming-1",
            "shipment": "LOT 1",
            "source_row": 3,
            "suppliers": "PT BARU",
            "completed_unloading": "2026-03-01T00:00:00",
            "loading_gcv_arb": 4300,
            "unloading_gcv_arb": 4280,
            "internal_gcv_arb": 4200,
            "umpire_status": "none",
        },
        {
            "id": "incoming-dup",
            "shipment": "LOT 1",
            "source_row": 4,
            "suppliers": "PT BARU",
            "completed_unloading": "2026-03-01T00:00:00",
            "loading_gcv_arb": 4300,
            "unloading_gcv_arb": 4280,
            "internal_gcv_arb": 4200,
            "umpire_status": "none",
        },
        {
            "id": "incoming-2",
            "shipment": "LOT 2",
            "source_row": 5,
            "suppliers": "PT BARU 2",
            "completed_unloading": "2026-03-02T00:00:00",
            "loading_gcv_arb": 4400,
            "unloading_gcv_arb": 4380,
            "internal_gcv_arb": 4350,
            "umpire_status": "none",
        },
    ]
    existing = [
        {
            "id": "existing-1",
            "shipment": "LOT 1",
            "suppliers": "PT LAMA",
            "completed_unloading": "2026-02-01T00:00:00",
            "loading_gcv_arb": 4100,
            "unloading_gcv_arb": 4080,
            "internal_gcv_arb": 4000,
            "umpire_status": "proposed",
            "dispute_notes": [{"note": "jangan hilang"}],
        },
        {
            "id": "existing-removed",
            "shipment": "LOT 99",
            "umpire_status": "completed",
            "dispute_attachments": [{"filename": "roa.pdf"}],
        },
    ]

    preview = build_combined_coa_import_preview(
        records,
        {"records": 3, "loading": 3, "unloading": 3, "internal": 3, "umpire": 0},
        existing,
    )

    assert preview["validation_summary"]["critical"] == 1
    assert any(issue["type"] == "duplicate_in_file" for issue in preview["issues"])
    assert preview["diff_summary"]["inserted"] == 1
    assert preview["diff_summary"]["updated"] == 1
    assert preview["diff_summary"]["removed_if_replace"] == 1
    assert preview["preservation_summary"]["matched_records_with_dispute"] == 1
    assert preview["preservation_summary"]["removed_records_with_dispute_if_replace"] == 1


def test_apply_preserved_coa_fields_keeps_dispute_workflow_and_existing_id():
    imported = {
        "id": "new-id",
        "shipment": "LOT 7",
        "created_at": "2026-05-01T00:00:00",
        "umpire_status": "none",
        "internal_gcv_arb": 4200,
    }
    existing = {
        "id": "existing-id",
        "shipment": "LOT 7",
        "created_at": "2026-04-01T00:00:00",
        "umpire_status": "in_progress",
        "umpire_sample_number": "S-7",
        "dispute_notes": [{"note": "preserve"}],
    }

    merged = apply_preserved_coa_fields(imported, existing)

    assert merged["id"] == "existing-id"
    assert merged["created_at"] == "2026-04-01T00:00:00"
    assert merged["umpire_status"] == "in_progress"
    assert merged["umpire_sample_number"] == "S-7"
    assert merged["dispute_notes"] == [{"note": "preserve"}]
    assert merged["import_preserved_dispute"] is True
