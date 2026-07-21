# Phase 36 T7 Agent Section Content Contract

Status: finalized for P36-T7 F-DIR-1 implementation; Claude G's two K1R
required edits applied in place 2026-07-20 (availability row 2 extension;
whole-synthesis-document non-embedding rule). First implementation pass
returned BLOCKED on the composer embed + read-side suppression; Claude G
re-review required before commit.

## K1R Finalization

K2B/K2C is the committed baseline at `393af1a`. This contract now authorizes
only the backend composition and Markdown-projection change described below.
It does not authorize a schema, route, source, provider, prompt, validator, or
frontend change.

The existing frozen `SavedAgentTeamRoleSummaryRead` read contract is sufficient
for this slice: `live_report_markdown` supplies `Analysis`; `summary_markdown`
supplies `Frozen debugging details`; and the existing role status, provider
status, warning codes, unavailable reason, and evidence references supply the
reviewed metadata. No additive read-contract field is approved for K1R.

If Codex C cannot make the two-part projection solely from those existing
frozen fields without inferring content, combining fields, or exposing a new
value, implementation must stop and return the smallest additive read-contract
proposal for Codex B and Claude G review. It must not invent a fallback field
or repurpose a currently private field.

## Purpose

The 2026-07-20 five-role internal run completed safely but the analyst live
sections were withheld by output gates. This contract makes that state legible
without turning each role section into a mixed wall of role prose, deterministic
facts, and status codes.

This is a composition and projection contract only. It changes neither output
gates nor prompts, evidence acquisition, provider behavior, persistence, source
rights, frozen-readback behavior, or the Portfolio Manager prompt.

## Scope

Applies to the tool-mediated saved-report role sections in the backend composer,
the generated Markdown projection, and a later frontend read-only rendering.
It applies equally to a newly generated report and historical frozen readback.

It does not apply to the legacy console, a live Agent Console run, or the
deterministic Trade Review surface.

## Binding Rendering Rule

For each role, the report has two explicitly labeled parts:

1. `Analysis`: only the accepted live analysis authored for that same role.
2. `Frozen debugging details`: backend-owned, historical facts about that role's
   evidence, freshness, scope, availability, caveats, and output review status.

`Analysis` must render `live_report_markdown` verbatim when it is present and
accepted. It must not append, prepend, or interleave `summary_markdown`,
deterministic finding text, freshness narration, scope narration, tool status,
warning labels, citations, or text from another role. This is the only
user-facing analyst narrative in the primary role section.

If accepted live analysis is absent, `Analysis` renders exactly one static,
closed-vocabulary line selected by backend status:

| Condition | Visible analysis line |
| --- | --- |
| A safety or output gate withheld the role prose | `Live analysis was withheld by review safeguards.` |
| Provider or role execution was unavailable, or no live analysis was attempted for this saved report | `Live analysis was unavailable for this saved report.` |
| No role evidence was available | `Analysis was not available from the frozen evidence package.` |

The line is an availability disclosure, not an explanation, conclusion, or
recommendation. It contains no raw warning code, private data, provider detail,
or inference about the trade.

## Frozen Debugging Details

The debugging subsection is clearly labeled `Frozen debugging details`, is
visually and semantically secondary to `Analysis`, and is the sole location in
this projection for deterministic role material. It may show only data already
permitted in the frozen report read contract and only for the same role:

- the role's deterministic `summary_markdown` or deterministic findings;
- humanized availability, freshness, scope, caveat, and warning labels;
- safe evidence/provenance labels and opaque reviewed references already allowed
  by the saved-report contract;
- the closed availability state used for the Analysis line.

It must not show raw tool payloads, URLs, prompts, traces, provider responses,
provider keys, account/provider/broker identifiers, account numbers, balances,
buying power, holdings, positions, quantities, lots, or any current-state data.
Codes are humanized through the existing display-label path. Unknown internal
tokens remain unavailable rather than being rendered as raw text.

The subsection is a frozen audit aid, not a second analyst narrative. It does
not render a new calculation, recompute evidence, or cause a source or provider
call. Historical reports render exactly their saved content.

## Cross-Role Separation

- An analyst's `Analysis` can contain only that analyst's accepted role prose.
- Deterministic facts assigned to one role cannot be copied into another
  analyst's Analysis.
- The Portfolio Manager section contains only the Portfolio Manager's accepted
  synthesis. It may make a high-level, non-verdict-capable synthesis of the
  frozen package but must not embed an analyst's `live_report_markdown`,
  deterministic section, or debugging subsection verbatim.
- The final synthesis document as a whole must not embed any analyst's
  `live_report_markdown` or its absence-fallback line. The existing Market
  context embed of the Technical Analyst note is removed by this contract; the
  deterministic market-context table remains. This non-embedding rule is a
  composition invariant for newly generated documents; historical frozen
  documents render exactly their saved content.
- This contract does not change the existing PM prompt input or PM gate. It
  constrains only user-facing composition and readback projection.

## Required Behavior and Tests

Codex C's implementation must add focused offline tests that prove:

