from datetime import date, datetime, timedelta
from typing import Any, Optional

from dateutil.relativedelta import relativedelta

from services.query_filters import (
    abs_delta,
    merge_match,
    mode_match,
    risk_status,
    safe_float,
    stock_status,
    supplier_match,
)
from utils.database import db


REALIZED_SOURCES = [
    ("vessel", db.vessels, ["completed_unloading", "time_arrival"], "suppliers", "ds_mt"),
    ("barge", db.barges, ["completed_unloading", "ta", "time_arrival"], "suppliers", "ds_mt"),
    ("trucking", db.trucking, ["completed_unloading", "ta", "time_arrival"], "suppliers", "ds_mt"),
    ("biomassa", db.biomassa, ["completed_unloading", "time_arrival"], "suppliers", "jembatan_timbang_mt"),
]

FORECAST_HORIZONS = [7, 14, 30]


def _date_prefix(value: Any) -> str:
    return str(value or "")[:10]


def _parse_date(value: Any) -> Optional[date]:
    prefix = _date_prefix(value)
    if not prefix:
        return None
    try:
        return date.fromisoformat(prefix)
    except ValueError:
        return None


def _format_date(value: date) -> str:
    return value.isoformat()


def _date_range_match(field: str, start: Optional[date], end_exclusive: Optional[date]) -> dict:
    condition = {}
    if start:
        condition["$gte"] = _format_date(start)
    if end_exclusive:
        condition["$lt"] = _format_date(end_exclusive)
    return {field: condition} if condition else {}


def _multi_date_match(fields: list[str], start: Optional[date], end_exclusive: Optional[date]) -> dict:
    if not fields:
        return {}
    matches = [_date_range_match(field, start, end_exclusive) for field in fields]
    matches = [match for match in matches if match]
    if not matches:
        return {}
    if len(matches) == 1:
        return matches[0]
    return {"$or": matches}


async def _sum_collection(collection, match: dict, field: str) -> float:
    result = await collection.aggregate([
        {"$match": match},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": [f"${field}", 0]}}}},
    ]).to_list(1)
    return float(result[0]["total"]) if result else 0.0


async def _latest_date_from_sources() -> Optional[date]:
    sources = [
        (db.smartstock, "date"),
        (db.sumberpemakaian, "date"),
        (db.po_batubara, "time_arrival"),
        (db.vessels, "completed_unloading"),
        (db.vessels, "time_arrival"),
        (db.barges, "completed_unloading"),
        (db.barges, "ta"),
        (db.trucking, "completed_unloading"),
        (db.trucking, "ta"),
        (db.biomassa, "completed_unloading"),
        (db.biomassa, "time_arrival"),
        (db.coa_reconciliation, "completed_unloading"),
    ]
    latest: Optional[date] = None
    for collection, field in sources:
        doc = await collection.find_one(
            {field: {"$nin": [None, ""]}},
            {"_id": 0, field: 1},
            sort=[(field, -1)],
        )
        parsed = _parse_date(doc.get(field)) if doc else None
        if parsed and (latest is None or parsed > latest):
            latest = parsed
    return latest


