# Phase 19A - Basic Portfolio-Aware LLM Agent Team + Analysis Console Contract

Status: architecture contract for implementation
Owner: Codex B - Architecture / Tech Lead
Last updated: 2026-05-22

## Purpose

Phase 19A introduces the first visible LLM-style agent team for Portfolio Copilot. The goal is to let the user inspect role-by-role analysis for a proposed `TradeIntent` in a simple analysis console before major UI refinement.

The phase must preserve the product center: broker-aware, portfolio-aware manual trade review. Agents provide analysis-only educational commentary over approved structured evidence. Deterministic Python services remain the source of financial metrics.

## Non-Goals

- No automatic trading.
- No broker order placement, cancellation, modification, or order-ticket UI.
- No broker scraping, Fidelity credential storage, or MFA bypass.
- No LLM-generated financial metrics.
- No real news or macro calendar provider integration.
- No Forex Factory scraping.
- No real TradingAgents graph execution.
- No bull/bear debate loops.
- No trader node that proposes BUY/HOLD/SELL.
- No frontend provider calls.
- No frontend storage of portfolio/review/prompt data.

## Orchestration Choice

Use LangGraph through an app-owned wrapper.

Phase 19A may depend on LangGraph for graph execution, but the application must own the node/stage vocabulary, state schema, prompt data boundaries, provider gateway, output schemas, and fallback behavior. The graph must work with the mock LLM provider by default and must be testable without network calls or API keys.

## Stage Sequence

Approved stage order:

1. `validate_trade_intent`
2. `build_deterministic_evidence_bundle`
3. `classify_actionability`
4. `prepare_public_evidence_context`
5. `fundamentals_analyst`
6. `news_analyst`
7. `technical_analyst`
8. `risk_management_agent`
9. `portfolio_manager_agent`
10. `compose_analysis_console_output`
11. `persist_run_steps`

The first implementation may execute synchronously for a preview endpoint. Streaming/SSE can be added later after the response contract is stable.

## Recommended Backend Namespace

Add a new namespace:

`backend/app/services/agent_team/`

Keep existing `backend/app/services/agents/` for Phase 16 deterministic components. Phase 19A is a higher-level LLM-agent-team layer that consumes Phase 16/18C safe outputs.

Suggested modules:

- `state.py`
- `roles.py`
- `evidence.py`
- `prompts.py`
- `prompt_safety.py`
- `llm_provider.py`
- `mock_provider.py`
- `orchestrator.py`
- `frontend_read.py`

Add frontend/API schemas under `backend/app/schemas/agent_team.py` or a similarly explicit schema file.

## Agent State

The `AgentTeamAnalysisState` should be a typed object containing only safe, structured fields:

- `run_reference`
- `workflow_version`
- `supported_flow`
- `trade_intent_summary`
- `actionability`
- `broker_snapshot_freshness`
- `market_quote_freshness`
- `deterministic_evidence`
- `public_evidence`
- `analyst_outputs`
- `risk_management_output`
- `portfolio_manager_output`
- `stage_statuses`
- `provider_trace`
- `safety_flags`
- `errors`
- `generated_at`

Do not store raw ORM objects, provider payloads, broker identifiers, raw holdings, raw positions, account values, cash balances, or secrets in graph state.

## Deterministic Evidence

Agent-visible deterministic evidence may include:

- `TradeReviewAgentProjection`
- `PortfolioActionabilityDecision`
- broker snapshot freshness summary
- market quote freshness summary
- trade intent summary from the frontend-safe contract
- deterministic review summary from `TradeReviewWorkspaceRead`
- risk-rule violation summaries without raw/account-specific thresholds
- missing-data warnings
- covered-call and CSP modelling caveats
- safe portfolio shape counts
- Phase 16 orchestration summary

User-visible console output should be more selective:

- role outputs;
- final educational synthesis;
- actionability and freshness status;
- key deterministic evidence summary;
- caveats and unavailable states.

Do not show raw context envelopes, full prompt snapshots, internal policy traces, or all deterministic intermediate fields by default.

## Role Data Boundaries

### Fundamentals Analyst

May see:

- ticker;
- company name if available;
- public/mock fundamentals evidence;
- evidence freshness/source status.

Must not see:

- private portfolio context;
- holdings, positions, cash, buying power, account values;
- trade size, collateral, account-specific thresholds, broker/provider ids.

### News Analyst

May see:

- ticker/company;
- public/mock company news evidence;
- public/mock macro event evidence;
- evidence source and availability status.

Must not see private portfolio or account context.

### Technical Analyst

May see:

- ticker;
- public/mock market snapshot;
- public/mock technical indicators if available;
- unavailable status if no technical data exists.

Must not see private portfolio or account context.

### Risk Management Agent

May see:

- proposed `TradeIntent` summary;
- deterministic trade-review summary;
- actionability/freshness status;
- agent-safe portfolio projection;
- risk-rule summaries without raw thresholds;
- missing-data warnings and caveats.

