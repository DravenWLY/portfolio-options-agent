# Phase 30B - Golden Path Prototype Hardening And Demo Readiness

Owner: Codex B
Status: accepted founder demo checkpoint
Date: 2026-06-22

## Product Position

Phase 30A proved the first coherent Portfolio Copilot loop:

`select review account/scope -> enter proposed trade -> run deterministic review -> save evidence snapshot -> explicitly generate Agent Team briefing -> reopen the exact historical report`

Phase 30B should harden that accepted loop until it is durable,
reproducible, and ready for founder demo and internal MVP validation.

The product framing remains:

> Portfolio Copilot is a read-only specialist review desk for busy
> self-directed investors.

The app should not answer "Should I make this trade?" It should answer:

> What would I be ignoring if I acted manually now?

## P30B Goal

Make the P30A golden path trustworthy outside the private-safe smoke harness:

1. Prove the real DB-backed saved-review/report-generation chain with
   integration tests.
2. Keep private-safe fixtures clearly bounded as smoke overlays, not product
   demo data.
3. Add a stable synthetic demo seed path that can reproduce the founder demo
   without real brokerage data.
4. Create a founder-demo script for one stock/ETF flow and one simple options
   flow.
5. Apply only narrow copy/onboarding polish where it directly clarifies the
   review-desk loop.

## Current Coverage Split

### Real DB-backed coverage already exists

The backend test suite already covers important pieces of the chain:

- Portfolio-backed Trade Review can record a backend-owned
  `saved_review_source_reference`.
- Saving from a reviewed trade-review source ignores client-supplied mutable
  scope/summary fields and persists generation-time scope.
- Report list/detail read saved scope and summary state without reinterpreting
  later mutable account state.
- Explicit Agent Team report generation persists a summary and projects it on
  report list/detail.
- Regeneration updates generated report state while preserving the immutable
  saved source fields and saved public evidence.
- Unsafe private fields, unsafe wording, malformed source refs, and cross-user
  source access fail closed.

### P30A behavior covered only by private-safe fixtures/smoke

The connected browser proof used the dev/test-only Skyframe fixture overlay for
the full interactive loop:

- `POST /trade-reviews/portfolio-preview` for stock/ETF and
  `cash_secured_put` paths.
- `POST /users/{uid}/reports/from-trade-review`.
- `POST /users/{uid}/reports/{thread_id}/agent-team-report`.
- Five report display states: `source_snapshot`, `full_agent_report`,
  `deterministic_draft`, `agent_unavailable`, and `validation_failed`.
- Manual generation click behavior and no-auto-generation behavior.

Those fixtures are useful for private-safe UI smoke, but they are not a
substitute for DB-backed integration tests or a stable demo seed.

## Backend Integration-Test Plan

P30B-T1 should add DB-enabled tests that exercise the real route spine, not the
Skyframe fixture overlay.

Required stock/ETF chain:

1. Create a synthetic user, broker connection, broker account, and reviewed
   account/scope setup using test factories or existing test helpers.
2. Call `POST /trade-reviews/portfolio-preview` with a stock/ETF flow and a
   selected reviewed account/scope.
3. Assert a valid `saved_review_source_reference` is returned and persisted.
4. Call `POST /users/{uid}/reports/from-trade-review` with only the reviewed
   source reference and normal save metadata.
5. Assert the saved artifact uses backend-owned generation-time scope,
   deterministic summary, caveats, and freshness.
6. Call `POST /users/{uid}/reports/{thread_id}/agent-team-report`.
7. Assert the generated summary is read from the saved evidence package and is
   visible through `GET /users/{uid}/reports` and
   `GET /users/{uid}/reports/{thread_id}`.
8. Mutate or add later current account/context state after the save, then
   assert report readback and regeneration preserve the saved source fields and
   do not silently reinterpret current selector state.

Required simple-options chain:

1. Repeat the same chain for one simple options flow, preferably
   `cash_secured_put`.
2. Assert options-specific caveats and scope/feasibility limitations are
   preserved in the saved artifact/report evidence.
3. Keep account-level feasibility caveats honest when real account-level
   feasibility is not evaluated by the reviewed contract.

Required regeneration/retry chain:

1. Generate a report once.
2. Regenerate or retry via the explicit generation endpoint.
3. Assert saved source, scope, deterministic summary, saved public evidence,
   source timestamps, and immutable artifact fields are preserved.
4. Assert no current-account selector state is consulted for saved report
   readback or regeneration.

Required failure and safety assertions:

- Cross-user source references fail closed.
- Unsupported or malformed source references fail closed.
- Client-supplied scope/summary fields are ignored when a reviewed source
  exists.
- Forbidden private fields and unsafe trading/action wording cannot be saved or
  generated.
- No raw account/provider/broker IDs, raw payloads, prompts, traces, secrets, or
  opaque save refs are exposed in report read contracts.

## Fixture And Demo Seed Plan

### Fixture cleanup boundary

The existing Skyframe fixture overlay should remain:

- dev/test-only;
- gated by explicit fixture headers and local/test environment;
- private-safe and synthetic-only;
- stateless;
- a UI smoke harness, not canonical demo data.

P30B should document that boundary in code/tests/docs and avoid growing the
overlay into a second product backend.

### Stable synthetic demo seed

The demo seed should be separate from the Skyframe overlay.

Recommended properties:

- Backend-owned and idempotent.
- Local/internal only.
- Uses mock providers and synthetic account/scope data only.
- Does not require broker, market-data, EDGAR, LLM, TradingAgents, web, MCP, or
  external provider calls.
