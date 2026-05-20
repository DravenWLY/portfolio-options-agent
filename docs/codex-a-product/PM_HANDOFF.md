# PM Handoff from Codex C

## Current Repo Status

The repo is a working full-stack local development app with a substantial backend foundation and a React/Vite dashboard. It is not production-ready and is not yet a public product.

Current docs indicate Phases 1-15 are complete and Phase 16 is active. Some recent backend Phase 14/15 work may still be uncommitted; check `git status` before planning work.

## Current Product State

Portfolio Copilot is framed as a read-only portfolio-aware trade review and risk copilot for manual investors.

The strongest current wedge is options-aware portfolio risk review, but the product has been deliberately broadened beyond wheel/CSP/covered-call workflows. The core abstraction is `TradeIntent` for proposed stock, ETF, and option trades.

The current product promise is:

> Before a user manually places a stock, ETF, or options trade outside this app, help them understand portfolio impact, cash/collateral impact, exposures, data freshness, and risk-rule violations.

## Current Technical State

Implemented foundations include:

- FastAPI backend, PostgreSQL, SQLAlchemy, Alembic, pytest.
- Users/accounts and multi-account portfolio storage.
- Cash balances, stock/ETF positions, option contracts, option positions.
- SnapTrade read-only broker sync and connection flow.
- Encrypted SnapTrade user-secret storage and local-dev access guard.
- Manual input and Fidelity CSV fallback.
- Portfolio summary and broker-data warnings.
- React/Vite dashboard shell, broker connection UI, market data status slice, risk review slice, appearance mode, and collapsible sidebar.
- Report/agent persistence foundation.
- Strategy-neutral market data contracts with manual/mock provider only.
- Generic deterministic option/risk services.
- TradeIntent foundation and deterministic trade-review engine.
- Agent-safe projection for trade-review reports.

Not implemented or not production-ready:

- Real market data provider adapter.
- Portfolio Snapshot Actionability Policy as a first-class gate.
- Custom agent orchestrator.
- TradingAgents adapter.
- Frontend trade review workspace.
- Hosted authentication, production deployment, observability, data deletion/export, and formal compliance/privacy materials.

## What Is Unclear

- First target customer segment and paid MVP.
- Whether broker sync is required for first external users or whether manual/CSV mode should be the safer beta.
- How strict the product should be when broker portfolio snapshots are stale but market quotes are fresh.
- Which trade intents are required in MVP versus later.
- How much AI explanation should appear before compliance/security review.

## Current Risks

- Product scope can drift into a brokerage dashboard, options-income tool, AI stock picker, or TradingAgents wrapper.
- Broker portfolio snapshots may be stale/daily while market quotes later become fresh; polished agent reports could sound current when inputs are not.
- Real brokerage data is sensitive and can leak into prompts, logs, frontend fields, reports, or review sessions if boundaries are loose.
- Backend implementation has moved faster than formal PM artifacts.
- Architecture docs are large; future agents need concise current-context docs to avoid context overload.

## Current MVP Assumptions

- Read-only manual decision support.
- No automatic trading or order execution.
- Broker sync is useful but not trustworthy as live unless proven.
- Deterministic Python calculates metrics.
- LLMs explain structured results and do not invent metrics.
- Options are an early wedge, not the product boundary.

## Recommended First 5 PM Tasks

1. Write a one-page MVP definition: target user, core job-to-be-done, top 3 workflows, explicit non-goals.
2. Decide the first supported trade-review flows for MVP.
3. Define product policy for stale broker snapshots: block, downgrade to analysis-only, or user-confirmed override.
4. Draft positioning: why this differs from broker dashboards, option screeners, portfolio trackers, and AI stock research tools.
5. Define initial success metrics for local MVP and beta: review completion, stale-data guardrail hits, report usefulness, user trust, and retention proxy.

## Decisions PM Should Make Before More Implementation

- Whether Portfolio Snapshot Actionability Policy is a pre-Phase-16 blocker.
- MVP target segment.
- MVP trade-review workflow list.
- Product wording for stale data, analysis-only mode, and AI explanations.
- Which frontend workspace matters first: agent report review or trade intent entry/review.

## Decisions PM Should Not Overthink Yet

- Exact pricing.
- Enterprise/advisor workflows.
- Multi-leg advanced optimizer.
- Real provider choice beyond keeping SnapTrade primary and provider abstraction open.
- Full compliance program for a hosted public launch.

## How To Communicate Decisions

For Codex B Architecture:

- State the product decision, affected user flow, required contracts, and non-goals.

For Codex C Backend:

- State the accepted task, files/areas likely affected, required tests, and safety boundaries.

For Claude A Frontend:

- State the user story, required states, copy boundaries, and API contract readiness.

## Engineering Framework Sections For PM First Pass

Use `docs/shared/ENGINEERING_REVIEW_FRAMEWORK.md` sections on:

- Product Definition and User Value
- Audience and Communication
- Complexity Control
- Metrics and Observability
- Documentation and Maintainability
- Teamwork and Handoff Readiness
