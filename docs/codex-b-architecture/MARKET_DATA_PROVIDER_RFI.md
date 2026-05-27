# Market Data Provider Request For Information

Status: parked reference template - no provider selected or outreach authorized
Date: 2026-05-25
Owner: Codex B - Architecture / Systems / Integration

## Purpose

Portfolio Copilot is evaluating commercially suitable U.S. equity and
listed-options market-data providers for a read-only, portfolio-aware trade
review product. This RFI is intended to be sent with the same questions to
Intrinio, Databento, dxFeed, and optionally Massive.

This document is not a selection, procurement commitment, or authorization to
integrate any provider.

Codex A parked commercial vendor outreach on 2026-05-26. Retain this template
for later commercial-scale planning only; do not send it or begin negotiation
without a future PM reactivation decision.

## Product Use Case

Portfolio Copilot lets a user submit a hypothetical stock, ETF, covered-call,
or cash-secured-put trade for deterministic analysis against an app-owned
portfolio context. The application does not route, place, or manage orders.

Potential market-data uses include:

- backend retrieval of stock/ETF underlying quote snapshots;
- backend retrieval of selected listed-option quotes and option chains;
- deterministic calculations and risk-review inputs;
- external user display of approved quote timestamps, data-source/mode labels,
  and selected derived review summaries;
- retention of a bounded snapshot sufficient for reproducible review reports;
- possible future use of sanitized market-derived evidence in LLM analysis,
  subject to separate product, privacy, and security approval.

## Requested Response Format

Please answer each question for:

- trial/evaluation use;
- private alpha use;
- paid beta use;
- production use with hundreds of end users;
- production use with thousands of end users.

Please identify any separate agreement, exchange approval, entitlement,
reporting, audit, or end-user classification requirement.

## 1. U.S. Equity Quote Coverage

1. Which U.S. stock and ETF quote feeds are included?
2. Does coverage include consolidated CTA/UTP/SIP data, or is it limited to
   particular exchanges/venues?
3. Which realtime, delayed, indicative, snapshot, and historical modes are
   available?
4. Which fields are provided for quote snapshots: bid, ask, last, NBBO, mark,
   trade timestamp, quote timestamp, exchange/venue, market status?
5. May the application display those fields or derived labels to external
   paying end users?
6. May the application use those fields in backend deterministic
   calculations for portfolio-aware trade review?

## 2. U.S. Listed-Options Coverage

1. Is listed-options coverage OPRA-derived and consolidated across U.S.
   options exchanges?
2. Which quote modes are available: realtime, delayed, indicative,
   historical/replay, or snapshot-only?
3. Are expirations, option contract definitions, chains, and selected
   contract quote endpoints included?
4. Which fields are included: NBBO, bid, ask, last, mark, volume, open
   interest, quote timestamp, trade timestamp, underlying quote?
5. Are implied volatility and Greeks included?
6. If IV or Greeks are included, are they provider-derived, exchange-derived,
   calculated by your system, or supplied by another licensed source?
7. Are adjusted, mini, weekly, index, or non-standard contracts covered and
   identified in a way suitable for manual-review guardrails?

## 3. Commercial And Product Rights

1. May Portfolio Copilot display quote/chain fields to external paying users
   in a read-only trade-review workflow?
2. May it show derived deterministic metrics or summaries computed from the
   data, such as analysis results, freshness/status labels, or risk-review
   outputs?
3. May it use data solely in backend deterministic calculations even when raw
   quote fields are not displayed?
4. May it retain bounded quote/chain snapshots to reproduce a previously shown
   review/report? If so, for how long and in what form?
5. May it show historical report snapshots after the underlying quote data is
   no longer current?
6. If separately approved in a future product phase, may sanitized
   market-derived evidence or summaries be included in an LLM analysis prompt
   or output? Please distinguish raw data, derived data, and non-displayed
   internal processing rights.
7. Are screenshots, exports, report sharing, or downloadable reports subject
   to separate rights?

## 4. Licensing And Compliance

1. What OPRA, CTA, UTP, SIP, exchange, or other entitlement fees apply?
2. Which fees are included in your pricing and which are pass-through?
3. Are there per-user, per-device, per-query, per-symbol, per-connection, or
   redistribution fees?
4. How must non-professional and professional users be classified and
   reported?
5. What user agreements, attestations, audit records, or display notices are
   required?
6. What usage reporting is required from the application operator?
7. Do trial or evaluation terms prohibit user display, retention, derived
   calculations, or commercial product testing?
8. Are there geographic, customer-segment, or application-type limitations?

## 5. Engineering Capabilities

1. Which REST snapshot endpoints support underlying quotes, option
   expirations, chains, and selected option quotes?
2. Which streaming mechanisms are available if a future reviewed use case
   justifies them?
3. What rate limits, concurrency limits, symbol/contract limits, and chain
   request limits apply at each commercial stage?
4. Are historical or replay data available for deterministic testing and report
   reproducibility?
5. How are timestamps, delayed/indicative/live modes, market status, and data
   corrections represented?
6. What are your outage, partial-data, retry, incident-notification, and SLA
   practices?
7. Are sandbox, mock, trial, or delayed datasets available without production
   credentials?
8. What client libraries or API versions are maintained, and what are your
   deprecation practices?

## 6. Commercial Scaling

Please provide pricing structure and minimum commitments for:

1. Internal evaluation with synthetic/replay tests and a small number of
   authorized developers.
2. Private alpha with a limited number of invited end users.
3. Paid beta.
4. Production with hundreds of end users.
5. Production with thousands of end users.

Please include:

- platform/base fees;
- exchange/entitlement/pass-through fees;
- per-user or per-device charges;
- API/request/streaming usage charges;
- professional/non-professional impacts;
- minimum term and cancellation terms;
- support/SLA tier costs.

## 7. Provider Response Checklist

Please attach or link to:

- applicable market-data licensing agreements;
- exchange/OPRA entitlement documentation;
- redistribution/display terms;
- retention and derived-use terms;
- API field/endpoint documentation;
- rate-limit and SLA documents;
- trial limitations;
- a representative pricing proposal.

## Internal Evaluation Notes

The Portfolio Copilot team will evaluate responses against these non-negotiable
boundaries:

- Market data must remain separate from broker portfolio freshness.
- Deterministic backend services own financial metrics.
- Raw provider payloads and credentials are not frontend or LLM prompt inputs.
- No product surface may describe indicative, delayed, stale, or unavailable
  data as live/current quote truth.
- Future sanitized agent-evidence use is not authorized merely by selecting a
  market-data provider.