1. accepted role prose appears only in its own `Analysis` subsection;
2. deterministic role facts appear only in that role's `Frozen debugging
   details`, never mixed into `Analysis`;
3. each withheld/unavailable/no-evidence state renders exactly one approved
   availability line and preserves its humanized debugging metadata;
4. the PM section does not reproduce any analyst section verbatim;
5. frozen readback is byte-stable and performs zero provider/source calls;
6. all current output safety, private-data, URL, advice, order, execution,
   safe-to-trade, ready-to-trade, and guaranteed-return checks remain green;
7. gate outcomes and warning-code semantics are unchanged from the pre-slice
   runner for the same deterministic and fake-provider inputs.

8. the implementation reads only the saved role summary and frozen artifact;
   it performs no provider, source, selector, Account Details, or current-scope
   lookup while composing either subsection.

No schema expansion is approved for this slice. If the existing frozen role
summary cannot represent the two subsections without guessing, stop and return
the smallest additive read-contract proposal for Codex B and Claude G review.

## Delivery Sequence

1. Codex C implements only this composition/projection change against the
   finalized K1R contract and committed K2B/K2C baseline.
2. Codex B performs contract/readback review.
3. Claude G performs the final architecture/privacy review of the implemented
   projection before it is accepted.
4. The frontend follows later, display-only, using the same two-part rule and
   no new report fields.

## Non-Goals

- No output-gate threshold or validator change.
- No prompt tuning, provider change, source expansion, or live run.
- No frontend implementation in this slice.
- No second live validation without fresh founder authorization.

## Amendment — K3 additive status field (Codex B binding decision, K3A-R1)

Recorded by Claude E at Codex B's direction while resolving the P36-T7-K3A
design blockers. See
`docs/claude-e-agentic/PHASE_36_T7_K3A_ANALYST_OUTPUT_SURVIVAL_DESIGN.md` §5.

K3 authorizes **exactly two** additive fields and no other expansion:

```python
analysis_status: Literal[
    "accepted", "withheld_by_review", "provider_unavailable", "no_evidence"
] | None = None
```

- It is added to the frozen source model and to the read projection.
- It is **nullable with default `None`**. It must not default to
  `no_evidence`: a pre-K3 artifact never had this state evaluated, and
  stamping one would retroactively assert a status that was never determined.
- **Historical artifacts carrying `None` retain the existing K1-compatible
  projection behavior exactly** — the two-part rendering rule above is
  unchanged for them. No migration and no backfill.
- Every newly generated K3 role writes a non-null value, asserted by test.
- `analysis_status == "accepted"` becomes the sole signal that a role's
  `Analysis` may render composed live analysis for a K3 run; any other
  non-null value renders exactly one approved availability line from the table
  above. A completed provider request is explicitly not sufficient.

K3 also authorizes this metadata-only frozen tool-run artifact field:

```python
pm_fallback_reason: Literal["unavailable", "gate_drop"] | None = None
```

- It has a closed vocabulary and defaults to `None` for successful synthesis
  and legacy artifacts.
- It records only the deterministic PM fallback category after the P36-T7-L1
  regression; it does not expose provider content, prompts, calculations, or
  new report facts.
- It is rendered solely through one of the two approved static PM fallback
  disclosure lines, never as free-form metadata or new user-visible prose.

No other field, subsection, or projection behavior is expanded by K3. The
binding rendering rule, cross-role separation rule, and privacy constraints of
this contract remain in force unchanged.

## Amendment — M2 truncation status (Codex B binding decision, M2-R1)

Recorded by Claude E at Codex B's direction while resolving the P36-T7-M2
design blockers. See
`docs/claude-e-agentic/PHASE_36_T7_M2_ANALYST_CONSTRAINT_REMOVAL.md` §8.1.

The L2 run classified a Fundamentals response as `provider_unavailable` while
`provider_status` was `ok` — a **content** outcome reported as an
**availability** outcome. M2 splits the two. The `analysis_status`
enumeration above gains exactly one additive value:

```python
analysis_status: Literal[
    "accepted", "withheld_by_review", "provider_unavailable",
    "note_incomplete_response", "no_evidence"
] | None = None
```

- `note_incomplete_response` is set **only** when the provider returned a
  response whose finish reason is `length`. Every other outcome keeps its
  current classification: transport failure, auth error, timeout, and
  quota/rate-limit results remain `provider_unavailable`.
- One additive closed warning code accompanies it:
  `live_note_incomplete_response`.
- The rendering table above gains exactly one row:

| Condition | Visible analysis line |
| --- | --- |
| The live response arrived incomplete | `Live analysis was incomplete for this saved report.` |

  The line follows the same rule as the others: an availability disclosure,
  not an explanation, conclusion, or recommendation. It discloses no provider
  detail, no internals, and no blame.
- **Historical artifacts remain `analysis_status = None` with unchanged
  behavior.** No migration, no backfill, no re-derivation.
- No gate, threshold, source, provider, PM-prompt, or
  no-facts/advice/privacy rule changes accompany this value.
