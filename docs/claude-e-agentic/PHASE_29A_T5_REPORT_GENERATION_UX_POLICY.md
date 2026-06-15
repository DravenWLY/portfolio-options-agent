# Phase 29A-T5 Report Generation UX Policy And Trigger Model

Status: policy accepted (design/product architecture only; no code
implementation). Codex B review PASS 2026-06-15; product sign-off (manual vs
auto) remains with Codex A / founder.
Owner: Claude E (agentic-system / product architecture)
Reviewer: Codex B (architecture/privacy/safety); product sign-off: Codex A / founder
Related plan: `docs/shared/implementation_plan.md` Phase 29A, task `P29A-T5`
Builds on (shipped): P29A-T1 evidence package, P29A-T2 report output contract,
P29A-T3 generation backend path, P29A-T4/T4A Reports redesign.
References:
- `docs/codex-b-architecture/PHASE_29A_AGENT_TEAM_REPORT_ARCHITECTURE.md`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- `docs/codex-b-architecture/PHASE_28A_SAVED_REVIEW_ARTIFACT_CONTRACT.md`

## 1. Scope And What Already Exists

This task defines the **product/contract policy** for when and how a saved
review snapshot becomes an Agent Team report, and the honest user-facing
lifecycle across the existing states. It is design-only. No code, no
provider/LLM/broker/market-data/TradingAgents calls, no private-tier tools, no
order/execution surfaces, no advice wording.

What the shipped foundation already does (the policy must stay coherent with
it):

- Save: `POST /users/{uid}/reports/from-trade-review` persists an immutable
  source snapshot (`agent_summary = None` → `report_status = source_snapshot`).
- Generate: `POST /users/{uid}/reports/{thread_id}/agent-team-report` runs the
  Agent Team **on demand** from the saved evidence package only, then persists
  `agent_summary` (role summaries, synthesis, `report_status`,
  `evidence_schema_version`, `evidence_references`, `warning_codes`).
- Read: `AgentTeamReportRead.from_saved_review_artifact` derives the report from
  the saved artifact (+ its `SavedEvidencePackageRead`) with
  `report_built_at = now`; never reads current account state.
- Reports UI leads with synthesis + role sections; deterministic
  scope/evidence/caveats are supporting provenance; the Generate action is gated
  to snapshots that carry saved scope; honest states exist for
  `source_snapshot` / `deterministic_draft` / `agent_unavailable` /
  `validation_failed`.

So the product is **already manual on-demand**. T5 ratifies, sharpens, and fills
the gaps (timestamps, transient generating state, regeneration, partial
coverage) rather than rebuilding.

## 2. Recommended Policy: Guided Manual (Explicit Trigger)

**Recommendation: keep generation manual and explicitly user-triggered — never
automatic, never silent — but make the next step clearly guided.** This is a
hybrid only in the sense that the product *suggests* generation without ever
*auto-spending*: save captures, Reports synthesizes on an explicit click.

Rejected alternatives:

- **Automatic after save.** Rejected. It couples save latency/reliability to
  provider latency/availability; spends provider budget on snapshots the user
  may never open; turns a fast, always-succeeds "save" into a flaky one when the
  provider is down (every save would degrade to `agent_unavailable` noise); and
  nudges the product toward an "auto-analyzer / AI stock-picker" posture that
  contradicts the manual-decision-support north star. It is also low value
  *today*: public analyst roles are skipped and synthesis is portfolio-aware
  only, so auto-generating now produces thin reports at real cost.
- **Automatic in some states only.** Rejected for now. A conditional auto-trigger
  (non-blocked actionability + healthy provider + complete-enough scope + a
  per-user opt-in) adds config surface and a preference model that overlaps the
  **deferred** scope/preference-management work. Revisit as an *opt-in*
  preference after public-evidence roles land (section 8), not before.

Why guided-manual is best for Portfolio Copilot:

