# Phase 30A-T2 Agent Team Briefing Shape For The Golden Path Review Desk

Status: design draft (design-only; no code in this task)
Owner: Claude E (agentic-system design)
Reviewer: Codex B (architecture/privacy/safety)
Related plan: `docs/shared/implementation_plan.md` Phase 30A, task `P30A-T2`
Builds on (accepted/shipped):
- `docs/codex-b-architecture/PHASE_30A_GOLDEN_PATH_REVIEW_DESK_CONTRACT.md` (P30A-T0)
- P30A-T1 backend gap audit PASS (no backend schema/endpoint/storage change required)
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- `docs/claude-e-agentic/PHASE_29B_T2_PUBLIC_ROLE_AGENTIC_DESIGN.md`
- `docs/claude-e-agentic/PHASE_29C_T3B_PUBLIC_ROLE_EDGAR_PROFILE_DESIGN.md`
- Shipped generation: `backend/app/services/reports/agent_team_report.py`;
  validator `backend/app/services/agent_team/report_output_safety.py`

## 1. Design Summary

P30A reframes the saved Agent Team report from a neutral "analysis is generated"
artifact into a **read-only specialist briefing that answers one question**:

> What would I be ignoring if I acted manually now?

This is a **wording and structure reshape of the existing deterministic-template
generation**, not a new architecture. Generation stays
`provider_mode="deterministic_template"`, runs only over the immutable
`SavedEvidencePackageRead`, preserves the package-aware validation seam, and uses
existing output fields. No LLM, no current account state, no new sources, no new
fields are required (section 7).

The shift is editorial: every role section and the final synthesis are framed as
**flags of ignored risk, ignored context, and data gaps** the user would not
have in mind if they acted from memory — never as a verdict, actionability
conclusion, or instruction. Portfolio-aware roles (Risk Manager, Portfolio
Manager) stay primary; public analyst roles (Fundamentals, News, Technical) stay
secondary context, and their **absence** (not_reviewed evidence) is itself
surfaced as an ignored-context gap.

## 2. Proposed Briefing Structure

The saved report renders, in this order (frontend ordering is P30A-T3/T4; this
fixes the content and its provenance role):

1. **Headline question + scope frame.** Restate "What you would be ignoring if
   you acted manually now" for `{symbol_or_underlying}` in the saved scope, with
   the saved scope/freshness/timestamps visible. Read-only, not a judgment.
2. **Final synthesis — "What you'd be ignoring" (primary).** Authored by the
   Portfolio Manager role (deterministic template). Groups the ignored items
   into four honest buckets (section 3.2): deterministic risk flags; data
   freshness/availability gaps; scope/feasibility caveats; context not reviewed.
3. **Role-separated flags.** Risk Manager and Portfolio Manager first (primary);
   Fundamentals, News, Technical beneath (secondary). Each is a short
   "what you might overlook" section or an honest skip.
4. **Manual verification checklist (section 5).** Carried inside the final
   synthesis prose (existing field) so it persists in the saved artifact.
5. **Deterministic facts and provenance beneath** — existing evidence sections,
   saved scope, caveat codes, freshness labels, source attribution. Audit layer.

This maps onto the existing `SavedAgentTeamSummaryRead`
(`final_synthesis_markdown`, `role_summaries[*].summary_markdown`,
`warning_codes`, `evidence_references`, `report_status`, `report_generated_at`)
with no shape change.

## 3. Role-By-Role Behavior

All role narrative is deterministic template text built from the saved evidence,
digit-free, category/label-only, and free of advice/verdict/order wording
(section 6). Citations stay at section-key granularity within each role's
existing allowlist and availability gate.

### 3.1 Primary: portfolio-aware roles

- **Risk Manager** (primary). Reframe from "Risk review uses the saved
  deterministic evidence" to "Risk review — what you would be overlooking."
  Surfaces, from saved deterministic evidence only: highest risk-rule severity
  label; concentration/allocation drift caveats; liquidity and collateral
  caveats; options exposure / assignment caveats; **broker snapshot freshness**
  and **market quote freshness** labels (both are already in its evidence
  references); and, when `scope_state.account_level_feasibility_evaluated` is
  false, an explicit "account-level feasibility was not evaluated, so
  collateral/buying-power capacity is unconfirmed" flag. It states these are
  items to verify, never that the trade is safe/blocked-from-trading.
  `warning_codes` continue to carry `caveat_codes`.
