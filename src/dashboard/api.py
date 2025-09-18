"""
Dashboard API stub - minimal implementation to allow app to boot
"""

from fastapi import APIRouter

router = APIRouter()


def create_dashboard_app():
    return router


def set_dashboard_manager(manager):
    pass


@router.get("/dashboard")
async def get_dashboard():
    return {"dashboard": "stub", "status": "ready"}