- **Honest and cost-bounded.** The user decides when synthesis (and any provider
  cost/latency) happens. No surprise spend, no implied automation.
- **Save stays atomic and reliable.** A failed/slow generation can never corrupt
  or block the act of saving the snapshot.
- **`source_snapshot` is a legitimate first-class end state.** A user may keep a
  deterministic snapshot forever and never generate — it is complete, not a
  defect or a half-finished draft.
- **Reproducible.** Generation reads only the immutable saved evidence;
  re-rendering and (explicit) re-generation never recompute from current account
  state.
- **North-star aligned.** "Manual decision support," role-bounded commentary,
  deterministic backend as the calculation/evidence foundation.

### 2.1 Answer: should `source_snapshot` stay first-class?

Yes. `source_snapshot` is a stable, durable, valid object the user may keep
indefinitely without ever generating an Agent Team report. The UI must present
it as a complete saved analysis (deterministic evidence + scope + caveats), with
generation offered as an *optional enrichment*, not as a missing/required step.
It must never be labeled as incomplete, pending, broken, or "not ready."

## 3. State Model And Lifecycle

Persisted report statuses are unchanged from the shipped contract
(`AgentTeamReportStatus`): `source_snapshot`, `deterministic_draft`,
`full_agent_report`, `agent_unavailable`, `validation_failed`. T5 adds one
**transient, non-persisted** UI state and clarifies the persisted ones.

Lifecycle: **save → (optional) generate → revisit.**

1. **Review → Save (Trade Review).** User saves a source snapshot. Persisted:
   immutable evidence/scope/deterministic summary. Status: `source_snapshot`.
   Trade Review shows a non-blocking confirmation and a *suggestion* (not an
   auto-action) to generate in Reports (section 6).
2. **Offer (Reports).** The snapshot appears in the Reports library with an
   honest "Agent Team analysis not generated yet" indicator and a "Generate
   Agent Team Report" action (already gated to snapshots carrying saved scope).
3. **Generate (Reports, explicit click).** Backend runs the Agent Team from the
   saved evidence package only. While running, the UI shows the **transient
   `generating` state** (section 3.1) layered over the last persisted status —
   nothing new is persisted until the run resolves to one of:
   - `full_agent_report` (`run_completeness` full or partial),
   - `deterministic_draft` (blocked/unknown actionability gated all roles),
   - `agent_unavailable` (provider unavailable for all roles),
   - `validation_failed` (generated output rejected by the validator).
4. **Revisit (any time).** The report renders from the saved artifact only,
   reproducibly. `report_built_at` reflects the current render;
   source/generation timestamps reflect history (section 5). A snapshot that was
   never generated still shows the Generate action.

### 3.1 Transient `generating` state (UI-only, not persisted)

While a generation request is in flight, the UI shows a transient "Generating
Agent Team report…" affordance **over the last persisted status** (normally
`source_snapshot`). It is deliberately **not** a persisted status:

- if the request times out, fails, or the app reloads, the snapshot remains its
  last clean persisted status — never a stuck "pending"/"draft" row;
- it never implies that analysis already exists;
- it is single-flight per snapshot (the Generate action disables while in
  flight) to avoid concurrent duplicate runs.

This resolves the naming ambiguity inherited from the architecture doc's
original `draft` ("pending or in progress"): **pending is transient/UI-only**,
while the persisted `deterministic_draft` means "deterministic evidence shown as
the body because no Agent Team narrative was generated (gated)". They are
different things and must read differently to the user.

### 3.2 Per-state UX intent

