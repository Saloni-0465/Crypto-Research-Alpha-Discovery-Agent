from __future__ import annotations

import asyncio

from celery import shared_task

from app.agents.runner import run_full_pipeline
from app.database import AsyncSessionLocal


async def _run() -> str:
    async with AsyncSessionLocal() as db:
        run_id = await run_full_pipeline(db=db)
        await db.commit()
        return str(run_id)


@shared_task(name="app.worker.tasks.run_alpha_pipeline")
def run_alpha_pipeline() -> str:
    return asyncio.run(_run())
