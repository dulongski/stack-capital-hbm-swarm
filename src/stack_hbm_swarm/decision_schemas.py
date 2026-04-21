from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ParticipantType = Literal[
    "sell_side_analyst",
    "buy_side_pm",
    "procurement_exec",
    "nvidia_supply",
    "memory_exec",
    "equipment_rep",
    "trader",
]

InformationAccess = Literal["public", "channel", "internal", "market_microstructure"]
Direction = Literal["positive", "negative", "mixed", "neutral"]
Quarter = Literal["2026Q2", "2026Q3", "2026Q4", "2027Q1"]

DECISION_TYPES_BY_PARTICIPANT: dict[str, set[str]] = {
    "sell_side_analyst": {"rating_revision", "price_target_revision", "estimate_revision"},
    "buy_side_pm": {"position_adjustment", "hedge_adjustment", "conviction_change"},
    "procurement_exec": {"volume_commitment_change", "vendor_allocation_change", "deployment_timeline_change"},
    "nvidia_supply": {"supplier_qualification_change", "packaging_allocation_change", "platform_ramp_change"},
    "memory_exec": {"pricing_strategy", "capacity_allocation", "customer_contract_strategy"},
    "equipment_rep": {"tool_order_signal", "capacity_expansion_signal"},
    "trader": {"flow_signal", "options_signal", "relative_value_signal"},
}


class AgentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    name: str
    participant_type: ParticipantType
    covered_nodes: list[str] = Field(min_length=1)
    covered_tickers: list[str] = Field(min_length=1)
    information_access: InformationAccess
    credibility_weight: float = Field(ge=0.0, le=1.0)
    bias_profile: str
    persona: str


class FinancialDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quarter: Quarter
    agent_id: str
    participant_type: ParticipantType
    decision_type: str
    affected_nodes: list[str] = Field(min_length=1)
    affected_tickers: list[str] = Field(min_length=1)
    direction: Direction
    magnitude: int = Field(ge=-3, le=3)
    confidence: float = Field(ge=0.0, le=1.0)
    horizon_months: int = Field(ge=1, le=24)
    reasoning: str = Field(min_length=20)
    key_assumptions: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator("decision_type")
    @classmethod
    def decision_type_is_known(cls, value: str) -> str:
        all_types = set().union(*DECISION_TYPES_BY_PARTICIPANT.values())
        if value not in all_types:
            raise ValueError(f"unknown decision_type: {value}")
        return value

    @model_validator(mode="after")
    def decision_type_matches_participant(self) -> "FinancialDecision":
        allowed = DECISION_TYPES_BY_PARTICIPANT[self.participant_type]
        if self.decision_type not in allowed:
            raise ValueError(f"{self.decision_type} is not valid for {self.participant_type}")
        if self.direction == "positive" and self.magnitude < 0:
            raise ValueError("positive decisions must have non-negative magnitude")
        if self.direction == "negative" and self.magnitude > 0:
            raise ValueError("negative decisions must have non-positive magnitude")
        if self.direction == "neutral" and self.magnitude != 0:
            raise ValueError("neutral decisions must use magnitude 0")
        return self


def validate_decision_payload(payload: dict) -> FinancialDecision:
    return FinancialDecision.model_validate(payload)

