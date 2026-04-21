# Presentation Script: Stack Capital HBM Swarm Simulation

## Slide 1 - Opening

Isaac, Marcos, thanks for taking the time. I built a focused HBM catalyst simulation around the Samsung HBM4 yield parity scenario. The goal was not to make a generic demo. The goal was to turn an ambiguous market event into structured, inspectable investment signals.

At a high level, the system takes the taxonomy and dependency graph, selects the part of the AI value chain most exposed to HBM, creates role-native agents, runs four quarterly simulation rounds, and then synthesizes the decisions into ticker signals, bottleneck analysis, a memo, and event forecasts.

## Slide 2 - The Problem

The important point is that this catalyst has two credible interpretations.

The bear case is Micron-specific: Samsung becoming a credible HBM4 supplier earlier than expected can compress scarcity pricing and reduce Micron's negotiating leverage when contracts renew.

The bull case is chain-wide: if HBM supply loosens, then NVIDIA and the hyperscalers may be able to pull forward deployments. That would benefit equipment, packaging, cloud platforms, and datacenter infrastructure.

So I did not want to hard-code a conclusion. I built the simulation to let different participant types react through their own incentives and information access.

## Slide 3 - Implementation Scope

I deliberately scoped the simulation to 11 nodes instead of all 87.

The selected nodes cover memory, GPU design, advanced packaging, substrates, equipment, server platforms, datacenter operators, and cloud AI compute. That is the economic path through which this catalyst should travel.

The run uses 32 agents and generates 128 structured decisions: 32 agents across four quarters. That gives enough heterogeneity to show emergence without making the system shallow or expensive.

The design choice here was practical: for a one-week case, I would rather simulate the right subset deeply than simulate the whole taxonomy superficially.

## Slide 4 - System Flow

The pipeline has five stages.

First, it loads the provided structured inputs: taxonomy, ticker mappings, dependency edges, and the catalyst facts.

Second, it builds the focused HBM subgraph. This is where the system narrows from the full value chain to the relevant causal neighborhood.

Third, it creates the agent roster. The agents are not generic chatbots. They have participant type, covered nodes, covered tickers, information access, credibility, and bias profile.

Fourth, each agent produces role-native decisions across Q2 2026 through Q1 2027.

Fifth, the synthesis layer aggregates decisions by ticker, node, quarter, and participant type to produce portfolio outputs.

## Slide 5 - Why Not Default MiroFish?

MiroFish is useful as an architectural pattern, but the default action space is social-media oriented: post, like, repost, comment, follow.

That is not the right action space for financial research. A sell-side analyst does not "like" a post. They revise estimates or ratings. A hyperscaler procurement executive changes vendor allocation or deployment timelines. A PM adjusts exposure or hedges.

So I preserved the MiroFish ideas that matter: graph grounding, personas, simulation rounds, action logs, and synthesis. But I replaced the action space with financial decision schemas.

Technically, I avoided patching the OASIS `ActionType` enum because that enum lives in the external `camel-oasis` package. Instead, I used a custom structured logger pattern, similar to a ManualAction approach. It is less brittle and easier to review.

## Slide 6 - Propagation Map

This slide shows how the event moves through the value chain.

The shock starts in node 3.3, memory. Samsung's HBM4 yield parity changes the market's view of supply credibility and future pricing power.

From there, it affects node 3.1, GPU design, because NVIDIA's supplier mix and Rubin ramp planning depend on qualified HBM supply.

Then it moves into packaging and substrates. If HBM becomes less constrained, the bottleneck may shift into advanced packaging, interposers, ABF substrates, thermal materials, and assembly capacity.

Finally, downstream cloud and datacenter nodes only benefit if power, cooling, sites, networking, and server integration can absorb the extra compute supply.

This is why the simulation cannot be single-stock only.

## Slide 7 - Agent Design

The agents are split into three broad information regimes.

Market-facing agents include sell-side analysts, buy-side PMs, and traders. They evaluate valuation, positioning, estimates, and risk/reward.

Supply-chain agents include hyperscaler procurement and NVIDIA supply-chain leadership. They reason about vendor allocation, qualification timing, packaging allocation, and deployment schedules.

Company-facing agents include Micron, Samsung, SK Hynix, and equipment representatives. They reason about pricing strategy, capacity allocation, capex, and tool demand.

The reason this matters is information asymmetry. A procurement executive should have different context from a trader. That is how the simulation can produce disagreement that is meaningful rather than just noisy.

## Slide 8 - Ticker Signals

The ticker output is intentionally multi-name.

The strongest positive scores are cloud and equipment beneficiaries: AMZN, GOOGL, MSFT, ASML, AMAT, LRCX, Tokyo Electron, and NVDA.

Micron is the underweight candidate. The model does not say Micron demand collapses. It says the catalyst shifts the risk/reward. Demand may still be strong, but the premium memory pricing setup becomes less protected if Samsung is credible earlier than expected.

So the investment view is not "short all memory." It is more nuanced: favor the companies that benefit from broader AI deployment and capex response, while watching Micron's margin and share assumptions more carefully.

## Slide 9 - Forecasting Layer

After the first implementation, I added a forecasting layer inspired by Thinking Machines' Mantic post on training LLMs to predict world events.

The idea I borrowed was not just "ask an LLM for a forecast." It was the structure: separate research context from the forecast, ask binary questions, use scenario components, ensemble diverse predictors, and make the output scoreable later.

In this project, the research packet is the simulation decision log. The binary forecasts ask things like: will MU underperform memory peers, will Samsung hit 40% HBM4 mix, will Rubin be pulled forward, will packaging become the bottleneck, and will equipment expectations move higher.

The outputs are probabilities, not certainties. If real outcomes are supplied later, the system can compute Brier scores. That makes the research process more falsifiable.

## Slide 10 - Portfolio View

The practical portfolio readout is relative value.

The positive side is equipment and deployment beneficiaries: NVDA, ASML, AMAT, LRCX, Tokyo Electron, and the major hyperscalers.

The risk side is MU. Again, not because demand disappears, but because the narrative changes from scarcity-led margin expansion to contract durability, capex execution, and competitive response.

The pair-trade expression is: long equipment and deployment beneficiaries versus underweight MU if Samsung's ramp is confirmed by follow-on data.

The watch items are HBM share data, packaging capacity, and hyperscaler deployment cadence.

## Slide 11 - What I Would Improve Next

There are three obvious next steps.

First, richer data. I implemented the FMP client, but the default demo is deterministic and offline for reproducibility. In a production version, I would pull actual estimates, price targets, historical prices, holdings, and fundamentals into each agent's context.

Second, more realism. I would run larger OpenRouter-based simulations and compare LLM-generated decision distributions against the deterministic baseline.

Third, better evaluation. The forecasting layer is designed so that future outcomes can be scored with Brier scores. Over time, that would let the system learn which agent cohorts are better calibrated for each kind of market question.

The main point is that the MVP is not a one-off script. It is a foundation for iterative investment simulation.

## Slide 12 - Close

To summarize, I converted an ambiguous catalyst into a structured simulation system.

I adapted the MiroFish pattern into a finance-native agent loop, replaced social actions with role-native financial decisions, preserved traceability through JSONL logs, and added a synthesis layer that outputs tickers, bottlenecks, memo conclusions, and binary event forecasts.

The conclusion is that the Samsung HBM4 catalyst is not simply negative for Micron. It is a chain-wide catalyst. It likely pressures Micron's scarcity premium, but it can also benefit equipment, NVIDIA, hyperscalers, and the broader AI infrastructure deployment cycle.

That is the kind of multi-name view I wanted the system to produce.

