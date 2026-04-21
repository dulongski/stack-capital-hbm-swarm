from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .decision_schemas import AgentProfile, FinancialDecision


ACCESS_WEIGHT = {
    "public": 1.0,
    "channel": 1.12,
    "internal": 1.25,
    "market_microstructure": 0.82,
}

DIRECTION_SIGN = {
    "positive": 1.0,
    "negative": -1.0,
    "mixed": 0.25,
    "neutral": 0.0,
}

TICKER_SIGNAL_PRIORS = {
    "AMZN": 0.80,
    "GOOGL": 0.76,
    "MSFT": 0.78,
    "ASML": 0.68,
    "AMAT": 0.72,
    "LRCX": 0.70,
    "8035.T": 0.66,
    "NVDA": 0.88,
    "005930.KS": 0.74,
    "000660.KS": 0.58,
    "MU": 1.15,
}


def _clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def synthesize(decisions: list[FinancialDecision], roster: list[AgentProfile]) -> dict[str, Any]:
    agents = {agent.agent_id: agent for agent in roster}
    ticker_scores: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    node_scores: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    quarter_scores: dict[str, list[float]] = defaultdict(list)
    participant_scores: dict[str, list[float]] = defaultdict(list)

    for decision in decisions:
        agent = agents[decision.agent_id]
        magnitude = abs(decision.magnitude)
        sign = DIRECTION_SIGN[decision.direction]
        if decision.direction == "mixed" and decision.magnitude < 0:
            sign = -0.25
        relevance = 1.15 if set(decision.affected_nodes) & set(agent.covered_nodes) else 0.85
        weight = agent.credibility_weight * decision.confidence * ACCESS_WEIGHT[agent.information_access] * relevance
        signed = sign * max(1, magnitude) * weight
        capacity = 3 * weight
        record = {
            "signed": signed,
            "capacity": capacity,
            "direction": decision.direction,
            "confidence": decision.confidence,
            "weight": weight,
        }
        for ticker in decision.affected_tickers:
            ticker_scores[ticker].append(record)
        for node in decision.affected_nodes:
            node_scores[node].append(record)
        quarter_scores[decision.quarter].append(signed)
        participant_scores[decision.participant_type].append(signed)

    def summarize_bucket(records: list[dict[str, float | str]], ticker: str | None = None) -> dict[str, Any]:
        signed_sum = sum(float(record["signed"]) for record in records)
        capacity_sum = sum(float(record["capacity"]) for record in records) or 1.0
        positives = sum(1 for record in records if record["direction"] == "positive")
        negatives = sum(1 for record in records if record["direction"] == "negative")
        mixed = sum(1 for record in records if record["direction"] == "mixed")
        disagreement = 0.0
        if positives + negatives > 0:
            disagreement = min(positives, negatives) / max(positives, negatives)
        raw_score = 100 * signed_sum / capacity_sum
        if ticker:
            exposure = TICKER_SIGNAL_PRIORS.get(ticker, 0.70)
            evidence_depth = min(1.0, len(records) / 36)
            concentration_penalty = 0.82 + 0.18 * evidence_depth
            disagreement_penalty = 1 - (0.34 * disagreement)
            raw_score = raw_score * exposure * concentration_penalty * disagreement_penalty
        return {
            "net_signal_score": round(_clamp(raw_score), 2),
            "decision_count": len(records),
            "avg_confidence": round(mean(float(record["confidence"]) for record in records), 3),
            "disagreement_score": round(disagreement, 3),
            "positive_count": positives,
            "negative_count": negatives,
            "mixed_count": mixed,
        }

    ticker_summary = {ticker: summarize_bucket(records, ticker) for ticker, records in ticker_scores.items()}
    node_summary = {node: summarize_bucket(records) for node, records in node_scores.items()}
    top_positive = sorted(ticker_summary.items(), key=lambda item: item[1]["net_signal_score"], reverse=True)[:8]
    top_negative = sorted(ticker_summary.items(), key=lambda item: item[1]["net_signal_score"])[:8]
    bottlenecks = sorted(
        node_summary.items(),
        key=lambda item: (item[1]["decision_count"], abs(item[1]["net_signal_score"])),
        reverse=True,
    )[:6]

    return {
        "decision_count": len(decisions),
        "ticker_summary": ticker_summary,
        "node_summary": node_summary,
        "quarter_summary": {quarter: round(mean(values), 3) for quarter, values in quarter_scores.items()},
        "participant_summary": {
            participant: round(mean(values), 3) for participant, values in participant_scores.items()
        },
        "top_positive_tickers": [{"ticker": ticker, **summary} for ticker, summary in top_positive],
        "top_negative_tickers": [{"ticker": ticker, **summary} for ticker, summary in top_negative],
        "key_bottleneck_nodes": [{"node": node, **summary} for node, summary in bottlenecks],
        "portfolio_view": {
            "long_candidates": [ticker for ticker, summary in top_positive if summary["net_signal_score"] > 10],
            "short_or_underweight_candidates": [
                ticker for ticker, summary in top_negative if summary["net_signal_score"] < 0
            ],
            "pair_trade_candidates": ["Long equipment/capex beneficiaries vs underweight MU if signal split persists"],
            "watchlist": ["advanced packaging substrate suppliers", "HBM share data", "hyperscaler deployment cadence"],
        },
    }


def write_synthesis(decisions: list[FinancialDecision], roster: list[AgentProfile], output_path: Path) -> dict[str, Any]:
    output = synthesize(decisions, roster)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    return output
