# Phase 20D Dashboard Account-Detail Display Contract

Status: architecture contract for next backend slice  
Owner: Codex B - Architecture / Systems / Integration  
Date: 2026-05-26  
Related plan task: `P20D-T1`

## Decision

Portfolio Copilot may eventually show private authenticated Dashboard
account-detail labels, but only through backend-owned, display-ready strings
with explicit freshness, provenance, and privacy state.

The Dashboard remains a compact risk-and-review cockpit. Account details may
support the review-readiness job, but they must not turn the first viewport
into a broker dashboard, quote terminal, options screener, market-data viewer,
or recommendation feed.

Codex A's 2026-05-29 Stock Rover/Product B pressure-test decision reinforces
this boundary: Portfolio Copilot complements serious research and portfolio
tools instead of replacing them. Real-source account summary plus broker
freshness should land before persisted review history, and plausible synthetic
headline dollar values should be hidden or replaced with unmistakable
non-real placeholders in the normal cockpit.

## Contract Posture

Revise the existing `DashboardAccountSummaryRead` / 
`GET /users/{uid}/dashboard-account-summary` contract rather than creating a
parallel endpoint.

Reasons:

- The existing endpoint already represents the account-summary Dashboard
  surface and is consumed by the current frontend.
- A duplicate endpoint would create competing sources of truth for the same
  panel.
- The current contract can evolve in a backward-compatible way by adding
  provenance and privacy fields while preserving existing display labels.

If Codex C finds that the existing contract cannot be evolved without
misleading semantics, Codex C should stop and propose a narrowly named
successor schema before adding code.

## Allowed Display Fields

The contract may expose only backend-formatted display fields and safe
metadata. Candidate fields are:

- `data_mode`: source mode for the Dashboard account summary, such as
  `synthetic_demo`, `private_real_source`, or `unavailable`.
- `demo_notice`: required when synthetic/demo data is emitted.
- `generated_at`: backend-generated timestamp for the read response.
- `summary_reference`: opaque app-owned reference that does not encode broker,
  account, provider, or CSV identifiers.
- `display_scope`: `selected_context`, `selected_account`, `combined_portfolio`,
  `manual_csv`, `synthetic_demo`, or `unavailable`.
- `source_label`: user-readable backend-owned scope label.
- `valuation_basis`: `market_value`, `book_value`, `mixed`, `indicative`,
  `delayed`, or `unavailable`.
- `broker_snapshot_freshness`: separate broker snapshot freshness object with
  `freshness_scope="broker_snapshot"`.
- `market_quote_freshness`: separate market quote freshness object when any
  market-derived value is displayed.
- `market_data_mode`: `synthetic`, `indicative`, `delayed`, `unavailable`, or
  later approved `live`; do not emit or claim `live` until provider licensing
  and display rights are approved.
- `total_value_label`: backend-formatted total portfolio/account value label,
  or a backend-owned hidden/unavailable label.
- `cash_label`: backend-formatted cash/liquidity label, or a hidden/unavailable
  label.
- `cash_state_label`: categorical cash posture label.
- `stock_etf_exposure_label`: backend-formatted stock/ETF exposure label.
- `options_exposure_label`: backend-formatted options exposure label.
- `collateral_usage_label`: backend-formatted collateral/cash-usage state
  where applicable.
- `portfolio_shape_label`: backend-formatted portfolio-shape summary.
- `position_count_label`: backend-formatted count summary.
- `portfolio_shape`: existing safe counts only, if still useful.
- `caveat_codes`: machine-readable caveats for stale, unavailable, delayed,
  indicative, synthetic, hidden, or partial data.
- `privacy_display_mode`: `amounts_visible` or `amounts_hidden`.
- `display_sections`: backend-owned grouping metadata for the Dashboard card.

Codex C may refine exact enum names during implementation, but tests must make
the semantics explicit and prevent `persisted` or `indicative` from being
misread as current licensed market truth.

## Forbidden Fields

The account-detail contract must not expose:

- raw holdings;
- raw positions;
- quantities, lots, tax lots, or contract counts beyond approved aggregate
  display labels/count labels;
- raw cash balances;
- raw buying power;
- raw account values beyond approved display labels;
- exact allocation vectors unless transformed into backend-owned display
  labels and approved in the task;
- account ids, broker ids, provider ids, or provider account ids;
- raw CSV rows;
- raw provider payloads;
- account-specific thresholds;
- prompts, LLM responses, LLM traces, provider traces, or raw agent context
  envelopes;
- credentials, secret references, API keys, access tokens, or entitlement
  metadata;
- execution, recommendation, guaranteed-return, `safe to trade`, or
  `ready to trade` wording.

## Privacy Display Mode

The safest default for real-source private account details is
`privacy_display_mode="amounts_hidden"` until the frontend has an explicit
reviewed toggle.

When amounts are hidden:

- raw numeric values still must not be returned;
- amount labels should be omitted or replaced with backend-owned hidden labels
  such as `Hidden` / `Amounts hidden`;
- categorical fields such as cash state, position count, freshness, and caveats
  may remain visible when safe.

When amounts are visible:

- the backend still owns every calculation and formatted label;
- the frontend renders labels verbatim and performs only presentational
  layout;
- the response must include provenance, valuation basis, freshness, data mode,
  and caveats sufficient for the user to understand limitations.

Synthetic/demo account values should be hidden by default in normal product
view or shown only behind an explicit example/demo state. Demo labels must not
look like real account data.

## Freshness And Provenance

Every response must preserve separate provenance concepts:

- broker portfolio snapshot freshness;
- market quote freshness when market-derived labels are used;
- market-data mode and valuation basis;
- display scope and source label;
- safe as-of timestamp or as-of label;
- caveats for stale, unavailable, delayed, indicative, synthetic, hidden, or
  partial values.

Broker snapshot freshness and market quote freshness must never be collapsed
into a generic readiness value. Market-derived labels must not be displayed as
current quote truth unless a future provider, licensing, and display-rights
decision explicitly permits it.

## Scope Recommendation

The first real-source implementation should default to a selected context or
selected account scope, not silent aggregation.

`combined_portfolio` may be supported by the enum and emitted only when the
backend can prove the aggregation scope, source freshness, and caveats are
clear and safe. Trade Review should continue to make selected context explicit.

This keeps the first backend slice honest while leaving room for a later
combined portfolio summary once aggregation semantics are reviewed.

## Agent And LLM Boundary

Dashboard account-detail labels are private user-facing display fields. They
must not be sent to LLMs, TradingAgents, agent-team prompts, or agent evidence
packages by default.

Allowed agent inputs remain separately approved agent-safe projections, such
as categorical actionability, freshness status, caveat codes, sanitized
deterministic review summaries, and safe portfolio-shape summaries.

Do not send by default:

- total value labels;
- cash labels;
- buying-power labels;
- raw holdings or positions;
- quantities;
- account/provider identifiers;
- provider payloads;
- account-specific thresholds.

Any future use of account-detail data in agent prompts requires a separate PM
decision, privacy review, and prompt-safety tests.

## Frontend And Design Boundary

Claude A may visually reserve space for the reviewed account-summary panel
using existing fields, but may not invent account values or unsupported
fields.

Claude Design may explore hierarchy only after the allowed content model is
documented. It must not invent broker fields, fake real account values, order
controls, quote-terminal widgets, recommendation language, or unreviewed
market-data claims.

## P20D-T1 Acceptance Shape

Codex C should implement or refine the backend contract with synthetic tests
first. Acceptance requires:

- display-label-only account values;
- explicit privacy mode;
- selected-scope default or clearly labelled combined scope;
- broker freshness and market freshness separation;
- valuation basis and market-data mode;
- forbidden-field and forbidden-wording tests;
- no frontend changes;
- no LLM/agent prompt changes;
- no market-provider call or broker execution behavior.
