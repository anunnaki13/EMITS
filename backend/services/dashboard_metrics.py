from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta

from models import DashboardStats
from services.data_quality import build_data_quality_caveat
from services.trend_analytics import build_dashboard_trends
from services.query_filters import (
    aging_days,
    distinct_strings,
    merge_match,
    mode_match,
    normalize_mode,
    period_any_match,
    period_match,
    risk_status,
    source_enabled,
    stock_risk,
    sum_collection,
    supplier_match,
    supplier_name as normalize_supplier_name,
)
from utils.database import db

risk_level = risk_status

async def build_dashboard_operational(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    mode: Optional[str] = "all",
    user: Optional[dict] = None,
):
    """Operational dashboard data focused on stock, arrivals, supplier risk, and coal disputes."""
    selected_period = period or "all"
    selected_supplier = supplier or "all"
    selected_mode = normalize_mode(mode)

    stock_match = period_match("date", selected_period)
    total_penerimaan = await sum_collection(db.smartstock, stock_match, "total_penerimaan")
    total_pemakaian = await sum_collection(db.sumberpemakaian, stock_match, "total_pemakaian")
    latest_stock = await db.smartstock.find_one({}, {"_id": 0}, sort=[("date", -1)])
    latest_usage = await db.sumberpemakaian.find_one({}, {"_id": 0}, sort=[("date", -1)])
    current_stock = latest_stock.get("stock_akhir") if latest_stock and latest_stock.get("stock_akhir") is not None else None
    if current_stock is None:
        latest_stock_awal = latest_stock.get("stock_awal", 0) if latest_stock else 0
        latest_penerimaan = latest_stock.get("total_penerimaan", 0) if latest_stock else 0
        latest_pemakaian = latest_usage.get("total_pemakaian", 0) if latest_usage else 0
        current_stock = latest_stock_awal + latest_penerimaan - latest_pemakaian
    avg_daily_usage = total_pemakaian / 30 if total_pemakaian > 0 else 0
    days_of_supply = int(current_stock / avg_daily_usage) if avg_daily_usage > 0 else None
    stock_risk_payload = stock_risk(days_of_supply)

    po_period_match = period_match("time_arrival", selected_period)
    po_supplier_match = supplier_match("supplier_name", selected_supplier)
    po_mode_match = mode_match("moda", selected_mode)
    po_match = merge_match(po_period_match, po_supplier_match, po_mode_match)
    scheduled_count = await db.po_batubara.count_documents(po_match)
    scheduled_tonnage = await sum_collection(db.po_batubara, po_match, "tonase_po")
    today_prefix = date.today().isoformat()
    at_risk_match = merge_match(po_match, {"time_arrival": {"$lt": today_prefix}})
    at_risk_count = await db.po_batubara.count_documents(at_risk_match)
    at_risk_schedule = await db.po_batubara.find(
        at_risk_match,
        {"_id": 0, "no_jadwal": 1, "supplier_name": 1, "moda": 1, "time_arrival": 1, "tonase_po": 1}
    ).sort("time_arrival", 1).limit(5).to_list(5)
    upcoming_match = merge_match(po_match, {"time_arrival": {"$gte": today_prefix}})
    upcoming_schedule = await db.po_batubara.find(
        upcoming_match,
        {"_id": 0, "no_jadwal": 1, "supplier_name": 1, "moda": 1, "time_arrival": 1, "tonase_po": 1}
    ).sort("time_arrival", 1).limit(8).to_list(8)

    realized_sources = [
        ("vessel", db.vessels, ["time_arrival", "completed_unloading"], "ds_mt"),
        ("barge", db.barges, ["ta", "completed_unloading", "time_arrival"], "ds_mt"),
        ("trucking", db.trucking, ["ta", "completed_unloading", "time_arrival"], "ds_mt"),
        ("biomassa", db.biomassa, ["ta", "completed_unloading", "time_arrival"], "jembatan_timbang_mt"),
    ]
    realized_by_mode = []
    realized_count = 0
    realized_tonnage = 0.0
    realized_records_by_supplier = {}
    for source_mode, collection, date_fields, tonnage_field in realized_sources:
        if not source_enabled(selected_mode, source_mode):
            continue
        match = merge_match(
            period_any_match(date_fields, selected_period),
            supplier_match("suppliers", selected_supplier),
        )
        count = await collection.count_documents(match)
        tonnage = await sum_collection(collection, match, tonnage_field)
        realized_count += count
        realized_tonnage += tonnage
        realized_by_mode.append({"mode": source_mode, "count": count, "tonnage": tonnage})
        supplier_docs = await collection.find(match, {"_id": 0, "suppliers": 1}).to_list(10000)
        for item in supplier_docs:
            name = normalize_supplier_name(item.get("suppliers"))
            realized_records_by_supplier[name] = realized_records_by_supplier.get(name, 0) + 1

    coa_match = merge_match(
        period_match("completed_unloading", selected_period),
        supplier_match("suppliers", selected_supplier),
    )
    all_coa = await db.coa_reconciliation.find(coa_match, {"_id": 0}).to_list(10000)
    critical_count = sum(1 for item in all_coa if str(item.get("status", "")).lower() in {"critical", "kritis"})
    warning_count = sum(1 for item in all_coa if str(item.get("status", "")).lower() == "warning")
    proposed_count = sum(1 for item in all_coa if item.get("umpire_status") == "proposed")
    in_progress_count = sum(1 for item in all_coa if item.get("umpire_status") == "in_progress")
    completed_count = sum(1 for item in all_coa if item.get("umpire_status") == "completed")
    active_umpire_count = proposed_count + in_progress_count
    recent_disputes = sorted(
        [
            {
                "id": item.get("id"),
                "shipment": item.get("shipment"),
                "suppliers": item.get("suppliers"),
                "status": item.get("status"),
                "umpire_status": item.get("umpire_status"),
                "delta_loading_internal": item.get("delta_loading_internal"),
                "completed_unloading": item.get("completed_unloading"),
                "aging_days": aging_days(item.get("completed_unloading")),
            }
            for item in all_coa
            if str(item.get("status", "")).lower() in {"critical", "kritis", "warning"} or item.get("umpire_status") not in [None, "", "none"]
        ],
        key=lambda item: item.get("completed_unloading") or "",
        reverse=True,
    )[:8]

    supplier_risk_map = {}

    def risk_entry(name: Optional[str]) -> dict:
        supplier_name = normalize_supplier_name(name)
        if supplier_name not in supplier_risk_map:
            supplier_risk_map[supplier_name] = {
                "supplier": supplier_name,
                "quality_records": 0,
                "critical_count": 0,
                "warning_count": 0,
                "active_disputes": 0,
                "scheduled_count": 0,
                "at_risk_count": 0,
                "realized_count": 0,
                "avg_delta": None,
                "max_delta": None,
                "_delta_sum": 0.0,
                "_delta_count": 0,
            }
        return supplier_risk_map[supplier_name]

    def numeric(value) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return abs(float(value))
        except (TypeError, ValueError):
            return None

    scheduled_rows = await db.po_batubara.find(
        po_match,
        {"_id": 0, "supplier_name": 1, "time_arrival": 1}
    ).to_list(10000)
    for item in scheduled_rows:
        entry = risk_entry(item.get("supplier_name"))
        entry["scheduled_count"] += 1
        if str(item.get("time_arrival") or "") < today_prefix:
            entry["at_risk_count"] += 1

    for supplier_name, count in realized_records_by_supplier.items():
        risk_entry(supplier_name)["realized_count"] += count

    for item in all_coa:
        entry = risk_entry(item.get("suppliers"))
        entry["quality_records"] += 1
        status = str(item.get("status", "")).lower()
        umpire_status = str(item.get("umpire_status", "")).lower()
        if status in {"critical", "kritis"}:
            entry["critical_count"] += 1
        elif status == "warning":
            entry["warning_count"] += 1
        if umpire_status in {"proposed", "in_progress"}:
            entry["active_disputes"] += 1
        delta = None
        for delta_field in ["delta_loading_internal", "delta_unloading_internal", "delta_loading_unloading"]:
            delta = numeric(item.get(delta_field))
            if delta is not None:
                break
        if delta is not None:
            entry["_delta_sum"] += delta
            entry["_delta_count"] += 1
            entry["max_delta"] = max(entry["max_delta"] or 0, delta)

    supplier_risk = []
    for entry in supplier_risk_map.values():
        if entry["_delta_count"] > 0:
            entry["avg_delta"] = entry["_delta_sum"] / entry["_delta_count"]
        timeliness_rate = None
        if entry["scheduled_count"] > 0:
            not_late = max(entry["scheduled_count"] - entry["at_risk_count"], 0)
            timeliness_rate = not_late / entry["scheduled_count"] * 100
        avg_delta = entry["avg_delta"] or 0
        risk_score = (
            entry["critical_count"] * 35
            + entry["warning_count"] * 15
            + entry["active_disputes"] * 25
            + entry["at_risk_count"] * 10
            + min(avg_delta / 4, 25)
        )
        if timeliness_rate is not None:
            risk_score += max((100 - timeliness_rate) / 4, 0)
        risk_score = min(max(risk_score, 0), 100)
        supplier_risk.append({
            "supplier": entry["supplier"],
            "quality_records": entry["quality_records"],
            "critical_count": entry["critical_count"],
            "warning_count": entry["warning_count"],
            "active_disputes": entry["active_disputes"],
            "scheduled_count": entry["scheduled_count"],
            "at_risk_count": entry["at_risk_count"],
            "realized_count": entry["realized_count"],
            "avg_delta": entry["avg_delta"],
            "max_delta": entry["max_delta"],
            "timeliness_rate": timeliness_rate,
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level(risk_score),
        })
    supplier_risk.sort(
        key=lambda item: (
            item["risk_score"],
            item["active_disputes"],
            item["critical_count"],
            item["at_risk_count"],
        ),
        reverse=True,
    )
    supplier_risk = supplier_risk[:8]

    supplier_values = set()
    supplier_values.update(await distinct_strings(db.po_batubara, "supplier_name", po_period_match))
    supplier_values.update(await distinct_strings(db.coa_reconciliation, "suppliers", period_match("completed_unloading", selected_period)))
    for _source_mode, collection, date_fields, _tonnage_field in realized_sources:
        supplier_values.update(await distinct_strings(collection, "suppliers", period_any_match(date_fields, selected_period)))
    if selected_supplier != "all":
        supplier_values.add(selected_supplier)
    available_suppliers = [{"value": "all", "label": "Semua Supplier"}] + [
        {"value": item, "label": item} for item in sorted(supplier_values)
    ]

    available_periods = [
        {"value": "all", "label": "Semua Periode"},
        {"value": "2026", "label": "2026"},
        {"value": "2025", "label": "2025"},
        {"value": "2024", "label": "2024"},
    ]
    available_modes = [
        {"value": "all", "label": "Semua Moda"},
        {"value": "vessel", "label": "Vessel"},
        {"value": "barge", "label": "Barge/Tongkang"},
        {"value": "trucking", "label": "Trucking"},
        {"value": "biomassa", "label": "Biomassa"},
    ]
    data_quality = await build_data_quality_caveat(limit=5)
    trend_analytics = await build_dashboard_trends(
        period=selected_period,
        supplier=selected_supplier,
        mode=selected_mode,
    )

    return {
        "period": selected_period,
        "supplier": selected_supplier,
        "mode": selected_mode,
        "filters": {
            "period": selected_period,
            "supplier": selected_supplier,
            "mode": selected_mode,
        },
        "available_periods": available_periods,
        "available_suppliers": available_suppliers,
        "available_modes": available_modes,
        "stock": {
            "current_stock": current_stock,
            "latest_stock_date": latest_stock.get("date") if latest_stock else None,
            "latest_usage_date": latest_usage.get("date") if latest_usage else None,
            "total_penerimaan": total_penerimaan,
            "total_pemakaian": total_pemakaian,
            "avg_daily_usage": avg_daily_usage,
            "days_of_supply": days_of_supply,
            **stock_risk_payload,
        },
        "arrivals": {
            "scheduled_count": scheduled_count,
            "scheduled_tonnage": scheduled_tonnage,
            "realized_count": realized_count,
            "realized_tonnage": realized_tonnage,
            "count_gap": scheduled_count - realized_count,
            "tonnage_gap": scheduled_tonnage - realized_tonnage,
            "fulfillment_rate": (realized_count / scheduled_count * 100) if scheduled_count > 0 else None,
            "tonnage_fulfillment_rate": (realized_tonnage / scheduled_tonnage * 100) if scheduled_tonnage > 0 else None,
            "at_risk_count": at_risk_count,
            "at_risk_schedule": at_risk_schedule,
            "realized_by_mode": realized_by_mode,
            "upcoming_schedule": upcoming_schedule,
        },
        "disputes": {
            "total_records": len(all_coa),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "umpire": {
                "proposed": proposed_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
                "active": active_umpire_count,
            },
            "recent": recent_disputes,
        },
        "supplier_risk": supplier_risk,
        "data_quality": data_quality,
        "trend_analytics": trend_analytics,
    }

