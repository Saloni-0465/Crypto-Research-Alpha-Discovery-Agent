from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Signal


async def insert_signal(
    db: AsyncSession,
    *,
    coin_id,
    agent: str,
    kind: str,
    ts: datetime,
    score: float,
    confidence: float,
    data: dict[str, Any],
) -> Signal:
    row = Signal(
        coin_id=coin_id,
        agent=agent,
        kind=kind,
        ts=ts,
        score=score,
        confidence=confidence,
        data=data,
    )
    db.add(row)
    await db.flush()
    return row
