from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"
RUNS_DIR = PROJECT_ROOT / "runs"
DOCS_DIR = PROJECT_ROOT / "docs"

TAXONOMY_PATH = INPUT_DIR / "taxonomy_tickers.json"
DEPENDENCY_GRAPH_PATH = INPUT_DIR / "dependency_graph.json"
SELECTED_SUBGRAPH_PATH = PROCESSED_DIR / "selected_subgraph.json"
AGENT_ROSTER_PATH = PROCESSED_DIR / "agent_roster.json"


@dataclass(frozen=True)
class RuntimeConfig:
    openrouter_api_key: str | None
    fmp_api_key: str | None
    zep_api_key: str | None
    openrouter_model: str
    openrouter_small_model: str
    simulation_budget_usd: float

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            fmp_api_key=os.getenv("FMP_API_KEY"),
            zep_api_key=os.getenv("ZEP_API_KEY"),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1"),
            openrouter_small_model=os.getenv("OPENROUTER_SMALL_MODEL", "qwen/qwen3-14b"),
            simulation_budget_usd=float(os.getenv("SIMULATION_BUDGET_USD", "200")),
        )


def ensure_directories() -> None:
    for path in (INPUT_DIR, PROCESSED_DIR, CACHE_DIR, RUNS_DIR, DOCS_DIR):
        path.mkdir(parents=True, exist_ok=True)

