from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .decision_schemas import AgentProfile, FinancialDecision, validate_decision_payload
from .llm_client import OpenRouterClient


DEFAULT_QUARTERS = ("2026Q2", "2026Q3", "2026Q4", "2027Q1")

QUARTER_THEMES = {
    "2026Q2": "Immediate market repricing after Samsung yield parity and NVIDIA initial qualification.",
    "2026Q3": "Samsung volume shipments begin and hyperscalers renegotiate supplier allocation.",
    "2026Q4": "Samsung targets HBM4 at 40% of HBM revenue and bottlenecks move toward packaging.",
    "2027Q1": "Contract renewal expectations, capex responses, and competitive margin reset become visible.",
}

TYPE_DECISION = {
    "sell_side_analyst": "estimate_revision",
    "buy_side_pm": "position_adjustment",
    "procurement_exec": "vendor_allocation_change",
    "nvidia_supply": "platform_ramp_change",
    "memory_exec": "pricing_strategy",
    "equipment_rep": "tool_order_signal",
    "trader": "relative_value_signal",
}


def _direction_and_magnitude(agent: AgentProfile, quarter: str) -> tuple[str, int]:
    bias = agent.bias_profile
    if "defend_micron" in bias:
        return ("negative", -2 if quarter in {"2026Q2", "2026Q3"} else -1)
    if "share_capture" in bias:
        return ("positive", 2 if quarter in {"2026Q2", "2026Q3"} else 1)
    if "bottleneck_relief" in bias or "platform_ramp" in bias:
        return ("positive", 2 if quarter in {"2026Q3", "2026Q4"} else 1)
    if "capex_cycle" in bias:
        return ("positive", 2 if quarter in {"2026Q4", "2027Q1"} else 1)
    if "flow_driven" in bias:
        return ("mixed", 1 if quarter in {"2026Q2", "2026Q3"} else 0)
    if "portfolio" in bias:
        return ("mixed", -1)
    if "balanced_revisionist" in bias:
        return ("negative", -2 if quarter in {"2026Q2", "2026Q3"} else -1)
    return ("mixed", 1)


def _affected_tickers(agent: AgentProfile) -> list[str]:
    if agent.bias_profile == "defend_micron_margin":
        return ["MU", "005930.KS", "000660.KS"]
    if agent.bias_profile == "share_capture":
        return ["005930.KS", "000660.KS", "MU"]
    if agent.bias_profile == "balanced_revisionist":
        return ["MU"]
    if agent.bias_profile == "portfolio_risk_reward":
        return ["MU"]
    if agent.bias_profile == "capex_cycle":
        return [ticker for ticker in agent.covered_tickers if ticker in {"ASML", "AMAT", "LRCX", "8035.T"}]
    if agent.bias_profile in {"bottleneck_relief", "platform_ramp"}:
        return [ticker for ticker in agent.covered_tickers if ticker in {"NVDA", "AMZN", "GOOGL", "MSFT", "005930.KS"}]
    if agent.participant_type == "trader":
        return ["MU", "NVDA", "005930.KS", "000660.KS"]
    return agent.covered_tickers[:5]


def deterministic_decision(agent: AgentProfile, quarter: str, subgraph: dict[str, Any]) -> FinancialDecision:
    direction, magnitude = _direction_and_magnitude(agent, quarter)
    tickers = _affected_tickers(agent) or agent.covered_tickers[:3]
    nodes = [node for node in agent.covered_nodes if node in subgraph["nodes"]][:4] or agent.covered_nodes[:2]
    confidence_boost = {
        "internal": 0.10,
        "channel": 0.05,
        "market_microstructure": -0.05,
        "public": 0.0,
    }[agent.information_access]
    confidence = min(0.92, max(0.45, agent.credibility_weight + confidence_boost - 0.08))
    reasoning = (
        f"{QUARTER_THEMES[quarter]} {agent.name} interprets the Samsung HBM4 catalyst through "
        f"{agent.bias_profile}: the event changes supplier leverage, HBM availability, packaging load, "
        "and downstream deployment timing rather than creating a single-stock Micron-only signal."
    )
    payload = {
        "quarter": quarter,
        "agent_id": agent.agent_id,
        "participant_type": agent.participant_type,
        "decision_type": TYPE_DECISION[agent.participant_type],
        "affected_nodes": nodes,
        "affected_tickers": tickers,
        "direction": direction,
        "magnitude": magnitude,
        "confidence": round(confidence, 2),
        "horizon_months": 3 if quarter != "2027Q1" else 6,
        "reasoning": reasoning,
        "key_assumptions": [
            "Samsung HBM4 yield parity is treated as factual for the simulation.",
            "Packaging and substrate capacity remain relevant constraints even if HBM supply loosens.",
        ],
        "risk_flags": [
            "NVIDIA qualification may not translate linearly into volume share.",
            "Existing long-term supply agreements can delay price discovery.",
        ],
    }
    return validate_decision_payload(payload)


