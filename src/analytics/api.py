"""
Analytics API stub - minimal implementation to allow app to boot
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/analytics")
async def get_analytics():
    return {"analytics": "stub", "status": "ready"}
