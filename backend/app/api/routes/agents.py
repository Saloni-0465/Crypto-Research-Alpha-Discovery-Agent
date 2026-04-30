from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runner import run_fetch_only, run_full_pipeline
from app.database import get_db
from app.models import AgentLog, Report
from app.schemas import RunAgentsResponse

router = APIRouter()


@router.post("/fetch-data")
async def fetch_data(db: AsyncSession = Depends(get_db)) -> dict:
    run_id = await run_fetch_only(db=db)
    await db.commit()
    return {"run_id": str(run_id), "status": "ok"}


@router.post("/run-agents", response_model=RunAgentsResponse)
async def run_agents(db: AsyncSession = Depends(get_db)) -> RunAgentsResponse:
    run_id = await run_full_pipeline(db=db)

    # commit pipeline writes
    await db.commit()

    # Derive counts from logs (simple + reliable)
    logs = (await db.execute(select(AgentLog).where(AgentLog.run_id == run_id))).scalars().all()
    signals_created = 0
    opportunities_created = 0
    for l in logs:
        if l.agent == "sentiment" and l.step == "done":
            signals_created += int(l.output.get("signals_written", 0) or 0)
        if l.agent == "pattern" and l.step == "done":
            signals_created += int(l.output.get("pattern_signals_written", 0) or 0)
        if l.agent == "onchain" and l.step == "done":
            # unknown count; onchain writes conditional signals
            pass
        if l.agent == "report" and l.step == "done":
            opportunities_created += int(l.output.get("opportunities_created", 0) or 0)

    # Find most recent report referencing this run
    report_id: uuid.UUID | None = None
    rep = (
        await db.execute(select(Report).order_by(Report.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    if rep and rep.payload.get("run_id") == str(run_id):
        report_id = rep.id

    return RunAgentsResponse(
        run_id=run_id,
        report_id=report_id,
        opportunities_created=opportunities_created,
        signals_created=signals_created,
        notes=["Pipeline executed. See /logs for step-by-step explainability."],
    )
