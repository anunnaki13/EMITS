import re
from datetime import date, datetime, timezone
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
    escaped = re.escape(str(supplier).strip())
    return {field: {"$regex": f"^{escaped}$", "$options": "i"}}


def _merge_match(*parts: dict) -> dict:
    result = {}
    for part in parts:
        result.update(part)
    return result


def _and_match(*parts: dict) -> dict:
    active = [part for part in parts if part]
    if not active:
        return {}
    if len(active) == 1:
        return active[0]
    return {"$and": active}


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


def _risk_status(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _safe_float(value) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _abs_delta(item: dict) -> Optional[float]:
    for field in ["delta_loading_internal", "delta_unloading_internal", "delta_loading_unloading"]:
        if item.get(field) is not None and item.get(field) != "":
            return abs(_safe_float(item.get(field)))
    return None


def _aging_days(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return max((date.today() - date.fromisoformat(str(value)[:10])).days, 0)
    except ValueError:
        return None


def _source_slice(name: str, collections: list[str], record_count: int, fields: list[str]) -> dict:
    return {
        "name": name,
        "collections": collections,
        "record_count": record_count,
        "fields": fields,
    }


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


async def _supplier_scorecard(
    period: Optional[str],
    supplier: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> list[dict]:
    supplier_map: dict[str, dict] = {}
    today_prefix = date.today().isoformat()

    def entry(name: Optional[str]) -> dict:
        supplier_name = str(name or "Tanpa Supplier").strip() or "Tanpa Supplier"
        if supplier_name not in supplier_map:
            supplier_map[supplier_name] = {
                "supplier": supplier_name,
                "scheduled_count": 0,
                "scheduled_tonnage": 0.0,
                "at_risk_count": 0,
                "realized_count": 0,
                "realized_tonnage": 0.0,
                "quality_records": 0,
                "critical_count": 0,
                "warning_count": 0,
                "active_disputes": 0,
                "avg_coa_delta": None,
                "max_coa_delta": None,
                "_delta_sum": 0.0,
                "_delta_count": 0,
            }
        return supplier_map[supplier_name]

    po_match = _merge_match(_date_match("time_arrival", period, date_from, date_to), _supplier_match("supplier_name", supplier))
    po_rows = await db.po_batubara.find(
        po_match,
        {"_id": 0, "supplier_name": 1, "time_arrival": 1, "tonase_po": 1},
    ).to_list(10000)
    for item in po_rows:
        row = entry(item.get("supplier_name"))
        row["scheduled_count"] += 1
        row["scheduled_tonnage"] += _safe_float(item.get("tonase_po"))
        if str(item.get("time_arrival") or "") < today_prefix:
            row["at_risk_count"] += 1

    sources = [
        (db.vessels, "completed_unloading", "suppliers", "ds_mt"),
        (db.barges, "completed_unloading", "suppliers", "ds_mt"),
        (db.trucking, "completed_unloading", "suppliers", "ds_mt"),
        (db.biomassa, "completed_unloading", "suppliers", "jembatan_timbang_mt"),
    ]
    for collection, date_field, supplier_field, tonnage_field in sources:
        match = _merge_match(_date_match(date_field, period, date_from, date_to), _supplier_match(supplier_field, supplier))
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": f"${supplier_field}",
                    "record_count": {"$sum": 1},
                    "realized_tonnage": {"$sum": {"$ifNull": [f"${tonnage_field}", 0]}},
                }
            },
        ]
        for item in await collection.aggregate(pipeline).to_list(1000):
            row = entry(item.get("_id"))
            row["realized_count"] += int(item.get("record_count") or 0)
            row["realized_tonnage"] += float(item.get("realized_tonnage") or 0)

    coa_match = _merge_match(_date_match("completed_unloading", period, date_from, date_to), _supplier_match("suppliers", supplier))
    coa_rows = await db.coa_reconciliation.find(
        coa_match,
        {"_id": 0, "suppliers": 1, "status": 1, "umpire_status": 1, "delta_loading_internal": 1, "delta_unloading_internal": 1, "delta_loading_unloading": 1},
    ).to_list(10000)
    for item in coa_rows:
        row = entry(item.get("suppliers"))
        row["quality_records"] += 1
        status = str(item.get("status", "")).lower()
        umpire_status = str(item.get("umpire_status", "")).lower()
        if status in {"critical", "kritis"}:
            row["critical_count"] += 1
        elif status == "warning":
            row["warning_count"] += 1
        if umpire_status in {"proposed", "in_progress"}:
            row["active_disputes"] += 1
        delta = _abs_delta(item)
        if delta is not None:
            row["_delta_sum"] += delta
            row["_delta_count"] += 1
            row["max_coa_delta"] = max(row["max_coa_delta"] or 0, delta)

    scorecard = []
    for row in supplier_map.values():
        if row["_delta_count"]:
            row["avg_coa_delta"] = row["_delta_sum"] / row["_delta_count"]
        timeliness_rate = None
        if row["scheduled_count"]:
            timeliness_rate = max(row["scheduled_count"] - row["at_risk_count"], 0) / row["scheduled_count"] * 100
        fulfillment_rate = None
        if row["scheduled_tonnage"]:
            fulfillment_rate = row["realized_tonnage"] / row["scheduled_tonnage"] * 100
        risk_score = (
            row["critical_count"] * 35
            + row["warning_count"] * 15
            + row["active_disputes"] * 25
            + row["at_risk_count"] * 10
            + min((row["avg_coa_delta"] or 0) / 4, 25)
        )
        if timeliness_rate is not None:
            risk_score += max((100 - timeliness_rate) / 4, 0)
        risk_score = min(max(risk_score, 0), 100)
        public_row = {
            "rank": 0,
            "supplier": row["supplier"],
            "scheduled_count": row["scheduled_count"],
            "scheduled_tonnage": row["scheduled_tonnage"],
            "at_risk_count": row["at_risk_count"],
            "realized_count": row["realized_count"],
            "realized_tonnage": row["realized_tonnage"],
            "fulfillment_rate": fulfillment_rate,
            "timeliness_rate": timeliness_rate,
            "quality_records": row["quality_records"],
            "avg_coa_delta": row["avg_coa_delta"],
            "max_coa_delta": row["max_coa_delta"],
            "critical_count": row["critical_count"],
            "warning_count": row["warning_count"],
            "active_disputes": row["active_disputes"],
            "risk_score": round(risk_score, 1),
            "risk_status": _risk_status(risk_score),
        }
        scorecard.append(public_row)

    scorecard.sort(
        key=lambda item: (
            item["risk_score"],
            item["active_disputes"],
            item["critical_count"],
            item["at_risk_count"],
            item["realized_tonnage"],
        ),
        reverse=True,
    )
    for index, item in enumerate(scorecard, start=1):
        item["rank"] = index
    return scorecard[:20]


