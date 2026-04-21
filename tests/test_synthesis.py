from stack_hbm_swarm.agent_profiles import build_agent_roster
from stack_hbm_swarm.decision_schemas import FinancialDecision
from stack_hbm_swarm.synthesis import synthesize


def test_synthesis_weights_confidence_and_credibility() -> None:
    subgraph = {"nodes": {"3.3": {"name": "Memory"}, "3.1": {"name": "GPU"}}}
    roster = build_agent_roster(subgraph)
    high_agent = roster[0]
    low_agent = roster[-1]
    decisions = [
        FinancialDecision(
            quarter="2026Q2",
            agent_id=high_agent.agent_id,
            participant_type=high_agent.participant_type,
            decision_type="estimate_revision",
            affected_nodes=["3.3"],
            affected_tickers=["MU"],
            direction="negative",
            magnitude=-3,
            confidence=0.9,
            horizon_months=3,
            reasoning="High credibility analyst sees Samsung HBM4 parity pressuring Micron scarcity margins.",
            key_assumptions=[],
            risk_flags=[],
        ),
        FinancialDecision(
            quarter="2026Q2",
            agent_id=low_agent.agent_id,
            participant_type=low_agent.participant_type,
            decision_type="relative_value_signal",
            affected_nodes=["3.3"],
            affected_tickers=["MU"],
            direction="positive",
            magnitude=1,
            confidence=0.5,
            horizon_months=3,
            reasoning="Lower credibility flow agent sees a short-term bounce from oversold positioning in memory.",
            key_assumptions=[],
            risk_flags=[],
        ),
    ]
    output = synthesize(decisions, roster)
    assert output["ticker_summary"]["MU"]["net_signal_score"] < 0
    assert output["ticker_summary"]["MU"]["decision_count"] == 2

