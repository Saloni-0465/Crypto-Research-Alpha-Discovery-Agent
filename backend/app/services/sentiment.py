from __future__ import annotations

from typing import Any, Literal, TypedDict

from google.genai import types

from app.settings import settings
from app.services.gemini import extract_text, gemini_client


class SentimentResult(TypedDict):
    label: Literal["bullish", "bearish", "neutral"]
    confidence: float  # 0..1
    rationale: str
    raw: dict[str, Any]


def _heuristic_sentiment(*, change_24h_pct: float | None, volume_24h_usd: float | None) -> SentimentResult:
    ch = float(change_24h_pct or 0.0)
    vol = float(volume_24h_usd or 0.0)
    conf = min(0.85, 0.45 + min(0.4, abs(ch) / 30.0) + (0.1 if vol > 50_000_000 else 0.0))
    if ch > 2.5:
        return {"label": "bullish", "confidence": conf, "rationale": "Positive 24h trend with healthy activity.", "raw": {"mode": "heuristic"}}
    if ch < -2.5:
        return {"label": "bearish", "confidence": conf, "rationale": "Negative 24h trend suggests risk-off sentiment.", "raw": {"mode": "heuristic"}}
    return {"label": "neutral", "confidence": 0.55, "rationale": "No strong directional signal in 24h move.", "raw": {"mode": "heuristic"}}


async def analyze_sentiment(
    *,
    symbol: str,
    name: str,
    change_24h_pct: float | None,
    volume_24h_usd: float | None,
    market_cap_usd: float | None,
    news_snippets: list[str] | None = None,
) -> SentimentResult:
    if not settings.gemini_api_key:
        return _heuristic_sentiment(change_24h_pct=change_24h_pct, volume_24h_usd=volume_24h_usd)

    snippets = "\n".join(f"- {s}" for s in (news_snippets or [])[:8]) or "- (no news snippets available)"

    prompt = f"""
You are a crypto market analyst. Classify sentiment for {name} ({symbol}) using available context.

Context:
- 24h change (%): {change_24h_pct}
- 24h volume (USD): {volume_24h_usd}
- market cap (USD): {market_cap_usd}
- snippets:
{snippets}

Return STRICT JSON with keys:
label (bullish|bearish|neutral), confidence (0..1), rationale (<= 2 sentences)
""".strip()

    try:
        import json

        client = gemini_client()
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )
        content = extract_text(resp) or "{}"
        obj = json.loads(content)
        label = obj.get("label", "neutral")
        if label not in ("bullish", "bearish", "neutral"):
            label = "neutral"
        confidence = float(obj.get("confidence", 0.55))
        confidence = max(0.0, min(1.0, confidence))
        rationale = str(obj.get("rationale", "")).strip()[:400]
        return {"label": label, "confidence": confidence, "rationale": rationale, "raw": {"mode": "gemini", "model": settings.gemini_model}}
    except Exception:  # noqa: BLE001
        return _heuristic_sentiment(change_24h_pct=change_24h_pct, volume_24h_usd=volume_24h_usd)