async def _resolve_windows(
    period: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> dict:
    selected_period = period or "all"
    if date_from or date_to:
        current_start = _parse_date(date_from) if date_from else None
        current_end_inclusive = _parse_date(date_to) if date_to else current_start
        if current_start is None and current_end_inclusive is not None:
            current_start = current_end_inclusive
        if current_start is None:
            latest = await _latest_date_from_sources()
            current_start = latest or date.today()
            current_end_inclusive = current_start
        if current_end_inclusive is None:
            current_end_inclusive = current_start
        if current_end_inclusive < current_start:
            current_start, current_end_inclusive = current_end_inclusive, current_start
        days = max((current_end_inclusive - current_start).days + 1, 1)
        current_end = current_end_inclusive + timedelta(days=1)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=days)
        return {
            "mode": "date_range",
            "current": {"start": current_start, "end": current_end, "label": f"{current_start.isoformat()} s.d. {current_end_inclusive.isoformat()}"},
            "previous": {"start": previous_start, "end": previous_end, "label": f"{previous_start.isoformat()} s.d. {(previous_end - timedelta(days=1)).isoformat()}"},
            "days": days,
        }

    if len(selected_period) == 7 and selected_period[4] == "-":
        year = int(selected_period[:4])
        month = int(selected_period[5:7])
        current_start = date(year, month, 1)
        current_end = current_start + relativedelta(months=1)
        previous_start = current_start - relativedelta(months=1)
        return {
            "mode": "month",
            "current": {"start": current_start, "end": current_end, "label": selected_period},
            "previous": {"start": previous_start, "end": current_start, "label": previous_start.strftime("%Y-%m")},
            "days": max((current_end - current_start).days, 1),
        }

    if len(selected_period) == 4 and selected_period.isdigit():
        year = int(selected_period)
        current_start = date(year, 1, 1)
        current_end = date(year + 1, 1, 1)
        previous_start = date(year - 1, 1, 1)
        return {
            "mode": "year",
            "current": {"start": current_start, "end": current_end, "label": selected_period},
            "previous": {"start": previous_start, "end": current_start, "label": str(year - 1)},
            "days": max((current_end - current_start).days, 1),
        }

    latest = await _latest_date_from_sources()
    anchor = latest or date.today()
    current_end = anchor + timedelta(days=1)
    current_start = current_end - timedelta(days=30)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=30)
    return {
        "mode": "latest_30_days",
        "current": {"start": current_start, "end": current_end, "label": "30 hari terakhir"},
        "previous": {"start": previous_start, "end": previous_end, "label": "30 hari sebelumnya"},
        "days": 30,
    }


def _direction(delta: Optional[float], tolerance: float = 0.01) -> str:
    if delta is None:
        return "unknown"
    if delta > tolerance:
        return "up"
    if delta < -tolerance:
        return "down"
    return "flat"


def _direction_label(direction: str) -> str:
    return {
        "up": "Naik",
        "down": "Turun",
        "flat": "Stabil",
        "unknown": "Belum cukup data",
    }.get(direction, "Belum cukup data")


def _metric(
    *,
    current: Optional[float],
    previous: Optional[float],
    label: str,
    unit: str = "",
    higher_is_better: bool = True,
    digits: int = 2,
) -> dict:
    current_value = float(current or 0)
    previous_value = float(previous or 0)
    delta = current_value - previous_value
    delta_percent = (delta / previous_value * 100) if previous_value else None
    direction = _direction(delta)
    if direction == "unknown" or (abs(delta) < 0.01 and previous_value == 0 and current_value == 0):
        status = "unknown" if previous_value == 0 and current_value == 0 else "stable"
    elif direction == "flat":
        status = "stable"
    else:
        improved = (delta > 0 and higher_is_better) or (delta < 0 and not higher_is_better)
        status = "improving" if improved else "worsening"
    return {
        "label": label,
        "unit": unit,
        "current": round(current_value, digits),
        "previous": round(previous_value, digits),
        "delta": round(delta, digits),
        "delta_percent": round(delta_percent, 2) if delta_percent is not None else None,
        "direction": direction,
        "direction_label": _direction_label(direction),
        "status": status,
    }


async def _stock_snapshot(window: dict) -> dict:
    start = window["start"]
    end = window["end"]
    stock_match = _date_range_match("date", start, end)
    usage_match = _date_range_match("date", start, end)
    total_penerimaan = await _sum_collection(db.smartstock, stock_match, "total_penerimaan")
    total_pemakaian = await _sum_collection(db.sumberpemakaian, usage_match, "total_pemakaian")
    latest_stock = await db.smartstock.find_one(stock_match, {"_id": 0}, sort=[("date", -1)])
    latest_usage = await db.sumberpemakaian.find_one(usage_match, {"_id": 0}, sort=[("date", -1)])
    current_stock = latest_stock.get("stock_akhir") if latest_stock and latest_stock.get("stock_akhir") is not None else None
    if current_stock is None:
        current_stock = (
            safe_float(latest_stock.get("stock_awal")) if latest_stock else 0
        ) + (
            safe_float(latest_stock.get("total_penerimaan")) if latest_stock else 0
        ) - (
            safe_float(latest_usage.get("total_pemakaian")) if latest_usage else 0
        )
    days = max((end - start).days, 1)
    avg_daily_usage = total_pemakaian / days if total_pemakaian > 0 else 0
    days_of_supply = int(float(current_stock or 0) / avg_daily_usage) if avg_daily_usage > 0 else None
    return {
        "current_stock": float(current_stock or 0),
        "total_penerimaan": total_penerimaan,
        "total_pemakaian": total_pemakaian,
        "avg_daily_usage": avg_daily_usage,
        "days_of_supply": days_of_supply,
        "stock_records": await db.smartstock.count_documents(stock_match),
        "usage_records": await db.sumberpemakaian.count_documents(usage_match),
        "latest_stock_date": latest_stock.get("date") if latest_stock else None,
        "latest_usage_date": latest_usage.get("date") if latest_usage else None,
    }


