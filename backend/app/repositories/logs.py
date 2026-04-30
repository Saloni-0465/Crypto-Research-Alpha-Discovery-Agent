from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentLog


async def write_agent_log(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    agent: str,
    step: str,
    input: dict[str, Any],
    output: dict[str, Any],
    meta: dict[str, Any] | None = None,
    coin_id: uuid.UUID | None = None,
    severity: str = "info",
    duration_ms: int | None = None,
) -> AgentLog:
    row = AgentLog(
        run_id=run_id,
        agent=agent,
        step=step,
        ts=datetime.utcnow(),
        input=input,
        output=output,
        meta=meta or {},
        coin_id=coin_id,
        severity=severity,
        duration_ms=duration_ms,
    )
    db.add(row)
    await db.flush()
    return row


@asynccontextmanager
async def log_step(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    agent: str,
    step: str,
    input: dict[str, Any],
    coin_id: uuid.UUID | None = None,
) -> AsyncIterator[dict[str, Any]]:
    started = time.perf_counter()
    output: dict[str, Any] = {}
    meta: dict[str, Any] = {}
    severity = "info"
    try:
        yield {"output": output, "meta": meta}
    except Exception as e:  # noqa: BLE001
        severity = "error"
        output = {"error": str(e), "type": type(e).__name__}
        raise
    finally:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await write_agent_log(
            db,
            run_id=run_id,
            agent=agent,
            step=step,
            input=input,
            output=output,
            meta=meta,
            coin_id=coin_id,
            severity=severity,
            duration_ms=duration_ms,
        )
