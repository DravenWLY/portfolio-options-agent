# Claude B / Opus Review Brief

Use this short brief for high-stakes Claude Opus reviews. Prefer this over loading the full `docs/shared/implementation_plan.md` or `docs/shared/completed_phases_log.md`.

## Project Direction

This project is a read-only, portfolio-aware trade review and risk copilot for manual investors. It is not a SnapTrade dashboard, market-data viewer, option-chain browser, options-income app, AI stock picker, automated trading system, or thin TradingAgents wrapper.

The system combines:

1. Portfolio system of record.
2. Market data layer.
3. Proposed stock/ETF/options `TradeIntent` review.
4. Deterministic portfolio, options, and risk engine.
5. Custom portfolio-aware agents.
6. Optional TradingAgents stock/company research adapter.
7. Dashboard and durable report history.

## Hard Safety Rules

- No automatic trading.
- No broker scraping.
- No Fidelity username/password storage.
- No MFA bypass.
- No real account data or API keys in git.
- No guaranteed-return language.
- LLMs explain structured outputs; deterministic Python calculates metrics.
- Real SnapTrade/Fidelity brokerage data is private user data and is out of scope for agent inspection by default.
- Do not query local DB/API/browser screens/logs or inspect screenshots if they may expose real balances, holdings, transactions, account identifiers, provider account IDs, raw provider payloads, SnapTrade user IDs, user secrets, portal URLs, or generated reports.
- If real brokerage data access appears necessary, stop and ask for explicit narrow permission; prefer redacted or synthetic evidence.

## Current State

Completed foundation:

- Users/accounts.
- Internal cash/stock/option storage.
- SnapTrade-first read-only broker sync foundation, mock-first.
- Manual input and Fidelity CSV preview fallback.
- Broker freshness and portfolio warning surfaces.
- Report/agent persistence foundation with `report_threads`, `report_messages`, `agent_runs`, and `agent_steps`.
- Market data contracts and manual/mock provider.
- Generic option/risk services.
- TradeIntent foundation for stock, ETF, and options intents.
- Deterministic trade-review engine with payoff, portfolio impact, risk integration, strategy wrappers, deterministic report, and agent-safe projection.
- Product docs for PRD, MVP scope, feature priority, and metrics.

## Active Roadmap

Current active phase: Phase 16 - Custom Portfolio-Aware Agent Orchestrator.

Immediate review concern:

- Portfolio Snapshot Actionability Policy should be first-class before polished account-specific agent reports. Fresh quotes plus stale broker positions can produce confidently wrong cash, collateral, coverage, assignment, concentration, or allocation conclusions.

Next likely phases:

- Phase 17 - TradingAgents Adapter as async research evidence only.
- Phase 18 - Frontend Trade Review Workspace after backend contracts and safety gates are stable.

## What Opus Should Review

Use Opus for:

- financial calculation semantics
- option long/short liability handling
- cash collateral and assignment exposure
- broker snapshot actionability and freshness semantics
- schema/migration decisions
- broker sync security boundaries
- secret handling
- agent-safe projection and LLM data minimization
- major architecture or roadmap disagreement
- conflicts between Codex and Claude Sonnet

Avoid using Opus for:

- routine implementation review
- frontend visual hierarchy
- small documentation cleanup
- ordinary test naming or code style

## Default Opus Read List

Read:

- `AGENTS.md`
- `docs/shared/current_roadmap.md`
- this file
- the current task section in `docs/shared/implementation_plan.md`
- relevant PM or architecture docs when the review scope requires them
- specific changed files

Do not read by default:

- full `docs/shared/completed_phases_log.md`
- full `docs/codex-b-architecture/architecture.md`
- unrelated backend files
- `.env` or private data
- `../TradingAgents`

## Output Format

- PASS or BLOCKED
- Blockers
- Important issues
- Defer items
- Suggested changes for Codex
- Files safe to commit
- Files that should remain uncommitted
