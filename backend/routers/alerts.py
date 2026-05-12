from datetime import date, datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from utils.auth import get_current_user, require_role
from utils.database import db

router = APIRouter(prefix="/alerts", tags=["Alerts"])

ALERT_RULE_CONFIG = {
    "low_stock_days": 14,
    "critical_stock_days": 7,
    "high_coa_delta": 100,
    "stale_dispute_days": 7,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_prefix(value):
    return str(value or "")[:10]


def _days_since(value):
    prefix = _date_prefix(value)
    if not prefix:
        return None
    try:
        return max((date.today() - date.fromisoformat(prefix)).days, 0)
    except ValueError:
        return None


async def _sum_collection(collection, match: dict, field: str) -> float:
    result = await collection.aggregate([
        {"$match": match},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": [f"${field}", 0]}}}},
    ]).to_list(1)
    return float(result[0]["total"]) if result else 0.0


async def _collect_alert_candidates() -> list[dict]:
    candidates = []
    today_prefix = date.today().isoformat()

    latest_stock = await db.smartstock.find_one({}, {"_id": 0}, sort=[("date", -1)])
    latest_usage = await db.sumberpemakaian.find_one({}, {"_id": 0}, sort=[("date", -1)])
    total_usage = await _sum_collection(db.sumberpemakaian, {}, "total_pemakaian")
    avg_daily_usage = total_usage / 30 if total_usage > 0 else 0
    current_stock = 0
    if latest_stock:
        current_stock = latest_stock.get("stock_akhir")
        if current_stock is None:
            current_stock = (
                latest_stock.get("stock_awal", 0)
                + latest_stock.get("total_penerimaan", 0)
                - (latest_usage.get("total_pemakaian", 0) if latest_usage else 0)
            )
    days_of_supply = int(current_stock / avg_daily_usage) if avg_daily_usage > 0 else None
    if days_of_supply is not None and days_of_supply < ALERT_RULE_CONFIG["low_stock_days"]:
        severity = "critical" if days_of_supply < ALERT_RULE_CONFIG["critical_stock_days"] else "warning"
        candidates.append({
            "key": "stock:days-of-supply",
            "type": "low_stock",
            "severity": severity,
            "title": "Stok batubara mendekati batas reorder",
            "message": f"Projected supply {days_of_supply} hari dengan stok {current_stock:.0f} MT.",
            "source_path": "/smart-stock/sumber-penerimaan",
            "source_id": latest_stock.get("id") if latest_stock else None,
            "metadata": {
                "current_stock": current_stock,
                "days_of_supply": days_of_supply,
                "threshold_days": ALERT_RULE_CONFIG["low_stock_days"],
            },
        })

    delayed_pos = await db.po_batubara.find(
        {"time_arrival": {"$lt": today_prefix}},
        {"_id": 0, "id": 1, "no_jadwal": 1, "supplier_name": 1, "time_arrival": 1, "tonase_po": 1},
    ).sort("time_arrival", 1).limit(25).to_list(25)
    for item in delayed_pos:
        alert_id = item.get("id") or item.get("no_jadwal") or _date_prefix(item.get("time_arrival"))
        candidates.append({
            "key": f"arrival:{alert_id}",
            "type": "delayed_arrival",
            "severity": "warning",
            "title": "Jadwal kedatangan melewati ETA",
            "message": f"{item.get('no_jadwal') or '-'} melewati ETA {item.get('time_arrival') or '-'} ({item.get('supplier_name') or '-'}).",
            "source_path": "/po-batubara",
            "source_id": item.get("id"),
            "metadata": {
                "no_jadwal": item.get("no_jadwal"),
                "supplier_name": item.get("supplier_name"),
                "time_arrival": item.get("time_arrival"),
                "tonase_po": item.get("tonase_po"),
            },
        })

    coa_items = await db.coa_reconciliation.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "shipment": 1,
            "suppliers": 1,
            "status": 1,
            "umpire_status": 1,
            "delta_loading_internal": 1,
            "completed_unloading": 1,
            "umpire_proposed_at": 1,
        },
    ).to_list(10000)
    for item in coa_items:
        delta = abs(float(item.get("delta_loading_internal") or 0))
        status = str(item.get("status") or "").lower()
        if status in {"critical", "kritis"} or delta >= ALERT_RULE_CONFIG["high_coa_delta"]:
            candidates.append({
                "key": f"coa-delta:{item.get('id') or item.get('shipment')}",
                "type": "high_coa_delta",
                "severity": "critical" if status in {"critical", "kritis"} else "warning",
                "title": "Selisih COA perlu ditindaklanjuti",
                "message": f"{item.get('shipment') or '-'} memiliki delta {delta:.0f}.",
                "source_path": "/coa-reconciliation",
                "source_id": item.get("id"),
                "metadata": {
                    "shipment": item.get("shipment"),
                    "suppliers": item.get("suppliers"),
                    "delta_loading_internal": item.get("delta_loading_internal"),
                    "status": item.get("status"),
                },
            })

        if item.get("umpire_status") in {"proposed", "in_progress"}:
            age = _days_since(item.get("umpire_proposed_at") or item.get("completed_unloading"))
            if age is not None and age >= ALERT_RULE_CONFIG["stale_dispute_days"]:
                candidates.append({
                    "key": f"stale-dispute:{item.get('id') or item.get('shipment')}",
                    "type": "stale_dispute",
                    "severity": "warning",
                    "title": "Dispute umpire belum selesai",
                    "message": f"{item.get('shipment') or '-'} masih {item.get('umpire_status')} selama {age} hari.",
                    "source_path": "/dispute-monitor",
                    "source_id": item.get("id"),
                    "metadata": {
                        "shipment": item.get("shipment"),
                        "umpire_status": item.get("umpire_status"),
                        "aging_days": age,
                    },
                })

    return candidates


