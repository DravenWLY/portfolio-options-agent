# Phase 36 - FMP Free-Plan NOW Entitlement Investigation

Status: research complete; NOW five-agent readiness remains blocked.

Owner: Codex E (research/design only)

As of: 2026-07-20

Related: `PHASE_36_NOW_PUBLIC_EVIDENCE_SOURCE_INVESTIGATION.md`,
`EXTERNAL_API_LIMITS.md`, `PHASE_36_FIVE_AGENT_ACTIVATION_CONTRACT.md`, and
`PHASE_36_T7_SOURCE_READINESS_AND_ETF_EVIDENCE_CONTRACT.md`.

## 1. Scope And Safe Evidence

This investigation uses the two supplied, sanitized observations only. It did
not inspect account configuration, a key, a dashboard, a raw response, a log,
or a report, and it made no FMP request.

| Symbol | EOD daily OHLCV | Income statement | Balance sheet | Cash flow |
| --- | --- | --- | --- | --- |
| AAPL | Available with required normalized fields | Available with required normalized fields | Available with required normalized fields | Available with required normalized fields |
| NOW | HTTP 402 -> `source_subscription_required` | HTTP 402 -> `source_subscription_required` | HTTP 402 -> `source_subscription_required` | HTTP 402 -> `source_subscription_required` |

The AAPL result rules out a globally invalid key, a globally unavailable stable
endpoint, and an unconditional account-wide denial for all four lanes. It does
not establish NOW coverage, complete free-plan US coverage, or display and
retention rights.

## 2. Official FMP Plan Documentation Versus The Evidence Contract

FMP's current pricing page describes Basic as a free plan for testing endpoints,
with 250 calls per day, end-of-day historical data, and profile/reference data.
The same page describes Starter as adding US coverage, annual fundamentals and
ratios, historical stock-price data, and 300 calls per minute. Its comparison
table lists Basic as end-of-day, 250 calls/day, and five years of historical
range. Five years would exceed the app's 260-daily-bar minimum *for a symbol
whose EOD endpoint is entitled and returns valid rows*.

The public plan description is not a contract that every U.S. common stock is
available to Basic. It distinguishes Basic testing from Starter US coverage. In
addition, FMP's support material says a plan may have ticker-specific endpoint
limits and that a plan upgrade may still have ticker restrictions. The pricing
matrix visibly labels a Basic-tier symbol set as limited rather than all-US.

| Required lane | FMP public documentation | Contract implication for NOW |
| --- | --- | --- |
| Full daily EOD OHLCV | Stable `historical-price-eod/full` documents open, high, low, close, and volume. Basic advertises EOD history and five years. | Technically sufficient only if NOW is in the entitled symbol set and yields at least 260 valid daily rows. The known NOW 402 prevents this. |
| Income statement | Stable documentation names `income-statement`; Starter explicitly advertises annual fundamentals. AAPL proves the configured account can receive one limited-symbol result. | FMP does not publicly promise Basic access for NOW or all U.S. issuers. Two labeled comparable periods cannot be assumed for NOW. |
| Balance sheet | Stable documentation names `balance-sheet-statement`; financial statement docs describe this group generally. | Same coverage gap. AAPL success cannot establish NOW entitlement. |
| Cash flow | Stable documentation names `cash-flow-statement`; financial statement docs describe this group generally. | Same coverage gap. AAPL success cannot establish NOW entitlement. |

The app's maximum external demand is modest but is not evidence of entitlement:
up to two EOD requests per run and a 10-request UTC-day statement cap. Even the
maximum 12 FMP calls is below FMP's published Basic 250/day ceiling. A rate
budget cannot cure a symbol/plan access restriction.

## 3. What The Documentation Explains About NOW Versus AAPL

### Supported explanation

The smallest explanation consistent with both the safe observations and FMP's
published plan material is a **likely symbol-coverage/plan-entitlement
difference**:

1. The same configured access serves all four lanes for AAPL, so a universally
   unusable key or an unconditional stable-endpoint outage is inconsistent with
   the observations.
2. FMP labels Basic as a testing plan and reserves US coverage and annual
   fundamentals for Starter.
3. A plan-level limited symbol universe can therefore admit AAPL while denying
   NOW on several endpoints.

This is a coverage/entitlement hypothesis, not a claim that NOW is invalid or
unmapped. The current evidence contains no FMP symbol-directory result, source
payload, account plan, or FMP-authored NOW rule. The fact that all four NOW
lanes produce the same status makes a single app-side statement-field mapping
failure less likely, but it does not prove FMP's internal reason.

### What FMP does not document

- FMP's published quickstart error list includes 403, 429, and 500; its support
  FAQ lists 200, 403, 429, 501, 502, and 504. Neither official page documents
  HTTP 402 semantics.
