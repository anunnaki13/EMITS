from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import uuid
from datetime import datetime, timezone
import pandas as pd
import io
import jwt
from app.ai.openrouter_client import LLMUnavailableError
from routers.auth import router as auth_router, users_router
from routers.admin import router as admin_router
from routers.alerts import router as alerts_router
from routers.ai_intelligence import router as ai_intelligence_router
from routers.coa import router as coa_router
from routers.data_quality import router as data_quality_router
from routers.dashboard import router as dashboard_router
from routers.planning_data import router as planning_data_router
from routers.reports import router as reports_router
from routers.smart_stock import router as smart_stock_router
from services.backup_service import backup_scheduler_loop
from services.runtime_status import build_public_version_status
from utils.auth import get_current_user, require_role
from utils.filters import build_rekap_query

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
_db_name = os.environ.get("MONGO_TEST_DB_NAME") or os.environ['DB_NAME']
db = client[_db_name]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'tenayan-fuel-management-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="PLTU Tenayan Fuel Management System")


# ==================== LLM UNAVAILABLE HANDLER (D-09, OPS-02) ====================
# Maps LLMUnavailableError -> HTTP 503 with Indonesian detail body.
# Covers: retry exhaustion, 401/402/non-retryable OpenRouter responses.
@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )

# ==================== AUTHFIX-02: VALIDATION ERROR HANDLER ====================
# CONS-auth-header (locked SPEC) requires HTTP 400 for malformed body on /api/auth/*.
# FastAPI's default for Pydantic ValidationError is HTTP 422 — we remap ONLY for
# /api/auth/* paths so other routes (vessels/COA/etc.) keep the standard 422 default.
# Decision record: pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md (D-AUTH-01).
@app.exception_handler(RequestValidationError)
async def auth_validation_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/auth/"):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.errors()},
        )
    # Fall through to FastAPI default for non-auth routes (preserve 422 elsewhere).
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(alerts_router)
api_router.include_router(ai_intelligence_router)
api_router.include_router(coa_router)
api_router.include_router(data_quality_router)
api_router.include_router(dashboard_router)
api_router.include_router(planning_data_router)
api_router.include_router(reports_router)
api_router.include_router(smart_stock_router)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AUDIT_RESOURCE_PREFIXES = {
    "vessels": "rekap",
    "barges": "rekap",
    "trucking": "rekap",
    "biomassa": "rekap",
    "po-batubara": "rekap",
    "merit-order": "rekap",
    "smart-stock": "rekap",
    "sumber-pemakaian": "rekap",
    "coa-reconciliation": "coa",
    "settings": "settings",
    "ai/settings": "settings",
    "admin/backup": "settings",
    "admin/restore": "settings",
    "auth/register": "users",
    "users": "users",
}

AUDIT_ACTIONS = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

AUDIT_COLLECTIONS = {
    "vessels": "vessels",
    "barges": "barges",
    "trucking": "trucking",
    "biomassa": "biomassa",
    "po-batubara": "po_batubara",
    "merit-order": "merit_order",
    "smart-stock": "smartstock",
    "sumber-pemakaian": "sumberpemakaian",
    "coa-reconciliation": "coa_reconciliation",
    "users": "users",
}

AUDIT_SECRET_FIELDS = {"password", "hashed_password", "custom_api_key", "api_key", "token", "access_token"}


def _audit_scope(path: str) -> Optional[Dict[str, Optional[str]]]:
    if not path.startswith("/api/"):
        return None

    relative_path = path.removeprefix("/api/").strip("/")
    for prefix, category in AUDIT_RESOURCE_PREFIXES.items():
        if relative_path == prefix or relative_path.startswith(f"{prefix}/"):
            parts = relative_path.split("/")
            record_id = parts[len(prefix.split("/"))] if len(parts) > len(prefix.split("/")) else None
            return {
                "resource": prefix.split("/")[0],
                "category": category,
                "record_id": record_id,
            }
    return None


def _audit_severity(method: str, path: str, record_id: Optional[str]) -> str:
    if path == "/api/admin/restore" or (method == "DELETE" and record_id is None):
        return "high"
    if method in {"DELETE", "PUT", "PATCH"}:
        return "medium"
    return "low"


