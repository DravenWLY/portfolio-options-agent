# Phase 29B Public Agent Evidence Contract

Status: accepted direction; design handoff ready
Owner: Codex B
Implementation/design owners: Codex C and Claude E
Related plan: `docs/shared/implementation_plan.md` Phase 29B
Builds on:
- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- P29A saved evidence package and Agent Team report generation path

## Purpose

Phase 29A made Agent Team reports reproducible from immutable saved evidence.
The public analyst roles are still skipped because no reviewed public evidence
contract exists for them.

Phase 29B defines the public-evidence boundary that lets these roles become real
contributors without widening private brokerage exposure:

- `fundamentals_analyst`
- `news_analyst`
- `technical_analyst`

This phase is about reviewed evidence contracts, source/rights boundaries, role
projections, validation, and graceful degradation. It is not a frontend redesign
phase and it is not a provider-selection free-for-all.

## Architecture Decision

Public analyst roles may consume only backend-built, reviewed public evidence
sections that are persisted or attached to the saved evidence package at report
generation time.

The core P29A decisions remain unchanged:

- evidence-package-first;
- deterministic backend services own calculations;
- saved reports are reproducible from generation-time evidence;
- private brokerage/account data never flows raw into LLM prompts, saved
  reports, frontend contracts, logs, traces, or public-role evidence;
- runtime private tools and private MCP remain deferred;
- report generation remains explicit and manual;
- no order placement, execution, advice, recommendation, guaranteed-return, or
  safe/ready-to-trade wording.

Public evidence is allowed because it is not brokerage data, but it still needs
the same validation discipline: provenance, source rights, freshness, allowed
fields, role-specific projections, and output safety.

## Codex C And Claude E Design Freedom

Codex C and Claude E have broad freedom to design the backend and agentic
implementation inside the hard rails in this document.

Codex C may choose:

- the backend schema shapes for public evidence sections;
- whether to model public evidence as a saved-evidence-package extension,
  generation-time attachment, provider cache, or adapter-backed projection;
- the source adapter interfaces and fake/test providers;
- persistence strategy, if any, as long as saved reports remain reproducible;
- validator implementation details and test organization.

Claude E may choose:

- per-role prompt/evidence projection shapes;
- role degradation behavior when evidence is absent, stale, limited, or
  provider-unavailable;
- role summary structure and how public role outputs are synthesized by the
  portfolio manager role;
- evaluation cases and safety checks for generated public-role narrative;
- how to preserve the existing Agent Team report output contract or propose
  additive changes.

The only constraint on that freedom is architectural: no design may bypass the
approved evidence package, expose private data, introduce live runtime tools by
default, or weaken the safety language rules.

## Source And Rights Boundary

Public evidence must come from reviewed source categories. Before production
display or LLM use, every source category needs an explicit source/rights answer:

- provider name or source category;
- allowed use: internal demo, LLM summarization, saved report display, citations,
  screenshots/exports, or production UI display;
- retention policy: generated-only, cached, persisted in saved artifact, or not
  stored;
- attribution requirements;
- refresh/freshness expectations;
- forbidden content shape.

Hard rules:

- no browser scraping;
- no broker scraping;
- no bypassing paywalls, auth walls, robots restrictions, or source terms;
- no copying full articles, transcripts, or provider payloads into prompts or
  saved reports unless a reviewed license explicitly allows it;
- no raw provider payloads in frontend contracts, saved reports, logs, prompts,
  or test fixtures;
- no source URLs, IDs, or bodies that leak user-specific or credentialed access;
- mocked/fake public evidence remains the default for tests.

If rights are not reviewed, the evidence section must be marked
`not_reviewed` or `not_available`, and the role must degrade honestly.

## Public Evidence Sections

The initial contract should support additive evidence sections. Recommended
section keys:

- `public_company_profile`
- `public_fundamentals_snapshot`
- `public_news_snapshot`
- `public_events_calendar`
- `public_technical_context`
- `public_market_context`

Codex C and Claude E may merge, split, or rename these during design review if
the resulting keys are stable, validated, and role-citation rules are updated.

All public evidence sections should carry:

- `section_key`;
- `availability`: `available`, `limited`, `not_available`, `not_reviewed`, or
  `not_applicable`;
- `freshness_label` or `freshness_category`;
- `as_of` / `published_at` / `collected_at` when meaningful;
- `source_label` or provider-neutral source category;
- `rights_status`: `reviewed`, `internal_demo_only`, `not_reviewed`, or
  equivalent;
- short `limitations`;
- sanitized, bounded facts or summaries only.

The package must fail closed if a public evidence section contains forbidden
private-data keys, raw provider payload hints, prompt/trace fields, or unsafe
trading language.

## Allowed Content By Role

### Fundamentals Analyst

