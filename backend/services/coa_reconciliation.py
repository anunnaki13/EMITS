"""
COA Reconciliation Service
Handles data parsing and comparison between Loading, Unloading, and Lab Internal data
"""

import pandas as pd
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import uuid


def safe_float(val):
    """Safely convert value to float"""
    if pd.isna(val) or val == '' or val is None or val == '-':
        return None
    try:
        return float(val)
    except:
        return None


def safe_str(val):
    """Safely convert value to string"""
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()


def safe_int(val):
    """Safely convert value to int"""
    if pd.isna(val) or val == '' or val is None:
        return None
    try:
        return int(float(val))
    except:
        return None


def clean_column_name(col):
    """Clean column name by removing newlines and extra spaces"""
    if isinstance(col, str):
        return col.replace('\n', ' ').replace('  ', ' ').strip()
    return col


def safe_datetime(val):
    """Safely convert value to ISO datetime string"""
    if pd.isna(val) or val is None or val == '':
        return None
    try:
        if isinstance(val, pd.Timestamp):
            return val.isoformat()
        if isinstance(val, datetime):
            return val.isoformat()
        # Try parsing string
        return pd.to_datetime(val).isoformat()
    except:
        return None


def parse_coa_excel(file_contents: bytes, source_type: str) -> List[Dict]:
    """
    Parse COA Excel file (Loading, Unloading, or Lab Internal)
    Returns list of records with standardized field names
    """
    df = pd.read_excel(io.BytesIO(file_contents))
    
    # Clean column names
    df.columns = [clean_column_name(col) for col in df.columns]
    
    records = []
    for _, row in df.iterrows():
        # Extract Shipment as STRING to preserve "Lot XX" format
        shipment_raw = row.get("Shipment")
        if pd.isna(shipment_raw) or shipment_raw is None or shipment_raw == '':
            continue
        shipment = safe_str(shipment_raw)  # Keep as string!
        if not shipment:
            continue
            
        record = {
            "shipment": shipment,  # Now stored as string
            "periode": safe_str(row.get("Periode")),
            "suppliers": safe_str(row.get("Suppliers")),
            "tb": safe_str(row.get("TB")),
            "bg": safe_str(row.get("BG")),
            "ds_mt": safe_float(row.get("DS (MT)")),
            "commenced_unloading": safe_datetime(row.get("Commenced Unloading")),
            "completed_unloading": safe_datetime(row.get("Completed Unloading")),
            # GCV values
            "gcv_arb": safe_float(row.get("GCV (Kcal/Kg) ARB", row.get("GCV (Kcal/Kg)\nARB"))),
            "gcv_adb": safe_float(row.get("GCV (Kcal/Kg) ADB", row.get("GCV (Kcal/Kg)\nADB"))),
            "gcv_db": safe_float(row.get("GCV (Kcal/Kg) DB", row.get("GCV (Kcal/Kg)\nDB"))),
            # Moisture
            "tm_arb": safe_float(row.get("TM (%wt) ARB", row.get("TM (%wt)\nARB"))),
            "im_adb": safe_float(row.get("IM (%wt) ADB", row.get("IM (%wt) \nADB"))),
            # Ash Content
            "ash_arb": safe_float(row.get("Ash Content (%wt) ARB", row.get("Ash \nContent (%wt) \nARB"))),
            "ash_adb": safe_float(row.get("Ash Content (%wt) ADB", row.get("Ash \nContent (%wt)\nADB", row.get("Ash \nContent (%wt) \nADB")))),
            "ash_db": safe_float(row.get("Ash Content (%wt) DB", row.get("Ash \nContent (%wt)\nDB", row.get("Ash \nContent (%wt) \nDB")))),
            # Total Sulphur
            "ts_arb": safe_float(row.get("Total Sulphur (%wt) ARB", row.get("Total Sulphur (%wt)\nARB"))),
            "ts_adb": safe_float(row.get("Total Sulphur (%wt) ADB", row.get("Total Sulphur (%wt)\nADB"))),
            "ts_db": safe_float(row.get("Total Sulphur (%wt) DB", row.get("Total Sulphur (%wt)\nDB"))),
            # HGI and IDT
            "hgi": safe_float(row.get("HGI (Point Index)")),
            "idt_reducing": safe_float(row.get("IDT Reducing (C°)")),
            # Source type
            "source_type": source_type
        }
        
        # Add source-specific fields
        if source_type == "loading":
            record["surveyor"] = safe_str(row.get("Surveyor Loading"))
            record["no_coa"] = safe_str(row.get("NO.COA"))
            record["tgl_coa"] = safe_str(row.get("Tgl Terbit COA"))
        elif source_type == "unloading":
            record["surveyor"] = safe_str(row.get("Surveyor Unloading"))
            record["no_cow"] = safe_str(row.get("NO.COW"))
            record["tgl_cow"] = safe_str(row.get("Tgl Terbit COW"))
            record["no_coa"] = safe_str(row.get("NO. COA"))
            record["tgl_coa"] = safe_str(row.get("Tgl Terbit COA"))
            record["slagging_index"] = safe_str(row.get("Slagging (Index)"))
            record["fouling_index"] = safe_str(row.get("Fouling (Index)"))
        
        records.append(record)
    
    return records


