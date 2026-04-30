from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Coin, MarketData


async def insert_market_data(
    db: AsyncSession,
    *,
    coin_id,
    source: str,
    ts: datetime,
    price_usd: float | None,
    volume_24h_usd: float | None,
    market_cap_usd: float | None,
    change_24h_pct: float | None,
    raw: dict[str, Any],
) -> MarketData:
    row = MarketData(
        coin_id=coin_id,
        source=source,
        ts=ts,
        price_usd=price_usd,
        volume_24h_usd=volume_24h_usd,
        market_cap_usd=market_cap_usd,
        change_24h_pct=change_24h_pct,
        raw=raw,
    )
    db.add(row)
    await db.flush()
    return row


async def latest_market_snapshots(
    db: AsyncSession,
    *,
    source: str = "coingecko",
    limit: int = 20,
) -> list[tuple[Coin, MarketData]]:
    rows = (
        await db.execute(
            select(Coin, MarketData)
            .join(MarketData, MarketData.coin_id == Coin.id)
            .where(MarketData.source == source)
            .order_by(MarketData.ts.desc())
            .limit(limit * 4)
        )
    ).all()

    seen: set[str] = set()
    snapshots: list[tuple[Coin, MarketData]] = []
    for coin, market in rows:
        if coin.symbol in seen:
            continue
        seen.add(coin.symbol)
        snapshots.append((coin, market))
        if len(snapshots) >= limit:
            break
    return snapshots
