# Codex C Handoff: P16-T0 Portfolio Snapshot Actionability Policy

Status: ready for backend implementation
Owner: Codex C - Backend Implementation
Review owner: Codex B - Architecture / Tech Lead
Last updated: 2026-05-20

## Task Name

`P16-T0` - Portfolio Snapshot Actionability Policy

## Goal

Implement the smallest backend contract/service that classifies trade-review readiness from separate broker snapshot freshness and market quote freshness before Phase 16A deterministic agent components continue.

The service should return one explicit `review_actionability_status` plus separate `broker_snapshot` and `market_quotes` metadata. Agents, reports, and the future frontend should consume this policy instead of inferring readiness from scattered fields.

## Non-Goals

- No frontend implementation.
- No broker sync rewrite.
- No market-data provider rewrite.
- No TradingAgents integration.
- No LLM-generated financial metrics.
- No order tickets, broker actions, automatic trading, broker disconnect/delete, or execution affordances.
- No broad report schema redesign beyond safe policy snapshots.

## Architecture References

- `docs/codex-b-architecture/adr/0001-portfolio-snapshot-actionability-policy.md`
- `docs/codex-b-architecture/architecture.md`, Section K2
- `docs/shared/implementation_plan.md`, `P16-T0`
- `docs/shared/current_roadmap.md`
- `AGENTS.md`

## Files Likely To Change

- `backend/app/schemas/actionability.py` or an existing equivalent schema module.
- `backend/app/services/trade_review/actionability.py` or an existing equivalent trade-review service module.
- `backend/tests/services/trade_review/test_actionability.py`.
- Optional: `backend/app/api/routes/trade_reviews.py` only if a small preflight route already matches existing patterns.
- `docs/shared/implementation_plan.md` for verification notes after implementation.

## Required Inputs

The service should accept sanitized internal inputs for:

- broker snapshot freshness: status, source as-of timestamp, received timestamp, last successful sync timestamp, sync status, and source category;
- market quote freshness: aggregate required quote status, quote timestamp range, received timestamp range, data mode, and provider status;
- source/provenance: `snaptrade`, `manual`, `csv`, or `synthetic_mock`;
- broker sync status/errors: sanitized category/code and retryable flag;
- market provider status/errors: sanitized category/code and retryable flag;
- timestamp metadata: policy evaluation time, policy version, source as-of times, and internally computed ages;
- optional user confirmation state: state, scope, confirmed timestamp, expiration timestamp, and actor user id.

## Accepted Vocabulary

`review_actionability_status` values:

- `normal_review`
- `analysis_only`
- `manual_confirmation_required`
- `blocked_stale_broker_snapshot`
- `blocked_stale_market_quote`
- `blocked_unknown_freshness`
- `blocked_provider_error`

Source/provenance values:

- `snaptrade`
- `manual`
- `csv`
- `synthetic_mock`

Freshness scopes:

- `broker_snapshot`
- `market_quote`

Do not reuse or overwrite quote-level market-data actionability fields. This policy is the review-level gate.

## Status Rules

Use deterministic precedence:

1. Provider errors, reauth required, or unavailable required providers -> `blocked_provider_error`.
2. Missing or unknown required provider freshness metadata for SnapTrade or market-provider inputs -> `blocked_unknown_freshness`.
3. Broker snapshot outside policy -> `blocked_stale_broker_snapshot`.
4. Market quotes outside policy -> `blocked_stale_market_quote`.
5. Manual, CSV, synthetic/mock, cached, delayed, or EOD inputs without valid confirmation -> `manual_confirmation_required`.
6. Confirmed non-provider-verified or non-live inputs -> `analysis_only`.
7. Fresh broker snapshot plus fresh/live market quotes -> `normal_review`.

Manual confirmation must not upgrade anything to `normal_review`.

## Safety Boundaries

Do not expose or send to frontend, LLMs, TradingAgents, analytics, docs, tests, logs, or report text:

- raw holdings;
- account values;
- cash balances or buying power;
- broker account ids or provider account ids;
- provider connection ids;
- raw provider payloads;
- secrets, portal URLs, access tokens, or API keys;
- trade journal entries;
- account-specific thresholds or private strategy settings.

Use synthetic examples only.

## Tests Required

Add synthetic tests for:

- each accepted `review_actionability_status`;
- status precedence when multiple problems are present;
- broker stale with market fresh -> broker blocked, not normal;
- broker fresh with market stale -> market blocked, not normal;
- manual/CSV/synthetic/mock unconfirmed -> `manual_confirmation_required`;
- manual/CSV/synthetic/mock confirmed -> `analysis_only`, not `normal_review`;
- provider error precedence;
- unknown freshness precedence;
- safe output shape forbids raw holdings, balances, cash, provider ids, raw payloads, secrets, trade journal entries, and account-specific thresholds.

Run:

```bash
cd backend && ./.venv/bin/python -m pytest backend/tests/services/trade_review/test_actionability.py
cd backend && ./.venv/bin/python -m pytest
```

## Open Questions

- Exact time thresholds should be implementation constants/config, but they must not be exposed in safe read schemas or docs as account-specific values.
- Whether to add an API preflight route in the first slice depends on current route shape. Service/schema-only is acceptable for `P16-T0`.
- If an existing persisted trade-review model already has a freshness snapshot field, reuse it for the policy decision snapshot instead of adding persistence.

## Recommendation

PASS for Codex C to implement `P16-T0` as the next backend gate.

BLOCKED for continuing polished Phase 16A agent outputs until this policy exists and tests pass.
