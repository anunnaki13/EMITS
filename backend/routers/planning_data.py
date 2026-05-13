from datetime import datetime, timezone
import io
import logging
import re
from typing import Optional
import uuid

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
import pandas as pd
from pydantic import BaseModel

from models import MeritOrderCreate, MeritOrderResponse, POBatubaraCreate, POBatubaraResponse
from services.data_quality import summarize_import_quality
from utils.auth import get_current_user, require_role
from utils.database import db

router = APIRouter(tags=["Planning Data"])
logger = logging.getLogger(__name__)


class ImportCommitRequest(BaseModel):
    mode: str = "append"


def _safe_float(val):
    if pd.isna(val) or val == '' or val is None or val == '-':
        return None
    try:
        return float(val)
    except Exception:
        return None


def _safe_str(val):
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()


def _safe_regex(value: str) -> dict:
    return {"$regex": re.escape(str(value).strip()), "$options": "i"}


def _parse_datetime(val):
    if pd.isna(val) or val is None:
        return None, None, None
    try:
        if isinstance(val, (int, float)):
            dt = pd.to_datetime('1899-12-30') + pd.to_timedelta(val, 'D')
        elif isinstance(val, str):
            dt = pd.to_datetime(val)
        else:
            dt = val
        return str(dt), dt.year, dt.month
    except Exception:
        return str(val), None, None


def _parse_periode(val):
    if pd.isna(val) or val is None:
        return None, None, None
    try:
        if isinstance(val, str):
            dt = pd.to_datetime(val)
        else:
            dt = val
        return str(dt.date()), dt.year, dt.month
    except Exception:
        return str(val), None, None


def _get_col(row, *possible_names):
    for name in possible_names:
        val = row.get(name)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            return val
    return None


def _parse_po_batubara_records(contents: bytes, user_id: str) -> tuple[list[dict], list[str]]:
    df = pd.read_excel(io.BytesIO(contents))
    df.columns = df.columns.str.replace('\n', ' ').str.strip()
    records = []
    for _, row in df.iterrows():
        completed_str, completed_year, completed_month = _parse_datetime(_get_col(row, "Completed"))
        po_doc = {
            "id": str(uuid.uuid4()),
            "district_code": _safe_str(_get_col(row, "District Code")),
            "district_name": _safe_str(_get_col(row, "District Name")),
            "periode": _safe_str(_get_col(row, "Periode")),
            "stock_code": _safe_float(_get_col(row, "Stock Code")),
            "warehouse": _safe_float(_get_col(row, "Warehouse")),
            "po_number": _safe_str(_get_col(row, "PO Number")),
            "supplier_code": _safe_str(_get_col(row, "Supplier Code")),
            "supplier_name": _safe_str(_get_col(row, "Supplier Name")),
            "spec": _safe_str(_get_col(row, "Spec")),
            "vessel_tugboat": _safe_str(_get_col(row, "Vessel / Tugboat", "Vessel/Tugboat")),
            "barge": _safe_str(_get_col(row, "Barge No", "Barge")),
            "no_jadwal": _safe_str(_get_col(row, "No Jadwal", "Jadwal Id BBO (No Pengiriman)")),
            "id_bbo_no_pengiriman": _safe_str(_get_col(row, "Id BBO (No Pengiriman)", "Jadwal Id BBO (No Pengiriman)")),
            "id_bbo_trans": _safe_str(_get_col(row, "Id BBO Trans")),
            "no_shipment": _safe_str(_get_col(row, "No Shipment")),
            "time_arrival": _safe_str(_get_col(row, "Time Arrival")),
            "completed": completed_str,
            "completed_year": completed_year,
            "completed_month": completed_month,
            "tonase_po": _safe_float(_get_col(row, "Tonase PO")),
            "tonase_po_1000": _safe_float(_get_col(row, "Tonase PO*1000")),
            "inventory_price": _safe_float(_get_col(row, "Inventory Price")),
            "freight_inventory_fob": _safe_float(_get_col(row, "Freight Inventory (FOB)", "Freight", "Inventory (FOB)")),
            "total": _safe_float(_get_col(row, "Total")),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id
        }
        records.append(po_doc)
    return records, list(df.columns)


