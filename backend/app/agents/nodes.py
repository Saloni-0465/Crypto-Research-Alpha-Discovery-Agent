from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState, CoinContext
from app.repositories.coins import upsert_coin
from app.repositories.logs import log_step
from app.repositories.market_data import insert_market_data, latest_market_snapshots
from app.repositories.opportunities import insert_opportunity
from app.repositories.reports import insert_report
from app.repositories.signals import insert_signal
from app.services.binance import BinanceClient
from app.services.coingecko import CoinGeckoClient
from app.services.onchain import simulate_onchain_whale_activity
from app.services.patterns import detect_patterns
from app.services.scoring import rank_opportunity, validate_token
from app.services.sentiment import analyze_sentiment
from app.services.vector_store import embed_text, vector_store_from_settings


async def data_collector_node(state: AgentState, *, db: AsyncSession, coingecko: CoinGeckoClient, binance: BinanceClient) -> AgentState:
    run_id = state["run_id"]

    try:
        async with log_step(db, run_id=run_id, agent="data_collector", step="fetch_trending", input={"mode": state["mode"]}) as logged:
            trending = await coingecko.trending()
            logged["output"].update({"trending_count": len(trending), "sample": trending[:5]})

        ids = [c["coingecko_id"] for c in trending if c.get("coingecko_id")]
        async with log_step(db, run_id=run_id, agent="data_collector", step="fetch_markets", input={"ids": ids[:20]}) as logged:
            markets = await coingecko.markets(ids=ids[:20])
            logged["output"].update({"markets_count": len(markets)})
    except Exception as exc:  # noqa: BLE001
        async with log_step(db, run_id=run_id, agent="data_collector", step="cached_markets", input={"reason": type(exc).__name__}) as logged:
            cached = await latest_market_snapshots(db, limit=20)
            markets = [
                {
                    **(market.raw or {}),
                    "id": coin.coingecko_id,
                    "symbol": coin.symbol,
                    "name": coin.name,
                    "current_price": market.price_usd,
                    "total_volume": market.volume_24h_usd,
                    "market_cap": market.market_cap_usd,
                    "price_change_percentage_24h": market.change_24h_pct,
                }
                for coin, market in cached
            ]
            logged["output"].update({"markets_count": len(markets), "fallback": "latest_cached_market_data"})

    coins: list[CoinContext] = []
    now = datetime.now(tz=timezone.utc)

    for row in markets:
        m = coingecko.normalize_market_row(row)
        if not m["symbol"]:
            continue

        coin = await upsert_coin(db, symbol=m["symbol"], name=m["name"], coingecko_id=m["coingecko_id"])
        await insert_market_data(
            db,
            coin_id=coin.id,
            source="coingecko",
            ts=now,
            price_usd=m["price_usd"],
            volume_24h_usd=m["volume_24h_usd"],
            market_cap_usd=m["market_cap_usd"],
            change_24h_pct=m["change_24h_pct"],
            raw=m["raw"],
        )

        # Optional: enrich with Binance if symbol exists as <SYMBOL>USDT
        ticker = await binance.ticker_24hr(f"{m['symbol']}USDT")
        if ticker:
            b = binance.normalize_ticker(ticker)
            await insert_market_data(
                db,
                coin_id=coin.id,
                source="binance",
                ts=now,
                price_usd=b["price_usd"],
                volume_24h_usd=b["volume_24h_usd"],
                market_cap_usd=None,
                change_24h_pct=b["change_24h_pct"],
                raw=b["raw"],
            )

        coins.append(
            {
                "coin_id": coin.id,
                "symbol": coin.symbol,
                "name": coin.name,
                "coingecko_id": coin.coingecko_id,
                "market": {
                    "ts": now.isoformat(),
                    "price_usd": m["price_usd"],
                    "volume_24h_usd": m["volume_24h_usd"],
                    "market_cap_usd": m["market_cap_usd"],
                    "change_24h_pct": m["change_24h_pct"],
                },
            }
        )

    async with log_step(db, run_id=run_id, agent="data_collector", step="persisted", input={"coins": len(coins)}) as logged:
        logged["output"].update({"coins_persisted": len(coins)})

    state["coins"] = coins
    return state


