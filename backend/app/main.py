from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.database import engine
from app.db_init import create_all
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.db_auto_create:
        await create_all(engine)
    yield


def cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]


app = FastAPI(
    title=settings.app_name,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True, "env": settings.app_env}


app = CORSMiddleware(
    app,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
