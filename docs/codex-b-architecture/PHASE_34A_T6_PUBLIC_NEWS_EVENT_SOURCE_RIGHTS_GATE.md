# Phase 34A-T6 - Public News/Event Source-Rights Gate

Status: source-rights decision
Owner: Codex B - Architecture / Contract / Privacy
Date: 2026-06-30

## Decision

P34A-T6 does not approve a general public-news provider for Agent Team tools.
It conditionally approves one narrow company-event lane:

> SEC EDGAR recent filing metadata only.

This is an event-metadata source, not a news interpretation source. It may be
used to help the Agent Team say that recent company filing activity was checked,
was unavailable, or included specific recent form-type/date metadata. It must not
summarize, quote, interpret, or classify filing contents.

## Source Decisions

| Source | Decision | Reason |
| --- | --- | --- |
| NewsAPI / generic article aggregators | Not approved | Terms include third-party content and restrict reproduction/republishing; developer plan is development-only. Requires a specific paid/commercial license review plus excerpt/URL policy before use. |
| Benzinga / Finnhub / Polygon / FMP news | Not approved | Commercial news/data products require provider-specific licensing and redistribution/display review. |
| GDELT / web-scale news/event databases | Not approved for P34A | Broad news-derived content and URL/snippet provenance need a separate source-rights, excerpt, and retention policy. |
| SEC EDGAR recent filing metadata | Conditionally approved | SEC says EDGAR data can be accessed for free, APIs need no authentication, and filing indexes expose company name, form type, CIK, date filed, and file name. Use must follow fair-access/user-agent guidance. |

## Approved EDGAR Event Scope

Allowed normalized fields:

- `section_key = "public_events_calendar"` or a reviewed tool result ref that
  reduces to `public_events_calendar`;
- `source_key = "sec_edgar_recent_filings"`;
- `source_label = "SEC EDGAR recent filing metadata - company events only"`;
- availability and freshness/as-of/collected_at;
- ticker and company display label only if already resolved by the existing
  reviewed public-company-profile boundary;
- CIK reference only in structured saved evidence when already available from
  the reviewed public-company-profile boundary;
- form type;
- filing date;
- accession reference only as an opaque normalized filing reference if needed
  for deduplication/audit, not as a raw URL;
- reviewed caveat codes and limitations;
- count/window labels if they are backend-derived from the normalized records.

Not allowed:

- filing body text;
- HTML filing text;
- exhibit text;
- press releases;
- article/news text;
- long excerpts;
- XBRL company facts;
- insider-transaction interpretation;
- filing interpretation or event interpretation;
- raw URLs;
- raw SEC payload persistence;
- raw file path rendering;
- buy/sell/hold/recommendation/order/execution/safe-to-trade wording;
- SEC endorsement wording.

## LLM Prompt Use

Approved only through sanitized `ToolResult` envelopes and only as company-event
context. The LLM may receive normalized form-type/date labels and caveats. It may
not receive raw filing text, raw URLs, raw payloads, or raw SEC paths. The LLM
must not infer financial impact, sentiment, materiality, urgency, or trading
action from filing metadata.

Permitted role behavior:

- `news_analyst` may say reviewed EDGAR filing metadata was available, limited,
  unavailable, or not reviewed.
- `portfolio_manager_agent` may include the absence or presence of reviewed
  company-event metadata as a context gap/background point.

The backend continues to own citations; the LLM cannot introduce evidence refs.

## Saved-Report Persistence

Allowed:

- normalized event metadata;
- source label/key;
- availability/freshness/as-of/collected_at;
- caveats/limitations;
- tool result envelope;
- saved report freeze for reproducibility.

Forbidden:

- raw SEC response payload;
- raw URLs or raw file paths;
- filing body or excerpts;
- provider request/response logs;
- prompts/traces/secrets.

## Attribution And Caveat

Short label:

`SEC EDGAR recent filing metadata - company events only`

Attribution:

`Source: SEC EDGAR submissions/index metadata. Recent filing metadata only. Not investment advice or a trading signal.`

Caveat:

`EDGAR filing metadata may lag, be corrected, or omit filings that are not available through EDGAR. Portfolio Copilot does not interpret filing contents or treat filing metadata as a trading signal.`

Non-endorsement:

`Use of SEC EDGAR data does not imply endorsement by the U.S. Securities and Exchange Commission.`

## Retention / Cache Limits

- No background crawler.
- No bulk ingestion.
- Fetch only for explicit saved review/report evidence generation.
- Conservative request budget: one company filing-metadata lookup per underlying
  per report run unless Codex B approves otherwise.
- Process-wide rate limit must stay stricter than SEC's published fair-access
  limit; target one request/second or lower.
- Raw response may exist only transiently during normalization.
- Normalized local/internal cache TTL: up to 24 hours.
- Saved reports may persist normalized metadata indefinitely as historical report
  evidence.

## Failure Behavior

Failures degrade to `not_available` / `provider_unavailable` /
`source_rights_not_approved` without breaking report generation. Do not fall
back to NewsAPI, GDELT, FMP, CNN, Benzinga, Finnhub, Polygon, web search, or
scraping. Absence of EDGAR event metadata is a gap/context point, not a signal.

## Sources Consulted

- SEC EDGAR APIs: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- SEC EDGAR access/fair-access guidance: `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`
- NewsAPI terms: `https://newsapi.org/terms`

## Next Implementation Slice

Open `P34A-T6A - SEC EDGAR recent filing metadata tool`.

Owner: Codex C.
Reviewer: Codex B.

This slice should add a backend-only, disabled-by-default, fake/replay-tested
tool that reads or builds normalized SEC EDGAR recent filing metadata through
the reviewed public-evidence/source policy boundary. It must not add a frontend
surface, live browser smoke, filing-body extraction, news-provider integration,
or any new public-news source.