async def build_dashboard_stats(user: Optional[dict] = None):
    total_vessel = await db.vessels.count_documents({})
    total_barge = await db.barges.count_documents({})
    total_trucking = await db.trucking.count_documents({})
    total_biomassa = await db.biomassa.count_documents({})
    
    # Calculate total tonase batubara from vessels and barges
    vessel_pipeline = [{"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}]
    barge_pipeline = [{"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}]
    biomassa_pipeline = [{"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$jembatan_timbang_mt", 0]}}}}]
    
    vessel_tonase = await db.vessels.aggregate(vessel_pipeline).to_list(1)
    barge_tonase = await db.barges.aggregate(barge_pipeline).to_list(1)
    biomassa_tonase = await db.biomassa.aggregate(biomassa_pipeline).to_list(1)
    
    total_tonase_batubara = (vessel_tonase[0]["total"] if vessel_tonase else 0) + (barge_tonase[0]["total"] if barge_tonase else 0)
    total_tonase_biomassa = biomassa_tonase[0]["total"] if biomassa_tonase else 0
    
    # Average GCV
    gcv_pipeline = [{"$match": {"gcv_arb": {"$ne": None}}}, {"$group": {"_id": None, "avg": {"$avg": "$gcv_arb"}}}]
    vessel_gcv = await db.vessels.aggregate(gcv_pipeline).to_list(1)
    avg_gcv = vessel_gcv[0]["avg"] if vessel_gcv else 0
    
    # Recent shipments
    recent_vessels = await db.vessels.find({}, {"_id": 0}).sort([
        ("time_arrival", -1),
        ("completed_unloading", -1),
        ("created_at", -1),
    ]).limit(5).to_list(5)
    recent_barges = await db.barges.find({}, {"_id": 0}).sort([
        ("ta", -1),
        ("completed_unloading", -1),
        ("created_at", -1),
    ]).limit(5).to_list(5)
    recent_shipments = []
    for v in recent_vessels:
        recent_shipments.append({
            "type": "vessel",
            "name": v.get("name_of_vessel", ""),
            "code": v.get("shipment_code", ""),
            "date": v.get("time_arrival") or v.get("completed_unloading") or v.get("created_at", ""),
        })
    for b in recent_barges:
        recent_shipments.append({
            "type": "barge",
            "name": b.get("name_of_barge", ""),
            "code": b.get("shipment_code", ""),
            "date": b.get("ta") or b.get("completed_unloading") or b.get("created_at", ""),
        })
    recent_shipments = sorted(recent_shipments, key=lambda x: x.get("date", ""), reverse=True)[:5]
    
    # Monthly trend (simplified)
    monthly_trend = [
        {"month": "Jan", "vessel": 5, "barge": 3, "trucking": 10, "biomassa": 8},
        {"month": "Feb", "vessel": 4, "barge": 5, "trucking": 12, "biomassa": 6},
        {"month": "Mar", "vessel": 6, "barge": 4, "trucking": 8, "biomassa": 10},
        {"month": "Apr", "vessel": 3, "barge": 6, "trucking": 15, "biomassa": 7},
        {"month": "May", "vessel": 7, "barge": 2, "trucking": 11, "biomassa": 9},
        {"month": "Jun", "vessel": 5, "barge": 4, "trucking": 9, "biomassa": 12}
    ]
    
    # Supplier stats
    supplier_pipeline = [
        {"$group": {"_id": "$suppliers", "count": {"$sum": 1}, "total_tonase": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}},
        {"$sort": {"total_tonase": -1}},
        {"$limit": 10}
    ]
    supplier_stats_raw = await db.vessels.aggregate(supplier_pipeline).to_list(10)
    supplier_stats = [{"supplier": s["_id"], "count": s["count"], "tonase": s["total_tonase"]} for s in supplier_stats_raw if s["_id"]]
    
    return DashboardStats(
        total_vessel=total_vessel,
        total_barge=total_barge,
        total_trucking=total_trucking,
        total_biomassa=total_biomassa,
        total_tonase_batubara=total_tonase_batubara,
        total_tonase_biomassa=total_tonase_biomassa,
        avg_gcv=avg_gcv or 0,
        recent_shipments=recent_shipments,
        monthly_trend=monthly_trend,
        supplier_stats=supplier_stats
    )