May consume:

- reviewed public company/fund profile fields;
- reviewed high-level fundamentals labels or categories;
- reviewed event context that affects company/fund understanding.

May output:

- qualitative framing of what public company/fund evidence says;
- explicit unknowns and limitations;
- non-directional context for the reviewed instrument.

Must not output:

- invented valuation metrics;
- price targets;
- buy/sell/hold conclusions;
- "cheap", "overvalued", "undervalued" as an investment verdict unless the
  source explicitly supplies a neutral, licensed label and the wording remains
  non-advice;
- portfolio/account-specific interpretation.

### News Analyst

May consume:

- reviewed public news/event metadata;
- reviewed licensed short summaries;
- earnings/dividend/corporate-event timing if source rights allow;
- market/economic context that is already approved for reports.

May output:

- neutral event summaries;
- what is known, unknown, stale, or unavailable;
- potential topics for the user to verify manually.

Must not output:

- predictions of price movement;
- "trade before/after event" framing;
- article bodies or long excerpts;
- urgency or fear/greed language;
- unlicensed source text.

### Technical Analyst

May consume:

- reviewed public market context;
- backend-owned technical-context labels, if Codex C defines them;
- quote freshness categories and non-private market-data provenance.

May output:

- neutral market-context framing;
- freshness and limitation notes;
- non-directional observations from backend-approved labels.

Must not output:

- entry/exit instructions;
- support/resistance levels invented by an LLM;
- price targets;
- indicator values unless backend-calculated or source-provided under reviewed
  rights;
- "signal says buy/sell" language.

## Role Projection Rules

Public analyst prompts may receive only their role-specific public evidence
projection plus the minimal trade-intent context needed to identify the reviewed
instrument.

They must not receive:

- account labels or account references;
- broker/provider/account IDs;
- balances, buying power, cash, holdings, positions, quantities, lots,
  transactions, orders, thresholds, or private strategy settings;
- raw deterministic portfolio-impact sections unless explicitly allowed for a
  portfolio-aware role;
- raw provider payloads;
- prompt text, LLM traces, tool traces, secrets, or API keys.

The portfolio manager role may consume public role summaries after they pass
validation. It must not treat public role summaries as recommendations or use
them to produce a decision verdict.

## Saved Report Reproducibility

Any public evidence used to generate a saved Agent Team report must be
reproducible from the saved artifact or from immutable generation-time evidence
references.

Allowed approaches:

- persist sanitized public evidence sections in the saved artifact;
- persist stable generation-time public evidence snapshots in a report-owned
  table;
- persist stable evidence references plus enough sanitized display fields to
  reproduce the report without calling current providers.

Not allowed:

- silently re-fetching current public data when opening an old report;
- silently regenerating old public sections with newer provider data;
- recomputing report narrative from current market/news state;
- treating current source freshness as historical report freshness.

## Validation Requirements

The public evidence validator must reject or strip:

- private brokerage/account keys or values;
- raw payload, raw metadata, prompt, trace, completion, token, secret, API key,
  access token, provider response body, or unreviewed URL/body fields;
- advice/recommendation/order/execution wording;
- guaranteed-return or safe/ready-to-trade wording;
- article bodies or long excerpts unless separately approved;
- role citations to unavailable or unreviewed sections;
- role citations outside that role's allowed public-evidence set.

Generated public-role output must also pass the existing Agent Team report
output validator or a stricter additive validator before persistence.

Validation failures must fail closed:

- offending text is not persisted;
- role status becomes `validation_failed` or equivalent;
- report falls back to deterministic evidence and safe role availability
  messaging.

## Provider And Runtime Tool Boundary

Phase 29B may define backend provider adapters or fake providers, but Agent Team
roles do not call public-data providers directly at runtime.

Allowed:

- backend-owned public evidence assembly before report generation;
- fake/mock public evidence for tests and internal demos;
- cached public evidence if source rights and retention are reviewed;
- provider-unavailable states that degrade honestly.

Deferred:

- live public web search inside an agent;
- runtime agent tools for public evidence;
- streaming public evidence retrieval;
- source-specific production display beyond reviewed rights.

Prohibited:

- private MCP/tool access;
- broker/provider account tools;
- unreviewed scraping;
- live TradingAgents tool execution;
- LLM-generated deterministic metrics.

## Frontend Boundary

No frontend implementation is required to start Phase 29B.

The existing Reports UI may continue to show compact coverage notes until public
roles produce validated summaries. The frontend should not invent public role
fields or infer missing evidence from symbols, routes, account state, or current
market data.

When public role summaries are available, frontend agents may optimize display,
but only by consuming reviewed report fields.

## When To Introduce Claude Design Or Stitch

Do not introduce Claude Design or Stitch at the start of Phase 29B. The first
work is backend/agent evidence design, and visual exploration before stable
sample payloads would encourage invented fields.

