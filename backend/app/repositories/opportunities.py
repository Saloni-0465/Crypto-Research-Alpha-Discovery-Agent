from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Opportunity


async def insert_opportunity(
    db: AsyncSession,
    *,
    coin_id,
    momentum_score: float,
    sentiment_score: float,
    liquidity_score: float,
    risk_score: float,
    credibility_score: float,
    final_score: float,
    reasoning: str,
    evidence: dict[str, Any],
) -> Opportunity:
    row = Opportunity(
        coin_id=coin_id,
        momentum_score=momentum_score,
        sentiment_score=sentiment_score,
        liquidity_score=liquidity_score,
        risk_score=risk_score,
        credibility_score=credibility_score,
        final_score=final_score,
        reasoning=reasoning,
        evidence=evidence,
    )
    db.add(row)
    await db.flush()
    return row