async def build_dashboard_advanced(
    year: Optional[int] = None,
    month: Optional[int] = None,
    moda: Optional[str] = None,
    user: Optional[dict] = None,
):
    """Advanced dashboard data with filters"""
    # Calculate 6 months ago
    today = date.today()
    six_months_ago = today - relativedelta(months=6)
    
    # Build date filter based on completed_unloading field
    date_filter = {}
    if year and month:
        # Filter specific month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        date_filter = {"completed_unloading": {"$gte": start_date, "$lt": end_date}}
    
    # Moda filter for trucking
    moda_filter = {}
    
    # === 1. Contract Monitoring (Gauge) ===
    # Total DS MT from all sources
    vessel_ds = await db.vessels.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}
    ]).to_list(1)
    barge_ds = await db.barges.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}
    ]).to_list(1)
    trucking_ds = await db.trucking.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}
    ]).to_list(1)
    biomassa_ds = await db.biomassa.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$jembatan_timbang_mt", 0]}}}}
    ]).to_list(1)
    
    total_ds_mt = (
        (vessel_ds[0]["total"] if vessel_ds else 0) +
        (barge_ds[0]["total"] if barge_ds else 0) +
        (trucking_ds[0]["total"] if trucking_ds else 0) +
        (biomassa_ds[0]["total"] if biomassa_ds else 0)
    )
    
    # Total Tonase PO from PO Batubara
    po_tonase = await db.po_batubara.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$tonase_po", 0]}}}}
    ]).to_list(1)
    total_tonase_po = po_tonase[0]["total"] if po_tonase else 0
    
    contract_percentage = (total_ds_mt / total_tonase_po * 100) if total_tonase_po > 0 else 0
    
    # === 2. Fuel Composition (Donut) - Based on PO Batubara spec (LRC/MRC) and Biomassa types ===
    # Get coal spec (LRC, MRC) from PO Batubara with tonase
    po_spec_data = await db.po_batubara.aggregate([
        {"$match": {"spec": {"$ne": None}, "tonase_po": {"$ne": None}}},
        {"$group": {"_id": "$spec", "total_tonase": {"$sum": {"$ifNull": ["$tonase_po", 0]}}, "count": {"$sum": 1}}}
    ]).to_list(100)
    
    # Get biomass types from biomassa collection
    biomass_types = await db.biomassa.aggregate([
        {"$match": {"biomass_type": {"$ne": None}}},
        {"$group": {"_id": "$biomass_type", "total_tonase": {"$sum": {"$ifNull": ["$jembatan_timbang_mt", 0]}}, "count": {"$sum": 1}}}
    ]).to_list(100)
    
    fuel_composition = []
    
    # Add coal types (LRC, MRC) from PO
    for item in po_spec_data:
        spec_name = item["_id"]
        if spec_name:
            fuel_composition.append({
                "name": f"Batubara {spec_name}",
                "value": item["total_tonase"],
                "count": item["count"],
                "type": "coal"
            })
    
    # Add biomass types
    for item in biomass_types:
        btype = item["_id"]
        if btype:
            fuel_composition.append({
                "name": f"Biomassa {btype}",
                "value": item["total_tonase"],
                "count": item["count"],
                "type": "biomass"
            })
    
    # Sort by value descending
    fuel_composition.sort(key=lambda x: x["value"], reverse=True)
    
    # === 3. GCV Trend (Line Chart) ===
    # Get GCV data with dates from vessels and barges
    gcv_trend = []
    vessel_gcv_data = await db.vessels.find(
        {"gcv_arb": {"$ne": None}, "completed_unloading": {"$ne": None}},
        {"_id": 0, "completed_unloading": 1, "gcv_arb": 1, "name_of_vessel": 1}
    ).sort("completed_unloading", 1).to_list(500)
    
    barge_gcv_data = await db.barges.find(
        {"gcv_arb": {"$ne": None}, "completed_unloading": {"$ne": None}},
        {"_id": 0, "completed_unloading": 1, "gcv_arb": 1}
    ).sort("completed_unloading", 1).to_list(500)
    
    # Combine and sort
    all_gcv = []
    for v in vessel_gcv_data:
        try:
            date_str = str(v.get("completed_unloading", ""))[:10]
            all_gcv.append({"date": date_str, "gcv": v["gcv_arb"], "source": "vessel"})
        except:
            pass
    for b in barge_gcv_data:
        try:
            date_str = str(b.get("completed_unloading", ""))[:10]
            all_gcv.append({"date": date_str, "gcv": b["gcv_arb"], "source": "barge"})
        except:
            pass
    
    # Group by date and calculate average
    gcv_by_date = {}
    for item in all_gcv:
        d = item["date"]
        if d not in gcv_by_date:
            gcv_by_date[d] = []
        gcv_by_date[d].append(item["gcv"])
    
    for d, values in sorted(gcv_by_date.items()):
        gcv_trend.append({
            "date": d,
            "gcv_avg": sum(values) / len(values),
            "count": len(values),
            "target": 4000
        })
    
    # Limit to last 50 data points
    gcv_trend = gcv_trend[-50:]
    
    # === 4. Supplier Economy Analysis (Bar Chart) ===
    # Calculate Actual Rp/Kcal = (Harga CIF / GCV ARB) / 1000
    supplier_economy = []
    
    # Get merit order data with harga_cif
    merit_orders = await db.merit_order.find(
        {"harga_cif": {"$ne": None}, "pemasok": {"$ne": None}},
        {"_id": 0, "pemasok": 1, "harga_cif": 1, "rp_kcal": 1}
    ).to_list(1000)
    
    # Get GCV by supplier from vessels
    supplier_gcv = {}
    vessels_data = await db.vessels.find(
        {"gcv_arb": {"$ne": None}, "suppliers": {"$ne": None}},
        {"_id": 0, "suppliers": 1, "gcv_arb": 1}
    ).to_list(1000)
    
    for v in vessels_data:
        sup = v["suppliers"]
        if sup not in supplier_gcv:
            supplier_gcv[sup] = []
        supplier_gcv[sup].append(v["gcv_arb"])
    
    # Calculate Rp/Kcal for each supplier in merit order
    supplier_rp_kcal = {}
    for mo in merit_orders:
        sup = mo["pemasok"]
        if mo.get("rp_kcal"):
            if sup not in supplier_rp_kcal:
                supplier_rp_kcal[sup] = []
            supplier_rp_kcal[sup].append(mo["rp_kcal"])
    
    # Average and sort
    for sup, values in supplier_rp_kcal.items():
        avg_rp_kcal = sum(values) / len(values)
        supplier_economy.append({
            "supplier": sup[:30] + "..." if len(sup) > 30 else sup,
            "full_name": sup,
            "rp_kcal": avg_rp_kcal,
            "count": len(values)
        })
    
    # Sort by rp_kcal (lowest = most efficient) and take top 10
    supplier_economy.sort(key=lambda x: x["rp_kcal"])
    supplier_economy = supplier_economy[:10]
    
    # === 5. Slagging Risk Matrix (Heatmap) - Include Vessel, Barge, and Trucking ===
    slagging_matrix = []
    
    # Get from Vessels
    vessels_slagging = await db.vessels.find(
        {"$or": [{"slagging_index": {"$ne": None}}, {"fouling_index": {"$ne": None}}]},
        {"_id": 0, "name_of_vessel": 1, "suppliers": 1, "slagging_index": 1, "fouling_index": 1, "completed_unloading": 1}
    ).sort("completed_unloading", -1).limit(15).to_list(15)
    
    # Get from Barges
    barges_slagging = await db.barges.find(
        {"$or": [{"slagging_index": {"$ne": None}}, {"fouling_index": {"$ne": None}}]},
        {"_id": 0, "name_of_barge": 1, "suppliers": 1, "slagging_index": 1, "fouling_index": 1, "completed_unloading": 1}
    ).sort("completed_unloading", -1).limit(15).to_list(15)
    
    # Get from Trucking
    trucking_slagging = await db.trucking.find(
        {"$or": [{"slagging_index": {"$ne": None}}, {"fouling_index": {"$ne": None}}]},
        {"_id": 0, "suppliers": 1, "slagging_index": 1, "fouling_index": 1, "completed_unloading": 1}
    ).sort("completed_unloading", -1).limit(15).to_list(15)
    
    def get_risk_level(index_value):
        if not index_value:
            return "UNKNOWN"
        val = str(index_value).upper()
        if "SEVERE" in val:
            return "SEVERE"
        elif "HIGH" in val:
            return "HIGH"
        elif "MEDIUM" in val:
            return "MEDIUM"
        elif "LOW" in val:
            return "LOW"
        return "UNKNOWN"
    
    # Add Vessel data
    for v in vessels_slagging:
        slagging_matrix.append({
            "name": v.get("name_of_vessel", "Unknown Vessel"),
            "supplier": v.get("suppliers", ""),
            "slagging": v.get("slagging_index", ""),
            "slagging_risk": get_risk_level(v.get("slagging_index")),
            "fouling": v.get("fouling_index", ""),
            "fouling_risk": get_risk_level(v.get("fouling_index")),
            "date": str(v.get("completed_unloading", ""))[:10],
            "moda": "Vessel"
        })
    
    # Add Barge data
    for b in barges_slagging:
        slagging_matrix.append({
            "name": b.get("name_of_barge", b.get("suppliers", "Unknown Barge")),
            "supplier": b.get("suppliers", ""),
            "slagging": b.get("slagging_index", ""),
            "slagging_risk": get_risk_level(b.get("slagging_index")),
            "fouling": b.get("fouling_index", ""),
            "fouling_risk": get_risk_level(b.get("fouling_index")),
            "date": str(b.get("completed_unloading", ""))[:10],
            "moda": "Barge"
        })
    
    # Add Trucking data
    for t in trucking_slagging:
        slagging_matrix.append({
            "name": t.get("suppliers", "Unknown Trucking"),
            "supplier": t.get("suppliers", ""),
            "slagging": t.get("slagging_index", ""),
            "slagging_risk": get_risk_level(t.get("slagging_index")),
            "fouling": t.get("fouling_index", ""),
            "fouling_risk": get_risk_level(t.get("fouling_index")),
            "date": str(t.get("completed_unloading", ""))[:10],
            "moda": "Trucking"
        })
    
    # Sort by date descending
    slagging_matrix.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # === 6. Six Months Summary ===
    six_months_summary = []
    current_date = date.today()
    
    for i in range(6):
        target_date = current_date - relativedelta(months=i)
        year_val = target_date.year
        month_val = target_date.month
        month_name = target_date.strftime("%b %Y")
        
        # Count by month
        vessel_count = await db.vessels.count_documents({
            "completed_unloading": {"$regex": f"^{year_val}-{month_val:02d}"}
        })
        barge_count = await db.barges.count_documents({
            "completed_unloading": {"$regex": f"^{year_val}-{month_val:02d}"}
        })
        trucking_count = await db.trucking.count_documents({
            "completed_unloading": {"$regex": f"^{year_val}-{month_val:02d}"}
        })
        biomassa_count = await db.biomassa.count_documents({
            "completed_unloading": {"$regex": f"^{year_val}-{month_val:02d}"}
        })
        
        # Tonase by month
        vessel_ton = await db.vessels.aggregate([
            {"$match": {"completed_unloading": {"$regex": f"^{year_val}-{month_val:02d}"}}},
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}
        ]).to_list(1)
        barge_ton = await db.barges.aggregate([
            {"$match": {"completed_unloading": {"$regex": f"^{year_val}-{month_val:02d}"}}},
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ds_mt", 0]}}}}
        ]).to_list(1)
        
        six_months_summary.append({
            "month": month_name,
            "year": year_val,
            "month_num": month_val,
            "vessel": vessel_count,
            "barge": barge_count,
            "trucking": trucking_count,
            "biomassa": biomassa_count,
            "total_shipments": vessel_count + barge_count + trucking_count + biomassa_count,
            "vessel_tonase": vessel_ton[0]["total"] if vessel_ton else 0,
            "barge_tonase": barge_ton[0]["total"] if barge_ton else 0,
            "total_tonase": (vessel_ton[0]["total"] if vessel_ton else 0) + (barge_ton[0]["total"] if barge_ton else 0)
        })
    
    # Reverse to show oldest first
    six_months_summary.reverse()
    
    # === Available filters ===
    available_periods = []
    years = [2023, 2024, 2025, 2026]
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    for y in years:
        for m_idx, m_name in enumerate(months, 1):
            available_periods.append({"year": y, "month": m_idx, "label": f"{m_name} {y}"})
    
    available_moda = ["Vessel", "Barge", "Trucking", "Tongkang"]
    
    return {
        "total_ds_mt": total_ds_mt,
        "total_tonase_po": total_tonase_po,
        "contract_percentage": min(contract_percentage, 100),
        "fuel_composition": fuel_composition,
        "gcv_trend": gcv_trend,
        "supplier_economy": supplier_economy,
        "slagging_matrix": slagging_matrix,
        "six_months_summary": six_months_summary,
        "available_periods": available_periods[-24:],  # Last 2 years
        "available_moda": available_moda
    }
