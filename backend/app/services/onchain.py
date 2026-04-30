from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone
from typing import Any


def _seed(symbol: str) -> int:
    h = hashlib.sha256(symbol.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def simulate_onchain_whale_activity(
    *,
    symbol: str,
    market_cap_usd: float | None,
    volume_24h_usd: float | None,
) -> dict[str, Any]:
    """
    Deterministic simulation (seeded by symbol) so runs are stable.
    Replace with real on-chain indexer when you add one (e.g., Etherscan, Alchemy, Bitquery).
    """
    rng = random.Random(_seed(symbol))
    ts = datetime.now(tz=timezone.utc).isoformat()

    mc = market_cap_usd or 0.0
    vol = volume_24h_usd or 0.0
    base = min(1.0, (vol / 50_000_000.0) + (mc / 5_000_000_000.0))
    whale_prob = min(0.85, 0.1 + 0.6 * base)

    is_whale = rng.random() < whale_prob
    if not is_whale:
        return {"ts": ts, "whale": False, "transfers": []}

    transfers = []
    n = 1 + (1 if rng.random() < 0.35 else 0) + (1 if rng.random() < 0.15 else 0)
    for _ in range(n):
        amount_usd = max(25_000.0, rng.lognormvariate(12.0, 0.8))  # heavy tail
        direction = "inflow" if rng.random() < 0.55 else "outflow"
        transfers.append(
            {
                "amount_usd": round(amount_usd, 2),
                "direction": direction,
                "network": "simulated",
                "from": f"0x{rng.getrandbits(80):020x}",
                "to": f"0x{rng.getrandbits(80):020x}",
            }
        )

    total_usd = sum(t["amount_usd"] for t in transfers)
    intensity = min(1.0, total_usd / max(1.0, (vol or 1.0)) * 10.0)
    return {"ts": ts, "whale": True, "transfers": transfers, "total_usd": total_usd, "intensity": intensity}