| status | what it means | primary UX | actions |
| --- | --- | --- | --- |
| `source_snapshot` | snapshot saved; no report generated | complete deterministic snapshot, framed as a kept analysis; "Agent Team analysis not generated yet" | Generate (if saved scope present) |
| `generating` (transient) | a generation request is in flight | "Generating…" over the prior status; inputs disabled | Cancel/await; single-flight |
| `full_agent_report` | Agent Team narrative generated and validated | synthesis + role sections lead; deterministic evidence supporting; coverage disclosure if `partial` | Regenerate (explicit); View provenance |
| `deterministic_draft` | narrative intentionally not generated (actionability gated all roles) | deterministic evidence body + honest "narrative not generated because the review was gated"; no defect framing | none required; (Regenerate optional, will re-gate) |
| `agent_unavailable` | generation attempted; provider unavailable for all roles | deterministic evidence remains; honest "narrative unavailable" + retry | Try again (re-run generation) |
| `validation_failed` | output produced but withheld by safety validation | deterministic evidence remains; honest "narrative withheld by safety validation"; offending text never shown | Try again (re-run) |

Across all states: deterministic evidence is always present as the trustworthy
foundation; no state implies advice, a recommendation, trading readiness, or a
product defect. Existing headline strings in
`_agent_team_report_headline` already match this intent.

## 4. Behavior Under Stress (Question 3)

- **Slow generation.** Use the transient `generating` state; keep it
  single-flight. Generation should be implemented behind an async-capable seam
  so a future queue/timeout policy does not change the contract; today's
  synchronous endpoint is acceptable. A timeout resolves to `agent_unavailable`
  (provider) and leaves the snapshot clean — never a stuck status.
- **Generation unavailable (provider down / not configured).** Result
  `agent_unavailable`; deterministic evidence is the fallback body; offer "Try
  again". Retry re-runs the Agent Team from the **same saved evidence**; it never
  recomputes the source.
- **Public-evidence roles still skipped.** Expected and honest, not an error.
  Reports must disclose coverage: which roles ran vs. were skipped, with neutral
  copy (e.g. "Public market analysts are not yet enabled"). A `full_agent_report`
  built from portfolio-aware roles only is still the primary narrative but must
  carry `run_completeness = partial` plus a coverage note (section 5 adds a
  small coverage descriptor so the UI need not infer this).
- **Valid but incomplete snapshot.** If sections are `not_reviewed` /
  `not_available` (e.g. economic/market-mood/public evidence today), generation
  proceeds with available evidence and the synthesis states the limited inputs;
  it never fabricates. If the snapshot lacks saved scope entirely, the Generate
  action stays hidden/disabled (already shipped) — generation is gated, not
  attempted-and-failed.
- **Revisiting an older saved report.** Renders from the saved artifact at its
  persisted `evidence_schema_version`; we never silently re-project an old report
  onto a newer evidence schema or re-run it. If schemas advance, any refresh is
  an **explicit** user-initiated regeneration, surfaced as such — never silent.
  This keeps old reports honest, reproducible, and stable.

## 5. Persisted vs Recomputed, And Honest Timestamps (Question 5)

**Persisted (immutable source + generated narrative):** source snapshot
evidence/scope/deterministic summary; `agent_summary` (role summaries,
synthesis, `report_status`, `evidence_schema_version`, `evidence_references`,
`warning_codes`, `provider_mode`); timestamps.

**Derived at read (pure functions of persisted data + render clock; never
account state):** the `AgentTeamReportRead` projection, `report_built_at = now`,
`report_headline`, `run_completeness`.

**Never recomputed:** deterministic metrics, scope, evidence — always read from
the saved artifact.

### 5.1 Required timestamp change (contract gap found)

Today the report read conflates two different moments:
`AgentTeamReportRead.generated_at` is set to `artifact.generated_at` (the
**saved-source** generation time), and there is **no** field capturing when the
Agent Team **report run** actually executed. Only `report_built_at` (render
time) and the source times exist. A snapshot saved on day 1 and generated on
day 5 currently shows the report's "generated_at" as day 1, which is
misleading.

Recommendation — three honest, distinct timestamps:

1. **Source saved/generated** — `artifact.generated_at` + `artifact.saved_at`
   (when the review snapshot was produced/persisted). Unchanged.
