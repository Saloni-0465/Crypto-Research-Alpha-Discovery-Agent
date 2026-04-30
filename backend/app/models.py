from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Coin(Base):
    __tablename__ = "coins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(128))
    coingecko_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    market_data: Mapped[list["MarketData"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    signals: Mapped[list["Signal"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="coin", cascade="all, delete-orphan")


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coins.id", ondelete="CASCADE"), index=True)

    source: Mapped[str] = mapped_column(String(32), index=True)  # coingecko|binance
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_cap_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    coin: Mapped["Coin"] = relationship(back_populates="market_data")

    __table_args__ = (Index("ix_market_data_coin_ts", "coin_id", "ts"),)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coins.id", ondelete="CASCADE"), index=True)

    agent: Mapped[str] = mapped_column(String(64), index=True)  # onchain|sentiment|pattern
    kind: Mapped[str] = mapped_column(String(64), index=True)  # whale_tx|sentiment|volume_spike|...
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    score: Mapped[float] = mapped_column(Float, default=0.0)  # normalized 0..1
    confidence: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    coin: Mapped["Coin"] = relationship(back_populates="signals")

    __table_args__ = (Index("ix_signals_coin_ts_kind", "coin_id", "ts", "kind"),)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coins.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    embedding_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    momentum_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    liquidity_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)

    reasoning: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    coin: Mapped["Coin"] = relationship(back_populates="opportunities")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    title: Mapped[str] = mapped_column(String(256), default="Alpha Report")
    summary: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    agent: Mapped[str] = mapped_column(String(64), index=True)
    step: Mapped[str] = mapped_column(String(64), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Optional linkage
    coin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(16), default="info", index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class NewsItem(Base):
    """
    Optional: used when wiring a real news/Twitter ingestion pipeline.
    Kept in schema for future-proofing and vector search demo.
    """

    __tablename__ = "news_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    source: Mapped[str] = mapped_column(String(64), index=True)  # twitter|rss|newsapi
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    coin_symbol: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    embedding_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
