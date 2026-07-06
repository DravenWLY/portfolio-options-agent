# Phase 34A-T9B Readiness Review — Live Report Quality After T9A

Status: design/evaluation only (no implementation).
Owner: Claude E. Reviewer: Codex B.
Inputs reviewed: post-T9A `tool_mediated_report.py` (specificity claims at
`_freshness_specificity_claim` / `_scope_specificity_claim` /
`_gap_specificity_claim` / `_fred_economic_awareness_listing`, compositional
`_synthesis_markdown`, live seam `_live_provider_role_findings`), `tools.py`,
`test_tool_mediated_report.py` (incl.
`test_p34a_t9_deterministic_specificity_names_freshness_scope_gaps_and_inventory`),
`test_tool_mediated_eval.py`, and the T9 design memo.

Locked question (unchanged): **"What would I be ignoring if I acted manually
now?"**

---

## 1. Quality assessment of post-T9A reports

**Deterministic (mock) mode: materially better — the floor now answers the
question.** Freshness is named by category ("categorized as stale"), scope
caveats render readably, unavailable sections are listed by name, FRED/SEC
events appear as deterministic metadata listings with proper degradation
sentences and warning codes, and the PM synthesis is a real briefing: role
digests + not-reviewed inventory + open questions + checklist + read-only
clause. Test coverage backs each piece. A manual reviewer reading the
deterministic report now sees *specific* ignorable items, not category
labels.

**Live mode: currently subtracts value — this is the decisive finding.**
`_live_provider_role_findings` still implements T1-era *replacement*
semantics: on success it returns `findings=(proposed_finding,)` — one merged,
digit-free LLM sentence with unioned refs — discarding the role's entire
deterministic finding set. Post-T9A that discards exactly the specificity T9A
added: the Risk Manager's five findings (named freshness categories, readable
scope caveats, named gaps) collapse into one generic sentence, and the model
**cannot** restate the gap names because `evidence_gap_inspector` results
live in `summary_payload`, which the prompt envelope strips. The PM role
digests then digest the LLM sentence, propagating the loss into the
synthesis. Only the SEC and FRED news findings are protected (the
`*_stays_deterministic` guards).

Net: post-T9A, a live-enabled report is *less* specific than a deterministic
one whenever the provider succeeds. The deterministic floor now carries most
of the informational value; live prose in its current shape carries almost
none of it.

**Sections still generic (minor, non-blocking):**
- The risk role's first finding ("Saved deterministic risk flags, portfolio
  impact, and concentration drift are context that could be overlooked…")
  still doesn't name the actionability status label it sits on.
