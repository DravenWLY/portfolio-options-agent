# Phase 36 - NOW Public-Evidence Source Investigation

Status: blocked for the NOW five-agent acceptance case pending a rights-approved
260-bar OHLCV source.

Owner: Codex E (architecture/source-rights research)

Date: 2026-07-17

Related: `PHASE_36_FIVE_AGENT_ACTIVATION_CONTRACT.md`,
`PHASE_36_T7_SOURCE_READINESS_AND_ETF_EVIDENCE_CONTRACT.md`, and
`EXTERNAL_API_LIMITS.md`.

## 1. Scope And Fixed Constraints

This investigation covers only the confirmed `operating_company_equity` NOW
acceptance case. It does not change the ETF path, call a provider, use a key,
inspect environment files, run a report, or authorize implementation.

The acceptance contract continues to require all of the following before a
five-agent generation may begin:

- SEC company-profile and recent-filings metadata;
- statement fundamentals for income statement, balance sheet, and cash flow;
- a frozen technical window with at least 260 normalized daily OHLCV bars; and
- zero provider calls on generation after preparation, regeneration, or report
  readback.

The observed FMP `402 Payment Required` result means the configured project
cannot serve its required EOD or three statement endpoints for NOW. It is an
honest source-access failure, not an invalid-symbol result. The 260-bar
requirement remains binding: recent-100 data cannot be substituted.

## 2. Decision

**Recommended direction: D. BLOCKED.**

There is a credible no-key, public primary source for statement facts (SEC
Company Facts), but there is no currently rights-approved *free-tier* source
that can serve and permanently freeze the required 260-bar OHLCV evidence for a
user-readable five-agent report.

- Alpha Vantage fails the free-tier technical requirement: its free daily
  `compact` response is 100 points; the 20+ year `full` response is premium.
  Its terms also classify investment analysis, research, testing, and monitoring
  beyond personal use as commercial use requiring a separate agreement.
- Twelve Data can technically return the needed daily history, but its Basic
  plan is expressly for internal non-display usage. Its individual plans forbid
  commercial display to third parties and redistribution. The current frozen
  report contract displays technical evidence and persists normalized bars for
  readback, so it cannot be treated as approved without written provider
  confirmation covering that exact use.

Do not silently switch the NOW run to either provider. The FMP plan/access
change remains a possible later product decision, but it is not a free-tier
replacement and must independently confirm display, retention, and statement
endpoint rights.

## 3. Provider Comparison

| Source | 260-bar daily OHLCV | Fundamentals groups | Free-tier limit | NOW support in principle | Rights conclusion | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Current FMP account | No: observed `402` on required EOD endpoint | No: observed `402` on all three required statement endpoints | Plan entitlement unknown; existing key cannot serve this case | Yes as a symbol category, but inaccessible for this account | Existing internal-evaluation contract does not override actual plan access or display licensing | Reject for current NOW run |
| Alpha Vantage | No on free tier: `TIME_SERIES_DAILY compact` is 100 bars; `full` is premium | API documents income statement, balance sheet, and cash flow | Up to 25 free requests/day for the majority of datasets | Global-equity API documentation makes NOW plausible; no source call was made | Terms require written commercial agreement for this app's investment-analysis/testing use | Reject |
| Twelve Data Basic | Technically yes: daily `time_series` supports bounded history and up to 5,000 rows/request | Not selected; its statement endpoints are high-credit and unnecessary if SEC facts are adopted | 8 API credits/minute; 800/day; `time_series` is documented as one credit/symbol | US equities are included in Basic; exact NOW entitlement remains unverified without an authorized smoke | Basic is internal non-display; individual plans prohibit commercial display to third parties and redistribution | Do not approve without written rights clarification |
| SEC EDGAR Company Facts | No OHLCV | In principle, yes, through normalized SEC XBRL company facts | No API key or published daily quota; existing app guardrail is 1 request/second and 60/day | Yes for a SEC-reporting issuer resolved to an existing CIK; exact concept mapping remains unverified | Public primary source, but current product contract explicitly permits EDGAR metadata only | Candidate for a new fundamentals lane only |
| yfinance/Yahoo | Technically can retrieve history but is not an approved provider contract | May expose statement-like fields but is not an approved primary statement lane | No stable, official service entitlement for this use | Not evaluated | yfinance says it is unaffiliated with Yahoo and intended for research/education; Yahoo terms restrict non-commercial/high-volume use without consent | Rejected comparison |

### 3.1 Alpha Vantage

Alpha Vantage documents the required statement endpoints:
`INCOME_STATEMENT`, `BALANCE_SHEET`, and `CASH_FLOW`. Those endpoints return
annual and quarterly reported statements, so they could technically supply the
three statement groups after normalization. The documented free allowance is up
to 25 requests per day, which would make a four-call acquisition sequence
(daily history plus three statements) arithmetically small.

