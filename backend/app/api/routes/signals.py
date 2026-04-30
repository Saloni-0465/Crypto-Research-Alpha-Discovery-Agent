from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Coin, Signal

router = APIRouter()


@router.get("/signals")
async def list_signals(
    coin_symbol: str | None = Query(None),
    kind: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    q = select(Signal, Coin).join(Coin, Coin.id == Signal.coin_id)
    if coin_symbol:
        q = q.where(Coin.symbol == coin_symbol.upper())
    if kind:
        q = q.where(Signal.kind == kind)
    q = q.order_by(desc(Signal.ts)).limit(limit).offset(offset)
    rows = (await db.execute(q)).all()
    items = []
    for s, c in rows:
        items.append(
            {
                "id": str(s.id),
                "ts": s.ts.isoformat(),
                "agent": s.agent,
                "kind": s.kind,
                "score": s.score,
                "confidence": s.confidence,
                "data": s.data,
                "coin": {"id": str(c.id), "symbol": c.symbol, "name": c.name},
            }
        )
    return {"items": items, "limit": limit, "offset": offset}
