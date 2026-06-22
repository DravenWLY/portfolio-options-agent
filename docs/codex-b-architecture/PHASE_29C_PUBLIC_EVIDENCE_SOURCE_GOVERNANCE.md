# Phase 29C Public Evidence Source Governance

Status: proposed architecture; source approval pending founder decision
Owner: Codex B
Future implementation owner: Codex C
Agentic reviewer: Claude E only after a source-backed evidence package exists
Builds on:

- `PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md`
- `SavedPublicEvidencePackageRead` and its existing section contracts
- the generation-time persistence and package-aware validation shipped in P29B

## Purpose

Phase 29B established the safe shape and agent boundary for public evidence.
The default provider still returns `not_reviewed` because no production source
category has been approved for retrieval, LLM use, saved-report display, or
retention.

Phase 29C governs that missing source boundary. It does not authorize a provider
merely because an adapter can be written or data is publicly reachable.

## Architecture Decision

Keep the P29B evidence and report contracts. Add production public evidence only
through a backend-owned, source-approved acquisition pipeline:

`approved source adapter -> ephemeral raw response -> bounded normalization ->`
`public-evidence validation -> immutable generation-time package -> public roles`

Public roles never call sources directly. The frontend never calls sources and
never assembles evidence. Opening or regenerating an existing saved report never
re-fetches current public data.

Until a source category is approved, its sections remain `not_reviewed` or
`not_available` and the corresponding role degrades honestly.

## Real-Source Exploration Decision

Synthetic evidence is a regression and fixture mechanism, not the product
direction for public evidence. P29C should actively move toward a reviewed real
source once the rights and retention record is complete.

The preferred first source candidate for `public_company_profile` is an
official, low-volatility, structured source category, with SEC EDGAR submissions
as the initial architecture reference for U.S. public companies:

- symbol-to-CIK/company lookup through SEC-published mapping or an approved
  licensed resolver;
- `data.sec.gov/submissions/CIK##########.json` for current company metadata;
- bounded identity facts only, such as company name, ticker, exchange, SIC label
  if reviewed, and fiscal year/end metadata if useful;
- no filing bodies, business-description extraction, raw URLs, raw payloads,
  broad fundamentals, or article/news text in the first slice.

This source path is narrower than a commercial "company overview" endpoint, but
it is a better first production candidate because it is official, structured,
slow-moving, and avoids the text-rights and narrative risks that come with news
or scraped profile descriptions.

If the product needs richer sector/industry/profile summaries than SEC metadata
provides, that becomes a second source-approval decision for a licensed company
reference provider. Do not use yfinance/Yahoo-derived data for saved report
evidence unless Yahoo data rights are separately reviewed and approved for this
specific LLM, persistence, display, and retention use.

TradingAgents is useful as a reference for provider routing, not as a source
boundary to copy. It routes fundamental tools across yfinance and Alpha Vantage
vendors and lets research agents request broad text/CSV outputs. Portfolio
Copilot should borrow the adapter/fallback shape, but must reject runtime agent
tool access, broad raw reports, and unnormalized provider output.

## EDGAR Profile Integration Workflow

The first integration workflow is `public_company_profile` from SEC EDGAR
submissions metadata. It is deliberately narrow: prove the source-governed
acquisition path with official structured identity facts before adding
fundamentals, news, technical context, or richer commercial reference data.

### Step 1 - Source policy and adapter boundary

Codex C should define a backend-only public evidence source policy and adapter
interface. The policy must make EDGAR explicitly disabled unless an approved
runtime mode turns it on. Default tests and default runtime remain offline.

Required concepts:

- source key, such as `sec_edgar_submissions`;
- section key, fixed to `public_company_profile` for the first slice;
- allowed environments;
- request budget and timeout;
- user-agent requirement;
- raw-response retention policy;
- allowed normalized facts;
- unavailable/error mapping.

### Step 2 - Symbol-to-CIK resolution

The adapter may resolve `symbol_or_underlying` to CIK through SEC-published
company tickers data or an approved licensed resolver. Resolution output must
not echo user, account, broker, portfolio, or report-scope data.

If a symbol cannot be resolved confidently, return
`public_company_profile.availability = "not_available"` with an explicit
limitation. Do not guess the entity from search results.

