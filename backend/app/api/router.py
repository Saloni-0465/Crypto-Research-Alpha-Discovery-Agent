from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.agents import router as agents_router
from app.api.routes.logs import router as logs_router
from app.api.routes.opportunities import router as opportunities_router
from app.api.routes.reports import router as reports_router
from app.api.routes.search import router as search_router
from app.api.routes.signals import router as signals_router

api_router = APIRouter()

api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(opportunities_router, tags=["opportunities"])
api_router.include_router(reports_router, tags=["reports"])
api_router.include_router(search_router, tags=["search"])
api_router.include_router(signals_router, tags=["signals"])
api_router.include_router(logs_router, tags=["logs"])