def _management_summary(report: dict) -> list[str]:
    stock = report["stock"]
    arrivals = report["arrivals"]
    disputes = report["disputes"]
    quality = report["quality"]
    summary = [
        f"Stok saat ini {stock['current_stock']:,.0f} MT dengan status {stock['status']} dan estimasi coverage {stock['days_of_supply'] if stock['days_of_supply'] is not None else '-'} hari.",
        f"Realisasi kedatangan {arrivals['realized_tonnage']:,.0f} MT dari jadwal {arrivals['scheduled_tonnage']:,.0f} MT.",
        f"COA mencatat {quality['coa_records']} record, {quality['critical_count']} critical, {quality['warning_count']} warning, dan rata-rata delta {quality['avg_coa_delta'] if quality['avg_coa_delta'] is not None else '-'} kcal/kg.",
        f"Dispute aktif {disputes['umpire']['active']} record dengan {disputes['stale_count']} dispute stale.",
    ]
    if report["data_health"]["empty"]:
        summary.append("Data pada filter ini masih kosong atau sangat terbatas; gunakan ringkasan ini sebagai indikasi awal, bukan kesimpulan final.")
    return summary


async def build_management_report(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: Optional[dict] = None,
) -> dict:
    """Build a source-traceable executive report payload."""
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
    today_prefix = date.today().isoformat()
    at_risk_match = _and_match(po_match, {"time_arrival": {"$lt": today_prefix}})
    at_risk_count = await db.po_batubara.count_documents(at_risk_match)
    at_risk_tonnage = await _sum_collection(db.po_batubara, at_risk_match, "tonase_po")

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
    active_items = [item for item in coa_items if item.get("umpire_status") in {"proposed", "in_progress"}]
    active_aging = [_aging_days(item.get("completed_unloading")) for item in active_items]
    stale_aging = [value for value in active_aging if value is not None and value >= 7]
    deltas = [delta for delta in (_abs_delta(item) for item in coa_items) if delta is not None]
    potential_loss_mt = sum(deltas)
    impacted_tonnage = sum(float(item.get("ds_mt") or 0) for item in coa_items if _abs_delta(item) is not None)

    settings = await db.app_settings.find_one({"type": "coa"}, {"_id": 0, "price_per_kcal_per_ton": 1})
    price_per_kcal_per_ton = _safe_float(settings.get("price_per_kcal_per_ton")) if settings else 0
    estimated_loss_value = None
    if price_per_kcal_per_ton:
        estimated_loss_value = sum(
            (_abs_delta(item) or 0) * _safe_float(item.get("ds_mt")) * price_per_kcal_per_ton
            for item in coa_items
        )

    supplier_performance = await _supplier_performance(period, supplier, date_from, date_to)
    supplier_scorecard = await _supplier_scorecard(period, supplier, date_from, date_to)
    total_source_records = sum(int(value or 0) for value in source_counts.values())
    partial_warnings = []
    if source_counts["po_batubara"] == 0:
        partial_warnings.append("Tidak ada data jadwal PO pada filter ini.")
    if realized_count == 0:
        partial_warnings.append("Tidak ada data realisasi kedatangan pada filter ini.")
    if len(coa_items) == 0:
        partial_warnings.append("Tidak ada data COA reconciliation pada filter ini.")
    if total_pemakaian == 0:
        partial_warnings.append("Tidak ada data pemakaian stock pada filter ini sehingga days of supply tidak bisa dihitung.")

    source_slices = [
        _source_slice("stock_summary", ["smartstock", "sumberpemakaian"], source_counts["smartstock"] + source_counts["sumberpemakaian"], ["date", "total_penerimaan", "total_pemakaian", "stock_akhir"]),
        _source_slice("arrival_schedule_vs_realization", ["po_batubara", "vessels", "barges", "trucking", "biomassa"], scheduled_count + realized_count, ["time_arrival", "completed_unloading", "supplier", "tonnage"]),
        _source_slice("supplier_scorecard", ["po_batubara", "vessels", "barges", "trucking", "biomassa", "coa_reconciliation"], len(supplier_scorecard), ["volume", "timeliness", "coa_delta", "dispute_count", "risk_status"]),
        _source_slice("coa_quality_disputes", ["coa_reconciliation"], len(coa_items), ["status", "umpire_status", "delta_loading_internal", "completed_unloading", "ds_mt"]),
    ]

    report = {
        "period": period or "all",
        "supplier": supplier or "all",
        "date_from": date_from,
        "date_to": date_to,
        "filter_scope": {
            "period": period or "all",
            "supplier": supplier or "all",
            "date_from": date_from,
            "date_to": date_to,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": (user or {}).get("username") or (user or {}).get("email") or (user or {}).get("id"),
        "source_counts": source_counts,
        "source_slices": source_slices,
        "data_health": {
            "empty": total_source_records == 0,
            "total_source_records": total_source_records,
            "partial_warnings": partial_warnings,
            "message": "Data tersedia untuk filter ini." if total_source_records else "Belum ada data untuk filter laporan ini.",
        },
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
            "at_risk_count": at_risk_count,
            "at_risk_tonnage": at_risk_tonnage,
            "realized_by_mode": realized_by_mode,
        },
        "quality": {
            "avg_gcv": (sum(gcv_values) / len(gcv_values)) if gcv_values else None,
            "sample_count": sum(item["count"] for item in realized_by_mode),
            "coa_records": len(coa_items),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "avg_coa_delta": (sum(deltas) / len(deltas)) if deltas else None,
            "max_coa_delta": max(deltas) if deltas else None,
        },
        "supplier_performance": supplier_performance,
        "supplier_scorecard": supplier_scorecard,
        "potential_loss": {
            "record_count": len(coa_items),
            "potential_loss_mt": potential_loss_mt,
            "potential_loss_kcal_mt": potential_loss_mt,
            "impacted_tonnage": impacted_tonnage,
            "price_per_kcal_per_ton": price_per_kcal_per_ton or None,
            "estimated_loss_value": estimated_loss_value,
            "critical_count": critical_count,
            "warning_count": warning_count,
        },
        "disputes": {
            "critical_count": critical_count,
            "warning_count": warning_count,
            "stale_count": len(stale_aging),
            "oldest_active_aging_days": max([value for value in active_aging if value is not None], default=None),
            "umpire": {
                "proposed": proposed_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
                "active": proposed_count + in_progress_count,
            },
        },
    }
    report["executive_summary"] = _management_summary(report)
    return report


@router.get("/management")
async def get_management_report(
    period: Optional[str] = Query("all"),
    supplier: Optional[str] = Query("all"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Executive report summary for stock, arrivals, suppliers, loss, and disputes."""
    return await build_management_report(period, supplier, date_from, date_to, user)