def merge_coa_data(loading_data: List[Dict], unloading_data: List[Dict], internal_data: List[Dict]) -> List[Dict]:
    """
    Merge data from all three sources based on Shipment ID (string)
    Returns merged records with comparison data
    """
    # Create dictionaries keyed by shipment (string)
    loading_dict = {r["shipment"]: r for r in loading_data if r["shipment"]}
    unloading_dict = {r["shipment"]: r for r in unloading_data if r["shipment"]}
    internal_dict = {r["shipment"]: r for r in internal_data if r["shipment"]}
    
    # Get all unique shipments
    all_shipments = set(loading_dict.keys()) | set(unloading_dict.keys()) | set(internal_dict.keys())
    
    merged_records = []
    for shipment in all_shipments:
        loading = loading_dict.get(shipment, {})
        unloading = unloading_dict.get(shipment, {})
        internal = internal_dict.get(shipment, {})
        
        # Use the first available data for common fields
        base_data = loading or unloading or internal
        
        # Calculate deltas
        loading_gcv = loading.get("gcv_arb")
        unloading_gcv = unloading.get("gcv_arb")
        internal_gcv = internal.get("gcv_arb")
        
        delta_loading_internal = None
        delta_unloading_internal = None
        delta_loading_unloading = None
        
        if loading_gcv and internal_gcv:
            delta_loading_internal = loading_gcv - internal_gcv
        if unloading_gcv and internal_gcv:
            delta_unloading_internal = unloading_gcv - internal_gcv
        if loading_gcv and unloading_gcv:
            delta_loading_unloading = loading_gcv - unloading_gcv
        
        # Determine status based on delta (Loading vs Internal)
        # KRITIS: Loading > Internal (supplier overclaim, Anda RUGI)
        # NORMAL: Loading <= Internal (supplier underclaim atau sama, Anda UNTUNG/OK)
        status = "normal"
        if delta_loading_internal is not None:
            if delta_loading_internal > 150:  # Hanya positif = Loading > Internal = RUGI
                status = "critical"
            elif delta_loading_internal > 100:  # Warning jika selisih > 100 tapi <= 150
                status = "warning"
        
        # Build merged record
        record = {
            "id": str(uuid.uuid4()),
            "shipment": shipment,  # Now string: "555" or "Lot 24"
            "periode": base_data.get("periode", ""),
            "suppliers": base_data.get("suppliers", ""),
            "tb": base_data.get("tb", ""),
            "bg": base_data.get("bg", ""),
            "ds_mt": base_data.get("ds_mt"),
            "completed_unloading": base_data.get("completed_unloading"),  # For sorting
            # Loading data
            "loading_gcv_arb": loading_gcv,
            "loading_tm_arb": loading.get("tm_arb"),
            "loading_ash_arb": loading.get("ash_arb"),
            "loading_ts_arb": loading.get("ts_arb"),
            "loading_surveyor": loading.get("surveyor"),
            "loading_no_coa": loading.get("no_coa"),
            # Unloading data
            "unloading_gcv_arb": unloading_gcv,
            "unloading_tm_arb": unloading.get("tm_arb"),
            "unloading_ash_arb": unloading.get("ash_arb"),
            "unloading_ts_arb": unloading.get("ts_arb"),
            "unloading_surveyor": unloading.get("surveyor"),
            "unloading_slagging": unloading.get("slagging_index"),
            "unloading_fouling": unloading.get("fouling_index"),
            # Internal data
            "internal_gcv_arb": internal_gcv,
            "internal_tm_arb": internal.get("tm_arb"),
            "internal_ash_arb": internal.get("ash_arb"),
            "internal_ts_arb": internal.get("ts_arb"),
            # Umpire data (empty initially, filled later)
            "umpire_gcv_arb": None,
            "umpire_tm_arb": None,
            "umpire_ash_arb": None,
            "umpire_ts_arb": None,
            "umpire_lab_name": None,
            "umpire_result_date": None,
            # Deltas
            "delta_loading_internal": delta_loading_internal,
            "delta_unloading_internal": delta_unloading_internal,
            "delta_loading_unloading": delta_loading_unloading,
            # Status
            "status": status,
            "umpire_status": "none",  # none, proposed, in_progress, completed
            "umpire_sample_number": None,
            "umpire_proposed_at": None,
            "umpire_completed_at": None,
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        merged_records.append(record)
    
    # Sort by completed_unloading date (newest first)
    merged_records.sort(key=lambda x: x.get("completed_unloading") or "", reverse=True)
    
    return merged_records


def calculate_kpis(merged_data: List[Dict], price_per_kcal_per_ton: float = None) -> Dict:
    """
    Calculate KPI metrics for the anomaly dashboard
    
    Args:
        merged_data: List of reconciliation records
        price_per_kcal_per_ton: Price per kCal per ton from settings (optional)
    """
    total_records = len(merged_data)
    
    # High Deviation Alert: Count where |delta_loading_internal| > 100
    high_deviation_count = sum(
        1 for r in merged_data 
        if r.get("delta_loading_internal") and abs(r["delta_loading_internal"]) > 100
    )
    
    # Potential Loss calculation
    # Loss = sum of (delta_gcv * ds_mt * price_per_kcal_per_ton)
    potential_loss = 0
    total_tonnage_problem = 0
    
    # Use provided price or None (will show as "Harga belum diatur")
    if price_per_kcal_per_ton is not None and price_per_kcal_per_ton > 0:
        for r in merged_data:
            delta = r.get("delta_loading_internal")
            ds_mt = r.get("ds_mt") or 0
            if delta and delta > 0:  # Only positive delta (loss)
                potential_loss += delta * ds_mt * price_per_kcal_per_ton
                total_tonnage_problem += ds_mt
    else:
        # Just calculate tonnage problem without loss
        for r in merged_data:
            delta = r.get("delta_loading_internal")
            ds_mt = r.get("ds_mt") or 0
            if delta and delta > 0:
                total_tonnage_problem += ds_mt
    
    # Umpire status counts
    umpire_proposed = sum(1 for r in merged_data if r.get("umpire_status") == "proposed")
    umpire_in_progress = sum(1 for r in merged_data if r.get("umpire_status") == "in_progress")
    umpire_completed = sum(1 for r in merged_data if r.get("umpire_status") == "completed")
    
    # Supplier accuracy calculation
    supplier_stats = {}
    for r in merged_data:
        supplier = r.get("suppliers") or "Unknown"
        if supplier not in supplier_stats:
            supplier_stats[supplier] = {"count": 0, "total_deviation": 0, "deviations": []}
        
        supplier_stats[supplier]["count"] += 1
        delta = r.get("delta_loading_internal")
        if delta is not None:
            supplier_stats[supplier]["total_deviation"] += abs(delta)
            supplier_stats[supplier]["deviations"].append(delta)
    
    # Calculate average deviation per supplier
    supplier_deviations = []
    for supplier, stats in supplier_stats.items():
        if stats["deviations"]:
            avg_deviation = sum(abs(d) for d in stats["deviations"]) / len(stats["deviations"])
            supplier_deviations.append({
                "supplier": supplier,
                "count": stats["count"],
                "avg_deviation": round(avg_deviation, 2),
                "total_deviation": round(stats["total_deviation"], 2)
            })
    
    # Sort by average deviation (worst first)
    supplier_deviations.sort(key=lambda x: x["avg_deviation"], reverse=True)
    
    # Find worst supplier
    worst_supplier = supplier_deviations[0] if supplier_deviations else None
    
    # Average accuracy (100% - normalized deviation)
    all_deviations = [abs(r.get("delta_loading_internal", 0) or 0) for r in merged_data]
    avg_deviation = sum(all_deviations) / len(all_deviations) if all_deviations else 0
    # Normalize to percentage (assuming 500 kcal max deviation = 0% accuracy)
    avg_accuracy = max(0, 100 - (avg_deviation / 5))  # 500 kcal = 0%, 0 kcal = 100%
    
    return {
        "total_records": total_records,
        "high_deviation_count": high_deviation_count,
        "potential_loss_rp": round(potential_loss, 0),
        "total_tonnage_problem": round(total_tonnage_problem, 2),
        "umpire_status": {
            "proposed": umpire_proposed,
            "in_progress": umpire_in_progress,
            "completed": umpire_completed,
            "total": umpire_proposed + umpire_in_progress
        },
        "supplier_deviations": supplier_deviations[:10],  # Top 10 worst
        "worst_supplier": worst_supplier,
        "avg_accuracy": round(avg_accuracy, 1),
        "critical_count": sum(1 for r in merged_data if r.get("status") == "critical"),
        "warning_count": sum(1 for r in merged_data if r.get("status") == "warning"),
        "normal_count": sum(1 for r in merged_data if r.get("status") == "normal")
    }


def get_gcv_trend_data(merged_data: List[Dict], months: int = 3) -> List[Dict]:
    """
    Get GCV trend data for line chart comparing all three sources
    """
    # Group by periode (month)
    monthly_data = {}
    
    for r in merged_data:
        periode = r.get("periode", "")
        if not periode:
            continue
        
        # Extract month key (YYYY-MM)
        try:
            if isinstance(periode, str) and len(periode) >= 7:
                month_key = periode[:7]  # Get YYYY-MM
            else:
                continue
        except:
            continue
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "loading_gcv": [],
                "unloading_gcv": [],
                "internal_gcv": []
            }
        
        if r.get("loading_gcv_arb"):
            monthly_data[month_key]["loading_gcv"].append(r["loading_gcv_arb"])
        if r.get("unloading_gcv_arb"):
            monthly_data[month_key]["unloading_gcv"].append(r["unloading_gcv_arb"])
        if r.get("internal_gcv_arb"):
            monthly_data[month_key]["internal_gcv"].append(r["internal_gcv_arb"])
    
    # Calculate averages and format for chart
    trend_data = []
    for month_key in sorted(monthly_data.keys())[-months*4:]:  # Get recent months
        data = monthly_data[month_key]
        trend_data.append({
            "periode": month_key,
            "loading": round(sum(data["loading_gcv"]) / len(data["loading_gcv"]), 0) if data["loading_gcv"] else None,
            "unloading": round(sum(data["unloading_gcv"]) / len(data["unloading_gcv"]), 0) if data["unloading_gcv"] else None,
            "internal": round(sum(data["internal_gcv"]) / len(data["internal_gcv"]), 0) if data["internal_gcv"] else None
        })
    
    return trend_data


