# Phase 22A Early Market-Data Evaluation Provider Assessment

Status: completed assessment for PM approval - no integration authorized
Date: 2026-05-25
Owner: Codex B - Architecture / Systems / Integration
Task: `P22A-T3`

## Decision Question

Portfolio Copilot has two separate market-data tracks:

1. **Early working evaluation**: obtain a free or low-friction backend data
   source for local/private development testing, with explicit limitation
   labels and no production claims.
2. **Commercial-scale selection**: later obtain written display, licensing,
   retention, derived-use, and scaling rights before serving paying users or
   claiming current licensed quotes.

This assessment serves only the first track. The commercial RFI materials
remain useful, but vendor outreach is deferred until early evaluation clarifies
the product's actual required fields and operating posture.

## Method And Boundary

This assessment used public official provider documentation only. It did not
create an account, inspect credentials, call a provider endpoint, run a trial,
or authorize an adapter.

Any later external smoke test must be separately approved, backend-only,
explicitly opt-in, and use credentials configured locally by the user without
being read or exposed by an agent.

## Recommendation

Recommend **Alpaca Basic as the first candidate for a separately approved
local/internal evaluation adapter**, with these strict constraints:

- equity data is represented as `indicative` or `limited_source`, because the
  free Basic equity feed is IEX rather than consolidated U.S. market truth;
- option data is represented as `indicative`, because Alpaca documents its
  free Indicative Pricing Feed as a derivative of OPRA whose quotes are not
  actual OPRA quotes and whose trades are delayed;
- all reviews using that data remain `analysis_only`;
- no external-user display, redistribution, private-alpha user exposure, live
  claim, or agent ingestion is authorized;
- a later adapter task must default to mocked tests and make any real call an
  explicit external smoke path only.

Why Alpaca first: its official Basic-plan documentation identifies a zero-cost
path for U.S. equities and options; its options endpoints expose latest quotes,
snapshots, option chains, and Greeks-shaped data needed to exercise the
provider-neutral contracts. It is not a production foundation: Alpaca's
official support material says Alpaca API data cannot be redistributed.

If the early test must use **actual 15-minute delayed equity and option quotes**
rather than an indicative options feed, recommend **Tradier Sandbox as the
secondary candidate**, accepting that its official market-data table says
Greeks are unavailable in sandbox and its FAQ limits application distribution
to Tradier Partners.

If the early test must use **delayed OPRA options plus IV and Greeks**, recommend
seeking written terms for an **Intrinio delayed-options free trial** as a
separately approved candidate. Intrinio publicly advertises a free trial and a
15-minute delayed OPRA options product with IV and Greeks, but it is not a
confirmed zero-friction free development plan until written trial terms are
reviewed.

## Candidate Comparison

| Candidate | Official Early-Access Evidence | Equity Fit | Options Fit | IV / Greeks Fit | Contract Labeling Required | Blocking Limitation |
| --- | --- | --- | --- | --- | --- | --- |
| Alpaca Basic | Basic is documented as zero cost for Trading API paper/live accounts; authentication keys are required. | U.S. stocks/ETFs through realtime IEX only, not consolidated coverage. | U.S. option securities through the free Indicative Pricing Feed; option quote, snapshot, and chain endpoints are documented. | Option snapshots/chain endpoints include Greeks; provenance must remain provider/indicative, not licensed OPRA truth. | `limited_source` or `indicative` for equity; `indicative` for options; `analysis_only` output. | API data may not be redistributed; unsuitable for user-facing product display without new written rights. |
| Tradier Sandbox | Tradier Standard brokerage pricing publicly lists developer API access at $0/month; sandbox is for testing with delayed market data. | Sandbox equities are documented as delayed by industry-standard 15 minutes. | Sandbox options are documented as delayed; quote and chain capability is documented. | Official market-data table says Greeks are not available in sandbox. | `delayed`; Greeks `unavailable`; `analysis_only` output. | Requires Tradier Brokerage account/token; FAQ states APIs are for personal use unless a Tradier Partner. |
| Intrinio delayed trial | Pricing publicly advertises a free trial and a 15-minute delayed options product. | Delayed SIP and other business-use equity products are published; trial scope must be confirmed. | 15-minute delayed OPRA product states all U.S. exchanges / full market volume. | Delayed options product advertises IV and Greeks. | `delayed` and `evaluation_only`; `analysis_only` output. | Free-trial duration, API access, retention, display, and derived-use permissions require written confirmation. |

