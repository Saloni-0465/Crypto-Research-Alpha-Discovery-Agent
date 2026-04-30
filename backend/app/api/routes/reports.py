from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Report

router = APIRouter()


@router.get("/reports")
async def list_reports(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    q = select(Report).order_by(desc(Report.created_at)).limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    items = [
        {"id": str(r.id), "created_at": r.created_at.isoformat(), "title": r.title, "summary": r.summary, "payload": r.payload}
        for r in rows
    ]
    return {"items": items, "limit": limit, "offset": offset}


@router.get("/reports/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    r = (await db.execute(select(Report).where(Report.id == report_id))).scalar_one_or_none()
    if not r:
        return {"error": "not_found"}
    return {"id": str(r.id), "created_at": r.created_at.isoformat(), "title": r.title, "summary": r.summary, "payload": r.payload}