async def _arrival_snapshot(window: dict, supplier: Optional[str], mode: Optional[str]) -> dict:
    start = window["start"]
    end = window["end"]
    po_match = merge_match(
        _date_range_match("time_arrival", start, end),
        supplier_match("supplier_name", supplier),
        mode_match("moda", mode),
    )
    scheduled_count = await db.po_batubara.count_documents(po_match)
    scheduled_tonnage = await _sum_collection(db.po_batubara, po_match, "tonase_po")
    today_prefix = date.today().isoformat()
    at_risk_match = merge_match(po_match, {"time_arrival": {"$lt": today_prefix}})
    at_risk_count = await db.po_batubara.count_documents(at_risk_match)

    realized_count = 0
    realized_tonnage = 0.0
    realized_by_mode = []
    selected_mode = (mode or "all").lower()
    for source_mode, collection, date_fields, supplier_field, tonnage_field in REALIZED_SOURCES:
        if selected_mode not in {"all", source_mode}:
            continue
        match = merge_match(
            _multi_date_match(date_fields, start, end),
            supplier_match(supplier_field, supplier),
        )
        count = await collection.count_documents(match)
        tonnage = await _sum_collection(collection, match, tonnage_field)
        realized_count += count
        realized_tonnage += tonnage
        realized_by_mode.append({"mode": source_mode, "count": count, "tonnage": tonnage})

    return {
        "scheduled_count": scheduled_count,
        "scheduled_tonnage": scheduled_tonnage,
        "realized_count": realized_count,
        "realized_tonnage": realized_tonnage,
        "at_risk_count": at_risk_count,
        "fulfillment_rate": (realized_count / scheduled_count * 100) if scheduled_count else None,
        "tonnage_fulfillment_rate": (realized_tonnage / scheduled_tonnage * 100) if scheduled_tonnage else None,
        "realized_by_mode": realized_by_mode,
    }


async def _quality_snapshot(window: dict, supplier: Optional[str]) -> dict:
    match = merge_match(
        _date_range_match("completed_unloading", window["start"], window["end"]),
        supplier_match("suppliers", supplier),
    )
    rows = await db.coa_reconciliation.find(
        match,
        {
            "_id": 0,
            "status": 1,
            "umpire_status": 1,
            "completed_unloading": 1,
            "suppliers": 1,
            "shipment": 1,
            "ds_mt": 1,
            "delta_loading_internal": 1,
            "delta_unloading_internal": 1,
            "delta_loading_unloading": 1,
        },
    ).to_list(10000)
    deltas = [delta for delta in (abs_delta(item) for item in rows) if delta is not None]
    active_disputes = sum(1 for item in rows if item.get("umpire_status") in {"proposed", "in_progress"})
    stale_disputes = 0
    for item in rows:
        if item.get("umpire_status") not in {"proposed", "in_progress"}:
            continue
        parsed = _parse_date(item.get("completed_unloading"))
        if parsed and (date.today() - parsed).days >= 7:
            stale_disputes += 1
    return {
        "coa_records": len(rows),
        "critical_count": sum(1 for item in rows if str(item.get("status", "")).lower() in {"critical", "kritis"}),
        "warning_count": sum(1 for item in rows if str(item.get("status", "")).lower() == "warning"),
        "avg_coa_delta": (sum(deltas) / len(deltas)) if deltas else None,
        "max_coa_delta": max(deltas) if deltas else None,
        "active_disputes": active_disputes,
        "stale_disputes": stale_disputes,
    }


