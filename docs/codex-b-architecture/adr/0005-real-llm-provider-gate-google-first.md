# ADR 0005: Real LLM Provider Gate, Google-First, Mock-Default

Status: accepted
Date: 2026-05-22
Owner: Codex B - Architecture / Tech Lead

## Context

Phase 19A introduced the first app-owned agent-team analysis console using a mock LLM provider behind real provider contracts. The founder wants to test basic LLM-agent outputs with a Google API key, but the product must remain read-only, deterministic-review centered, and privacy safe.

The existing mock-provider foundation is intentionally conservative. Before live provider calls become available, the system needs a backend-owned configuration gate, provider factory, live-provider adapter boundary, rate-limit fallback, prompt/output validation, and review gates.

## Decision

Start **Phase 19B - Real LLM Provider Gate** as a backend-only phase.

Use Google/Gemini as the preferred first live provider candidate, but keep `MockLLMProvider` as the default provider.

Live provider calls are allowed only behind explicit backend configuration. Frontend clients must not provide provider names, model names, prompt text, temperature, credentials, freshness, actionability, or private portfolio metadata.

Provider API keys remain backend-only environment variables and must never be bundled into frontend code, logged, stored, returned in responses, or copied into docs/tests.

## Configuration Boundary

Use app-owned configuration names for product behavior:

- `POA_LLM_MODE=mock|live`
- `POA_LLM_PROVIDER=mock|google`
- `POA_LLM_MODEL=...`
- `POA_LLM_TIMEOUT_SECONDS=...`
- `POA_LLM_MAX_RETRIES=...`
- `POA_LLM_TOKEN_BUDGET_PER_RUN=...`
- `POA_LLM_RATE_LIMIT_FALLBACK=partial_report`
- `POA_LLM_LIVE_TESTS=0|1`

Use provider-native names only for backend secrets:

- `GOOGLE_API_KEY`

## Provider Boundary

Add a provider resolver/factory that returns an `LLMProvider`.

- mock mode returns `MockLLMProvider`;
- live Google mode returns a Google/Gemini provider adapter;
- invalid live config fails closed;
- missing dependency/key errors become safe provider statuses or configuration errors;
- SDK imports are lazy and must not affect app startup in mock mode.

## Safety Boundary

No raw private brokerage or account data may enter:

- prompt payloads;
- provider request metadata;
- provider response metadata;
- provider traces;
- cache keys;
- frontend contracts;
- logs;
- docs;
- tests.

Forbidden data includes raw holdings, raw positions, account values, cash balances, buying power, broker/provider ids, provider contract ids, raw provider payloads, secrets/API keys/access tokens/portal URLs, trade journal entries, account-specific thresholds, and private strategy settings.

LLMs may analyze and synthesize approved structured evidence. They must not calculate or invent financial metrics, issue buy/sell advice, create order instructions, claim a trade is safe/ready, or promise outcomes.

## Validator Hardening

Before live calls, split validation into:

- strict prompt/input validation;
- generated-output validation;
- final frontend response validation.

The mock-phase substring guard that blocks generic words such as `cash`, `positions`, and `threshold` is acceptable for mocked tests but too blunt for real provider text. Phase 19B should replace or supplement it with field/key checks, secret/id pattern checks, generated-metric checks, and prohibited advice/execution phrase checks.

## Failure Handling

Provider failures must map into the approved status vocabulary:

- `rate_limited`
- `quota_exceeded`
- `provider_timeout`
- `provider_auth_error`
- `provider_unavailable`
- `invalid_response`
- `safety_validation_failed`

Failures degrade to partial output. Deterministic review remains available.

## Consequences

Positive:

- Enables controlled real LLM testing without changing frontend contracts.
- Preserves app-owned orchestration and provider-agnostic role contracts.
- Makes rate-limit/quota behavior explicit before users see live provider output.

Tradeoffs:

- Adds configuration and provider-boundary complexity.
- Requires stricter output validation before real LLM calls can be trusted.
- Google-specific adapter details must remain isolated so later providers can be added without changing agent roles.

## Review Guidance

Block changes that:

- make live provider calls by default;
- require a Google API key for app startup or default tests;
- expose API keys or prompts to frontend;
- allow clients to choose provider/model/prompt;
- send raw/private portfolio data to LLMs;
- let LLMs invent financial metrics;
- convert provider failures into broken deterministic review;
- introduce TradingAgents execution, real news providers, broker calls, or market-data calls as part of this phase.
