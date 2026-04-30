from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    credibility_score: float  # 0..1
    liquidity_score: float  # 0..1
    risk_score: float  # 0..1 (higher = riskier)
    flags: list[str]
    meta: dict[str, Any]


def validate_token(
    *,
    volume_24h_usd: float | None,
    market_cap_usd: float | None,
    change_24h_pct: float | None,
    has_whale: bool,
) -> ValidationResult:
    vol = float(volume_24h_usd or 0.0)
    mc = float(market_cap_usd or 0.0)
    ch = float(change_24h_pct or 0.0)
    flags: list[str] = []

    # Liquidity score: sigmoid-ish
    liquidity_score = min(1.0, vol / 200_000_000.0)
    if vol < 2_000_000:
        flags.append("low_liquidity")

    # Credibility: higher for larger market cap + reasonable liquidity
    credibility = min(1.0, (mc / 50_000_000_000.0) * 0.7 + liquidity_score * 0.3)
    if mc < 50_000_000:
        flags.append("microcap")

    # Risk: increases with extreme moves and low liquidity
    risk = 0.25
    risk += min(0.5, abs(ch) / 60.0)
    risk += 0.25 * (1.0 - liquidity_score)
    if "low_liquidity" in flags and abs(ch) > 25:
        flags.append("pump_like_move")
        risk = min(1.0, risk + 0.2)
        credibility = max(0.0, credibility - 0.15)

    if has_whale and vol > 0 and mc > 0:
        # Whale + good liquidity can be informative (not always bearish)
        credibility = min(1.0, credibility + 0.05)

    return ValidationResult(
        credibility_score=max(0.0, min(1.0, credibility)),
        liquidity_score=max(0.0, min(1.0, liquidity_score)),
        risk_score=max(0.0, min(1.0, risk)),
        flags=flags,
        meta={"volume_24h_usd": vol, "market_cap_usd": mc, "change_24h_pct": ch},
    )


@dataclass(frozen=True)
class RankingResult:
    momentum_score: float
    sentiment_score: float
    liquidity_score: float
    risk_score: float
    credibility_score: float
    final_score: float
    weights: dict[str, float]


def rank_opportunity(
    *,
    momentum_score: float,
    sentiment_score: float,
    liquidity_score: float,
    risk_score: float,
    credibility_score: float,
) -> RankingResult:
    # Higher is better; risk is subtracted
    weights = {
        "momentum": 0.32,
        "sentiment": 0.22,
        "liquidity": 0.18,
        "credibility": 0.18,
        "risk": 0.20,
    }
    final = (
        weights["momentum"] * momentum_score
        + weights["sentiment"] * sentiment_score
        + weights["liquidity"] * liquidity_score
        + weights["credibility"] * credibility_score
        - weights["risk"] * risk_score
    )
    final = max(0.0, min(1.0, final))
    return RankingResult(
        momentum_score=max(0.0, min(1.0, momentum_score)),
        sentiment_score=max(0.0, min(1.0, sentiment_score)),
        liquidity_score=max(0.0, min(1.0, liquidity_score)),
        risk_score=max(0.0, min(1.0, risk_score)),
        credibility_score=max(0.0, min(1.0, credibility_score)),
        final_score=final,
        weights=weights,
    )