- **Portfolio Manager** (primary, synthesizer). Authors the final synthesis
  (section 3.2). Combines the validated role flags and saved evidence into the
  four-bucket "what you'd be ignoring" view plus open questions and the manual
  checklist. Treats any public analyst context as analysis-only background.
  Never a verdict, instruction, or decision about whether to act.

### 3.2 Final synthesis buckets (Portfolio Manager)

The synthesis is organized as "the things not in view if you act now":
1. **Deterministic risk flags** — severity label + which risk/concentration/
   collateral/options caveats fired (categories only).
2. **Data freshness / availability gaps** — stale broker snapshot, stale or
   unavailable market quotes, surfaced from the freshness labels.
3. **Scope / feasibility caveats** — review-account vs portfolio scope,
   account-level feasibility not evaluated, scope caveat codes.
4. **Context not reviewed** — public coverage state: no reviewed
   news / fundamentals / technical context attached (so the user would act
   without that check). Surfaced here even though the secondary roles are silent
   when skipped.
Then the manual verification checklist (section 5). Closes with the standing
"read-only context, not an instruction or judgment about whether to act;
deterministic backend services own all calculations" line.

### 3.3 Secondary: public analyst roles

Behavior and boundaries are unchanged from P29B-T2 / P29C-T3B; only the framing
becomes "context you might overlook."

- **Fundamentals analyst.** When EDGAR `public_company_profile` is
  `available`/`limited` (and in its allowlist), present it as company identity /
  listing context you might overlook (company name, ticker, listing exchange,
  CIK reference, SEC SIC regulatory metadata, fiscal year-end), with the SIC
  caveat, digit-free prose (literal CIK/fiscal-year stay in structured facts),
  short source label. Note that no reviewed fundamentals snapshot / events were
  attached (a gap). Background only. When the profile is not citable, the role
  skips honestly and the gap is surfaced by the synthesis bucket 4.
- **News analyst.** May cite only `public_news_snapshot`,
  `public_events_calendar`, `public_market_context` (per allowlist); must not
  cite `public_company_profile`. Default state is `not_reviewed` -> skip; the
  "no reviewed news/event context attached" gap is surfaced by synthesis
  bucket 4.
- **Technical analyst.** May cite only `public_technical_context`,
  `public_market_context` via its projection; must not cite
  `public_company_profile`. Note: stale/unavailable **market quotes** are not in
  the technical projection — they are deterministic evidence already surfaced by
  Risk Manager / synthesis bucket 2. Technical stays secondary, non-directional,
  no invented indicator values / support / resistance / levels / targets;
  default `not_reviewed` -> skip.

Public roles remain secondary: they never override or precede the portfolio-aware
flags, and their absence is an ignored-context gap rather than a failure.

## 4. Status / Degradation Matrix

`report_status` semantics are unchanged; only the briefing framing adapts. The
deterministic generator already branches on `blocked_*` and provider mode.

| evidence / status | report_status | briefing framing |
| --- | --- | --- |
| `normal_review` | `full_agent_report` | "Deterministic review found no blocking gaps in the saved scope, but here is what it does not cover and what to verify." Never "safe"/"proceed." |
| `manual_confirmation_required` | `full_agent_report` | Center the items needing manual confirmation (e.g. feasibility not evaluated, stale snapshot) as the main "what you'd be ignoring." |
| `analysis_only` | `full_agent_report` | "This review is analysis-only context; it is not an actionability judgment. Here is the context and the gaps." |
| `blocked_*` | `deterministic_draft` | Roles gated (no role narrative). Recommended (section 7): populate `final_synthesis_markdown` with a short deterministic "the review is incomplete because {reason category}; acting now means ignoring that the review itself did not complete" message + checklist. |
| missing / `not_reviewed` public evidence | unchanged | Public role(s) skip honestly; synthesis bucket 4 surfaces "no reviewed {news/fundamentals/technical} context attached." |
| stale broker snapshot | unchanged | Risk Manager + synthesis bucket 2 + checklist: "broker snapshot is {freshness label}; positions/feasibility may have changed." |
| stale / unavailable market quotes | unchanged | Risk Manager + synthesis bucket 2 + checklist: "market quotes are {freshness label}; acting now would use stale or unavailable prices." |
| account-level feasibility not evaluated | unchanged | Risk Manager + synthesis bucket 3 + checklist: "account-level feasibility was not evaluated; confirm collateral/buying-power capacity yourself." (no raw numbers) |
| CSP / covered-call caveats | unchanged | Risk Manager via options exposure section + checklist: "confirm collateral and assignment/exercise mechanics for the option leg." |
| provider unavailable (all roles) | `agent_unavailable` | Honest: "the specialist briefing could not be generated; the deterministic evidence below still applies." Deterministic facts remain. (section 7) |
| generated output fails validation | `validation_failed` | Withhold offending text; fall back to deterministic evidence + honest "the briefing was withheld by safety validation." |

