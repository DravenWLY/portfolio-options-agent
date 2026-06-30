# Phase 31A - Founder Demo Polish And Product Narrative

Owner: Codex B
Status: active architecture contract
Date: 2026-06-23

## Product Position

P30A and P30B are complete. Portfolio Copilot now has a working internal MVP
validation loop:

`Trade Review -> save evidence snapshot -> Reports -> explicitly generate Agent Team briefing -> reopen saved report`

P31A should make that loop feel like a believable founder demo without
expanding product scope.

The product framing remains:

> Portfolio Copilot is a read-only specialist review desk for busy
> self-directed investors.

The product should not answer:

> Should I make this trade?

It should answer:

> What would I be ignoring if I acted manually now?

## P31A Goal

Reduce placeholder feel around the accepted golden path while preserving the
existing architecture, privacy, and safety boundaries.

P31A is not a capability-expansion phase. It is a product narrative and
presentation polish phase for the founder demo.

## In Scope

P31A may improve:

- Golden-path copy between Trade Review, evidence snapshot saving, Reports, and
  Agent Team briefing generation.
- Preview-only raw scope-note code presentation, using friendly labels mapped
  from existing reviewed codes.
- Explanatory copy for deterministic evidence, Agent Team synthesis, skipped
  roles, evidence gaps, freshness, caveats, provenance, and historical report
  readback.
- Synthetic/demo-data labeling so it is clear and graceful without making the
  product feel fake.
- Small route hygiene for visible technical artifacts that can distract from the
  founder demo, such as visible `ctx_` handles on accessible non-demo surfaces.
- Product docs and positioning language around the specialist review-desk
  concept.
- The founder demo script, only to make the accepted loop easier to present.

Frontend work must be presentation-only unless Codex B approves a separate
contract change. Frontend may map existing backend-owned codes to friendlier
display labels, as long as it does not invent new evidence, freshness,
actionability, status, or provenance semantics.

## Out Of Scope

- New public evidence sources.
- Real market-data provider work.
- Production EDGAR expansion.
- Dashboard expansion beyond direct golden-path clarification.
- Account Details redesign unless needed for demo narrative continuity.
- Agent Console composer activation.
- Interactive agent chat.
- Live LLM/provider calls.
- Broker/order/execution/staging behavior.
- Frontend financial computation.
- Auth, pricing, signup, or onboarding implementation beyond copy/docs.
- TradingAgents runtime, MCP, web search, runtime tools, or private tool calls.
- Raw private data exposure.

## Safety And Copy Boundaries

- No advice, recommendation, action-instruction, safe-to-trade, ready-to-trade,
  guaranteed-return, or AI-stock-picker posture.
- No "portfolio manager manages your money" framing.
- No order placement, order staging, broker execution, cancellation, transfer,
  or broker-action wording.
- Deterministic backend services remain the source of financial calculations.
- Agent Team output remains analysis-only and evidence-bounded.
- Synthetic/demo data must be clearly but gracefully labeled.
- Saved reports must continue to read from saved historical evidence, never from
  current selector state.

## Contract Direction

### Friendly Scope-Note Labels

Friendly labels for existing scope/caveat codes are allowed as frontend
presentation mapping under the current contract.

They do not require backend read-contract changes if:

- the frontend consumes existing reviewed code fields;
- labels are static copy for display only;
- raw codes remain available where useful for audit/debug disclosure;
- labels do not change actionability, feasibility, freshness, or report status;
- labels do not add new evidence or imply private account values were reviewed.

A backend contract change is required if agents want new fields such as
`display_label`, `severity_label`, `explanation`, grouped caveat objects, or
backend-owned user-facing copy.

### Visible `ctx_` References

Visible `ctx_` references on `/portfolio-context` are not a P30B blocker because
they are synthetic opaque app-owned handles outside the demo script. P31A may
hide, soften, or move them behind a technical disclosure if the route is
accessible during founder demo. This should be presentation-only and must not
change portfolio-context contracts.

## P31A Task Sequence

### P31A-T0 - Open Founder Demo Polish Contract

Owner: Codex B
Reviewer: Codex A/founder as needed
Status: done in this document

Define the polish scope, boundaries, task sequence, and review gates.

### P31A-T1 - Product Narrative Docs Alignment

Owner: Codex A
Reviewer: Codex B

Update PRD, MVP scope, positioning, and roadmap language where relevant so the
product is consistently described as a read-only specialist review desk. Do not
expand scope.

### P31A-T2 - Golden Path Copy And Technical-Artifact Audit

Owner: Claude A
Reviewers: Codex B and Claude B

Inventory the demo path and accessible adjacent pages for technical artifacts,
rough placeholder copy, synthetic-data labels, raw scope-note codes, and
disjointed save/generate/report continuity. Produce a narrow patch plan before
large visual changes.

### P31A-T3 - Golden Path Frontend Polish

Owner: Claude A, with Codex F as backup
Reviewers: Claude B visual/safety and Codex B contract/privacy/safety

Apply presentation-only polish to the accepted golden path:

- scope-note friendly labels;
- clearer deterministic evidence/caveat/freshness/provenance copy;
- stronger continuity from save snapshot to explicit briefing generation;
- better handling of skipped/unavailable Agent Team roles without inventing
  evidence.

### P31A-T4 - Adjacent Surface Hygiene

Owner: Codex F or Claude A
Reviewers: Claude B; Codex B if contract/privacy/copy semantics change

Minimally soften visible technical artifacts outside the demo flow only where
they can distract during founder demo. Candidate: `/portfolio-context` visible
`ctx_` references. Do not redesign Dashboard, Account Details, Agent Console, or
Portfolio Context.

### P31A-T5 - Agent Briefing Wording Check

Owner: Claude E if needed
Reviewer: Codex B

Only if frontend polish reveals confusing Agent Team wording, tighten existing
deterministic-template copy within existing report fields. No new sources,
roles, fields, or runtime tools.

### P31A-T6 - Founder Demo Polish Smoke

Owner: Claude A or Codex F
Reviewers: Claude B and Codex B

Run the founder demo script with P31A polish applied. Verify the demo feels
coherent, honest, and safe across stock/ETF and `cash_secured_put` flows.

### P31A-T7 - Founder Acceptance And Closeout

Owner: Codex B and Codex A/founder

Close when the demo can be presented without explaining internal placeholders
inside the golden path.

## Acceptance Criteria

P31A is accepted when:

- The founder demo communicates the review-desk concept clearly.
- Trade Review, save snapshot, Reports, and Agent Team briefing feel like one
  coherent loop.
- Raw technical codes are not front-and-center in the demo path.
- Synthetic/demo data is labeled clearly and gracefully.
- Skipped or unavailable Agent Team roles are honest without feeling broken.
- Deterministic evidence and Agent Team synthesis remain visibly distinct.
- Saved report historical scope/freshness/caveat/provenance remains clear.
- No new data sources, providers, frontend calculations, order/broker behavior,
  runtime tools, or private-data exposure are introduced.
- Claude B and Codex B review gates pass.

## Deferred Placeholder Areas

These remain outside P31A unless Codex A explicitly reopens them:

- Public evidence expansion beyond EDGAR company-profile metadata.
- Production-grade market data.
- Dashboard expansion.
- Account Details redesign.
- Agent Console composer.
- Auth, signup, pricing, and public onboarding implementation.
- Broad app-wide visual redesign.
- Real LLM/provider integration or TradingAgents runtime integration.
