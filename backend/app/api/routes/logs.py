from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AgentLog

router = APIRouter()


@router.get("/logs")
async def list_logs(
    run_id: str | None = Query(None),
    agent: str | None = Query(None),
    step: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    q = select(AgentLog)
    if run_id:
        q = q.where(AgentLog.run_id == run_id)
    if agent:
        q = q.where(AgentLog.agent == agent)
    if step:
        q = q.where(AgentLog.step == step)
    q = q.order_by(desc(AgentLog.ts)).limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    items = [
        {
            "id": str(l.id),
            "run_id": str(l.run_id),
            "agent": l.agent,
            "step": l.step,
            "ts": l.ts.isoformat(),
            "severity": l.severity,
            "duration_ms": l.duration_ms,
            "coin_id": str(l.coin_id) if l.coin_id else None,
            "input": l.input,
            "output": l.output,
            "meta": l.meta,
        }
        for l in rows
    ]
    return {"items": items, "limit": limit, "offset": offset}
