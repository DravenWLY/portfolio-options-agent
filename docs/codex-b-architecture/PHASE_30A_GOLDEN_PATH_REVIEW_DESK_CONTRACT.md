# Phase 30A - Golden Path Review Desk Contract

Owner: Codex B
Status: accepted prototype checkpoint
Date: 2026-06-22

## Product Position

Portfolio Copilot is a read-only specialist review desk for busy
self-directed investors. The app does not answer whether a user should make a
trade. It answers:

> What would I be ignoring if I acted manually now?

The Phase 30A goal is to make the first complete loop feel coherent and useful:

1. Select a review account and portfolio scope.
2. Enter a proposed stock/ETF or simple options trade.
3. Run backend-owned deterministic Trade Review.
4. Save an immutable evidence snapshot.
5. Explicitly generate an Agent Team briefing from that saved package.
6. Reopen the saved report later with the same historical scope, evidence, and
   report state.

## P30A Prototype Scope

P30A should prove one narrow, high-fidelity product loop before any more
horizontal expansion.

Approved prototype flows:

- One stock/ETF review flow, using the existing `stock_buy`, `stock_sell_trim`,
  `etf_buy`, or `etf_sell_trim` contracts.
- One simple options review flow, preferably `cash_secured_put` or
  `covered_call`.

Approved evidence:

- Existing deterministic Trade Review output.
- Saved scope metadata, caveat codes, and freshness labels.
- Broker snapshot freshness and market quote freshness as separate scopes.
- Existing portfolio-impact and account-readiness sections in
  `SavedEvidencePackageRead`.
- Existing EDGAR `public_company_profile` evidence when already available in
  the saved package.
- Market Mood / Economic Awareness only as existing reviewed saved-evidence
  availability states; do not feed them to agents by default unless the existing
  saved package already contains approved reviewed sections.

Out of scope:

- New public evidence sources or providers.
- Broader EDGAR expansion, filing bodies, XBRL facts, news, or classification
  normalization.
- Runtime TradingAgents, web search, MCP tools, EDGAR tools, or broker tools.
- Agent Console composer or interactive agent chat.
- Frontend financial calculations.
- Auto-generation after save.
- Order entry, order staging, broker execution, cancellation, transfers, or
  broker account-management flows.
- Advice, recommendation, buy/sell/hold conclusions, safe-to-trade,
  ready-to-trade, or guaranteed-return wording.

## Existing Contract Spine

The current code already contains the core spine:

- `POST /trade-reviews/portfolio-preview` returns backend-owned deterministic
  review output and records a save-eligible reviewed source when scope metadata
  is available.
- `POST /users/{user_id}/reports/from-trade-review` saves an immutable review
  artifact from the backend-owned reviewed source. The frontend sends only
  `source_kind`, `source_reference`, `title`, and `report_type`.
- `SavedEvidencePackageRead.from_saved_review_artifact(...)` derives the
  approved evidence package from the saved artifact, not from current account
  selectors.
- `POST /users/{user_id}/reports/{thread_id}/agent-team-report` explicitly
  generates an Agent Team report from the saved artifact.
- `generate_agent_team_report_for_thread(...)` uses the same
  `SavedEvidencePackageRead` instance for role projection, package-aware
  validation, and persistence.
- `GET /users/{user_id}/reports` and
  `GET /users/{user_id}/reports/{thread_id}` read saved scope, Agent Team
  summary, report timestamps, and reviewed public-evidence attribution without
  recomputing from current account state.

P30A should prefer this existing spine. New fields or endpoints require a
specific Codex B contract/privacy review and should be avoided unless the gap
audit proves they are necessary.

## Key Product Gaps To Close

P30A is mostly choreography and fidelity, not a new backend architecture.

Known gaps:

- Trade Review can save a snapshot, but the path from deterministic review to
  saved briefing should feel like one intentional workflow.
- Reports should feel like the destination artifact for the review loop, not a
  detached library.
- The selected review account and broader portfolio scope are present, but the
  golden path must verify that they stay visibly frozen from review through
  saved report readback.
- Stock/ETF plus one simple options flow must be verified end to end with
  private-safe fixtures.
- Agent Team wording should be shaped around ignored risk/context/data gaps,
  not verdicts or actionability conclusions.

## Safety And Privacy Requirements

- Deterministic backend services own calculations.
- Frontend renders reviewed backend fields only.
- Saved reports must not silently recompute from current account state.
- Agent Team must consume only approved structured saved evidence.
- Raw private account data must not enter frontend contracts, generated report
  prose, prompts, traces, logs, screenshots, or docs.
- Account labels/scope labels must not be sent into Agent Team evidence unless
  a reviewed backend contract explicitly permits a lossy/sanitized summary.
- Public evidence remains source-rights-governed and frozen at generation time.
- Any provider failure degrades honestly without breaking deterministic review.

## P30A Task Sequence

### P30A-T0 - Golden Path Contract And Acceptance Criteria

Owner: Codex B
Status: done in this document

Define the product loop, approved evidence, out-of-scope work, review gates, and
acceptance criteria.

### P30A-T1 - Backend Golden Path Gap Audit

Owner: Codex C
Reviewer: Codex B

Verify that one stock/ETF flow and one simple options flow travel end to end:
portfolio-backed preview -> saved source -> saved artifact -> saved evidence
package -> Agent Team generation -> report list/detail readback ->
regeneration/retry.

This task should identify gaps before implementing any new fields.

### P30A-T2 - Agent Team Briefing Shape

Owner: Claude E
Reviewer: Codex B

Design the specialist-team briefing language around the question "what would I
be ignoring?" Use existing saved evidence only. Preserve role separation and
manual decision-support posture.

### P30A-T3 - Trade Review Golden Path UX

Owner: Claude A or Codex F
Reviewer: Claude B visual/safety, Codex B only if contracts/copy semantics
change

Make the deterministic review -> save snapshot -> generate/open briefing path
clear and calm. Generation remains explicit.

### P30A-T4 - Saved Report Briefing Polish

Owner: Claude A
Reviewer: Claude B visual/safety, Codex B contract/privacy/safety

Refine Report Detail as the flagship saved specialist briefing: synthesis first,
role-separated flags, deterministic facts and provenance beneath, saved scope
and timestamps prominent.

### P30A-T5 - Private-Safe End-To-End Smoke

Owner: Codex F, with Codex C if fixture changes are required
Reviewer: Claude B visual/safety and Codex B privacy/safety if fixtures or
contracts change

Run the complete golden path for the chosen stock/ETF and options examples using
reviewed synthetic/private-safe fixtures only.

### P30A-T6 - Founder Acceptance And Closeout

Owner: Codex B and Codex A

Close only when the full loop is understandable, reproducible, and safe.

## Acceptance Criteria

P30A is accepted when:

- A user can complete the golden path for one stock/ETF and one simple options
  flow without leaving the app.
- The flow never implies the app is placing, preparing, or recommending a trade.
- The saved report reopens from frozen historical evidence and report state.
- Scope, freshness, caveats, and provenance remain visible and honest.
- Agent Team content cites only available reviewed evidence and degrades
  honestly when sections are missing.
- No new provider/source expansion is required.
- Private-safe connected smoke passes for the full loop.

## PRD / Positioning Follow-Up

Codex A should update PRD, MVP scope, and positioning language from a narrow
"pre-trade review" framing toward:

> Read-only specialist review desk for busy self-directed investors.

The core promise should be:

> What would I be ignoring if I acted manually now?
