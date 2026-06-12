# Implementation Plan

This file is the active coordination index for Portfolio Copilot work. It should stay short.

Detailed historical task notes were archived on 2026-06-03:

- `docs/shared/implementation_plan_archive_2026-06-03.md`
- `docs/shared/completed_phases_log.md`
- `docs/shared/CHANGELOG.md`

Use this file for current owner routing, active phases, and the next implementation handoff. Put long verification transcripts, review checklists, and completed task detail in the archive or changelog instead of expanding this file again.

## Working Rules

- Backend contracts and deterministic services own financial calculations, display labels, actionability policy, freshness, provenance, and privacy boundaries.
- Frontend renders reviewed backend fields verbatim and may only add presentational formatting.
- No automatic trading, order placement, order cancellation, broker scraping, credential storage, MFA bypass, advice wording, guaranteed-return wording, or safe/ready-to-trade wording.
- Do not expose raw holdings, raw positions, quantities, cash balances, buying power, account values, account/provider/broker IDs, raw provider payloads, prompts, provider traces, or LLM traces in frontend or agent prompts by default.
- No `.env`, secrets, real brokerage data, local DB contents, broker exports, generated reports, screenshots, logs, or `../TradingAgents` edits during ordinary implementation/review.
- Phase 21A realtime Agent Console remains paused. The disabled Agent Console composer remains disabled.
- Market/news/agent data may enter LLM or agent paths only through separately approved sanitized evidence contracts.

## Owner Map

- Codex A: PM / product approval.
- Codex B: architecture, privacy, safety, contract review.
- Codex C: backend implementation, except the agentic AI workflow.
- Claude A: frontend implementation.
- Claude B: frontend/privacy/safety review.
- Claude E: agentic AI system design and implementation.
- Codex D: DevOps, build, deployment, CI/CD.

## Active Work

### Phase 27B - Account Details Stability And Broker Snapshot Semantics

Status: P27B-T0 done; P27B-T1 done; P27B-T2 done; P27B-T3 done; P27B-T4 done; P27B-T5 done; P27B-T6 done; P27B-T7 done; P27B-T8 done; P27B-T9 done; P27B-T10 done; P27B-T11 done; P27B-T12 done; P27B-T13 done; P27B-T14 done; P27B-T16 done; P27B-T16A done; P27B-T17 done; P27B-T18 done; P27B-T19 done; P27B-T20 done; P27B-T21 done; P27B-T22 done.

Architecture reference:

- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`

Purpose:

- Reframe Account Details v1 as a broker-data readiness page, not a holdings mirror.
- Stabilize latest-sync membership before real broker position rows are treated as current holdings.
- Keep deterministic review and Agent Team evidence caveated until current-position truth is proven.

Product rule:

- A position is current only if it belongs to the latest successful sync snapshot/batch for that account, or is explicitly current in a reviewed manual/CSV snapshot.
- Missing-from-latest rows are not current.
- Expired options must never appear in a current positions section.

Tasks:

- P27B-T0 - Account Details data policy and contract freeze: done.
  - Owner: Codex B.
  - Write the stability contract covering Account Details v1 allowed/hidden fields, latest-sync membership semantics, deterministic review gates, and Agent Team evidence boundaries.
  - Acceptance: Codex C can implement membership work without guessing UI/product policy; P27A selected-position rows are explicitly not product-authoritative until P27B membership is complete.

- P27B-T1 - Latest sync membership foundation: done.
  - Owner: Codex C.
  - Add `sync_run_id`, `snapshot_id`, or equivalent membership identity to normalized cash/equity/option rows, or implement an equivalent current-snapshot membership model.
  - Repeated syncs where positions disappear must not leave those rows as current.
  - Tests: disappearing stock, disappearing option, repeated sync, missing-from-latest classification, forbidden fields.
  - Implementation: added nullable `sync_run_id` membership to normalized `cash_balances`, `stock_positions`, and `option_positions` with Alembic migration `0017_add_sync_membership_to_normalized_rows.py`. Broker sync now tags normalized cash/equity/option rows with the current `BrokerSyncRun.id`. Account Details summary and selected-account detail now use only rows tied to the latest successful or partially successful sync run for the account; historical rows remain stored but are not counted/rendered as current.
  - Verification: focused Account Details/Trade Review/Agent evidence/sync tests passed with DB-backed membership regressions skipped by the destructive-DB safety gate (`102 passed, 7 skipped`). Broker sync/normalization tests passed with DB-backed tests skipped by the same gate (`1 passed, 10 skipped`). `git diff --check` clean.
  - Codex B review PASS. Review note: disappearing-stock/disappearing-option repeated-sync regression coverage is present in `tests/services/test_sync_to_normalization_integration.py` but requires an explicitly safe disposable test DB to execute. One privacy test assertion should be narrowed later because random opaque refs can contain test sentinel digits by chance.

- P27B-T2 - Option current/expired/closed semantics: done.
  - Owner: Codex C.
  - Stop treating every normalized option position as `open`; expired and absent-from-latest options must not appear as current.
  - Implementation: option normalization now classifies options as `open`, `expired`, or `closed` instead of unconditionally `open` (`expired` when OCC expiration is before the app date; `closed` for non-positive quantity). Selected-account option rows and option exposure metrics now require both latest-successful-sync membership and non-expired open contract semantics. Expired latest-sync rows and older cached rows remain stored but are not rendered/counted as current Account Details option exposure.
  - Verification: focused sync/Account Details/Trade Review/Agent evidence/option normalization tests passed with DB-backed integration regressions skipped by the destructive-DB safety gate (`105 passed, 9 skipped`). Agent Team/agent eval tests passed (`208 passed, 2 deselected`). `git diff --check` clean.
  - Codex B review PASS. Review note: DB-backed tests include expired-latest-sync, older-expired/cached, missing-after-repeated-sync, and current-future-option cases, but they require an explicitly safe disposable test DB to execute.

- P27B-T3 - Account Details v1 backend read contract: done.
  - Owner: Codex C.
  - Refine Account Details into broker-readiness output: account/source/sync/freshness/cash labels and readable caveats. Suppress row-level holdings/options in normal v1 unless backend marks membership-safe.
  - Implementation: added backend-owned `readiness_caveats` objects to Account Details overview and per-account rows while preserving compatibility `caveat_codes`. Overview responses now expose display-ready broker/cash/sync caveats for broker-reported cash, incomplete buying-power/free-cash/collateral modeling, temporarily limited position details, possible stale local row history, current-position review caveats, and separate broker/market freshness. Normal `GET /users/{uid}/account-details` remains an overview/readiness contract and does not expose selected-account `cash_rows`, `equity_position_rows`, or `option_position_rows`.
  - Verification: Account Details/Trade Review/Agent evidence tests passed (`102 passed, 5 skipped`; skips require an explicitly safe disposable test DB). Agent Team/agent eval regression passed (`208 passed, 2 deselected`). `git diff --check` clean.
  - Blocker fix 2026-06-06: normal Account Details overview now uses overview-specific private labels so real normalized metrics do not mirror visible total value, stock/ETF exposure, options exposure, or collateral dollar labels. Cash may still render as a backend-owned broker-reported label with `some_amounts_hidden` and readiness caveats. Selected-account detail remains separate. Verification repeated: `102 passed, 5 skipped`; `208 passed, 2 deselected`; `git diff --check` clean.
  - Codex B review PASS after blocker fix.

- P27B-T4 - Deterministic trade-review gating: done.
  - Owner: Codex C.
  - Position-dependent real-broker flows must downgrade or block when current holdings, option positions, or collateral are not verified.
  - Implementation: added a deterministic real-broker position-truth gate in the workspace builder. Real broker review-account resolution still echoes a selected account, but it no longer marks that account as the account-level feasibility source. Position-dependent real-broker flows (`stock_sell_trim`, `etf_sell_trim`, `covered_call`, `cash_secured_put`) append explicit `current_position_truth_unstable` and `account_level_feasibility_not_evaluated` reasons/caveats; otherwise-normal reviews are downgraded to `analysis_only`, while existing manual-confirmation or blocked states are preserved. Covered-call and CSP flows add explicit unverified coverage/collateral caveats and keep broker snapshot freshness separate from market quote freshness.
  - Verification: Account Details/Trade Review/Agent evidence tests passed (`104 passed, 5 skipped`; skips require an explicitly safe disposable test DB). Agent Team/agent eval regression passed (`208 passed, 2 deselected`). `git diff --check` clean.
  - Codex B review PASS.

- P27B-T5 - Agent Team evidence boundary update: done.
  - Owner: Claude E.
  - Allow only freshness, scope mode, broad buckets, caveat codes, actionability status, and deterministic categories. Block account labels, refs, cash values, holdings, quantities, and option contracts by default.
  - Codex B review PASS. Evidence remains lossy and receives caveated counts/statuses/codes only.

- P27B-T6 - Account Details frontend v1 redesign: done.
  - Owner: Codex F or Claude A.
  - Redesign `/account-details` as broker-data readiness: account rail, selected account status, sync/freshness, cash summary, compact caveats. Hide holdings/options in normal v1 unless backend says safe.
  - Codex B review PASS. Current layout is accepted; future polish should focus on the selected-detail panel only.

- P27B-T7 - Account Details selected-detail label cleanup and option multiplier correctness: done.
  - Owner: Codex C plus Codex F.
  - Implementation: selected-account detail row labels now use backend-owned value-only table cells for cash, equity market value, and cost basis while leaving instrument names null unless safe normalized names exist. Option row market value now computes from option market price, absolute quantity, and OCC multiplier with short-side negative signing; selected-account option exposure summary uses the same multiplier-aware calculation. Summary labels remain backend-owned and descriptive; row freshness/as-of/caveat metadata remains available for technical disclosure but the display rows no longer require frontend string trimming.
  - Verification: Account Details/Trade Review/Agent evidence tests passed (`108 passed, 5 skipped`; skips require an explicitly safe disposable test DB). `git diff --check` clean.
  - Blocker fix 2026-06-06: real SnapTrade option mapping now stores signed total contract market value with multiplier 100 in the provider-normalized path, not only in hand-built `market_price` test rows. Verification repeated: `103 passed, 8 skipped`; `git diff --check` clean.
  - Codex B review PASS after blocker fix.

- P27B-T8 - Account Details selected-detail panel UI cleanup: done.
  - Owner: Codex F.
  - Redesign only the selected-account detail panel. Remove repeated freshness/as-of/caveat table noise; hide empty Instrument/Cost Basis columns; collapse raw caveat codes into technical disclosure; render backend display labels verbatim with exact legacy `Market value` prefix cleanup only.
  - Verification: Codex F ran frontend typecheck, lint, build, `git diff --check`, and browser smoke. Codex B review PASS for contract/privacy/safety.

- P27B-T9 - Buying power and collateral policy: done.
  - Owner: Codex B with Codex C.
  - Decision: broker-reported cash, available cash, buying power, currency, and balance-source labels may be displayed privately on Account Details, but they are display-only for deterministic feasibility in private alpha. Buying power is not cash and must not be treated as CSP collateral. Real-broker CSP and covered-call flows stay caveated/downgraded until later broker/account-type collateral and same-account coverage models are explicitly approved and tested. Agent Team evidence may receive caveat/status codes only, never display cash/buying-power values or account identifiers.
  - Architecture reference updated in `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`.

- P27B-T10 - SnapTrade data availability, tax-lot feasibility, and Account Details enrichment contract: done.
  - Owner: Codex C; review by Codex B.
  - Audit what SnapTrade account, balance, unified position, option-position, tax-lot, activity, and order-adjacent read data is available versus what Portfolio Copilot currently normalizes and exposes.
  - Produce a gap table against a brokerage-style positions page: symbol/name, asset class, quantity, last price, current value, average cost basis, cost basis total, day gain/loss, total gain/loss, percent of account, 52-week range, option contract terms, option last price, signed option market value, cash/buying-power fields, and expandable purchase-lot history.
  - Classify each candidate field as SnapTrade-provided, backend-derived from broker fields, market-quote-provider required, unavailable, unsafe, or deferred.
  - Treat broker-reported tax lots as optional private display data when available. Do not reconstruct tax lots from activities/transactions in this phase. Transaction/activity data remains analysis input for a later reviewed tax/history contract, not normal Account Details v1 display.
  - Propose a backend-owned selected-account detail read contract with display labels only, including optional paginated tax-lot rows behind an expanded position detail. Tax-lot row identifiers must be opaque app-owned refs if exposed at all.
  - Keep all tax language descriptive only: tax-lot awareness, holding-period context, broker-reported cost basis. No tax advice, tax optimization recommendation, or agent prompt ingestion by default.
  - No raw account IDs, provider IDs, raw balances, raw holdings, raw quantities, raw tax-lot IDs, transactions, orders, provider payloads, prompts, traces, or frontend financial math.
  - Acceptance: Account Details enrichment work can proceed from confirmed provider capabilities instead of guessed UI columns; frontend redesign waits for Codex B approval of the enriched contract.
  - Codex B decision 2026-06-06: proposal PASS with constraints. Selected-account detail may add nullable backend-owned display labels for `last_price_label`, `average_cost_label`, `cost_basis_label`, `total_gain_loss_label`, `gain_loss_percent_label`, and `valuation_source_label`. `account_weight_label` stays deferred until a denominator policy is defined and tested. SnapTrade broker-reported `price`, `average_purchase_price`, and `open_pnl` may be displayed privately with source/freshness caveats. Tax lots should be a separate expanded selected-position contract with optional paginated rows and opaque app-owned `lotref_...` refs only. Raw SnapTrade lot IDs, account IDs, provider IDs, payloads, transactions, and orders remain excluded. No Agent Team evidence widening and no deterministic trade-review feasibility use.
  - Codex C implementation 2026-06-06: added selected-account enrichment fields only; overview remains broker-readiness. SnapTrade provider snapshots/normalization now retain broker-reported price, average purchase price, open P/L, currency, mini-option multiplier, buying power, available cash, and sanitized tax-lot display data. Selected-account rows expose nullable backend-owned labels and opaque `lotref_...` tax-lot rows. Verification: focused SnapTrade/selected-detail suite -> 103 passed, 16 skipped; `pytest tests/api/test_trade_review_workspace.py tests/services/trade_review/test_frontend_read.py tests/services/agent_team/test_evidence_projection.py -q` -> 108 passed, 5 skipped; `pytest tests/services/agent_team/ tests/services/agent_eval -q` -> 211 passed, 2 deselected; `git diff --check` -> clean.
  - Codex C blocker fix 2026-06-06: option selected-account `cost_basis_label` now applies the option contract multiplier consistently with market value (`$2.00` average price x 1 standard contract x 100 -> `$200.00`; mini-options use multiplier 10). Selected-account limitations now state normalized broker-reported tax-lot display rows may be shown when available while raw lot IDs, raw provider payloads, transactions, and orders remain excluded. Verification: `pytest tests/services/trade_review/test_frontend_read.py tests/api/test_trade_review_workspace.py -q` -> 101 passed, 5 skipped; `pytest tests/services/agent_team/ tests/services/agent_eval -q` -> 211 passed, 2 deselected.

- P27B-T11 - Account Details selected-detail enriched UI cleanup: done.
  - Owner: Codex F; review by Codex B.
  - Frontend selected-account detail panel now consumes the P27B-T10 enriched backend labels, shows denser cash/position tables, hides all-empty columns, keeps tax-lot rows inside expanded position details, and avoids frontend financial math.
  - Codex B review PASS for contract/privacy/safety.

- P27B-T12 - Account Details visual polish and selected-detail table usability: done.
  - Owner: Codex F; review by Codex B.
  - Frontend polish tightened the account rail, compacted cash display, made selected-detail tables broker-style with sticky first columns, row-click expansion, collapsed data notes, sign-only gain/loss coloring, and no visible raw row/lot refs.
  - Verification: Codex F reported typecheck, lint, build, `git diff --check`, and browser smoke at 1024/1280/1440 passing. Codex B review PASS for contract/privacy/safety.

- P27B-T13 - Backend enforcement for display-only cash/buying-power/collateral policy: done.
  - Owner: Codex C; review by Codex B and Claude E if Agent Team evidence changes.
  - Ensure real-broker Trade Review cannot set account-level feasibility from display-only cash, available-cash, buying-power, or collateral labels. CSP stays generic/unreviewed and covered-call coverage stays unverified unless later same-account collateral/coverage models are approved. Agent Team evidence should carry only safe caveat/status codes such as `buying_power_display_only`, `cash_collateral_policy_not_reviewed`, and `account_level_feasibility_not_evaluated`.
  - Acceptance: no raw/display cash values, buying-power values, account refs/labels, holdings, option rows, tax lots, provider IDs, or raw payloads reach Agent Team evidence; deterministic review caveats remain visible and no advice/execution wording is added.
  - Codex C implementation 2026-06-07: enforced display-only buying-power/collateral policy in real-broker position-dependent reviews. CSP reviews now include `buying_power_display_only`, `cash_collateral_policy_not_reviewed`, and `csp_collateral_unverified` while remaining `analysis_only` with account-level feasibility not evaluated; covered-call coverage remains unverified. Agent-safe evidence sanitizes forbidden cash/buying-power code tokens into safe categories such as `broker_capacity_display_only` and `liquidity_collateral_policy_not_reviewed`, rejects display/account label keys, and preserves lossy scope/caveat metadata only. Verification: `pytest tests/services/trade_review/test_frontend_read.py tests/api/test_trade_review_workspace.py tests/services/agent_team/test_evidence_projection.py -q` -> 109 passed, 5 skipped; `pytest tests/services/agent_team/ tests/services/agent_eval -q` -> 211 passed, 2 deselected.
  - Codex B review PASS 2026-06-07. Re-ran focused verification: `pytest tests/services/trade_review/test_frontend_read.py tests/api/test_trade_review_workspace.py tests/services/agent_team/test_evidence_projection.py -q` -> 109 passed, 5 skipped; `git diff --check` clean.

- P27B-T14 - Account Details selected-detail visual polish pass: done.
  - Owner: Codex F; review by Codex B.
  - Frontend-only polish focused on the lower-right selected-account detail panel. Keep the accepted page layout and account rail. Improve cash density, broker-style position table column order, gain/loss color treatment, row expansion content, empty-column hiding, and user-readable data notes. Do not add backend fields, provider calls, storage writes, broker actions, or frontend financial calculations.
  - Acceptance: endpoints remain `GET /users/{uid}/account-details` and `GET /users/{uid}/account-details/{account_reference}` only; backend display labels remain the source of truth; exact display-only cleanup may remove redundant prefixes/suffixes and color gain/loss labels by leading sign only; raw row/lot refs stay hidden; no advice/execution wording.
  - Codex B backend-label contract confirmation 2026-06-10: selected-account gain/loss labels are Decimal money/percent display labels where losses are signed and gains are unsigned; backend gain/loss labels do not use non-numeric leading-parenthesis text. Selected-account `broker_snapshot_freshness.display_label` and `market_quote_freshness.display_label` are self-describing phrases, not bare `cached`, and remain distinct fields. `summary_labels` are self-prefixed backend display strings, while selected-account row data exposes opaque refs plus display labels only, not raw provider/account IDs, raw balances, raw payloads, transactions, or orders. Non-blocking frontend polish: remove or narrow the `compactFreshnessLabel("cached" -> "Available")` helper so any future bare cached label remains honest.

- P27B-T16 - Account Details option cost-basis unit audit and sync action contract: done.
  - Owner: Codex C; review by Codex B.
  - Codex C implementation 2026-06-11: audited selected-account option display and SnapTrade option normalization. Policy: SnapTrade `average_purchase_price` is treated as broker-reported contract-total average cost for selected-account display, so selected-account option `cost_basis_label` is `abs(quantity) * average_price` and is not multiplied again by OCC multiplier. App-owned/manual per-share option basis still multiplies by contract multiplier when unit semantics are known. Option market value continues to use market price x quantity x multiplier with short/long sign. Existing sync endpoint confirmed: `POST /users/{user_id}/broker-accounts/{broker_account_id}/sync` already exists and is ownership-guarded, but Account Details frontend cannot call it from opaque `acctref_...` without a reviewed private mapping/handoff.

- P27B-T16A - Account Details option average-cost display unit fix: done.
  - Owner: Codex C; review by Codex B.
  - Codex C implementation 2026-06-11: selected-account option `average_cost_label` now follows brokerage display semantics. SnapTrade `average_purchase_price` remains broker-reported contract-total cost basis per contract for `cost_basis_label`, while `average_cost_label` divides that value by the contract multiplier to display the per-share/per-unit premium basis (`$279.33` contract-total average purchase price / 100 -> `$2.79`; mini-option multiplier 10 supported). App-owned/manual per-share option rows continue to display stored average price as average cost and compute total basis with `abs(quantity) * average_price * multiplier`. Option market value sign/multiplier behavior unchanged. No frontend, provider call, DB migration, sync endpoint, Agent Team, or deterministic trade-review feasibility changes.
  - Codex B review PASS 2026-06-11. Verification from Codex C: `pytest tests/services/trade_review/test_frontend_read.py tests/api/test_trade_review_workspace.py tests/services/test_snaptrade_option_normalization.py -q` -> 106 passed, 10 skipped; `git diff --check` clean.

- P27B-T17 - Account Details selected-account visual polish and tax-lot display confirmation: done.
  - Owner: Claude A with Claude B visual/safety review; Codex B contract confirmation.
  - Claude B review PASS 2026-06-11 for the frontend-only Account Details panel polish: brokerage-style column order, equity/option row-expansion panels, and improved frozen-first-column styling. No endpoint, backend, provider, storage, broker-action, or frontend financial-math changes.
  - Codex B tax-lot label confirmation 2026-06-11: `AccountTaxLotDisplayRowRead` exposes only opaque `lotref_...` references plus display labels and validates through `validate_trade_review_workspace_payload`. Tax-lot gain/loss uses `current_value - cost_basis`; money and percent labels use Decimal formatting with unsigned gains, signed losses, and no accounting-parenthesis text, so glyph-driven frontend gain/loss coloring remains contract-safe. Raw lot IDs, provider IDs, provider payloads, account numbers, transactions, and orders remain excluded.

- P27B-T18 - Account Details opaque account sync bridge: done.
  - Owner: Codex C; review by Codex B.
  - Codex C implementation 2026-06-11: added protected `POST /users/{uid}/account-details/{account_reference}/sync` so Account Details can request a selected-account refresh using only the opaque `acctref_...` reference. The route resolves the reference server-side against broker accounts owned by the route user, reuses the existing broker sync service, and returns a small sanitized Account Details sync response with opaque `account_reference`, status, safe message, and timestamps only. Malformed, unknown, and cross-user references fail closed with the same not-found response. Active sync conflicts return sanitized `409` without sync-run or broker-account identifiers. Provider failures return sanitized failed status without provider IDs, request IDs, raw payloads, raw errors, or account numbers. No Account Details GET contract, frontend, Agent Team, deterministic feasibility, provider-live test, or sync endpoint widening was added.
  - Codex B review PASS 2026-06-11.

- P27B-T19 - Account Details selected-account refresh UI: done.
  - Owner: Claude A; visual review by Claude B; contract/safety review by Codex B.
  - Claude A implementation 2026-06-11: consumes only the reviewed P27B-T18 opaque sync bridge (`POST /users/{uid}/account-details/{account_reference}/sync`). New `AccountDetailsSyncRead` TS mirror (`account_reference`, `status`, `message`, `generated_at`, `started_at`, `completed_at`); new `accountDetailsApi.sync(userId, accountReference)`. The legacy broker-account sync route is not called. The frontend never builds or displays broker_account_id, provider IDs, sync_run_id, raw payloads, raw balances, raw holdings, raw quantities, raw lot IDs, transactions, orders, prompts, or traces — only the opaque `acctref_...` reference (already in page state) is sent, and only the sanitized response is rendered.
  - UI: compact `RefreshSnapshotControl` placed beside the selected-account title block (not in the account rail), using the existing Modern Portfolio Desk button + `MpIcon name="refresh"` idiom. Loading state disables the button, switches the label to "Refreshing", and spins the icon. On `succeeded` / `partially_succeeded` the page refetches both the overview (`accountDetailsApi.get`) and the selected-account detail (via the existing detail reload key) so freshness, sync labels, and tiles update without a manual reload. On 409 (running) the UI shows a quiet info-tone "Sync already in progress." line and allows retry later. On `failed` / network error the UI shows a single compact, non-alarming status line. The sync UI state resets when the selected account changes. No frontend financial math, no caveat boilerplate duplication, no broker-action/order/execution wording.
  - Verified: `cd frontend && npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, and `git diff --check` all pass. Browser route smoke at `/account-details` confirms the route renders cleanly with no console errors; the dev sandbox here cannot seed a live user + Account Details payload, so the click-through smoke of the success / partial / failed / running states and the 1024 / 1280 / 1440 light/dark visual verification are deferred to Claude B's review against a working backend.
  - Codex B review PASS 2026-06-11 after blocker fix. The 409/running state remains quiet but no longer keeps the refresh button disabled; endpoint usage remains the two Account Details GETs plus the opaque selected-account sync POST only.
  - Claude B visual/design + frontend-safety review PASS 2026-06-12 (the data-backed smoke deferred above is now complete). Run against the full local stack with a founder-approved one-time view of the real-source dev user (`data_mode: private_real_source`, `amounts_visible`); no real values/labels/identifiers were transcribed into reports. Verified at 1024/1280/1440 in light and dark: no page overflow (only the intended in-table scroll), frozen first column holds under full horizontal scroll with a soft gradient edge (no harsh divider), gain/loss colors readable in both themes, row expansion is a compact footer (empty tax-lot sections stay hidden), and the `RefreshSnapshotControl` stays quiet and on-system beside the title. DOM safety scan clean: no `acctref_`/UUID/`row_reference`/`lot_reference`/`sync_run_id`/`snapshot_id`, no SnapTrade user id/secret, no raw-payload keys, no broker-account numbers, and no advice/order/execution wording. Deferred polish (non-blocking): a few px right-padding inside the table scroller at max scroll; slightly more gap between the refresh button and the In-scope badge; nudge the expanded-row footer one contrast step brighter.
  - Devex follow-up 2026-06-12 (Claude B; tooling only, no T19 product code touched) — flagged for Codex B safety sign-off: the preview/screenshot tool only ever runs `npm run dev` (it ignores launch.json `runtimeExecutable`/`runtimeArgs`/`env` and cannot manage `docker compose`), so the data-backed page could not be previewed without the dev proxy token. Fix: `frontend/vite.config.ts` now reads `LOCAL_DEV_ACCESS_TOKEN`/`BACKEND_URL` via Vite `loadEnv` with `process.env` precedence (Docker path unchanged; values used only by the dev `/api` proxy and never bundled to the browser — Vite exposes only `VITE_`-prefixed vars to client code); `.claude/launch.json` rewritten to the honest `frontend` (npm) + `stack-docker` configs with documented data-backed prereqs; a gitignored `frontend/.env.local` holds the dev token (copied file→file from repo-root `.env`; value never read/printed). Verified: `preview_start("frontend")` → `/api/users` 200 with real data on 5173 (no side ports); Docker frontend `/api/users` still 200 (precedence intact); `npm run typecheck` and `npm run build` clean.
  - Codex B devex safety review PASS 2026-06-12: `loadEnv` is confined to the Vite dev-server config, `LOCAL_DEV_ACCESS_TOKEN` remains non-`VITE_` and is used only as the `/api` proxy header, `process.env` precedence preserves the Docker frontend path, `.env.local` is gitignored, and production build behavior/endpoints/product contracts are unchanged.