def _parse_merit_order_records(contents: bytes, user_id: str) -> tuple[list[dict], list[str]]:
    df = pd.read_excel(io.BytesIO(contents))
    records = []
    for _, row in df.iterrows():
        periode_str, periode_year, periode_month = _parse_periode(row.get("Periode"))
        records.append({
            "id": str(uuid.uuid4()),
            "periode": periode_str,
            "periode_year": periode_year,
            "periode_month": periode_month,
            "pemasok": _safe_str(row.get("Pemasok")),
            "moda": _safe_str(row.get("Moda")),
            "tipikal_kcal_kg": _safe_float(row.get("Tipikal (Kcal/Kg)")),
            "jenis_kontrak": _safe_str(row.get("Jenis Kontrak")),
            "harga_batubara": _safe_float(row.get("Harga Batubara (RP/Ton)")),
            "harga_freight": _safe_float(row.get("Harga Freight (RP/Ton)")),
            "harga_cif": _safe_float(row.get("Harga CIF(RP/Ton)")),
            "rp_kg": _safe_float(row.get("RP/Kg")),
            "rp_kcal": _safe_float(row.get("RP/Kcal")),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id
        })
    return records, list(df.columns)


IMPORT_CONFIG = {
    "po-batubara": {
        "collection": "po_batubara",
        "parser": _parse_po_batubara_records,
        "required_columns": ["PO Number", "Supplier Name", "Tonase PO"],
        "key_fields": ["po_number", "no_jadwal"],
    },
    "merit-order": {
        "collection": "merit_order",
        "parser": _parse_merit_order_records,
        "required_columns": ["Periode", "Pemasok", "Moda", "RP/Kcal"],
        "key_fields": ["periode", "pemasok", "moda", "jenis_kontrak"],
    },
}


def _record_key(record: dict, fields: list[str]) -> str:
    return "|".join(str(record.get(field) or "").strip().lower() for field in fields)


async def _preview_import(dataset: str, contents: bytes, filename: str, user: dict) -> dict:
    config = IMPORT_CONFIG.get(dataset)
    if not config:
        raise HTTPException(status_code=404, detail="Dataset import tidak didukung")

    records, columns = config["parser"](contents, user["id"])
    normalized_columns = {str(col).replace('\n', ' ').strip() for col in columns}
    issues = []
    for column in config["required_columns"]:
        if column not in normalized_columns:
            issues.append({"row": None, "field": column, "type": "missing_required_column", "message": f"Kolom wajib '{column}' tidak ditemukan"})

    seen = {}
    key_fields = config["key_fields"]
    for index, record in enumerate(records, start=2):
        key = _record_key(record, key_fields)
        if not key or set(key.split("|")) == {""}:
            issues.append({"row": index, "field": ",".join(key_fields), "type": "missing_key", "message": "Key import kosong"})
            continue
        if key in seen:
            issues.append({"row": index, "field": ",".join(key_fields), "type": "duplicate_in_file", "message": f"Duplikat dengan row {seen[key]}"})
        else:
            seen[key] = index

    collection = getattr(db, config["collection"])
    existing_duplicate_count = 0
    for record in records[:500]:
        query = {field: record.get(field) for field in key_fields if record.get(field) not in [None, ""]}
        if query and await collection.count_documents(query) > 0:
            existing_duplicate_count += 1
    if existing_duplicate_count:
        issues.append({"row": None, "field": ",".join(key_fields), "type": "duplicate_existing", "message": f"{existing_duplicate_count} baris berpotensi duplikat dengan data existing"})

    data_quality = summarize_import_quality(dataset, records, issues)
    preview_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    preview_doc = {
        "id": preview_id,
        "dataset": dataset,
        "filename": filename,
        "records": records,
        "columns": columns,
        "issues": issues,
        "data_quality": data_quality,
        "status": "previewed",
        "created_at": now,
        "created_by": user["id"],
    }
    await db.import_previews.insert_one(preview_doc)
    return {
        "preview_id": preview_id,
        "dataset": dataset,
        "filename": filename,
        "row_count": len(records),
        "issue_count": len(issues),
        "issues": issues[:100],
        "data_quality": data_quality,
        "preview_rows": records[:10],
        "allowed_modes": ["append", "replace", "merge"],
    }