def _supplier_entry(rows: dict[str, dict], supplier_name: Any) -> dict:
    name = str(supplier_name or "Tanpa Supplier").strip() or "Tanpa Supplier"
    if name not in rows:
        rows[name] = {
            "supplier": name,
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
            "_delta_sum": 0.0,
            "_delta_count": 0,
        }
    return rows[name]


async def _supplier_snapshot(window: dict, supplier: Optional[str], mode: Optional[str]) -> dict[str, dict]:
    start = window["start"]
    end = window["end"]
    rows: dict[str, dict] = {}
    today_prefix = date.today().isoformat()
    po_match = merge_match(
        _date_range_match("time_arrival", start, end),
        supplier_match("supplier_name", supplier),
        mode_match("moda", mode),
    )
    po_rows = await db.po_batubara.find(
        po_match,
        {"_id": 0, "supplier_name": 1, "time_arrival": 1, "tonase_po": 1},
    ).to_list(10000)
    for item in po_rows:
        row = _supplier_entry(rows, item.get("supplier_name"))
        row["scheduled_count"] += 1
        row["scheduled_tonnage"] += safe_float(item.get("tonase_po"))
        if str(item.get("time_arrival") or "") < today_prefix:
            row["at_risk_count"] += 1

    selected_mode = (mode or "all").lower()
    for source_mode, collection, date_fields, supplier_field, tonnage_field in REALIZED_SOURCES:
        if selected_mode not in {"all", source_mode}:
            continue
        match = merge_match(
            _multi_date_match(date_fields, start, end),
            supplier_match(supplier_field, supplier),
        )
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
            row = _supplier_entry(rows, item.get("_id"))
            row["realized_count"] += int(item.get("record_count") or 0)
            row["realized_tonnage"] += float(item.get("realized_tonnage") or 0)

    coa_match = merge_match(
        _date_range_match("completed_unloading", start, end),
        supplier_match("suppliers", supplier),
    )
    coa_rows = await db.coa_reconciliation.find(
        coa_match,
        {
            "_id": 0,
            "suppliers": 1,
            "status": 1,
            "umpire_status": 1,
            "delta_loading_internal": 1,
            "delta_unloading_internal": 1,
            "delta_loading_unloading": 1,
        },
    ).to_list(10000)
    for item in coa_rows:
        row = _supplier_entry(rows, item.get("suppliers"))
        row["quality_records"] += 1
        status = str(item.get("status", "")).lower()
        umpire_status = str(item.get("umpire_status", "")).lower()
        if status in {"critical", "kritis"}:
            row["critical_count"] += 1
        elif status == "warning":
            row["warning_count"] += 1
        if umpire_status in {"proposed", "in_progress"}:
            row["active_disputes"] += 1
        delta = abs_delta(item)
        if delta is not None:
            row["_delta_sum"] += delta
            row["_delta_count"] += 1

    for row in rows.values():
        if row["_delta_count"]:
            row["avg_coa_delta"] = row["_delta_sum"] / row["_delta_count"]
    return rows


def _risk_score(row: dict) -> float:
    timeliness_rate = None
    if row.get("scheduled_count"):
        timeliness_rate = max(row["scheduled_count"] - row.get("at_risk_count", 0), 0) / row["scheduled_count"] * 100
    risk_score = (
        row.get("critical_count", 0) * 35
        + row.get("warning_count", 0) * 15
        + row.get("active_disputes", 0) * 25
        + row.get("at_risk_count", 0) * 10
        + min((row.get("avg_coa_delta") or 0) / 4, 25)
    )
    if timeliness_rate is not None:
        risk_score += max((100 - timeliness_rate) / 4, 0)
    return min(max(risk_score, 0), 100)


def _risk_label(status: str) -> str:
    return {"high": "Risiko tinggi", "medium": "Perlu dipantau", "low": "Relatif stabil"}.get(status, "Belum ada sinyal")


