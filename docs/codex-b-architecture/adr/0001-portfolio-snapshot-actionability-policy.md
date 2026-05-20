# ADR 0001: Portfolio Snapshot Actionability Policy

Status: accepted
Date: 2026-05-20
Owner: Codex B - Architecture / Tech Lead

## Context

Portfolio Copilot reviews hypothetical manual trade intents against portfolio snapshots, market quotes, deterministic calculations, and optional agent explanations. Fresh market quotes can make a stale broker snapshot appear current, which would produce confidently wrong cash, collateral, coverage, concentration, assignment, or call-away analysis.

Phase 16 custom agents must not infer readiness from scattered broker and market fields. They need one explicit backend-owned actionability decision that preserves separate broker snapshot freshness and market quote freshness.

## Decision

Add a backend-owned Portfolio Snapshot Actionability Policy before polished Phase 16 agent outputs. The policy classifies the review state for a specific account, portfolio snapshot, market quote snapshot set, and trade intent context.

The policy output must include:

- a single `review_actionability_status` for orchestration and copy gating;
- separate broker snapshot freshness metadata;
- separate market quote freshness metadata;
- structured reasons and severity;
- policy version and evaluation timestamp;
- optional user confirmation state when manual, CSV, synthetic/mock, cached, delayed, or EOD data is intentionally used.

Accepted `review_actionability_status` vocabulary:

- `normal_review`
- `analysis_only`
- `manual_confirmation_required`
- `blocked_stale_broker_snapshot`
- `blocked_stale_market_quote`
- `blocked_unknown_freshness`
- `blocked_provider_error`

`normal_review` is allowed only when broker portfolio snapshot freshness and market quote freshness both satisfy the current policy and no provider error is present. Even in `normal_review`, product language remains read-only manual decision support, not trading advice.

`analysis_only` means deterministic review/report generation may proceed, but output must clearly say the result is scenario analysis based on the available snapshot. It must not imply immediate action readiness.

`manual_confirmation_required` means the backend needs an explicit user confirmation before generating a report from manual, CSV, synthetic/mock, cached, delayed, EOD, or otherwise non-provider-verified inputs. Confirmation does not upgrade the output to `normal_review`; it permits `analysis_only`.

Blocked statuses stop polished reports and agent explanations until the blocking condition is resolved. A blocked response may still return safe metadata and remediation hints.

## Required Inputs

The policy should consume a sanitized internal input object with:

- broker snapshot freshness: status, scope, account snapshot as-of timestamp, last successful sync timestamp, received timestamp, and source category;
- market quote freshness: aggregate status across required stock/ETF/option quotes, quote timestamp range, received timestamp range, data mode, and provider status;
- data source/provenance: `snaptrade`, `manual`, `csv`, or `synthetic_mock`;
- broker sync status/errors: coarse sync status, reauth/consent state, sanitized error category/code, and retryable flag;
- market provider status/errors: coarse provider status, rate-limit/unavailable/error category, and retryable flag;
- timestamp/as-of metadata: evaluation time, policy version, source as-of times, and age calculations used internally;
- optional user confirmation state: confirmation state, confirmation scope, confirmed timestamp, expiration timestamp, and actor user id.

The policy must not require or expose raw holdings, account values, cash balances, provider account ids, broker ids, raw provider payloads, secrets, trade journal entries, or account-specific thresholds.

## Output Contract

The safe read shape should resemble:

```json
{
  "policy_version": "portfolio_actionability_v1",
  "evaluated_at": "2026-05-20T15:00:00Z",
  "review_actionability_status": "analysis_only",
  "can_run_deterministic_review": true,
  "can_run_agent_explanation": true,
  "requires_user_confirmation": false,
  "language_tier": "analysis_only",
  "broker_snapshot": {
    "source": "manual",
    "freshness_scope": "broker_snapshot",
    "freshness_status": "user_provided",
    "sync_status": "not_applicable",
    "as_of": "2026-05-20T14:30:00Z",
    "last_successful_sync_at": null,
    "provider_status": "not_applicable"
  },
  "market_quotes": {
    "freshness_scope": "market_quote",
    "freshness_status": "fresh",
    "data_mode": "live_snapshot",
    "as_of_min": "2026-05-20T14:59:30Z",
    "as_of_max": "2026-05-20T14:59:40Z",
    "provider_status": "available"
  },
  "reasons": [
    {
      "code": "manual_snapshot_confirmed",
      "scope": "broker_snapshot",
      "severity": "warning"
    }
  ],
  "user_confirmation": {
    "state": "confirmed",
    "confirmed_at": "2026-05-20T14:58:00Z",
    "expires_at": "2026-05-20T15:28:00Z"
  }
}
```

Synthetic examples may use placeholder timestamps and symbols, but not real portfolio values.

## Status Precedence

Use deterministic precedence so callers get stable behavior:

1. Provider errors, reauth required, or unavailable required providers -> `blocked_provider_error`.
2. Missing or unknown required provider freshness metadata for SnapTrade or market-provider inputs -> `blocked_unknown_freshness`.
3. Broker snapshot outside policy -> `blocked_stale_broker_snapshot`.
4. Market quotes outside policy -> `blocked_stale_market_quote`.
5. Manual, CSV, synthetic/mock, cached, delayed, or EOD inputs without valid confirmation -> `manual_confirmation_required`.
6. Confirmed non-provider-verified or non-live inputs -> `analysis_only`.
7. Fresh broker snapshot plus fresh/live market quotes -> `normal_review`.

## Persistence

Compute current actionability on demand for dashboard, preflight, and trade-review submission previews.

Persist a policy decision snapshot when a trade review, report, agent run, or agent step is created. The persisted snapshot should include policy version, status, reasons, safe broker freshness metadata, safe market quote freshness metadata, and confirmation metadata. Persisting the decision preserves report auditability even after provider freshness or thresholds change.

Persist user confirmations as auditable metadata with confirmation scope and expiration. Do not persist raw portfolio data or provider payloads in the confirmation record.

Do not persist policy thresholds inside reports or expose account-specific thresholds to frontend, LLMs, TradingAgents, analytics, docs, or tests.

## Consequences

Positive:

- Agents and reports consume one explicit readiness decision.
- Broker freshness and market quote freshness remain visually and structurally separate.
- The top-level field name does not collide with quote-level market-data actionability metadata.
- Frontend work can render safe states without inventing fields.
- Stale data cannot accidentally become normal review language.

Tradeoffs:

- The policy adds a new contract before Phase 16 can continue.
- Some early manual/CSV demos will require confirmation and remain analysis-only.
- Backend tests must cover status precedence and forbidden-field exposure.

## Alternatives Considered

1. Let each agent inspect broker and market freshness independently. Rejected because it duplicates policy logic and increases the chance of inconsistent language.
2. Collapse broker and market freshness into one `freshness_status`. Rejected because it hides the most important safety distinction.
3. Block all manual, CSV, synthetic/mock, delayed, or EOD data. Rejected because early MVP and local demos need analysis-only workflows with explicit confirmation.

## Review Guidance

Architecture and integration reviews should block implementations that:

- collapse broker snapshot freshness and market quote freshness;
- allow stale/unknown/error data to produce `normal_review`;
- treat manual confirmation as proof of live broker state;
- expose provider ids, raw payloads, raw holdings, balances, cash, account values, secrets, or account-specific thresholds;
- let LLMs, TradingAgents, or frontend code infer actionability from raw fields.
