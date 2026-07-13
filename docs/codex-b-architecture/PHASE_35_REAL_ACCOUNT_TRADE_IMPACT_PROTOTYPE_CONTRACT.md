# Phase 35 - Real-Account Trade-Impact Working Prototype Contract

Status: accepted (founder decisions recorded 2026-07-08)
Owner: Claude G - Architecture / Contract / Privacy
Supersedes the P34A "working prototype" bar: the founder reviewed the first
structured live report (P34A-T18) and rejected it as not working. This phase
defines what "working" means and sequences the backend work. **No frontend
work starts until the founder accepts the backend prototype.**

## Founder's working-report definition (all four required)

1. **Trade-centered.** The report analyzes the proposed trade itself - what
   happens to the portfolio if it proceeds - not just the symbol's prices
   and indicators.
2. **Account-aware.** The analysis uses the real reviewed account: current
   positions, exposure before/after the trade, and overlap (the canonical
   example: holding SMH and buying NVDA means doubled semiconductor and
   NVDA exposure).
3. **Human-readable.** Raw caveat codes, variable names, snake_case tokens,
   and internal status strings are PROHIBITED in user-visible report prose.
   Everything renders as plain language.
4. **Well-formatted.** Clear titles, subtitles, complete paragraphs, and
   tables; markdown as the canonical report format (graphs later, once the
   frontend displays markdown).

## Founder decisions recorded (2026-07-08)

- **D1 - Test account:** the real Fidelity account is selected ONLY by its
  app nickname, `Fidelity Individual`. Account numbers, provider IDs, and
  raw broker identifiers are never used for selection, display, or logging.
- **D2 - Report content boundary (internal prototype):** derived portfolio
  values MAY appear in generated reports as both percentages and dollar
  amounts (e.g. "adds $8,400 of NVDA exposure"). Still banned everywhere:
  account numbers, provider/broker IDs, credentials, secrets, raw provider
  payloads. Test artifacts containing real derived values stay local and
  gitignored - never committed, never pasted into docs/tests/fixtures.
- **D3 - Agent access:** Claude G may read finished reports and derived
  intermediate values (exposure percentages, overlap weights, dollar
  deltas) while testing/debugging; never raw broker payloads, DB rows,
  identifiers, or credentials.
- **D4 - Standard test trade:** buy NVDA (against the SMH-holding account,
  the founder's double-exposure example).
- **D5 - Frontend gate:** P34A-T14 and all frontend report work are gated
  on founder acceptance of the backend prototype.
- **D6 - Data granularity v1:** FMP ETF constituent endpoints returned
  HTTP 402 (restricted tier) on 2026-07-08. v1 computes exposure at sector/
  industry level using free-tier classification endpoints (company profile
  sector/industry; ETF classification), which covers the SMH+NVDA example
  qualitatively. Constituent-level look-through ("SMH holds N% NVDA") is a
  named v2 decision: FMP paid plan or an alternative reviewed source.

## Standing boundaries (unchanged)

Deterministic backend Python owns every calculation; LLM roles receive only
sanitized envelopes and never compute or adjust numbers; all P33A/P34A
validators and gates stay; no order placement or advice/verdict wording;
saved reports reopen frozen state; live provider/data calls stay explicitly
gated and mock/offline by default; TradingAgents stays reference-only.

## Task sequence

- **P35-T1 - Trade-impact methodology consult.** Owner: Claude H.
  Deliverable: a written methodology memo (see prompt in plan handoff)
  covering exposure decomposition, overlap detection with and without
  constituent data, before/after deltas, concentration thresholds worth
  naming, and what a genuinely useful trade-impact section must say.
- **P35-T2 - Human-readable rendering + display-token ban.** Owner: Codex C.
  Reviewer: Claude G. Independent of T1. A reviewed label layer maps every
  caveat/status/section code to plain language at report-rendering time,
  and a fail-closed display validator rejects snake_case/internal tokens in
  user-visible prose fields of generated reports.
- **P35-T3 - Deterministic exposure engine v1.** Owner: Codex C. Reviewer:
  Claude G. After T1. Sector/industry exposure decomposition of the saved
  real-account snapshot; before/after deltas for the proposed trade; direct
  same-symbol overlap; ETF sector classification; dollar + percentage
  outputs; unit-tested against hand-checked fixtures; populates the
  existing before_after_portfolio_impact and concentration_risk_drift
  evidence sections with human-readable content.
- **P35-T4 - Report contract v4: trade-centered narrative.** Owner:
  Claude E. Reviewer: Claude G. After T1. Reframes role reports and PM
  synthesis around the proposed trade; weaves trade intent, exposure
  deltas, and market context into titled sections with complete paragraphs
  and tables; markdown canonical; extends the numeric gate to the new
  derived values; keeps every safety gate.
- **P35-T5 - v4 implementation.** Owner: Codex C. Reviewer: Claude G.
- **P35-T6 - Real-account gated run and founder read.** Owner: Claude G with
  founder authorization per run. Nickname-selected account, buy-NVDA
  preview, generated report delivered to the founder for the acceptance
  read against the four criteria.
- **P35-T7 - Constituent look-through decision.** Owner: founder (paid FMP
  plan vs alternative source vs defer).

## Block conditions

Block any implementation that selects accounts by number/ID, persists raw
broker payloads into reports, commits real-derived-value artifacts, exposes
internal tokens in user prose, lets the LLM compute portfolio math, starts
frontend work before founder acceptance, or weakens existing gates.
