# ADR 0002: TradingAgents-Inspired Portfolio-Aware Agent Team

Status: accepted
Date: 2026-05-20
Owner: Codex B - Architecture / Tech Lead

## Context

Portfolio Copilot's broader product goal is not only deterministic helper services. The product should become a TradingAgents-inspired, portfolio-aware trade review agent team for manual investors.

The system must combine broker-connected portfolio context, market data and option quote snapshots where available, deterministic portfolio/risk calculations, public research evidence, optional bull/bear/risk argumentation, freshness/actionability policy, and a proposed stock/ETF/options `TradeIntent`.

TradingAgents is useful inspiration for role-based analysis, research, debate, streaming, and checkpointing. However, Portfolio Copilot has privacy, broker-data, options collateral, actionability, and no-execution constraints that TradingAgents does not own.

## Decision

Portfolio Copilot is **TradingAgents-inspired, not TradingAgents-centered**. The product center remains broker-aware `TradeIntent` review. TradingAgents remains optional public ticker/company research evidence, not the portfolio-aware decision engine.

Split the current Phase 16 into:

- **Phase 16A - Deterministic Agent Components**: current P16-T0 through P16-T4. These are safe deterministic-first components and report composition helpers.
- **Phase 16B - Portfolio-Aware Agent Team Orchestrator**: new app-owned workflow layer that defines how portfolio-aware roles run as a team/stage graph, persist runs/steps, enforce actionability, compose outputs, and degrade safely when research or LLMs are unavailable.

Rename Phase 17 to **TradingAgents/Public Research Evidence Adapter**. It supplies optional public ticker/company evidence only.

## Portfolio Copilot Roles

MVP roles:

- Portfolio Context Agent: builds sanitized portfolio shape, freshness, and report-history context from approved projections.
- Trade Feasibility / Trade Review Agent: explains deterministic trade-review outputs, feasibility blockers, and open questions.
- Risk / Concentration behavior: interprets deterministic concentration, allocation, collateral, assignment/exercise, call-away, and risk-rule outputs.
- Freshness / Guardrail Agent: consumes the backend-owned actionability policy and gates report language.
- Report Composer Agent: composes deterministic outputs, guardrails, and approved interpretations into an educational report.

P1 roles:

- Market Data Agent: summarizes quote/chain/Greeks availability, data mode, market quote freshness, and provider status after real snapshots exist.
- News / Research Evidence Agent: normalizes public ticker/company evidence.
- Bull Case Agent: explains favorable public evidence and structured tradeoffs.
- Bear Case Agent: explains adverse public evidence and structured tradeoffs.

Later roles:

- Multi-agent debate loop coordinator.
- Deep research mode coordinator.
- Strategy memory / lifecycle agent.
- Advisor-style review workflow agent.

## Private-Data Boundary

Private/sanitized portfolio-aware roles may consume only approved app-owned projections and actionability decisions:

- Portfolio Context Agent.
- Trade Feasibility / Trade Review Agent.
- Risk / Concentration Agent.
- Freshness / Guardrail Agent.
- Report Composer Agent.

Public evidence roles must not receive private portfolio context by default:

- Market Data Agent.
- News / Research Evidence Agent.
- Bull Case Agent.
- Bear Case Agent.
- TradingAgents adapter.

Forbidden by default for all LLMs, TradingAgents, public evidence roles, analytics, docs, and tests:

- raw holdings;
- account values;
- cash balances or buying power;
- broker account ids or provider account ids;
- provider connection ids;
- raw provider payloads;
- secrets, portal URLs, API keys, or access tokens;
- trade journal entries;
- account-specific thresholds or private strategy settings.

## Orchestration Model

Use a stage-based graph first, not a free-form autonomous graph.

Recommended stage order:

1. Validate `TradeIntent`.
2. Build approved portfolio context projection.
3. Resolve market snapshot.
4. Run deterministic trade/risk review.
5. Evaluate Portfolio Snapshot Actionability Policy.
6. Optionally retrieve public research evidence.
7. Optionally run bull/bear/risk interpretation over sanitized/public evidence.
8. Run freshness/guardrail review.
9. Compose final educational report.
10. Persist report, run, and step outputs.

The orchestrator must work with deterministic-only inputs. If research, TradingAgents, market provider, or LLMs are unavailable, it should produce a safe deterministic report with explicit unavailable/analysis-only states instead of failing the whole review.

## Consequences

Positive:

- Preserves the founder's agent-team ambition without weakening safety boundaries.
- Gives Codex C a clear sequence after Phase 16A.
- Lets Phase 18 UI consume a stable workflow contract before rich research/debate UI exists.
- Keeps TradingAgents optional and public-evidence-only.

Tradeoffs:

- Phase 16 is no longer complete when deterministic components are done.
- Phase 16B adds an orchestration contract before Phase 17/18 can be treated as polished.
- Bull/bear/debate roles become P1 unless PM explicitly pulls them into MVP.

## Alternatives Considered

1. Treat current Phase 16A components as the full custom agent orchestrator. Rejected because it hides the missing agent-team workflow.
2. Let TradingAgents own the whole workflow. Rejected because it cannot safely own broker/private portfolio context, options collateral, or actionability policy.
3. Build a fully autonomous graph immediately. Rejected because MVP needs auditable stage boundaries and deterministic-first fallback.

## Review Guidance

Architecture reviews should block changes that:

- call Phase 16 complete without either implementing or explicitly deferring Phase 16B;
- send raw/private brokerage data to LLMs or TradingAgents by default;
- allow public research/debate roles to produce final portfolio-aware conclusions;
- let optional research evidence override deterministic calculations or actionability status;
- add order tickets, broker actions, or execution-like language.
