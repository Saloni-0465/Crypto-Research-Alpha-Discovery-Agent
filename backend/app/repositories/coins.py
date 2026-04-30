from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Coin


async def get_coin_by_symbol(db: AsyncSession, symbol: str) -> Coin | None:
    res = await db.execute(select(Coin).where(Coin.symbol == symbol.upper()))
    return res.scalar_one_or_none()


async def upsert_coin(
    db: AsyncSession,
    *,
    symbol: str,
    name: str,
    coingecko_id: str | None = None,
) -> Coin:
    symbol_u = symbol.upper()
    existing = await get_coin_by_symbol(db, symbol_u)
    now = datetime.utcnow()

    if existing:
        existing.name = name
        existing.coingecko_id = coingecko_id or existing.coingecko_id
        existing.updated_at = now
        await db.flush()
        return existing

    coin = Coin(symbol=symbol_u, name=name, coingecko_id=coingecko_id, created_at=now, updated_at=now)
    db.add(coin)
    await db.flush()
    return coin
