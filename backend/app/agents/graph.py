from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    data_collector_node,
    onchain_node,
    pattern_detection_node,
    ranking_node,
    report_generator_node,
    sentiment_node,
    validation_node,
)
from app.agents.state import AgentState


def build_graph(*, db, coingecko, binance):
    g: StateGraph[AgentState] = StateGraph(AgentState)

    g.add_node("fetch_data", partial(data_collector_node, db=db, coingecko=coingecko, binance=binance))
    g.add_node("onchain", partial(onchain_node, db=db))
    g.add_node("sentiment", partial(sentiment_node, db=db))
    g.add_node("patterns", partial(pattern_detection_node, db=db))
    g.add_node("validation", partial(validation_node, db=db))
    g.add_node("ranking", partial(ranking_node, db=db))
    g.add_node("report", partial(report_generator_node, db=db))

    g.set_entry_point("fetch_data")

    g.add_edge("fetch_data", "onchain")
    g.add_edge("onchain", "sentiment")
    g.add_edge("sentiment", "patterns")
    g.add_edge("patterns", "validation")
    g.add_edge("validation", "ranking")
    g.add_edge("ranking", "report")
    g.add_edge("report", END)

    return g.compile()
