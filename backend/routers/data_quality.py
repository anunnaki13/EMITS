from typing import Optional

from fastapi import APIRouter, Depends, Query, Response

from services.data_quality import build_data_quality_export_rows, build_data_quality_report
from utils.auth import require_role

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


def _csv_cell(value) -> str:
    text = str(value if value is not None else "").replace('"', '""')
    return f'"{text}"'


@router.get("/summary")
async def get_data_quality_summary(
    module: Optional[str] = Query("all"),
    severity: Optional[str] = Query("all"),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(require_role(["admin", "operator"])),
):
    return await build_data_quality_report(module=module or "all", severity=severity or "all", limit=limit)


@router.get("/issues")
async def get_data_quality_issues(
    module: Optional[str] = Query("all"),
    severity: Optional[str] = Query("all"),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(require_role(["admin", "operator"])),
):
    report = await build_data_quality_report(module=module or "all", severity=severity or "all", limit=limit)
    return {
        "items": report["issues"],
        "total": report["total_issues"],
        "filter_scope": report["filter_scope"],
        "status": report["status"],
        "counts": report["counts"],
    }


@router.post("/recompute")
async def recompute_data_quality(
    module: Optional[str] = Query("all"),
    severity: Optional[str] = Query("all"),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(require_role(["admin", "operator"])),
):
    report = await build_data_quality_report(module=module or "all", severity=severity or "all", limit=limit)
    return {"message": "Data quality rules evaluated", **report}


@router.get("/export")
async def export_data_quality(
    module: Optional[str] = Query("all"),
    severity: Optional[str] = Query("all"),
    user: dict = Depends(require_role(["admin", "operator"])),
):
    rows = await build_data_quality_export_rows(module=module or "all", severity=severity or "all")
    headers = ["severity", "module", "type", "field", "source_record_id", "source_label", "message", "suggested_fix", "source_path"]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(_csv_cell(row.get(header)) for header in headers))
    return Response(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=emits-data-quality.csv"},
    )
