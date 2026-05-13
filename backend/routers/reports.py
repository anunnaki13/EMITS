from typing import Optional

from fastapi import APIRouter, Depends, Query

from services.management_reports import build_management_report
from utils.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/management")
async def get_management_report(
    period: Optional[str] = Query("all"),
    supplier: Optional[str] = Query("all"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Executive report summary for stock, arrivals, suppliers, loss, and disputes."""
    return await build_management_report(period, supplier, date_from, date_to, user)
