from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from utils.auth import get_current_user
from utils.database import db

router = APIRouter(prefix="/reports", tags=["Reports"])


def _period_bounds(period: Optional[str]):
    if not period or period == "all":
        return None
    if len(period) == 4 and period.isdigit():
        year = int(period)
        return f"{year}-01-01", f"{year + 1}-01-01"
    if len(period) == 7 and period[4] == "-":
        year = int(period[:4])
        month = int(period[5:7])
        if month == 12:
            return f"{year}-12-01", f"{year + 1}-01-01"
        return f"{year}-{month:02d}-01", f"{year}-{month + 1:02d}-01"
    return None


def _period_match(field: str, period: Optional[str]) -> dict:
    bounds = _period_bounds(period)
    if not bounds:
        return {}
    start, end = bounds
    return {field: {"$gte": start, "$lt": end}}


def _date_match(field: str, period: Optional[str], date_from: Optional[str], date_to: Optional[str]) -> dict:
    if date_from or date_to:
        condition = {}
        if date_from:
            condition["$gte"] = date_from
        if date_to:
            condition["$lte"] = date_to
        return {field: condition}
    return _period_match(field, period)


def _supplier_match(field: str, supplier: Optional[str]) -> dict:
    if not supplier or supplier == "all":
        return {}
    return {field: supplier}


def _merge_match(*parts: dict) -> dict:
    result = {}
    for part in parts:
        result.update(part)
    return result


async def _sum_collection(collection, match: dict, field: str) -> float:
    result = await collection.aggregate([
        {"$match": match},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": [f"${field}", 0]}}}},
    ]).to_list(1)
    return float(result[0]["total"]) if result else 0.0


async def _avg_collection(collection, match: dict, field: str) -> Optional[float]:
    result = await collection.aggregate([
        {"$match": {**match, field: {"$ne": None}}},
        {"$group": {"_id": None, "avg": {"$avg": f"${field}"}}},
    ]).to_list(1)
    return float(result[0]["avg"]) if result else None


def _stock_status(days_of_supply: Optional[int]) -> str:
    if days_of_supply is None:
        return "unknown"
    if days_of_supply < 7:
        return "critical"
    if days_of_supply < 14:
        return "warning"
    if days_of_supply < 30:
        return "watch"
    return "healthy"


async def _supplier_performance(
    period: Optional[str],
    supplier: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> list[dict]:
    sources = [
        (db.vessels, "completed_unloading", "suppliers", "ds_mt"),
        (db.barges, "completed_unloading", "suppliers", "ds_mt"),
        (db.trucking, "completed_unloading", "suppliers", "ds_mt"),
        (db.biomassa, "completed_unloading", "suppliers", "jembatan_timbang_mt"),
    ]
    totals = {}
    for collection, date_field, supplier_field, tonnage_field in sources:
        match = _merge_match(_date_match(date_field, period, date_from, date_to), _supplier_match(supplier_field, supplier))
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": f"${supplier_field}",
                    "record_count": {"$sum": 1},
                    "realized_tonnage": {"$sum": {"$ifNull": [f"${tonnage_field}", 0]}},
                    "avg_gcv": {"$avg": "$gcv_arb"},
                }
            },
        ]
        for item in await collection.aggregate(pipeline).to_list(500):
            name = item.get("_id") or "Tanpa Supplier"
            current = totals.setdefault(name, {"supplier": name, "record_count": 0, "realized_tonnage": 0.0, "gcv_values": []})
            current["record_count"] += item.get("record_count", 0)
            current["realized_tonnage"] += float(item.get("realized_tonnage") or 0)
            if item.get("avg_gcv") is not None:
                current["gcv_values"].append(float(item["avg_gcv"]))

    rows = []
    for item in totals.values():
        gcv_values = item.pop("gcv_values")
        item["avg_gcv"] = (sum(gcv_values) / len(gcv_values)) if gcv_values else None
        rows.append(item)
    return sorted(rows, key=lambda row: row["realized_tonnage"], reverse=True)[:10]