### Step 3 - Submissions metadata retrieval

When enabled, the adapter may retrieve:

`https://data.sec.gov/submissions/CIK##########.json`

The request must be backend-only, rate-limited, bounded by timeout and response
size, and sent with a declared user-agent. No frontend or Agent Team role may
call EDGAR directly.

### Step 4 - Bounded normalization

Normalize only allowlisted identity fields into the existing
`SavedPublicEvidenceSectionRead` / `SavedPublicEvidenceFactRead` shape.

Initial allowed fact candidates:

- `company_name`;
- `ticker`;
- `exchange`;
- `cik_reference`;
- `sic_label`, only if present and reviewed;
- `fiscal_year_end`, only if useful and clearly labelled.

The section should include:

- `section_key = "public_company_profile"`;
- `availability = "available"` or `"limited"` only when rights/status are
  reviewed and at least one useful identity fact is present;
- `freshness_category` derived from collection time and source policy;
- `source_label`, such as `SEC EDGAR submissions metadata`;
- `rights_status`, according to the source approval record;
- `collected_at`;
- optional `as_of` only if the source supplies a meaningful source timestamp;
- limitations and caveat codes for missing/partial profile data.

### Step 5 - Validation and saved evidence freeze

The normalized section must pass the existing public-evidence safety validators
before it is attached to a saved evidence package. The same
`SavedEvidencePackageRead` instance must then be used for:

- role-scoped public evidence projection;
- package-aware report-output validation;
- saved artifact persistence.

Opening a saved report must read the saved normalized profile. It must never
re-fetch EDGAR or recompute profile evidence from current source state.

### Step 6 - Agentic use

Only after Codex B reviews the normalized sample package may Claude E refine the
fundamentals analyst behavior for `public_company_profile`. The role may cite
the section as company/instrument identity context only. It must not infer
valuation, trade timing, suitability, or actionability from the profile.

### Exclusions From The First EDGAR Slice

- SEC filing bodies, HTML, accession document text, exhibits, or long excerpts;
- XBRL company facts and financial statement concepts;
- insider transactions;
- current quote/market data;
- news, press releases, or event interpretation;
- sector/industry enrichment from unapproved commercial sources;
- frontend EDGAR calls;
- Agent Team runtime tools or web search.

## Codex A Source-Rights Decision - P29C-T2A

Status: approved with limits on 2026-06-20.

Codex A approved SEC EDGAR submissions metadata as the first real public
evidence source for `public_company_profile`, under strict local/internal use
limits.

Approved environments:

- local developer live smoke;
- internal test/demo;
- internal saved-report evidence generation.

Not approved:

- production or public SaaS retrieval at scale;
- automated background crawling;
- bulk ingestion;
- filing-body extraction;
- frontend EDGAR calls;
- Agent Team runtime EDGAR tools or web search.

Approved normalized content:

- `company_name`;
- `ticker`;
- `exchange`;
- `cik_reference`;
- `sic_label`, if present and reviewed;
- `fiscal_year_end`, if useful and clearly labelled;
- source label;
- freshness/as-of;
- `collected_at`;
- limitations and caveats.

Approved uses:

- backend-only local/internal live smoke;
- normalized `public_company_profile` evidence;
- Agent Team public roles may receive normalized public company identity
  metadata only;
- saved reports may persist normalized metadata, source label, `collected_at`,
  freshness, and caveats for report reproducibility.

Required display/attribution wording:

- Full wording: "Source: SEC EDGAR submissions metadata. Company identity and
  listing metadata only. Not investment advice or a trading signal."
- Short label: "SEC EDGAR metadata - company profile only"
- Caveat: "EDGAR metadata may lag company changes and does not include financial
  analysis, filing text, or investment conclusions."

Retention and cache limits:

- raw SEC payload must not be persisted;
- raw response may exist only transiently during normalization;
- normalized metadata may be cached for local/internal use;
- suggested TTL is 7 days;
- saved reports may retain normalized metadata indefinitely as historical report
  evidence.

Refresh limits:

- no background crawler;
- no broad scheduled refresh;
- fetch only when needed for a saved review/report evidence path;
- cache by CIK/ticker;
- conservative request rate, ideally 1 request/second process-wide or stricter;
- tiny per-run request budget, ideally one company-profile lookup per
  underlying;
- failures degrade to `not_available` / provider unavailable without breaking
  report generation.

Screenshots and exports:

- allowed for internal/demo and saved-report views if they contain only
  normalized metadata plus attribution/caveat;
- no raw SEC payload, filing body, raw URL, source trace, or SEC endorsement
  implication.

Explicitly prohibited:

- SEC filing bodies;
- HTML filing text;
- accession document text;
- exhibits;
- long excerpts;
- XBRL company facts;
- insider transactions;
- filing/event interpretation;
- news interpretation;
- raw URLs;
- raw payload persistence;
- frontend EDGAR calls;
- Agent Team runtime EDGAR tools or web search;
- broker/account/portfolio/private data;
- trading-action language;
- buy/sell/hold conclusions;
- SEC endorsement wording.

## Existing Contract Is The Default

P29C should reuse the shipped fields unless implementation proves a concrete gap:

- stable public section keys;
- per-section availability and freshness;
- provider-neutral source labels;
- `rights_status`;
- `as_of` and `collected_at`;
- bounded facts, limitations, and caveat codes;
- generation-time persistence;
- role-specific projection and citation validation.

No new frontend field, report status, evidence section, endpoint, or database
table is approved by this document. Any additive proposal requires a separate
Codex B contract review before implementation.

## Source Approval Record

Every source category must have a written approval record before production use.
The record must answer all of the following:

1. Source/provider category and the specific product or dataset covered.
2. Permitted environments: local demo, internal test, or production.
3. Whether automated backend retrieval is allowed.
4. Whether bounded facts may be sent to an LLM.
5. Whether normalized facts and short summaries may be persisted in saved reports.
6. Whether source labels or attribution must be displayed.
7. Retention and cache limits.
8. Refresh limits and expected freshness.
9. Whether export, sharing, or screenshots are permitted.
10. Explicitly prohibited content, including bodies, long excerpts, identifiers,
    or derived metrics.

Ambiguous or undocumented rights mean `not_reviewed`; reachability is not
permission.

## Section Approval Matrix

Initial status is intentionally fail-closed:

| Section | Production source status | Allowed behavior now |
|---|---|---|
| Company profile | Unapproved | `not_reviewed` or synthetic demo |
| Fundamentals snapshot | Unapproved | `not_reviewed` or synthetic demo |
| News snapshot | Unapproved | `not_reviewed`; no article bodies or excerpts |
| Events calendar | Unapproved for Agent reports | Existing separately reviewed product surfaces do not automatically authorize report/LLM use |
| Technical context | Unapproved | Backend-owned synthetic labels only |
| Market context | Unapproved for Agent reports | Existing context surfaces do not automatically authorize persistence or LLM use |

Approval is per use, not per provider. A source allowed for an internal dashboard
is not automatically allowed in an LLM request or immutable saved artifact.

## Acquisition Boundary

The production acquisition service may receive only minimal public instrument
context already allowed by P29B:

- `symbol_or_underlying`;
- an app-owned instrument classification only if separately reviewed as needed.

It must not receive user, account, broker, portfolio, holdings, quantities,
balances, strategy settings, saved scope labels, or report narrative.

Source adapters must:

- live behind a backend-owned interface;
- be disabled unless their source approval is active;
- use bounded timeouts, retries, and response-size limits;
- return explicit unavailable/error states;
- never expose credentials or provider payloads to callers;
- never log response bodies, query credentials, or raw source identifiers;
- support deterministic fake implementations for tests.

## Raw Response Boundary

Raw responses are transient adapter inputs only. They must not be:

- persisted in saved artifacts or application tables;
- placed in prompts, traces, logs, exceptions, or test snapshots;
- returned by APIs or rendered by the frontend;
- copied into summaries or facts without field-level normalization;
- retained in a cache unless the source approval explicitly permits it.

Normalization must use explicit structured parsing and an allowlist for each
section. Unknown fields are discarded. Article bodies, transcripts, HTML,
unreviewed URLs, and provider-specific payload metadata are rejected.

