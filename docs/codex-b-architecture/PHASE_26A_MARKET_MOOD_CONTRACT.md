# Phase 26A Market Mood Contract

Status: active internal-demo architecture reference
Owner: Codex B
Related plan: `docs/shared/implementation_plan.md` Phase 26A

## Purpose

Market Mood is a secondary Market Context surface based on CNN-derived Fear &
Greed data. It gives self-directed/manual investors broad market sentiment
context before they run a portfolio-aware trade review.

It is context only. It must not become a trading signal, market timing system,
screener, AI stock picker, actionability input, deterministic risk-rule input,
or LLM/agent input by default.

## Product Shape

Dashboard card:

- show only the overall Fear & Greed score/rating;
- use a Portfolio Copilot 0-100 bar/gauge treatment;
- keep the card glanceable: score, rating, compact source label, and optional
  data-mode/freshness affordance only;
- do not repeat generic disclaimer text on every Dashboard card;
- do not show component details on the dashboard.

Detail page:

- show the overall Fear & Greed Index;
- show the 7 component indicators:
  - Market Momentum;
  - Stock Price Strength;
  - Stock Price Breadth;
  - Put/Call Options;
  - Market Volatility;
  - Safe Haven Demand;
  - Junk Bond Demand;
- show interactive historical graphs for the overall index and each component;
- on hover, show date and value label for the hovered point;
- do not force every component graph onto a 0-100 scale. Each component graph
  should use backend-provided raw-value series, units, value formatting, and
  axis hints. The 0-100 score is a normalized sentiment score; it is not the
  same thing as every component's raw metric.
- show component summary, current normalized score/rating, raw current value
  label when available, and explanation text;
- show optional 1-week / 1-month / 1-year comparisons when backend-derived from
  cached history.

## Source Caveat

The source is CNN-derived Fear & Greed data from an unofficial/internal endpoint
pattern. This is approved only for internal demo pending source/rights review.

Required user-facing caveat:

> Source: CNN-derived Fear & Greed data. Not affiliated with CNN. Latest
> available snapshot. Internal demo only pending source/rights review.

Do not use CNN logos, CNN branding treatment, or clone CNN's exact visual
design.

## Backend Contract

Endpoints:

- `GET /market-context/market-mood`
- `POST /market-context/market-mood/refresh`

`POST` is explicit/manual only in the initial slice. No startup fetch is
authorized.

Runtime refresh wiring:

- `POST /market-context/market-mood/refresh` may use a backend-owned
  CNN-derived HTTP client behind an injected transport boundary.
- The refresh path must parse and validate provider data before activation,
  persist only normalized app-owned provider-reference JSON, and preserve the
  previous last-good snapshot on failure.
- Default tests must use fake/injected responses only. Live smoke checks, if
  ever needed, are explicit/manual and outside the default suite.
- Raw provider payloads, URLs, headers/cookies, provider IDs, exception bodies,
  credentials, prompts, traces, broker/account/private fields, and internal
  endpoint details must not enter API responses, cache JSON, docs examples, or
  tests.

Top-level read: `MarketMoodRead`

- `data_mode: "synthetic" | "provider_reference" | "unavailable"`
- `source_label: str`
- `source_detail_label: str`
- `source_rights_notice: str`
- `generated_at: datetime`
- `updated_at_utc: datetime | None`
- `updated_at_label: str | None`
- `freshness_status: "fresh" | "stale" | "unavailable"`
- `freshness_label: str`
- `is_trading_signal: false`
- `is_actionability_input: false`
- `is_risk_rule_input: false`
- `score: float | None`
- `score_label: str | None`
- `score_min: 0`
- `score_max: 100`
- `rating: "extreme_fear" | "fear" | "neutral" | "greed" | "extreme_greed" | "unknown"`
- `rating_label: str`
- `trend_series: MarketMoodTrendPointRead[]`
- `comparisons: MarketMoodComparisonRead[]`
- `components: MarketMoodComponentRead[]`
- `caveat_codes: str[]`
- `limitations: str[]`
- `status_message: str | None`

`MarketMoodTrendPointRead`:

- `date: YYYY-MM-DD`
- `score: float | None`
- `score_label: str | None`
- `rating`
- `rating_label`

`MarketMoodComparisonRead`:

- `window: "1w" | "1m" | "1y"`
- `prior_score: float | None`
- `prior_score_label: str | None`
- `change_label: str | None`
- `is_available: bool`

`MarketMoodComponentRead`:

- `component_key: str`
- `display_name: str`
- `score: float | None`
- `score_label: str | None`
- `rating`
- `rating_label`

## Detail-Page Contract Extension

The Dashboard compact card can use `MarketMoodRead` as-is. The full detail page
needs an extension before the frontend can build the CNN-style interactive
indicator sections correctly.

