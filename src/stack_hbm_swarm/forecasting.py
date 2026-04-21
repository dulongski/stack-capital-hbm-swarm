from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .decision_schemas import AgentProfile, FinancialDecision
from .synthesis import ACCESS_WEIGHT, DIRECTION_SIGN


@dataclass(frozen=True)
class ForecastQuestion:
    question_id: str
    question: str
    deadline: str
    target_nodes: tuple[str, ...]
    target_tickers: tuple[str, ...]
    yes_direction: str
    base_rate: float
    rationale: str


FORECAST_QUESTIONS: tuple[ForecastQuestion, ...] = (
    ForecastQuestion(
        question_id="mu_underperforms_memory_peers",
        question="Will MU underperform the Samsung/SK Hynix memory peer basket by Q1 2027?",
        deadline="2027-03-31",
        target_nodes=("3.3", "3.5"),
        target_tickers=("MU",),
        yes_direction="negative",
        base_rate=0.56,
        rationale="The catalyst directly tests whether a third qualified HBM4 source compresses Micron's scarcity premium.",
    ),
    ForecastQuestion(
        question_id="samsung_hbm4_mix_hits_40",
        question="Will Samsung plausibly reach HBM4 at 40% of total HBM revenue by Q4 2026?",
        deadline="2026-12-31",
        target_nodes=("3.3", "3.5"),
        target_tickers=("005930.KS",),
        yes_direction="positive",
        base_rate=0.55,
        rationale="The announced target is central to the hypothetical event and drives share-shift scenarios.",
    ),
    ForecastQuestion(
        question_id="rubin_supply_pull_forward",
        question="Will HBM4 availability pull forward NVIDIA Rubin platform supply or deployment plans before Q1 2027?",
        deadline="2027-03-31",
        target_nodes=("3.1", "3.3", "3.5", "5.1"),
        target_tickers=("NVDA", "AMZN", "GOOGL", "MSFT"),
        yes_direction="positive",
        base_rate=0.50,
        rationale="This captures the bull case that HBM relief expands total GPU/system shipments.",
    ),
    ForecastQuestion(
        question_id="packaging_becomes_binding_constraint",
        question="Will advanced packaging or substrate capacity become the binding bottleneck before Q1 2027?",
        deadline="2027-03-31",
        target_nodes=("3.5", "4.2", "4.3"),
        target_tickers=("NVDA", "005930.KS", "000660.KS", "MU"),
        yes_direction="positive",
        base_rate=0.58,
        rationale="If HBM loosens, the next constraint likely shifts to package assembly, interposers, substrates, or thermal materials.",
    ),
    ForecastQuestion(
        question_id="memory_equipment_orders_revised_up",
        question="Will memory/packaging equipment order expectations be revised upward by Q1 2027?",
        deadline="2027-03-31",
        target_nodes=("2.1", "2.2", "2.3", "3.3", "3.5"),
        target_tickers=("ASML", "AMAT", "LRCX", "8035.T"),
        yes_direction="positive",
        base_rate=0.52,
        rationale="Samsung catch-up and competitive capacity responses should show up in equipment-order expectations.",
    ),
)


def _logit(probability: float) -> float:
    clipped = min(0.99, max(0.01, probability))
    return math.log(clipped / (1 - clipped))


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def _decision_signal(decision: FinancialDecision, agent: AgentProfile, question: ForecastQuestion) -> float | None:
    ticker_hit = bool(set(decision.affected_tickers) & set(question.target_tickers))
    node_hit = bool(set(decision.affected_nodes) & set(question.target_nodes))
    if not ticker_hit and not node_hit:
        return None

    sign = DIRECTION_SIGN[decision.direction]
    if decision.direction == "mixed" and decision.magnitude < 0:
        sign = -0.25
    if question.yes_direction == "negative":
        sign *= -1

    specificity = 1.2 if ticker_hit else 0.75
    magnitude = max(1, abs(decision.magnitude))
    access_weight = ACCESS_WEIGHT[agent.information_access]
    return sign * magnitude * decision.confidence * agent.credibility_weight * access_weight * specificity


def _scenario_components(base_rate: float, evidence_signal: float) -> list[dict[str, float | str]]:
    base = min(0.92, max(0.08, base_rate))
    bull = min(0.95, max(0.05, _sigmoid(_logit(base) + abs(evidence_signal) * 0.8)))
    bear = min(0.95, max(0.05, _sigmoid(_logit(base) - abs(evidence_signal) * 0.8)))
    directional_weight = min(0.65, 0.35 + abs(evidence_signal) * 0.08)
    counter_weight = max(0.10, 0.25 - abs(evidence_signal) * 0.03)
    base_weight = max(0.15, 1 - directional_weight - counter_weight)
    if evidence_signal >= 0:
        components = [
            {"name": "base_case", "weight": base_weight, "yes_probability": base},
            {"name": "catalyst_accelerates", "weight": directional_weight, "yes_probability": bull},
            {"name": "catalyst_fades", "weight": counter_weight, "yes_probability": bear},
        ]
    else:
        components = [
            {"name": "base_case", "weight": base_weight, "yes_probability": base},
            {"name": "catalyst_accelerates", "weight": counter_weight, "yes_probability": bull},
            {"name": "catalyst_fades", "weight": directional_weight, "yes_probability": bear},
        ]
    total = sum(float(component["weight"]) for component in components)
    for component in components:
        component["weight"] = round(float(component["weight"]) / total, 3)
        component["yes_probability"] = round(float(component["yes_probability"]), 3)
    return components


def _component_probability(components: list[dict[str, float | str]]) -> float:
    return sum(float(component["weight"]) * float(component["yes_probability"]) for component in components)


