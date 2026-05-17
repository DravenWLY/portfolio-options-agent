# Current Roadmap

This is the short context file for routine Codex and Claude reviews. Prefer this file over the full architecture document when the task only needs current direction.

## Product North Star

`portfolio-options-agent` is a portfolio-aware options income and risk copilot for manual traders. It combines broker portfolio state, market context, deterministic options/risk calculations, custom portfolio-aware agents, optional TradingAgents stock/company research, and durable report history.

The dashboard is the cockpit, not the whole product. SnapTrade, market data providers, and TradingAgents are inputs/components, not the center.

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

Phase 12 - Market Data Contracts and Manual Provider.

Goal: define quote and option-chain contracts, keeping broker freshness strictly separate from market quote freshness.

Scope:

- Provider-agnostic MarketDataProvider interface.
- OptionDataProvider interface.
- Quote freshness model.
- Market quote response models.
- Manual/mock provider (deterministic, no real API calls).
- Mocked market data tests.

Out of scope:

- Real market data provider integrations (deferred).
- Option screener UI.
- TradingAgents UI.
- Trade execution UI.

## Next Phases

Phase 13 - Deterministic Options/Risk Engine MVP.

- option formulas, collateral/free cash, assignment scenario
- covered call eligibility, CSP candidate evaluator
- allocation/concentration risk
- `risk_rule_violations` with severity `info`, `warning`, `violation`, or `blocker`

Phase 14 - Custom Portfolio-Aware Agent Orchestrator.

- Portfolio Context Agent, Options Income Agent
- Collateral and Assignment Risk Agent, Allocation Risk Agent
- Freshness/Guardrail Agent, Report Composer Agent
- LLM boundary mocked by default

Phase 15 - TradingAgents Adapter (optional, stock/company research only).

Phase 16 - Frontend Agent Workspace B (report detail, agent run monitor, risk review).

## Review Guidance

Use `docs/agent_context/opus_review_brief.md` for high-stakes Opus reviews. Use `docs/agent_context/codex_working_context.md` for implementation tasks. Load `docs/architecture.md` only when the task needs the full design. Load `docs/completed_phases_log.md` only when historical verification details are directly relevant.
