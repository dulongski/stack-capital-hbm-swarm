# Stack Capital HBM Swarm Simulation

This repository implements an evaluator-ready MVP for the Stack Capital AI Research Engineer case study. It simulates how the hypothetical March 31, 2026 Samsung HBM4 yield parity catalyst propagates through a focused AI value-chain subgraph over Q2 2026 through Q1 2027.

The implementation follows MiroFish's useful architecture patterns: graph-grounded personas, role-specific context, round-based simulation, structured action logs, and post-simulation synthesis. It intentionally avoids fragile `camel-oasis` enum monkey-patching and records financial decisions through schema-validated custom records.

## Scope

The MVP focuses on the catalyst neighborhood:

- Memory: DRAM, HBM, NAND
- AI accelerator and GPU design
- OSAT, advanced packaging, and assembly
- Advanced packaging substrates and thermal interface materials
- Lithography, deposition/etch, and test/metrology equipment
- Server platforms, datacenter operators, and cloud AI compute

The demo run uses 32 agents across sell-side analysts, buy-side PMs, hyperscaler procurement, NVIDIA supply-chain leadership, memory executives, equipment representatives, and short-term traders.

## Setup

Use Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

Optional API keys are read from environment variables. Do not commit `.env`.

```bash
cp .env.example .env
```

Required only for remote enrichment or LLM runs:

- `FMP_API_KEY`
- `OPENROUTER_API_KEY`
- `ZEP_API_KEY` is documented for MiroFish/Zep extension work but is not required for this MVP path.

## Reproduce The Demo

```bash
python -m stack_hbm_swarm.cli prepare-data
python -m stack_hbm_swarm.cli build-roster
python -m stack_hbm_swarm.cli run-simulation --quarters 2026Q2,2026Q3,2026Q4,2027Q1 --run-id demo
python -m stack_hbm_swarm.cli synthesize --run-id demo
python -m stack_hbm_swarm.cli write-reports --run-id demo
```

Outputs:

- `data/processed/selected_subgraph.json`
- `data/processed/agent_roster.json`
- `runs/demo/decision_log.jsonl`
- `runs/demo/synthesis.json`
- `runs/demo/summary.md`
- `docs/architecture.md`
- `docs/investment_memo.md`

## Optional FMP Enrichment

```bash
python -m stack_hbm_swarm.cli fetch-fmp --tickers MU,NVDA,ASML,AMAT,LRCX,8035.T,005930.KS,000660.KS,AMZN,GOOGL,MSFT
```

FMP responses are cached under `data/cache/`, which is excluded from git.

## Optional OpenRouter Run

The default run is deterministic and offline so reviewers can reproduce the pipeline without spending API budget. To run remote LLM decisions:

```bash
python -m stack_hbm_swarm.cli run-simulation --run-id llm_run --use-llm
python -m stack_hbm_swarm.cli synthesize --run-id llm_run
python -m stack_hbm_swarm.cli write-reports --run-id llm_run
```

The OpenRouter client uses JSON-only prompts, tracks estimated usage, and stops once the configured budget guard is reached.

## Tests

```bash
python -m pytest
```

The tests cover taxonomy loading, subgraph selection, decision schema validation, and synthesis weighting.

## Submission Notes

The input taxonomy and dependency graph are NDA materials and should remain in a private repository. Secrets are excluded from git. The API keys originally supplied for this exercise should be rotated before any final submission because they appeared in chat.
