# Dashboard Content Decision And Contract Gap Map

Status: PM decision memo, documentation only  
Owner: Codex A - Product / Founder Strategy / PM  
Date: 2026-05-26  
Plan task: `P20D-T0`

Update (2026-05-26): Codex A approved private authenticated Dashboard
account-detail display in principle, provided it uses backend-formatted
display labels only, explicit freshness/provenance, and a privacy display
mode. Codex B captured the architecture boundary in
`docs/codex-b-architecture/PHASE_20D_DASHBOARD_ACCOUNT_DETAIL_CONTRACT.md`.

Update (2026-05-29): Codex A reviewed Claude C's Stock Rover heavy-user
pressure test and ratified the Dashboard positioning below. Stock Rover is a
useful Product B reference, but Portfolio Copilot should position as a
complementary pre-trade portfolio-aware review layer, not a Stock Rover
replacement. The Dashboard should borrow trust/freshness discipline from
serious portfolio tools while avoiding research-terminal, screener, holdings
grid, watchlist, fair-value, and market-terminal drift.

## Decision

The Dashboard should become a compact review-readiness cockpit, not a catalog
of demo cards. Its first viewport should answer:

1. Can I responsibly run a portfolio-aware manual trade review now?
2. What portfolio context and market-data limitations will affect that review?
3. What high-level portfolio risk or red-folder event needs attention before
   I review a trade?
4. Where do I begin a new review?
5. Is there real prior review activity worth returning to?

Phase 20C may remain as the current visual checkpoint, but additional
Dashboard wiring or visual expansion is not authorized by this memo.
Placeholder-heavy panels should not be treated as product progress merely
because a synthetic/demo read contract exists.

## First-Viewport Information Hierarchy

| Priority | Surface | User job | Display decision |
| --- | --- | --- | --- |
| 1 | Header and `New trade review` action | Start the core workflow immediately. | Keep. Use neutral workspace language unless safe profile data is approved. |
| 2 | Review-readiness summary | Understand whether analysis is available, limited, or blocked. | Keep, but prioritize review mode plus separate broker and market states over provider internals. |
| 3 | Portfolio context freshness | Know which portfolio snapshot will be used and whether it is stale. | Keep when backed by a reviewed user-facing contract. |
| 4 | Market-data availability and mode | Know whether market evidence is unavailable, synthetic, indicative, delayed, or later approved live. | Keep only with an explicitly display-authorized contract; Phase 22A evaluation data is not yet authorized for frontend display. |
| 5 | Private account summary | See total value, cash, stock/ETF exposure, options exposure, collateral/cash usage state, and portfolio-shape context needed for review. | Approved in principle for authenticated private display, but only through a reviewed backend display-label contract with privacy mode, freshness, valuation basis, and explicit caveats. |
| 6 | Recent reviews | Resume a real previous review. | Show only from safe persisted review history, not synthetic rows presented as activity. |
| 7 | Risk alerts | See actionable review-related deterministic warnings. | Show only when derived from real reviewed context or persisted reviews; avoid fabricated demo urgency. |

## Recommended First Viewport

The eventual private-alpha Dashboard first viewport should contain:

- A concise page header and prominent `New trade review` action.
- A plain-English readiness verdict above the supporting status tiles so the
  cockpit answers "can I review now?" in one glance.
- A single readiness band with distinct broker snapshot and market-data
  availability/freshness states, plus an overall analysis-only or blocked
  label.
- A compact portfolio summary panel using backend-owned display labels only,
  after `P20D-T1` defines and reviews the account-detail contract.
- A recent review panel, only after it is backed by persisted user review
  history.
- A limited warning area, only for deterministic warnings tied to an actual
  context or saved review.
- A secondary red-folder event surface only after a reviewed contract exists.
  Macro/economic events may live on the Dashboard as context; per-underlying
  earnings date belongs first in the trade-review/options context because it
  directly affects covered-call and cash-secured-put review quality.

Agent-provider status is operationally useful, but it should move off the
Dashboard first viewport. It may appear in Settings, Agent Console, or a thin
operator/status row once real product surfaces are available.

## Stock Rover Pressure-Test Decisions

Claude C's Stock Rover persona pressure test is advisory input. Codex A
ratifies the following product decisions:

| Decision | PM ruling | Rationale |
| --- | --- | --- |
| D1 - Product B positioning | Accept complement-not-replace. | Portfolio Copilot is the pre-trade portfolio-aware layer a research terminal lacks; it should not promise to replace a research/screener/analytics terminal. |
| D2 - Synthetic total-value policy | Accept. | Plausible fake headline dollars in `synthetic_demo` are a trust killer. Synthetic account summaries should default to hidden amounts or unmistakable placeholders such as "Connect a portfolio to see your value." |
| D3 - Real-source sequencing | Accept. | Real-source account summary plus broker freshness should precede persisted review history. Users can tolerate empty history; they cannot validate a decision cockpit on fake aggregates. |
| D4 - Market-data ceiling | Accept with beta distinction. | Indicative/manual pricing is acceptable for local/internal analysis-only demos, but external beta should plan a display-rights-cleared REST quote path for the underlying and specific option before implying quote-current review quality. |
| D5 - Earnings-date scope | Accept narrowly. | Per-underlying earnings date may enter review context without opening a generic company-news feed because it directly affects options review quality, especially covered calls and CSPs. |
| D6 - Agent-provider visibility | Accept. | `mock_default` or provider readiness reads as dev machinery to an investor. Keep it available operationally, but off the primary Dashboard viewport. |