- P27B-T20 - Purchase-history / tax-lot availability and selected-position detail: done.
  - Owner: Codex C; review by Codex B. Frontend follow-up by Claude A or Codex F only after backend review PASS.
  - Goal: explain and, where safe, complete why expanded Account Details rows may not show purchase-history details. Determine whether SnapTrade provider data is supplying tax lots for the current normalized positions, whether the app is persisting them, and whether selected-account detail responses return non-empty `tax_lot_rows` for positions that have broker-reported lots.
  - Scope: backend analysis and implementation only. Use CodeGraph first for the existing provider snapshot, normalization, selected-account read builder, and tax-lot display row flow. Do not inspect `.env`, secrets, raw DB contents, logs, raw broker payloads, screenshots, or generated reports. Do not make live SnapTrade calls unless the founder explicitly authorizes a separate smoke. Default tests must use fake provider/model data.
  - Acceptance: for fake SnapTrade/provider responses with broker-reported purchase lots, selected-account detail rows expose display-only `tax_lot_rows` with opaque `lotref_...` references and backend-owned labels for acquired date, term, total gain/loss, gain/loss percent, current value, quantity, average cost, and cost basis. If lots are absent from the provider snapshot, the backend returns an explicit safe empty/limitation state so the UI can say purchase history is unavailable rather than appearing broken.
  - Safety: no raw lot IDs, raw account IDs, provider IDs, provider account IDs, raw payloads, transactions, orders, account numbers, prompts, traces, frontend financial math, tax advice, trading advice, execution wording, or Agent Team evidence widening.
  - Tests: fake-provider tax-lot normalization, selected-account response with non-empty lot rows, absent-lot empty state, opaque-ref/forbidden-field tests, option lot cost-basis/average-cost unit tests, and existing Account Details / Agent Team evidence regressions.
  - Codex C implementation 2026-06-11: audit found equity/ETF tax lots already flowed through SnapTrade-shaped mapping, provider snapshot, stock normalization, `StockPosition.tax_lots`, and selected-account `tax_lot_rows`; missing purchase history was therefore either absent from the provider snapshot or, for options, not represented in the option provider/model/read path. Added nullable normalized `option_positions.tax_lots` with Alembic migration `0019_option_position_tax_lots`, extended `ProviderOptionPositionSnapshot` / SnapTrade option response mapping to carry sanitized tax lots, persisted option lots in normalization, and exposed optional option `tax_lot_rows` / `tax_lot_pagination` with opaque `lotref_...` refs and backend-owned labels. Added `average_cost_label` to tax-lot display rows while preserving existing `purchase_price_label`; option lot labels follow the reviewed unit policy (`SnapTrade purchase_price` treated as contract-total per contract, displayed average/purchase price divided by multiplier, total basis kept as broker-reported or safely computed). Selected-account detail now includes `purchase_history_unavailable` caveat/limitation when no normalized lots are present. Verification: `pytest tests/services/trade_review/test_frontend_read.py tests/api/test_trade_review_workspace.py tests/services/agent_team/test_evidence_projection.py tests/services/test_snaptrade_option_normalization.py -q` -> 117 passed, 19 skipped; `pytest tests/services/test_snaptrade_option_normalization.py -q` -> 4 passed, 5 skipped; skips are disposable-DB safety gates. `git diff --check` clean.
  - Codex B review PASS 2026-06-11. Option tax lots now flow through provider model, normalization, nullable persistence, and selected-account read output as display-only rows with opaque `lotref_...` references. SnapTrade option lot labels preserve the reviewed unit split (`$2.79` average/purchase premium display and `$279.33` total cost basis for a standard one-contract example). Raw lot IDs/provider IDs/raw payloads remain excluded, and no Agent Team evidence or deterministic feasibility scope widened.