Codex C should extend the backend contract in one implementation turn with
provider-neutral, frontend-safe detail fields. The exact class names may be
refined by implementation, but the contract must support:

`MarketMoodIndicatorHistoryPointRead`:

- `date: YYYY-MM-DD`
- `value: float | None`
- `value_label: str | None`
- `score: float | None`
- `score_label: str | None`
- `rating`
- `rating_label`

`MarketMoodIndicatorRead`:

- `component_key: str`
- `display_name: str`
- `subtitle: str`
- `description: str`
- `current_score: float | None`
- `current_score_label: str | None`
- `current_rating`
- `current_rating_label: str`
- `current_value: float | None`
- `current_value_label: str | None`
- `unit_label: str | None`
- `axis_label: str | None`
- `axis_value_format: "number" | "percent" | "ratio" | "index" | "currency" | "spread" | "unknown"`
- `higher_value_meaning: "fear" | "greed" | "neutral_or_contextual" | "unknown"`
- `lower_value_meaning: "fear" | "greed" | "neutral_or_contextual" | "unknown"`
- `history: MarketMoodIndicatorHistoryPointRead[]`

`MarketMoodDetailRead`:

- all safe top-level context needed for the detail page;
- the current overall score/rating and overall trend series;
- `indicators: MarketMoodIndicatorRead[]` containing all seven component
  indicators;
- source/provenance/freshness fields;
- caveat/status fields.

Rules:

- The backend owns all labels, descriptions, raw-value formatting, unit labels,
  and axis hints.
- The frontend may render charts and tooltips, but must not infer units, scale,
  explanation text, or fear/greed direction.
- Synthetic fixtures must remain test/design fixtures only. Runtime product
  reads must not serve synthetic Market Mood values or synthetic component
  histories to the Dashboard card or detail page.
- Provider data must be normalized and app-owned; raw provider payloads, URLs,
  headers, cookies, provider IDs, and exception bodies must not enter the
  response or cache.
- The detail page remains internal-demo context only and must not become a
  trading signal, screener, alert system, actionability input, or LLM/agent
  input by default.

## Cache And Fallback

- Backend fetch/cache only.
- Persist normalized app-owned JSON only at
  `backend/cache/market_mood_snapshot.json`.
- Activate a refreshed snapshot only after parse and validation succeed.
- Preserve active and persisted last-good snapshot on refresh failure.
- Return explicit stale state for stale last-good data.
- Runtime product reads return provider-reference last-good data when available.
- Return unavailable when no valid provider-reference snapshot exists.
- Synthetic fallback is allowed only through explicit test/design injection, not
  as the normal product GET fallback.

## Source-Update Detection Follow-Up

The displayed `updated_at_utc` / `updated_at_label` fields mean the provider or
source data update time. They must not be treated as the user's page-refresh
time or the backend's latest fetch-attempt time.

Backend owns source-update detection:

- compare refreshed provider data using a stable provider/source timestamp when
  available, such as provider `updated_at_utc`, plus normalized snapshot
  equivalence when needed;
- preserve the last-good provider-reference snapshot on refresh failure;
- do not activate a new snapshot if the provider source timestamp and normalized
  data are unchanged, except for safe backend-owned refresh metadata;
- if the UI needs fetch-attempt visibility, expose separate safe fields such as
  `last_checked_at_utc` / `last_checked_at_label` or equivalent status metadata;
- never conflate `last_checked_at` with `updated_at_utc`;
- never expose raw provider payloads, URLs, headers, cookies, provider IDs, raw
  exception bodies, prompts, traces, broker/account data, or secrets.

Frontend may refresh or poll backend-owned state only:

- no frontend-direct CNN/provider call;
- no user-facing `live` or `real-time` wording;
- page refresh/mount may request a backend refresh and then read backend detail;
- optional polling must be against backend state only, must pause/resume safely
  with tab visibility, and must update the page only from backend responses.

## Safety Boundaries

Do not expose:

- raw provider payloads;
- CNN internal URLs;
- headers/cookies;
- provider IDs;
- exception bodies;
- credentials/secrets;
- prompts/traces;
- broker/account/private fields.

Do not add:

- frontend-direct provider calls;
- startup fetch;
- Trade Review actionability integration;
- deterministic risk-rule integration;
- LLM/agent ingestion;
- alerts/notifications;
- market terminal, quote watchlist, or screener behavior;
- advice/recommendation/safe-to-trade/ready-to-trade/guaranteed-return/buy/sell;
- risk-on/risk-off or urgency/execution wording.

## Production Review

P26A-T4 must decide whether this source can be used beyond internal demo. Public
or production use requires founder/source-rights review, replacement with a
licensed source if needed, and final user-facing attribution approval.
