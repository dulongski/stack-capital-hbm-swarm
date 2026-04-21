from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Company:
    ticker: str
    name: str
    exchange: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class TaxonomyNode:
    node_id: str
    name: str
    description: str
    layer_id: str
    layer_name: str
    company_count: int
    companies: tuple[Company, ...]


@dataclass(frozen=True)
class DependencyEdge:
    from_node: str
    to_node: str
    relationship: str
    direction: str
    description: str


@dataclass(frozen=True)
class ValueChainGraph:
    nodes: dict[str, TaxonomyNode]
    edges: tuple[DependencyEdge, ...]
    total_nodes: int
    total_companies: int
    edge_count: int

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "total_nodes": self.total_nodes,
            "total_companies": self.total_companies,
            "edge_count": self.edge_count,
            "nodes": {node_id: asdict(node) for node_id, node in self.nodes.items()},
            "edges": [asdict(edge) for edge in self.edges],
        }


def load_taxonomy(path: Path) -> tuple[dict[str, TaxonomyNode], int, int]:
    raw = json.loads(path.read_text())
    layers = raw.get("layers")
    if not isinstance(layers, dict):
        raise ValueError("taxonomy_tickers.json must contain an object-shaped 'layers' field")

    nodes: dict[str, TaxonomyNode] = {}
    for layer_id, layer in layers.items():
        layer_name = layer["name"]
        for node_id, node in layer["nodes"].items():
            companies = tuple(
                Company(
                    ticker=company["ticker"],
                    name=company["name"],
                    exchange=company.get("exchange"),
                    country=company.get("country"),
                )
                for company in node.get("companies", [])
            )
            nodes[node_id] = TaxonomyNode(
                node_id=node_id,
                name=node["name"],
                description=node.get("description", ""),
                layer_id=layer_id,
                layer_name=layer_name,
                company_count=int(node.get("company_count", len(companies))),
                companies=companies,
            )
    return nodes, int(raw["total_nodes"]), int(raw["total_companies"])


def load_dependency_edges(path: Path) -> tuple[tuple[DependencyEdge, ...], int, int]:
    raw = json.loads(path.read_text())
    edges = tuple(
        DependencyEdge(
            from_node=edge["from_node"],
            to_node=edge["to_node"],
            relationship=edge["relationship"],
            direction=edge["direction"],
            description=edge.get("description", ""),
        )
        for edge in raw.get("edges", [])
    )
    return edges, int(raw["node_count"]), int(raw["edge_count"])


def load_value_chain_graph(taxonomy_path: Path, dependency_graph_path: Path) -> ValueChainGraph:
    nodes, taxonomy_node_count, total_companies = load_taxonomy(taxonomy_path)
    edges, graph_node_count, edge_count = load_dependency_edges(dependency_graph_path)
    if taxonomy_node_count != graph_node_count:
        raise ValueError(f"taxonomy node count {taxonomy_node_count} != dependency node count {graph_node_count}")
    if len(nodes) != taxonomy_node_count:
        raise ValueError(f"loaded {len(nodes)} nodes, expected {taxonomy_node_count}")
    if len(edges) != edge_count:
        raise ValueError(f"loaded {len(edges)} edges, expected {edge_count}")
    referenced_nodes = {edge.from_node for edge in edges} | {edge.to_node for edge in edges}
    missing = sorted(referenced_nodes - set(nodes))
    if missing:
        raise ValueError(f"dependency graph references missing nodes: {missing}")
    return ValueChainGraph(
        nodes=nodes,
        edges=edges,
        total_nodes=taxonomy_node_count,
        total_companies=total_companies,
        edge_count=edge_count,
    )
