from stack_hbm_swarm.agent_profiles import build_agent_roster
from stack_hbm_swarm.forecasting import build_forecasts
from stack_hbm_swarm.simulation import deterministic_decision


def test_forecasting_layer_outputs_binary_probabilities() -> None:
    subgraph = {
        "nodes": {
            "3.3": {"name": "Memory"},
            "3.1": {"name": "GPU"},
            "3.5": {"name": "Packaging"},
            "2.1": {"name": "Lithography"},
        }
    }
    roster = build_agent_roster(subgraph)
    decisions = [deterministic_decision(agent, "2026Q2", subgraph) for agent in roster[:10]]

    output = build_forecasts(decisions, roster)

    assert output["question_count"] == 5
    first = output["forecasts"][0]
    assert 0 <= first["ensemble"]["yes_probability"] <= 1
    assert first["research_packet"]["evidence_count"] > 0
    assert first["cohort_forecasts"]


def test_forecasting_layer_scores_when_outcomes_are_supplied() -> None:
    subgraph = {"nodes": {"3.3": {"name": "Memory"}, "3.5": {"name": "Packaging"}}}
    roster = build_agent_roster(subgraph)
    decisions = [deterministic_decision(agent, "2026Q2", subgraph) for agent in roster[:5]]

    output = build_forecasts(decisions, roster, {"mu_underperforms_memory_peers": True})
    forecast = next(item for item in output["forecasts"] if item["question_id"] == "mu_underperforms_memory_peers")

    assert "scoring" in forecast
    assert 0 <= forecast["scoring"]["brier_score"] <= 1
