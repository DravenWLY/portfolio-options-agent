# Phase 27C Trade Review And Agent Team Scope Integration Contract

Status: active architecture reference
Owner: Codex B
Related plan: `docs/shared/implementation_plan.md` Phase 27C

## Purpose

Phase 27B stabilized Account Details as the private, backend-owned source for
connected-account labels, opaque account references, broker snapshot freshness,
and selected-account sync. Phase 27C carries that scope model into Trade Review,
reports, and Agent Team readouts.

The product goal is simple: whenever a review or report is generated, the user
must know which account is being used for account-specific feasibility context
and which broader portfolio scope is being used for exposure context.

## Core Rule

Trade feasibility is account-specific. Portfolio exposure awareness can be
broader.

The UI and contracts must keep these two concepts separate:

- `review_account_selection`: the account where the user would manually review
  or place the trade. This is the only scope that can later support
  account-level cash, collateral, coverage, and account-type checks.
- `portfolio_context_selection`: the broader context used for concentration,
  exposure, and data-freshness awareness.

Reports and Agent Team outputs must never silently expand, narrow, or reinterpret
scope. If no review account is selected, account-level feasibility is not
evaluated and must be labeled that way.

## Existing Backend Contract To Consume

The backend already exposes the Phase 27C primitives:

- `TradeReviewPortfolioPreviewRequest.portfolio_context_selection`
- `TradeReviewPortfolioPreviewRequest.review_account_selection`
- `ReviewAccountSelectionRequest`
  - `mode: "unselected" | "selected_account"`
  - `account_reference: str | None`
- `TradeReviewWorkspaceRead.scope_metadata`
- `ReportScopeMetadataRead`
  - `review_account: ReviewAccountRead | None`
  - `portfolio_context_scope: PortfolioScopeRead`
  - `scope_summary_label`
  - `account_level_feasibility_evaluated`
  - `scope_caveat_codes`

The frontend must not invent new scope fields. It should mirror the existing
backend read/request shapes exactly.

## P27C-T1 Frontend Scope Wiring

Owner recommendation: Codex F or Claude A

Scope:

- Fetch Account Details overview for the selected app user using:
  `GET /users/{uid}/account-details`.
- Use `AccountDetailsRead.accounts[]` to populate a `Review account` selector.
- Submit only the opaque `account_reference` through
  `review_account_selection`.
- Keep the existing `portfolio_context_selection` control as a separate
  `Broader portfolio context` section.
- Render returned `scope_metadata` in Trade Review results using backend-owned
  display labels.

Acceptance:

- The form clearly separates `Review account` from `Broader portfolio context`.
- `No review account selected` remains possible and results in
  `review_account_selection.mode="unselected"`.
- A selected account submits:
  `review_account_selection.mode="selected_account"` plus the opaque
  `account_reference`.
- Results show:
  - review account display label when present;
  - account kind label when present;
  - whether account-level feasibility was evaluated;
  - portfolio context scope display label;
  - included/excluded account labels when provided;
  - scope caveat codes when provided.
- Results must not render `account_reference`, `scope_reference`,
  `context_reference`, broker IDs, provider IDs, raw balances, raw positions,
  raw holdings, raw quantities, raw payloads, prompts, traces, or secrets.
- No frontend financial computation.
- No advice, recommendation, buy/sell instruction, order, execution,
  `safe to trade`, or `ready to trade` wording.

## P27C-T2 Report Scope Display

Owner recommendation: Codex C for backend gaps if any, then Codex F or Claude A
for frontend display.

Scope:

- Ensure saved reports carry immutable scope metadata from the review run.
- Report history/detail views must display scope used at generation time.
- Reports must not re-resolve current account state and silently change scope.

Acceptance:

- Report display includes `Scope used`, `Review account`, and
  `Broader exposure context` where available.
- Historical reports remain tied to the original generated scope metadata.

## P27C-T3 Agent Team Scope Banner

Owner recommendation: Claude E for agent evidence boundary, Codex F or Claude A
for frontend display.

Scope:

- Agent Team readouts display the selected review/report scope.
- Agent evidence remains lossy and sanitized.
- Agents may receive safe scope categories, booleans, and caveat codes only
  unless a later Codex B review approves additional fields.

Acceptance:

- Agent Team UI states the review account and context scope using reviewed
  backend labels.
- Agent prompts/evidence do not receive account refs, account labels, cash
  values, holdings, option rows, tax lots, provider IDs, or raw payloads.

## P27C-T4 Account Group And Scope Management

Owner recommendation: Codex A product decision first.

Scope:

- Decide whether private alpha needs account-group creation and default review
  account preferences now, or whether groups remain deferred.

Deferred until product approval:

- account group CRUD;
- include/exclude toggles that persist user preferences;
- default review account per strategy;
- report filtering by account group.

## Full-Stack Preview Requirement

P27C work touches connected-account data. Frontend agents must use the full-stack
preview path from `docs/shared/agent_workflows.md`, not `.claude/launch.json`
alone.

Minimum smoke:

- Start Postgres, backend, and frontend together.
- Confirm:
  - `http://localhost:8000/health` returns 200;
  - backend `/users` returns the local dev user;
  - frontend proxy `/api/users` returns the same user;
  - `/trade-review` shows the review-account selector with connected accounts.
- Generate one portfolio-backed preview with a selected review account.
- Confirm result scope metadata displays labels, not opaque refs.
- Stop preview ports only after verification is complete.

## Review Gates

Codex B review:

- request/response contract fidelity;
- privacy boundary;
- no raw refs/IDs/payloads in rendered UI;
- no financial computation;
- no advice/execution wording.

Claude B or Codex F visual review:

- selector is understandable;
- result scope panel is compact and not noisy;
- labels do not overflow at 1024/1280/1440 light and dark;
- no unnecessary repeated disclaimers.

## Rollback

Frontend-only P27C-T1 can be rolled back by removing:

- Account Details overview fetch from Trade Review page;
- review-account selector;
- `review_account_selection` field from submitted portfolio preview payload;
- `scope_metadata` rendering in Trade Review results;
- added TypeScript mirrors if no longer consumed.

Backend contracts should remain in place because they are already part of the
reviewed P27A/P27B scope model.