def _audit_sanitize(document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not document:
        return None
    return {key: value for key, value in document.items() if key not in AUDIT_SECRET_FIELDS and key != "_id"}


async def _audit_fetch_record(scope: Dict[str, Optional[str]]) -> Optional[Dict[str, Any]]:
    collection_name = AUDIT_COLLECTIONS.get(scope["resource"])
    record_id = scope.get("record_id")
    if not collection_name or not record_id:
        return None
    return _audit_sanitize(await db[collection_name].find_one({"id": record_id}, {"_id": 0}))


def _audit_diff(before: Optional[Dict[str, Any]], after: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if before is None or after is None:
        return None
    diff = {}
    for key in sorted(set(before.keys()) | set(after.keys())):
        if key in AUDIT_SECRET_FIELDS or key == "_id":
            continue
        if before.get(key) != after.get(key):
            diff[key] = {"before": before.get(key), "after": after.get(key)}
    return diff or None


async def _audit_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
    except Exception:
        return None


@app.middleware("http")
async def audit_mutations(request: Request, call_next):
    method = request.method.upper()
    audit_scope = _audit_scope(request.url.path) if method in AUDIT_ACTIONS else None
    before_record = await _audit_fetch_record(audit_scope) if audit_scope and method in {"PUT", "PATCH", "DELETE"} else None
    response = await call_next(request)

    if audit_scope and response.status_code < 400:
        actor = await _audit_user_from_request(request)
        try:
            after_record = await _audit_fetch_record(audit_scope) if method in {"PUT", "PATCH"} else None
            await db.audit_logs.insert_one({
                "id": str(uuid.uuid4()),
                "action": "restore" if request.url.path == "/api/admin/restore" else AUDIT_ACTIONS[method],
                "method": method,
                "path": request.url.path,
                "category": audit_scope["category"],
                "resource": audit_scope["resource"],
                "record_id": audit_scope["record_id"],
                "severity": _audit_severity(method, request.url.path, audit_scope["record_id"]),
                "before": before_record,
                "after": after_record,
                "diff": _audit_diff(before_record, after_record),
                "status_code": response.status_code,
                "actor_id": actor.get("id") if actor else None,
                "actor_email": actor.get("email") if actor else None,
                "actor_role": actor.get("role") if actor else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as exc:
            logger.warning("audit log write failed: %s", exc)

    return response


@app.on_event("startup")
async def start_backup_scheduler():
    app.state.backup_scheduler_task = asyncio.create_task(backup_scheduler_loop())


@app.on_event("shutdown")
async def stop_backup_scheduler():
    task = getattr(app.state, "backup_scheduler_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

# ==================== MODELS ====================

# Vessel TNY Model - Complete fields based on PLTU Tenayan Excel template
class VesselTNYCreate(BaseModel):
    # Informasi Shipment
    periode_ta: str
    periode_realisasi: str
    shipment_code: str
    voyage_code: str
    suppliers: str
    voyage: str
    name_of_vessel: str
    coal_from: str
    # Waktu Operasional
    time_arrival: Optional[str] = None
    berthed_time: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    durasi_pembongkaran_hari: Optional[float] = None
    durasi_pembongkaran_jam: Optional[float] = None
    waktu_tunggu_jam: Optional[float] = None
    # Muatan
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    # COW (Certificate of Weighing)
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    # Kualitas - GCV
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    # Kualitas - Moisture
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    # Kualitas - Ash Content
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    # Kualitas - VM & FC
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    # Kualitas - Sulfur
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    ts_dafb: Optional[float] = None
    # Ultimate Analysis
    c_arb: Optional[float] = None
    c_adb: Optional[float] = None
    h_arb: Optional[float] = None
    h_adb: Optional[float] = None
    n_arb: Optional[float] = None
    n_adb: Optional[float] = None
    n_dafb: Optional[float] = None
    o_arb: Optional[float] = None
    o_adb: Optional[float] = None
    # HGI & Index
    hgi: Optional[float] = None
    slagging_index: Optional[str] = None
    fouling_index: Optional[str] = None
    idt_reducing: Optional[float] = None
    # Ash Composition
    sio2_db: Optional[float] = None
    al2o3_db: Optional[float] = None
    tio2_db: Optional[float] = None
    fe2o3_db: Optional[float] = None
    cao_db: Optional[float] = None
    mgo_db: Optional[float] = None
    k2o_db: Optional[float] = None
    na2o_db: Optional[float] = None
    so3_db: Optional[float] = None
    p2o5_db: Optional[float] = None
    mno2_db: Optional[float] = None
    mn3o4_db: Optional[float] = None
    # Size Analysis
    size_70mm: Optional[float] = None
    size_50mm: Optional[float] = None
    size_32mm: Optional[float] = None
    size_2_38mm: Optional[float] = None
    # COA (Certificate of Analysis)
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None
    durasi_terbit_coa: Optional[str] = None

class VesselTNYResponse(BaseModel):
    id: str
    # Informasi Shipment
    periode_ta: str
    periode_realisasi: str
    shipment_code: str
    voyage_code: str
    suppliers: str
    voyage: str
    name_of_vessel: str
    coal_from: str
    # Waktu Operasional
    time_arrival: Optional[str] = None
    berthed_time: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    durasi_pembongkaran_hari: Optional[float] = None
    durasi_pembongkaran_jam: Optional[float] = None
    waktu_tunggu_jam: Optional[float] = None
    # Muatan
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    # COW
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    # Kualitas - GCV
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    # Kualitas - Moisture
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    # Kualitas - Ash Content
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    # Kualitas - VM & FC
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    # Kualitas - Sulfur
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    ts_dafb: Optional[float] = None
    # Ultimate Analysis
    c_arb: Optional[float] = None
    c_adb: Optional[float] = None
    h_arb: Optional[float] = None
    h_adb: Optional[float] = None
    n_arb: Optional[float] = None
    n_adb: Optional[float] = None
    n_dafb: Optional[float] = None
    o_arb: Optional[float] = None
    o_adb: Optional[float] = None
    # HGI & Index
    hgi: Optional[float] = None
    slagging_index: Optional[str] = None
    fouling_index: Optional[str] = None
    idt_reducing: Optional[float] = None
    # Ash Composition
    sio2_db: Optional[float] = None
    al2o3_db: Optional[float] = None
    tio2_db: Optional[float] = None
    fe2o3_db: Optional[float] = None
    cao_db: Optional[float] = None
    mgo_db: Optional[float] = None
    k2o_db: Optional[float] = None
    na2o_db: Optional[float] = None
    so3_db: Optional[float] = None
    p2o5_db: Optional[float] = None
    mno2_db: Optional[float] = None
    mn3o4_db: Optional[float] = None
    # Size Analysis
    size_70mm: Optional[float] = None
    size_50mm: Optional[float] = None
    size_32mm: Optional[float] = None
    size_2_38mm: Optional[float] = None
    # COA
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None
    durasi_terbit_coa: Optional[str] = None
    # Metadata
    created_at: str
    created_by: Optional[str] = None

# Barge TNY Model - Complete fields based on PLTU Tenayan Excel template
class BargeTNYCreate(BaseModel):
    # Informasi Shipment
    periode: str
    shipment_code: str
    voyage_code: str
    shipment: Optional[str] = None
    suppliers: str
    voyage: str
    tb: Optional[str] = None  # Tug Boat
    bg: Optional[str] = None  # Barge Name
    coal_from: str
    # Waktu Operasional
    ta: Optional[str] = None  # Time Arrival
    berthed_time: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    durasi_pembongkaran_hari: Optional[float] = None
    durasi_pembongkaran_jam: Optional[float] = None
    waktu_tunggu_jam: Optional[float] = None
    # Muatan
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    # COW
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    # Kualitas - GCV
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    # Kualitas - Moisture
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    # Kualitas - Ash Content
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    # Kualitas - VM & FC
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    # Kualitas - Sulfur
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    ts_dafb: Optional[float] = None
    # Ultimate Analysis
    c_arb: Optional[float] = None
    c_adb: Optional[float] = None
    h_arb: Optional[float] = None
    h_adb: Optional[float] = None
    n_arb: Optional[float] = None
    n_adb: Optional[float] = None
    n_dafb: Optional[float] = None
    o_arb: Optional[float] = None
    o_adb: Optional[float] = None
    # HGI & Index
    hgi: Optional[float] = None
    slagging_index: Optional[str] = None
    fouling_index: Optional[str] = None
    idt_reducing: Optional[float] = None
    # Ash Composition
    sio2_db: Optional[float] = None
    al2o3_db: Optional[float] = None
    tio2_db: Optional[float] = None
    fe2o3_db: Optional[float] = None
    cao_db: Optional[float] = None
    mgo_db: Optional[float] = None
    k2o_db: Optional[float] = None
    na2o_db: Optional[float] = None
    so3_db: Optional[float] = None
    p2o5_db: Optional[float] = None
    mno2_db: Optional[float] = None
    mn3o4_db: Optional[float] = None
    # Size Analysis
    size_70mm: Optional[float] = None
    size_50mm: Optional[float] = None
    size_32mm: Optional[float] = None
    size_2_38mm: Optional[float] = None
    # COA
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None
    durasi_terbit_coa: Optional[str] = None

class BargeTNYResponse(BargeTNYCreate):
    id: str
    created_at: str
    created_by: Optional[str] = None

# Trucking TNY Model - Complete fields based on PLTU Tenayan Excel template
class TruckingTNYCreate(BaseModel):
    # Informasi Shipment
    periode_ta: str
    periode_realisasi: str
    shipment_code: str
    voyage_code: str
    shipment: Optional[str] = None
    suppliers: str
    transportasi: Optional[str] = None
    coal_from: str
    # Waktu Operasional
    ta: Optional[str] = None
    berthed_time: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    durasi_pembongkaran_hari: Optional[float] = None
    durasi_pembongkaran_jam: Optional[float] = None
    # Muatan
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    rit: Optional[int] = None  # Jumlah RIT
    # COW
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    # Kualitas - GCV
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    # Kualitas - Moisture
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    # Kualitas - Ash Content
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    # Kualitas - VM & FC
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    # Kualitas - Sulfur
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    ts_dafb: Optional[float] = None
    # Ultimate Analysis
    c_arb: Optional[float] = None
    c_adb: Optional[float] = None
    h_arb: Optional[float] = None
    h_adb: Optional[float] = None
    n_arb: Optional[float] = None
    n_adb: Optional[float] = None
    n_dafb: Optional[float] = None
    o_arb: Optional[float] = None
    o_adb: Optional[float] = None
    # HGI & Index
    hgi: Optional[float] = None
    slagging_index: Optional[str] = None
    fouling_index: Optional[str] = None
    idt_reducing: Optional[float] = None
    # Ash Composition
    sio2_db: Optional[float] = None
    al2o3_db: Optional[float] = None
    tio2_db: Optional[float] = None
    fe2o3_db: Optional[float] = None
    cao_db: Optional[float] = None
    mgo_db: Optional[float] = None
    k2o_db: Optional[float] = None
    na2o_db: Optional[float] = None
    so3_db: Optional[float] = None
    p2o5_db: Optional[float] = None
    mno2_db: Optional[float] = None
    mn3o4_db: Optional[float] = None
    # Size Analysis
    size_70mm: Optional[float] = None
    size_50mm: Optional[float] = None
    size_32mm: Optional[float] = None
    size_2_38mm: Optional[float] = None
    # COA
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None

class TruckingTNYResponse(TruckingTNYCreate):
    id: str
    created_at: str
    created_by: Optional[str] = None

# Biomassa TNY Model - Complete fields based on PLTU Tenayan Excel template
class BiomassaTNYCreate(BaseModel):
    # Informasi Shipment
    periode: Optional[str] = None
    shipment_code: Optional[str] = None
    voyage_code: Optional[str] = None
    lot: Optional[str] = None
    suppliers: Optional[str] = None
    shipper: Optional[str] = None
    lot_1: Optional[str] = None
    tb: Optional[str] = None  # Tug Boat
    bg: Optional[str] = None  # Barge
    biomass_type: Optional[str] = None  # Jenis Biomassa
    # Waktu Operasional
    ta: Optional[str] = None  # Time Arrival
    berthed_time: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    durasi_pembongkaran_hari: Optional[float] = None
    # Muatan
    bl_mt: Optional[float] = None
    jembatan_timbang_mt: Optional[float] = None
    surveyor_unloading: Optional[str] = None
    # COW/ROW
    no_cow_row: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    lama_terbit_row: Optional[float] = None
    # Kualitas
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    # COA
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None
    durasi_pembongkaran_hari_2: Optional[float] = None
    waktu_tunggu_jam: Optional[float] = None
    durasi_terbit_coa: Optional[float] = None

class BiomassaTNYResponse(BiomassaTNYCreate):
    id: str
    created_at: str
    created_by: Optional[str] = None

# PO Batubara Model
class POBatubaraCreate(BaseModel):
    district_code: Optional[str] = None
    district_name: Optional[str] = None
    periode: Optional[str] = None
    stock_code: Optional[float] = None
    warehouse: Optional[float] = None
    po_number: Optional[str] = None
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    spec: Optional[str] = None
    vessel_tugboat: Optional[str] = None
    barge: Optional[str] = None
    no_jadwal: Optional[str] = None
    id_bbo_no_pengiriman: Optional[str] = None
    id_bbo_trans: Optional[str] = None
    no_shipment: Optional[str] = None
    time_arrival: Optional[str] = None
    completed: Optional[str] = None
    completed_year: Optional[int] = None
    completed_month: Optional[int] = None
    tonase_po: Optional[float] = None
    tonase_po_1000: Optional[float] = None
    inventory_price: Optional[float] = None
    freight_inventory_fob: Optional[float] = None
    total: Optional[float] = None

class POBatubaraResponse(POBatubaraCreate):
    id: str
    created_at: str
    created_by: Optional[str] = None

# Merit Order Model
class MeritOrderCreate(BaseModel):
    periode: Optional[str] = None
    periode_year: Optional[int] = None
    periode_month: Optional[int] = None
    pemasok: Optional[str] = None
    moda: Optional[str] = None  # Tongkang, Trucking, Vessel
    tipikal_kcal_kg: Optional[float] = None
    jenis_kontrak: Optional[str] = None  # CIF, CFR, FOB
    harga_batubara: Optional[float] = None  # RP/Ton
    harga_freight: Optional[float] = None  # RP/Ton
    harga_cif: Optional[float] = None  # RP/Ton
    rp_kg: Optional[float] = None
    rp_kcal: Optional[float] = None

class MeritOrderResponse(MeritOrderCreate):
    id: str
    created_at: str
    created_by: Optional[str] = None

# ==================== VESSEL TNY ROUTES ====================

@api_router.post("/vessels", response_model=VesselTNYResponse)
async def create_vessel(data: VesselTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    vessel_id = str(uuid.uuid4())
    vessel_doc = {
        "id": vessel_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    await db.vessels.insert_one(vessel_doc)
    vessel_doc.pop("_id", None)
    return VesselTNYResponse(**vessel_doc)

@api_router.get("/vessels")
async def get_vessels(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50000),
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = build_rekap_query(
        search=search,
        search_fields=["shipment_code", "name_of_vessel", "suppliers"],
        supplier=supplier,
        date_from=date_from,
        date_to=date_to,
        date_field="time_arrival",
    )
    
    # Server-side pagination
    skip = (page - 1) * page_size
    total = await db.vessels.count_documents(query)
    vessels = await db.vessels.find(query, {"_id": 0}).sort([
        ("time_arrival", -1),
        ("completed_unloading", -1),
        ("created_at", -1),
    ]).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "items": vessels,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@api_router.get("/vessels/{vessel_id}", response_model=VesselTNYResponse)
async def get_vessel(vessel_id: str, user: dict = Depends(get_current_user)):
    vessel = await db.vessels.find_one({"id": vessel_id}, {"_id": 0})
    if not vessel:
        raise HTTPException(status_code=404, detail="Data vessel tidak ditemukan")
    return VesselTNYResponse(**vessel)

@api_router.put("/vessels/{vessel_id}", response_model=VesselTNYResponse)
async def update_vessel(vessel_id: str, data: VesselTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.vessels.update_one({"id": vessel_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Data vessel tidak ditemukan")
    vessel = await db.vessels.find_one({"id": vessel_id}, {"_id": 0})
    return VesselTNYResponse(**vessel)

@api_router.delete("/vessels/{vessel_id}")
async def delete_vessel(vessel_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.vessels.delete_one({"id": vessel_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data vessel tidak ditemukan")
    return {"message": "Data vessel berhasil dihapus"}

@api_router.delete("/vessels")
async def delete_all_vessels(user: dict = Depends(require_role(["admin"]))):
    result = await db.vessels.delete_many({})
    return {"message": f"Berhasil menghapus {result.deleted_count} data vessel", "count": result.deleted_count}

# ==================== BARGE TNY ROUTES ====================

@api_router.post("/barges", response_model=BargeTNYResponse)
async def create_barge(data: BargeTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    barge_id = str(uuid.uuid4())
    barge_doc = {
        "id": barge_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    await db.barges.insert_one(barge_doc)
    barge_doc.pop("_id", None)
    return BargeTNYResponse(**barge_doc)

@api_router.get("/barges")
async def get_barges(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50000),
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = build_rekap_query(
        search=search,
        search_fields=["shipment_code", "name_of_barge", "suppliers"],
        supplier=supplier,
        date_from=date_from,
        date_to=date_to,
        date_field="ta",
    )
    
    skip = (page - 1) * page_size
    total = await db.barges.count_documents(query)
    barges = await db.barges.find(query, {"_id": 0}).sort([
        ("ta", -1),
        ("completed_unloading", -1),
        ("created_at", -1),
    ]).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "items": barges,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@api_router.get("/barges/{barge_id}", response_model=BargeTNYResponse)
async def get_barge(barge_id: str, user: dict = Depends(get_current_user)):
    barge = await db.barges.find_one({"id": barge_id}, {"_id": 0})
    if not barge:
        raise HTTPException(status_code=404, detail="Data barge tidak ditemukan")
    return BargeTNYResponse(**barge)

@api_router.put("/barges/{barge_id}", response_model=BargeTNYResponse)
async def update_barge(barge_id: str, data: BargeTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.barges.update_one({"id": barge_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Data barge tidak ditemukan")
    barge = await db.barges.find_one({"id": barge_id}, {"_id": 0})
    return BargeTNYResponse(**barge)

@api_router.delete("/barges/{barge_id}")
async def delete_barge(barge_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.barges.delete_one({"id": barge_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data barge tidak ditemukan")
    return {"message": "Data barge berhasil dihapus"}

@api_router.delete("/barges")
async def delete_all_barges(user: dict = Depends(require_role(["admin"]))):
    result = await db.barges.delete_many({})
    return {"message": f"Berhasil menghapus {result.deleted_count} data barge", "count": result.deleted_count}

# ==================== TRUCKING TNY ROUTES ====================

@api_router.post("/trucking", response_model=TruckingTNYResponse)
async def create_trucking(data: TruckingTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    trucking_id = str(uuid.uuid4())
    trucking_doc = {
        "id": trucking_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    await db.trucking.insert_one(trucking_doc)
    trucking_doc.pop("_id", None)
    return TruckingTNYResponse(**trucking_doc)

@api_router.get("/trucking")
async def get_trucking(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50000),
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = build_rekap_query(
        search=search,
        search_fields=["shipment_code", "no_truck", "suppliers"],
        supplier=supplier,
        date_from=date_from,
        date_to=date_to,
        date_field="ta",
    )
    
    skip = (page - 1) * page_size
    total = await db.trucking.count_documents(query)
    trucking_list = await db.trucking.find(query, {"_id": 0}).sort([
        ("ta", -1),
        ("completed_unloading", -1),
        ("created_at", -1),
    ]).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "items": trucking_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@api_router.get("/trucking/{trucking_id}", response_model=TruckingTNYResponse)
async def get_trucking_item(trucking_id: str, user: dict = Depends(get_current_user)):
    trucking = await db.trucking.find_one({"id": trucking_id}, {"_id": 0})
    if not trucking:
        raise HTTPException(status_code=404, detail="Data trucking tidak ditemukan")
    return TruckingTNYResponse(**trucking)

@api_router.put("/trucking/{trucking_id}", response_model=TruckingTNYResponse)
async def update_trucking(trucking_id: str, data: TruckingTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.trucking.update_one({"id": trucking_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Data trucking tidak ditemukan")
    trucking = await db.trucking.find_one({"id": trucking_id}, {"_id": 0})
    return TruckingTNYResponse(**trucking)

@api_router.delete("/trucking/{trucking_id}")
async def delete_trucking(trucking_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.trucking.delete_one({"id": trucking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data trucking tidak ditemukan")
    return {"message": "Data trucking berhasil dihapus"}

@api_router.delete("/trucking")
async def delete_all_trucking(user: dict = Depends(require_role(["admin"]))):
    result = await db.trucking.delete_many({})
    return {"message": f"Berhasil menghapus {result.deleted_count} data trucking", "count": result.deleted_count}

# ==================== BIOMASSA TNY ROUTES ====================

@api_router.post("/biomassa", response_model=BiomassaTNYResponse)
async def create_biomassa(data: BiomassaTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    biomassa_id = str(uuid.uuid4())
    biomassa_doc = {
        "id": biomassa_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    await db.biomassa.insert_one(biomassa_doc)
    biomassa_doc.pop("_id", None)
    return BiomassaTNYResponse(**biomassa_doc)

@api_router.get("/biomassa")
async def get_biomassa(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50000),
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = build_rekap_query(
        search=search,
        search_fields=["shipment_code", "suppliers", "biomass_type"],
        supplier=supplier,
        date_from=date_from,
        date_to=date_to,
        date_field="ta",
    )
    
    skip = (page - 1) * page_size
    total = await db.biomassa.count_documents(query)
    biomassa_list = await db.biomassa.find(query, {"_id": 0}).sort([
        ("ta", -1),
        ("completed_unloading", -1),
        ("periode", -1),
        ("created_at", -1),
    ]).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "items": biomassa_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@api_router.get("/biomassa/{biomassa_id}", response_model=BiomassaTNYResponse)
async def get_biomassa_item(biomassa_id: str, user: dict = Depends(get_current_user)):
    biomassa = await db.biomassa.find_one({"id": biomassa_id}, {"_id": 0})
    if not biomassa:
        raise HTTPException(status_code=404, detail="Data biomassa tidak ditemukan")
    return BiomassaTNYResponse(**biomassa)

@api_router.put("/biomassa/{biomassa_id}", response_model=BiomassaTNYResponse)
async def update_biomassa(biomassa_id: str, data: BiomassaTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.biomassa.update_one({"id": biomassa_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Data biomassa tidak ditemukan")
    biomassa = await db.biomassa.find_one({"id": biomassa_id}, {"_id": 0})
    return BiomassaTNYResponse(**biomassa)

@api_router.delete("/biomassa/{biomassa_id}")
async def delete_biomassa(biomassa_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.biomassa.delete_one({"id": biomassa_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data biomassa tidak ditemukan")
    return {"message": "Data biomassa berhasil dihapus"}

@api_router.delete("/biomassa")
async def delete_all_biomassa(user: dict = Depends(require_role(["admin"]))):
    result = await db.biomassa.delete_many({})
    return {"message": f"Berhasil menghapus {result.deleted_count} data biomassa", "count": result.deleted_count}

# ==================== EXCEL UPLOAD ROUTES ====================

@api_router.post("/upload/vessel")
async def upload_vessel_excel(file: UploadFile = File(...), user: dict = Depends(require_role(["admin", "operator"]))):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        def safe_float(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return float(val)
            except:
                return None
        
        def safe_str(val):
            if pd.isna(val) or val is None:
                return ""
            return str(val).strip()
        
        records = []
        for _, row in df.iterrows():
            vessel_id = str(uuid.uuid4())
            vessel_doc = {
                "id": vessel_id,
                # Informasi Shipment
                "periode_ta": safe_str(row.get("Periode TA (Rakor)")),
                "periode_realisasi": safe_str(row.get("Periode Realisasi")),
                "shipment_code": safe_str(row.get("Shipment Code")),
                "voyage_code": safe_str(row.get("Voyage Code")),
                "suppliers": safe_str(row.get("Suppliers")),
                "voyage": safe_str(row.get("Voyage")),
                "name_of_vessel": safe_str(row.get("Name Of Vessel")),
                "coal_from": safe_str(row.get("Coal From")),
                # Waktu Operasional
                "time_arrival": safe_str(row.get("Time Arrival")),
                "berthed_time": safe_str(row.get("Berthed Time")),
                "commenced_unloading": safe_str(row.get("Commenced Unloading")),
                "completed_unloading": safe_str(row.get("Completed Unloading")),
                "durasi_pembongkaran_hari": safe_float(row.get("Durasi Pembongkaran (Hari)")),
                "durasi_pembongkaran_jam": safe_float(row.get("Durasi Pembongkaran (Jam)")),
                "waktu_tunggu_jam": safe_float(row.get("waktu tunggu (Jam)")),
                # Muatan
                "bl_mt": safe_float(row.get("B/L (MT)")),
                "ds_mt": safe_float(row.get("DS (MT)")),
                # COW
                "no_cow": safe_str(row.get("NO.COW")),
                "tgl_terbit_cow": safe_str(row.get("Tgl Terbit COW")),
                # Kualitas - GCV (handle multi-line headers)
                "gcv_arb": safe_float(row.get("GCV (Kcal/Kg)\nARB", row.get("GCV (Kcal/Kg) ARB"))),
                "gcv_adb": safe_float(row.get("GCV (Kcal/Kg)\nADB", row.get("GCV (Kcal/Kg) ADB"))),
                "gcv_db": safe_float(row.get("GCV (Kcal/Kg)\nDB", row.get("GCV (Kcal/Kg) DB"))),
                # Kualitas - Moisture
                "tm_arb": safe_float(row.get("TM (%wt)\nARB", row.get("TM (%wt) ARB"))),
                "im_adb": safe_float(row.get("IM (%wt) \nADB", row.get("IM (%wt) ADB"))),
                # Kualitas - Ash Content
                "ash_arb": safe_float(row.get("Ash \nContent (%wt) \nARB", row.get("Ash Content (%wt) ARB"))),
                "ash_adb": safe_float(row.get("Ash \nContent (%wt)\nADB", row.get("Ash Content (%wt) ADB"))),
                "ash_db": safe_float(row.get("Ash \nContent (%wt)\nDB", row.get("Ash Content (%wt) DB"))),
                # Kualitas - VM & FC
                "vm_arb": safe_float(row.get("VM (%wt)\nARB", row.get("VM (%wt) ARB"))),
                "vm_adb": safe_float(row.get("VM (%wt)\nADB", row.get("VM (%wt) ADB"))),
                "fc_arb": safe_float(row.get("FC (%wt)\nARB", row.get("FC (%wt) ARB"))),
                "fc_adb": safe_float(row.get("FC (%wt)\nADB", row.get("FC (%wt) ADB"))),
                # Kualitas - Sulfur
                "ts_arb": safe_float(row.get("Total Sulphur (%wt)\nARB", row.get("Total Sulphur (%wt) ARB"))),
                "ts_adb": safe_float(row.get("Total Sulphur (%wt)\nADB", row.get("Total Sulphur (%wt) ADB"))),
                "ts_db": safe_float(row.get("Total Sulphur (%wt)\nDB", row.get("Total Sulphur (%wt) DB"))),
                "ts_dafb": safe_float(row.get("Total Sulphur (%wt)\nDAFB", row.get("Total Sulphur (%wt) DAFB"))),
                # Ultimate Analysis
                "c_arb": safe_float(row.get("C (%wt)\nARB", row.get("C (%wt) ARB"))),
                "c_adb": safe_float(row.get("C (%wt)\nADB", row.get("C (%wt) ADB"))),
                "h_arb": safe_float(row.get("H (%wt)\nARB", row.get("H (%wt) ARB"))),
                "h_adb": safe_float(row.get("H (%wt)\nADB", row.get("H (%wt) ADB"))),
                "n_arb": safe_float(row.get("N (%wt)\nARB", row.get("N (%wt) ARB"))),
                "n_adb": safe_float(row.get("N (%wt)\nADB", row.get("N (%wt) ADB"))),
                "n_dafb": safe_float(row.get("N (%wt)\nDAFB", row.get("N (%wt) DAFB"))),
                "o_arb": safe_float(row.get("O (%wt)\nARB", row.get("O (%wt) ARB"))),
                "o_adb": safe_float(row.get("O (%wt)\nADB", row.get("O (%wt) ADB"))),
                # HGI & Index
                "hgi": safe_float(row.get("HGI (Point Index)")),
                "slagging_index": safe_str(row.get("Slagging (Index)")),
                "fouling_index": safe_str(row.get("Fouling (Index)")),
                "idt_reducing": safe_float(row.get("IDT Reducing (C°)")),
                # Ash Composition
                "sio2_db": safe_float(row.get("SiO2 (%DB)")),
                "al2o3_db": safe_float(row.get("Al2O3 (%DB)")),
                "tio2_db": safe_float(row.get("TiO2 (%DB)")),
                "fe2o3_db": safe_float(row.get("Fe2O3 (%DB)")),
                "cao_db": safe_float(row.get("CaO (%DB)")),
                "mgo_db": safe_float(row.get("MgO (%DB)")),
                "k2o_db": safe_float(row.get("K2O (%DB)")),
                "na2o_db": safe_float(row.get("Na2O (%DB)")),
                "so3_db": safe_float(row.get("SO3 (%DB)")),
                "p2o5_db": safe_float(row.get("P2O5 (%DB)")),
                "mno2_db": safe_float(row.get("MnO2 (%DB)")),
                "mn3o4_db": safe_float(row.get("Mn3O4 (%DB)")),
                # Size Analysis
                "size_70mm": safe_float(row.get("< 70 mm (%wt)")),
                "size_50mm": safe_float(row.get("< 50 mm (%wt)")),
                "size_32mm": safe_float(row.get("< 32 mm (%wt)")),
                "size_2_38mm": safe_float(row.get("< 2,38 mm (%wt)")),
                # COA
                "no_coa": safe_str(row.get("NO. COA")),
                "tgl_terbit_coa": safe_str(row.get("Tgl Terbit COA")),
                "durasi_terbit_coa": safe_str(row.get("DURASI TERBIT COA")),
                # Metadata
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user["id"]
            }
            records.append(vessel_doc)
        
        if records:
            await db.vessels.insert_many(records)
        
        return {"message": f"Berhasil mengimport {len(records)} data vessel", "count": len(records)}
    except Exception as e:
        logger.error(f"Error uploading vessel excel: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file: {str(e)}")

@api_router.post("/upload/barge")
async def upload_barge_excel(file: UploadFile = File(...), user: dict = Depends(require_role(["admin", "operator"]))):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        def safe_float(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return float(val)
            except:
                return None
        
        def safe_str(val):
            if pd.isna(val) or val is None:
                return ""
            return str(val).strip()
        
        records = []
        for _, row in df.iterrows():
            barge_id = str(uuid.uuid4())
            barge_doc = {
                "id": barge_id,
                # Informasi Shipment
                "periode": safe_str(row.get("Periode")),
                "shipment_code": safe_str(row.get("Shipment Code")),
                "voyage_code": safe_str(row.get("Voyage Code")),
                "shipment": safe_str(row.get("Shipment")),
                "suppliers": safe_str(row.get("Suppliers")),
                "voyage": safe_str(row.get("Voyage")),
                "tb": safe_str(row.get("TB")),
                "bg": safe_str(row.get("BG")),
                "coal_from": safe_str(row.get("Coal From")),
                # Waktu Operasional
                "ta": safe_str(row.get("TA")),
                "berthed_time": safe_str(row.get("Berthed Time")),
                "commenced_unloading": safe_str(row.get("Commenced Unloading")),
                "completed_unloading": safe_str(row.get("Completed Unloading")),
                "durasi_pembongkaran_hari": safe_float(row.get("Durasi Pembongkaran (Hari)")),
                "durasi_pembongkaran_jam": safe_float(row.get("Durasi Pembongkaran (Jam)")),
                "waktu_tunggu_jam": safe_float(row.get("waktu tunggu (Jam)")),
                # Muatan
                "bl_mt": safe_float(row.get("B/L (MT)")),
                "ds_mt": safe_float(row.get("DS (MT)")),
                # COW
                "no_cow": safe_str(row.get("NO.COW")),
                "tgl_terbit_cow": safe_str(row.get("Tgl Terbit COW")),
                # Kualitas - GCV
                "gcv_arb": safe_float(row.get("GCV (Kcal/Kg)\nARB", row.get("GCV (Kcal/Kg) ARB"))),
                "gcv_adb": safe_float(row.get("GCV (Kcal/Kg)\nADB", row.get("GCV (Kcal/Kg) ADB"))),
                "gcv_db": safe_float(row.get("GCV (Kcal/Kg)\nDB", row.get("GCV (Kcal/Kg) DB"))),
                # Kualitas - Moisture
                "tm_arb": safe_float(row.get("TM (%wt)\nARB", row.get("TM (%wt) ARB"))),
                "im_adb": safe_float(row.get("IM (%wt) \nADB", row.get("IM (%wt) ADB"))),
                # Kualitas - Ash Content
                "ash_arb": safe_float(row.get("Ash \nContent (%wt) \nARB", row.get("Ash Content (%wt) ARB"))),
                "ash_adb": safe_float(row.get("Ash \nContent (%wt)\nADB", row.get("Ash Content (%wt) ADB"))),
                "ash_db": safe_float(row.get("Ash \nContent (%wt)\nDB", row.get("Ash Content (%wt) DB"))),
                # Kualitas - VM & FC
                "vm_arb": safe_float(row.get("VM (%wt)\nARB")), "vm_adb": safe_float(row.get("VM (%wt)\nADB")),
                "fc_arb": safe_float(row.get("FC (%wt)\nARB")), "fc_adb": safe_float(row.get("FC (%wt)\nADB")),
                # Kualitas - Sulfur
                "ts_arb": safe_float(row.get("Total Sulphur (%wt)\nARB")),
                "ts_adb": safe_float(row.get("Total Sulphur (%wt)\nADB")),
                "ts_db": safe_float(row.get("Total Sulphur (%wt)\nDB")),
                "ts_dafb": safe_float(row.get("Total Sulphur (%wt)\nDAFB")),
                # Ultimate Analysis
                "c_arb": safe_float(row.get("C (%wt)\nARB")), "c_adb": safe_float(row.get("C (%wt)\nADB")),
                "h_arb": safe_float(row.get("H (%wt)\nARB")), "h_adb": safe_float(row.get("H (%wt)\nADB")),
                "n_arb": safe_float(row.get("N (%wt)\nARB")), "n_adb": safe_float(row.get("N (%wt)\nADB")),
                "n_dafb": safe_float(row.get("N (%wt)\nDAFB")),
                "o_arb": safe_float(row.get("O (%wt)\nARB")), "o_adb": safe_float(row.get("O (%wt)\nADB")),
                # HGI & Index
                "hgi": safe_float(row.get("HGI (Point Index)")),
                "slagging_index": safe_str(row.get("Slagging (Index)")),
                "fouling_index": safe_str(row.get("Fouling (Index)")),
                "idt_reducing": safe_float(row.get("IDT Reducing (C°)")),
                # Ash Composition
                "sio2_db": safe_float(row.get("SiO2 (%DB)")), "al2o3_db": safe_float(row.get("Al2O3 (%DB)")),
                "tio2_db": safe_float(row.get("TiO2 (%DB)")), "fe2o3_db": safe_float(row.get("Fe2O3 (%DB)")),
                "cao_db": safe_float(row.get("CaO (%DB)")), "mgo_db": safe_float(row.get("MgO (%DB)")),
                "k2o_db": safe_float(row.get("K2O (%DB)")), "na2o_db": safe_float(row.get("Na2O (%DB)")),
                "so3_db": safe_float(row.get("SO3 (%DB)")), "p2o5_db": safe_float(row.get("P2O5 (%DB)")),
                "mno2_db": safe_float(row.get("MnO2 (%DB)")), "mn3o4_db": safe_float(row.get("Mn3O4 (%DB)")),
                # Size Analysis
                "size_70mm": safe_float(row.get("< 70 mm (%wt)")), "size_50mm": safe_float(row.get("< 50 mm (%wt)")),
                "size_32mm": safe_float(row.get("< 32 mm (%wt)")), "size_2_38mm": safe_float(row.get("< 2,38 mm (%wt)")),
                # COA
                "no_coa": safe_str(row.get("NO. COA")),
                "tgl_terbit_coa": safe_str(row.get("Tgl Terbit COA")),
                "durasi_terbit_coa": safe_str(row.get("DURASI TERBIT COA")),
                # Metadata
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user["id"]
            }
            records.append(barge_doc)
        
        if records:
            await db.barges.insert_many(records)
        
        return {"message": f"Berhasil mengimport {len(records)} data barge", "count": len(records)}
    except Exception as e:
        logger.error(f"Error uploading barge excel: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file: {str(e)}")

@api_router.post("/upload/trucking")
async def upload_trucking_excel(file: UploadFile = File(...), user: dict = Depends(require_role(["admin", "operator"]))):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        def safe_float(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return float(val)
            except:
                return None
        
        def safe_str(val):
            if pd.isna(val) or val is None:
                return ""
            return str(val).strip()
        
        def safe_int(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return int(float(val))
            except:
                return None
        
        records = []
        for _, row in df.iterrows():
            trucking_id = str(uuid.uuid4())
            trucking_doc = {
                "id": trucking_id,
                # Informasi Shipment
                "periode_ta": safe_str(row.get("Periode TA (Rakor)")),
                "periode_realisasi": safe_str(row.get("Periode Realisasi")),
                "shipment_code": safe_str(row.get("Shipment Code")),
                "voyage_code": safe_str(row.get("Voyage Code")),
                "shipment": safe_str(row.get("Shipment")),
                "suppliers": safe_str(row.get("Suppliers")),
                "transportasi": safe_str(row.get("Transportasi")),
                "coal_from": safe_str(row.get("Coal From")),
                # Waktu Operasional
                "ta": safe_str(row.get("TA")),
                "berthed_time": safe_str(row.get("Berthed Time")),
                "commenced_unloading": safe_str(row.get("Commenced Unloading")),
                "completed_unloading": safe_str(row.get("Completed Unloading")),
                "durasi_pembongkaran_hari": safe_float(row.get("Durasi Pembongkaran (Hari)")),
                "durasi_pembongkaran_jam": safe_float(row.get("Durasi Pembongkaran (Jam)")),
                # Muatan
                "bl_mt": safe_float(row.get("B/L (MT)")),
                "ds_mt": safe_float(row.get("DS (MT)")),
                "rit": safe_int(row.get("RIT")),
                # COW
                "no_cow": safe_str(row.get("NO.COW")),
                "tgl_terbit_cow": safe_str(row.get("Tgl Terbit COW")),
                # Kualitas - GCV
                "gcv_arb": safe_float(row.get("GCV (Kcal/Kg)\nARB", row.get("GCV (Kcal/Kg) ARB"))),
                "gcv_adb": safe_float(row.get("GCV (Kcal/Kg)\nADB", row.get("GCV (Kcal/Kg) ADB"))),
                "gcv_db": safe_float(row.get("GCV (Kcal/Kg)\nDB", row.get("GCV (Kcal/Kg) DB"))),
                # Kualitas - Moisture
                "tm_arb": safe_float(row.get("TM (%wt)\nARB", row.get("TM (%wt) ARB"))),
                "im_adb": safe_float(row.get("IM (%wt) \nADB", row.get("IM (%wt) ADB"))),
                # Kualitas - Ash Content
                "ash_arb": safe_float(row.get("Ash \nContent (%wt) \nARB")),
                "ash_adb": safe_float(row.get("Ash \nContent (%wt)\nADB")),
                "ash_db": safe_float(row.get("Ash \nContent (%wt)\nDB")),
                # Kualitas - VM & FC
                "vm_arb": safe_float(row.get("VM (%wt)\nARB")), "vm_adb": safe_float(row.get("VM (%wt)\nADB")),
                "fc_arb": safe_float(row.get("FC (%wt)\nARB")), "fc_adb": safe_float(row.get("FC (%wt)\nADB")),
                # Kualitas - Sulfur
                "ts_arb": safe_float(row.get("Total Sulphur (%wt)\nARB")),
                "ts_adb": safe_float(row.get("Total Sulphur (%wt)\nADB")),
                "ts_db": safe_float(row.get("Total Sulphur (%wt)\nDB")),
                "ts_dafb": safe_float(row.get("Total Sulphur (%wt)\nDAFB")),
                # Ultimate Analysis
                "c_arb": safe_float(row.get("C (%wt)\nARB")), "c_adb": safe_float(row.get("C (%wt)\nADB")),
                "h_arb": safe_float(row.get("H (%wt)\nARB")), "h_adb": safe_float(row.get("H (%wt)\nADB")),
                "n_arb": safe_float(row.get("N (%wt)\nARB")), "n_adb": safe_float(row.get("N (%wt)\nADB")),
                "n_dafb": safe_float(row.get("N (%wt)\nDAFB")),
                "o_arb": safe_float(row.get("O (%wt)\nARB")), "o_adb": safe_float(row.get("O (%wt)\nADB")),
                # HGI & Index
                "hgi": safe_float(row.get("HGI (Point Index)")),
                "slagging_index": safe_str(row.get("Slagging (Index)")),
                "fouling_index": safe_str(row.get("Fouling (Index)")),
                "idt_reducing": safe_float(row.get("IDT Reducing (C°)")),
                # Ash Composition
                "sio2_db": safe_float(row.get("SiO2 (%DB)")), "al2o3_db": safe_float(row.get("Al2O3 (%DB)")),
                "tio2_db": safe_float(row.get("TiO2 (%DB)")), "fe2o3_db": safe_float(row.get("Fe2O3 (%DB)")),
                "cao_db": safe_float(row.get("CaO (%DB)")), "mgo_db": safe_float(row.get("MgO (%DB)")),
                "k2o_db": safe_float(row.get("K2O (%DB)")), "na2o_db": safe_float(row.get("Na2O (%DB)")),
                "so3_db": safe_float(row.get("SO3 (%DB)")), "p2o5_db": safe_float(row.get("P2O5 (%DB)")),
                "mno2_db": safe_float(row.get("MnO2 (%DB)")), "mn3o4_db": safe_float(row.get("Mn3O4 (%DB)")),
                # Size Analysis
                "size_70mm": safe_float(row.get("< 70 mm (%wt)")), "size_50mm": safe_float(row.get("< 50 mm (%wt)")),
                "size_32mm": safe_float(row.get("< 32 mm (%wt)")), "size_2_38mm": safe_float(row.get("< 2,38 mm (%wt)")),
                # COA
                "no_coa": safe_str(row.get("NO. COA")),
                "tgl_terbit_coa": safe_str(row.get("Tgl Terbit COA")),
                # Metadata
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user["id"]
            }
            records.append(trucking_doc)
        
        if records:
            await db.trucking.insert_many(records)
        
        return {"message": f"Berhasil mengimport {len(records)} data trucking", "count": len(records)}
    except Exception as e:
        logger.error(f"Error uploading trucking excel: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file: {str(e)}")

@api_router.post("/upload/biomassa")
async def upload_biomassa_excel(file: UploadFile = File(...), user: dict = Depends(require_role(["admin", "operator"]))):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Clean column names - remove newlines and extra spaces
        df.columns = df.columns.str.replace('\n', ' ').str.strip()
        
        def safe_float(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return float(val)
            except:
                return None
        
        def safe_str(val):
            if pd.isna(val) or val is None:
                return ""
            return str(val).strip()
        
        records = []
        for _, row in df.iterrows():
            biomassa_id = str(uuid.uuid4())
            biomassa_doc = {
                "id": biomassa_id,
                # Informasi Shipment
                "periode": safe_str(row.get("Periode")),
                "shipment_code": safe_str(row.get("Shipment Code")),
                "voyage_code": safe_str(row.get("Voyage Code")),
                "lot": safe_str(row.get("Lot")),
                "suppliers": safe_str(row.get("Suppliers")),
                "shipper": safe_str(row.get("Shipper")),
                "lot_1": safe_str(row.get("Lot.1")),
                "tb": safe_str(row.get("TB")),
                "bg": safe_str(row.get("BG")),
                "biomass_type": safe_str(row.get("Biomass", row.get("Biomass "))),
                # Waktu Operasional
                "ta": safe_str(row.get("TA")),
                "berthed_time": safe_str(row.get("Berthed Time")),
                "commenced_unloading": safe_str(row.get("Commenced Unloading")),
                "completed_unloading": safe_str(row.get("Completed Unloading")),
                "durasi_pembongkaran_hari": safe_float(row.get("Durasi Pembongkaran (Hari)")),
                # Muatan
                "bl_mt": safe_float(row.get("B/L (MT)")),
                "jembatan_timbang_mt": safe_float(row.get("Jembatan Timbang (MT)")),
                "surveyor_unloading": safe_str(row.get("Surveyor Unloading", row.get(" Surveyor Unloading "))),
                # COW/ROW
                "no_cow_row": safe_str(row.get("NO.COW / ROW")),
                "tgl_terbit_cow": safe_str(row.get("Tgl Terbit COW")),
                "lama_terbit_row": safe_float(row.get("Lama terbit Row")),
                # Kualitas - handle column names with newlines converted to spaces
                "gcv_arb": safe_float(row.get("GCV (Kcal/Kg) ARB")),
                "gcv_adb": safe_float(row.get("GCV (Kcal/Kg) ADB")),
                "tm_arb": safe_float(row.get("TM (%wt) ARB")),
                "im_adb": safe_float(row.get("IM (%wt)  ADB", row.get("IM (%wt) ADB"))),
                # COA
                "no_coa": safe_str(row.get("NO. COA")),
                "tgl_terbit_coa": safe_str(row.get("Tgl Terbit COA")),
                "durasi_pembongkaran_hari_2": safe_float(row.get("Durasi Pembongkaran (Hari).1")),
                "waktu_tunggu_jam": safe_float(row.get("Waktu Tunggu (Jam)")),
                "durasi_terbit_coa": safe_float(row.get("DURASI TERBIT COA")),
                # Metadata
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user["id"]
            }
            records.append(biomassa_doc)
        
        if records:
            await db.biomassa.insert_many(records)
        
        return {"message": f"Berhasil mengimport {len(records)} data biomassa", "count": len(records)}
    except Exception as e:
        logger.error(f"Error uploading biomassa excel: {e}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file: {str(e)}")

# ==================== SUPPLIERS LIST ====================

@api_router.get("/suppliers")
async def get_suppliers_list(user: dict = Depends(get_current_user)):
    """Get unique list of suppliers from all data sources"""
    suppliers_set = set()
    
    # Get suppliers from vessels
    vessel_suppliers = await db.vessels.distinct("suppliers")
    for s in vessel_suppliers:
        if s:
            suppliers_set.add(s)
    
    # Get suppliers from barges
    barge_suppliers = await db.barges.distinct("suppliers")
    for s in barge_suppliers:
        if s:
            suppliers_set.add(s)
    
    # Get suppliers from trucking
    trucking_suppliers = await db.trucking.distinct("suppliers")
    for s in trucking_suppliers:
        if s:
            suppliers_set.add(s)
    
    # Get suppliers from biomassa
    biomassa_suppliers = await db.biomassa.distinct("suppliers")
    for s in biomassa_suppliers:
        if s:
            suppliers_set.add(s)
    
    # Get suppliers from PO Batubara
    po_suppliers = await db.po_batubara.distinct("supplier_name")
    for s in po_suppliers:
        if s:
            suppliers_set.add(s)
    
    # Get pemasok from Merit Order
    merit_suppliers = await db.merit_order.distinct("pemasok")
    for s in merit_suppliers:
        if s:
            suppliers_set.add(s)
    
    # Sort alphabetically
    suppliers_list = sorted(list(suppliers_set))
    
    return {
        "suppliers": suppliers_list,
        "total": len(suppliers_list)
    }

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "PLTU Tenayan Fuel Management System API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@api_router.get("/health/version")
async def health_version_check():
    return await build_public_version_status()

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
