# Architecture Document

## Design Choice

This implementation uses a focused subgraph around the Samsung HBM4 catalyst rather than the full 87-node taxonomy. The selected nodes cover memory, accelerator design, packaging, equipment, server platforms, datacenter operators, and cloud AI compute. This keeps the run inspectable while preserving the propagation path that matters for a portfolio manager.

## MiroFish Mapping

MiroFish's useful primitives are graph-grounded personas, round-based activation, action logs, and post-simulation synthesis. The implementation keeps those primitives but avoids patching OASIS `ActionType`, because that enum lives in the external `camel-oasis` package. Financial actions are captured as schema-validated decision records, equivalent to using a custom ManualAction logger.

## Data Flow

The pipeline loads `taxonomy_tickers.json` and `dependency_graph.json`, normalizes object-shaped layers into node records, selects the HBM catalyst subgraph, builds a 32-agent roster, optionally enriches tickers with FMP cache data, runs quarterly simulation rounds, writes JSONL decisions, and synthesizes ticker/node/portfolio signals.

## Agent Design

Agents represent sell-side analysts, buy-side PMs, procurement executives, NVIDIA supply leadership, memory executives, equipment representatives, and short-term traders. Each receives role-specific covered nodes, covered tickers, credibility, information access, and bias profile.

## Decision Schemas

Every decision includes quarter, agent, participant type, action type, affected nodes, tickers, direction, magnitude, confidence, horizon, reasoning, assumptions, and risks. Pydantic validation enforces allowed role-native action types and direction/magnitude consistency.

## Time Design

The simulation runs sequential quarters from Q2 2026 through Q1 2027. Quarter themes capture the immediate qualification shock, Samsung shipment start, Q4 HBM4 mix target, and Q1 2027 renewal/capex effects. Sequential runs preserve path dependence without pretending to forecast exact market prices.

## FMP And LLM Use

FMP and OpenRouter clients are implemented behind environment variables. The default simulation is offline deterministic for reproducibility and budget control. A `--use-llm` flag enables OpenRouter decision generation, with JSON-only prompts, one repair attempt, and budget guardrails.

## Limitations

The MVP does not run the original Zep Cloud graph builder or OASIS social action loop. It implements the financial behavior layer that MiroFish lacks and documents the extension point. The deterministic run is a demonstration of pipeline mechanics, not a substitute for a fully budgeted LLM swarm run.