def llm_decision(
    agent: AgentProfile,
    quarter: str,
    subgraph: dict[str, Any],
    client: OpenRouterClient,
) -> FinancialDecision:
    system_prompt = (
        "You produce one JSON object matching the FinancialDecision schema. "
        "No markdown. Use only the allowed decision type for the participant."
    )
    user_prompt = json.dumps(
        {
            "quarter": quarter,
            "theme": QUARTER_THEMES[quarter],
            "agent": agent.model_dump(),
            "available_nodes": {node_id: node["name"] for node_id, node in subgraph["nodes"].items()},
            "schema_rules": {
                "direction": ["positive", "negative", "mixed", "neutral"],
                "magnitude": "integer -3..3; negative direction must be <=0; positive direction must be >=0",
                "decision_type": TYPE_DECISION[agent.participant_type],
            },
        },
        indent=2,
    )
    result = client.complete_json(system_prompt, user_prompt)
    try:
        return validate_decision_payload(json.loads(result.content))
    except (json.JSONDecodeError, ValidationError):
        repair_prompt = (
            "Repair this into valid JSON for the schema. Keep the same economic conclusion where possible.\n"
            f"Bad payload:\n{result.content}"
        )
        repaired = client.complete_json(system_prompt, repair_prompt)
        return validate_decision_payload(json.loads(repaired.content))


def run_simulation(
    roster: list[AgentProfile],
    subgraph: dict[str, Any],
    run_dir: Path,
    quarters: list[str] | None = None,
    *,
    use_llm: bool = False,
    dry_run: bool = False,
    llm_client: OpenRouterClient | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    selected_quarters = quarters or list(DEFAULT_QUARTERS)
    decisions: list[FinancialDecision] = []
    rejected: list[dict[str, Any]] = []

    for quarter in selected_quarters:
        if quarter not in QUARTER_THEMES:
            raise ValueError(f"unsupported quarter: {quarter}")
        active_roster = roster[:6] if dry_run else roster
        for agent in active_roster:
            try:
                decision = (
                    llm_decision(agent, quarter, subgraph, llm_client)
                    if use_llm and llm_client is not None
                    else deterministic_decision(agent, quarter, subgraph)
                )
                decisions.append(decision)
            except Exception as exc:  # noqa: BLE001 - logged as rejected simulation record
                rejected.append({"quarter": quarter, "agent_id": agent.agent_id, "error": str(exc)})

    decision_log = run_dir / "decision_log.jsonl"
    with decision_log.open("w") as handle:
        for decision in decisions:
            handle.write(json.dumps(decision.model_dump()) + "\n")

    metadata = {
        "run_id": run_dir.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "llm" if use_llm else "offline_deterministic",
        "dry_run": dry_run,
        "quarters": selected_quarters,
        "agent_count": len(roster),
        "active_agent_count": len(roster[:6] if dry_run else roster),
        "decision_count": len(decisions),
        "rejected_count": len(rejected),
        "rejected": rejected,
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata


def load_decisions(path: Path) -> list[FinancialDecision]:
    decisions = []
    with path.open() as handle:
        for line in handle:
            if line.strip():
                decisions.append(FinancialDecision.model_validate_json(line))
    return decisions
