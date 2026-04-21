from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .agent_profiles import load_agent_roster, write_agent_roster
from .config import (
    AGENT_ROSTER_PATH,
    CACHE_DIR,
    DEPENDENCY_GRAPH_PATH,
    DOCS_DIR,
    RUNS_DIR,
    SELECTED_SUBGRAPH_PATH,
    TAXONOMY_PATH,
    RuntimeConfig,
    ensure_directories,
)
from .fmp_client import FMPClient
from .forecasting import write_forecast_markdown, write_forecasts
from .graph_loader import load_value_chain_graph
from .llm_client import OpenRouterClient
from .report_writer import read_synthesis, write_architecture_doc, write_investment_memo, write_run_summary
from .simulation import DEFAULT_QUARTERS, load_decisions, run_simulation
from .subgraph_selector import CORE_TICKERS, write_selected_subgraph
from .synthesis import write_synthesis


def _load_subgraph() -> dict:
    if not SELECTED_SUBGRAPH_PATH.exists():
        raise FileNotFoundError("selected subgraph missing; run prepare-data first")
    return json.loads(SELECTED_SUBGRAPH_PATH.read_text())


def _run_dir(run_id: str | None) -> Path:
    if run_id:
        return RUNS_DIR / run_id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return RUNS_DIR / timestamp


def prepare_data(_: argparse.Namespace) -> None:
    ensure_directories()
    graph = load_value_chain_graph(TAXONOMY_PATH, DEPENDENCY_GRAPH_PATH)
    subgraph = write_selected_subgraph(graph, SELECTED_SUBGRAPH_PATH)
    print(
        f"Prepared {subgraph['node_count']} selected nodes, "
        f"{subgraph['edge_count']} internal edges, {subgraph['boundary_edge_count']} boundary edges"
    )


def fetch_fmp(args: argparse.Namespace) -> None:
    config = RuntimeConfig.from_env()
    tickers = args.tickers.split(",") if args.tickers else list(CORE_TICKERS)
    client = FMPClient(config.fmp_api_key, CACHE_DIR)
    results = client.fetch_bundle(tickers, refresh=args.refresh)
    print(f"Fetched or skipped {len(results)} FMP endpoint payloads for {len(tickers)} tickers")


def build_roster(_: argparse.Namespace) -> None:
    subgraph = _load_subgraph()
    roster = write_agent_roster(subgraph, AGENT_ROSTER_PATH)
    print(f"Built {len(roster)} agents at {AGENT_ROSTER_PATH}")


def run_simulation_command(args: argparse.Namespace) -> None:
    subgraph = _load_subgraph()
    roster = load_agent_roster(AGENT_ROSTER_PATH)
    quarters = args.quarters.split(",") if args.quarters else list(DEFAULT_QUARTERS)
    config = RuntimeConfig.from_env()
    llm_client = OpenRouterClient(config.openrouter_api_key, config.openrouter_small_model, config.simulation_budget_usd)
    run_dir = _run_dir(args.run_id)
    metadata = run_simulation(
        roster,
        subgraph,
        run_dir,
        quarters,
        use_llm=args.use_llm,
        dry_run=args.dry_run,
        llm_client=llm_client,
    )
    print(f"Wrote {metadata['decision_count']} decisions to {run_dir / 'decision_log.jsonl'}")


def synthesize_command(args: argparse.Namespace) -> None:
    run_dir = _run_dir(args.run_id)
    roster = load_agent_roster(AGENT_ROSTER_PATH)
    decisions = load_decisions(run_dir / "decision_log.jsonl")
    output = write_synthesis(decisions, roster, run_dir / "synthesis.json")
    print(f"Wrote synthesis for {output['decision_count']} decisions to {run_dir / 'synthesis.json'}")


def write_reports(args: argparse.Namespace) -> None:
    run_dir = _run_dir(args.run_id)
    synthesis = read_synthesis(run_dir / "synthesis.json")
    write_run_summary(run_dir, synthesis)
    write_architecture_doc(DOCS_DIR / "architecture.md")
    write_investment_memo(DOCS_DIR / "investment_memo.md", synthesis)
    print(f"Wrote summary and docs for run {run_dir.name}")


def forecast_events(args: argparse.Namespace) -> None:
    run_dir = _run_dir(args.run_id)
    roster = load_agent_roster(AGENT_ROSTER_PATH)
    decisions = load_decisions(run_dir / "decision_log.jsonl")
    outcomes_path = Path(args.outcomes) if args.outcomes else None
    forecasts = write_forecasts(decisions, roster, run_dir / "event_forecasts.json", outcomes_path)
    write_forecast_markdown(forecasts, run_dir / "event_forecasts.md")
    print(f"Wrote {forecasts['question_count']} event forecasts to {run_dir / 'event_forecasts.json'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stack Capital HBM swarm simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-data")
    prepare.set_defaults(func=prepare_data)

    fmp = subparsers.add_parser("fetch-fmp")
    fmp.add_argument("--tickers", default=",".join(CORE_TICKERS))
    fmp.add_argument("--refresh", action="store_true")
    fmp.set_defaults(func=fetch_fmp)

    roster = subparsers.add_parser("build-roster")
    roster.set_defaults(func=build_roster)

    run = subparsers.add_parser("run-simulation")
    run.add_argument("--quarters", default=",".join(DEFAULT_QUARTERS))
    run.add_argument("--run-id")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--use-llm", action="store_true")
    run.set_defaults(func=run_simulation_command)

    synth = subparsers.add_parser("synthesize")
    synth.add_argument("--run-id", required=True)
    synth.set_defaults(func=synthesize_command)

    reports = subparsers.add_parser("write-reports")
    reports.add_argument("--run-id", required=True)
    reports.set_defaults(func=write_reports)

    forecasts = subparsers.add_parser("forecast-events")
    forecasts.add_argument("--run-id", required=True)
    forecasts.add_argument("--outcomes", help="Optional JSON file mapping forecast question ids to true/false outcomes")
    forecasts.set_defaults(func=forecast_events)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
