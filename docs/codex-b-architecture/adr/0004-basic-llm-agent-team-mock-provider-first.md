# ADR 0004: Basic Portfolio-Aware LLM Agent Team, LangGraph, and Mock-Provider-First Execution

Status: accepted
Date: 2026-05-22
Owner: Codex B - Architecture / Tech Lead

## Context

Portfolio Copilot's product identity is a TradingAgents-inspired, portfolio-aware trade review agent team for manual investors. Phases 16, 17A, and 18C created the deterministic orchestration, public evidence boundary, and portfolio-backed trade-review workspace. The next product step is to make the agent-team analysis visible before major UI refinement.

The founder wants basic LLM agents similar in spirit to TradingAgents roles: fundamentals analyst, news analyst, technical analyst, risk management, and portfolio manager. The system should support a simple analysis console/chatbox where role outputs can be inspected for a proposed `TradeIntent`.

TradingAgents uses a LangGraph-style staged graph with analysts, debate, manager synthesis, trader, risk discussion, and portfolio manager. Portfolio Copilot should borrow the staged graph, role separation, and manager synthesis pattern, but must not copy the trading-decision model directly.

## Decision

Start **Phase 19A - Basic Portfolio-Aware LLM Agent Team + Analysis Console**.

Use **LangGraph in Phase 19A only through an app-owned orchestration boundary**. App-owned means Portfolio Copilot owns:

- graph stage order;
- state schema;
- prompt data boundaries;
- role access policy;
- LLM provider gateway;
- rate-limit and provider-error handling;
- output schemas;
- persistence mapping;
- frontend read contract;
- safety language and prohibited-output checks.

Do not call or embed TradingAgents' graph as the product workflow. Do not copy TradingAgents source. TradingAgents remains architectural inspiration and later optional public research evidence.

Phase 19A uses a **mock LLM provider by default** behind real provider contracts. Real LLM/API calls are a second gate. Google Gemini is the preferred first live provider candidate because the founder has a Google API key for testing, but it must be backend-only, explicit opt-in, external-test-only by default, and safe under free-tier rate limits.

## Phase 19A Graph

Recommended app-owned graph stages:

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

Phase 19A does not include bull/bear debate loops, a trader node, deep TradingAgents execution, real news APIs, real macro calendar APIs, or frontend research-evidence polish.

## Role Access Policy

Public-only roles:

- Fundamentals Analyst: public ticker/company/fundamentals evidence only.
- News Analyst: public ticker/company news and public macro/event-risk evidence only.
- Technical Analyst: ticker plus public/mock market snapshot or technical indicators only.

Sanitized portfolio-aware roles:

- Risk Management Agent: may see sanitized `TradeIntent`, actionability/freshness, deterministic review summaries, risk-rule summaries without raw thresholds, missing-data warnings, and agent-safe portfolio projection.
- Portfolio Manager Agent: may see prior role summaries, deterministic review summary, actionability/freshness, caveats, and agent-safe portfolio projection.

Forbidden by default for all LLM prompts and frontend analysis-console contracts:

- raw holdings;
- raw positions;
- account values;
- cash balances or buying power;
- broker account ids;
- provider account ids;
- provider connection ids;
- provider contract ids;
- raw provider payloads or raw metadata;
- secrets, API keys, access tokens, portal URLs, or secret refs;
- trade journal entries;
- account-specific thresholds or private strategy settings.

The LLM workflow should be portfolio-aware through sanitized deterministic evidence, not through raw brokerage data.

## News and Macro Event Evidence

TradingAgents' News Analyst pattern is useful: a public-news role can consume ticker news and global macro context, then hand a `news_report`-like output to later agents.

Portfolio Copilot should split the concept internally:

- public company/ticker news evidence;
- public macro calendar / event-risk evidence.

Phase 19A should use mocked public news and mocked macro events only. A later real-provider phase may evaluate Trading Economics, Benzinga Economic Calendar, Forex News API, or another licensed provider. Forex Factory can remain a human reference or dev-only/export-import reference if terms allow, but the app should not scrape Forex Factory or make it the first production dependency.

## LLM Provider Gateway

Define an app-owned provider gateway with a stable interface, for example:

- `MockLLMProvider`
- future `GoogleGeminiLLMProvider`
- later OpenAI, Anthropic, OpenRouter, local/Ollama-compatible providers if approved.

Configuration should use app-owned names such as:

- `POA_LLM_MODE=mock|live`
- `POA_LLM_PROVIDER=mock|google|openai|anthropic|openrouter|ollama`
- `POA_LLM_MODEL=...`
- `POA_LLM_TIMEOUT_SECONDS=...`
- `POA_LLM_MAX_RETRIES=...`
- `POA_LLM_TOKEN_BUDGET_PER_RUN=...`
- `POA_LLM_RATE_LIMIT_FALLBACK=partial_report`

Provider API keys remain backend-only environment variables such as `GOOGLE_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`. They must never be bundled into frontend code, stored in reports, or printed in logs.

## Provider Error Handling

Real provider calls must classify failures into safe statuses:

- `rate_limited`
- `quota_exceeded`
- `provider_timeout`
- `provider_auth_error`
- `provider_unavailable`
- `invalid_response`
- `safety_validation_failed`

Rate limits or quota exhaustion must produce a partial analysis result, not a broken trade-review workflow. Deterministic evidence remains available. Affected agent steps should be `failed` or `skipped`, and the run should become `partially_completed` with a user-facing explanation that some LLM analysis was unavailable.

## Prompt and Output Safety

Every prompt template must have synthetic prompt snapshot tests.

Tests must prove:

- forbidden private keys do not appear in rendered prompts;
- private-looking value tokens do not appear in rendered prompts;
- public-only roles do not receive sanitized portfolio evidence;
- portfolio-aware roles receive only approved sanitized evidence;
- prompts tell agents not to calculate or invent financial metrics;
- outputs validate against typed role schemas;
- outputs do not contain prohibited advice, guarantee, or execution language.

LLM-generated outputs may analyze, debate, explain, and synthesize. They must not calculate financial metrics, create trade orders, or tell the user what they should buy or sell.

## Persistence and Frontend

Phase 19A should reuse existing `agent_runs`, `agent_steps`, and report-history contracts where practical. It may also return a stateless/synthetic preview response for the first console slice if persistence plumbing would make the slice too large, but the schema must be persistence-compatible.

The frontend analysis console should show:

- run status;
- role-by-role messages;
- actionability/freshness status;
- deterministic evidence summary;
- public evidence availability;
- final educational synthesis;
- caveats and unavailable/provider-limit states.

It must not render order tickets, execution controls, "confirm trade" controls, guaranteed-return language, or "you should buy/sell" wording.

## Consequences

Positive:

- Makes the agent-team product identity visible.
- Aligns better with TradingAgents' staged graph pattern while preserving app ownership.
- Lets the founder test basic agent outputs before frontend beautification.
- Creates the right boundary for later Google/API testing and eventual richer debate.

Tradeoffs:

- Adds LangGraph and LLM orchestration complexity earlier.
- Requires strict prompt and output safety tests before real API calls.
- News/macro data remains mocked until a licensed provider is selected.

## Review Guidance

Architecture reviews should block changes that:

- call real LLM APIs before the mock-provider graph and prompt safety pass;
- send raw/private brokerage data to prompts;
- let public analyst roles see portfolio context;
- let LLMs invent financial metrics;
- introduce buy/sell recommendation, order, execution, or guaranteed-return language;
- add real news/macro providers, Forex Factory scraping, TradingAgents execution, or frontend provider calls without a separate approved gate.