## Freshness And Availability

Freshness is section-specific and backend-owned. A source approval must define
the mapping from generation-time timestamps into the existing categories:

- `fresh`;
- `stale`;
- `unknown`;
- `not_available`;
- `not_reviewed`.

Missing timestamps never become fresh by assumption. Stale or partial evidence
may be `limited` only with an explicit limitation and caveat. Provider failure
does not become empty evidence; it becomes an honest unavailable state.

Public market-data freshness remains separate from brokerage snapshot freshness.

## Generation And Regeneration Semantics

Acquisition, when eventually approved, happens only during an explicit backend
workflow that builds a new generation-time evidence package.

Rules:

- validated public evidence is frozen with the saved artifact used by Agent Team;
- the exact same package is used for role projection, validation, and persistence;
- a provider or agent failure may leave a deterministic report with honest public
  role degradation;
- opening a saved report never triggers acquisition;
- regenerating narrative from an existing saved artifact reuses its saved public
  evidence and does not refresh it;
- newer public evidence requires a new explicit saved snapshot/workflow, not a
  silent mutation of historical evidence.

## Agent And Frontend Boundaries

Claude E may refine role behavior only after Codex C can produce reviewed
synthetic samples matching an approved source category. Existing P29B citation,
availability, and output-safety validation remains mandatory.

No frontend work is required for P29C source approval. Reports continue to render
the existing saved contract. The frontend must not infer coverage, freshness,
rights, or provenance from a symbol or current route state.

## Runtime And Product Prohibitions

P29C does not introduce:

- agent web search or runtime source tools;
- scraping, paywall/auth-wall bypass, or browser automation;
- private MCP, broker tools, or TradingAgents execution;
- frontend provider calls or financial calculations;
- order placement, cancellation, transfer, or broker action flows;
- directional verdicts, price targets, or guaranteed outcomes;
- automatic report generation or background refresh of saved reports.

## Required Founder Decisions

Before Codex C receives a production adapter task, the founder must approve:

1. Which public evidence section should be enabled first.
2. The exact source/product category for that section.
3. Permitted LLM, persistence, display, attribution, and retention uses.
4. Whether the first release is internal-only or production-facing.
5. Whether unavailable provider behavior should leave the role skipped or allow
   another separately approved source category.

The preferred first slice is one low-volatility structured section, not news.
News carries the highest text-rights, excerpt, timeliness, and attribution risk.

## Proposed Task Sequence

### P29C-T0 - Source governance and founder decision

Owner: Codex B and founder.

- Accept this architecture.
- Complete one source approval record.
- Select exactly one section for the first implementation slice.

### P29C-T1 - Offline source policy and adapter contract

Owner: Codex C. Reviewer: Codex B.

- Implement only after T0 approval.
- Define the fail-closed source policy boundary and the provider-neutral adapter
  interface for the approved source candidate.
- Include deterministic fake/replay implementations only for tests and local
  verification; they are not the product source path.
- Preserve the existing `SavedPublicEvidencePackageRead` contract by default.
- Make no external calls in tests or default runtime.
- For the SEC-first path, implement symbol/CIK resolution and submissions
  normalization behind disabled-by-default gates until source approval and
  access policy are recorded.

### P29C-T2 - Approved single-source acquisition slice

Owner: Codex C. Reviewers: Codex B and source-rights/product owner.

- Implement one approved section and source category.
- Normalize explicit fields into the existing public evidence contract.
- Freeze and validate generation-time evidence before public-role use, then
  persist that same package with the report result.
- Keep all other sections honestly unavailable or unreviewed.

### P29C-T3 - Agentic and product closeout

Owner: Claude E after T2 samples exist. Reviewers: Codex B and Claude B only if
rendered hierarchy changes.

- Confirm role degradation and citation behavior with real-shaped synthetic
  samples before any approved live smoke.
- Frontend changes remain optional and contract-driven.

## Acceptance Gate For Backend Handoff

Codex C must not begin P29C-T1 or T2 until:

- this architecture is accepted;
- one section/source approval record is complete;
- allowed use and retention are explicit;
- default and test behavior remains offline;
- no new contract field is assumed;
- review ownership is recorded in the active plan.
