from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_graph
from app.agents.state import AgentState
from app.services.binance import BinanceClient
from app.services.coingecko import CoinGeckoClient
from app.services.http import make_client


async def run_full_pipeline(*, db: AsyncSession) -> uuid.UUID:
    run_id = uuid.uuid4()

    state: AgentState = {
        "run_id": run_id,
        "started_at": datetime.now(tz=timezone.utc),
        "mode": "full",
        "coins": [],
        "notes": [],
    }

    async with make_client() as client:
        coingecko = CoinGeckoClient(client)
        binance = BinanceClient(client)
        graph = build_graph(db=db, coingecko=coingecko, binance=binance)
        await graph.ainvoke(state)

    return run_id


async def run_fetch_only(*, db: AsyncSession) -> uuid.UUID:
    run_id = uuid.uuid4()
    state: AgentState = {
        "run_id": run_id,
        "started_at": datetime.now(tz=timezone.utc),
        "mode": "fetch_only",
        "coins": [],
        "notes": [],
    }

    async with make_client() as client:
        coingecko = CoinGeckoClient(client)
        binance = BinanceClient(client)
        # Reuse same graph but stop after fetch_data by invoking that node directly.
        # LangGraph doesn't expose "partial run" cleanly across versions; simplest is to call node.
        from app.agents.nodes import data_collector_node

        await data_collector_node(state, db=db, coingecko=coingecko, binance=binance)

    return run_id