That arithmetic does not create a viable path. For daily OHLCV, the free
`compact` response has only 100 data points, while `outputsize=full` is a
premium capability. The required 260 bars cannot be obtained through the free
documented route. More importantly, Alpha Vantage's terms define the app's
investment-analysis, research, testing, and monitoring use as commercial unless
otherwise agreed in writing. A free key is therefore not source-rights approval
for Portfolio Copilot.

- Identification only: a future adapter would require
  `ALPHA_VANTAGE_API_KEY`; no new environment variable is authorized here.
- Required normalized fields if separately licensed: `symbol`, `bar_date`,
  `open`, `high`, `low`, `close`, `volume`, provider/source key and label,
  source as-of/collection timestamps, freshness category, and caveat codes.
- Per-package behavior if ever approved: one EOD acquisition before the
  evidence freeze; no EOD call on role retries, generation, or readback. Four
  calls per fresh package if Alpha Vantage also supplies all three statements.
- Safe failure codes: `source_subscription_required`,
  `source_rate_limited`, `source_rights_not_approved`,
  `ohlcv_insufficient_history`, `ohlcv_missing_required_field`, and
  `provider_unavailable`.

Official sources: [Alpha Vantage documentation](https://www.alphavantage.co/documentation/),
[free-tier support](https://www.alphavantage.co/support/), and
[terms of service](https://www.alphavantage.co/terms_of_service/).

### 3.2 Twelve Data

Twelve Data documents a daily `time_series` route with `start_date` and
`end_date`, and says a response can contain up to 5,000 points. Its free Basic
plan documents 8 API credits/minute and 800/day; the pricing page gives a
one-credit `time_series` example. One 260-bar NOW request would therefore fit
within the published technical and rate limits.

The rights issue is decisive. Basic is described as "internal non-display
usage." Its support policy says individual plans are for personal or internal
use and do not permit redistribution or commercial display to third parties.
The frozen report contract persists normalized OHLCV bars and renders derived
technical evidence. Until Twelve Data confirms in writing that this specific
internal prototype, retained frozen evidence, and report display are permitted,
its free plan is not approved for this lane.

- Identification only: a future adapter would require `TWELVE_DATA_API_KEY`;
  no new environment variable is authorized here.
- Required normalized fields: the same OHLCV allowlist as Alpha Vantage;
  `volume` may not be silently omitted because it is part of the required
  existing normalized bar shape.
- Per-package behavior if rights are later approved: one `time_series` call per
  new NOW evidence package, one app-owned call cap per package, then freeze
  normalized rows and derived calculations. Treat provider limits as an upper
  ceiling, not an app budget.
- Safe failure codes: `source_rights_not_approved`,
  `source_endpoint_not_available`, `source_rate_limited`,
  `ohlcv_insufficient_history`, `ohlcv_missing_required_field`,
  `ohlcv_stale`, and `provider_unavailable`.

Official sources: [Twelve Data historical-data guidance](https://support.twelvedata.com/en/articles/5214728-getting-historical-data),
[pricing](https://twelvedata.com/pricing), and
[commercial/personal-use policy](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage).

### 3.3 Rejected yfinance/Yahoo Comparison

The sibling reference project uses yfinance by default and optionally Alpha
Vantage. That is useful only as a design reference. yfinance is not affiliated
with or vetted by Yahoo; its own documentation calls it research/educational
and says Yahoo Finance API use is intended for personal use. Yahoo's general
terms prohibit commercial activity on non-commercial properties or apps and
high-volume activity without written consent. There is no reviewed Yahoo source
contract for frozen retention, report display, source versioning, or failure
semantics.

That combination is incompatible with Portfolio Copilot's provider-mediated,
freeze-once evidence contract. Do not use yfinance/Yahoo as an emergency
fallback or an implementation dependency.

Official/primary sources: [yfinance legal notice](https://ranaroussi.github.io/yfinance/index.html)
and [Yahoo terms of service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html).

## 4. SEC Company Facts Fundamentals Assessment

SEC's `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` returns the
company concepts data for a single CIK. SEC documents that its XBRL APIs use
non-custom taxonomies and entity-wide facts, which makes them substantially
better primary evidence than a vendor's undocumented statement mapping. The API
is refreshed as filings are disseminated, typically under a minute for XBRL
data, subject to peak-time delay.

It can be a viable replacement for the three statement groups only through a
new, narrow `SEC Company Facts` source contract. It is **not** allowed by the
current EDGAR contract, which expressly limits EDGAR to identity and recent
filing metadata and prohibits XBRL facts.

The new lane must select and normalize, rather than expose, only reviewed facts
for two comparable annual or quarterly periods:

| Group | Required normalized facts |
| --- | --- |
| Income statement | revenue, gross income where reported, operating income, net income, EPS; fiscal period, period start/end, form, filing date, currency/unit |
| Balance sheet | assets, liabilities, current assets, current liabilities, reviewed debt fact(s); instant date, form, filing date, currency/unit |
| Cash flow | operating cash flow, capital expenditure where reported, free cash flow only as backend calculation; fiscal period, period start/end, form, filing date, currency/unit |

It must use a reviewed concept-precedence map, explicit unit validation, exact
period/form selection rules, and a per-fact source/report-date label. It must
not invent a missing GAAP field, merge incomparable durations, choose a custom
company tag without approval, or calculate an unsupported "current" value.

- Identification only: no key. Continue to require a descriptive
  `SEC_EDGAR_USER_AGENT`; any future opt-in must be separately named and
  disabled by default (for example, `POA_EDGAR_COMPANY_FACTS_MODE`).
- Per-package budget: one Company Facts acquisition after safe CIK resolution,
  under the existing process-wide one-request-per-second and 60/day EDGAR
  guardrails unless Codex B changes them explicitly. Freeze normalized facts
  only; discard raw concepts, raw URLs, accessions, payloads, and filing text.
- Failure codes: `sec_company_facts_symbol_unresolved`,
  `sec_company_facts_mapping_not_reviewed`, `sec_company_facts_concept_missing`,
  `sec_company_facts_unit_invalid`, `sec_company_facts_period_ambiguous`,
  `sec_company_facts_comparable_period_missing`, `source_rate_limited`, and
  `provider_unavailable`.

Company Facts provides source facts, not an SEC conclusion, recommendation, or
guarantee. It is backend-fetched only and must carry source attribution without
SEC-endorsement wording.

Official sources: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
and [SEC developer/fair-access guidance](https://www.sec.gov/developer).

## 5. Freeze, Prompt, And Failure Requirements

Any future approved source must use the existing preparation lifecycle:

1. A new saved NOW package acquires each approved lane once, under an
   app-owned per-run and UTC-day budget.
2. The backend validates the normalized allowlist and the technical minimum of
   260 distinct ordered daily bars before any technical calculation.
3. Only normalized evidence, provenance labels, deterministic calculations,
   freshness state, and caveat codes freeze with that package.
4. All analyst roles, PM synthesis, retry paths, generation, regeneration, and
   readback reuse that frozen package. They make zero source calls.

Raw source responses, URLs, accessions, API keys, account/provider identifiers,
and provider headers remain unpersisted, unlogged, unrendered, and absent from
LLM prompts. LLMs receive only reviewed evidence envelopes and deterministic
calculation results. They do not compute financial values.

## 6. Exact Source-Rights Decisions Required Before Implementation

1. **OHLCV provider entitlement.** Codex B must record a provider and plan that
   explicitly permits Portfolio Copilot's backend retrieval, technical use,
   user-visible internal report display, and permanent retention of normalized
   260-bar evidence for frozen historical readback. A free plan labelled
   non-display is insufficient without written confirmation.
2. **FMP option.** If FMP is selected instead, obtain the plan/access decision
   and written confirmation for NOW EOD history, all three statements, display,
   and frozen retention. A `402` must remain
   `source_subscription_required`; it cannot trigger an unapproved fallback.
3. **SEC Company Facts expansion.** Approve a separate XBRL facts lane with a
   concept-precedence registry, allowed forms/periods/units, two-period
   comparability policy, metadata-only lane separation, attribution/non-
   endorsement wording, and the existing EDGAR fair-access budget.
4. **Evidence retention.** Confirm the selected OHLCV vendor permits the
   report's permanent normalized-bar retention. “No raw payload” does not by
   itself answer a market-data retention or redistribution question.
5. **Display boundary.** Approve exactly which values may be rendered: raw bars,
   latest close, 52-week range, SMA-200, and derived labels must not be assumed
   equivalent under vendor rights.
6. **Failure semantics.** Add the closed caveat codes above and preserve
   `not_ready` when any required lane fails. No 100-bar substitute, stale
   result, provider swap, or reconstructed data may make readiness `ready`.

## 7. Proposed One-Owner Implementation Sequence After A Decision

1. **Codex B:** select and document the licensed OHLCV source or FMP plan,
   approve the Company Facts extension if chosen, and amend the Phase 36 source
   contract and readiness matrix.
2. **Claude G:** perform architecture/privacy/source-retention review of the
   approved contract before code begins.
3. **Codex C:** implement one provider adapter and/or the Company Facts
   normalizer with offline fakes, package-only caching, frozen-readback
   tripwires, 260-bar validation, and typed unavailable outcomes.
4. **Codex B:** review contract fidelity and authorize one explicit, bounded
   source smoke only after the rights and environment decision exists.
5. **Founder:** separately authorize a real NOW preparation/run after the
   source smoke and readiness evidence are recorded.

## 8. Blocking Conditions

- The configured FMP account cannot access the four required endpoints.
- Alpha Vantage free tier cannot provide the required 260 daily bars and its
  documented terms do not approve this app's use without a commercial agreement.
- Twelve Data free Basic access has a clear non-display restriction; it is not a
  rights-cleared report source.
- SEC Company Facts is not yet within the approved EDGAR source boundary.

Until an OHLCV rights decision and a Company Facts/FMP fundamentals decision are
made, the correct NOW preparation result remains `not_ready`; no five-agent
acceptance generation should occur.
