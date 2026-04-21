from pathlib import Path

from stack_hbm_swarm.config import DEPENDENCY_GRAPH_PATH, TAXONOMY_PATH
from stack_hbm_swarm.graph_loader import load_value_chain_graph
from stack_hbm_swarm.subgraph_selector import REQUIRED_NODES, select_hbm_subgraph


def test_loader_handles_object_shaped_layers() -> None:
    graph = load_value_chain_graph(TAXONOMY_PATH, DEPENDENCY_GRAPH_PATH)
    assert graph.total_nodes == 87
    assert graph.total_companies == 987
    assert graph.edge_count == 544
    assert graph.nodes["3.3"].name.startswith("Memory")


def test_subgraph_selector_includes_required_nodes() -> None:
    graph = load_value_chain_graph(TAXONOMY_PATH, DEPENDENCY_GRAPH_PATH)
    subgraph = select_hbm_subgraph(graph)
    assert set(REQUIRED_NODES).issubset(set(subgraph["nodes"]))
    assert subgraph["node_count"] == len(REQUIRED_NODES)
    assert subgraph["edge_count"] > 0


def test_input_files_exist() -> None:
    assert Path(TAXONOMY_PATH).exists()
    assert Path(DEPENDENCY_GRAPH_PATH).exists()