async def onchain_node(state: AgentState, *, db: AsyncSession) -> AgentState:
    run_id = state["run_id"]
    for c in state["coins"]:
        market = c.get("market") or {}
        onchain = simulate_onchain_whale_activity(
            symbol=c["symbol"], market_cap_usd=market.get("market_cap_usd"), volume_24h_usd=market.get("volume_24h_usd")
        )
        c["onchain"] = onchain
        if onchain.get("whale"):
            await insert_signal(
                db,
                coin_id=c["coin_id"],
                agent="onchain",
                kind="whale_activity",
                ts=datetime.now(tz=timezone.utc),
                score=float(onchain.get("intensity") or 0.5),
                confidence=0.55,
                data=onchain,
            )

    async with log_step(db, run_id=run_id, agent="onchain", step="done", input={"coins": len(state["coins"])}) as logged:
        logged["output"].update({"signals": "whale_activity when detected"})
    return state


async def sentiment_node(state: AgentState, *, db: AsyncSession) -> AgentState:
    run_id = state["run_id"]
    for c in state["coins"]:
        market = c.get("market") or {}
        res = await analyze_sentiment(
            symbol=c["symbol"],
            name=c["name"],
            change_24h_pct=market.get("change_24h_pct"),
            volume_24h_usd=market.get("volume_24h_usd"),
            market_cap_usd=market.get("market_cap_usd"),
            news_snippets=None,
        )
        c["sentiment"] = res
        label = res["label"]
        score = 1.0 if label == "bullish" else 0.0 if label == "bearish" else 0.5
        await insert_signal(
            db,
            coin_id=c["coin_id"],
            agent="sentiment",
            kind="sentiment",
            ts=datetime.now(tz=timezone.utc),
            score=score,
            confidence=float(res["confidence"]),
            data=res,
        )

    async with log_step(db, run_id=run_id, agent="sentiment", step="done", input={"coins": len(state["coins"])}) as logged:
        logged["output"].update({"signals_written": len(state["coins"])})
    return state


async def pattern_detection_node(state: AgentState, *, db: AsyncSession) -> AgentState:
    run_id = state["run_id"]
    total = 0
    for c in state["coins"]:
        market = c.get("market") or {}
        patterns = detect_patterns(
            change_24h_pct=market.get("change_24h_pct"),
            volume_24h_usd=market.get("volume_24h_usd"),
            market_cap_usd=market.get("market_cap_usd"),
        )
        c["patterns"] = [p.__dict__ for p in patterns]
        for p in patterns:
            total += 1
            await insert_signal(
                db,
                coin_id=c["coin_id"],
                agent="pattern",
                kind=p.kind,
                ts=datetime.now(tz=timezone.utc),
                score=p.score,
                confidence=p.confidence,
                data=p.data,
            )

    async with log_step(db, run_id=run_id, agent="pattern", step="done", input={"coins": len(state["coins"])}) as logged:
        logged["output"].update({"pattern_signals_written": total})
    return state


async def validation_node(state: AgentState, *, db: AsyncSession) -> AgentState:
    run_id = state["run_id"]
    for c in state["coins"]:
        market = c.get("market") or {}
        onchain = c.get("onchain") or {}
        vr = validate_token(
            volume_24h_usd=market.get("volume_24h_usd"),
            market_cap_usd=market.get("market_cap_usd"),
            change_24h_pct=market.get("change_24h_pct"),
            has_whale=bool(onchain.get("whale")),
        )
        c["validation"] = {
            "credibility_score": vr.credibility_score,
            "liquidity_score": vr.liquidity_score,
            "risk_score": vr.risk_score,
            "flags": vr.flags,
            "meta": vr.meta,
        }

    async with log_step(db, run_id=run_id, agent="validation", step="done", input={"coins": len(state["coins"])}) as logged:
        logged["output"].update({"validated": len(state["coins"])})
    return state


