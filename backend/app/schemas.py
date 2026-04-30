from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CoinOut(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    coingecko_id: str | None = None


class MarketDataOut(BaseModel):
    id: uuid.UUID
    coin_id: uuid.UUID
    source: str
    ts: datetime
    price_usd: float | None = None
    volume_24h_usd: float | None = None
    market_cap_usd: float | None = None
    change_24h_pct: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class SignalOut(BaseModel):
    id: uuid.UUID
    coin_id: uuid.UUID
    agent: str
    kind: str
    ts: datetime
    score: float
    confidence: float
    data: dict[str, Any] = Field(default_factory=dict)


class OpportunityOut(BaseModel):
    id: uuid.UUID
    coin_id: uuid.UUID
    created_at: datetime

    momentum_score: float
    sentiment_score: float
    liquidity_score: float
    risk_score: float
    credibility_score: float
    final_score: float

    reasoning: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ReportOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    title: str
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentLogOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    agent: str
    step: str
    ts: datetime
    input: dict[str, Any]
    output: dict[str, Any]
    meta: dict[str, Any]
    coin_id: uuid.UUID | None = None
    severity: Literal["debug", "info", "warn", "error"] = "info"
    duration_ms: int | None = None


class RunAgentsResponse(BaseModel):
    run_id: uuid.UUID
    report_id: uuid.UUID | None = None
    opportunities_created: int
    signals_created: int
    notes: list[str] = Field(default_factory=list)