## What Is Not Available For Free Today

Based on reviewed official documentation, no confirmed zero-cost path combines
all of the following for Portfolio Copilot:

- actual consolidated delayed or realtime U.S. equity data;
- actual OPRA-derived delayed or realtime listed-options quotes/chains;
- IV and Greeks;
- permission for product display or redistribution to external users.

The early path must therefore choose which testing property matters first:

- **Breadth of API contract testing at zero cost**: Alpaca Basic, with
  indicative/limited-source labeling.
- **Actual delayed quote testing without Greeks**: Tradier Sandbox, for
  internal/personal evaluation only.
- **Higher-fidelity delayed options with IV/Greeks**: Intrinio delayed trial,
  only after written trial terms are reviewed.

## Yahoo Finance Screening Decision

Do not use Yahoo Finance or unofficial wrappers as an application backend
market-data source. Yahoo's official help material says Finance information may
not be redistributed and is informational only. It does not establish a
supported commercial options/quote contract for this product.

Yahoo Finance may be referenced only as a rejected alternative or as a manual
human research site outside product data flows.

## Proposed Next Gate

Codex A should choose one of the following before Codex C receives an adapter
implementation task:

1. Approve an **Alpaca Basic local/internal evaluation adapter** as the first
   free contract-exercising path, accepting `indicative`/`limited_source`
   semantics and no redistribution.
2. Approve a **Tradier Sandbox local/internal evaluation adapter** if real
   delayed quote semantics matter more than Greeks for the first test.
3. Approve contacting Intrinio about a **delayed-options trial** if delayed
   OPRA plus IV/Greeks is required before adapter work.

If option 1 or 2 is approved, the later Codex C task must remain narrow:

- backend provider adapter behind existing provider-neutral interfaces;
- mock-driven tests by default;
- opt-in external smoke testing only after explicit approval;
- locally configured credentials only, never inspected or committed;
- no frontend market-data display;
- no agent/LLM ingestion;
- no streaming;
- no public live/current-data claim.

## Official Sources Reviewed

Accessed 2026-05-25:

- Alpaca Market Data API plans:
  <https://docs.alpaca.markets/docs/about-market-data-api>
- Alpaca historical options data sources:
  <https://docs.alpaca.markets/docs/historical-option-data>
- Alpaca option snapshots:
  <https://docs.alpaca.markets/reference/optionsnapshots>
- Alpaca option chain endpoint:
  <https://docs.alpaca.markets/v1.3/reference/optionchain>
- Alpaca redistribution support answer:
  <https://alpaca.markets/support/redistribute-alpaca-api>
- Tradier market-data modes:
  <https://docs.tradier.com/docs/market-data>
- Tradier endpoints and sandbox:
  <https://docs.tradier.com/docs/endpoints>
- Tradier FAQ and distribution limitation:
  <https://docs.tradier.com/docs/faq>
- Tradier developer API pricing page:
  <https://join.tradier.com/try-tradier>
- Intrinio pricing and free-trial availability:
  <https://intrinio.com/pricing>
- Yahoo Finance exchange/data-provider notice:
  <https://help.yahoo.com/kb/SLN2310.html>

## Not Authorized By This Assessment

- Provider account creation or credential use.
- Provider API calls, external smoke tests, SDK installation, or adapter code.
- Data display to any end user from an early-evaluation source.
- A commercial provider selection or RFI outreach.
- Market-data input to LLM agents.
- Phase 21A work or Agent Console composer activation.