Founder-gated follow-up decisions:

1. Whether complement-not-replace should become explicit external marketing
   copy or remain internal positioning.
2. Whether external beta requires a display-rights-cleared market quote path,
   or whether a narrower analysis-only beta is acceptable.
3. Which provider/source should supply per-underlying earnings date, and what
   licensing/display terms are acceptable before user-facing display.

## Current Panel And Contract Map

| Current or proposed panel | Current contract/readiness | Product decision |
| --- | --- | --- |
| New trade review action | Existing navigation/workspace behavior. | Keep now. |
| Broker snapshot readiness | Reviewed P20B readiness contract, currently `synthetic_demo`. | Keep for development preview; require real-source mapping before removing demo labelling. |
| Market quote readiness | Reviewed P20B readiness contract, currently `synthetic_demo` or unavailable. | Keep only as visibly demo/unavailable today. Do not surface Alpaca evaluation output from P22A-T4. |
| Agent provider readiness | Reviewed P20B readiness contract. | Move off first viewport; keep in Settings, Agent Console, or a thin operator/status row if needed. |
| Account summary: total value, cash, stock/ETF exposure, options exposure, collateral/cash usage, shape | Reviewed `DashboardAccountSummaryRead`, currently `synthetic_demo` display labels only. | Approved in principle for private authenticated display. Requires `P20D-T1` to refine the contract before real-source mapping or UI expansion. |
| Portfolio context summary | Reviewed P20B portfolio-context read contract, currently demo-labelled. | Useful supporting panel; real-source mapping needed before normal-product claims. |
| Recent trade reviews | Reviewed narrow read contract, currently synthetic/demo because preview runs are stateless. | Hide or clearly reduce in normal UX until persisted review source exists. |
| Risk alerts | Reviewed narrow read contract, currently synthetic/demo. | Hide or reduce until generated from real reviewed context or persisted reviews. |
| Quick review presets | Static navigation helpers. | Keep only if they prefill the corresponding reviewed flow or are clearly simple shortcuts. Remove dead-looking presets that navigate without context. |
| What's running | Derived readiness presentation, not a real live run feed. | Remove or defer from Dashboard; it duplicates readiness and implies activity. |
| Reports shortcut/list | No approved real user-facing report list/detail contract. | Defer. |
| Market overview/watchlist/options chain | No approved display contract and outside MVP cockpit. | Defer/out of scope. |
| Macro economic calendar / red-folder events | Reviewed contract required before normal display. | Allow only as secondary context with source/freshness and `is_trading_signal=false`; do not let it crowd review readiness. |
| Per-underlying earnings date | New narrow contract required. | Allow as a future review-context input for options flows; do not expand into generic ticker news or research feed. |
| Personalized greeting/avatar | Profile/auth contract blocked. | Use neutral copy until approved app-owned profile display exists. |

## What To Reduce Or Remove Before Further Expansion

When a later implementation task is authorized, the preferred cleanup is:

- Do not show synthetic recent-review rows as though the user has prior
  activity.
- Do not show synthetic risk-alert urgency as though it came from the user's
  portfolio.
- Do not show plausible synthetic headline account values as though they might
  be real. In normal product view, hide synthetic amounts or replace them with
  unmistakable non-real placeholders.
- Remove `What's running` unless a real, safe run-status contract exists.
- Avoid personalized greetings until an approved profile/display contract
  exists.
- Move agent-provider readiness off the first viewport.
- Promote the backend-owned readiness verdict above the supporting readiness
  tiles.
- Ensure quick-review presets either prefill a reviewed flow or are removed.
- Consolidate repeated `demo - not yet connected` surfaces into a clear demo
  environment state where practical, while preserving labels on any displayed
  synthetic values.

## Private User-Facing Information Boundary

Some information may be valuable on a private, authenticated user Dashboard
but remains prohibited from LLM or agent prompts by default.

| Candidate user-visible aggregate | Dashboard posture | Agent-prompt posture |
| --- | --- | --- |
| Backend-formatted total portfolio value label | Approved in principle after `P20D-T1` defines privacy mode, scope, freshness, and valuation basis. | Excluded by default. |
| Backend-formatted cash summary label | Approved in principle after `P20D-T1`; frontend renders backend labels verbatim. | Excluded by default. |
| Backend-formatted stock/ETF exposure label | Approved in principle after `P20D-T1`; no frontend calculation. | Excluded by default unless transformed into a separately approved agent-safe projection. |
| Backend-formatted options exposure label | Approved in principle after `P20D-T1`; no frontend calculation. | Excluded by default unless transformed into a separately approved agent-safe projection. |
| Backend-formatted collateral/cash usage label | Approved in principle after `P20D-T1`; must carry caveats and scope. | Excluded by default unless separately approved. |
| Position counts and safe portfolio shape | Already permitted in narrow sanitized contracts. | Only where an approved agent-safe projection permits it. |
| Broker and market freshness labels | Appropriate for user display. | Only approved freshness/actionability summaries, never raw provider/account context. |

