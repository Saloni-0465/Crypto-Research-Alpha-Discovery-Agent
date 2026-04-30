from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from app.settings import settings


class CoinGeckoClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.5, max=4))
    async def trending(self) -> list[dict[str, Any]]:
        r = await self._client.get(f"{settings.coingecko_base_url}/search/trending")
        r.raise_for_status()
        data = r.json()
        coins = []
        for item in data.get("coins", []):
            c = item.get("item") or {}
            coins.append(
                {
                    "coingecko_id": c.get("id"),
                    "symbol": (c.get("symbol") or "").upper(),
                    "name": c.get("name") or "",
                    "market_cap_rank": c.get("market_cap_rank"),
                    "score": item.get("score"),
                }
            )
        return coins

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.5, max=4))
    async def markets(self, *, ids: list[str], vs_currency: str = "usd") -> list[dict[str, Any]]:
        if not ids:
            return []
        r = await self._client.get(
            f"{settings.coingecko_base_url}/coins/markets",
            params={
                "vs_currency": vs_currency,
                "ids": ",".join(ids),
                "order": "market_cap_desc",
                "per_page": 250,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
        )
        r.raise_for_status()
        return r.json()

    def normalize_market_row(self, row: dict[str, Any]) -> dict[str, Any]:
        ts = datetime.now(tz=timezone.utc)
        return {
            "ts": ts,
            "coingecko_id": row.get("id"),
            "symbol": (row.get("symbol") or "").upper(),
            "name": row.get("name") or "",
            "price_usd": row.get("current_price"),
            "volume_24h_usd": row.get("total_volume"),
            "market_cap_usd": row.get("market_cap"),
            "change_24h_pct": row.get("price_change_percentage_24h"),
            "raw": row,
        }
