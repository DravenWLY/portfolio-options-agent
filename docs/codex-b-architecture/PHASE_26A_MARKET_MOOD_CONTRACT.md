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
- show latest available timestamp plus stale/unavailable state;
- show: "Broad market sentiment context only. Not a trading signal.";
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
- show a 1-year trend graph for the overall index;
- show component summary bars and explanation text;
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

## Cache And Fallback

- Backend fetch/cache only.
- Persist normalized app-owned JSON only at
  `backend/cache/market_mood_snapshot.json`.
- Activate a refreshed snapshot only after parse and validation succeed.
- Preserve active and persisted last-good snapshot on refresh failure.
- Return explicit stale state for stale last-good data.
- Return unavailable or synthetic fallback when no valid snapshot exists.

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