def _supplier_trends(current: dict[str, dict], previous: dict[str, dict]) -> list[dict]:
    suppliers = set(current.keys()) | set(previous.keys())
    rows = []
    for supplier in suppliers:
        cur = current.get(supplier, {"supplier": supplier})
        prev = previous.get(supplier, {"supplier": supplier})
        timeliness_current = None
        if cur.get("scheduled_count"):
            timeliness_current = max(cur["scheduled_count"] - cur.get("at_risk_count", 0), 0) / cur["scheduled_count"] * 100
        timeliness_previous = None
        if prev.get("scheduled_count"):
            timeliness_previous = max(prev["scheduled_count"] - prev.get("at_risk_count", 0), 0) / prev["scheduled_count"] * 100
        risk_score = _risk_score(cur)
        risk_level = risk_status(risk_score)
        rows.append({
            "supplier": supplier,
            "risk_score": round(risk_score, 1),
            "risk_status": risk_level,
            "risk_label": _risk_label(risk_level),
            "volume": _metric(
                current=cur.get("realized_tonnage"),
                previous=prev.get("realized_tonnage"),
                label="Volume realisasi",
                unit="MT",
                higher_is_better=True,
            ),
            "timeliness": _metric(
                current=timeliness_current,
                previous=timeliness_previous,
                label="Ketepatan jadwal",
                unit="%",
                higher_is_better=True,
            ),
            "quality_delta": _metric(
                current=cur.get("avg_coa_delta"),
                previous=prev.get("avg_coa_delta"),
                label="Rata-rata delta COA",
                unit="kcal/kg",
                higher_is_better=False,
            ),
            "disputes": _metric(
                current=cur.get("active_disputes"),
                previous=prev.get("active_disputes"),
                label="Dispute aktif",
                unit="record",
                higher_is_better=False,
                digits=0,
            ),
            "current": {
                "scheduled_count": cur.get("scheduled_count", 0),
                "scheduled_tonnage": cur.get("scheduled_tonnage", 0),
                "realized_count": cur.get("realized_count", 0),
                "realized_tonnage": cur.get("realized_tonnage", 0),
                "avg_coa_delta": cur.get("avg_coa_delta"),
                "active_disputes": cur.get("active_disputes", 0),
            },
            "previous": {
                "scheduled_count": prev.get("scheduled_count", 0),
                "scheduled_tonnage": prev.get("scheduled_tonnage", 0),
                "realized_count": prev.get("realized_count", 0),
                "realized_tonnage": prev.get("realized_tonnage", 0),
                "avg_coa_delta": prev.get("avg_coa_delta"),
                "active_disputes": prev.get("active_disputes", 0),
            },
        })
    rows.sort(key=lambda item: (item["risk_score"], item["current"]["realized_tonnage"]), reverse=True)
    return rows[:12]


