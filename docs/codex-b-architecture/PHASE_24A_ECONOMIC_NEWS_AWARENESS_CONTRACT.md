# Phase 24A Economic News Awareness Contract

Status: architecture contract for future backend slice
Owner: Codex B - Architecture / Systems / Integration
Date: 2026-05-27
Related plan task: `P24A-T1`

## Goal

Create a backend-owned economic/news awareness foundation for Dashboard display
and later, separately approved, sanitized agent evidence.

The initial implementation must be synthetic/replay-first, source-labelled, and
analysis-only. It must not present news or macro events as trade signals,
recommendations, alerts to act, or live market-moving claims.

## Product Use Cases

Phase 24A supports:

- a Dashboard "Economic awareness" panel for public macro/calendar context;
- red-folder or high-importance economic events such as CPI, FOMC, jobs data,
  central-bank decisions, or major earnings-calendar awareness;
- explicit freshness, source, and "not a trading signal" labels;
- later provider evaluation without redesigning frontend contracts.

It does not support:

- trading recommendations;
- sentiment scores that imply buy/sell action;
- personalized news based on private holdings;
- broker or account data;
- direct LLM/agent ingestion in the initial slice.

## Dashboard Contract Shape

Initial backend endpoint:

- `GET /economic-events`

If later user-specific filtering is approved, it should be introduced as a new
reviewed contract rather than overloading the global public feed.

`EconomicEventListRead`

- `data_mode`
- `source_label`
- `as_of_label`
- `freshness_label`
- `items`
- `demo_notice`
- `is_trading_signal`
- `limitations`

`EconomicEventRead`

- `event_reference`
- `event_date`
- `event_time_label`
- `event_title`
- `event_type`
- `importance`
- `currency_or_region`
- `source_label`
- `freshness_label`
- `relevance_label`
- `is_trading_signal`
- `data_mode`
- `details_url_label`

Allowed `importance` values:

- `red_folder`
- `high`
- `medium`
- `low`
- `unknown`

Allowed `event_type` values:

- `economic_release`
- `central_bank`
- `earnings_calendar`
- `holiday`
- `geopolitical`
- `other`

Allowed `data_mode` values:

- `synthetic`
- `replay`
- `delayed`
- `provider_reference`
- `unavailable`

The initial task may emit only `synthetic` or `replay`.

## Language Rules

Every response and frontend panel must preserve these concepts:

- informational awareness only;
- not a trading signal;
- source-labelled;
- freshness/as-of visible;
- public data only.

Forbidden wording:

- "buy because";
- "sell because";
- "trade signal";
- "market will";
- "guaranteed";
- "safe to trade";
- "ready to trade";
- "top event to trade";
- "AI pick".

## Privacy Boundary

The economic/news awareness contract must not include:

- user holdings, positions, quantities, lots, or portfolio values;
- broker/account/provider identifiers;
- account-specific thresholds;
- raw provider payloads;
- provider entitlement metadata;
- credentials, API keys, or access tokens;
- LLM prompts, provider traces, or agent outputs.

## Provider Boundary

The initial implementation must not call Forex Factory, Bloomberg, CNBC,
Yahoo, Alpaca, Intrinio, Databento, dxFeed, Google, OpenAI, Anthropic, or any
other external provider.

Future provider evaluation must be separately approved and must review:

- license and permitted display;
- refresh rate and delay;
- attribution requirements;
- retention/replay rights;
- whether red-folder labels are provider-owned or app-derived;
- whether agent use of sanitized event evidence is allowed.

## Frontend Boundary

No frontend work is authorized by `P24A-T1`.

After backend review, Claude A may add a Dashboard economic-awareness panel only
if it:

- shows source and freshness;
- keeps `not a trading signal` visible;
- does not create urgency or advice;
- handles `synthetic`/`replay` demo labels;
- does not merge economic awareness with risk alerts.

## Agent Boundary

No market/news data ingestion by LLM agents is authorized in Phase 24A.

If PM later wants the News Analyst to use economic/news data, Codex B must first
define a sanitized public-evidence contract that is separate from Dashboard
display. It must exclude private portfolio context unless an agent-safe
projection is explicitly approved.

## Acceptance Direction

The first implementation should prove:

- red-folder/high-importance event representation;
- no-event state;
- stale/unavailable state;
- source/freshness labels;
- `is_trading_signal=false` invariant;
- forbidden-wording tests;
- forbidden-private-field tests;
- no external calls in default tests.
