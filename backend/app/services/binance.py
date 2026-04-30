from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from app.settings import settings


class BinanceClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @retry(stop=stop_after_attempt(2), wait=wait_exponential_jitter(initial=0.2, max=2))
    async def ticker_24hr(self, symbol: str) -> dict[str, Any] | None:
        # symbol like BTCUSDT
        r = await self._client.get(f"{settings.binance_base_url}/api/v3/ticker/24hr", params={"symbol": symbol})
        if r.status_code == 400:
            return None
        r.raise_for_status()
        return r.json()

    def normalize_ticker(self, ticker: dict[str, Any]) -> dict[str, Any]:
        ts = datetime.now(tz=timezone.utc)
        return {
            "ts": ts,
            "symbol": ticker.get("symbol"),
            "price_usd": float(ticker["lastPrice"]) if "lastPrice" in ticker else None,
            "volume_24h_usd": float(ticker["quoteVolume"]) if "quoteVolume" in ticker else None,
            "change_24h_pct": float(ticker["priceChangePercent"]) if "priceChangePercent" in ticker else None,
            "raw": ticker,
        }