async def _stock_forecast(current_stock: float, avg_daily_usage: float, supplier: Optional[str], mode: Optional[str]) -> dict:
    today = date.today()
    caveats = []
    confidence = "high"
    if avg_daily_usage <= 0:
        recent_start = today - timedelta(days=30)
        recent_usage = await _sum_collection(
            db.sumberpemakaian,
            _date_range_match("date", recent_start, today + timedelta(days=1)),
            "total_pemakaian",
        )
        avg_daily_usage = recent_usage / 30 if recent_usage > 0 else 0
        if avg_daily_usage <= 0:
            confidence = "low"
            caveats.append("Forecast stok belum bisa dihitung akurat karena data pemakaian belum tersedia.")
    if avg_daily_usage <= 0:
        return {
            "current_stock": round(float(current_stock or 0), 2),
            "avg_daily_usage": 0,
            "expected_arrivals_30d": 0,
            "projected_coverage_days": None,
            "confidence": confidence,
            "caveats": caveats,
            "assumptions": [
                "Burn rate memakai rata-rata pemakaian pada filter aktif; fallback 30 hari terakhir bila filter kosong.",
                "Expected arrivals memakai jadwal PO dari tanggal hari ini sampai horizon forecast.",
            ],
            "horizons": [],
        }

    horizons = []
    expected_30d = 0.0
    for horizon in FORECAST_HORIZONS:
        end_date = today + timedelta(days=horizon + 1)
        po_match = merge_match(
            _date_range_match("time_arrival", today, end_date),
            supplier_match("supplier_name", supplier),
            mode_match("moda", mode),
        )
        expected_arrivals = await _sum_collection(db.po_batubara, po_match, "tonase_po")
        if horizon == 30:
            expected_30d = expected_arrivals
        projected_stock = float(current_stock or 0) + expected_arrivals - (avg_daily_usage * horizon)
        projected_coverage = int(projected_stock / avg_daily_usage) if projected_stock > 0 else 0
        horizons.append({
            "days": horizon,
            "expected_arrivals": round(expected_arrivals, 2),
            "projected_stock": round(projected_stock, 2),
            "projected_coverage_days": projected_coverage,
            "status": stock_status(projected_coverage),
        })

    projected_coverage_days = int(float(current_stock or 0) / avg_daily_usage) if current_stock > 0 else 0
    if expected_30d == 0:
        confidence = "medium" if confidence == "high" else confidence
        caveats.append("Belum ada jadwal kedatangan mendatang pada horizon 30 hari.")
    return {
        "current_stock": round(float(current_stock or 0), 2),
        "avg_daily_usage": round(avg_daily_usage, 2),
        "expected_arrivals_30d": round(expected_30d, 2),
        "projected_coverage_days": projected_coverage_days,
        "confidence": confidence,
        "caveats": caveats,
        "assumptions": [
            "Burn rate memakai rata-rata pemakaian pada filter aktif; fallback 30 hari terakhir bila filter kosong.",
            "Expected arrivals memakai jadwal PO dari tanggal hari ini sampai horizon forecast.",
        ],
        "horizons": horizons,
    }


def _source_counts(current_stock: dict, previous_stock: dict, current_arrivals: dict, previous_arrivals: dict, current_quality: dict, previous_quality: dict) -> dict:
    return {
        "current": {
            "stock_records": current_stock.get("stock_records", 0),
            "usage_records": current_stock.get("usage_records", 0),
            "po_batubara": current_arrivals.get("scheduled_count", 0),
            "arrivals": current_arrivals.get("realized_count", 0),
            "coa_reconciliation": current_quality.get("coa_records", 0),
        },
        "previous": {
            "stock_records": previous_stock.get("stock_records", 0),
            "usage_records": previous_stock.get("usage_records", 0),
            "po_batubara": previous_arrivals.get("scheduled_count", 0),
            "arrivals": previous_arrivals.get("realized_count", 0),
            "coa_reconciliation": previous_quality.get("coa_records", 0),
        },
    }


def _confidence_and_caveats(source_counts: dict, forecast: dict) -> tuple[str, bool, list[str]]:
    current_total = sum(int(value or 0) for value in source_counts["current"].values())
    previous_total = sum(int(value or 0) for value in source_counts["previous"].values())
    caveats = []
    sparse = False
    confidence = "high"
    if current_total == 0:
        sparse = True
        confidence = "low"
        caveats.append("Belum ada data periode aktif untuk menghitung tren.")
    if previous_total < 3:
        sparse = True
        confidence = "low" if current_total < 3 else "medium"
        caveats.append("Data historis periode pembanding belum cukup; tren ditampilkan sebagai indikasi awal.")
    if source_counts["current"].get("usage_records", 0) == 0:
        sparse = True
        confidence = "low"
        caveats.append("Data pemakaian stock pada filter ini belum tersedia sehingga forecast memakai fallback atau ditandai rendah.")
    for caveat in forecast.get("caveats", []):
        if caveat not in caveats:
            caveats.append(caveat)
    if not caveats:
        caveats.append("Data pembanding cukup untuk membaca tren operasional.")
    return confidence, sparse, caveats


