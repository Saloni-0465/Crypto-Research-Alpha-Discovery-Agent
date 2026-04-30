from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Coin, Opportunity, Report

router = APIRouter()


@router.get("/opportunities")
async def list_opportunities(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    latest_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    latest_report = (
        await db.execute(select(Report).order_by(desc(Report.created_at)).limit(1))
    ).scalar_one_or_none()

    latest_ids: list[uuid.UUID] = []
    latest_run_id: str | None = None
    if latest_report:
        payload = latest_report.payload or {}
        latest_run_id = payload.get("run_id")
        for item in payload.get("top", []):
            try:
                latest_ids.append(uuid.UUID(str(item.get("opportunity_id"))))
            except (AttributeError, TypeError, ValueError):
                continue

    q = (
        select(Opportunity, Coin)
        .join(Coin, Coin.id == Opportunity.coin_id)
        .order_by(desc(Opportunity.final_score), desc(Opportunity.created_at))
        .limit(limit)
        .offset(offset)
    )
    if latest_only and latest_ids:
        q = q.where(Opportunity.id.in_(latest_ids))

    rows = (await db.execute(q)).all()
    items = []
    for opp, coin in rows:
        items.append(
            {
                "id": str(opp.id),
                "created_at": opp.created_at.isoformat(),
                "run_id": latest_run_id,
                "final_score": opp.final_score,
                "momentum_score": opp.momentum_score,
                "sentiment_score": opp.sentiment_score,
                "liquidity_score": opp.liquidity_score,
                "risk_score": opp.risk_score,
                "credibility_score": opp.credibility_score,
                "reasoning": opp.reasoning,
                "coin": {"id": str(coin.id), "symbol": coin.symbol, "name": coin.name, "coingecko_id": coin.coingecko_id},
                "evidence": opp.evidence,
            }
        )
    return {"items": items, "limit": limit, "offset": offset, "latest_only": latest_only, "run_id": latest_run_id}
