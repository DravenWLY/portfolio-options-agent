# Phase 22A Market Data Vendor Capability And Licensing Comparison

Status: completed parked reference - no provider selected or outreach authorized
Date: 2026-05-25
Owner: Codex B - Architecture / Systems / Integration
Task: `P22A-T2`

## Method And Boundary

This memo evaluates candidate providers against the provider-neutral contract
in `PHASE_22A_MARKET_DATA_EVALUATION_CONTRACT.md` and the questions in
`MARKET_DATA_PROVIDER_RFI.md`.

The review used public official vendor pages only. It did not create accounts,
test credentials, call provider endpoints, begin a trial, approve external
display, or authorize implementation.

## Recommendation

Keep the provider-neutral Phase 22A architecture unchanged and retain this
commercial comparison for a future scale-selection track. Codex A parked
commercial provider work on 2026-05-26: do not send the RFI, start licensing
or pricing discussions, or select a production provider unless that track is
explicitly reopened. `P22A-T4` is a separate local/internal Alpaca Basic
fake-client mapping evaluation, not commercial provider selection.

When commercial selection becomes timely, the same written RFI should be sent
to:

- Intrinio;
- Databento;
- dxFeed;
- Massive.

Massive materially improves the comparison because its public business options
offering advertises snapshots, real-time calculated values, Greeks/IV, and a
commercial packaging posture that differs from the other candidates. Its
published material does not, by itself, answer which outputs are raw
OPRA-derived quotes versus calculated fair-market values, or which external
display, storage, derived-use, and later sanitized agent-evidence rights apply.

No production provider should be selected from public pages alone. A later
bounded provider evaluation task should be considered only after Codex A
reviews written vendor answers covering external paid-user display,
deterministic backend calculation, bounded snapshot retention/replay,
derived-report display, entitlement and user-classification costs, and any
future separately approved sanitized market-evidence use by LLM agents.

## Required Product Fit

| Requirement | Why It Matters | Written Answer Required Before Provider Selection |
| --- | --- | --- |
| U.S. stock and ETF quote snapshots | Trade review needs underlying-price provenance distinct from broker holdings freshness. | Coverage source, CTA/UTP/SIP versus limited venue, mode, latency, and external display rights. |
| U.S. listed-option quote and chain snapshots | Covered-call and cash-secured-put review needs contract-specific market inputs. | OPRA derivation, chains/contracts, NBBO or bid/ask/last coverage, modes, entitlements, and display rights. |
| IV and Greeks provenance | Deterministic review cannot present invented or unattributed analytical inputs. | Provider-supplied versus calculated provenance, mode, timestamp, retention, and derived-display rights. |
| Snapshot/replay support | A shown review must remain reproducible without implying a historical quote is current. | Permitted stored fields, retention duration, replay/historical access, report/export restrictions. |
| Commercial use at scale | The product is intended for external users, not only internal testing. | Per-user/device/professional fees, exchange reporting, minimum commitment, and hundreds/thousands-user pricing. |
| Future sanitized agent evidence | Agent expansion is paused and must not silently gain market-data rights. | Whether a later separately approved derived/sanitized use is permitted, distinct from raw data use. |

## Public Official Information Matrix

The entries below distinguish publicly stated capabilities from open rights or
commercial questions. Marketing statements are not treated as a license grant.

| Vendor | Publicly Stated Equity Coverage | Publicly Stated Listed-Options Coverage | IV / Greeks And Delivery Evidence | Rights / Pricing Evidence Found Publicly | Questions Requiring Written Confirmation |
| --- | --- | --- | --- | --- | --- |
| Intrinio | Pricing lists IEX realtime stock prices as limited market-volume coverage and delayed SIP U.S. stock prices as full-market-volume delayed coverage. | Pricing lists realtime and 15-minute delayed U.S. options products covering all U.S. exchanges; its Options Edge product is described as a realtime algorithmic/synthetic alternative to OPRA agreements and exchange fees. | Realtime and delayed options descriptions include IV and Greeks. | Public business pricing is listed. Intrinio states that displaying delayed options prices does not incur additional charge or require exchange approval, while displaying realtime options requires contact and exchange fees. | Full paid-user display grant; full realtime consolidated equity path; retention/replay and report export; derived deterministic summary rights; future sanitized LLM-evidence rights; complete scale pricing and classification duties. |
| Databento | U.S. equities datasets are offered separately; exact consolidated equity package and external-display fit must be confirmed for this product. | The OPRA.PILLAR dataset is identified as direct from OPRA for U.S. options, with live and historical availability and schemas for trades, NBBO/depth, definitions, statistics, and status. | IV/Greeks inclusion was not confirmed on the reviewed OPRA dataset page. | Licensing documentation distinguishes internal non-display, internal display, and external distribution. Pricing states display and external distribution licenses are available under commercial contact paths and licensing fees are separate. | Equity coverage/mode; IV/Greeks source; OPRA and external-user fees; snapshot retention/reports/exports; derived calculations and future sanitized LLM-evidence rights; scale commitments. |
| dxFeed | Market-data coverage pages list U.S. equities CTA/UTP and exchange/venue coverage. | Coverage pages list USA Options (OPRA) across U.S. options exchanges. | Options materials advertise implied volatility, Greeks, and analytics; the market-data page describes realtime, delayed, historical, replay, and aggregated delivery modes. | Detailed product rights and production pricing were not established on the reviewed public request-pricing material. | External paid-user display and redistribution; permitted stored/replayed snapshots and derived reports; REST snapshot fit and limits; OPRA/CTA/UTP fee structure; future sanitized LLM-evidence rights; scale pricing and SLA. |
| Massive | Stock API documentation describes U.S. stock coverage sourced through SIPs and direct/regulated market sources, delivered by REST, WebSocket, and flat files. | Its Options Business page advertises all U.S. options tickers, snapshots, realtime fair-market value, realtime Greeks/IV/open interest, and optional tick-level trades/quotes expansion associated with OPRA data. | Public business options packaging advertises calculated analytics and snapshot delivery. | Options Business publicly advertises a starting monthly price and a no-exchange-fees-or-approvals posture for its packaged offering. This does not establish all rights needed by Portfolio Copilot. | Raw OPRA NBBO/quote versus calculated fair-market-value boundary; rights under base package versus OPRA expansion; external paid display; retention/reports/exports; deterministic derived calculations; future sanitized LLM-evidence rights; equity/options scale costs. |

