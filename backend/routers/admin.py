from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from utils.auth import require_role
from utils.database import db

router = APIRouter(prefix="/admin", tags=["Admin"])

ACTIVE_BACKUP_COLLECTIONS = [
    "users",
    "user_settings",
    "audit_logs",
    "vessels",
    "barges",
    "trucking",
    "biomassa",
    "po_batubara",
    "merit_order",
    "smartstock",
    "sumberpemakaian",
    "coa_reconciliation",
    "app_settings",
    "ai_chat_history",
]


class RestoreRequest(BaseModel):
    confirmation: str
    backup: Dict[str, Any]
    dry_run: bool = False


def _json_safe(data: Any) -> Any:
    return json.loads(json.dumps(data, default=str))


def _validate_backup_payload(backup: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    if not isinstance(backup, dict):
        raise HTTPException(status_code=400, detail="Payload backup tidak valid")

    collections = backup.get("collections")
    if not isinstance(collections, dict):
        raise HTTPException(status_code=400, detail="File backup tidak memiliki collections")

    if backup.get("schema_version") != 1:
        raise HTTPException(status_code=400, detail="Versi schema backup tidak didukung")

    unknown_collections = sorted(set(collections.keys()) - set(ACTIVE_BACKUP_COLLECTIONS))
    if unknown_collections:
        raise HTTPException(
            status_code=400,
            detail=f"Backup berisi koleksi tidak dikenal: {', '.join(unknown_collections)}",
        )

    missing_collections = sorted(set(ACTIVE_BACKUP_COLLECTIONS) - set(collections.keys()))
    if missing_collections:
        raise HTTPException(
            status_code=400,
            detail=f"Backup tidak lengkap, koleksi hilang: {', '.join(missing_collections)}",
        )

    validated = {}
    for name, documents in collections.items():
        if not isinstance(documents, list):
            raise HTTPException(status_code=400, detail=f"Koleksi {name} harus berupa array")
        clean_documents = []
        for document in documents:
            if not isinstance(document, dict):
                raise HTTPException(status_code=400, detail=f"Dokumen pada koleksi {name} tidak valid")
            document.pop("_id", None)
            clean_documents.append(document)
        validated[name] = clean_documents

    return validated


@router.post("/backup")
async def create_admin_backup(user: dict = Depends(require_role(["admin"]))):
    generated_at = datetime.now(timezone.utc).isoformat()
    backup = {
        "schema_version": 1,
        "application": "emits-pltu-tenayan",
        "generated_at": generated_at,
        "generated_by": {
            "id": user.get("id"),
            "email": user.get("email"),
            "name": user.get("name"),
        },
        "collections": {},
        "counts": {},
    }

    for collection_name in ACTIVE_BACKUP_COLLECTIONS:
        documents = await db[collection_name].find({}, {"_id": 0}).to_list(length=None)
        backup["collections"][collection_name] = documents
        backup["counts"][collection_name] = len(documents)

    return _json_safe(backup)


@router.get("/audit-logs")
async def get_admin_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    record_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(require_role(["admin"])),
):
    query = {}
    if category and category != "all":
        query["category"] = category
    if action and action != "all":
        query["action"] = action
    if resource and resource != "all":
        query["resource"] = resource
    if record_id:
        query["record_id"] = record_id
    if severity and severity != "all":
        query["severity"] = severity
    if actor:
        query["$or"] = [
            {"actor_id": actor},
            {"actor_email": {"$regex": actor, "$options": "i"}},
        ]
    if date_from or date_to:
        created_filter = {}
        if date_from:
            created_filter["$gte"] = date_from
        if date_to:
            created_filter["$lte"] = f"{date_to}T23:59:59"
        query["created_at"] = created_filter

    total = await db.audit_logs.count_documents(query)
    skip = (page - 1) * page_size
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)

    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/audit-logs/export")
async def export_admin_audit_logs(
    category: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    record_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(require_role(["admin"])),
):
    query = {}
    if category and category != "all":
        query["category"] = category
    if action and action != "all":
        query["action"] = action
    if resource and resource != "all":
        query["resource"] = resource
    if record_id:
        query["record_id"] = record_id
    if severity and severity != "all":
        query["severity"] = severity
    if actor:
        query["$or"] = [
            {"actor_id": actor},
            {"actor_email": {"$regex": actor, "$options": "i"}},
        ]
    if date_from or date_to:
        created_filter = {}
        if date_from:
            created_filter["$gte"] = date_from
        if date_to:
            created_filter["$lte"] = f"{date_to}T23:59:59"
        query["created_at"] = created_filter

    rows = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(5000).to_list(5000)
    headers = ["created_at", "severity", "category", "action", "resource", "record_id", "actor_email", "path", "status_code"]
    lines = [",".join(headers)]
    for row in rows:
        values = []
        for header in headers:
            value = str(row.get(header, "")).replace('"', '""')
            values.append(f'"{value}"')
        lines.append(",".join(values))
    csv = "\n".join(lines)
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=emits-audit-logs.csv"},
    )


@router.post("/restore")
async def restore_admin_backup(request: RestoreRequest, user: dict = Depends(require_role(["admin"]))):
    if request.confirmation != "RESTORE":
        raise HTTPException(status_code=400, detail="Konfirmasi restore harus bernilai RESTORE")

    collections = _validate_backup_payload(request.backup)
    counts = {name: len(documents) for name, documents in collections.items()}

    if request.dry_run:
        return {
            "message": "Validasi restore berhasil",
            "dry_run": True,
            "collections": sorted(collections.keys()),
            "counts": counts,
        }

    restored = {}
    for collection_name in ACTIVE_BACKUP_COLLECTIONS:
        documents = collections.get(collection_name, [])
        await db[collection_name].delete_many({})
        if documents:
            await db[collection_name].insert_many(documents)
        restored[collection_name] = len(documents)

    return {
        "message": "Restore backup berhasil",
        "dry_run": False,
        "restored": restored,
        "restored_at": datetime.now(timezone.utc).isoformat(),
        "restored_by": user.get("id"),
    }