- No reviewed FMP page maps NOW to a tier, exchange restriction, or unavailable
  security class.
- No reviewed FMP page guarantees the three statement endpoints, two comparable
  labeled periods, and 260 valid EOD bars for every U.S. operating-company
  equity on Basic.
- No reviewed page explains a stable-endpoint-specific AAPL/NOW rule.

The application mapping of a received 402 to
`source_subscription_required` remains the correct safe product caveat. It
must not be presented as FMP's documented 402 definition.

## 4. Stable API Versus Legacy API

The project uses the current `/stable/` family. FMP says free plans do not have
legacy API access and directs new/free users to Stable. It also says Stable
endpoints may have consolidated, relocated, or removed fields, and that Stable
has updated access controls based on subscription level. FMP further says the
plan-by-plan Stable documentation is still being developed.

Therefore, the project must not infer Stable endpoint entitlement from an old
legacy endpoint, outdated endpoint family, or a generic marketing statement.
The current stable paths are correct for the project, but their public
documentation does not resolve the NOW-versus-AAPL differential.

## 5. Source Rights: Display And Frozen Retention

FMP's pricing page states that displaying or redistributing FMP-sourced data
requires a specific Data Display and Licensing Agreement. Its terms further
prohibit data display in multi-user software without a specific agreement and
restrict personal-plan use. These restrictions apply independently of endpoint
call count and coverage.

The frozen-report design also needs an explicit retention decision. FMP's terms
say that, upon termination, license rights end and the customer must cease use
of data or information derived from the service and delete received data,
including cached data. The terms contain a limited retention statement for
reports/information in one confidentiality clause, but it remains subject to
license restrictions. The public terms therefore do **not** establish a right
to retain normalized FMP OHLCV and statement facts permanently for historical
readback after the subscription or license ends.

No implementation may treat normalized data as rights-free merely because raw
payloads are discarded.

## 6. Classification

**Classification: likely symbol-coverage/plan-entitlement difference; exact
provider behavior unresolved.**

This is stronger than “inconclusive” because the AAPL/NOW split and FMP's own
limited-Basic versus US-coverage-Starter materials point in the same direction.
It is weaker than “confirmed entitlement failure” because FMP does not document
HTTP 402, a NOW-specific entitlement rule, or the active account's actual plan
and symbol matrix.

The required NOW evidence package remains `not_ready`. No live five-agent run
may use a partial package or replace a missing lane automatically.

## 7. Decisions Required Before Any New Source Work

1. **FMP plan decision:** Founder and Codex B must decide whether to pursue
   FMP access that explicitly includes NOW on all four stable endpoints. A
   pricing-page label alone is insufficient; confirm the exact plan, symbol
   coverage, statement period depth, and EOD history range with FMP.
2. **Display license decision:** Before any user-visible report surface, obtain
   the required Data Display and Licensing Agreement or record that FMP data
   remains limited to an authorized non-display internal evaluation.
3. **Retention/deletion decision:** Obtain written terms for the freeze-once
   saved-report retention period, readback after subscription termination, and
   deletion obligations for normalized data and calculations derived from it.
4. **Source-contract decision:** Codex B must amend the Phase 36 source-rights
   contract only after the above answers exist. It must preserve per-package
   acquisition, the 260-bar validation, two comparable statement periods,
   provenance, and typed unavailable outcomes.
5. **Evidence status decision:** Until that amendment and a separate authorized
   smoke exist, the NOW case remains `not_ready`; FMP 402 remains
   `source_subscription_required`, with no silent provider fallback.

## 8. Required Post-Decision Guardrails

Any approved path must preserve all of the following:

- at least 260 distinct normalized daily OHLCV bars before SMA-200 and 52-week
  calculations;
- two labeled, comparable fiscal periods for all three statement groups;
- exactly one provider acquisition sequence per saved package;
- normalized-only evidence freeze, no raw-payload persistence, and no raw
  provider data in prompts;
- zero provider calls on role retries, generation, regeneration, and readback;
- honest `not_ready`/unavailable outcomes rather than provider substitution;
- no live five-agent generation while a required NOW lane remains partial.

## 9. Official Sources Checked

All sources below were checked on 2026-07-20. No provider API was called.

- [FMP pricing and plan comparison](https://site.financialmodelingprep.com/developer/docs/pricing)
- [FMP Stable API quickstart and documented common errors](https://site.financialmodelingprep.com/developer/docs/quickstart)
- [FMP full historical price and volume API](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full)
- [FMP support/FAQ on Stable restrictions, legacy access, and tier limits](https://site.financialmodelingprep.com/contact)
- [FMP Terms of Service](https://site.financialmodelingprep.com/developer/docs/terms-of-service)
