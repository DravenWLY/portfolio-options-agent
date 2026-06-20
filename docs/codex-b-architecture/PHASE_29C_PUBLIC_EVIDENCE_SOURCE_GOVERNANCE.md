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

The recommended first slice is one low-volatility structured section, not news.
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
- Define the fail-closed source policy boundary and fake adapter.
- Preserve the existing `SavedPublicEvidencePackageRead` contract by default.
- Make no external calls in tests or default runtime.

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
