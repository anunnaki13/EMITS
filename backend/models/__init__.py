# Backend Models - Pydantic schemas
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any, Dict

# ==================== AUTH MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "operator"

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

# ==================== COA MODELS ====================

class COASettingsUpdate(BaseModel):
    price_per_kcal_per_ton: float

class UmpireProposal(BaseModel):
    reconciliation_id: str
    sample_number: str
    notes: Optional[str] = None

class UmpireResultInput(BaseModel):
    reconciliation_id: str
    umpire_gcv_arb: float
    umpire_tm_arb: Optional[float] = None
    umpire_ash_arb: Optional[float] = None
    umpire_ts_arb: Optional[float] = None
    umpire_lab_name: str
    umpire_result_date: str
    notes: Optional[str] = None

class DisputeNoteInput(BaseModel):
    note: str
    visibility: str = "internal"

class DisputeAttachmentInput(BaseModel):
    filename: str
    url: Optional[str] = None
    description: Optional[str] = None

class DisputeCloseInput(BaseModel):
    resolution: str
    closure_notes: Optional[str] = None

class COAManualInput(BaseModel):
    shipment: str
    suppliers: str
    periode: Optional[str] = None
    tb: Optional[str] = None
    bg: Optional[str] = None
    ds_mt: Optional[float] = None
    completed_unloading: Optional[str] = None
    loading_gcv_arb: Optional[float] = None
    loading_tm_arb: Optional[float] = None
    loading_ash_arb: Optional[float] = None
    loading_ts_arb: Optional[float] = None
    unloading_gcv_arb: Optional[float] = None
    unloading_tm_arb: Optional[float] = None
    unloading_ash_arb: Optional[float] = None
    unloading_ts_arb: Optional[float] = None
    internal_gcv_arb: Optional[float] = None
    internal_tm_arb: Optional[float] = None
    internal_ash_arb: Optional[float] = None
    internal_ts_arb: Optional[float] = None

# ==================== VESSEL MODELS ====================

class VesselTNYCreate(BaseModel):
    periode_ta: str
    periode_realisasi: str
    shipment_code: str
    voyage_code: str
    suppliers: str
    voyage: str
    name_of_vessel: str
    coal_from: str
    time_arrival: Optional[str] = None
    berthed_time: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    durasi_pembongkaran_hari: Optional[float] = None
    durasi_pembongkaran_jam: Optional[float] = None
    waktu_tunggu_jam: Optional[float] = None
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    no_cow: Optional[str] = None
    tgl_terbit_cow: Optional[str] = None
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    vm_db: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    fc_db: Optional[float] = None
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    hgi: Optional[float] = None
    c_adb: Optional[float] = None
    h_adb: Optional[float] = None
    o_adb: Optional[float] = None
    n_adb: Optional[float] = None
    afi: Optional[float] = None
    slagging_index: Optional[float] = None
    fouling_index: Optional[float] = None
    size_0_to_50_persen: Optional[float] = None
    size_lebih_50_persen: Optional[float] = None
    status: str = "draft"

class VesselTNYResponse(VesselTNYCreate):
    id: str
    created_at: str
    created_by: str

# ==================== BARGE MODELS ====================

class BargeTNYCreate(BaseModel):
    periode: str
    shipment_code: str
    suppliers: str
    tb: Optional[str] = None
    bg: Optional[str] = None
    ta: Optional[str] = None
    commenced_unloading: Optional[str] = None
    completed_unloading: Optional[str] = None
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    vm_db: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    fc_db: Optional[float] = None
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    hgi: Optional[float] = None
    c_adb: Optional[float] = None
    h_adb: Optional[float] = None
    o_adb: Optional[float] = None
    n_adb: Optional[float] = None
    afi: Optional[float] = None
    slagging_index: Optional[float] = None
    fouling_index: Optional[float] = None
    size_0_to_50_persen: Optional[float] = None
    size_lebih_50_persen: Optional[float] = None
    status: str = "draft"

class BargeTNYResponse(BargeTNYCreate):
    id: str
    created_at: str
    created_by: str

# ==================== TRUCKING MODELS ====================

class TruckingTNYCreate(BaseModel):
    periode_ta: str
    periode_realisasi: str
    shipment_code: str
    suppliers: str
    coal_from: Optional[str] = None
    ta: Optional[str] = None
    ds_mt: Optional[float] = None
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    ash_arb: Optional[float] = None
    ash_adb: Optional[float] = None
    ash_db: Optional[float] = None
    vm_arb: Optional[float] = None
    vm_adb: Optional[float] = None
    vm_db: Optional[float] = None
    fc_arb: Optional[float] = None
    fc_adb: Optional[float] = None
    fc_db: Optional[float] = None
    ts_arb: Optional[float] = None
    ts_adb: Optional[float] = None
    ts_db: Optional[float] = None
    hgi: Optional[float] = None
    c_adb: Optional[float] = None
    h_adb: Optional[float] = None
    o_adb: Optional[float] = None
    n_adb: Optional[float] = None
    afi: Optional[float] = None
    slagging_index: Optional[float] = None
    fouling_index: Optional[float] = None
    status: str = "draft"

