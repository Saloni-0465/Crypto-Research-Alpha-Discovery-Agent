from __future__ import annotations

import httpx

from app.settings import settings


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=settings.request_timeout_s, headers={"User-Agent": "crypto-alpha-agent/1.0"})
