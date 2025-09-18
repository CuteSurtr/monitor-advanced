"""
Portfolio API stub - minimal implementation to allow app to boot
"""

from fastapi import APIRouter

portfolio_router = APIRouter()


def set_portfolio_manager(manager):
    pass


@portfolio_router.get("/portfolio")
async def get_portfolio():
    return {"portfolio": "stub", "status": "ready"}