- P27B-T21 - Account Details purchase-history display polish: done.
  - Owner: Claude A; contract/privacy review by Codex B; visual review by Claude B.
  - Claude A initial implementation 2026-06-11: shared `PurchaseHistoryBlock` consumed by equity + option expansions; TS types mirror the P27B-T20 backend additions (`AccountTaxLotDisplayRowRead.average_cost_label`; `AccountOptionPositionDisplayRowRead.tax_lot_rows` + `tax_lot_pagination`). Endpoints unchanged (Account Details overview GET, selected-account GET, opaque selected-account sync POST). No provider/SnapTrade direct calls, no new endpoints, no storage writes, no frontend financial math, no Agent Team / LLM ingestion.
  - Claude A 2026-06-11 polish pass (this turn) — Account Details cleanup while tax lots are deferred upstream:
    - Tax-lot/purchase-history block is hidden entirely when `tax_lot_rows` is empty. No "purchase history unavailable from broker snapshot" copy, no empty table, no prominent missing-feature signal. (Previous compact unavailable line and its style were removed.)
    - Row expansion is now offered only when something useful is in the expanded panel: equity rows expand when lots exist OR `instrument_name_label` OR `asset_class_label` is present; option rows expand when lots exist OR `multiplier_label` is present. Otherwise the row stays a flat data row.
    - `valuation_source_label` is no longer rendered in either expansion footer per the P27B-T21 display policy. Equity expansion footer keeps `asset_class_label`; option expansion footer keeps `multiplier_label`. `row_reference` and `lot_reference` remain React-key / state-only and are never displayed.
    - Position-table column hierarchy is brokerage-style: identity first, then price / current or market value / total gain-loss / gain-loss %, then quantity, then avg cost and cost basis. Equity header is "Symbol | Last price | Current value | Total gain/loss | Gain/loss % | Quantity | Avg cost | Cost basis"; option header is "Contract | Type / side | Strike | Expiration | Last price | Market value | Total gain/loss | Gain/loss % | Quantity | Avg cost | Cost basis". Quantity loses redundant "shares" / "contract(s)" suffix via the existing label cleaners. Gain/loss cell color is purely glyph-driven from the backend label (leading `-` / `−` / accounting `(...)` -> block, leading `+` or unsigned non-zero -> live, all-zero / em-dash -> neutral) and stays paired with the signed label text. Headers are display-only renames; every cell renders the backend label verbatim and the frontend performs no arithmetic.
    - Frozen first column already uses a soft `::after` gradient elevation in `.account-details-workspace .mp-sticky-col` (no hard vertical line) — left unchanged.
    - Selected-account "Refresh snapshot" UI from P27B-T19 is unchanged; on success / partial success the page still refetches both the overview and the selected-account detail, the 409 running state stays quiet and retryable, and broker_account_id / provider IDs are never sent or rendered.
  - Live label-shape spot-check against the docker stack synthetic-demo user (Fidelity-style brokerage labels, rendered verbatim by the frontend, no math):
    - Last price label `'$4.87'` -> per-share option premium.
    - Market value label `'$-487.00'` -> signed contracts × 100 × premium.
    - Avg cost label `'$2.79'` -> per-share avg premium.
    - Cost basis label `'$279.33'` -> contracts × 100 × avg cost.
    - Multiplier label `'1 multiplier'` -> rendered as the option-expansion footer line verbatim (backend wording; not modified by frontend).
    - All accounts return `tax_lot_rows: []` while SnapTrade does not supply lots for the connected accounts, so the new "hide when empty" path is the observable one and no purchase-history block renders.
  - Verified: `cd frontend && npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, `git diff --check` all pass. Full-stack smoke against `docker compose up -d postgres backend frontend`: `GET /health` -> 200; `GET /users` (authed) -> 200, one dev user; `GET /users/{uid}/account-details` -> `data_mode=private_real_source`, 7 accounts, every reference shaped `acctref_...`; per-account `GET /users/{uid}/account-details/{ref}` -> response key set matches the extended TS types one-for-one for both equity and option rows; the Vite proxy at `http://localhost:5173/api/users` returns 200 once docker carries the dev access token. `/account-details` route shell returns 200.
  - Browser-interactive expand-row click-through at 1024 / 1280 / 1440 light/dark is deferred to Claude B. The blocker is environmental: the Chrome browser MCP is not connected in this dev sandbox, and the Claude_Preview server cannot inherit `LOCAL_DEV_ACCESS_TOKEN` from the project root `.env` so the Vite proxy returns 401 without it; once the founder is at the keyboard the docker stack already serves the page at `http://localhost:5173/account-details` with the proxy authed for the visual smoke.
  - Codex B contract/privacy review PASS 2026-06-11. Endpoint usage remains limited to the Account Details overview GET, selected-account GET, and opaque selected-account sync POST. Empty `tax_lot_rows` render no purchase-history block or unavailable copy; row and lot refs are React-key/state-only; `valuation_source_label` is no longer rendered; option/equity labels remain backend-owned display labels with no frontend financial math; gain/loss tone is glyph-driven and paired with signed text. Deferred polish: remove the stale code comment that still mentions the old unavailable purchase-history copy, and let Claude B/Claude A continue visual treatment of the table/frozen-column details.
  - Backend blocker watch (not blocking this frontend task): the multiplier label `"1 multiplier"` reads oddly when rendered verbatim; if the founder wants `"100x multiplier"` or `"x100"`, that is a separate backend label adjustment. The frontend will pick it up automatically.
  - Claude A 2026-06-11 visual-polish pass (addresses Codex B deferred polish; frontend-only):
    - Frozen first column refined: the `::after` elevation gradient narrowed 12px -> 7px, dropped the always-on 0.85 opacity band, and softened the `--mp-sticky-edge` token (dark 0.42 -> 0.28, light 0.13 -> 0.10). At rest the edge sits over same-colored cells and is nearly invisible; once content scrolls beneath it the gradient reads as a gentle elevation. No hard vertical line; the hover-tint box-shadow rule is untouched.
    - Numeric scanning: `tdMono` cell color promoted from `--mp-ink-2` (muted) to `--mp-ink` so prices/values/quantities read crisply; `tabular-nums` retained; gain/loss color override still wins for those cells.
    - Expansion redesign: removed the large display-font title + separate footer; replaced with one compact, left-aligned contextual-metadata line (`ExpandedMeta`) — instrument name (equity) / contract (option) as the slightly stronger primary, asset class / multiplier as muted secondary, dot-separated. Reads as metadata, not a panel header.
    - Expansion gating tightened so it only opens when it adds something the row lacks: equity expands on lots OR `instrument_name_label` (asset class alone no longer triggers, it rides along as secondary); options expand on lots only (multiplier alone no longer triggers — it was the odd "1 multiplier" string). With lots deferred upstream, option rows therefore do not expand in the current demo, which is the honest state.
    - Stale comment removed: the `PurchaseHistoryBlock` docstring no longer claims an "unavailable from broker snapshot" line renders when lots are empty; it now documents that the block renders nothing.
    - Endpoints unchanged (overview GET, selected-account GET, opaque selected-account sync POST). No backend, provider, storage, Agent Team, financial-math, raw-ref, or broker-action changes. The P27B-T19 refresh control is untouched.
    - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, `git diff --check` all clean. Full-stack docker smoke: `GET /health` 200; authed `GET /users` 200; Vite proxy `GET /api/users` 200; `/account-details` 200. Confirmed the running docker frontend (volume-mounted live source) serves the polished build — the transformed `AccountDetailsPage.tsx` module contains the new `ExpandedMeta`/`expandedMetaPrimary` symbols, contains zero references to the old "unavailable from broker snapshot" copy, and `globals.css` serves the refined 7px sticky gradient.
    - Claude B final visual smoke PASS 2026-06-12 after the preview dev-token fix: standard Claude Preview path now renders real connected-account data on `http://localhost:5173/account-details` via the Vite `/api` proxy. Verified 1024 / 1280 / 1440 in light and dark with page overflow 0, frozen first column intact at full horizontal scroll, gain/loss colors readable, row expansion compact, empty tax-lot sections hidden, and refresh control quiet. Safety scan clean: no account refs, UUIDs, row/lot refs, sync/snapshot IDs, SnapTrade secret/user IDs, raw-payload keys, broker account numbers, or advice/order/execution wording. No visual blockers. Non-blocking console issue found in `AccountSelectorItem`: repeated React warning from mixing `border` shorthand with `borderColor` override across selected/deselected styles.

