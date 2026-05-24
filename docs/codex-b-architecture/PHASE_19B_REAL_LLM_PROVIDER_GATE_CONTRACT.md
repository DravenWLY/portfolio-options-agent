# Phase 19B - Real LLM Provider Gate Contract

Status: architecture contract for implementation
Owner: Codex B - Architecture / Tech Lead
Last updated: 2026-05-22

## Purpose

Phase 19B introduces the first real LLM-provider-capable backend path for the Phase 19A agent team while keeping the product safe, mock-first by default, and deterministic-review centered.

The goal is not to improve prompts for investment advice. The goal is to prove that Portfolio Copilot can run the existing app-owned agent-team provider contract against a live provider only when the backend is explicitly configured to do so, with privacy validation, rate-limit fallback, output validation, and review gates in place.

Preferred first live provider candidate: Google/Gemini, because the founder has a Google API key for controlled testing.

## Non-Goals

- No frontend API keys or frontend provider calls.
- No client-supplied provider, model, prompt, temperature, freshness, actionability, or portfolio metadata.
- No automatic trading.
- No order placement, cancellation, modification, execution, or order-ticket UI.
- No broker scraping, credential storage, or MFA bypass.
- No SnapTrade, broker, market-data, news, macro, TradingAgents, or external research calls as part of this phase.
- No raw private portfolio data in prompts, provider traces, responses, cache keys, analytics, logs, docs, or tests.
- No LLM-generated financial metrics.
- No user-facing claims that a trade is safe, ready, recommended, or guaranteed.

## Scope

Phase 19B is backend-only unless a later task explicitly asks Claude A to adjust UI labels for provider status. The analysis console may continue to use the same frontend contract from Phase 19A.

Allowed implementation scope:

- provider configuration model;
- provider factory/resolver;
- Google/Gemini provider adapter behind the existing `LLMProvider` protocol;
- lazy optional SDK import;
- no-live-call default tests with mocked provider client behavior;
- external/live smoke test marker that is skipped by default;
- provider error classification;
- prompt and output safety validator hardening for real provider text;
- orchestrator/provider integration using server-owned config only;
- docs and review gates.

## Default Behavior

Default behavior must remain:

- `POA_LLM_MODE=mock`;
- `MockLLMProvider`;
- no API key required;
- no network call;
- all default tests synthetic and offline.

Live provider behavior is enabled only when all are true:

- backend configuration explicitly sets live mode;
- provider is explicitly set to Google;
- a backend-only Google API key is available to the process;
- the code path is running in a reviewed live-provider mode;
- tests or manual smoke runs are explicitly opted into external execution.

Frontend requests must not be able to switch the provider or model.

## Configuration Contract

Recommended app-owned environment names:

- `POA_LLM_MODE=mock|live`
- `POA_LLM_PROVIDER=mock|google`
- `POA_LLM_MODEL=<provider model name>`
- `POA_LLM_TIMEOUT_SECONDS=<positive integer>`
- `POA_LLM_MAX_RETRIES=<non-negative integer>`
- `POA_LLM_TOKEN_BUDGET_PER_RUN=<positive integer>`
- `POA_LLM_RATE_LIMIT_FALLBACK=partial_report`
- `POA_LLM_LIVE_TESTS=0|1`

Provider API keys remain provider-native and backend-only:

- `GOOGLE_API_KEY`

Rules:

- never expose provider keys to frontend code;
- never print keys or provider exception bodies;
- never persist keys, prompts, raw provider responses, or private prompt payloads;
- return generic safe error messages to the UI.

## Provider Factory

Add a backend provider resolver that returns an `LLMProvider`:

- mock mode returns `MockLLMProvider`;
- live Google mode returns `GoogleGeminiLLMProvider`;
- invalid config fails closed before any provider call;
- missing dependency or missing credential returns a safe configuration error path, not a secret-bearing exception.

The resolver must be server-owned. API clients cannot choose provider/model.

## Google/Gemini Adapter

The Google adapter should implement the existing Phase 19A `LLMProvider` protocol.

Provider adapter requirements:

- lazy import the Google SDK only when live Google mode is selected;
- construct requests from `LLMProviderRequest` only;
- keep prompts backend-only;
- apply timeout/retry limits;
- map responses into `LLMProviderResponse`;
- never return raw provider payloads;
- never expose provider request ids if they can be account- or key-correlated;
- classify failures into the approved provider status vocabulary.

Implementation must verify current official Google SDK/API usage before adding a dependency or finalizing SDK calls. The architecture contract intentionally owns the app boundary, not the provider SDK details.