## Fit By Product Stage

| Product Stage | Acceptable Data Posture | Comparison Conclusion |
| --- | --- | --- |
| Current Phase 22A backend foundation | Synthetic/replay only, deterministic, offline, with explicit provenance. | Already addressed by `P22A-T1`; no vendor is needed or authorized. |
| Optional future internal/private-alpha evaluation | Only a separately approved delayed, indicative, or otherwise limitation-labelled evaluation with written trial/use terms. | Intrinio delayed options is publicly understandable as a possible evaluation question; no trial is authorized here. Other vendors may also answer the RFI with suitable evaluation terms. |
| Paid beta with quote-current product claims | Licensed external-user display and deterministic-calculation rights for required equities/options data, with clear freshness/provenance semantics. | Public pages are insufficient for selection; written RFI answers are required. |
| Commercial scale | Contracted entitlements, reporting duties, retention/export terms, support/SLA, and predictable hundreds/thousands-user cost model. | No candidate may be selected from currently reviewed public information alone. |

## Rights Gap Matrix

| Required Right Or Duty | Public Information Sufficient For Selection? | Required Next Evidence |
| --- | --- | --- |
| External paying-user quote/chain display | No. Intrinio gives useful delayed/realtime display guidance, but not the full product grant; other candidates also need confirmation. | Written vendor/license response. |
| Internal deterministic financial calculations | No. | Written permission distinguishing raw input processing from displayed derived output. |
| Bounded retained snapshots and reproducible historical reports | No. | Retention, storage, replay, export, and audit terms. |
| Display of deterministic derived summaries | No. | Written derived-use and report-display rights. |
| Later sanitized market-derived LLM evidence | No, and the product phase is paused/out of scope. | Separate future PM/security approval plus written vendor permission. |
| Entitlement, non-professional/professional, reporting, and per-user/device costs | No. | Written licensing and pricing schedule for each planned scale tier. |

## Future RFI Recipient Recommendation

When Codex A opens the commercial-scale selection track, send the uniform RFI
to all four candidates, subject to PM approval:

- **Intrinio** provides public delayed/realtime options packaging and display
  guidance useful for evaluating an explicitly delayed early path.
- **Databento** provides a clearly identified official OPRA dataset and an
  explicit external-distribution licensing category, useful for a raw-data and
  rights-focused comparison.
- **dxFeed** publicly describes broad CTA/UTP and OPRA coverage plus replay and
  analytics, making it relevant for a commercial full-coverage comparison.
- **Massive** publicly packages business options analytics and snapshots in a
  meaningfully different way, so its raw-versus-calculated data and license
  boundaries should be tested by the same RFI.

RFI outreach is parked under the Codex A decision of 2026-05-26 and remains a
future reference only until commercial-scale planning is explicitly reopened.
This memo does not authorize outreach, an adapter, trial, provider request,
frontend data display, market-data streaming, or agent ingestion.

## Product Documentation Alignment Finding

The amended ADR 0003 and Phase 22A decision reopen provider selection and no
longer assume Tradier as the production foundation. The following product
documents still contain Tradier-first wording and require a separate
PM-approved alignment update:

- `docs/codex-a-product/PRD.md`
- `docs/codex-a-product/MVP_SCOPE.md`
- `docs/codex-a-product/FEATURE_PRIORITY.md`

Those product documents should not be used to infer a selected provider while
Phase 22A evaluation is active.

## Official Sources Reviewed

Accessed 2026-05-25:

- Intrinio pricing: <https://intrinio.com/pricing>
- Intrinio FAQ: <https://intrinio.com/faq>
- Intrinio options display licensing explainer:
  <https://intrinio.com/blog/how-much-does-it-cost-to-display-options-data-to-end-users>
- Databento OPRA.PILLAR dataset: <https://databento.com/datasets/OPRA.PILLAR>
- Databento pricing: <https://databento.com/pricing>
- Databento licensing overview:
  <https://databento.com/docs/knowledge-base/new-users/licenses/overview>
- dxFeed market-data coverage: <https://dxfeed.com/market-data/>
- dxFeed options coverage: <https://dxfeed.com/market-data/options/>
- dxFeed request-prices page: <https://dxfeed.com/request-prices/>
- Massive Options Business: <https://massive.com/business-options>
- Massive Stocks API overview: <https://massive.com/docs/stocks/getting-started>

## Not Authorized By This Memo

- A production provider selection.
- An external provider account, trial, credential, API call, SDK, or adapter.
- Live, delayed, or indicative frontend market-data display.
- Streaming, WebSocket, or SSE market-data integration.
- LLM or agent ingestion of market data.
- Phase 21A reactivation or Agent Console composer activation.