In every state the deterministic evidence package is the always-present
foundation, and the report stays reproducible from the frozen package.

## 5. Manual Verification Checklist Wording (safe)

Carried in the final synthesis prose. Bare imperatives (no "you should", no
"safe/ready to trade", no buy/sell/order/execute, no guaranteed-return). Only the
items whose evidence applies are emitted; phrased as self-verification, never as
clearance to act. Suggested copy:

- "Before acting on your own, consider verifying the items below yourself."
- "Confirm the broker snapshot is current — it was {freshness label} in this
  saved review."
- "Re-check live market quotes — they were {freshness label} here and are not
  refreshed in this saved report."
- "Confirm account-level feasibility yourself (collateral / buying-power
  capacity); it was not evaluated in the saved scope."
- "Review the concentration / allocation impact for the reviewed scope."
- "For option legs, confirm collateral and assignment/exercise mechanics."
- "Note that no reviewed {news / fundamentals / technical} context was attached,
  so that check is not reflected here."
- "This checklist is read-only context for your own review, not an instruction
  or a judgment about whether to act."

## 6. Validator / Output-Safety Expectations

The reshape is wording only; all existing guards in
`validate_agent_team_report_output(payload, label=..., evidence_package=evidence)`
remain the enforcement seam and must keep passing:
- `REPORT_PROHIBITED_PHRASES` + `_SAVED_REVIEW_PROHIBITED_PHRASES`: no advice,
  recommendation, buy/sell/hold, order/execution, safe-/ready-to-trade,
  guaranteed-return, or "you should" wording. The "what would I be ignoring" and
  "verify yourself" framing avoids all of these; do not introduce the nouns
  "advice"/"recommendation" in templates (substring matching rejects the
  governed forms).
- `INVENTED_LEVEL_PATTERNS`: keep briefing prose digit-free; no support /
  resistance / pivot / target / level + number. Severities and freshness are
  labels, not numbers.
- `GENERATED_METRIC_PATTERNS`: no `$` / `%` / share-or-contract counts / Greeks /
  price targets — reference categories and labels, never values.
- `SOURCE_LEAK_PATTERNS`: no URLs; EDGAR CIK is identity metadata, not a link.
- Private-data guards: no holdings, quantities, balances, buying-power amounts,
  account/provider/broker IDs, raw payloads, prompts, or traces — categories
  only.
- Package-aware citation: each role's `evidence_references` stays within its
  existing allowlist and is availability-gated; news/technical cannot cite
  `public_company_profile`; EDGAR profile is identity/listing context only.
- The same `SavedEvidencePackageRead` instance is used for projection,
  validation, and persistence; failed-safe behavior (withhold + fall back to
  deterministic evidence) is unchanged.

## 7. Are Existing Fields Sufficient?

**Yes — no new field is required for P30A-T2.** The briefing is entirely
expressible in existing fields:
- `final_synthesis_markdown` carries the four-bucket "what you'd be ignoring"
  synthesis and the manual checklist;
- `role_summaries[*].summary_markdown` / `warning_codes` /
  `evidence_references` / `unavailable_reason` carry the role flags and honest
  skips;
- `report_status` / `report_generated_at` / saved evidence sections carry status,
  timing, and the deterministic/provenance layer.

Two behavior notes within existing fields (no schema change), for Codex B to
confirm during review:
1. **Populate the `blocked_*` / `deterministic_draft` synthesis.** Today
   `deterministic_draft` leaves `final_synthesis_markdown=None`. For P30A the
   blocked case is the most important "what you'd be ignoring" moment, so the
   generator should populate a short, safe deterministic synthesis + checklist
   explaining the incomplete review. This uses the existing field; it adds no
   schema.
2. The manual checklist lives in prose, not a structured field (below).

**Smallest additive field — future-only, requires Codex B review before any
implementation:** an optional `manual_verification_checklist: tuple[str, ...]`
on `SavedAgentTeamSummaryRead` would let the frontend (P30A-T4) render the
checklist as discrete, reproducible items instead of parsing prose. It is **not**
needed for P30A-T2 and is explicitly deferred; default to the prose checklist in
`final_synthesis_markdown` now. If pursued later it must be additive,
backward-compatible, default-empty, pass all validators, and be derived
deterministically from saved evidence.

