"""
Alert API stub - minimal implementation to allow app to boot
"""

from fastapi import APIRouter

alerts_router = APIRouter()


@alerts_router.get("/alerts")
async def get_alerts():
    return {"alerts": "stub", "status": "ready"}
