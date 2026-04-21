import pytest
from pydantic import ValidationError

from stack_hbm_swarm.decision_schemas import FinancialDecision


VALID_DECISION = {
    "quarter": "2026Q2",
    "agent_id": "a01",
    "participant_type": "sell_side_analyst",
    "decision_type": "estimate_revision",
    "affected_nodes": ["3.3"],
    "affected_tickers": ["MU"],
    "direction": "negative",
    "magnitude": -2,
    "confidence": 0.73,
    "horizon_months": 3,
    "reasoning": "Samsung HBM4 parity reduces scarcity pricing and lowers Micron estimate durability.",
    "key_assumptions": ["Samsung ships in Q3 2026."],
    "risk_flags": ["Contracts may delay price pressure."],
}


def test_valid_decision_schema() -> None:
    decision = FinancialDecision.model_validate(VALID_DECISION)
    assert decision.decision_type == "estimate_revision"


def test_rejects_wrong_role_decision_type() -> None:
    payload = dict(VALID_DECISION)
    payload["decision_type"] = "vendor_allocation_change"
    with pytest.raises(ValidationError):
        FinancialDecision.model_validate(payload)


def test_rejects_bad_magnitude_direction() -> None:
    payload = dict(VALID_DECISION)
    payload["direction"] = "negative"
    payload["magnitude"] = 2
    with pytest.raises(ValidationError):
        FinancialDecision.model_validate(payload)


def test_rejects_bad_confidence() -> None:
    payload = dict(VALID_DECISION)
    payload["confidence"] = 1.5
    with pytest.raises(ValidationError):
        FinancialDecision.model_validate(payload)