## 8. Proposed Implementation Handoff (if this design PASSes)

Backend deterministic-template wording slice (smallest safe change), owner
Claude E or Codex C per Codex B/Codex A assignment; Codex B reviews:
- Reshape `_portfolio_role_summary`, `_public_role_markdown` /
  `_fundamentals_company_profile_markdown`, and the synthesis builder in
  `agent_team_report.py` into the "what you'd be ignoring" framing and
  four-bucket synthesis; add the manual checklist to the synthesis prose.
- Populate the `deterministic_draft` synthesis for `blocked_*` (item 7.1).
- Keep `provider_mode="deterministic_template"`, saved-evidence-only, package-
  aware validation, and failed-safe fallback unchanged.
- Tests (offline, deterministic, synthetic, private-safe): one stock/ETF flow and
  one `cash_secured_put`/`covered_call` flow across `normal_review`,
  `manual_confirmation_required`, `analysis_only`, `blocked_*`, stale broker
  snapshot, stale/unavailable market quotes, feasibility-not-evaluated, EDGAR
  profile available vs not_reviewed, provider unavailable, and validation
  failure; assert framing, checklist presence, role primacy/secondariness,
  citation boundaries, and that all guards pass.

Implementer safety reminders (from Codex B review):
- Never let the literal `safe to trade` / `ready to trade` strings land in
  generated prose even in a negated "never says safe to trade" form — the
  validators match the substring regardless of negation. Express the posture
  positively ("read-only context, not an instruction or judgment about whether
  to act").
- Keep freshness labels digit-free where they are interpolated into narrative
  (or route any digit-bearing value to structured facts) so they cannot trip
  `INVENTED_LEVEL_PATTERNS` / `GENERATED_METRIC_PATTERNS`.
- Note the attribute/section-key split: the liquidity/collateral section is the
  `cash_collateral_caveats` attribute on `SavedEvidencePackageRead` carrying
  `section_key="liquidity_collateral_caveats"`; cite by the section key.

Then the UX tasks already in the contract consume this content:
- **P30A-T3** (Trade Review golden-path UX, Claude A / Codex F): make
  deterministic review -> save snapshot -> generate/open briefing calm and
  explicit.
- **P30A-T4** (Saved Report briefing polish, Claude A): render synthesis-first,
  role-separated flags, deterministic facts/provenance beneath, scope/timestamps
  prominent; optionally consume the future checklist field if approved.

## 9. Blockers

- None. Design uses existing fields and the existing spine. The only items
  needing Codex B sign-off are the two within-existing-fields behavior notes
  (populate `deterministic_draft` synthesis; checklist in prose) and the
  explicitly-deferred future `manual_verification_checklist` field.

## 10. Codex B Review Result

Codex B review (review-only sub-agent, architecture/privacy/safety): **PASS**,
2026-06-22. No blockers, no important issues. The reviewer re-ran the actual
validator logic (`REPORT_PROHIBITED_PHRASES`, `_SAVED_REVIEW_PROHIBITED_PHRASES`,
`INVENTED_LEVEL_PATTERNS`, `SOURCE_LEAK_PATTERNS`) against every proposed copy
line and confirmed all pass, and verified the key shipped-code claims:
- the briefing maps onto existing `SavedAgentTeamSummaryRead` fields; no new
  field needed for P30A-T2; the future `manual_verification_checklist` field is
  correctly deferred;
- stale/unavailable market quotes and broker snapshot are surfaced by the
  Risk Manager / synthesis (both in `_PORTFOLIO_ROLE_EVIDENCE`), not Technical
  (whose projection narrows only `public_technical_context`/`public_market_context`);
- `report_status` semantics and public-role citation boundaries are preserved;
  saved-evidence-only, deterministic-template, package-aware validation, and
  failed-safe fallback are unchanged.

Three deferred-polish implementer reminders were folded into section 8 (avoid the
literal "safe/ready to trade" substring even negated; keep interpolated freshness
labels digit-free; name the `cash_collateral_caveats` attribute vs the
`liquidity_collateral_caveats` section key). The two within-existing-field
behavior notes (populate the `deterministic_draft` synthesis; checklist in prose)
must be re-reviewed by Codex B at implementation; the deferred checklist field
needs a separate Codex B contract review if pursued.

Plan status applied to `docs/shared/implementation_plan.md` P30A-T2. Stop for the
owner to schedule the implementation slice; no code lands until then.
