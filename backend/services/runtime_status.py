import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.backup_service import get_backup_health
from utils.database import client, db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(data: Any) -> Any:
    return json.loads(json.dumps(data, default=str))


def _status_rank(status: str) -> int:
    return {"healthy": 0, "pass": 0, "disabled": 0, "unknown": 1, "warning": 1, "fail": 2, "critical": 2}.get(status, 1)


def _aggregate_status(parts: List[str]) -> str:
    worst = max((_status_rank(part) for part in parts), default=1)
    if worst >= 2:
        return "critical"
    if worst == 1:
        return "warning"
    return "healthy"


def _disk_path() -> Path:
    configured = os.environ.get("FRONTEND_STATIC_ROOT") or "/"
    path = Path(configured)
    while not path.exists() and path.parent != path:
        path = path.parent
    return path if path.exists() else Path("/")


def _disk_status() -> Dict[str, Any]:
    usage = shutil.disk_usage(_disk_path())
    used_percent = round((usage.used / usage.total) * 100, 2) if usage.total else 0
    status = "healthy"
    if used_percent >= 90:
        status = "critical"
    elif used_percent >= 80:
        status = "warning"

    return {
        "status": status,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "used_percent": used_percent,
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git_revision() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_repo_root(),
            capture_output=True,
            check=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return None
    value = result.stdout.strip()
    return value or None


def _safe_metadata_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("<") and text.endswith(">"):
        return None
    return text[:120]


def _backend_version_status() -> Dict[str, Optional[str]]:
    env_build_id = _safe_metadata_value(os.environ.get("APP_BUILD_ID"))
    git_sha = _git_revision()
    build_id = env_build_id or git_sha
    return {
        "app_version": os.environ.get("APP_VERSION"),
        "release_tag": os.environ.get("APP_RELEASE_TAG"),
        "build_id": build_id,
        "build_source": "env" if env_build_id else ("git" if git_sha else "unknown"),
        "git_sha": git_sha,
        "environment": os.environ.get("APP_ENV") or "unknown",
    }


def _unknown_frontend_version() -> Dict[str, Optional[str]]:
    return {
        "app_version": None,
        "release_tag": None,
        "build_id": None,
        "build_source": "unknown",
        "git_sha": None,
        "built_at": None,
    }


def _frontend_version_status(root: Path) -> Dict[str, Optional[str]]:
    version = _unknown_frontend_version()
    version_file = root / "version.json"
    if not version_file.exists():
        return version

    try:
        payload = json.loads(version_file.read_text(encoding="utf-8"))
    except Exception:
        version["build_source"] = "unreadable"
        return version

    for key in ("app_version", "release_tag", "build_id", "git_sha", "built_at"):
        version[key] = _safe_metadata_value(payload.get(key))
    version["build_source"] = "static-version-json"
    return version


def _frontend_status() -> Dict[str, Any]:
    static_root = os.environ.get("FRONTEND_STATIC_ROOT")
    root_source = "env"
    if static_root:
        root = Path(static_root)
    else:
        root_source = "auto"
        candidates = [
            _repo_root() / "frontend" / "build",
            Path("/var/www/emits"),
        ]
        root = next((candidate for candidate in candidates if (candidate / "index.html").exists()), candidates[0])

    index_file = root / "index.html"
    build_present = root.exists() and index_file.exists()
    return {
        "status": "healthy" if build_present else "warning",
        "build_present": build_present,
        "static_root": str(root),
        "static_root_source": root_source,
        "reason": "Build frontend tersedia" if build_present else "Build frontend statis belum ditemukan",
        "version": _frontend_version_status(root) if build_present else _unknown_frontend_version(),
    }


async def _database_status() -> Dict[str, Any]:
    try:
        await client.admin.command("ping")
        collections = await db.list_collection_names()
        return {
            "status": "healthy",
            "name": db.name,
            "collections": len(collections),
        }
    except Exception as exc:
        return {
            "status": "critical",
            "name": db.name,
            "collections": 0,
            "error": exc.__class__.__name__,
        }


def _safe_backup_event(event: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not event:
        return None
    allowed = {
        "id",
        "status",
        "trigger",
        "created_at",
        "finished_at",
        "duration_ms",
        "filename",
        "file_size_bytes",
        "total_documents",
    }
    return {key: event.get(key) for key in allowed if key in event}


def _safe_backup_health(health: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": health.get("status", "unknown"),
        "stale": bool(health.get("stale")),
        "reason": health.get("reason"),
        "enabled": bool(health.get("enabled")),
        "latest_success": _safe_backup_event(health.get("latest_success")),
        "latest_event": _safe_backup_event(health.get("latest_event")),
        "interval_hours": health.get("interval_hours"),
        "retention_days": health.get("retention_days"),
        "max_backups": health.get("max_backups"),
    }


def _smoke_summary(report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not report:
        return {
            "status": "unknown",
            "finished_at": None,
            "passed": 0,
            "failed": 0,
            "results": [],
        }

    results = report.get("results") or []
    passed = int(report.get("passed") if report.get("passed") is not None else sum(1 for item in results if item.get("ok")))
    failed = int(report.get("failed") if report.get("failed") is not None else sum(1 for item in results if not item.get("ok")))
    status = "fail" if failed else "pass"
    return {
        "status": report.get("status") or status,
        "finished_at": report.get("finished_at"),
        "passed": passed,
        "failed": failed,
        "results": results[:25],
    }


async def latest_smoke_report() -> Optional[Dict[str, Any]]:
    report = await db.runtime_smoke_reports.find_one(
        {},
        {"_id": 0},
        sort=[("finished_at", -1), ("created_at", -1)],
    )
    return _json_safe(report) if report else None


async def build_runtime_status() -> Dict[str, Any]:
    database = await _database_status()
    frontend = _frontend_status()
    backup = _safe_backup_health(await get_backup_health())
    disk = _disk_status()
    smoke = _smoke_summary(await latest_smoke_report())
    backend_version = _backend_version_status()
    frontend_version = frontend.get("version") or _unknown_frontend_version()

    aggregate = _aggregate_status(
        [
            database["status"],
            frontend["status"],
            backup["status"],
            "warning" if backup.get("stale") else "healthy",
            disk["status"],
            smoke["status"],
        ]
    )

    return {
        "status": aggregate,
        "generated_at": _now_iso(),
        "version": {
            **backend_version,
            "backend": backend_version,
            "frontend": frontend_version,
        },
        "backend": {
            "status": "healthy",
            "api_prefix": "/api",
            "version": backend_version,
        },
        "database": database,
        "frontend": frontend,
        "backup": backup,
        "smoke": smoke,
        "disk": disk,
    }


async def build_public_version_status() -> Dict[str, Any]:
    """Return non-sensitive deployment identity for smoke checks and operator triage."""
    database = await _database_status()
    frontend = _frontend_status()
    backend_version = _backend_version_status()
    frontend_version = frontend.get("version") or _unknown_frontend_version()
    versions_match = bool(
        backend_version.get("git_sha")
        and frontend_version.get("git_sha")
        and backend_version.get("git_sha") == frontend_version.get("git_sha")
    )

    return {
        "status": _aggregate_status([database["status"], frontend["status"]]),
        "generated_at": _now_iso(),
        "backend": {
            "status": "healthy",
            "version": backend_version,
        },
        "frontend": {
            "status": frontend["status"],
            "version": frontend_version,
        },
        "database": {
            "status": database["status"],
            "name": database["name"],
            "collections": database["collections"],
        },
        "versions_match": versions_match,
    }


async def record_smoke_report(report: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    results = [
        {
            "name": str(item.get("name", "unknown"))[:120],
            "ok": bool(item.get("ok")),
            "detail": str(item.get("detail", ""))[:500],
        }
        for item in (report.get("results") or [])[:100]
        if isinstance(item, dict)
    ]
    passed = sum(1 for item in results if item["ok"])
    failed = sum(1 for item in results if not item["ok"])
    stored = {
        "id": str(uuid.uuid4()),
        "status": "fail" if failed else "pass",
        "started_at": report.get("started_at"),
        "finished_at": report.get("finished_at") or _now_iso(),
        "base_url": report.get("base_url"),
        "frontend_url": report.get("frontend_url"),
        "passed": passed,
        "failed": failed,
        "results": results,
        "created_at": _now_iso(),
        "created_by": user.get("id"),
        "created_by_email": user.get("email"),
    }
    await db.runtime_smoke_reports.insert_one(stored)
    stored.pop("_id", None)
    return _json_safe(stored)
