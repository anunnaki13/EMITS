# Data Routes - Vessels, Barges, Trucking, Biomassa with Pagination
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import pandas as pd
import io

from models import (
    VesselTNYCreate, VesselTNYResponse,
    BargeTNYCreate, BargeTNYResponse,
    TruckingTNYCreate, TruckingTNYResponse,
    BiomassaTNYCreate, BiomassaTNYResponse
)
from utils.database import db
from routers.auth import get_current_user, require_role

router = APIRouter(tags=["Data Management"])

# ==================== PAGINATION HELPER ====================

class PaginatedResponse:
    def __init__(self, items: List, total: int, page: int, page_size: int):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

async def paginate_query(collection, query: dict, page: int, page_size: int, sort_field: str = "created_at", sort_order: int = -1):
    """Server-side pagination helper"""
    skip = (page - 1) * page_size
    total = await collection.count_documents(query)
    cursor = collection.find(query, {"_id": 0}).sort(sort_field, sort_order).skip(skip).limit(page_size)
    items = await cursor.to_list(page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}

# ==================== VESSELS ====================

@router.post("/vessels", response_model=VesselTNYResponse)
async def create_vessel(data: VesselTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    vessel_doc = data.model_dump()
    vessel_doc["id"] = str(uuid.uuid4())
    vessel_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    vessel_doc["created_by"] = user["id"]
    await db.vessels.insert_one(vessel_doc)
    return VesselTNYResponse(**vessel_doc)

@router.get("/vessels")
async def get_vessels(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}},
            {"name_of_vessel": {"$regex": search, "$options": "i"}}
        ]
    return await paginate_query(db.vessels, query, page, page_size, "time_arrival")

@router.get("/vessels/{vessel_id}", response_model=VesselTNYResponse)
async def get_vessel(vessel_id: str, user: dict = Depends(get_current_user)):
    vessel = await db.vessels.find_one({"id": vessel_id}, {"_id": 0})
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return VesselTNYResponse(**vessel)