@router.get("/management")
async def get_management_report(
    period: Optional[str] = Query("all"),
    supplier: Optional[str] = Query("all"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Executive report summary for stock, arrivals, suppliers, loss, and disputes."""
    stock_match = _date_match("date", period, date_from, date_to)
    total_penerimaan = await _sum_collection(db.smartstock, stock_match, "total_penerimaan")
    total_pemakaian = await _sum_collection(db.sumberpemakaian, stock_match, "total_pemakaian")
    latest_stock = await db.smartstock.find_one({}, {"_id": 0}, sort=[("date", -1)])
    latest_usage = await db.sumberpemakaian.find_one({}, {"_id": 0}, sort=[("date", -1)])
    current_stock = latest_stock.get("stock_akhir") if latest_stock and latest_stock.get("stock_akhir") is not None else None
    if current_stock is None:
        current_stock = (
            (latest_stock.get("stock_awal", 0) if latest_stock else 0)
            + (latest_stock.get("total_penerimaan", 0) if latest_stock else 0)
            - (latest_usage.get("total_pemakaian", 0) if latest_usage else 0)
        )
    avg_daily_usage = total_pemakaian / 30 if total_pemakaian > 0 else 0
    days_of_supply = int(current_stock / avg_daily_usage) if avg_daily_usage > 0 else None

    po_match = _merge_match(_date_match("time_arrival", period, date_from, date_to), _supplier_match("supplier_name", supplier))
    scheduled_count = await db.po_batubara.count_documents(po_match)
    scheduled_tonnage = await _sum_collection(db.po_batubara, po_match, "tonase_po")

    realized_sources = [
        ("vessel", db.vessels, "completed_unloading", "suppliers", "ds_mt"),
        ("barge", db.barges, "completed_unloading", "suppliers", "ds_mt"),
        ("trucking", db.trucking, "completed_unloading", "suppliers", "ds_mt"),
        ("biomassa", db.biomassa, "completed_unloading", "suppliers", "jembatan_timbang_mt"),
    ]
    realized_count = 0
    realized_tonnage = 0.0
    realized_by_mode = []
    gcv_values = []
    source_counts = {
        "smartstock": await db.smartstock.count_documents(stock_match),
        "sumberpemakaian": await db.sumberpemakaian.count_documents(stock_match),
        "po_batubara": scheduled_count,
    }
    for mode, collection, date_field, supplier_field, tonnage_field in realized_sources:
        match = _merge_match(_date_match(date_field, period, date_from, date_to), _supplier_match(supplier_field, supplier))
        count = await collection.count_documents(match)
        tonnage = await _sum_collection(collection, match, tonnage_field)
        avg_gcv = await _avg_collection(collection, match, "gcv_arb")
        realized_count += count
        realized_tonnage += tonnage
        if avg_gcv is not None:
            gcv_values.append(avg_gcv)
        source_counts[mode] = count
        realized_by_mode.append({"mode": mode, "count": count, "tonnage": tonnage})

    coa_match = _merge_match(_date_match("completed_unloading", period, date_from, date_to), _supplier_match("suppliers", supplier))
    coa_items = await db.coa_reconciliation.find(coa_match, {"_id": 0}).to_list(10000)
    source_counts["coa_reconciliation"] = len(coa_items)
    critical_count = sum(1 for item in coa_items if str(item.get("status", "")).lower() in {"critical", "kritis"})
    warning_count = sum(1 for item in coa_items if str(item.get("status", "")).lower() == "warning")
    proposed_count = sum(1 for item in coa_items if item.get("umpire_status") == "proposed")
    in_progress_count = sum(1 for item in coa_items if item.get("umpire_status") == "in_progress")
    completed_count = sum(1 for item in coa_items if item.get("umpire_status") == "completed")
    potential_loss_mt = sum(abs(float(item.get("delta_loading_internal") or 0)) for item in coa_items)
    impacted_tonnage = sum(float(item.get("ds_mt") or 0) for item in coa_items if item.get("delta_loading_internal") is not None)

    return {
        "period": period or "all",
        "supplier": supplier or "all",
        "date_from": date_from,
        "date_to": date_to,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.get("username") or user.get("email") or user.get("id"),
        "source_counts": source_counts,
        "stock": {
            "current_stock": float(current_stock or 0),
            "latest_stock_date": latest_stock.get("date") if latest_stock else None,
            "latest_usage_date": latest_usage.get("date") if latest_usage else None,
            "total_penerimaan": total_penerimaan,
            "total_pemakaian": total_pemakaian,
            "avg_daily_usage": avg_daily_usage,
            "days_of_supply": days_of_supply,
            "status": _stock_status(days_of_supply),
        },
        "arrivals": {
            "scheduled_count": scheduled_count,
            "scheduled_tonnage": scheduled_tonnage,
            "realized_count": realized_count,
            "realized_tonnage": realized_tonnage,
            "count_gap": scheduled_count - realized_count,
            "tonnage_gap": scheduled_tonnage - realized_tonnage,
            "fulfillment_rate": (realized_count / scheduled_count * 100) if scheduled_count else None,
            "tonnage_fulfillment_rate": (realized_tonnage / scheduled_tonnage * 100) if scheduled_tonnage else None,
            "realized_by_mode": realized_by_mode,
        },
        "quality": {
            "avg_gcv": (sum(gcv_values) / len(gcv_values)) if gcv_values else None,
            "sample_count": sum(item["count"] for item in realized_by_mode),
        },
        "supplier_performance": await _supplier_performance(period, supplier, date_from, date_to),
        "potential_loss": {
            "record_count": len(coa_items),
            "potential_loss_mt": potential_loss_mt,
            "impacted_tonnage": impacted_tonnage,
            "critical_count": critical_count,
            "warning_count": warning_count,
        },
        "disputes": {
            "critical_count": critical_count,
            "warning_count": warning_count,
            "umpire": {
                "proposed": proposed_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
                "active": proposed_count + in_progress_count,
            },
        },
    }