async def generate_alerts() -> dict:
    candidates = await _collect_alert_candidates()
    seen_keys = []
    timestamp = _now()
    for candidate in candidates:
        seen_keys.append(candidate["key"])
        existing = await db.alerts.find_one({"key": candidate["key"]}, {"_id": 0})
        doc = {
            **candidate,
            "last_seen_at": timestamp,
            "updated_at": timestamp,
        }
        if existing:
            await db.alerts.update_one({"key": candidate["key"]}, {"$set": doc})
        else:
            await db.alerts.insert_one({
                "id": str(uuid.uuid4()),
                "status": "open",
                "created_at": timestamp,
                **doc,
            })

    return {"generated": len(candidates), "keys": seen_keys}


@router.post("/recompute")
async def recompute_alerts(user: dict = Depends(get_current_user)):
    result = await generate_alerts()
    return {"message": "Alert rules evaluated", **result}


@router.get("")
async def list_alerts(
    status: str = Query("open"),
    limit: int = Query(25, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    await generate_alerts()
    query = {} if status == "all" else {"status": status}
    items = await db.alerts.find(query, {"_id": 0}).sort([("severity", 1), ("updated_at", -1)]).limit(limit).to_list(limit)
    total = await db.alerts.count_documents(query)
    open_count = await db.alerts.count_documents({"status": "open"})
    critical_count = await db.alerts.count_documents({"status": "open", "severity": "critical"})
    warning_count = await db.alerts.count_documents({"status": "open", "severity": "warning"})
    return {
        "items": items,
        "total": total,
        "open_count": open_count,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "rule_config": ALERT_RULE_CONFIG,
    }


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: dict = Depends(require_role(["admin", "operator"]))):
    timestamp = _now()
    result = await db.alerts.update_one(
        {"id": alert_id},
        {"$set": {"status": "acknowledged", "acknowledged_at": timestamp, "acknowledged_by": user["id"], "updated_at": timestamp}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: dict = Depends(require_role(["admin", "operator"]))):
    timestamp = _now()
    result = await db.alerts.update_one(
        {"id": alert_id},
        {"$set": {"status": "resolved", "resolved_at": timestamp, "resolved_by": user["id"], "updated_at": timestamp}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved"}