2. **Report generated** — **NEW** `report_generated_at`: when the Agent Team run
   executed. Add to `SavedAgentTeamSummaryRead` (persisted) and surface on
   `AgentTeamReportRead`. Null for `source_snapshot` and legacy artifacts.
3. **Last viewed/built** — `report_built_at` (render time). Already exists;
   informational only; must never imply data freshness or re-analysis.

UI copy then reads honestly, e.g. "Snapshot saved {1} · Agent Team report
generated {2} · Viewed {3}", and `deterministic_draft` / `source_snapshot` omit
{2}.

P29A-T7 implementation note: the frontend intentionally surfaces the historical
timestamps only ("Snapshot saved" and, when present, "Report generated"). It does
not show a "Viewed" timestamp because the consumed report list/detail payloads do
not expose `report_built_at`; fabricating a render time in the UI would be less
honest than omitting it. If a future read contract exposes `report_built_at`,
the UI may add a clearly secondary viewed/rendered label.

## 6. Reports vs Trade Review Responsibilities (Question 4)

- **Trade Review = capture.** Owns the save action that creates the source
  snapshot. It must **not** generate the report inline (keeps save fast, atomic,
  always-succeeds). After save it shows a non-blocking confirmation plus an
  optional suggestion/link: "Saved. You can generate an Agent Team report from
  this snapshot in Reports." No advice framing, no auto-navigation, no
  auto-generation.
- **Reports = synthesize + revisit.** Owns the Generate action (shipped),
  regeneration, the per-state UX, coverage disclosure, and provenance.
- **One clean handoff.** Trade Review *suggests* the next step; Reports *performs*
  it. Generation is **optional and suggested**, never silent and never blocking.

A combined "Save and generate" convenience button is possible but deferred: it
would still route through the same two backend calls and still show generation
as a distinct, failable step. Defer until generation value is higher (public
roles) — see open questions.

### 6.1 Regeneration policy

Re-running generation on a snapshot is allowed only as an **explicit**
"Regenerate" action. It replaces the `agent_summary` narrative and updates
`report_generated_at`; the immutable source snapshot is never touched, so
reproducibility of the *source* is preserved. Versioned report history /
side-by-side comparison stays **deferred** (per P28A/P29A deferred list). The
backend must make replace-vs-append explicit and ownership-checked; silent
overwrite without an explicit user action is not allowed.

## 7. Required Contract / Wording Changes (no code here)

1. **Add `report_generated_at`** (section 5.1) to `SavedAgentTeamSummaryRead`
   (persisted, nullable) and to `AgentTeamReportRead` (surfaced, nullable);
   backfill null for legacy/source-snapshot. Keep `generated_at` = source time
   and `report_built_at` = render time. Validator unchanged (timestamps carry no
   private data).
2. **Optional small coverage descriptor** on the agent summary / report read so
   the UI can state which roles ran vs. were skipped without inferring it (e.g.
   reuse role `role_status` + a derived `skipped_role_count`, or a
   `coverage_note` warning code). Prefer deriving from existing `role_summaries`
   to avoid new persisted fields; add a field only if derivation is insufficient.
3. **`generating` is a transient UI state, not a persisted status.** Do not add a
   "pending/generating" value to `AgentTeamReportStatus`. Document the transient
   layer so frontend and backend agree.
4. **Regeneration semantics** (section 6.1): explicit replace, update
   `report_generated_at`, immutable source, history deferred.