## Error and Rate-Limit Handling

Approved provider statuses remain:

- `ok`
- `skipped`
- `failed`
- `rate_limited`
- `quota_exceeded`
- `provider_timeout`
- `provider_auth_error`
- `provider_unavailable`
- `invalid_response`
- `safety_validation_failed`

Live provider failures must degrade safely:

- deterministic review remains available;
- failed roles become unavailable;
- run status becomes `partially_completed`;
- provider warnings use generic messages;
- no raw exception body, prompt, key, account data, provider payload, or stack trace reaches frontend responses.

## Prompt Safety

Phase 19B must harden the mock-phase validator before real provider calls.

Separate validation layers:

1. Prompt/input payload validation:
   - recursive forbidden key rejection;
   - recursive private-looking value rejection;
   - secret/API-key/access-token pattern rejection;
   - prompt text must include role boundaries and deterministic-metric ownership rules.

2. Provider output validation:
   - recursive forbidden key rejection;
   - prohibited advice/execution/guarantee phrase rejection;
   - no invented financial metrics;
   - no order instructions;
   - no raw provider payloads;
   - no private identifier or secret-like token patterns.

3. Console response validation:
   - existing Pydantic `extra="forbid"`;
   - response-model validation;
   - forbidden-field sweep;
   - prohibited phrase sweep.

The current mock-phase substring guard is intentionally over-conservative. Phase 19B should avoid relying on bare domain words such as `cash`, `positions`, or `threshold` as universal response blockers. Those words may be legitimate in safety instructions or generic analysis. The real-provider gate should prefer field/key validation, secret/id patterns, and stricter generated-metric checks.

## No LLM-Generated Financial Metrics

For the first live-provider gate, provider-generated text should not introduce new numeric financial claims.

Recommended initial rule:

- role outputs may reference deterministic evidence qualitatively;
- role outputs must not create new dollar values, percentages, probabilities, share counts, contract counts, breakevens, price targets, ROI, yield, or Greeks;
- numeric-like generated claims should be rejected or replaced with unavailable output unless explicitly present in approved deterministic evidence and rendered through a structured citation field in a later phase.

This keeps deterministic Python services as the only source of financial metrics.

## Endpoint Behavior

The existing Phase 19A endpoint may remain:

`POST /agent-team/trade-review-analysis/preview`

Provider selection is backend-owned. If live mode is enabled server-side, the endpoint may use the live provider through the same orchestrator contract, but clients must not supply provider/model/prompt fields.

If live mode is not enabled, the endpoint remains mock-only.

## Testing Contract

Default tests must not call external APIs.

Required tests:

- config defaults to mock;
- invalid live config fails closed;
- missing Google key in live mode maps to safe provider/auth configuration behavior;
- Google provider is not imported or constructed in mock mode;
- mocked Google success maps to `LLMProviderResponse(status="ok")`;
- mocked rate-limit/quota/auth/timeout/unavailable/invalid-response cases map to approved statuses;
- provider exception messages are sanitized;
- prompt payloads reject forbidden private keys and private-looking values;
- output payloads reject advice/execution/guarantee wording and generated metric patterns;
- orchestrator preserves partial completion on provider failure;
- existing P19A agent-team endpoint and Phase 18C trade-review tests still pass.

External/live smoke tests:

- must be marked `external`;
- must be skipped by default;
- must require explicit opt-in such as `POA_LLM_LIVE_TESTS=1`;
- must not inspect `.env` in agent review contexts;
- must use synthetic prompts and synthetic trade intents only.

## Review Gates

Codex B owns:

- Phase 19B architecture contract and implementation plan;
- architecture review of config/provider boundary;
- final integration signoff before real live calls become a routine development path.

Codex C owns:

- backend implementation and tests against this contract.

Claude B owns:

- backend safety/QA review after Codex C implementation;
- review of prompt/output safety, no secrets, no private data, no invented metrics, and no live default calls.

Claude A is not needed for Phase 19B unless the provider status UX needs a small copy-only adjustment after backend review.

## PASS Criteria for Phase 19B

- Mock remains default.
- No default test or local app startup requires a Google API key.
- Live Google provider is reachable only through explicit backend config.
- No frontend provider/key path exists.
- No raw private portfolio data can enter prompts/provider traces/frontend responses.
- Rate-limit/quota/auth/timeout failures degrade to safe partial output.
- Generated text is analysis-only and cannot introduce financial metrics, advice, order instructions, or guaranteed-return language.
- Codex B and Claude B review gates pass before any real live-provider workflow is treated as available.