- Does not persist raw provider payloads, real-looking account numbers, broker
  IDs, provider IDs, prompts, traces, secrets, or real user data.
- Creates enough reviewed synthetic state for one stock/ETF flow and one
  `cash_secured_put` or `covered_call` flow to run through the real app routes.
- Can be reset and rerun without accumulating confusing duplicate demo rows.

The exact implementation path is a Codex C decision, but preferred shape is a
small backend seed helper or script with tests, not frontend mocks.

## Frontend Demo Readiness

Existing routes should be sufficient by default:

- Trade Review for input and deterministic review.
- Reports for save, manual generation, and report readback.
- Report Detail for the saved specialist briefing.

Do not add a demo-specific frontend flow unless the stable seed proves the
existing navigation is too ambiguous for a founder demo. Any frontend change
must be presentation-only, use reviewed read fields, and go through Claude B
visual/safety review. Codex B re-reviews if wording, privacy, report semantics,
or frontend read-contract assumptions change.

## Founder Demo Script Outline

1. Start the app with the stable synthetic demo seed loaded.
2. Select the synthetic review user/account/scope.
3. Open Trade Review and show the read-only/manual boundary.
4. Run the stock/ETF review.
5. Point out deterministic review status, broker freshness, market quote
   freshness, caveats, and scope.
6. Save the evidence snapshot and note that nothing is generated automatically.
7. Open Reports and explicitly generate the Agent Team briefing.
8. Show the saved report: synthesis first, role-separated flags, deterministic
   facts, provenance, timestamps, and caveats.
9. Reopen the report and confirm it is historical saved evidence, not current
   selector state.
10. Repeat the loop for one simple options flow, preferably
    `cash_secured_put`, highlighting assignment/collateral caveats only as
    analysis context.
11. End by restating the boundary: read-only specialist briefing, no order
    placement, no recommendation, no safe/ready-to-trade verdict.

## Out Of Scope

- New public evidence sources.
- Production EDGAR expansion.
- Market-data provider expansion.
- Broker/order/execution behavior.
- Agent Console composer activation or interactive agent chat.
- Runtime TradingAgents, web search, MCP tools, or live LLM/provider calls.
- Frontend financial computation.
- Dashboard expansion, Account Details redesign, or broader product surfaces
  unless directly required for the accepted golden path.

## P30B Task Sequence

### P30B-T0 - Open Hardening Contract

Owner: Codex B
Reviewer: Codex A/founder as needed
Status: done in this document

Define the hardening goal, coverage split, integration-test plan, fixture/demo
seed boundary, demo script, and review gates.

### P30B-T1 - DB-Backed Golden Path Integration Tests

Owner: Codex C
Reviewer: Codex B

Implement the backend integration-test plan for one stock/ETF flow and one
simple options flow. Prefer tests only unless a genuine contract gap is found.
Stop for Codex B review before any production code or schema changes.

### P30B-T2 - Stable Synthetic Demo Seed

Owner: Codex C
Reviewer: Codex B

Design and implement an idempotent local/internal synthetic demo seed for the
accepted golden path. Keep it separate from the Skyframe fixture overlay and use
mock/synthetic data only.

### P30B-T3 - Fixture Boundary Cleanup

Owner: Codex C
Reviewer: Codex B

Rename, document, or consolidate fixture helpers only where needed to make the
Skyframe overlay clearly a private-safe smoke harness. Do not remove useful
coverage before the stable seed exists.

### P30B-T4 - Founder Demo Script And Narrow UX Polish

Owner: Claude A or Codex F
Reviewer: Claude B; Codex B if copy/contract/privacy changes

Write the founder-demo script and apply only narrow copy/onboarding polish that
directly clarifies the review-desk loop.

### P30B-T5 - Demo Readiness Smoke

Owner: Claude A or Codex F
Reviewer: Claude B and Codex B

Run the demo script against the stable synthetic seed for one stock/ETF flow and
one simple options flow. Verify no unsafe wording, no private-data exposure, no
hidden recomputation, no auto-generation, and no layout regressions.

### P30B-T6 - Founder Demo Acceptance And Closeout

Owner: Codex B and Codex A/founder

Close only when the demo is reproducible from a clean local/internal setup and
the real DB-backed route spine is covered.

## Review Gates

- Codex B reviews backend integration tests, demo seed contracts, fixture
  boundaries, privacy/safety wording, and any read-contract assumptions.
- Claude B reviews any frontend visual/Skyframe/product-safety work.
- Codex A/founder accepts the final demo script and demo readiness result.
- Any new field, endpoint, provider, source, storage write, or report semantic
  change requires a separate Codex B contract/privacy review before
  implementation.

## P30B Acceptance Criteria

P30B is accepted when:

- DB-enabled integration tests prove the real stock/ETF and simple-options
  golden paths through preview, save, explicit generation, report readback, and
  regeneration.
- Tests demonstrate saved reports do not silently recompute from current
  account selector state.
- A stable synthetic demo seed can reproduce the golden path without real
  brokerage data, external providers, LLM calls, TradingAgents, web, MCP, or
  frontend mocks.
- Skyframe/private-safe fixtures are documented as smoke overlays and are not
  confused with product demo data.
- The founder-demo script covers one stock/ETF flow and one simple options
  flow.
- Demo readiness smoke passes with no unsafe trading/action wording, no
  private-data leaks, no auto-generation, and no order/broker-action posture.
