import re
from datetime import date
from typing import Optional


def period_bounds(period: Optional[str]):
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


def period_match(field: str, period: Optional[str]) -> dict:
    bounds = period_bounds(period)
    if not bounds:
        return {}
    start, end = bounds
    return {field: {"$gte": start, "$lt": end}}


def date_match(field: str, period: Optional[str], date_from: Optional[str], date_to: Optional[str]) -> dict:
    if date_from or date_to:
        condition = {}
        if date_from:
            condition["$gte"] = date_from
        if date_to:
            condition["$lte"] = date_to
        return {field: condition}
    return period_match(field, period)


def supplier_match(field: str, supplier: Optional[str]) -> dict:
    if not supplier or supplier == "all":
        return {}
    escaped = re.escape(str(supplier).strip())
    return {field: {"$regex": f"^{escaped}$", "$options": "i"}}


def merge_match(*parts: dict) -> dict:
    active = [part for part in parts if part]
    if not active:
        return {}
    if len(active) == 1:
        return active[0]
    return {"$and": active}


def and_match(*parts: dict) -> dict:
    return merge_match(*parts)


def normalize_mode(mode: Optional[str]) -> str:
    if not mode:
        return "all"
    value = str(mode).strip().lower()
    aliases = {
        "kapal": "vessel",
        "vessel": "vessel",
        "barge": "barge",
        "tongkang": "barge",
        "truck": "trucking",
        "truk": "trucking",
        "trucking": "trucking",
        "biomass": "biomassa",
        "biomassa": "biomassa",
    }
    return aliases.get(value, "all")


def mode_match(field: str, mode: Optional[str]) -> dict:
    normalized = normalize_mode(mode)
    if normalized == "all":
        return {}
    patterns = {
        "vessel": r"(vessel|kapal)",
        "barge": r"(barge|tongkang)",
        "trucking": r"(truck|trucking|truk)",
        "biomassa": r"(biomass|biomassa)",
    }
    return {field: {"$regex": patterns[normalized], "$options": "i"}}


def source_enabled(selected_mode: str, source_mode: str) -> bool:
    return selected_mode == "all" or selected_mode == source_mode


def supplier_name(value: Optional[str]) -> str:
    cleaned = str(value or "").strip()
    return cleaned if cleaned else "Unknown"


def risk_status(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def stock_status(days_of_supply: Optional[int]) -> str:
    if days_of_supply is None:
        return "unknown"
    if days_of_supply < 7:
        return "critical"
    if days_of_supply < 14:
        return "warning"
    if days_of_supply < 30:
        return "watch"
    return "healthy"


def stock_risk(days_of_supply: Optional[int]) -> dict:
    if days_of_supply is None:
        return {
            "status": "unknown",
            "label": "Belum ada pemakaian",
            "severity": 0,
            "reorder_risk": "unknown",
            "reorder_threshold_days": 14,
        }
    if days_of_supply < 7:
        return {
            "status": "critical",
            "label": "Kritis",
            "severity": 3,
            "reorder_risk": "high",
            "reorder_threshold_days": 14,
        }
    if days_of_supply < 14:
        return {
            "status": "warning",
            "label": "Perlu reorder",
            "severity": 2,
            "reorder_risk": "medium",
            "reorder_threshold_days": 14,
        }
    if days_of_supply < 30:
        return {
            "status": "watch",
            "label": "Dipantau",
            "severity": 1,
            "reorder_risk": "low",
            "reorder_threshold_days": 14,
        }
    return {
        "status": "healthy",
        "label": "Aman",
        "severity": 0,
        "reorder_risk": "low",
        "reorder_threshold_days": 14,
    }


def safe_float(value) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def abs_delta(item: dict) -> Optional[float]:
    for field in ["delta_loading_internal", "delta_unloading_internal", "delta_loading_unloading"]:
        if item.get(field) is not None and item.get(field) != "":
            return abs(safe_float(item.get(field)))
    return None


def aging_days(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return max((date.today() - date.fromisoformat(str(value)[:10])).days, 0)
    except ValueError:
        return None


def source_slice(name: str, collections: list[str], record_count: int, fields: list[str]) -> dict:
    return {
        "name": name,
        "collections": collections,
        "record_count": record_count,
        "fields": fields,
    }


async def sum_collection(collection, match: dict, field: str) -> float:
    result = await collection.aggregate([
        {"$match": match},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": [f"${field}", 0]}}}},
    ]).to_list(1)
    return float(result[0]["total"]) if result else 0.0


async def avg_collection(collection, match: dict, field: str) -> Optional[float]:
    result = await collection.aggregate([
        {"$match": merge_match(match, {field: {"$ne": None}})},
        {"$group": {"_id": None, "avg": {"$avg": f"${field}"}}},
    ]).to_list(1)
    return float(result[0]["avg"]) if result else None


async def distinct_strings(collection, field: str, match: Optional[dict] = None) -> list:
    values = await collection.distinct(field, match or {})
    return sorted({str(value).strip() for value in values if str(value or "").strip()})