5. **Wording additions** (advice-free, honest): Trade Review post-save
   suggestion; "Generating…" transient label; retry copy for
   `agent_unavailable` / `validation_failed`; coverage disclosure ("Public market
   analysts are not yet enabled"); three-timestamp display copy. All must pass
   the existing generated-output / saved-review validators and avoid
   advice/recommendation/order/execution/safe-to-trade/ready-to-trade/guaranteed
   wording. Note for T7: the literal token `prompt` is a forbidden value token in
   the saved-review validator, so microcopy must avoid words like "prompt the
   agent."

These are additive and backward-compatible; legacy artifacts and
deterministic-only snapshots remain readable.

## 8. Follow-On Task Split

- **P29A-T6 (Codex C, backend; reviewers Codex B + Claude E).** Add
  `report_generated_at` to schema + persistence + projection; backfill null;
  define explicit regeneration replace semantics with ownership checks; keep
  generation behind an async-capable seam (do not enable async/queue yet);
  optional coverage descriptor; tests for timestamp distinctness,
  reproducibility, and legacy nulls. Fold the `report_generated_at` field into
  the single `SavedAgentTeamSummaryRead` extension already flagged in the T2
  review closeout (report_status/final_synthesis) so the model is extended /
  migrated once, not twice.
- **P29A-T7 (Claude A or Codex F, frontend; reviewers Claude B + Codex B).**
  Three-timestamp honest display; transient `generating` state over the prior
  status (single-flight); retry affordance for `agent_unavailable` /
  `validation_failed`; coverage disclosure on partial reports; Trade Review
  non-blocking post-save suggestion linking to Reports. Follow
  `.claude/skills/frontend-design/SKILL.md` and
  `.claude/skills/finance-dashboard-ux-review/SKILL.md`.
- **Precondition for richer reports (separate phase):** the reviewed
  public-evidence contract for currently skipped public analyst roles
  (`current_roadmap.md`). This is also the precondition before any future
  auto-generation reconsideration.
- **Reviews:** Codex B for the schema/wording change; Claude B visual review of
  the UX; Codex A / founder product sign-off on the manual-vs-auto decision.

## 9. Open Founder / Product Questions

- After public analyst roles land and synthesis is richer, do we want an
  **opt-in** "auto-generate on save" preference? (Touches deferred
  scope/preference management — would need its own contract.)
- Should Trade Review offer a combined "Save and generate" convenience, or keep
  strict save/generate separation (current recommendation)?
- Regeneration: always replace (recommended now), or eventually keep versioned
  history / comparison (currently deferred)?
- Should the UI disclose generation cost/latency expectations given mock-default
  today and real providers behind explicit backend opt-in?
- For partial reports, is a coverage note enough, or should the founder want a
  minimum-role threshold below which we show `deterministic_draft` instead of a
  thin `full_agent_report`?

## 10. Codex B Review Result

Codex B review (review-only sub-agent, architecture/privacy/safety): **PASS**,
2026-06-15. No blockers; no important issues. Every contract claim was verified
directly against the shipped code:

- save vs. on-demand generate endpoints match the recommended guided-manual
  model (`routes/reports.py`);
- no silent recomputation — the report projection reads only the saved artifact
  and sets `report_built_at = now` (`AgentTeamReportRead.from_saved_review_artifact`);
- the timestamp gap is real — `generated_at` echoes the saved-source time and
  no agent-run timestamp exists, so the additive nullable `report_generated_at`
  is justified;
- the five persisted statuses match `AgentTeamReportStatus`, and `generating`
  stays UI-only;
- every proposed copy string was run against `_SAVED_REVIEW_PROHIBITED_PHRASES`
  and `_SAVED_REVIEW_FORBIDDEN_VALUE_TOKENS` with zero hits;
- no private data is introduced; regeneration/responsibility split align with
  the P28A/P29A deferred lists and enable no order placement/auto-spend.

Deferred-polish notes carried into follow-on tasks:

- T7 microcopy must avoid the forbidden `prompt` token (folded into section 7.5);
- T6 should fold `report_generated_at` into the single
  `SavedAgentTeamSummaryRead` extension already flagged in the T2 closeout, to
  migrate once not twice (folded into section 8);
- T7 should confirm the three-timestamp separator/format passes the frontend
  copy lint (no validator concern).

Product sign-off on the manual-vs-auto decision remains with Codex A / founder.
Plan status line applied to `docs/shared/implementation_plan.md` P29A-T5.