This memo does not approve raw holdings, raw positions, quantities, raw cash
balances, buying power, raw account values, account/broker/provider
identifiers, provider payloads, account-specific thresholds, prompts, or LLM
traces for frontend display or agent use.

## Market-Data Display Boundary

`P22A-T4` validates an internal adapter mapping only. It does not authorize
Dashboard consumption of Alpaca-shaped data.

| Market-data condition | Dashboard decision |
| --- | --- |
| `synthetic` / `synthetic_demo` | May be used for development preview only with prominent demo labelling. |
| `indicative` plus `limited_source` | Evaluation-only until a separate frontend-display decision; if later approved, must display both limitations and remain analysis-only. |
| `delayed` | Not yet authorized for Dashboard; later display requires explicit delayed/as-of labelling and actionability review. |
| `unavailable` | May be displayed clearly as unavailable when supported by existing reviewed contracts. |
| `live` | Not authorized for product display until production provider/licensing/display-rights approval. |

Broker snapshot freshness, underlying quote freshness, option quote/chain
freshness, and IV/Greeks provenance must remain distinct.

## Ranked Backend Contract Needs

These are recommendations for later task approval, not implementation
authorization.

| Rank | Needed contract/source work | Why it matters | Dependency/gate |
| --- | --- | --- | --- |
| 1 | `P20D-T1` private Dashboard account-summary contract refinement. | Total value, cash, stock/ETF exposure, options exposure, collateral/cash usage, and portfolio shape are central to portfolio-aware review context. | Approved in principle; Codex C must refine the backend display-label contract before real-source mapping or frontend expansion. |
| 2 | Real-source readiness mapping for broker freshness and market-data availability/mode. | The Dashboard's primary promise is trustworthy review readiness, not demo status. | Market display must stay unavailable/demo until a display-authorized data source exists; no P22A-T4 frontend use. |
| 3 | Persistence-backed recent trade-review read source. | Makes recent-review return flow real instead of simulated. | Requires safe persistence mapping and opaque references; no raw review inputs. |
| 4 | Deterministic risk-alert source tied to an actual selected context or persisted review. | Alerts are valuable only when they are true and attributable. | Must avoid raw thresholds/private rule exposure and synthetic urgency. |
| 5 | Display-rights-cleared underlying and option quote snapshot path. | This lifts the external-beta ceiling for quote-current options review without building a market terminal. | Requires market-data provider/display-rights approval; REST snapshots only, no streaming/terminal. |
| 6 | Per-underlying earnings-date review context. | Earnings timing is a high-impact options review datum, especially for covered calls and CSPs. | Keep source/freshness visible; do not open generic ticker news feed. |
| 7 | Safe report list/detail reads. | Supports returning to completed review output. | Existing blocked P20B report decision remains required. |
| 8 | Minimal app-owned profile/display contract. | Supports greeting/avatar polish only. | Low product value; keep neutral copy until auth/profile boundary is approved. |

## What Claude A May Refine Visually Now

When Claude A is available, visual work may safely address:

- layout density and spacing of the existing Dashboard;
- hierarchy that elevates the start-review action and readiness band;
- reducing the prominence of duplicate/demo-only panels;
- clear visual distinction between broker freshness, market availability, and
  analysis-only state;
- empty/unavailable/demo presentation using existing fields only.

Claude A must wait for reviewed backend contracts before:

- showing real total value, cash, stock/ETF exposure, options exposure, or
  collateral/cash usage;
- replacing demo recent reviews with user history;
- presenting risk alerts as real user warnings;
- displaying Alpaca or other provider market data;
- enabling reports, market/news panels, profile-backed greeting, or any
  agent-console interaction.

## Decisions Requiring Founder Approval

1. Whether synthetic activity and risk panels should be hidden by default in
   private alpha rather than shown with repeated demo labels.
2. Whether later internal Dashboard display of `indicative` /
   `limited_source` market data is useful, or whether market data should remain
   invisible until a stronger provider path is approved.
3. Whether persisted review history or real account summary should be the
   first frontend follow-up after `P20D-T1`.

Resolved on 2026-05-26: private authenticated Dashboard display of
backend-formatted account-detail labels is approved in principle. The safest
first backend default is selected context or selected account scope; combined
portfolio display may be emitted only when clearly labelled and reviewed.

## Non-Goals

- No frontend or backend implementation.
- No endpoint, schema, or persistence authorization.
- No provider/API call or provider-selection decision.
- No Agent Console activation.
- No advice, execution, screening, watchlist, or brokerage-mirror expansion.
