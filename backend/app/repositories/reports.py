from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Report


async def insert_report(db: AsyncSession, *, title: str, summary: str, payload: dict[str, Any]) -> Report:
    row = Report(title=title, summary=summary, payload=payload)
    db.add(row)
    await db.flush()
    return row
