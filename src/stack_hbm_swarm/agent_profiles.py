from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decision_schemas import AgentProfile
from .subgraph_selector import CORE_TICKERS


def _persona(role: str, focus: str, access: str) -> str:
    return (
        f"You are a {role} in a financial-market simulation of Samsung achieving HBM4 yield parity "
        f"with SK Hynix on March 31, 2026. Focus on {focus}. Your information access is {access}. "
        "Return only role-native structured decisions with explicit assumptions and risks."
    )


def build_agent_roster(subgraph: dict[str, Any]) -> list[AgentProfile]:
    agents: list[AgentProfile] = []

    def add(
        participant_type: str,
        count: int,
        base_name: str,
        covered_nodes: list[str],
        covered_tickers: list[str],
        access: str,
        credibility: float,
        bias_profile: str,
        focus: str,
    ) -> None:
        start = len(agents) + 1
        for idx in range(count):
            agent_no = start + idx
            agents.append(
                AgentProfile(
                    agent_id=f"a{agent_no:02d}",
                    name=f"{base_name} {idx + 1}",
                    participant_type=participant_type,  # type: ignore[arg-type]
                    covered_nodes=covered_nodes,
                    covered_tickers=covered_tickers,
                    information_access=access,  # type: ignore[arg-type]
                    credibility_weight=credibility,
                    bias_profile=bias_profile,
                    persona=_persona(base_name, focus, access),
                )
            )

    add(
        "sell_side_analyst",
        5,
        "Sell-side semiconductor analyst",
        ["3.3", "3.1", "3.5", "2.1", "2.2", "2.3"],
        ["MU", "005930.KS", "000660.KS", "NVDA", "ASML", "AMAT", "LRCX", "8035.T"],
        "public",
        0.72,
        "balanced_revisionist",
        "estimate revisions, ratings, price targets, and relative valuation across memory and equipment",
    )
    add(
        "buy_side_pm",
        5,
        "Buy-side portfolio manager",
        ["3.3", "3.1", "3.5", "6.1", "9.3"],
        list(CORE_TICKERS),
        "channel",
        0.82,
        "portfolio_risk_reward",
        "multi-name position sizing, hedges, and where the catalyst creates asymmetric risk",
    )
    add(
        "procurement_exec",
        4,
        "Hyperscaler procurement executive",
        ["3.1", "3.3", "5.1", "6.1", "9.3"],
        ["AMZN", "GOOGL", "MSFT", "NVDA", "MU", "005930.KS", "000660.KS"],
        "internal",
        0.86,
        "bottleneck_relief",
        "vendor allocation, deployment timing, and negotiating leverage from a credible third HBM4 source",
    )
    add(
        "nvidia_supply",
        3,
        "NVIDIA supply-chain leader",
        ["3.1", "3.3", "3.5", "4.2", "5.1"],
        ["NVDA", "MU", "005930.KS", "000660.KS"],
        "internal",
        0.90,
        "platform_ramp",
        "Rubin qualification, HBM supplier mix, packaging allocation, and GPU shipment unlocks",
    )
    add(
        "memory_exec",
        2,
        "Micron executive",
        ["3.3", "3.5"],
        ["MU", "005930.KS", "000660.KS"],
        "internal",
        0.80,
        "defend_micron_margin",
        "pricing strategy, committed HBM supply, customer contracts, and competitive narrative",
    )
    add(
        "memory_exec",
        2,
        "Samsung executive",
        ["3.3", "3.5"],
        ["005930.KS", "MU", "NVDA", "000660.KS"],
        "internal",
        0.80,
        "share_capture",
        "HBM4 yield ramp, share gains, and customer contract strategy",
    )
    add(
        "memory_exec",
        2,
        "SK Hynix executive",
        ["3.3", "3.5"],
        ["000660.KS", "005930.KS", "MU", "NVDA"],
        "internal",
        0.80,
        "share_capture",
        "HBM leadership defense, customer allocation, and competitive response",
    )
    add(
        "equipment_rep",
        5,
        "Semiconductor equipment representative",
        ["2.1", "2.2", "2.3", "3.3", "3.5"],
        ["ASML", "AMAT", "LRCX", "8035.T", "MU", "005930.KS", "000660.KS"],
        "channel",
        0.76,
        "capex_cycle",
        "tool orders, memory capacity expansion, process-control intensity, and advanced packaging equipment",
    )
    add(
        "trader",
        4,
        "Short-term trader or quant fund",
        ["3.3", "3.1", "2.1", "2.2", "9.3"],
        ["MU", "NVDA", "ASML", "AMAT", "LRCX", "AMZN", "GOOGL", "MSFT"],
        "market_microstructure",
        0.56,
        "flow_driven",
        "positioning, options skew, crowded trades, and relative-value reactions",
    )

    if len(agents) != 32:
        raise RuntimeError(f"expected 32 agents, built {len(agents)}")
    return agents


def write_agent_roster(subgraph: dict[str, Any], output_path: Path) -> list[AgentProfile]:
    roster = build_agent_roster(subgraph)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([agent.model_dump() for agent in roster], indent=2))
    return roster


def load_agent_roster(path: Path) -> list[AgentProfile]:
    return [AgentProfile.model_validate(item) for item in json.loads(path.read_text())]
