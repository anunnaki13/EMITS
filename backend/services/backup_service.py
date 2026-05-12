import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from utils.database import db

logger = logging.getLogger(__name__)

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

DEFAULT_BACKUP_SETTINGS = {
    "type": "backup",
    "enabled": False,
    "interval_hours": 24,
    "retention_days": 14,
    "max_backups": 7,
    "backup_dir": None,
}

ROOT_DIR = Path(__file__).resolve().parents[1]
_backup_lock = asyncio.Lock()


def json_safe(data: Any) -> Any:
    return json.loads(json.dumps(data, default=str))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _backup_dir(settings: Dict[str, Any]) -> Path:
    configured = settings.get("backup_dir") or os.environ.get("BACKUP_DIR")
    path = Path(configured) if configured else ROOT_DIR / "backups"
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


async def get_backup_settings() -> Dict[str, Any]:
    stored = await db.app_settings.find_one({"type": "backup"}, {"_id": 0}) or {}
    settings = {**DEFAULT_BACKUP_SETTINGS, **stored}
    return settings


async def update_backup_settings(data: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    settings = {
        "type": "backup",
        "enabled": bool(data.get("enabled", False)),
        "interval_hours": int(data.get("interval_hours") or DEFAULT_BACKUP_SETTINGS["interval_hours"]),
        "retention_days": int(data.get("retention_days") or DEFAULT_BACKUP_SETTINGS["retention_days"]),
        "max_backups": int(data.get("max_backups") or DEFAULT_BACKUP_SETTINGS["max_backups"]),
        "backup_dir": data.get("backup_dir") or None,
        "updated_at": _now_iso(),
        "updated_by": user.get("id"),
    }
    await db.app_settings.update_one({"type": "backup"}, {"$set": settings}, upsert=True)
    return settings


async def build_backup_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    generated_at = _now_iso()
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

    return json_safe(backup)


def _history_projection() -> Dict[str, int]:
    return {"_id": 0}


async def _latest_success() -> Optional[Dict[str, Any]]:
    return await db.backup_history.find_one(
        {"status": "success"},
        _history_projection(),
        sort=[("created_at", -1)],
    )


async def get_backup_health(settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    settings = settings or await get_backup_settings()
    latest = await _latest_success()
    latest_any = await db.backup_history.find_one({}, _history_projection(), sort=[("created_at", -1)])

    status = "disabled"
    stale = False
    reason = "Backup otomatis nonaktif"
    if settings.get("enabled"):
        if not latest:
            status = "warning"
            stale = True
            reason = "Belum ada backup sukses"
        else:
            last_success = datetime.fromisoformat(str(latest["created_at"]))
            max_age = timedelta(hours=max(int(settings.get("interval_hours") or 24) * 2, 1))
            stale = _now() - last_success > max_age
            status = "warning" if stale else "healthy"
            reason = "Backup terakhir sudah terlalu lama" if stale else "Backup otomatis sehat"

    return {
        "status": status,
        "stale": stale,
        "reason": reason,
        "enabled": bool(settings.get("enabled")),
        "latest_success": latest,
        "latest_event": latest_any,
        "interval_hours": settings.get("interval_hours"),
        "retention_days": settings.get("retention_days"),
        "max_backups": settings.get("max_backups"),
    }


async def list_backup_history(page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    skip = (page - 1) * page_size
    total = await db.backup_history.count_documents({})
    items = await db.backup_history.find({}, _history_projection()).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


async def create_managed_backup(user: Dict[str, Any], trigger: str = "manual") -> Dict[str, Any]:
    async with _backup_lock:
        settings = await get_backup_settings()
        history = {
            "id": str(uuid.uuid4()),
            "status": "running",
            "trigger": trigger,
            "created_at": _now_iso(),
            "created_by": user.get("id"),
            "created_by_email": user.get("email"),
        }
        await db.backup_history.insert_one(history)
        history.pop("_id", None)
        start = _now()

        try:
            backup = await build_backup_payload(user)
            backup_dir = _backup_dir(settings)
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = start.strftime("%Y%m%dT%H%M%SZ")
            filename = f"emits-backup-{stamp}-{history['id'][:8]}.json"
            file_path = backup_dir / filename
            file_path.write_text(json.dumps(backup, indent=2, ensure_ascii=False), encoding="utf-8")
            file_size = file_path.stat().st_size
            duration_ms = int((_now() - start).total_seconds() * 1000)
            total_documents = sum(backup["counts"].values())

            update = {
                "status": "success",
                "finished_at": _now_iso(),
                "duration_ms": duration_ms,
                "filename": filename,
                "file_path": str(file_path),
                "file_size_bytes": file_size,
                "counts": backup["counts"],
                "total_documents": total_documents,
            }
            await db.backup_history.update_one({"id": history["id"]}, {"$set": update})
            await apply_retention(settings)
            return {**history, **update}
        except Exception as exc:
            logger.exception("Managed backup failed")
            update = {
                "status": "failed",
                "finished_at": _now_iso(),
                "duration_ms": int((_now() - start).total_seconds() * 1000),
                "error": str(exc),
            }
            await db.backup_history.update_one({"id": history["id"]}, {"$set": update})
            return {**history, **update}


async def apply_retention(settings: Optional[Dict[str, Any]] = None) -> int:
    settings = settings or await get_backup_settings()
    max_backups = max(int(settings.get("max_backups") or 1), 1)
    retention_days = max(int(settings.get("retention_days") or 1), 1)
    cutoff = _now() - timedelta(days=retention_days)
    successes = await db.backup_history.find({"status": "success"}, _history_projection()).sort("created_at", -1).to_list(length=500)

    pruned = 0
    for index, item in enumerate(successes):
        if index == 0:
            continue
        created_at = datetime.fromisoformat(str(item["created_at"]))
        should_prune = index >= max_backups or created_at < cutoff
        if not should_prune or item.get("file_pruned"):
            continue
        file_path = item.get("file_path")
        if file_path:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as exc:
                await db.backup_history.update_one({"id": item["id"]}, {"$set": {"retention_error": str(exc)}})
                continue
        await db.backup_history.update_one(
            {"id": item["id"]},
            {"$set": {"file_pruned": True, "pruned_at": _now_iso()}},
        )
        pruned += 1

    return pruned


async def backup_scheduler_loop(poll_seconds: Optional[int] = None):
    poll_seconds = poll_seconds or int(os.environ.get("BACKUP_SCHEDULER_POLL_SECONDS", "300"))
    while True:
        try:
            settings = await get_backup_settings()
            if settings.get("enabled"):
                latest = await _latest_success()
                due = latest is None
                if latest:
                    latest_at = datetime.fromisoformat(str(latest["created_at"]))
                    due = _now() - latest_at >= timedelta(hours=int(settings.get("interval_hours") or 24))
                if due:
                    await create_managed_backup({"id": "system", "email": "system", "name": "System Scheduler"}, trigger="scheduled")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Backup scheduler loop failed")
        await asyncio.sleep(poll_seconds)
