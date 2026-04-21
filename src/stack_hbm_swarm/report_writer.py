from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _ticker_lines(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- `{item['ticker']}`: score {item['net_signal_score']}, "
        f"{item['decision_count']} decisions, disagreement {item['disagreement_score']}"
        for item in items
    )


def write_run_summary(run_dir: Path, synthesis: dict[str, Any]) -> Path:
    path = run_dir / "summary.md"
    path.write_text(
        "# Simulation Run Summary\n\n"
        f"Decision records: {synthesis['decision_count']}\n\n"
        "## Top Positive Tickers\n\n"
        f"{_ticker_lines(synthesis['top_positive_tickers'])}\n\n"
        "## Top Negative Tickers\n\n"
        f"{_ticker_lines(synthesis['top_negative_tickers'])}\n\n"
        "## Portfolio View\n\n"
        f"- Long candidates: {', '.join(synthesis['portfolio_view']['long_candidates']) or 'None'}\n"
        "- Short or underweight candidates: "
        f"{', '.join(synthesis['portfolio_view']['short_or_underweight_candidates']) or 'None'}\n"
        f"- Watchlist: {', '.join(synthesis['portfolio_view']['watchlist'])}\n"
    )
    return path


def write_architecture_doc(path: Path) -> None:
    path.write_text(
        "# Architecture Document\n\n"
        "## Design Choice\n\n"
        "This implementation uses a focused subgraph around the Samsung HBM4 catalyst rather than the full "
        "87-node taxonomy. The selected nodes cover memory, accelerator design, packaging, equipment, server "
        "platforms, datacenter operators, and cloud AI compute. This keeps the run inspectable while preserving "
        "the propagation path that matters for a portfolio manager.\n\n"
        "## MiroFish Mapping\n\n"
        "MiroFish's useful primitives are graph-grounded personas, round-based activation, action logs, and "
        "post-simulation synthesis. The implementation keeps those primitives but avoids patching OASIS "
        "`ActionType`, because that enum lives in the external `camel-oasis` package. Financial actions are "
        "captured as schema-validated decision records, equivalent to using a custom ManualAction logger.\n\n"
        "## Data Flow\n\n"
        "The pipeline loads `taxonomy_tickers.json` and `dependency_graph.json`, normalizes object-shaped layers "
        "into node records, selects the HBM catalyst subgraph, builds a 32-agent roster, optionally enriches "
        "tickers with FMP cache data, runs quarterly simulation rounds, writes JSONL decisions, and synthesizes "
        "ticker/node/portfolio signals.\n\n"
        "## Agent Design\n\n"
        "Agents represent sell-side analysts, buy-side PMs, procurement executives, NVIDIA supply leadership, "
        "memory executives, equipment representatives, and short-term traders. Each receives role-specific "
        "covered nodes, covered tickers, credibility, information access, and bias profile.\n\n"
        "## Decision Schemas\n\n"
        "Every decision includes quarter, agent, participant type, action type, affected nodes, tickers, direction, "
        "magnitude, confidence, horizon, reasoning, assumptions, and risks. Pydantic validation enforces allowed "
        "role-native action types and direction/magnitude consistency.\n\n"
        "## Time Design\n\n"
        "The simulation runs sequential quarters from Q2 2026 through Q1 2027. Quarter themes capture the "
        "immediate qualification shock, Samsung shipment start, Q4 HBM4 mix target, and Q1 2027 renewal/capex "
        "effects. Sequential runs preserve path dependence without pretending to forecast exact market prices.\n\n"
        "## Forecasting Layer\n\n"
        "The project includes a binary event forecasting layer inspired by Thinking Machines/Mantic's world-event "
        "forecasting architecture. After role-native simulation decisions are produced, `forecast-events` frames "
        "those records as research context for concrete questions such as whether MU underperforms memory peers, "
        "whether Samsung reaches the announced HBM4 revenue mix, whether NVIDIA Rubin supply is pulled forward, "
        "whether packaging becomes the next binding bottleneck, and whether equipment order expectations are "
        "revised upward.\n\n"
        "For each question, the system builds a research packet from relevant decisions, converts each participant "
        "cohort into scenario-mixture probabilities, and then ensembles cohorts using a diversity-weighted method. "
        "This adds calibrated, falsifiable forecasts to the qualitative investment memo. If future outcomes are "
        "supplied later, the same output can include Brier scores.\n\n"
        "## FMP And LLM Use\n\n"
        "FMP and OpenRouter clients are implemented behind environment variables. The default simulation is "
        "offline deterministic for reproducibility and budget control. A `--use-llm` flag enables OpenRouter "
        "decision generation, with JSON-only prompts, one repair attempt, and budget guardrails.\n\n"
        "## Limitations\n\n"
        "The MVP does not run the original Zep Cloud graph builder or OASIS social action loop. It implements the "
        "financial behavior layer that MiroFish lacks and documents the extension point. The deterministic run is "
        "a demonstration of pipeline mechanics, not a substitute for a fully budgeted LLM swarm run.\n"
    )