def get_radar_chart_data(record: Dict) -> List[Dict]:
    """
    Get radar chart data for a single shipment comparing all tests (3 or 4 sources)
    Parameters: GCV, TM, Ash, Sulphur (normalized to 0-100 scale)
    Includes Umpire data if available
    """
    # Normalization ranges (typical coal values)
    gcv_range = (3000, 5000)  # kcal/kg
    tm_range = (20, 50)  # %
    ash_range = (2, 15)  # %
    ts_range = (0.1, 2)  # %
    
    def normalize(val, min_val, max_val):
        if val is None:
            return None
        normalized = ((val - min_val) / (max_val - min_val)) * 100
        return max(0, min(100, normalized))
    
    # Check if umpire data exists
    has_umpire = record.get("umpire_gcv_arb") is not None
    
    return [
        {
            "parameter": "GCV",
            "loading": normalize(record.get("loading_gcv_arb"), *gcv_range),
            "unloading": normalize(record.get("unloading_gcv_arb"), *gcv_range),
            "internal": normalize(record.get("internal_gcv_arb"), *gcv_range),
            "umpire": normalize(record.get("umpire_gcv_arb"), *gcv_range) if has_umpire else None,
            "fullMark": 100
        },
        {
            "parameter": "TM",
            "loading": normalize(record.get("loading_tm_arb"), *tm_range),
            "unloading": normalize(record.get("unloading_tm_arb"), *tm_range),
            "internal": normalize(record.get("internal_tm_arb"), *tm_range),
            "umpire": normalize(record.get("umpire_tm_arb"), *tm_range) if has_umpire else None,
            "fullMark": 100
        },
        {
            "parameter": "Ash",
            "loading": normalize(record.get("loading_ash_arb"), *ash_range),
            "unloading": normalize(record.get("unloading_ash_arb"), *ash_range),
            "internal": normalize(record.get("internal_ash_arb"), *ash_range),
            "umpire": normalize(record.get("umpire_ash_arb"), *ash_range) if has_umpire else None,
            "fullMark": 100
        },
        {
            "parameter": "Sulphur",
            "loading": normalize(record.get("loading_ts_arb"), *ts_range),
            "unloading": normalize(record.get("unloading_ts_arb"), *ts_range),
            "internal": normalize(record.get("internal_ts_arb"), *ts_range),
            "umpire": normalize(record.get("umpire_ts_arb"), *ts_range) if has_umpire else None,
            "fullMark": 100
        }
    ]