async def _commit_import(preview: dict, mode: str, user: dict) -> dict:
    if mode not in {"append", "replace", "merge"}:
        raise HTTPException(status_code=400, detail="Mode import harus append, replace, atau merge")
    config = IMPORT_CONFIG.get(preview["dataset"])
    if not config:
        raise HTTPException(status_code=404, detail="Dataset import tidak didukung")

    collection = getattr(db, config["collection"])
    records = preview.get("records") or []
    inserted = updated = deleted = 0
    if mode == "replace":
        deleted = (await collection.delete_many({})).deleted_count
        if records:
            await collection.insert_many(records)
            inserted = len(records)
    elif mode == "merge":
        key_fields = config["key_fields"]
        for record in records:
            query = {field: record.get(field) for field in key_fields if record.get(field) not in [None, ""]}
            if not query:
                continue
            result = await collection.update_one(query, {"$set": record}, upsert=True)
            if result.upserted_id:
                inserted += 1
            else:
                updated += result.modified_count or 1
    else:
        if records:
            await collection.insert_many(records)
            inserted = len(records)

    now = datetime.now(timezone.utc).isoformat()
    history = {
        "id": str(uuid.uuid4()),
        "preview_id": preview["id"],
        "dataset": preview["dataset"],
        "filename": preview.get("filename"),
        "mode": mode,
        "row_count": len(records),
        "issue_count": len(preview.get("issues") or []),
        "inserted": inserted,
        "updated": updated,
        "deleted": deleted,
        "created_at": now,
        "created_by": user["id"],
    }
    await db.import_history.insert_one(history)
    await db.import_previews.update_one(
        {"id": preview["id"]},
        {"$set": {"status": "committed", "committed_at": now, "committed_by": user["id"], "commit_mode": mode}},
    )
    return {k: v for k, v in history.items() if k != "_id"}

# ==================== PO BATUBARA ROUTES ====================

