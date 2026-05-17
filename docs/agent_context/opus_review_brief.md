# Opus Review Brief

Use this short brief for high-stakes Claude Opus reviews. Prefer this over loading the full `docs/implementation_plan.md` or `docs/completed_phases_log.md`.

## Project Direction

This project is a portfolio-aware options income and risk copilot for manual traders. It is not just a SnapTrade dashboard, not just a market data viewer, and not a thin TradingAgents wrapper.

The system combines:

1. Portfolio system of record.
2. Market data layer.
3. Deterministic options/risk engine.
4. Custom portfolio-aware agents.
5. Optional TradingAgents stock/company research adapter.
6. Dashboard and durable report history.

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

Completed through Phase 10:

- Users/accounts.
- Internal cash/stock/option storage.
- SnapTrade-first read-only broker sync foundation, mock-first.
- Manual input and Fidelity CSV preview fallback.
- Broker freshness and portfolio warning surfaces.
- Report/agent persistence foundation:
  - `report_threads`
  - `report_messages`
  - `agent_runs`
  - `agent_steps`
  - minimal report APIs
  - deterministic markdown report output

## Active Roadmap

Current active phase: Phase 11 - Frontend Dashboard Shell A.

Next:

- Phase 12 - Market Data Contracts and Manual Provider.
- Phase 13 - Deterministic Options/Risk Engine MVP.
- Phase 14 - Custom Portfolio-Aware Agent Orchestrator.
- Phase 15 - TradingAgents Adapter.
- Phase 16 - Frontend Agent Workspace B.

## What Opus Should Review

Use Opus for:

- financial calculation semantics
- option long/short liability handling
- cash collateral and assignment exposure
- schema/migration decisions
- broker sync security boundaries
- secret handling
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
- `docs/current_roadmap.md`
- this file
- the current task section in `docs/implementation_plan.md`
- specific changed files

Do not read by default:

- full `docs/completed_phases_log.md`
- full `docs/architecture.md`
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
