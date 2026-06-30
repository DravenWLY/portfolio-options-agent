# Portfolio Copilot PRD

Status: PM draft approved for product alignment
Owner: Codex A - Product / Founder Strategy / PM
Last updated: 2026-06-23

## Product Summary

Portfolio Copilot is a read-only specialist review desk for busy
self-directed investors. It is TradingAgents-inspired, not
TradingAgents-centered: the product center remains broker-aware `TradeIntent`
review and saved Agent Team briefing, not one-shot ticker research or automated
trading.

Before a user manually places a stock, ETF, covered call, or cash-secured put
trade in their broker, the app helps answer: "What would I be ignoring if I
acted manually now?" It reviews a proposed `TradeIntent` against the user's
portfolio snapshot, cash/collateral state, concentration exposure, assignment
or call-away exposure, risk rules, and data freshness. Deterministic services
calculate the facts; AI may explain only approved structured outputs and public
evidence.

Portfolio Copilot is complement-not-replace relative to serious investor
research and portfolio tools such as Stock Rover. Those tools help users
research, screen, track, and monitor. Portfolio Copilot's narrower promise is
the review-desk layer those tools usually lack: what a specific manual trade
would do to the user's portfolio, what data or context may be stale or missing,
and what should be manually verified before the user acts elsewhere.

The user-facing agent experience is framed as a specialist review team for
self-directed investors. The team helps the user review proposed trades,
understand portfolio risk, and manage their own portfolio decisions with clearer
evidence, freshness context, and analysis-only explanations. It does not manage
the portfolio for the user, recommend trades, allocate assets, place orders, or
decide what the user should buy or sell.

The current accepted implementation state is an internal validation prototype,
not a public MVP or commercial beta. P30A/P30B proved the golden path:
`Trade Review -> save evidence snapshot -> Reports -> explicitly generate Agent
Team briefing -> reopen saved report`. P31A polishes the founder demo narrative
around that loop without expanding product scope.

## Target User

The first target user is a busy active self-directed retail investor who
manages stocks, ETFs, and simple single-leg options across one or two brokerage
accounts. They may have limited time during market hours to monitor market
moves, company context, macro events, portfolio exposure, cash/collateral, and
data freshness. They are comfortable making their own trade decisions, but want
a portfolio-aware specialist briefing before manually acting in their broker.
The first wedge is users considering covered calls and cash-secured puts,
because those trades make collateral, assignment, coverage, concentration, and
stale-data risks easy to see.

The first target user is not:

- A passive investor looking only for a portfolio tracker.
- A trader looking for automated execution.
- A user looking for an options-income screener or wheel-strategy app.
- A user looking for AI stock picks.
- A financial advisor workflow buyer.

## Core Job

When I am considering a manual trade, help me understand what I might be
ignoring if I acted now: what changes in my portfolio, what risk rules or
caveats appear, what evidence is available or missing, what data is fresh or
stale, and what I need to confirm before acting in my broker.

## MVP Promise

The first useful internal validation prototype lets a user load or maintain a
portfolio snapshot, enter a proposed manual trade, save the reviewed evidence
snapshot, explicitly generate an Agent Team briefing, and reopen the historical
saved report. The deterministic review remains the evidence foundation and must
answer:

- How does this affect cash, collateral, and free cash?
- How does this affect stock/ETF concentration and allocation?
- For covered calls, what is the call-away exposure and is coverage modelled?
- For cash-secured puts, what is the assignment and collateral exposure?
- Which deterministic risk rules are violated or close to violation?
- Are broker positions, cash, option positions, and market quotes fresh enough for the output to be treated as more than analysis-only?

## Required MVP Flows

### 1. Portfolio Snapshot Setup

Users can review a portfolio snapshot from one of these sources:

- Read-only SnapTrade broker sync where available.
- Manual portfolio entry.
- CSV fallback for supported synthetic or user-provided exports.

The app must show portfolio snapshot provenance and freshness. Manual and CSV inputs are acceptable for local MVP and early beta, but must be labeled as user-provided snapshots rather than live broker state.

### 2. Equity Trade Review

The user can enter a proposed stock or ETF buy, sell, add, or trim review. The app calculates estimated cash impact, position change, allocation drift, concentration impact, and risk-rule status.

The product may use one generic "stock/ETF review" UX for MVP. It should not overbuild ETF-specific research or portfolio optimization.

### 3. Covered Call Review

The user can enter a single-leg covered call candidate against an existing stock position. The app reviews coverage assumptions, call-away scenario, premium assumptions, concentration impact, and freshness status.

If coverage-aware netting is incomplete, the product must explicitly caveat that coverage/collateral netting is not fully modelled before exposing the flow as a polished frontend feature.

### 4. Cash-Secured Put Review

The user can enter a single-leg cash-secured put candidate. The app reviews cash collateral, free cash after collateral, assignment exposure, breakeven assumptions, concentration after hypothetical assignment, and freshness status.

If existing collateral netting is incomplete, the product must explicitly caveat that collateral netting is not fully modelled before exposing the flow as a polished frontend feature.

### 5. Saved Agent Team Briefing

The app produces a saved review/report with deterministic metrics, freshness
state, risk-rule violations, evidence/provenance, and Agent Team synthesis when
generated. The briefing is the primary user-facing report experience when
available; deterministic facts remain the supporting evidence and audit layer.
The report must avoid directive advice and execution language.

## Freshness And Actionability

Portfolio Copilot must separate:

- Broker snapshot freshness: holdings, cash, option positions, collateral, broker sync status.
- Market quote freshness: stock quotes, option quotes, Greeks, IV, data mode, quote timestamp.