@router.get("/po-batubara")
async def get_po_batubara(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50000),
    year: Optional[int] = None,
    month: Optional[int] = None,
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    conditions = []
    
    if year:
        conditions.append({"completed_year": year})
    if month:
        conditions.append({"completed_month": month})
    if search:
        safe_search = re.escape(search)
        conditions.append({
            "$or": [
                {"po_number": {"$regex": safe_search, "$options": "i"}},
                {"supplier_name": {"$regex": safe_search, "$options": "i"}},
                {"no_shipment": {"$regex": safe_search, "$options": "i"}}
            ]
        })
    if supplier and supplier != "all":
        conditions.append({"supplier_name": _safe_regex(supplier)})
    
    if conditions:
        query = {"$and": conditions} if len(conditions) > 1 else conditions[0]
    
    skip = (page - 1) * page_size
    total = await db.po_batubara.count_documents(query)
    po_list = await db.po_batubara.find(query, {"_id": 0}).sort("periode", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "items": po_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/po-batubara/years")
async def get_po_years(supplier: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get list of available years with monthly summaries"""
    match_stage = {"completed_year": {"$ne": None}}
    if supplier and supplier != "all":
        match_stage["supplier_name"] = _safe_regex(supplier)
    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {"year": "$completed_year", "month": "$completed_month"},
            "count": {"$sum": 1},
            "total_tonase": {"$sum": "$tonase_po"},
            "total_value": {"$sum": "$total"}
        }},
        {"$sort": {"_id.year": -1, "_id.month": 1}}
    ]
    results = await db.po_batubara.aggregate(pipeline).to_list(1000)
    
    # Organize by year
    years_data = {}
    for r in results:
        year = r["_id"]["year"]
        month = r["_id"]["month"]
        if year not in years_data:
            years_data[year] = {"year": year, "months": {}, "total_count": 0, "total_tonase": 0, "total_value": 0}
        years_data[year]["months"][month] = {
            "month": month,
            "count": r["count"],
            "total_tonase": r["total_tonase"] or 0,
            "total_value": r["total_value"] or 0
        }
        years_data[year]["total_count"] += r["count"]
        years_data[year]["total_tonase"] += r["total_tonase"] or 0
        years_data[year]["total_value"] += r["total_value"] or 0
    
    return list(years_data.values())

@router.post("/po-batubara", response_model=POBatubaraResponse)
async def create_po_batubara(po: POBatubaraCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    po_id = str(uuid.uuid4())
    po_doc = {
        "id": po_id,
        **po.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    await db.po_batubara.insert_one(po_doc)
    return POBatubaraResponse(**{k: v for k, v in po_doc.items() if k != "_id"})

@router.get("/po-batubara/{po_id}", response_model=POBatubaraResponse)
async def get_po_batubara_by_id(po_id: str, user: dict = Depends(get_current_user)):
    po = await db.po_batubara.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Data PO tidak ditemukan")
    return POBatubaraResponse(**po)

@router.put("/po-batubara/{po_id}", response_model=POBatubaraResponse)
async def update_po_batubara(po_id: str, po: POBatubaraCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    existing = await db.po_batubara.find_one({"id": po_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Data PO tidak ditemukan")
    await db.po_batubara.update_one({"id": po_id}, {"$set": po.model_dump()})
    updated = await db.po_batubara.find_one({"id": po_id}, {"_id": 0})
    return POBatubaraResponse(**updated)

@router.delete("/po-batubara/{po_id}")
async def delete_po_batubara(po_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.po_batubara.delete_one({"id": po_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data PO tidak ditemukan")
    return {"message": "Data PO berhasil dihapus"}

@router.delete("/po-batubara")
async def delete_all_po_batubara(user: dict = Depends(require_role(["admin"]))):
    result = await db.po_batubara.delete_many({})
    return {"message": f"Berhasil menghapus {result.deleted_count} data PO", "count": result.deleted_count}

@router.post("/import-preview/{dataset}")
async def preview_excel_import(
    dataset: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_role(["admin", "operator"]))
):
    try:
        contents = await file.read()
        return await _preview_import(dataset, contents, file.filename or "upload.xlsx", user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing import {dataset}: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal preview file: {str(e)}")


@router.post("/import-preview/{preview_id}/commit")
async def commit_excel_import(
    preview_id: str,
    request: ImportCommitRequest = Body(default_factory=ImportCommitRequest),
    user: dict = Depends(require_role(["admin", "operator"]))
):
    preview = await db.import_previews.find_one({"id": preview_id}, {"_id": 0})
    if not preview:
        raise HTTPException(status_code=404, detail="Preview import tidak ditemukan")
    if preview.get("status") == "committed":
        raise HTTPException(status_code=400, detail="Preview import sudah pernah dicommit")
    result = await _commit_import(preview, request.mode, user)
    return {"message": "Import berhasil dicommit", **result}


@router.get("/import-history")
async def get_import_history(
    dataset: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    query = {"dataset": dataset} if dataset else {}
    skip = (page - 1) * page_size
    total = await db.import_history.count_documents(query)
    items = await db.import_history.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}

@router.post("/upload/po-batubara")
async def upload_po_batubara_excel(file: UploadFile = File(...), user: dict = Depends(require_role(["admin", "operator"]))):
    try:
        contents = await file.read()
        records, _ = _parse_po_batubara_records(contents, user["id"])
        
        if records:
            await db.po_batubara.insert_many(records)
        
        return {"message": f"Berhasil mengimport {len(records)} data PO Batubara", "count": len(records)}
    except Exception as e:
        logger.error(f"Error uploading PO batubara excel: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file: {str(e)}")

# ==================== MERIT ORDER ROUTES ====================

@router.get("/merit-order")
async def get_merit_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50000),
    year: Optional[int] = None,
    month: Optional[int] = None,
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    conditions = []
    
    if year:
        conditions.append({"periode_year": year})
    if month:
        conditions.append({"periode_month": month})
    if search:
        safe_search = re.escape(search)
        conditions.append({
            "$or": [
                {"pemasok": {"$regex": safe_search, "$options": "i"}},
                {"moda": {"$regex": safe_search, "$options": "i"}},
                {"jenis_kontrak": {"$regex": safe_search, "$options": "i"}}
            ]
        })
    if supplier and supplier != "all":
        conditions.append({"pemasok": _safe_regex(supplier)})
    
    if conditions:
        query = {"$and": conditions} if len(conditions) > 1 else conditions[0]
    
    skip = (page - 1) * page_size
    total = await db.merit_order.count_documents(query)
    mo_list = await db.merit_order.find(query, {"_id": 0}).sort("periode", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "items": mo_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/merit-order/periods")
async def get_merit_order_periods(user: dict = Depends(get_current_user)):
    """Get list of available periods with summaries"""
    pipeline = [
        {"$match": {"periode_year": {"$ne": None}}},
        {"$group": {
            "_id": {"year": "$periode_year", "month": "$periode_month"},
            "count": {"$sum": 1},
            "avg_rp_kcal": {"$avg": "$rp_kcal"},
            "min_rp_kcal": {"$min": "$rp_kcal"},
            "max_rp_kcal": {"$max": "$rp_kcal"}
        }},
        {"$sort": {"_id.year": -1, "_id.month": -1}}
    ]
    results = await db.merit_order.aggregate(pipeline).to_list(1000)
    
    # Organize by year
    years_data = {}
    for r in results:
        year = r["_id"]["year"]
        month = r["_id"]["month"]
        if year not in years_data:
            years_data[year] = {"year": year, "months": {}, "total_count": 0}
        years_data[year]["months"][month] = {
            "month": month,
            "count": r["count"],
            "avg_rp_kcal": r["avg_rp_kcal"] or 0,
            "min_rp_kcal": r["min_rp_kcal"] or 0,
            "max_rp_kcal": r["max_rp_kcal"] or 0
        }
        years_data[year]["total_count"] += r["count"]
    
    return list(years_data.values())

@router.post("/merit-order", response_model=MeritOrderResponse)
async def create_merit_order(mo: MeritOrderCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    mo_id = str(uuid.uuid4())
    mo_doc = {
        "id": mo_id,
        **mo.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    await db.merit_order.insert_one(mo_doc)
    return MeritOrderResponse(**{k: v for k, v in mo_doc.items() if k != "_id"})

@router.get("/merit-order/{mo_id}", response_model=MeritOrderResponse)
async def get_merit_order_by_id(mo_id: str, user: dict = Depends(get_current_user)):
    mo = await db.merit_order.find_one({"id": mo_id}, {"_id": 0})
    if not mo:
        raise HTTPException(status_code=404, detail="Data Merit Order tidak ditemukan")
    return MeritOrderResponse(**mo)

@router.put("/merit-order/{mo_id}", response_model=MeritOrderResponse)
async def update_merit_order(mo_id: str, mo: MeritOrderCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    existing = await db.merit_order.find_one({"id": mo_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Data Merit Order tidak ditemukan")
    await db.merit_order.update_one({"id": mo_id}, {"$set": mo.model_dump()})
    updated = await db.merit_order.find_one({"id": mo_id}, {"_id": 0})
    return MeritOrderResponse(**updated)

@router.delete("/merit-order/{mo_id}")
async def delete_merit_order(mo_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.merit_order.delete_one({"id": mo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data Merit Order tidak ditemukan")
    return {"message": "Data Merit Order berhasil dihapus"}

@router.delete("/merit-order")
async def delete_all_merit_orders(user: dict = Depends(require_role(["admin"]))):
    result = await db.merit_order.delete_many({})
    return {"message": f"Berhasil menghapus {result.deleted_count} data Merit Order", "count": result.deleted_count}

@router.post("/upload/merit-order")
async def upload_merit_order_excel(file: UploadFile = File(...), user: dict = Depends(require_role(["admin", "operator"]))):
    try:
        contents = await file.read()
        records, _ = _parse_merit_order_records(contents, user["id"])
        
        if records:
            await db.merit_order.insert_many(records)
        
        return {"message": f"Berhasil mengimport {len(records)} data Merit Order", "count": len(records)}
    except Exception as e:
        logger.error(f"Error uploading merit order excel: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file: {str(e)}")