async def build_trend_analytics(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    mode: Optional[str] = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """Build deterministic current-vs-previous trend and stock forecast payload."""
    selected_supplier = supplier or "all"
    selected_mode = mode or "all"
    windows = await _resolve_windows(period, date_from, date_to)
    current_window = windows["current"]
    previous_window = windows["previous"]

    current_stock = await _stock_snapshot(current_window)
    previous_stock = await _stock_snapshot(previous_window)
    current_arrivals = await _arrival_snapshot(current_window, selected_supplier, selected_mode)
    previous_arrivals = await _arrival_snapshot(previous_window, selected_supplier, selected_mode)
    current_quality = await _quality_snapshot(current_window, selected_supplier)
    previous_quality = await _quality_snapshot(previous_window, selected_supplier)
    current_suppliers = await _supplier_snapshot(current_window, selected_supplier, selected_mode)
    previous_suppliers = await _supplier_snapshot(previous_window, selected_supplier, selected_mode)

    forecast = await _stock_forecast(
        current_stock=current_stock.get("current_stock", 0),
        avg_daily_usage=current_stock.get("avg_daily_usage", 0),
        supplier=selected_supplier,
        mode=selected_mode,
    )
    source_counts = _source_counts(current_stock, previous_stock, current_arrivals, previous_arrivals, current_quality, previous_quality)
    confidence, sparse_data, caveats = _confidence_and_caveats(source_counts, forecast)

    supplier_trends = _supplier_trends(current_suppliers, previous_suppliers)
    avg_supplier_risk = (
        sum(item["risk_score"] for item in supplier_trends) / len(supplier_trends)
        if supplier_trends else 0
    )
    previous_avg_supplier_risk = (
        sum(_risk_score(item) for item in previous_suppliers.values()) / len(previous_suppliers)
        if previous_suppliers else 0
    )

    metrics = {
        "stock": _metric(
            current=current_stock.get("current_stock"),
            previous=previous_stock.get("current_stock"),
            label="Stok akhir periode",
            unit="MT",
            higher_is_better=True,
        ),
        "stock_coverage": _metric(
            current=current_stock.get("days_of_supply"),
            previous=previous_stock.get("days_of_supply"),
            label="Coverage stok",
            unit="hari",
            higher_is_better=True,
            digits=0,
        ),
        "arrivals": _metric(
            current=current_arrivals.get("tonnage_fulfillment_rate"),
            previous=previous_arrivals.get("tonnage_fulfillment_rate"),
            label="Fulfillment kedatangan",
            unit="%",
            higher_is_better=True,
        ),
        "supplier_performance": _metric(
            current=avg_supplier_risk,
            previous=previous_avg_supplier_risk,
            label="Rata-rata risiko supplier",
            unit="score",
            higher_is_better=False,
        ),
        "quality_delta": _metric(
            current=current_quality.get("avg_coa_delta"),
            previous=previous_quality.get("avg_coa_delta"),
            label="Rata-rata delta COA",
            unit="kcal/kg",
            higher_is_better=False,
        ),
        "disputes": _metric(
            current=current_quality.get("active_disputes"),
            previous=previous_quality.get("active_disputes"),
            label="Dispute aktif",
            unit="record",
            higher_is_better=False,
            digits=0,
        ),
    }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "filter_scope": {
            "period": period or "all",
            "supplier": selected_supplier,
            "mode": selected_mode,
            "date_from": date_from,
            "date_to": date_to,
        },
        "period_comparison": {
            "mode": windows["mode"],
            "current": {
                "start": current_window["start"].isoformat(),
                "end": (current_window["end"] - timedelta(days=1)).isoformat(),
                "label": current_window["label"],
            },
            "previous": {
                "start": previous_window["start"].isoformat(),
                "end": (previous_window["end"] - timedelta(days=1)).isoformat(),
                "label": previous_window["label"],
            },
        },
        "confidence": confidence,
        "sparse_data": sparse_data,
        "caveats": caveats,
        "source_counts": source_counts,
        "metrics": metrics,
        "stock_forecast": forecast,
        "supplier_trends": supplier_trends,
        "snapshots": {
            "current": {
                "stock": current_stock,
                "arrivals": current_arrivals,
                "quality": current_quality,
            },
            "previous": {
                "stock": previous_stock,
                "arrivals": previous_arrivals,
                "quality": previous_quality,
            },
        },
    }


async def build_dashboard_trends(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    mode: Optional[str] = "all",
) -> dict:
    return await build_trend_analytics(period=period, supplier=supplier, mode=mode)


async def build_management_trends(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    return await build_trend_analytics(
        period=period,
        supplier=supplier,
        mode="all",
        date_from=date_from,
        date_to=date_to,
    )