class TruckingTNYResponse(TruckingTNYCreate):
    id: str
    created_at: str
    created_by: str

# ==================== BIOMASSA MODELS ====================

class BiomassaTNYCreate(BaseModel):
    periode: str
    shipment_code: str
    suppliers: str
    coal_from: Optional[str] = None
    bl_mt: Optional[float] = None
    ds_mt: Optional[float] = None
    gcv_arb: Optional[float] = None
    gcv_adb: Optional[float] = None
    gcv_db: Optional[float] = None
    tm_arb: Optional[float] = None
    im_adb: Optional[float] = None
    ash_arb: Optional[float] = None
    vm_arb: Optional[float] = None
    fc_arb: Optional[float] = None
    ts_arb: Optional[float] = None
    status: str = "draft"

class BiomassaTNYResponse(BiomassaTNYCreate):
    id: str
    created_at: str
    created_by: str

# ==================== PO BATUBARA MODELS ====================

class POBatubaraCreate(BaseModel):
    district_code: Optional[str] = None
    district_name: Optional[str] = None
    po_number: str
    supplier_name: str
    spec: Optional[str] = None
    periode: Optional[str] = None
    no_shipment: Optional[str] = None
    coal_category: Optional[str] = None
    bl_mt: Optional[float] = None
    inventory_mt: Optional[float] = None
    hba: Optional[float] = None
    inventory_price: Optional[float] = None
    price_ppl_cargo: Optional[float] = None
    tonase_po: Optional[float] = None
    nilai_po: Optional[float] = None
    harga_material_po: Optional[float] = None
    ppl_po: Optional[float] = None
    ppl_charge_po: Optional[float] = None
    status: str = "draft"

class POBatubaraResponse(POBatubaraCreate):
    id: str
    created_at: str
    created_by: str

# ==================== MERIT ORDER MODELS ====================

class MeritOrderCreate(BaseModel):
    periode: str
    periode_year: Optional[int] = None
    periode_month: Optional[int] = None
    pemasok: str
    moda: Optional[str] = None
    tipikal_kcal_kg: Optional[float] = None
    jenis_kontrak: Optional[str] = None
    harga_cif: Optional[float] = None
    rp_kcal: Optional[float] = None
    ranking: Optional[int] = None
    status: str = "draft"

class MeritOrderResponse(MeritOrderCreate):
    id: str
    created_at: str
    created_by: str

# ==================== DASHBOARD MODELS ====================

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

# ==================== SMART STOCK MODELS ====================

class SmartStockCreate(BaseModel):
    date: str
    stock_awal: float = 0.0
    suppliers: Dict[str, Any] = {}
    total_penerimaan: float = 0.0
    stock_akhir: float = 0.0

class SmartStockResponse(SmartStockCreate):
    id: str
    created_at: str
    created_by: str

class SmartStockEntry(BaseModel):
    date: str
    stock_awal: float
    suppliers: dict
    total_penerimaan: Optional[float] = 0.0

# ==================== SUMBER PEMAKAIAN MODELS ====================

class SumberPemakaianCreate(BaseModel):
    date: str
    unit1_burn: float = 0.0
    unit2_burn: float = 0.0
    unit1_details: Dict[str, Any] = {}
    unit2_details: Dict[str, Any] = {}

class SumberPemakaianResponse(SumberPemakaianCreate):
    id: str
    created_at: str
    created_by: str

class SumberPemakaianEntry(BaseModel):
    date: str
    stock_awal: float
    suppliers: dict
    total_pemakaian: Optional[float] = 0.0

# ==================== AI MODELS ====================

class AIQueryRequest(BaseModel):
    query: str
    module: str = "general"
    context: Optional[Dict[str, Any]] = None

class AIQueryResponse(BaseModel):
    response: str
    module: str
    query: str

class SmartBlendingRequest(BaseModel):
    target_gcv: float
    max_ash: float
    max_sulphur: float
    max_total_moisture: float = 35.0
    max_inherent_moisture: float = 18.0
    min_volatile_matter: float = 35.0
    min_fixed_carbon: float = 25.0
    target_quantity: float

# ==================== SETTINGS MODELS ====================

class AISettingsUpdate(BaseModel):
    custom_api_key: Optional[str] = None
    use_custom_key: bool = False
