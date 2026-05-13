from typing import Optional

from fastapi import APIRouter, Depends, Query

from models import DashboardStats
from services.dashboard_metrics import (
    build_dashboard_advanced,
    build_dashboard_operational,
    build_dashboard_stats,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/operational")
async def get_dashboard_operational(
    period: Optional[str] = Query("all"),
    supplier: Optional[str] = Query("all"),
    mode: Optional[str] = Query("all"),
    user: dict = Depends(get_current_user),
):
    """Operational dashboard data focused on stock, arrivals, supplier risk, and coal disputes."""
    return await build_dashboard_operational(period, supplier, mode, user)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    return await build_dashboard_stats(user)


@router.get("/advanced")
async def get_dashboard_advanced(
    year: Optional[int] = None,
    month: Optional[int] = None,
    moda: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Advanced dashboard data with filters."""
    return await build_dashboard_advanced(year, month, moda, user)
