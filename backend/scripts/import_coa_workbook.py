#!/usr/bin/env python3
"""Import the combined COA workbook into MongoDB."""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.coa_reconciliation import parse_combined_coa_workbook  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Import combined COA workbook into MongoDB")
    parser.add_argument("workbook", type=Path, help="Path to Rekapitulasi CoA workbook")
    parser.add_argument("--db-name", default=None, help="Override DB_NAME from backend/.env")
    parser.add_argument("--dry-run", action="store_true", help="Parse only; do not write MongoDB")
    parser.add_argument("--uploaded-by", default="system-import", help="Audit value for uploaded_by")
    return parser.parse_args()


def main():
    args = parse_args()
    workbook = args.workbook if args.workbook.is_absolute() else PROJECT_DIR / args.workbook
    if not workbook.exists():
        raise SystemExit(f"Workbook not found: {workbook}")

    records, source_counts = parse_combined_coa_workbook(workbook.read_bytes())
    print("Parsed combined COA workbook")
    for key in sorted(source_counts):
        print(f"  {key}: {source_counts[key]}")

    if args.dry_run:
        return

    load_dotenv(BACKEND_DIR / ".env")
    mongo_url = os.environ["MONGO_URL"]
    db_name = args.db_name or os.environ["DB_NAME"]

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    collection = db.coa_reconciliation

    uploaded_at = datetime.now(timezone.utc).isoformat()
    for record in records:
        record["uploaded_by"] = args.uploaded_by
        record["uploaded_at"] = uploaded_at
        record["import_source"] = workbook.name

    previous_count = collection.count_documents({})
    collection.delete_many({})
    if records:
        collection.insert_many(records)
    print(f"Replaced coa_reconciliation: {previous_count} -> {len(records)} records in DB {db_name}")
    client.close()


if __name__ == "__main__":
    main()
