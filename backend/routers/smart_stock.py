from datetime import datetime, timedelta, timezone
import io
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
import pandas as pd

from models import SmartStockEntry, SumberPemakaianEntry
from utils.auth import get_current_user
from utils.database import db

router = APIRouter(tags=["Smart Stock"])
logger = logging.getLogger(__name__)


@router.get("/smart-stock")
async def get_smart_stock(
    limit: int = Query(100, ge=1, le=50000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get smart stock data with optional date range filter"""
    query = {}
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["date"] = date_query

    stocks = await db.smartstock.find(query, {"_id": 0}).sort("date", -1).limit(limit).to_list(limit)

    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_stocks = await db.smartstock.find(
        {"date": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("date", 1).to_list(100)

    supplier_totals = {}
    for stock in recent_stocks:
        suppliers = stock.get("suppliers", {})
        for supplier_name, zones in suppliers.items():
            if supplier_name not in supplier_totals:
                supplier_totals[supplier_name] = 0
            for zone, value in zones.items():
                supplier_totals[supplier_name] += value if value else 0

    return {
        "data": stocks,
        "recent_30_days": recent_stocks,
        "supplier_totals": supplier_totals,
        "total_count": len(stocks)
    }


@router.post("/smart-stock/entry")
async def create_smart_stock_entry(
    entry: SmartStockEntry,
    user: dict = Depends(get_current_user)
):
    """Create new manual smart stock entry"""
    total = 0
    for supplier, zones in entry.suppliers.items():
        for zone, value in zones.items():
            total += value if value else 0

    entry.total_penerimaan = total

    new_entry = {
        "id": str(uuid.uuid4()),
        "date": entry.date,
        "stock_awal": entry.stock_awal,
        "suppliers": entry.suppliers,
        "total_penerimaan": entry.total_penerimaan,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.smartstock.insert_one(new_entry)
    return {"message": "Entry created successfully", "id": new_entry["id"]}


@router.post("/smart-stock/upload")
async def upload_smart_stock_excel(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload Excel file and parse smart stock data"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), header=None)

        header_row_0 = df.iloc[0].tolist()

        logger.info(f"Header row 0 (first 15): {header_row_0[:15]}")

        skip_keywords = [
            'TANGGAL', 'STOCK', 'AWAL', 'SUMBER', 'PENERIMAAN', 'TOTAL',
            'TOTALPENERIMAAN', 'TOTAL_PENERIMAAN', 'AKHIR', 'MT'
        ]

        supplier_columns = {}
        current_supplier = None
        col_start = None

        for col_idx in range(4, len(header_row_0)):
            cell_value = header_row_0[col_idx]

            if pd.notna(cell_value) and str(cell_value).strip() != '':
                cell_str = str(cell_value).strip().upper().replace(" ", "")
                is_skip = any(kw in cell_str for kw in skip_keywords)

                if is_skip:
                    if current_supplier and col_start is not None:
                        supplier_columns[current_supplier] = (col_start, col_idx)
                        current_supplier = None
                        col_start = None
                    continue

                if current_supplier and col_start is not None:
                    supplier_columns[current_supplier] = (col_start, col_idx)

                current_supplier = str(cell_value).strip()
                col_start = col_idx

        if current_supplier and col_start is not None:
            supplier_columns[current_supplier] = (col_start, len(df.columns))

        logger.info(f"Found {len(supplier_columns)} suppliers: {list(supplier_columns.keys())}")

        inserted_count = 0
        for idx in range(2, len(df)):
            row = df.iloc[idx]

            if pd.isna(row.iloc[0]):
                continue

            try:
                date_val = row.iloc[0]
                if isinstance(date_val, (int, float)):
                    date_value = pd.to_datetime(date_val, origin='1899-12-30', unit='D')
                else:
                    date_value = pd.to_datetime(date_val)
                date_str = date_value.strftime("%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Date parsing error at row {idx}: {e}")
                continue

            stock_awal = _safe_float(row.iloc[1])

            total_penerimaan = 0.0
            for col_idx, header in enumerate(header_row_0):
                if pd.notna(header):
                    header_str = str(header).upper().replace(" ", "")
                    if 'TOTALPENERIMAAN' in header_str or header_str == 'TOTAL':
                        total_penerimaan = _safe_float(row.iloc[col_idx])
                        break

            if total_penerimaan == 0.0:
                total_penerimaan = _safe_float(row.iloc[3]) if len(row) > 3 else 0.0

            suppliers_data = {}
            for supplier_name, (start_col, end_col) in supplier_columns.items():
                supplier_key = (supplier_name.strip()
                    .replace(" ", "_")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("&", "")
                    .replace("-", "_")
                    .upper())

                zones = {"A": 0.0, "B": 0.0, "C": 0.0}
                zone_keys = ["A", "B", "C"]

                for i, col in enumerate(range(start_col, min(start_col + 3, end_col))):
                    if col < len(row) and i < 3:
                        zones[zone_keys[i]] = _safe_float(row.iloc[col])

                suppliers_data[supplier_key] = zones

            stock_akhir = stock_awal + total_penerimaan
            existing = await db.smartstock.find_one({"date": date_str})

            if existing:
                await db.smartstock.update_one(
                    {"date": date_str},
                    {"$set": {
                        "stock_awal": stock_awal,
                        "suppliers": suppliers_data,
                        "total_penerimaan": total_penerimaan,
                        "stock_akhir": stock_akhir,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            else:
                new_entry = {
                    "id": str(uuid.uuid4()),
                    "date": date_str,
                    "stock_awal": stock_awal,
                    "suppliers": suppliers_data,
                    "total_penerimaan": total_penerimaan,
                    "stock_akhir": stock_akhir,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.smartstock.insert_one(new_entry)

            inserted_count += 1

        return {
            "message": f"Successfully processed {inserted_count} entries",
            "count": inserted_count,
            "suppliers_found": list(supplier_columns.keys())
        }

    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


def _safe_float(value) -> float:
    """Safely convert value to float"""
    if pd.isna(value) or value == '' or value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


@router.delete("/smart-stock/{entry_id}")
async def delete_smart_stock_entry(
    entry_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a smart stock entry"""
    result = await db.smartstock.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": "Entry deleted successfully"}


@router.delete("/smart-stock")
async def delete_all_smart_stock(
    user: dict = Depends(get_current_user)
):
    """Delete all smart stock entries"""
    result = await db.smartstock.delete_many({})

    return {
        "message": f"Successfully deleted {result.deleted_count} entries",
        "deleted_count": result.deleted_count
    }


@router.get("/sumber-pemakaian")
async def get_sumber_pemakaian(
    limit: int = Query(100, ge=1, le=50000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get sumber pemakaian data with optional date range filter"""
    query = {}
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["date"] = date_query

    pemakaian = await db.sumberpemakaian.find(query, {"_id": 0}).sort("date", -1).limit(limit).to_list(limit)

    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_pemakaian = await db.sumberpemakaian.find(
        {"date": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("date", 1).to_list(100)

    latest_data = await db.sumberpemakaian.find_one({}, {"_id": 0}, sort=[("date", -1)])

    stats = {
        "total_burn_today": 0,
        "unit1_load": 0,
        "unit2_load": 0,
        "dominant_source": "N/A",
        "latest_date": None
    }

    if latest_data and latest_data.get("suppliers"):
        stats["latest_date"] = latest_data["date"]
        supplier_totals = {}

        for supplier, units in latest_data["suppliers"].items():
            supplier_total = 0
            for unit, zones in units.items():
                unit_total = sum(zones.values())
                if unit == "UNIT1":
                    stats["unit1_load"] += unit_total
                elif unit == "UNIT2":
                    stats["unit2_load"] += unit_total
                supplier_total += unit_total
            supplier_totals[supplier] = supplier_total

        stats["total_burn_today"] = stats["unit1_load"] + stats["unit2_load"]

        if supplier_totals:
            dominant = max(supplier_totals.items(), key=lambda x: x[1])
            if dominant[1] > 0:
                stats["dominant_source"] = dominant[0].replace("_", " ")

    return {
        "data": pemakaian,
        "recent_30_days": recent_pemakaian,
        "stats": stats,
        "total_count": len(pemakaian)
    }


@router.post("/sumber-pemakaian/entry")
async def create_sumber_pemakaian_entry(
    entry: SumberPemakaianEntry,
    user: dict = Depends(get_current_user)
):
    """Create new manual sumber pemakaian entry"""
    total = 0
    for supplier, units in entry.suppliers.items():
        for unit, zones in units.items():
            for zone, value in zones.items():
                total += value if value else 0

    entry.total_pemakaian = total

    new_entry = {
        "id": str(uuid.uuid4()),
        "date": entry.date,
        "stock_awal": entry.stock_awal,
        "suppliers": entry.suppliers,
        "total_pemakaian": entry.total_pemakaian,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.sumberpemakaian.insert_one(new_entry)
    return {"message": "Entry created successfully", "id": new_entry["id"]}


@router.post("/sumber-pemakaian/upload")
async def upload_sumber_pemakaian_excel(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload Excel file and parse sumber pemakaian data with correct column mapping"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), header=None)

        suppliers_row = df.iloc[1, 2:].tolist()

        supplier_columns = []
        current_supplier = None
        col_count = 0

        for i, cell_value in enumerate(suppliers_row):
            if pd.notna(cell_value) and str(cell_value).strip() != '':
                if current_supplier and col_count > 0:
                    supplier_columns.append((current_supplier, col_count))
                current_supplier = str(cell_value).strip()
                col_count = 1
            else:
                col_count += 1

        if current_supplier:
            supplier_columns.append((current_supplier, col_count))

        logger.info(f"Found suppliers for pemakaian: {[s[0] for s in supplier_columns]}")

        inserted_count = 0
        for idx in range(4, len(df)):
            row = df.iloc[idx]

            if pd.isna(row[0]):
                continue

            try:
                if isinstance(row[0], (int, float)):
                    date_value = pd.to_datetime(row[0], origin='1899-12-30', unit='D')
                else:
                    date_value = pd.to_datetime(row[0])
                date_str = date_value.strftime("%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Date parsing error at row {idx}: {e}")
                continue

            stock_awal = float(row[1]) if pd.notna(row[1]) and row[1] != '' else 0.0

            suppliers_data = {}
            col_offset = 2

            for supplier_name, num_cols in supplier_columns:
                supplier_key = supplier_name.strip().replace(" ", "_").replace("(", "").replace(")", "").replace("&", "").replace("-", "_").upper()

                units_data = {
                    "UNIT1": {"A": 0.0, "B": 0.0, "C": 0.0},
                    "UNIT2": {"A": 0.0, "B": 0.0, "C": 0.0}
                }

                for i in range(min(num_cols, 6)):
                    col = col_offset + i
                    if col < len(row):
                        unit = "UNIT1" if i < 3 else "UNIT2"
                        zone = ["A", "B", "C"][i % 3]
                        try:
                            units_data[unit][zone] = float(row[col]) if pd.notna(row[col]) and row[col] != '' else 0.0
                        except Exception:
                            units_data[unit][zone] = 0.0

                suppliers_data[supplier_key] = units_data
                col_offset += num_cols

            total_pemakaian = 0
            for col in range(2, len(row)):
                try:
                    val = float(row[col]) if pd.notna(row[col]) and row[col] != '' else 0.0
                    total_pemakaian += val
                except Exception:
                    pass

            existing = await db.sumberpemakaian.find_one({"date": date_str})

            if existing:
                await db.sumberpemakaian.update_one(
                    {"date": date_str},
                    {"$set": {
                        "stock_awal": stock_awal,
                        "suppliers": suppliers_data,
                        "total_pemakaian": total_pemakaian,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            else:
                new_entry = {
                    "id": str(uuid.uuid4()),
                    "date": date_str,
                    "stock_awal": stock_awal,
                    "suppliers": suppliers_data,
                    "total_pemakaian": total_pemakaian,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.sumberpemakaian.insert_one(new_entry)

            inserted_count += 1

        return {
            "message": f"Successfully processed {inserted_count} entries",
            "count": inserted_count
        }

    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.delete("/sumber-pemakaian")
async def delete_all_sumber_pemakaian(
    user: dict = Depends(get_current_user)
):
    """Delete all sumber pemakaian entries"""
    result = await db.sumberpemakaian.delete_many({})

    return {
        "message": f"Successfully deleted {result.deleted_count} entries",
        "deleted_count": result.deleted_count
    }