Introduce Claude Design when all of these are true:

- Codex C has a reviewed public evidence read contract or realistic synthetic
  sample payloads;
- Claude E has a reviewed public-role output contract and role-state examples;
- the product question is about information hierarchy, report readability, role
  grouping, citation/provenance display, or comparison between generated and
  deterministic content;
- Codex B can provide hard contract rails and forbidden wording.

Use Claude Design for divergent concepts: how richer Agent Team reports should
feel, how public roles sit beside portfolio-aware roles, how coverage and
provenance should be understood, and how much public context belongs in the
main report versus disclosure.

Introduce Stitch only after a direction is chosen and the team wants to optimize
or implement frontend UI quickly from a stable design target. Use it for
component/layout acceleration, not for deciding backend fields or evidence
semantics. Stitch should consume reviewed mock data and must not create new API
fields, new finance calculations, or new report states.

Claude B remains the visual/safety reviewer after any design or Stitch-assisted
frontend work. Codex B reviews only contract/privacy/safety seams.

## Phase 29B Task Split

### P29B-T0 Architecture Contract

Owner: Codex B.

Define the public evidence architecture, role boundaries, source/rights rules,
design freedom, validation requirements, and frontend timing.

Acceptance:

- public roles can become real contributors without private data exposure;
- Codex C and Claude E have broad design freedom inside explicit rails;
- source/rights review is required before production public evidence display or
  LLM use;
- runtime tools remain deferred by default;
- frontend design tools are sequenced after stable contracts and samples.

### P29B-T1 Backend Public Evidence Contract And Projection Design

Owner: Codex C.
Reviewer: Codex B.

Goal:

Design and, if scoped, implement the backend public evidence schema/projection
that can extend saved evidence packages for public analyst roles.

Freedom:

Codex C may choose schema names, section split, adapter boundaries, persistence
strategy, fake-provider shape, and validator internals, as long as the hard
contract in this document is preserved.

Acceptance:

- public evidence sections are additive and backward-compatible;
- all public sections include availability, freshness/provenance, rights status,
  limitations, and stable section keys;
- saved reports remain reproducible without current-provider re-fetch;
- validators reject private keys, raw payloads, unreviewed article bodies,
  unsafe wording, prompts, traces, and secrets;
- tests use synthetic public evidence and mocked/fake providers only.

### P29B-T2 Public Role Agentic Design

Owner: Claude E.
Reviewer: Codex B.

Goal:

Design the public-role evidence projections, role behavior, output rules,
degraded states, and validation/evaluation plan for fundamentals, news, and
technical analysts.

Freedom:

Claude E may choose prompt/projection shape, role degradation semantics,
evaluation cases, role output structure, and whether additive report-output
fields are needed.

Acceptance:

- public roles cite only approved available/limited public evidence sections;
- missing/unreviewed evidence degrades honestly;
- generated output remains analysis-only and avoids advice/order/execution,
  guaranteed-return, safe/ready-to-trade, and buy/sell instruction wording;
- portfolio manager synthesis can use validated public role summaries without
  turning them into recommendations;
- no prompts, traces, raw provider payloads, private data, or tool outputs are
  saved or exposed.

### P29B-T3 Integrated Backend / Agent Implementation

Owner: Codex C and Claude E, sequenced by their design outputs.
Reviewers: Codex B; Claude E or Codex C cross-review as appropriate.

Implement the reviewed P29B-T1/T2 design in the smallest safe slice. Default to
mock/fake public evidence unless source/rights approval exists for a real
provider.

Acceptance:

- public roles can produce validated sections from synthetic reviewed public
  evidence;
- unavailable/unreviewed sources preserve honest skipped/degraded states;
- reports remain reproducible from saved generation-time evidence;
- default tests are offline, deterministic, and synthetic;
- no frontend work is required unless the read contract changes need type
  mirrors.

### P29B-T4 Frontend Rich Report Optimization

Owner: Claude A or Codex F.
Reviewers: Claude B and Codex B.
Dependency: P29B-T3 reviewed and accepted, with stable sample payloads.

Optimize Reports UI for richer public + portfolio-aware role output. This is
where Claude Design or Stitch may be introduced under the timing rules above.

Acceptance:

- frontend consumes reviewed fields only;
- no invented public evidence, role states, calculations, or citations;
- public-role coverage/provenance is understandable without overwhelming the
  report;
- no advice/execution/trading-readiness language;
- full-stack preview uses synthetic/demo data only.

## Deferred

- real production provider selection;
- production source/rights approval;
- frontend redesign before stable payloads;
- runtime public-data tools;
- public/private MCP;
- report export/share/version comparison;
- auto-generation after save;
- any broker action or execution workflow.
