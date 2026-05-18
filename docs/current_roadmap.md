# Current Roadmap

This is the short context file for routine Codex and Claude reviews. Prefer this file over the full architecture document when the task only needs current direction.

## Product North Star

`portfolio-options-agent` is a portfolio-aware options income and risk copilot for manual traders. It combines broker portfolio state, market context, deterministic options/risk calculations, strategy-extensible evaluators, custom portfolio-aware agents, optional TradingAgents stock/company research, and durable report history.

The dashboard is the cockpit, not the whole product. SnapTrade, market data providers, and TradingAgents are inputs/components, not the center. Wheel-style workflows are the first practical use case, not the product boundary.

## Safety Boundary

- Manual decision support only.
- No automatic trading.
- No broker scraping.
- No Fidelity credential storage.
- No MFA bypass.
- No guaranteed-return language.
- No real account data, API keys, broker CSVs, or private strategy thresholds in git.
- Deterministic Python services calculate financial metrics. LLMs may explain structured outputs but must not invent metrics.

## Completed Foundation

- Phase 1: database foundation.
- Phase 2: users and accounts.
- Phase 3: internal portfolio storage primitives.
- Phase 4: broker sync foundation.
- Phase 5: SnapTrade read-only adapter, mock-first.
- Phase 6: SnapTrade connection flow backend.
- Phase 7: SnapTrade portfolio normalization.
- Phase 8: portfolio dashboard backend from synced data.
- Phase 9: manual input and Fidelity CSV fallback.
- Phase 10: thin report/agent persistence foundation.
- Phase 11: React/Vite frontend dashboard shell — user/account selector, portfolio summary, cash/stock/option positions, broker freshness bar and warnings panel, report history placeholder. P11-T7 (broker connection UI at `/broker`) is an incremental extension using only existing backend endpoints.

Detailed verification history lives in `docs/completed_phases_log.md`.

## Active Phase

Phase 12 - Market Data Contracts, Snapshots, Manual Provider, and Market Status UI Slice.

Goal: define quote and option-chain contracts, keeping broker freshness strictly separate from market quote freshness.

Scope:

- Strategy-agnostic market data domain models.
- Option contract identity and immutable quote/chain snapshots.
- Provider-agnostic MarketDataProvider, OptionDataProvider, and GreeksProvider interfaces.
- Quote freshness and actionability policy.
- Market quote response models.
- Manual/mock provider (deterministic, no real API calls).
- Mocked market data tests.
- Claude review of frontend implications after backend contracts are stable.
- Thin frontend market-data status slice using only mock/manual data.
- Codex integration/security review before Phase 13.

Out of scope:

- Real market data provider integrations (deferred).
- Option screener UI.
- TradingAgents UI.
- Trade execution UI.

## Next Phases

Phase 13 - Generic Options Metrics and Portfolio Risk Engine plus Risk Review UI Slice.

- option formulas, collateral/free cash, assignment/exercise scenario
- allocation impact and concentration risk
- generic deterministic risk report
- `risk_rule_violations` with severity `info`, `warning`, `violation`, or `blocker`
- Claude review of deterministic risk contracts before UI work
- thin frontend deterministic risk review slice

Phase 14 - Strategy Evaluator Framework MVP plus Strategy Review UI Slice.

- `StrategyEvaluator` protocol and deterministic `StrategyEvaluationResult`
- first evaluators: cash-secured put and covered call
- light wheel lifecycle composition as a workflow view, not the product boundary
- future-ready for protective puts, collars, long options, vertical spreads, ETF overlays, and hedge analysis

Phase 15 - Custom Portfolio-Aware Agent Orchestrator plus Agent/Report Workspace Slice A.

- Portfolio Context Agent, Options Income Agent
- Collateral and Assignment Risk Agent, Allocation Risk Agent
- Freshness/Guardrail Agent, Report Composer Agent
- LLM boundary mocked by default
- frontend report/agent workspace slice that displays persisted custom-agent outputs

Future Broker Activities / Transactions layer.

- Read-only activity sync for historical buys, sells, dividends, deposits, withdrawals, fees, option open/close events, assignment, exercise, and expiration where the broker provider supports it.
- Store sanitized raw broker activities separately first; normalize selected events into trades, premium income records, and wheel lifecycle records later.
- Treat activity freshness separately from broker position freshness and market quote freshness. Activities may be cached/daily and must not be treated as real-time execution data.
- Keep orders separate from activities and read-only only.

Phase 16 - TradingAgents Adapter plus Evidence UI Slice (optional, stock/company research only).

Phase 17 - Expanded Frontend Agent Workspace B (deeper report detail, agent run monitor, risk review).

## Delivery Rhythm

Each new capability should now ship as a small vertical slice:

1. Codex implements the backend contract/service with synthetic tests.
2. Claude reviews frontend implications and finance-safety language.
3. Claude implements the corresponding frontend view only after the backend contract exists.
4. Codex performs the final integration/security review.

Do not build speculative frontend fields before backend contracts exist, and do not run backend phases far ahead without a minimal reviewable UI surface.

## Review Guidance

Use `docs/agent_context/opus_review_brief.md` for high-stakes Opus reviews. Use `docs/agent_context/codex_working_context.md` for implementation tasks. Load `docs/architecture.md` only when the task needs the full design. Load `docs/completed_phases_log.md` only when historical verification details are directly relevant.