async def ranking_node(state: AgentState, *, db: AsyncSession) -> AgentState:
    run_id = state["run_id"]
    for c in state["coins"]:
        market = c.get("market") or {}
        sent = c.get("sentiment") or {}
        patterns = c.get("patterns") or []
        vr = c.get("validation") or {}

        # Momentum: based on positive change + pattern support
        ch = float(market.get("change_24h_pct") or 0.0)
        mom = max(0.0, min(1.0, (ch - 1.0) / 25.0))
        if any(p.get("kind") == "momentum_breakout" for p in patterns):
            mom = min(1.0, mom + 0.15)

        label = sent.get("label", "neutral")
        sentiment_score = 1.0 if label == "bullish" else 0.0 if label == "bearish" else 0.5
        rr = rank_opportunity(
            momentum_score=mom,
            sentiment_score=sentiment_score,
            liquidity_score=float(vr.get("liquidity_score") or 0.0),
            risk_score=float(vr.get("risk_score") or 0.0),
            credibility_score=float(vr.get("credibility_score") or 0.0),
        )
        c["ranking"] = {
            "momentum_score": rr.momentum_score,
            "sentiment_score": rr.sentiment_score,
            "liquidity_score": rr.liquidity_score,
            "risk_score": rr.risk_score,
            "credibility_score": rr.credibility_score,
            "final_score": rr.final_score,
            "weights": rr.weights,
        }

    async with log_step(db, run_id=run_id, agent="ranking", step="done", input={"coins": len(state["coins"])}) as logged:
        logged["output"].update({"ranked": len(state["coins"])})
    return state


async def report_generator_node(state: AgentState, *, db: AsyncSession) -> AgentState:
    run_id = state["run_id"]
    coins = state["coins"]
    coins_sorted = sorted(coins, key=lambda c: float((c.get("ranking") or {}).get("final_score") or 0.0), reverse=True)

    store = None

    top = []
    opportunities_created = 0
    for c in coins_sorted[:10]:
        r = c.get("ranking") or {}
        v = c.get("validation") or {}
        s = c.get("sentiment") or {}
        market = c.get("market") or {}
        onchain = c.get("onchain") or {}
        patterns = c.get("patterns") or []

        flags = v.get("flags") or []
        reasoning = (
            f"{c['symbol']} scored {r.get('final_score', 0):.2f}. "
            f"Momentum {r.get('momentum_score', 0):.2f}, sentiment {s.get('label','neutral')} "
            f"({s.get('confidence',0):.2f}), liquidity {v.get('liquidity_score',0):.2f}, "
            f"risk {v.get('risk_score',0):.2f}. "
            f"{'Flags: ' + ', '.join(flags) + '. ' if flags else ''}"
        )

        opp = await insert_opportunity(
            db,
            coin_id=c["coin_id"],
            momentum_score=float(r.get("momentum_score") or 0.0),
            sentiment_score=float(r.get("sentiment_score") or 0.0),
            liquidity_score=float(r.get("liquidity_score") or 0.0),
            risk_score=float(r.get("risk_score") or 0.0),
            credibility_score=float(r.get("credibility_score") or 0.0),
            final_score=float(r.get("final_score") or 0.0),
            reasoning=reasoning,
            evidence={"market": market, "sentiment": s, "onchain": onchain, "patterns": patterns, "validation": v},
        )
        vec, embed_meta = await embed_text(reasoning)
        if vec is not None:
            if store is None:
                store = vector_store_from_settings(dim=len(vec))
            embedding_id = store.add(
                vector=vec,
                meta={"type": "opportunity", "opportunity_id": str(opp.id), "coin_symbol": c["symbol"], "run_id": str(run_id), **embed_meta},
            )
            opp.embedding_id = embedding_id
            await db.flush()
        opportunities_created += 1
        top.append(
            {
                "opportunity_id": str(opp.id),
                "coin": {"symbol": c["symbol"], "name": c["name"], "coin_id": str(c["coin_id"])},
                "final_score": r.get("final_score"),
                "reasoning": reasoning,
                "evidence": {"market": market, "sentiment": s, "patterns": patterns, "onchain": onchain, "flags": flags},
            }
        )

    summary = "Top opportunities ranked by momentum, sentiment, liquidity, credibility, and risk."
    payload = {"run_id": str(run_id), "generated_at": datetime.now(tz=timezone.utc).isoformat(), "top": top}
    report = await insert_report(db, title="Alpha Report", summary=summary, payload=payload)

    async with log_step(db, run_id=run_id, agent="report", step="done", input={"coins": len(coins)}) as logged:
        logged["output"].update({"report_id": str(report.id), "top_count": len(top), "opportunities_created": opportunities_created})

    state["notes"].append(f"report_id={report.id}")
    return state
