# Phase 27A Account Details Selected Account Contract

Status: active architecture reference
Owner: Codex B
Related plan: `docs/shared/implementation_plan.md` Phase 27A / P27A-T8

Phase 27B update: this contract remains useful as a private selected-account
detail shape, but it is not sufficient for normal v1 product display until
latest-sync membership is stable. See
`docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`.
Account Details v1 should be a broker-data readiness page, not an authoritative
holdings mirror.

## Purpose

Account Details should become the user's private account workspace. It should
help the user inspect one connected account at a time, understand what SnapTrade
or another source has synced, and choose the review account for portfolio-aware
Trade Review.

This is not a broker dashboard or trading terminal. It must not include order
placement, order cancellation, account transfer, broker destructive action,
execution controls, advice, recommendations, or agent commentary.

## SnapTrade Data Discussion

SnapTrade can provide several categories of account data:

- Account detail: institution/account metadata, account category/type, sync
  status, holdings sync timestamps, and total market value.
- Balances: cash holdings and buying power, sometimes across multiple
  currencies.
- Positions: current holdings excluding cash, including stocks, ETFs, ADRs,
  mutual funds, closed-end funds, crypto, futures, and option positions when
  supported by the broker/source.
- Option positions: option-specific fields such as OCC ticker, put/call,
  strike, expiration, mini-option flag, and underlying symbol.
- Orders and activities: broker order records and transaction/activity history.
- Tax lots: documented but not generally enabled by default and not suitable
  for the first Account Details version.

The old all-user holdings endpoint is deprecated and should not be the product
foundation. Use account-specific provider sync paths and normalized app-owned
storage.

## Product Decision: What To Show

First selected-account detail view should show:

- selected account identity:
  - backend-owned display label;
  - account kind label;
  - source label;
  - connection status label;
  - last successful sync label;
- overview labels:
  - total value label;
  - cash label;
  - stock/ETF exposure label;
  - options exposure label;
  - collateral/cash usage label;
  - cash state label;
- freshness:
  - broker snapshot freshness;
  - market quote freshness;
  - separate source/as-of labels;
- stock/ETF/fund position display rows:
  - symbol label;
  - instrument name label when available;
  - asset class label;
  - quantity label;
  - market value label;
  - cost basis label only if normalized and safe;
  - as-of/freshness label;
- option position display rows:
  - underlying symbol label;
  - contract label or OCC label;
  - call/put label;
  - strike label;
  - expiration label;
  - side label;
  - quantity/contracts label;
  - market value label;
  - as-of/freshness label;
- cash/balance display rows:
  - currency label;
  - cash amount label;
  - buying power label only if normalized and explicitly available;
  - cash-state/freshness labels.

All monetary, quantity, and date values must be backend-owned display labels.
The frontend may sort/filter display rows but must not compute account values,
collateral, buying power, P/L, coverage, or feasibility.

## Deferred From First Version

- order history;
- transaction/activity history;
- tax lots;
- raw broker account profile fields;
- broker account numbers;
- provider account IDs;
- SnapTrade IDs;
- raw provider payloads;
- performance/P&L charts;
- execution/order controls;
- account transfer or disconnect/delete flows;
- agent commentary or LLM ingestion.

## Contract Shape

Endpoint:

- `GET /users/{uid}/account-details/{account_reference}`

Rules:

- `account_reference` must be an opaque app-owned `acctref_...` value returned
  by `GET /users/{uid}/account-details`.
- Backend resolves it only against accounts owned by `{uid}`.
- Unknown, malformed, or cross-user references return a safe unavailable/not
  found response without revealing whether the account exists elsewhere.
- The endpoint reads normalized app-owned rows only. It does not call SnapTrade
  directly.

Top-level read:

- `data_mode: "private_real_source" | "unavailable"`
- `generated_at`
- `account_reference`
- `display_label`
- `account_kind_label`
- `source_kind`
- `source_label`
- `connection_status_label`
- `last_successful_sync_label`
- `privacy_display_mode`
- `broker_snapshot_freshness`
- `market_quote_freshness`
- `summary_labels`
- `cash_rows`
- `equity_position_rows`
- `option_position_rows`
- `caveat_codes`
- `limitations`

Suggested row types:

- `AccountCashDisplayRowRead`
- `AccountEquityPositionDisplayRowRead`
- `AccountOptionPositionDisplayRowRead`

Each row should use display labels and app-owned row references only. Do not
return raw database IDs, provider IDs, raw account numbers, or raw provider
payload fields.

## Privacy Boundary

Allowed for private Account Details UI:

- backend-owned account display labels;
- opaque app-owned account/row references;
- symbols and instrument labels;
- backend-formatted quantity labels;
- backend-formatted amount labels;
- backend-formatted option contract labels;
- freshness/source/caveat labels.

Forbidden in frontend contracts:

- provider account IDs;
- broker account IDs;
- SnapTrade IDs;
- account numbers, even masked;
- raw provider payloads;
- raw broker account display names or user nicknames;
- raw balances, raw buying power, raw account values;
- raw position objects;
- tax lots;
- orders or activities;
- transaction history;
- prompts, LLM traces, provider traces, secrets, API keys, tokens.

Forbidden in Agent Team evidence:

- all account display labels;
- all account refs;
- all position rows;
- all balances and amounts;
- all raw/provider/private identifiers.

Agent Team may receive only lossy scope metadata already approved in P27A:
scope mode, selected-context presence, included/excluded counts,
review-account-present boolean, account-level-feasibility flag, and caveat
codes.

## Tests Required

Backend tests should cover:

- valid `acctref_...` resolves only for the route user;
- cross-user `acctref_...` fails closed and does not leak labels or refs;
- malformed/private-looking refs are rejected or unavailable-labelled safely;
- position display rows contain no raw IDs/provider payloads/account numbers;
- frontend-safe payload validation rejects forbidden keys;
- agent-safe evidence projection still excludes labels, refs, positions, and
  balances;
- missing normalized position data produces empty row arrays, not fabricated
  rows;
- options rows do not expose SnapTrade option symbol IDs or provider contract
  IDs;
- cash/buying-power labels are omitted or hidden when not normalized.

## References

- SnapTrade account data: https://docs.snaptrade.com/docs/account-data
- SnapTrade account detail: https://docs.snaptrade.com/reference/Account%20Information/AccountInformation_getUserAccountDetails
- SnapTrade account positions: https://docs.snaptrade.com/reference/Account%20Information/AccountInformation_getAllAccountPositions
- SnapTrade option positions: https://docs.snaptrade.com/reference/Options/Options_listOptionHoldings