Must not see raw holdings, raw positions, cash balances, buying power, account values, broker/provider ids, raw payloads, journal entries, or account-specific thresholds.

### Portfolio Manager Agent

May see:

- prior analyst summaries;
- risk management output;
- deterministic evidence summary;
- actionability/freshness status;
- caveats and limitations.

Must produce:

- educational synthesis;
- open risks;
- data limitations;
- manual-review status.

Must not produce:

- "you should buy/sell";
- order instructions;
- "safe to trade" or "ready to trade";
- guaranteed-return language;
- invented metrics.

## Public News and Macro Event Evidence

Phase 19A uses mocked evidence only.

Separate:

- public ticker/company news;
- public macro calendar / event-risk evidence.

Future real-provider candidates:

- Trading Economics for structured economic calendar;
- Benzinga for economic calendar plus trader-focused news;
- Forex News API for lightweight forex/news/calendar testing;
- Forex Factory only as a human reference or dev-only/export-import source if terms allow.

Do not scrape Forex Factory. Do not add live economic-calendar APIs in Phase 19A.

## LLM Provider Contract

Define an app-owned provider interface.

Conceptual request fields:

- `provider`
- `model`
- `role_name`
- `prompt_version`
- `system_prompt`
- `input_payload`
- `max_tokens`
- `timeout_seconds`
- `temperature`

Conceptual response fields:

- `provider`
- `model`
- `role_name`
- `prompt_version`
- `content`
- `output_json`
- `tokens_in`
- `tokens_out`
- `estimated_cost`
- `status`
- `error_code`

Default provider: `mock`.

Future first live provider: `google`, behind explicit opt-in configuration only.

## Provider Error Vocabulary

Use safe provider error categories:

- `rate_limited`
- `quota_exceeded`
- `provider_timeout`
- `provider_auth_error`
- `provider_unavailable`
- `invalid_response`
- `safety_validation_failed`

Provider limits must degrade to partial output. The deterministic review must remain available. The analysis console should show that some LLM analysis was unavailable due to provider limits or provider failure.

## Prompt Safety

Prompt rendering must be testable without calling an LLM.

Required tests:

- render each role prompt with synthetic inputs;
- recursively scan prompt payloads and rendered text for forbidden private fields;
- scan for private-looking value tokens;
- verify public-only roles receive no portfolio evidence;
- verify portfolio-aware roles receive only approved sanitized evidence;
- verify prompts state that deterministic services own financial metrics;
- verify prompts prohibit advice, guarantees, and execution instructions;
- validate mocked outputs against typed schemas;
- reject prohibited output phrases.

## API Contract For Analysis Console

Initial endpoint:

`POST /agent-team/trade-review-analysis/preview`

Request:

- safe trade intent fields or a supported flow payload compatible with the Phase 18C workspace;
- safe portfolio context selection reference;
- optional `analysis_mode`, defaulting to `mock`;
- no client-supplied provider freshness, actionability, broker ids, account ids, raw holdings, cash, or prompt text.

Response:

- `run_reference`
- `workflow_version`
- `generated_at`
- `analysis_mode`
- `run_status`
- `actionability`
- `broker_snapshot_freshness`
- `market_quote_freshness`
- `stage_order`
- `stage_statuses`
- `messages`
- `deterministic_evidence_summary`
- `public_evidence_summary`
- `final_synthesis`
- `caveats`
- `provider_warnings`

`messages[]` should include:

- `role_name`
- `role_label`
- `stage`
- `status`
- `content_markdown`
- `evidence_scope`
- `uses_private_context`
- `provider`
- `model`
- `error_code`

## Frontend Contract For Claude A

The first UI is an analysis console/chatbox, not a polished trading terminal.

It should:

- submit a proposed trade review to the backend endpoint;
- render role-by-role outputs;
- show final educational synthesis;
- show broker freshness and market quote freshness separately;
- show actionability/manual-review status;
- show mock/unavailable/provider-limit states;
- clearly label deterministic evidence versus LLM analysis.

It must not:

- call LLM providers directly;
- call TradingAgents directly;
- call broker or market providers directly;
- store prompts or portfolio/review data in browser storage;
- show order tickets or execution controls;
- use buy/sell recommendation or guaranteed-return wording.

## Review Gates

### Codex B

Review:

- state schema;
- prompt data boundary;
- role access rules;
- provider gateway;
- route contract;
- frontend/backend seam.

### Claude B

Review:

- forbidden private fields absent from prompts/responses;
- output schema validation;
- prohibited wording;
- provider error/rate-limit behavior;
- no real provider calls in default tests;
- no LLM-generated financial metrics.

### Real LLM/API Gate

Real Google/API calls may be added only after:

- mock graph passes;
- prompt snapshot tests pass;
- output validation passes;
- provider error taxonomy exists;
- rate-limit fallback is tested;
- backend-only configuration is reviewed;
- external tests are marked and skipped by default;
- Codex B and Claude B both pass the live-provider gate.