def write_investment_memo(path: Path, synthesis: dict[str, Any]) -> None:
    positives = _ticker_lines(synthesis["top_positive_tickers"][:5])
    negatives = _ticker_lines(synthesis["top_negative_tickers"][:5])
    path.write_text(
        "# Investment Memo: Samsung HBM4 Yield Parity Catalyst\n\n"
        "## Executive View\n\n"
        "The simulation reads Samsung's accelerated HBM4 ramp as a mixed but investable catalyst. The clearest "
        "positive signal accrues to the broader AI infrastructure chain: NVIDIA platform availability, "
        "hyperscaler deployment cadence, and semiconductor equipment demand. The most impaired signal is "
        "Micron-specific pricing power, because a credible third HBM4 source weakens scarcity economics even if "
        "total HBM demand remains strong.\n\n"
        "## Catalyst Interpretation\n\n"
        "Samsung achieving yield parity and early NVIDIA qualification changes the negotiation set. Procurement "
        "agents gain leverage, NVIDIA agents can pull forward Rubin platform planning, and equipment agents see "
        "memory and packaging capex as the second-order beneficiary. Memory executives diverge: Samsung and SK "
        "Hynix frame the event as share and supply-chain credibility, while Micron-facing agents defend contract "
        "quality but concede renewal risk.\n\n"
        "## Highest-Conviction Positive Names\n\n"
        f"{positives}\n\n"
        "Positive signals are strongest where loosened HBM availability increases units, capex, or deployment "
        "velocity rather than simply redistributing memory margin. Equipment and platform beneficiaries screen "
        "better than a pure long-Micron interpretation.\n\n"
        "## Highest-Conviction Negative Or Impaired Names\n\n"
        f"{negatives}\n\n"
        "Negative signals cluster around names exposed to premium memory pricing compression. The simulation does "
        "not say Micron demand disappears; it says the risk/reward shifts from scarcity margin expansion toward "
        "contract durability and capex execution.\n\n"
        "## Cross-Chain Propagation\n\n"
        "The catalyst begins in node `3.3` memory, propagates to `3.1` accelerator design through HBM availability, "
        "then to `3.5` packaging and `4.2` substrates as the next gating constraints. Downstream, `5.1`, `6.1`, "
        "and `9.3` benefit only if power, datacenter fit-out, and networking can absorb earlier GPU availability.\n\n"
        "## Agent Convergence And Divergence\n\n"
        "Procurement, NVIDIA supply, and equipment agents converge on bottleneck relief. Sell-side and PM agents "
        "diverge on Micron because valuation, long-term agreements, and capex intensity all cut against the "
        "headline demand story. Trader agents are lower credibility and mainly flag near-term flow risk.\n\n"
        "## Portfolio Construction\n\n"
        "A practical expression is to favor equipment/platform beneficiaries and avoid treating the catalyst as a "
        "simple long-memory basket. Pair-trade framing is appropriate: long capex and deployment beneficiaries "
        "against an underweight in the most margin-sensitive memory exposure if subsequent HBM share data confirms "
        "Samsung's ramp.\n\n"
        "## Risks And Invalidation\n\n"
        "The thesis weakens if Samsung qualification fails to become volume shipments, if packaging rather than HBM "
        "fully absorbs the bottleneck relief, if Micron's long-term agreements prove more insulated than expected, "
        "or if hyperscalers slow deployment because power/datacenter constraints dominate memory availability.\n"
    )


def read_synthesis(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())