@router.put("/vessels/{vessel_id}", response_model=VesselTNYResponse)
async def update_vessel(vessel_id: str, data: VesselTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.vessels.update_one({"id": vessel_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return await get_vessel(vessel_id, user)

@router.delete("/vessels/{vessel_id}")
async def delete_vessel(vessel_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.vessels.delete_one({"id": vessel_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return {"message": "Vessel deleted"}

@router.delete("/vessels")
async def delete_all_vessels(user: dict = Depends(require_role(["admin"]))):
    result = await db.vessels.delete_many({})
    return {"message": f"Deleted {result.deleted_count} vessels"}

# ==================== BARGES ====================

@router.post("/barges", response_model=BargeTNYResponse)
async def create_barge(data: BargeTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    barge_doc = data.model_dump()
    barge_doc["id"] = str(uuid.uuid4())
    barge_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    barge_doc["created_by"] = user["id"]
    await db.barges.insert_one(barge_doc)
    return BargeTNYResponse(**barge_doc)

@router.get("/barges")
async def get_barges(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}},
            {"tb": {"$regex": search, "$options": "i"}}
        ]
    return await paginate_query(db.barges, query, page, page_size, "ta")

@router.get("/barges/{barge_id}", response_model=BargeTNYResponse)
async def get_barge(barge_id: str, user: dict = Depends(get_current_user)):
    barge = await db.barges.find_one({"id": barge_id}, {"_id": 0})
    if not barge:
        raise HTTPException(status_code=404, detail="Barge not found")
    return BargeTNYResponse(**barge)

@router.put("/barges/{barge_id}", response_model=BargeTNYResponse)
async def update_barge(barge_id: str, data: BargeTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.barges.update_one({"id": barge_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Barge not found")
    return await get_barge(barge_id, user)

@router.delete("/barges/{barge_id}")
async def delete_barge(barge_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.barges.delete_one({"id": barge_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Barge not found")
    return {"message": "Barge deleted"}

@router.delete("/barges")
async def delete_all_barges(user: dict = Depends(require_role(["admin"]))):
    result = await db.barges.delete_many({})
    return {"message": f"Deleted {result.deleted_count} barges"}

# ==================== TRUCKING ====================

@router.post("/trucking", response_model=TruckingTNYResponse)
async def create_trucking(data: TruckingTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    trucking_doc = data.model_dump()
    trucking_doc["id"] = str(uuid.uuid4())
    trucking_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    trucking_doc["created_by"] = user["id"]
    await db.trucking.insert_one(trucking_doc)
    return TruckingTNYResponse(**trucking_doc)

@router.get("/trucking")
async def get_trucking(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}},
            {"coal_from": {"$regex": search, "$options": "i"}}
        ]
    return await paginate_query(db.trucking, query, page, page_size, "ta")

@router.get("/trucking/{trucking_id}", response_model=TruckingTNYResponse)
async def get_trucking_item(trucking_id: str, user: dict = Depends(get_current_user)):
    trucking = await db.trucking.find_one({"id": trucking_id}, {"_id": 0})
    if not trucking:
        raise HTTPException(status_code=404, detail="Trucking not found")
    return TruckingTNYResponse(**trucking)

@router.put("/trucking/{trucking_id}", response_model=TruckingTNYResponse)
async def update_trucking(trucking_id: str, data: TruckingTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.trucking.update_one({"id": trucking_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trucking not found")
    return await get_trucking_item(trucking_id, user)

@router.delete("/trucking/{trucking_id}")
async def delete_trucking(trucking_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.trucking.delete_one({"id": trucking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trucking not found")
    return {"message": "Trucking deleted"}

@router.delete("/trucking")
async def delete_all_trucking(user: dict = Depends(require_role(["admin"]))):
    result = await db.trucking.delete_many({})
    return {"message": f"Deleted {result.deleted_count} trucking records"}

# ==================== BIOMASSA ====================

@router.post("/biomassa", response_model=BiomassaTNYResponse)
async def create_biomassa(data: BiomassaTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    biomassa_doc = data.model_dump()
    biomassa_doc["id"] = str(uuid.uuid4())
    biomassa_doc["created_at"] = datetime.now(timezone.utc).isoformat()
    biomassa_doc["created_by"] = user["id"]
    await db.biomassa.insert_one(biomassa_doc)
    return BiomassaTNYResponse(**biomassa_doc)

@router.get("/biomassa")
async def get_biomassa(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query["$or"] = [
            {"shipment_code": {"$regex": search, "$options": "i"}},
            {"suppliers": {"$regex": search, "$options": "i"}},
            {"coal_from": {"$regex": search, "$options": "i"}}
        ]
    return await paginate_query(db.biomassa, query, page, page_size, "periode")

@router.get("/biomassa/{biomassa_id}", response_model=BiomassaTNYResponse)
async def get_biomassa_item(biomassa_id: str, user: dict = Depends(get_current_user)):
    biomassa = await db.biomassa.find_one({"id": biomassa_id}, {"_id": 0})
    if not biomassa:
        raise HTTPException(status_code=404, detail="Biomassa not found")
    return BiomassaTNYResponse(**biomassa)

@router.put("/biomassa/{biomassa_id}", response_model=BiomassaTNYResponse)
async def update_biomassa(biomassa_id: str, data: BiomassaTNYCreate, user: dict = Depends(require_role(["admin", "operator"]))):
    result = await db.biomassa.update_one({"id": biomassa_id}, {"$set": data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Biomassa not found")
    return await get_biomassa_item(biomassa_id, user)

@router.delete("/biomassa/{biomassa_id}")
async def delete_biomassa(biomassa_id: str, user: dict = Depends(require_role(["admin"]))):
    result = await db.biomassa.delete_one({"id": biomassa_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Biomassa not found")
    return {"message": "Biomassa deleted"}

@router.delete("/biomassa")
async def delete_all_biomassa(user: dict = Depends(require_role(["admin"]))):
    result = await db.biomassa.delete_many({})
    return {"message": f"Deleted {result.deleted_count} biomassa records"}
