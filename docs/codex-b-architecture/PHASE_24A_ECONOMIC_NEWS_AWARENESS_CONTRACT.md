# Phase 24A Economic Calendar Awareness Contract

Status: architecture contract for FMP-backed personal-demo evaluation
Owner: Codex B - Architecture / Systems / Integration
Date: 2026-05-29
Related plan task: `P24A-T1`

## Goal

Create a backend-owned economic calendar awareness foundation for Dashboard
display, centered on macro events similar to a Forex Factory-style calendar.

Phase 24A uses Financial Modeling Prep (FMP) Economic Calendar as the approved
personal-demo provider path after the synthetic contract is reviewed. FMP is not
approved as a commercial production provider by this contract.

The implementation must be source-labelled and analysis-only. It must not
present events as trade signals, recommendations, alerts to act, or guaranteed
market-moving claims.

## Product Use Cases

Phase 24A supports:

- a Dashboard "Economic awareness" panel for public macro/calendar context;
- red-folder/high-importance style economic events such as CPI, FOMC, jobs
  data, PCE, GDP, PMI, retail sales, central-bank decisions, and major
  scheduled macro releases;
- explicit freshness, source, and "not a trading signal" labels;
- provider-neutral contracts that can switch from synthetic fixtures to FMP
  without frontend rewrites.

It does not support:

- ticker/company news;
- trading recommendations;
- sentiment scores that imply buy/sell action;
- personalized news based on private holdings;
- broker or account data;
- direct LLM/agent ingestion in Phase 24A;
- WebSocket or streaming implementation.

## Dashboard Contract Shape

Initial backend endpoint:

- `GET /economic-calendar/events`

If later user-specific filtering is approved, it should be introduced as a new
reviewed contract rather than overloading the global public feed.

`EconomicCalendarEventListRead`

- `data_mode`
- `source_label`
- `as_of_label`
- `freshness_label`
- `window_start`
- `window_end`
- `timezone`
- `importance_source`
- `items`
- `demo_notice`
- `is_trading_signal`
- `limitations`

`EconomicCalendarEventRead`

- `event_reference`
- `event_date_label`
- `event_time_label`
- `event_title`
- `event_type`
- `importance`
- `importance_source`
- `country`
- `currency`
- `actual_label`
- `forecast_label`
- `previous_label`
- `unit_label`
- `source_label`
- `freshness_label`
- `is_trading_signal`
- `data_mode`

Allowed `importance` values:

- `high`
- `medium`
- `low`
- `unknown`

Allowed `importance_source` values:

- `provider`
- `app_classified`
- `unavailable`

Allowed `event_type` values:

- `economic_release`
- `central_bank`
- `holiday`
- `speech`
- `other`

Allowed `data_mode` values:

- `synthetic`
- `replay`
- `provider_reference`
- `unavailable`

The first backend task may emit only `synthetic` or `replay`. The FMP adapter
task may emit `provider_reference` when explicitly opted in.

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

## Importance Classification

FMP may not provide a Forex Factory-style impact label that is complete enough
for the desired UI. Phase 24A may therefore include an app-owned deterministic
importance classifier.

Rules:

- Provider-supplied importance may be rendered only when the adapter receives a
  documented provider field and maps it through a typed enum.
- App-owned classification must be labelled `importance_source="app_classified"`.
- Classification must be deterministic, table/rule based, and tested.
- Classification must never imply trading advice or urgency.
- Unknown events must degrade to `importance="unknown"`.

Examples of high-importance event families:

- FOMC / Fed rate decision;
- CPI / Core CPI;
- PCE / Core PCE;
- Nonfarm Payrolls / Unemployment Rate;
- GDP advance/preliminary/final;
- ISM / PMI headline releases;
- Retail Sales headline releases.

## Privacy Boundary

The economic calendar awareness contract must not include:

- user holdings, positions, quantities, lots, or portfolio values;
- broker/account/provider identifiers;
- account-specific thresholds;
- raw provider payloads;
- provider entitlement metadata;
- credentials, API keys, or access tokens;
- LLM prompts, provider traces, or agent outputs.

## Provider Boundary

Phase 24A provider choice for personal-demo evaluation:

- FMP Economic Calendar REST endpoint.

Provider rules:

- Synthetic fixtures remain the default test path.
- FMP adapter must use an injected HTTP/client boundary in tests.
- No network call may run on import or default tests.
- No FMP credential may appear in frontend code, docs, tests, fixtures, logs, or
  committed files.
- Any opt-in local refresh must fail closed to last-good cache or unavailable
  state.
- Raw FMP response payloads must not be exposed to frontend, agents, prompts, or
  persisted public read models.

Explicitly not approved in Phase 24A:

- Forex Factory scraping;
- ticker/company news providers;
- WebSocket/streaming provider integration;
- Trading Economics evaluation;
- market quotes or options data;
- agent/news-analyst tool ingestion.

Future provider evaluation must be separately approved and must review:

- license and permitted display;
- refresh rate and delay;
- attribution requirements;
- retention/replay rights;
- whether red-folder labels are provider-owned or app-derived;
- whether agent use of sanitized event evidence is allowed.

## Frontend Boundary

No frontend work is authorized by `P24A-T1`.

After backend review and FMP adapter review, Claude A may add a Dashboard
economic-calendar panel only if it:

- shows source and freshness;
- keeps `not a trading signal` visible;
- does not create urgency or advice;
- handles `synthetic`/`replay` demo labels;
- does not merge economic awareness with risk alerts;
- does not show ticker/company news.

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
- app-owned importance classification when provider importance is unavailable;
- FMP adapter mapping through injected-client tests;
- forbidden-wording tests;
- forbidden-private-field tests;
- no external calls in default tests.
