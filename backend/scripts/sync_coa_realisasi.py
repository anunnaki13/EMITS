#!/usr/bin/env python3
"""Sync combined COA workbook rows into arrival realization collections.

The combined COA workbook is the authoritative 2026 quality/reconciliation
source, but dashboard arrival realization reads from vessels/barges/trucking.
This script projects COA rows into those collections with an import marker so
the operation is idempotent and auditable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient, ReplaceOne

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.coa_reconciliation import parse_combined_coa_workbook  # noqa: E402


SYNC_SYSTEM = "coa_workbook_realisasi_sync"
SYNC_VERSION = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync COA workbook rows into realization collections")
    parser.add_argument("workbook", type=Path, help="Path to Rekapitulasi CoA workbook")
    parser.add_argument("--year", type=int, default=2026, help="Completed unloading year to sync")
    parser.add_argument("--db-name", default=None, help="Override DB_NAME from backend/.env")
    parser.add_argument("--dry-run", action="store_true", help="Parse and summarize only; do not write MongoDB")
    parser.add_argument("--uploaded-by", default="system-import", help="created_by value for synced records")
    parser.add_argument("--backup-dir", type=Path, default=PROJECT_DIR / "backend" / "backups")
    return parser.parse_args()


def _year(value: Any) -> int | None:
    text = str(value or "")
    return int(text[:4]) if len(text) >= 4 and text[:4].isdigit() else None


def _period(value: str | None) -> str:
    text = str(value or "")
    return f"{text[:7]}-01" if len(text) >= 7 else text


def _date(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None


def _text(value: Any) -> str:
    return str(value or "").strip()


def _source_key(workbook_name: str, record: dict[str, Any]) -> str:
    shipment = _text(record.get("shipment")).upper().replace(" ", "")
    completed = _text(record.get("completed_unloading"))[:19]
    return f"{workbook_name}:{shipment}:{completed}"


def classify_mode(record: dict[str, Any]) -> str:
    shipment = _text(record.get("shipment")).upper()
    tb = _text(record.get("tb")).upper()
    bg = _text(record.get("bg")).upper()
    text = f"{shipment} {tb} {bg}"
    if shipment.startswith("LOT") or "DUMP TRUCK" in text or re.search(r"\bLOT\b", text):
        return "trucking"
    if tb.startswith("MV") or (record.get("ds_mt") or 0) >= 20000:
        return "vessels"
    return "barges"


def _quality_fields(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "ds_mt": record.get("ds_mt"),
        "gcv_arb": record.get("unloading_gcv_arb") or record.get("loading_gcv_arb") or record.get("internal_gcv_arb"),
        "tm_arb": record.get("unloading_tm_arb") or record.get("loading_tm_arb") or record.get("internal_tm_arb"),
        "ash_arb": record.get("unloading_ash_arb") or record.get("loading_ash_arb") or record.get("internal_ash_arb"),
        "ts_arb": record.get("unloading_ts_arb") or record.get("loading_ts_arb") or record.get("internal_ts_arb"),
        "slagging_index": record.get("unloading_slagging") or None,
        "fouling_index": record.get("unloading_fouling") or None,
        "no_coa": record.get("loading_no_coa") or None,
    }


def build_realization_doc(record: dict[str, Any], *, mode: str, workbook_name: str, uploaded_by: str, synced_at: str) -> dict[str, Any]:
    completed = _date(record.get("completed_unloading"))
    period = _period(record.get("periode") or completed)
    shipment = _text(record.get("shipment"))
    supplier = _text(record.get("suppliers"))
    tb = _text(record.get("tb"))
    bg = _text(record.get("bg"))
    source_key = _source_key(workbook_name, record)
    base = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{SYNC_SYSTEM}:{source_key}")),
        "shipment": shipment,
        "suppliers": supplier,
        "completed_unloading": completed,
        "commenced_unloading": record.get("commenced_unloading"),
        "import_source": workbook_name,
        "source_system": SYNC_SYSTEM,
        "source_version": SYNC_VERSION,
        "source_key": source_key,
        "source_row": record.get("source_row"),
        "created_at": synced_at,
        "created_by": uploaded_by,
        **_quality_fields(record),
    }
    if mode == "trucking":
        return {
            **base,
            "periode_ta": period,
            "periode_realisasi": period,
            "shipment_code": f"COA REALISASI {period[:7]} #{shipment}",
            "voyage_code": f"COA {supplier}#{shipment}",
            "transportasi": "MODA TRUCKING",
            "coal_from": "",
            "ta": completed,
            "berthed_time": completed,
        }
    if mode == "vessels":
        return {
            **base,
            "periode_ta": period,
            "periode_realisasi": period,
            "shipment_code": f"COA REALISASI {period[:7]} #{shipment}",
            "voyage_code": f"COA {supplier}#{shipment}",
            "voyage": shipment,
            "name_of_vessel": tb or f"Shipment {shipment}",
            "coal_from": "",
            "time_arrival": completed,
            "berthed_time": completed,
        }
    return {
        **base,
        "periode": period,
        "shipment_code": f"COA REALISASI {period[:7]} #{shipment}",
        "voyage_code": f"COA {supplier}#{shipment}",
        "voyage": shipment,
        "tb": tb,
        "bg": bg,
        "coal_from": "",
        "ta": completed,
        "berthed_time": completed,
    }


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def backup_collections(db, backup_dir: Path, collections: list[str], label: str) -> Path:
    target = backup_dir / f"realisasi-sync-backup-{label}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "collections": {
            name: _json_safe(list(db[name].find({})))
            for name in collections
        },
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def main() -> int:
    args = parse_args()
    workbook = args.workbook if args.workbook.is_absolute() else PROJECT_DIR / args.workbook
    if not workbook.exists():
        raise SystemExit(f"Workbook not found: {workbook}")

    records, _counts = parse_combined_coa_workbook(workbook.read_bytes())
    selected = [record for record in records if _year(record.get("completed_unloading")) == args.year]
    docs_by_collection: dict[str, list[dict[str, Any]]] = {"vessels": [], "barges": [], "trucking": []}
    synced_at = datetime.now(timezone.utc).isoformat()
    for record in selected:
        mode = classify_mode(record)
        docs_by_collection[mode].append(
            build_realization_doc(
                record,
                mode=mode,
                workbook_name=workbook.name,
                uploaded_by=args.uploaded_by,
                synced_at=synced_at,
            )
        )

    print(f"Parsed {len(records)} COA records; selected {len(selected)} for {args.year}")
    print("Mode counts:", {name: len(docs) for name, docs in docs_by_collection.items()})
    for name, docs in docs_by_collection.items():
        preview = sorted(docs, key=lambda item: item.get("completed_unloading") or "", reverse=True)[:3]
        print(f"  {name}: {len(docs)}")
        for item in preview:
            print(f"    {item.get('completed_unloading')} {item.get('shipment')} {item.get('suppliers')} {item.get('ds_mt')}")

    if args.dry_run:
        return 0

    load_dotenv(BACKEND_DIR / ".env")
    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=5000)
    db = client[args.db_name or os.environ["DB_NAME"]]
    label = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_collections(db, args.backup_dir, ["vessels", "barges", "trucking", "po_batubara"], label)
    print(f"Backup written: {backup_path}")

    for collection_name, docs in docs_by_collection.items():
        if not docs:
            continue
        operations = [
            ReplaceOne(
                {"source_system": SYNC_SYSTEM, "source_key": doc["source_key"]},
                doc,
                upsert=True,
            )
            for doc in docs
        ]
        result = db[collection_name].bulk_write(operations, ordered=False)
        print(
            f"{collection_name}: matched={result.matched_count} "
            f"modified={result.modified_count} upserted={len(result.upserted_ids)}"
        )

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
