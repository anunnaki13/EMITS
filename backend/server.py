from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import pandas as pd
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'tenayan-fuel-management-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="PLTU Tenayan Fuel Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "operator"  # admin, operator, viewer

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

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

# Trucking TNY Model
class TruckingTNYCreate(BaseModel):
    periode: str
    shipment_code: str
    suppliers: str
    no_truck: str
    driver_name: Optional[str] = None
    origin: str
    destination: str
    pickup_date: Optional[str] = None
    delivery_date: Optional[str] = None
    weight_mt: Optional[float] = None
    no_cow: Optional[str] = None
    gcv_arb: Optional[float] = None
    tm_arb: Optional[float] = None

class TruckingTNYResponse(BaseModel):
    id: str
    periode: str
    shipment_code: str
    suppliers: str
    no_truck: str
    driver_name: Optional[str] = None
    origin: str
    destination: str
    pickup_date: Optional[str] = None
    delivery_date: Optional[str] = None
    weight_mt: Optional[float] = None
    no_cow: Optional[str] = None
    gcv_arb: Optional[float] = None
    tm_arb: Optional[float] = None
    created_at: str
    created_by: Optional[str] = None

# Biomassa TNY Model
class BiomassaTNYCreate(BaseModel):
    periode: str
    shipment_code: str
    lot: str
    suppliers: str
    shipper: str
    biomass_type: str  # WOODCHIP, SAWDUST, OIL PALM MESOCARP FIBER
    berthed_time: Optional[str] = None
    commenced: Optional[str] = None
    completed: Optional[str] = None
    durasi_pembongkaran: Optional[float] = None
    jembatan_timbang_mt: Optional[float] = None
    surveyor: Optional[str] = None
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    tm_arb: Optional[float] = None
    im_arb: Optional[float] = None
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None

class BiomassaTNYResponse(BaseModel):
    id: str
    periode: str
    shipment_code: str
    lot: str
    suppliers: str
    shipper: str
    biomass_type: str
    berthed_time: Optional[str] = None
    commenced: Optional[str] = None
    completed: Optional[str] = None
    durasi_pembongkaran: Optional[float] = None
    jembatan_timbang_mt: Optional[float] = None
    surveyor: Optional[str] = None
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    tm_arb: Optional[float] = None
    im_arb: Optional[float] = None
    no_coa: Optional[str] = None
    tgl_terbit_coa: Optional[str] = None
    created_at: str
    created_by: Optional[str] = None

# Dashboard Stats Model
class DashboardStats(BaseModel):
    total_vessel: int
    total_barge: int
    total_trucking: int
    total_biomassa: int
    total_tonase_batubara: float
    total_tonase_biomassa: float
    avg_gcv: float
    recent_shipments: List[dict]
    monthly_trend: List[dict]
    supplier_stats: List[dict]

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User tidak ditemukan")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token sudah kadaluarsa")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

def require_role(allowed_roles: List[str]):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Akses ditolak")
        return user
    return role_checker

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": data.email,
        "password": hash_password(data.password),
        "name": data.name,
        "role": data.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, data.email, data.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=data.email,
            name=data.name,
            role=data.role,
            created_at=user_doc["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email atau password salah")
    
    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"]
    )

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(user: dict = Depends(require_role(["admin"]))):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

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

@api_router.get("/vessels", response_model=List[VesselTNYResponse])
async def get_vessels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"name_of_vessel": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}}
        ]
    vessels = await db.vessels.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [VesselTNYResponse(**v) for v in vessels]

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

@api_router.get("/barges", response_model=List[BargeTNYResponse])
async def get_barges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"name_of_barge": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}}
        ]
    barges = await db.barges.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [BargeTNYResponse(**b) for b in barges]

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

@api_router.get("/trucking", response_model=List[TruckingTNYResponse])
async def get_trucking(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"no_truck": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}}
        ]
    trucking_list = await db.trucking.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [TruckingTNYResponse(**t) for t in trucking_list]

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

@api_router.get("/biomassa", response_model=List[BiomassaTNYResponse])
async def get_biomassa(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}},
            {"biomass_type": {"$regex": search, "$options": "i"}}
        ]
    biomassa_list = await db.biomassa.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [BiomassaTNYResponse(**b) for b in biomassa_list]

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
        
        records = []
        for _, row in df.iterrows():
            barge_id = str(uuid.uuid4())
            barge_doc = {
                "id": barge_id,
                "periode_ta": str(row.get("Periode TA (Rakor)", "")),
                "periode_realisasi": str(row.get("Periode Realisasi", "")),
                "shipment_code": str(row.get("Shipment Code", "")),
                "voyage_code": str(row.get("Voyage Code", "")),
                "suppliers": str(row.get("Suppliers", "")),
                "voyage": str(row.get("Voyage", "")),
                "name_of_barge": str(row.get("Name Of Barge", row.get("Name Of Vessel", ""))),
                "coal_from": str(row.get("Coal From", "")),
                "bl_mt": float(row.get("B/L (MT)", 0)) if pd.notna(row.get("B/L (MT)")) else None,
                "ds_mt": float(row.get("DS (MT)", 0)) if pd.notna(row.get("DS (MT)")) else None,
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
        
        records = []
        for _, row in df.iterrows():
            trucking_id = str(uuid.uuid4())
            trucking_doc = {
                "id": trucking_id,
                "periode": str(row.get("Periode", "")),
                "shipment_code": str(row.get("Shipment Code", "")),
                "suppliers": str(row.get("Suppliers", row.get("Carrier", ""))),
                "no_truck": str(row.get("No Truck", row.get("Tractor", ""))),
                "origin": str(row.get("Origin", "")),
                "destination": str(row.get("Destination", "")),
                "weight_mt": float(row.get("Weight (MT)", 0)) if pd.notna(row.get("Weight (MT)")) else None,
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
        
        records = []
        for _, row in df.iterrows():
            biomassa_id = str(uuid.uuid4())
            biomassa_doc = {
                "id": biomassa_id,
                "periode": str(row.get("Periode", "")),
                "shipment_code": str(row.get("Shipment Code", "")),
                "lot": str(row.get("Lot", "")),
                "suppliers": str(row.get("Suppliers", "")),
                "shipper": str(row.get("Shipper", "")),
                "biomass_type": str(row.get("Biomass", row.get("Biomass Type", ""))),
                "jembatan_timbang_mt": float(row.get("Jembatan Timbang (MT)", 0)) if pd.notna(row.get("Jembatan Timbang (MT)")) else None,
                "gcv_arb": float(row.get("GCV (Kcal/Kg) ARB", 0)) if pd.notna(row.get("GCV (Kcal/Kg) ARB")) else None,
                "tm_arb": float(row.get("TM (%wt) ARB", 0)) if pd.notna(row.get("TM (%wt) ARB")) else None,
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

# ==================== DASHBOARD STATS ====================

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
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
    recent_vessels = await db.vessels.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    recent_barges = await db.barges.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    recent_shipments = []
    for v in recent_vessels:
        recent_shipments.append({"type": "vessel", "name": v.get("name_of_vessel", ""), "code": v.get("shipment_code", ""), "date": v.get("created_at", "")})
    for b in recent_barges:
        recent_shipments.append({"type": "barge", "name": b.get("name_of_barge", ""), "code": b.get("shipment_code", ""), "date": b.get("created_at", "")})
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

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "PLTU Tenayan Fuel Management System API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

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