- P27B-T22 - Account rail React border-warning cleanup: done.
  - Owner: Codex F or Claude A; review by Codex B if needed.
  - Scope: tiny frontend-only cleanup in `frontend/src/pages/AccountDetailsPage.tsx` around `AccountSelectorItem` account-rail button styles. Replace mixed `border` shorthand plus `borderColor` overrides (`selectorButton` / `selectorButtonSelected`) with longhand `borderWidth`, `borderStyle`, and `borderColor` so account switching no longer spams React's console warning.
  - Acceptance: no visual behavior change to the account rail; selected/deselected/focus states stay token-based; no endpoint, backend, provider, storage, financial-math, raw-ref, or broker-action changes. Verification should include `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, `git diff --check`, and a quick `/account-details` account-switch smoke confirming the warning is gone.
  - Codex B implementation 2026-06-12: changed `selectorButton` from the `border` shorthand to `borderWidth`, `borderStyle`, and `borderColor` longhands while preserving `selectorButtonSelected.borderColor`. This keeps the visual states unchanged and removes the React shorthand/longhand warning source.

Recommended next assignment:

- Resume Trade Review / Agent Team scope integration.

### Phase 27A - Multi-Account Scope And Account Details

Status: P27A-T1 done; P27A-T2 done; P27A-T3 done; P27A-T4 done; P27A-T5 done; P27A-T6 done; P27A-T7 done; P27A-T8 done; P27A-T9 done. Superseded for normal v1 display by Phase 27B until latest-sync membership is stable.

Architecture references:

- `docs/codex-b-architecture/PHASE_27A_ACCOUNT_DETAILS_SELECTED_ACCOUNT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_27B_ACCOUNT_DETAILS_STABILITY_CONTRACT.md`

Summary:

- P27A established the selectable multi-account scope model, Account Details overview, private selected-account detail contract, review-account selection, and lossy Agent Team scope evidence.
- P27A used opaque app-owned `acctref_...` references and backend-owned display labels to avoid exposing broker/provider IDs, account numbers, raw balances, raw holdings, raw quantities, raw provider payloads, prompts, or traces.
- P27A-T8/T9 added selected-account position detail support, but those rows are not product-authoritative until Phase 27B fixes latest-sync membership and option current/expired/closed semantics.

Completed tasks:

- P27A-T1 - Multi-account scope and Account Details backend contract: done; Codex B PASS.
- P27A-T2 - Private Account Details frontend page: done; Codex B PASS.
- P27A-T3 - Real broker snapshot to Account Details projection: done; Codex B PASS.
- P27A-T4 - Private Account Details value-label contract and account identity: done; Codex B PASS.
- P27A-T5 - Account Details page redesign for multi-account browsing: done; Codex B PASS.
- P27A-T6 - Trade Review review-account and context-scope request contract: done; Codex B PASS.
- P27A-T7 - Real review-account resolution for portfolio-backed Trade Review: done; Codex B PASS.
- P27A-T8 - Selected Account Details positions contract: done; Codex B PASS after latest-only duplicate-row blocker fix.
- P27A-T9 - Account Details selected-account detail frontend consumption: done; Codex B PASS.

Product caveat:

- Normal Account Details v1 display now follows Phase 27B: broker-data readiness first, holdings/options suppressed unless current-position membership is explicitly safe.

### Phase 26A - Market Mood Context

Status: active P1/internal-demo planning and implementation.

Architecture contract:

- `docs/codex-b-architecture/PHASE_26A_MARKET_MOOD_CONTRACT.md`

Purpose:

- Add broad market sentiment context using CNN-derived Fear & Greed style data.
- Dashboard shows only a compact Market Mood context card.
- A dedicated Market Context page shows the overall index plus the seven component indicators with native-scale charts and explanations.

Safety boundaries:

- Internal-demo only pending source/rights review.
- Backend fetch/cache only; no frontend-direct provider calls.
- Do not label as live or real-time.
- Do not use CNN logo, CNN branding treatment, or clone CNN visual design.
- Do not affect trade-review actionability or deterministic risk rules.
- Do not send Market Mood data to LLM/agent prompts by default.
- No advice, recommendation, buy/sell, urgency, risk-on/risk-off, execution, safe-to-trade, or ready-to-trade wording.

Tasks:

- P26A-T0 - Market Mood architecture contract: done.
- P26A-T1 - Backend contract, adapter, cache, and tests: done; Codex B review PASS.
- P26A-T2 - Dashboard Market Mood compact card: done (Claude B visual/design PASS).
  - New `frontend/src/types/marketMood.ts` (exact mirror of `market_mood.py`; verified all 24 read keys match the live payload), `frontend/src/api/marketMood.ts` (GET `/market-context/market-mood` only — no refresh, no provider call), `frontend/src/components/market-context/MarketMoodCard.tsx` (compact, self-fetching, secondary card in the Dashboard left column under account/portfolio + economic-awareness surfaces).
  - Glanceable hierarchy: header (title + compact data-mode badge) → hero (large score + uppercase rating) → 0–100 gradient spectrum ramp with a marker placed by the backend score → one quiet footer line (compact source label only; generic safety boundaries live in the product disclaimers, not per-card). Components, trend graph, and 1w/1m/1y comparisons intentionally deferred to P26A-T3. Runtime UI displays provider-reference data only and treats synthetic/unavailable as unavailable. No CNN branding, no forbidden wording, no storage writes, no external calls.
  - Same pass also cleaned up Dashboard noise: ReviewReadiness verdict reworded to plain-English headline + quiet secondary line (overall-mode chip removed), DemoChip de-duped in the visible area from 5 spots to 2 (verdict + Account summary), raw `caveat_codes` no longer rendered as user-visible badges, and the literal "demo · not yet connected" cell content removed.
  - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, `git diff --check` all clean; live backend returns a valid `MarketMoodRead` (200) whose keys/shape match the new TS types exactly. Live visual smoke at 1024/1280/1440 (light + dark) confirmed by Claude B in an authenticated preview.
- P26A-T3 - Market Mood detail-page backend contract extension: done; Codex B review PASS.
  - Added `GET /market-context/market-mood/detail` with a provider-neutral `MarketMoodDetailRead` contract. Existing compact `GET /market-context/market-mood` and protected `POST /market-context/market-mood/refresh` remain unchanged.
  - Added detail schemas for per-indicator history points and seven `MarketMoodIndicatorRead` items, including backend-owned subtitles, descriptions, raw value labels, unit labels, axis labels, axis value format, and higher/lower value meaning. Detail graphs are not forced onto 0-100; each indicator has its own raw scale while retaining normalized score/rating labels.
  - Added synthetic history for all seven detail indicators so P26A-T4 frontend design can proceed without live provider access. Provider-reference detail preserves safe component histories only when the provider payload supplies them; missing provider-reference histories remain empty/unavailable and are not fabricated.
  - Verification: `./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q` passed (`16 passed`); `./.venv/bin/python -m pytest tests/services/test_economic_calendar.py tests/api/test_economic_calendar.py -q` passed (`52 passed`). No frontend work, external API calls, LLM/agent ingestion, actionability/risk-rule integration, raw provider payload exposure, or forbidden advice/execution wording added.
- P26A-T4 - Market Mood detail-page frontend redesign: done; Claude B visual/design + frontend-safety PASS; Codex B contract/safety PASS.
  - Consumes only the reviewed detail contract `GET /market-context/market-mood/detail` → `MarketMoodDetailRead`. Frontend types extended to mirror it exactly (`MarketMoodAxisValueFormat`, `MarketMoodValueMeaning`, `MarketMoodIndicatorHistoryPointRead`, `MarketMoodIndicatorRead`, `MarketMoodDetailRead`); no invented fields. `marketMoodApi.detail()` added (the compact card still uses `marketMoodApi.get()`, unchanged).
  - Files: new `frontend/src/pages/MarketMoodPage.tsx` (rewritten to the detail contract), new `frontend/src/components/market-context/MarketMoodIndicatorChart.tsx` (interactive SVG line chart — no chart lib in the stack), `frontend/src/components/market-context/marketMoodHelpers.ts` (+`formatAxisValue`), `frontend/src/types/marketMood.ts`, `frontend/src/api/marketMood.ts`. Route `/market-context/market-mood` unchanged (added in T3); Dashboard card untouched.
  - Design (frontend-design skill, within Modern Portfolio Desk language): editorial analyst-desk layout — a confident overall band (large score + rating + 0–100 ramp + freshness + "versus prior" 1w/1m/1y aside), then all 7 indicators as cards, each with its own interactive raw-scale history chart, current value (verbatim `current_value_label`), normalized index/rating as secondary, `axis_label`, higher/lower-value meaning, and `description`. One compact source/attribution section at the end; broad disclaimers not repeated per card.
  - Charts plot RAW `history[].value` on each indicator's native scale (%, index, ratio, bps) — never forced onto the 0–100 score. Hover shows date + backend `value_label` verbatim, with rating_label + score_label/100 as secondary. Only math is autoscale + light axis formatting keyed off `axis_value_format`. States handled: loading / error+retry / unavailable / empty-history (per chart) / synthetic / provider_reference.
  - Safety: minimal CNN wording ("CNN-derived Fear & Greed Index"); no logo/branding/gauge clone; no advice/recommendation/urgency/order/execution wording; no external provider call; no storage writes; no new endpoint; no backend change; no Agent Console / Phase 21A change.
  - Verified: `npm run typecheck`, `npm run lint -- --max-warnings 0`, `npm run build`, backend Market Mood tests, and `git diff --check` all clean. Browser smoke against backend detail payload confirmed all 7 indicators render with raw-scale charts, hover tooltip shows date + value label, and the layout responds 1-up (1024) / 2-up (1280, 1440).
  - Claude B visual/design + frontend-safety review (2026-06-04): PASS. Verified: polished editorial layout (overall band → Indicator Desk rail+focused panel → Source Status), confident hierarchy with the large score/rating as the focus and a deliberate type/spacing scale; per-indicator charts plot RAW `history[].value` autoscaled to native min/max (never forced 0–100) with readable line/area/marker/clamped tooltip and a per-chart "Insufficient history" fallback (<2 points); `role="img"`+aria-labels on charts; color supplementary (meaning in labels); no CNN logo/branding/gauge clone (linear ramp + text attribution only); no advice/recommendation/urgency/order/execution/risk-on-off/buy-sell wording; typed primitives/tokens only, no emoji/ambiguous glyphs; no storage/external calls/new endpoint/backend change; Dashboard `MarketMoodCard.tsx` unchanged (absent from the diff) — no regression. Re-ran `npm run typecheck`, `npm run lint -- --max-warnings 0`, `git diff --check` clean (build per Claude A). Live authenticated browser smoke not run in this environment — responsiveness assessed statically (minWidth:0 throughout, ResizeObserver-driven SVG width, clampTooltip); rely on Claude A's recorded 1024/1280/1440 light + 1280 dark smoke.
  - Codex B alignment: detail-page source copy now uses "CNN-derived Fear & Greed Index", matching the contract posture and compact card; backend `source_rights_notice` remains rendered in Source Status.
  - Deferred polish: empty-history copy reads "Insufficient history" / "The backend did not provide enough raw values…" rather than the spec's "Not enough history to chart." — cosmetic.
  - Status: `done`.
- P26A-T5 - Market Mood real-data-only page behavior: done; Codex B review PASS.
  - Backend runtime product reads are now provider-reference-only: `GET /market-context/market-mood` and `GET /market-context/market-mood/detail` return last-good CNN-derived/provider-reference snapshots when available, otherwise `data_mode="unavailable"`. Synthetic fixtures remain injectable for tests only and are ignored by the default runtime service, including if an old synthetic snapshot is active/restored.
  - Frontend Market Mood surfaces now treat anything other than `provider_reference` as unavailable. Removed visible "Synthetic", "Demo history", and synthetic chart overlay behavior from the Dashboard card/detail page path; indicators without real provider history render the existing insufficient-history state instead of a sample chart.
  - Provider-reference detail still renders overall score/rating and any safe component histories supplied by the provider payload; it does not fabricate missing component histories. Safety invariants remain false (`is_trading_signal`, `is_actionability_input`, `is_risk_rule_input`).
  - Verification: `./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q` passed (`21 passed`); `npm run typecheck` passed; `npm run lint -- --max-warnings 0` passed; `npm run build` passed; `git diff --check` clean.
- P26A-T6 - Market Mood runtime refresh wiring for provider-reference snapshots: done; Codex B review PASS.
  - Goal: make the existing protected `POST /market-context/market-mood/refresh` able to fetch the CNN-derived Fear & Greed data through a backend-only injected HTTP boundary and persist a normalized provider-reference last-good snapshot, so the compact Dashboard card and detail page can display real provider-reference data after refresh.
  - Scope: backend only; no frontend-direct provider calls; no startup fetch; no scheduler; no public production claims; no synthetic product fallback. Tests must use mocked/injected HTTP responses only. A live smoke may be documented as founder-run/explicit-only, not part of default tests.
  - Acceptance: refresh success persists and activates provider-reference data; refresh failure preserves last-good and returns sanitized status; product GETs display provider-reference data or unavailable; provider component histories are preserved only when supplied; missing histories are not fabricated; no raw provider payload, URL, headers, cookies, exception body, credential, prompt, trace, broker/private data, advice, execution, or trading-signal language leaks.
  - Implementation: added `CnnFearGreedHttpClient` with injected text transport, `build_cnn_market_mood_refresh_runner(...)`, and wired protected `POST /market-context/market-mood/refresh` to the runner. The runner fetches only when the protected refresh endpoint is explicitly invoked, validates through `CnnDerivedMarketMoodProvider`, persists normalized JSON, then activates the provider-reference last-good snapshot. CNN-shaped key aliases are normalized internally; raw provider URLs/payloads/headers/cookies/provider IDs are not exposed or cached.
  - Verification: `./.venv/bin/python -m pytest tests/services/test_market_mood.py tests/api/test_market_context.py -q` passed (`27 passed`); `git diff --check` clean. One founder-approved live smoke through the backend refresh runner passed on 2026-06-04: `data_mode="provider_reference"`, 1323 trend points, 7 components, 7 indicators, and 7 indicators with provider history. Browser check of `/market-context/market-mood` showed provider-reference detail data and no visible Synthetic/Demo-history wording.
- P26A-T6A - Market Mood provider component scale calibration: done (frontend honesty layer; Claude B PASS 2026-06-04).
  - Goal: calibrate the live provider-reference component `value` / `value_label` / `axis_value_format` treatment so each detail-page chart uses honest native units. The live refresh path works, but first smoke showed at least one unit mismatch, e.g. Market Momentum appearing as a very large percent-like value.
  - Scope: keep provider-reference data only; no synthetic product fallback; no new provider source; no frontend-direct calls. Backend should own corrected unit/axis/value-label metadata where possible. Frontend should render backend labels and avoid implying an incorrect unit.
  - Acceptance: live-provider component histories remain real/provider-reference; value labels are not misleading; charts still plot native raw values; unavailable/missing histories remain insufficient-history; no actionability/risk/LLM/advice/execution scope added.
  - Implemented (frontend-only honesty layer; backend unit alignment deferred as the optional Codex C follow-up): `marketMoodHelpers.ts` `formatAxisValue({neutral})` strips %/$/unit suffixes; `indicatorScaleCalibration(ind)` flags neutral when `percent` + |v|>150 (catches Market Momentum 7553.68 → was "7553.7%") or `spread`+"bp" + |v|<10 (catches Safe Haven 3.77 → "4 bps", Junk Bond 1.46 → "1 bps"). `MarketMoodIndicatorChart` `neutralScale` neutralizes Y-axis ticks AND the tooltip raw value (bypasses the misleading backend `value_label`). `MarketMoodPage` rail chip + focused panel use the calibration consistently (both show the neutral raw value); the focused panel axis becomes "Provider raw value" with a calm italic muted caption "Native scale uncertain — provider raw value shown." Trustworthy indicators (Stock Price Strength 1.7%, Breadth, Put/Call 0.58, Volatility 16.1, 335 bps) pass the plausibility check and keep their backend `value_label` verbatim. Values are never fabricated — only the misleading unit suffix is suppressed.
  - Claude B review (2026-06-04): PASS. Calibration caption + "Provider raw value" axis read calmly (xs/mute/italic), consistent between rail chip and focused panel; thresholds catch the three implausible live cases without over-firing on plausible ones; honesty preserved; no advice/CNN-clone/forbidden wording; no regression (typecheck/lint/git-diff clean). Deferred polish: the `spread`+bp `|v|<10` rule could false-neutralize a legitimately small (3–9 bp) spread — acceptable for the observed provider payload; the real fix is the optional backend `unit_label`/`axis_value_format` alignment (Codex C). Plan-note hygiene: this task was originally framed as "backend should own corrected metadata"; the shipped fix is the frontend honesty layer with the backend alignment deferred — note retained here for traceability.
- P26A-T8/T9/T10 - Market Mood detail UX polish and one-year chart window: done; Codex B visual/contract re-review PASS.
  - Indicator charts now render only the past one year. Market Momentum computes its 125-day moving average from the full raw history, then renders only the one-year visible slice; other indicators have no moving-average overlay. Tooltips use visible raw points and show the moving-average value only when it exists for the hovered date. Endpoint scope remains `GET /market-context/market-mood/detail` only; no backend/provider/CNN call, refresh, storage write, or trading-action wording was added.
- P26A-T7 - Source/rights and production-readiness review: required before production/public display.

Next handoff:

- Optional backend polish: align provider `unit_label` / `axis_value_format` with emitted Market Mood component value scales so the frontend neutralization heuristic can be removed later.
- Optional design polish: the founder plans to revisit the Market Mood detail-page UI with Claude Design after the current data-fetching and chart behavior is stable.
- Keep P26A-T7 open for source/rights and production-readiness review before production/public display.

### Phase 25A - Agentic Workflow Foundation

Status: active, but mock-first and gated.

Accepted ADRs:

- `docs/codex-b-architecture/adr/0008-agentic-orchestration-spine.md`
- `docs/codex-b-architecture/adr/0009-agent-persona-display-labels.md`

Current posture:

- App-owned safety spine is permanent.
- Custom runner first; LangGraph deferred/gated.
- SSE-first transport remains independent of engine, but realtime Agent Console implementation remains paused.
- OpenAI Agents SDK remains rejected.
- MCP remains future-only and public/agent-safe only; private-tier MCP is prohibited.
- Memory is disabled for MVP.
- Mock remains default. Gemini/OpenAI live provider tests are explicit, opt-in, and backend-only.

Recent status:

- P25A-T7 - Provider key setup and Gemini live-smoke path: done.
- P25A-T8 - OpenAI adapter: done after review.
- P25A-T9 - Backend packaging/build migration cleanup: done after documentation cleanup.
- P25A-T10 - Persona model analysis: done.
- P25A-T11 - Backend display-label contract: done; frontend may render `display_name` verbatim when scheduled.
- P25A-T12 - Read-only Agent Console handoff polish: done; Codex B review PASS.
  - Frontend-only copy/label cleanup. Agent Console now presents itself as a read-only analysis report, not an interactive chat surface. Composer remains disabled and non-interactive; no backend, endpoint, fetch, payload, storage, provider/model selector, LLM, TradingAgents, MCP, LangGraph, or financial-computation behavior changed.
- P25A-T13 - Single-run real-provider gate: done; Codex B review PASS.
  - Hardened the opt-in Gemini/OpenAI live-smoke tests (synthetic data only) so a single controlled live run through `ReviewRunner` asserts: output passes the existing safety/eval path; run status is `completed`/`partially_completed`/`failed_safe`; no forbidden private keys/values, secret/key/URL patterns, or advice/order/execution wording; and provider failures degrade safely with no raw provider details leaked. Gemini path: `POA_LLM_LIVE_TESTS=1` + already-exported `GOOGLE_API_KEY`, cheap Flash model default, rate-limit/quota/unavailable are safe non-blocking. OpenAI path: extra `POA_LLM_OPENAI_LIVE=1` paid-ack gate; not run by default. Default suite stays offline/mock; no route/persistence/frontend/composer change. Founder-run Gemini live smoke passed (`1 passed, 1 warning in 1.77s`); the warning tracks the known `google.generativeai` deprecation and is covered by P25A-T14.

- P25A-T14 - Migrate Gemini adapter to `google-genai`: done; Codex B review PASS.
  - The Gemini adapter now lazily imports `google.genai` and uses `genai.Client(...).models.generate_content(...)`; the app-owned `LLMProvider` protocol, injected/fake-client testability, `LLMProviderResponse` shape, safe status mapping, and mock-default posture are unchanged. `pyproject.toml` `live-llm` extra and `uv.lock` updated (removed deprecated `google-generativeai`; added `google-genai` v2.8.0, which also slimmed the transitive tree). Default suite stays offline/mock with injected fakes; no route/persistence/frontend/composer change. Founder-run post-migration Gemini live smoke passed (`1 passed in 0.03s`) with no `google.generativeai` deprecation warning.
- P25A-T15 - Agent Console read-only run path on `ReviewRunner`: done; Codex B review PASS.
  - The `/agent-team/trade-review-analysis/preview` route now runs the reviewed `ReviewRunner` spine (safety/eval/timing/budget) via a new backend projection `build_console_read_from_review_run_state(AgentReviewRunState) -> AgentTeamAnalysisConsoleRead`, preserving the endpoint, response contract, and backend-owned `display_name` labels (ADR 0009). `run_status` maps `failed_safe -> failed` for the console vocabulary; provider warnings are sanitized and provider-neutral (no raw payload/URL/key/exception body); `deterministic_evidence_summary` keeps the legacy `stock_position_count` key for payload parity. Fixed the hardcoded "Mock portfolio-team synthesis" wording in `ReviewRunner._compose_final_synthesis` to provider-neutral "Portfolio-team synthesis" so it is correct on live runs. Behavior note: blocked-actionability snapshots now correctly degrade to a deterministic-only console (no LLM role commentary) instead of emitting mock commentary that ignored the gate. Mock stays default; live providers via backend env only; composer stays disabled; no new endpoint, streaming, persistence, parallel dispatch, or tool execution.
- P25A-T16 - Live LLM development runtime profile for Agent Console: done.
  - Need: the default Docker backend intentionally excludes optional live-provider SDKs, so the Agent Console route remains mock-only in ordinary Compose runs even when provider keys are present. Add a dev-only, opt-in runtime/build path that installs the `live-llm` extra and lets the existing backend env gate run Gemini/OpenAI from the read-only Agent Console route. Default Docker image must remain lean/offline/mock; no secrets in commands/docs; no frontend provider selector, streaming, composer activation, persistence, or new endpoint.
  - Implementation: added Docker build arg `INSTALL_LIVE_LLM=false` and opt-in
    `docker-compose.live-llm.yml`, which builds
    `portfolio-options-agent-backend:live-llm` with `INSTALL_LIVE_LLM=true`.
    The ordinary `backend` build path remains lean and mock-default. The live
    override still defaults `POA_LLM_MODE`/`POA_LLM_PROVIDER` to mock unless
    backend env gates are explicitly configured in private `.env` or shell
    environment.
  - Verification: `docker compose build backend` passed; default image import
    probe returned `{"google.genai": false, "openai": false}`. Opt-in build
    `docker compose -f docker-compose.yml -f docker-compose.live-llm.yml build
    backend` passed and tagged `portfolio-options-agent-backend:live-llm`; live
    image import probe returned `{"google.genai": true, "openai": true}`. No live
    provider calls were run, no keys were read or printed, touched docs/config
    contained no inline key assignments, and `git diff --check` passed.
  - Founder-approved Gemini route-function smoke: restarted backend with the
    opt-in live profile and `POA_LLM_MODE=live`, `POA_LLM_PROVIDER=google`,
    `POA_LLM_MODEL=gemini-2.5-flash-lite`; confirmed key presence/SDK availability
    without printing the key. Host-to-container HTTP ports were unavailable in the
    sandbox, so the backend route function was invoked inside the live backend
    container. Result: `run_status=completed`, 5 role outputs, all provider
    statuses `ok`, `is_mock=False`, `safety_flags=["provider:google",
    "analysis_only", "deterministic_metrics_owned_by_backend"]`, no provider
    warnings. The backend was then restored to the ordinary mock-default Compose
    profile.

Next possible work:

- Larger agentic work (Options Strategist persona P1, durable conversational Console, streaming/SSE, persistence, parallel dispatch, or tool execution) needs a separate product decision.

### Phase 24B - FRED Economic Awareness

Status: backend foundation available; frontend/economic-news expansion may be paused if Market Mood or agentic workflow has higher priority.

Current posture:

- FRED API key is backend-only.
- FRED refresh is opt-in and sanitized.
- Forecast remains unavailable unless a future approved source provides it.
- Exact future release times are not claimed when unknown.
- Economic awareness remains context-only and not a trading signal.

Recent status:

- P24B-T1 - FRED backend provider and official macro snapshot: done after review.
- P24B-T1A - FRED refresh resilience and partial success: done after review.
- Frontend follow-up should only proceed if the economic panel is reactivated.

### Phase 23B - Symbol Lookup

Status: functional for personal demo; future cleanup remains.

Current posture:

- Frontend autocomplete uses backend-owned normalized symbol search.
- Browser-local recent symbols are per-browser LRU only.
- Backend empty query returns no symbols.
- Global symbol directory is shared; recents are user/browser local.

Recent status:

- P23B-T1/T2 - Persistent last-good symbol directory and opt-in refresh wiring: done.
- P23B-T3 - Uppercase frontend autocomplete polish: done.
- P23B-T5 - Backend recents/default cleanup: done.
- P23B-T6 - Browser-local recents LRU: done.
- P23B-T7 - Offline fixture cleanup: done.
- P23B-T8 - Agent Console autocomplete parity: done; no code change needed because Agent Console reuses `TradeReviewForm`.

Deferred cleanup:

- Remove demo fixture prominence once real refreshed symbol directory is reliable.
- Avoid duplicate task IDs in future Phase 23 references.

### Phase 22A - Market Data Evaluation

Status: backend evaluation foundation complete; commercial provider track parked.

Current posture:

- Provider-neutral market-data contracts exist.
- Alpaca Basic evaluation adapter is internal/demo only and indicative/limited-source.
- No provider is selected for production.
- Tradier is not the assumed scalable production provider.
- Commercial vendor comparison/RFI is parked until external paid beta or production market-data licensing is planned.

Recent status:

- P22A-T1 - Provider-neutral snapshot contracts and synthetic/replay tests: done.
- P22A-T4 - Alpaca Basic local/internal evaluation adapter: done.

## Paused / Deferred

### Phase 21A - Realtime Agent Console Backend Contract

Status: paused.

Do not implement:

- Agent Console follow-up composer activation.
- SSE follow-up command path.
- Agent-thread persistence.
- Live multi-agent debate/routing/reflection/memory.

Reactivation requires Codex A/PM approval after founder learning and architecture review.

### Commercial Market-Data Provider Selection

Status: parked.

Do not start vendor outreach, licensing negotiation, pricing negotiation, production-provider selection, or public current-quote display until external paid beta or production planning reopens the track.

### Dashboard Claude Design Exploration

Status: allowed only after contract boundaries are defined.

Claude Design may explore hierarchy and visual treatment, but must not invent backend fields, fake real account values, add execution controls, or make demo data appear real.

## Older Phase References

Older phase details remain preserved in:

- `docs/shared/implementation_plan_archive_2026-06-03.md`
- `docs/shared/completed_phases_log.md`
- `docs/shared/CHANGELOG.md`

Key architecture/product docs:

- `docs/shared/current_roadmap.md`
- `docs/shared/TASKS.md`
- `docs/codex-a-product/DASHBOARD_CONTENT_DECISION.md`
- `docs/codex-b-architecture/ARCHITECTURE_HANDOFF.md`
- `docs/codex-b-architecture/architecture.md`

## Current Next Step

If frontend work resumes, the next clean handoff is:

- Claude A: P26A-T2 Dashboard Market Mood compact card.
- Reviewer: Claude B or Codex B.

Keep the implementation prompt narrow: consume reviewed Market Mood backend fields, render the compact Dashboard card below primary review-readiness/portfolio-risk surfaces, and preserve all source-rights and non-signal caveats.
