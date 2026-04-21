from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .graph_loader import DependencyEdge, TaxonomyNode, ValueChainGraph


REQUIRED_NODES = (
    "3.3",
    "3.1",
    "3.5",
    "4.2",
    "4.3",
    "2.1",
    "2.2",
    "2.3",
    "5.1",
    "6.1",
    "9.3",
)

CORE_TICKERS = (
    "MU",
    "005930.KS",
    "000660.KS",
    "NVDA",
    "AMZN",
    "GOOGL",
    "MSFT",
    "ASML",
    "AMAT",
    "LRCX",
    "8035.T",
)

PACKAGING_TICKER_LIMIT = 8


def _rank_company(ticker: str) -> tuple[int, str]:
    if ticker in CORE_TICKERS:
        return (0, ticker)
    us_listing_bonus = 1 if "." not in ticker else 2
    return (us_listing_bonus, ticker)


def companies_for_node(node: TaxonomyNode) -> list[dict[str, Any]]:
    companies = sorted(node.companies, key=lambda company: _rank_company(company.ticker))
    if node.node_id in {"3.5", "4.2", "4.3"}:
        companies = companies[:PACKAGING_TICKER_LIMIT]
    else:
        companies = [company for company in companies if company.ticker in CORE_TICKERS] or companies[:6]
    return [asdict(company) for company in companies]


def select_hbm_subgraph(graph: ValueChainGraph) -> dict[str, Any]:
    selected_nodes = {node_id: graph.nodes[node_id] for node_id in REQUIRED_NODES}
    selected_node_ids = set(selected_nodes)
    selected_edges: list[DependencyEdge] = [
        edge
        for edge in graph.edges
        if edge.from_node in selected_node_ids and edge.to_node in selected_node_ids
    ]
    boundary_edges: list[DependencyEdge] = [
        edge
        for edge in graph.edges
        if (edge.from_node in selected_node_ids) ^ (edge.to_node in selected_node_ids)
    ]

    ticker_to_nodes: dict[str, list[str]] = {}
    for node_id, node in selected_nodes.items():
        for company in companies_for_node(node):
            ticker_to_nodes.setdefault(company["ticker"], []).append(node_id)

    return {
        "scope": "Samsung HBM4 yield parity catalyst neighborhood",
        "required_nodes": list(REQUIRED_NODES),
        "core_tickers": list(CORE_TICKERS),
        "node_count": len(selected_nodes),
        "edge_count": len(selected_edges),
        "boundary_edge_count": len(boundary_edges),
        "nodes": {
            node_id: {
                "node_id": node.node_id,
                "name": node.name,
                "description": node.description,
                "layer_id": node.layer_id,
                "layer_name": node.layer_name,
                "companies": companies_for_node(node),
            }
            for node_id, node in selected_nodes.items()
        },
        "edges": [asdict(edge) for edge in selected_edges],
        "boundary_edges": [asdict(edge) for edge in boundary_edges[:80]],
        "ticker_to_nodes": ticker_to_nodes,
    }


def write_selected_subgraph(graph: ValueChainGraph, output_path: Path) -> dict[str, Any]:
    subgraph = select_hbm_subgraph(graph)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(subgraph, indent=2, sort_keys=True))
    return subgraph