If either broker snapshot freshness or market quote freshness is stale, unknown, error, manual-only, or EOD-only, the review must not be labeled immediately actionable. The output may be shown as analysis-only with explicit confirmation language.

Approved language:

- "Based on portfolio snapshot received at [time]."
- "Analysis-only: holdings, cash, collateral, or option positions may have changed."
- "Refresh or confirm your brokerage account before placing any manual trade."
- "Market quote freshness is separate from broker portfolio freshness."
- "This is scenario analysis for a manual decision outside the app."

Avoided language:

- "Safe to trade."
- "Ready to trade."
- "You should buy/sell."
- "Live portfolio" unless provider-verified.
- "Fully covered" or "cash secured" unless deterministic modelling and freshness policy support the claim.
- "Guaranteed return."

## Deterministic vs AI Boundary

Deterministic backend services own all financial calculations, including cash impact, collateral, coverage, payoff/scenario outputs, breakeven assumptions, allocation drift, concentration, assignment exposure, call-away exposure, freshness classification, and risk-rule violations.

AI may:

- Explain structured deterministic outputs.
- Summarize tradeoffs already present in structured data.
- Compose educational reports.
- Ask review questions for the human user.

AI must not:

- Invent financial metrics.
- Recompute metrics from raw broker data.
- Receive raw holdings, account values, cash balances, broker account ids, trade journal entries, account-specific thresholds, or provider raw payloads by default.
- Produce order instructions or financial advice.

## Specialist Review Team

Approved MVP/private-alpha user-facing persona labels:

| UI label | Role in the product | Evidence boundary |
| --- | --- | --- |
| Fundamentals Analyst | Reviews approved public company/fundamental evidence. | Public only. |
| News Analyst | Reviews approved public news, macro, and event context. | Public only. |
| Technical Analyst | Reviews approved public market/technical context and must state when data is unavailable. | Public only. |
| Risk Manager | Explains portfolio risk, concentration, collateral, assignment/exercise, and freshness issues from sanitized deterministic evidence. | Agent-safe deterministic projection only. |
| Portfolio Manager | Synthesizes the team's analysis for the user's review. | Agent-safe synthesis only. |

The UI should not append "Agent" to these labels. Backend role keys may remain
unchanged unless a separate back-compat task approves a machine-key rename.

Required Portfolio Manager guardrail copy:

"Synthesizes the team's analysis for your review — does not manage your
portfolio or recommend trades."

If user testing or compliance review shows fiduciary confusion, approved
fallback labels are `Portfolio Lead`, then `Portfolio Synthesis` /
`Review Synthesizer`. Avoid `Portfolio Strategist` because it implies strategy
recommendation.

## MVP Non-Goals

- Automatic trading, order placement, order cancellation, or broker order management.
- Broker disconnect/delete flows in MVP UX.
- Broker scraping, Fidelity credential storage, or MFA bypass.
- Option-chain browser or market-data terminal.
- Research terminal, screener, watchlist, holdings-grid cockpit, fair-value
  rating surface, or Stock Rover replacement.
- Options-income screener, wheel lifecycle app, or CSP/covered-call screener as the product center.
- AI stock picking.
- Thin TradingAgents wrapper.
- Advanced options strategies such as spreads, collars, rolls, diagonals, iron condors, or multi-leg optimization.
- Public SaaS auth, billing, mobile app, PDF export, OPRA redistribution, or production compliance launch.

## Product Acceptance Criteria

The MVP is useful when:

- A user can complete the golden path from portfolio-backed Trade Review to
  saved evidence snapshot, explicit Agent Team briefing generation, and reopened
  saved report.
- The report explains portfolio impact, cash/collateral impact, assignment or
  call-away exposure, concentration impact, risk-rule violations, evidence
  limitations, and manual verification points.
- Stale, unknown, manual, EOD-only, or provider-error inputs cannot produce action-ready language.
- Broker freshness and market quote freshness are displayed separately.
- AI/Agent Team explanation is optional, explicit, and grounded in approved
  structured saved evidence.
- The app remains clearly read-only and manual-decision-support only.

## PM Decisions

- First target segment: active self-directed retail investors using stocks, ETFs, covered calls, and cash-secured puts manually.
- First useful wedge: a portfolio-aware specialist review desk for proposed
  manual trades, not brokerage dashboarding, screening, or trade execution.
- Next implementation gate: Portfolio Snapshot Actionability Policy before polished Phase 16 agent outputs.
- Phase 16 should be split into Phase 16A deterministic agent components and Phase 16B portfolio-aware agent-team orchestration.
- TradingAgents is optional public ticker/company research evidence, not the final portfolio-aware decision engine.
- Market-data provider selection is under staged evaluation. Indicative/manual
  pricing is acceptable for local/internal analysis-only demos, but external
  beta should plan a display-rights-cleared backend REST snapshot path for the
  underlying and specific option before implying quote-current review quality.
  WebSocket/streaming market data is deferred.
- MVP trade-review surface: equity buy/sell/trim, single-leg covered call, and single-leg cash-secured put.
- Long calls and long puts may exist in backend capability but are not first MVP UX priorities.
- Dashboard positioning: compact review-readiness cockpit, not broker
  dashboard, research terminal, market terminal, screener, or AI
  recommendation feed.
- Per-underlying earnings date is approved as a narrow future review-context
  input for options flows, but generic company-news feeds remain deferred.

## Handoff

Codex B Architecture should translate this PRD into actionability/readiness contracts and ADRs where decisions affect cross-layer boundaries.

Codex C Backend should implement only approved vertical slices using synthetic tests and should not continue polished agent output work until the portfolio snapshot actionability gate is accepted.

Claude A Frontend should wait for backend contracts before building a trade review workspace, then design around freshness, analysis-only states, deterministic results, and read-only manual decision support.