- Fundamentals analyst prose remains near-boilerplate ("Reviewed public
  company profile context is background that could be overlooked…").
- `_synthesis_markdown` joins sections into one long paragraph; content is
  coherent but rendering would benefit from markdown line breaks (formatting
  polish only, subject to validator/renderer check).

## 2. Answers to the review questions

1. **Does the report answer the locked question?** In deterministic mode,
   yes — clearly enough for the prototype bar. In live mode, no — the
   replacement collapse undoes it.
2. **Still generic:** fundamentals prose, the risk "flags" umbrella sentence,
   and PM paragraph formatting (§1 list).
3. **Is PM synthesis a coherent briefing?** Yes — digests + inventory + open
   questions + checklist is the right structure; only formatting polish
   remains.
4. **Is live prose still needed?** Not for facts — the deterministic floor
   owns those now, correctly. Live prose earns its place only as *connective
   tissue*: one qualitative, role-lens sentence that relates the named items
   ("taken together, the stale snapshot and unevaluated feasibility mean the
   saved picture may not reflect current conditions"). That is genuinely
   additive, cheap, and safe — but only if it can never replace the floor.
5. **T9B as proposed, or narrower?** **Narrower.** The original T9B
   (per-finding rewrite overlay) still rewrites deterministic text with LLM
   text and needs response-splitting/count-matching machinery; after T9A the
   rewrite direction is wrong — the LLM sentence is strictly less specific
   than what it replaces. Reshape T9B to an **additive-only overlay**:
   deterministic findings persist verbatim, live adds at most one appended
   connective finding per role, nothing is ever replaced. Simpler to
   implement, simpler to validate, immune to the subtraction problem.
6. **Eval gates:** §4 below — the central gate is the *no-subtraction
   superset property*.
7. **Live smoke before T9B?** Yes — one route-backed live Gemini smoke on
   synthetic evidence (existing T7D opt-in harness, Codex B owns) to capture
   the post-T9A live baseline and confirm the collapse in a real report;
   re-run after T9B to demonstrate the delta. Cheap, uses reviewed harness,
   no new surface.

## 3. Recommendation

**PASS — proceed to a narrowed P34A-T9B ("additive live overlay"), with the
no-subtraction eval gate as the acceptance bar.** Rationale: T9B is no longer
a quality enhancement; it is a correction of a live-mode regression risk that
T9A exposed. Deferring it would leave live mode strictly worse than mock
mode, which undermines the point of the live prototype.

Behavior spec for the narrowed T9B:

1. **Never replace.** Delete the replacement path in
   `_live_provider_role_findings`: deterministic findings always persist in
   the audited output, live or not. The SEC/FRED stays-deterministic guards
   become redundant but remain as belt-and-suspenders.
2. **Additive connective finding.** Per eligible role (public analysts +
   risk), live mode may append **at most one** new finding:
   `finding_type="missing_context"`, claim_text = the validated LLM sentence,
   `evidence_refs` = backend-assigned union of that role's deterministic
   refs, plus a distinguishing warning code (`live_provider_reasoning_used`
   retained; consider `live_connective_context` on the finding's caveats so
   readers/evals can identify it).
3. **All existing validation applies** to the added finding (hard blocks →
   drop the added finding only, keep the floor, record the eval flag; no
   re-pass for hard blocks, unchanged).
4. **Prompt v2** (`p34a-tool-mediated-role-v2`): per-role system prompt =
   role lens + locked question + "write exactly one qualitative sentence
   that connects the supplied envelope facts (availability, freshness
   categories, caveat codes); no numbers, no lists, no advice, no
   interpretation of filings or macro releases; do not restate boilerplate."
   Envelope fields unchanged (`summary_payload` stays stripped).
5. **PM digest ordering:** `_role_digest_lines` keeps digesting the *first*
   finding, which stays deterministic because the connective finding is
   appended last — assert this in evals rather than relying on it silently.
6. **Provider failure:** unchanged — floor persists, `live_provider_*`
   warning codes; the report is never worse than deterministic.

## 4. Eval gates for T9B (all offline, injected/fake provider)

| Gate | Assertion |
| --- | --- |
| G1 no-subtraction (central) | With live enabled and provider succeeding, every deterministic `claim_text` of every role appears verbatim in the audited findings; live report is a strict superset of the floor |
| G2 additive bound | Per role: audited findings count == floor count + at most 1; added finding carries the connective marker code |
| G3 digit policy | The added sentence is digit-free; deterministic listings (dates) never come from the LLM |
| G4 injection blocks | Injected advice / invented-metric / SEC- and FRED-interpretation / URL outputs → added finding dropped, floor intact, correct eval flag, no re-pass |
| G5 SEC/FRED untouched | News SEC/FRED findings byte-identical between live and mock runs |
| G6 PM digest source | Role digest lines equal the first *deterministic* sentence per role in live mode |
| G7 mock-mode stability | With live disabled, output byte-identical to pre-T9B behavior (existing T9A tests stay green unmodified) |
| G8 readback | Saved report readback re-runs neither tools nor provider (existing, keep) |

Plus the route-backed live smoke (§2 Q7) before and after implementation as a
manual quality check with the founder rubric from the T9 memo.

## 5. Exact Codex C implementation prompt

```text
Agent: Codex C
Task: P34A-T9B - Additive live connective overlay for tool-mediated Agent Team reports
Mode: backend implementation; one task; stop for Codex B review after.

Design references:
- docs/claude-e-agentic/PHASE_34A_T9B_READINESS_REVIEW.md (sections 3-4, binding)
- docs/claude-e-agentic/PHASE_34A_T9_LIVE_QUALITY_EVIDENCE_USE_DESIGN.md (background)

Scope (backend/app/services/agent_team/tool_mediated_report.py + tests only;
no schema/read-contract, frontend, new-source, or envelope-field changes):

1. Rework _live_provider_role_findings to additive-only semantics:
   - deterministic findings always persist verbatim (live never replaces);
   - on provider success, append at most ONE connective finding per role:
     finding_type="missing_context", claim_text = validated LLM sentence,
     evidence_refs = backend-assigned union of the role's deterministic refs,
     caveat marker "live_connective_context", role warning code
     "live_provider_reasoning_used" retained;
   - hard-blocked or invalid content -> drop only the added finding, keep the
     floor, record the existing eval flag, never re-pass hard blocks;
   - provider failure/timeout -> unchanged fallback (floor + live_provider_*
     warning code);
   - keep the SEC/FRED *_stays_deterministic guards as defense-in-depth.
2. Prompt v2: bump LIVE_PROMPT_VERSION to "p34a-tool-mediated-role-v2";
   per-role system prompts (fundamentals/news/technical/risk) = role lens +
   the locked question verbatim + output rule: exactly one qualitative
   connective sentence using only supplied envelope fields (availability,
   freshness, caveat_codes); no numbers, lists, advice, rankings, or
   filing/macro interpretation; no generic filler. The prompt envelope fields
   are unchanged - summary_payload, scope, as_of stay stripped.
3. PM digests: keep digesting the first (deterministic) finding per role;
   assert ordering in tests rather than relying on append order silently.
4. Evals: implement gates G1-G8 from the readiness review section 4 across
   tests/services/agent_team/test_tool_mediated_report.py and
   tests/services/agent_eval/test_tool_mediated_eval.py. Offline only,
   injected/fake providers, no live calls.

Boundaries: no LangGraph/LangChain/MCP/web/TradingAgents; no new sources; no
frontend; no raw private values, URLs, prompts, traces, secrets; no
advice/execution wording; deterministic backend owns all numbers and
citations; saved readback stays frozen; provider_runs freeze metadata
unchanged (additive status values only if needed).

Verification: cd backend && pytest (report counts for test_tools.py,
test_tool_mediated_report.py, test_tool_mediated_eval.py, report schema
tests); git diff --check.

Return per docs/shared/AGENT_REPORT_FORMAT.md with PASS/BLOCKED ask for Codex B.
```

## 6. Follow-ups (not in T9B)

- F1: name the actionability status label in the risk role's first finding
  (small deterministic change, needs a quick wording-safety check).
- F2: fundamentals analyst deterministic claim specificity (which profile
  sections were reviewed vs not).
- F3: PM synthesis markdown line breaks (rendering polish; verify validators
  and Reports UI handle newlines).
- Route-backed live smoke before and after T9B (Codex B, T7D harness,
  synthetic evidence, explicit credential authorization).

## 7. Blockers

None for starting T9B beyond the standing ones: Codex B review of this memo
(especially the additive-overlay reshape and the `live_connective_context`
caveat marker as an additive vocabulary value), and founder awareness that
the pre-T9B live smoke will show the collapse baseline.
