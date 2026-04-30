from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatternFinding:
    kind: str
    score: float  # 0..1
    confidence: float  # 0..1
    data: dict[str, Any]


def detect_patterns(*, change_24h_pct: float | None, volume_24h_usd: float | None, market_cap_usd: float | None) -> list[PatternFinding]:
    findings: list[PatternFinding] = []

    ch = float(change_24h_pct or 0.0)
    vol = float(volume_24h_usd or 0.0)
    mc = float(market_cap_usd or 0.0)

    # Volume spike heuristic: compare volume to market cap (rough proxy)
    if mc > 0:
        turnover = vol / mc
        if turnover > 0.25 and vol > 5_000_000:
            findings.append(
                PatternFinding(
                    kind="volume_spike",
                    score=min(1.0, (turnover - 0.25) / 0.75),
                    confidence=0.7,
                    data={"turnover": turnover, "volume_24h_usd": vol, "market_cap_usd": mc},
                )
            )

    # Momentum breakout: large positive change
    if ch > 7.5:
        findings.append(
            PatternFinding(
                kind="momentum_breakout",
                score=min(1.0, (ch - 7.5) / 25.0),
                confidence=0.65,
                data={"change_24h_pct": ch},
            )
        )

    # Volatility: absolute move large
    if abs(ch) > 12.5:
        findings.append(
            PatternFinding(
                kind="volatility_breakout",
                score=min(1.0, (abs(ch) - 12.5) / 35.0),
                confidence=0.6,
                data={"change_24h_pct": ch},
            )
        )

    return findings
