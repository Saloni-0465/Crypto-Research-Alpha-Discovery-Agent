from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, TypedDict


class CoinContext(TypedDict, total=False):
    coin_id: uuid.UUID
    symbol: str
    name: str
    coingecko_id: str | None

    market: dict[str, Any]
    onchain: dict[str, Any]
    sentiment: dict[str, Any]
    patterns: list[dict[str, Any]]
    validation: dict[str, Any]
    ranking: dict[str, Any]


class AgentState(TypedDict):
    run_id: uuid.UUID
    started_at: datetime
    mode: Literal["fetch_only", "full"]

    coins: list[CoinContext]
    notes: list[str]