def build_forecasts(
    decisions: list[FinancialDecision],
    roster: list[AgentProfile],
    outcomes: dict[str, bool] | None = None,
) -> dict[str, Any]:
    agents = {agent.agent_id: agent for agent in roster}
    question_outputs: list[dict[str, Any]] = []

    for question in FORECAST_QUESTIONS:
        cohort_signals: dict[str, list[float]] = defaultdict(list)
        evidence: list[dict[str, Any]] = []
        for decision in decisions:
            agent = agents[decision.agent_id]
            signal = _decision_signal(decision, agent, question)
            if signal is None:
                continue
            cohort_signals[decision.participant_type].append(signal)
            if len(evidence) < 8:
                evidence.append(
                    {
                        "quarter": decision.quarter,
                        "agent_id": decision.agent_id,
                        "participant_type": decision.participant_type,
                        "decision_type": decision.decision_type,
                        "direction": decision.direction,
                        "magnitude": decision.magnitude,
                        "confidence": decision.confidence,
                        "reasoning": decision.reasoning,
                    }
                )

        cohort_forecasts: list[dict[str, Any]] = []
        for participant_type, signals in cohort_signals.items():
            avg_signal = mean(signals)
            components = _scenario_components(question.base_rate, avg_signal)
            cohort_forecasts.append(
                {
                    "participant_type": participant_type,
                    "evidence_signal": round(avg_signal, 3),
                    "sample_count": len(signals),
                    "scenario_components": components,
                    "yes_probability": round(_component_probability(components), 3),
                }
            )

        if not cohort_forecasts:
            ensemble_probability = question.base_rate
            ensemble_weights: list[dict[str, Any]] = []
        else:
            crowd_mean = mean(float(item["yes_probability"]) for item in cohort_forecasts)
            raw_weights = []
            for item in cohort_forecasts:
                probability = float(item["yes_probability"])
                diversity = abs(probability - crowd_mean) + 0.05
                sample_weight = math.log1p(int(item["sample_count"]))
                raw_weight = diversity * sample_weight
                raw_weights.append(raw_weight)
            total_weight = sum(raw_weights) or 1.0
            ensemble_probability = sum(
                float(item["yes_probability"]) * raw_weight / total_weight
                for item, raw_weight in zip(cohort_forecasts, raw_weights, strict=True)
            )
            ensemble_weights = [
                {
                    "participant_type": item["participant_type"],
                    "weight": round(raw_weight / total_weight, 3),
                    "yes_probability": item["yes_probability"],
                }
                for item, raw_weight in zip(cohort_forecasts, raw_weights, strict=True)
            ]

        output = {
            **asdict(question),
            "research_packet": {
                "evidence_count": sum(len(signals) for signals in cohort_signals.values()),
                "evidence_samples": evidence,
            },
            "cohort_forecasts": sorted(
                cohort_forecasts,
                key=lambda item: abs(float(item["yes_probability"]) - 0.5),
                reverse=True,
            ),
            "ensemble": {
                "yes_probability": round(ensemble_probability, 3),
                "no_probability": round(1 - ensemble_probability, 3),
                "weights": ensemble_weights,
                "method": "diversity-weighted cohort ensemble inspired by Mantic's forecasting architecture",
            },
        }
        if outcomes and question.question_id in outcomes:
            outcome = 1.0 if outcomes[question.question_id] else 0.0
            output["scoring"] = {
                "outcome": bool(outcomes[question.question_id]),
                "brier_score": round((ensemble_probability - outcome) ** 2, 4),
            }
        question_outputs.append(output)

    return {
        "method": {
            "source_inspiration": "Thinking Machines / Mantic world-event forecasting post",
            "pattern": "research packet -> binary forecast -> scenario mixture -> diversity-weighted ensemble",
            "note": "No future outcomes are assumed; Brier scores are only emitted if an outcomes file is provided.",
        },
        "question_count": len(question_outputs),
        "forecasts": question_outputs,
    }


def write_forecasts(
    decisions: list[FinancialDecision],
    roster: list[AgentProfile],
    output_path: Path,
    outcomes_path: Path | None = None,
) -> dict[str, Any]:
    outcomes = json.loads(outcomes_path.read_text()) if outcomes_path else None
    output = build_forecasts(decisions, roster, outcomes)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    return output


def write_forecast_markdown(forecasts: dict[str, Any], output_path: Path) -> Path:
    lines = [
        "# Event Forecasts",
        "",
        "Inspired by Thinking Machines/Mantic's forecasting architecture: research context, binary questions,",
        "scenario mixtures, and diversity-weighted ensembles.",
        "",
    ]
    for forecast in forecasts["forecasts"]:
        ensemble = forecast["ensemble"]
        lines.extend(
            [
                f"## {forecast['question_id']}",
                "",
                forecast["question"],
                "",
                f"- Deadline: `{forecast['deadline']}`",
                f"- Ensemble yes probability: `{ensemble['yes_probability']}`",
                f"- Evidence records used: `{forecast['research_packet']['evidence_count']}`",
                f"- Rationale: {forecast['rationale']}",
                "",
                "Cohort probabilities:",
            ]
        )
        for cohort in forecast["cohort_forecasts"][:6]:
            lines.append(
                f"- `{cohort['participant_type']}`: yes `{cohort['yes_probability']}` "
                f"from {cohort['sample_count']} records"
            )
        if "scoring" in forecast:
            lines.append(f"- Brier score: `{forecast['scoring']['brier_score']}`")
        lines.append("")
    output_path.write_text("\n".join(lines))
    return output_path
