# Phase 35-T7c — Per-Agent Prompt Contract: Role Prompts + Shared System Prompt (p35-role-note-v2)

- Author: Claude E (agentic systems design lead)
- Date: 2026-07-09
- Status: DESIGN — awaiting Claude G review (PASS/BLOCKED)
- Mode: design only; no code changes in this task
- Inputs: founder feedback ("the live-prompt layer is too thin; each report
  section should have an owning agent; give specific prompt suggestions per
  role and a shared system prompt suggestion"), the v4 report contract
  (`PHASE_35_T4_REPORT_CONTRACT_V4_DESIGN.md`, PASS as amended), the T1
  methodology (`docs/claude-h-knowledge/P35_T1_TRADE_IMPACT_METHODOLOGY.md`),
  and the shipped P35-T5 composer + gates.

Fixed constraints (not open questions in this doc): all existing gates, the
deterministic floor, the envelopes-only input contract, and "LLMs never
compute financial values" are binding. This doc designs prompts *inside*
those walls.

---

## 1. Current state (what "too thin" is, precisely, with code citations)

The entire live-prompt layer today is:

1. **One shared system prompt template** built inline in
   `backend/app/services/agent_team/orchestration/tool_mediated_runner.py`,
   `_live_role_request` (lines 336–386). It is a single unbroken block of
   ~12 stacked prohibitions with the role identity reduced to
   `f"You are {role.display_name}."` (line 349).
2. **One playbook sentence per role, for two roles only**:
   `_live_role_playbook` (lines 389–392) returns a technical sentence for
   `technical_analyst` and — defect — the *risk* sentence for **every other
   role name** (it is the bare `return` fallback). If fundamentals/news were
   ever allowlisted without prompt work they would silently run under the
   Risk Manager's framing.
3. **A hard two-role allowlist** in `run_tool_mediated_agent_team`
   (line 216): only `technical_analyst` and `risk_management_agent` reach the
   live provider; fundamentals/news pass through deterministic-only. SEC/FRED
   findings are additionally pinned deterministic by
   `_sec_event_finding_stays_deterministic` /
   `_fred_economic_finding_stays_deterministic` (line 213).
4. **Prompt version** `LIVE_PROMPT_VERSION = "p35-role-note-v1"`
   (`orchestration/models.py:74`); `LIVE_ROLE_MAX_TOKENS` = 600 for all four
   roles (`models.py:75–80`); temperature 0.0, timeout 30s
   (`tool_mediated_runner.py:382–384`).
5. **The composer** `_synthesis_markdown` (runner lines 1147–1222) slots the
   technical note under `## Market context` (1189–1191) and the risk note
   under `## Risk and scope notes` (1193–1195) via `_live_note_for_role`
   (1388–1393). Synthesis is authored deterministically
   (`final_synthesis_authored_by: "deterministic_template"`, lines 1010–1011).

So the founder's reading is correct: there is no per-agent prompt contract —
only a shared ban list with a one-sentence role hint for half the team.

---

## 2. Section-ownership map for the v4 document (deliverable 1)

"Owns" means: the agent whose evidence domain the section renders, and — where
a live note exists — the agent that contributes the gated connective prose on
top of the deterministic floor. **Every number, table, threshold, and
citation in every section is deterministic backend output; no owner ever
computes.** The composer itself stays deterministic (§3e).

| # | v4 section (§1.1 heading) | Owning agent | Deterministic floor (code) | What the live note may add |
|---|---------------------------|--------------|----------------------------|-----------------------------|
| — | Title + read-only banner | Composer (deterministic) | `_trade_review_title` runner:1225–1228 | Nothing. Never live. |
| 1 | `## Summary` | Portfolio Manager | `_summary_paragraph` / `_summary_headline` runner:1247–1265 | Nothing in v4/v2. PM is the composer persona; no PM live prose (§3e). |
| 2 | `## If you proceed` | Portfolio Manager (steward of the frozen T3 narrative) | frozen `proceed_statements` via `trade_impact_narrative_groups`, runner:1156–1181 | Nothing, ever. Highest-stakes numbers; deterministic-owned by rule. |
| 3 | `## Exposure before and after` | Risk Manager (steward) | `_exposure_table_blocks` runner:1276 | Nothing. Tables are deterministic-owned. |
| 4 | `## Reference points` | Risk Manager (steward) | `_reference_point_lines` runner:1326 | Nothing. Threshold math is deterministic-owned. |
| 5 | `## Market context` | **Technical Analyst (live note)** | `_market_context_lines` runner:1336 (saved EOD values/labels table) | One 2–4 sentence connective note: how the close sits in its own saved range/average context, envelope labels only. |
| 6 | `## Risk and scope notes` | **Risk Manager (live note)** | `_risk_scope_lines` runner:1361 (caveats, scope limits, cited refs) | One 2–4 sentence connective note: which saved caveats most affect trust in this review's inputs + one imperative verification step. |
| 7 | `## Open questions` (conditional) | Evidence Auditor (deterministic) | contradiction-derived, runner:1197 | Nothing. Auditor output is not LLM-authored. |
| 8 | `## What was not reviewed` | Fundamentals + News Analysts (stewards) | frozen `not_reviewed_statement` + `_unavailable_inventory` runner:1198–1205, 1444 | Nothing in v2 while their sources are dormant. Their gap domains feed the deterministic inventory. |
| 9 | `## Verify before acting` | Risk Manager (steward) | frozen `verify_statement` runner:1207–1213 | Nothing. Frozen checklist is deterministic-owned. |
| — | Footer | Composer (deterministic) | `_document_footer` runner:1396–1403 | Nothing. |
| F1 | `## Company context` (future, design-forward) | **Fundamentals Analyst (dormant live note)** | new deterministic block from `public_company_profile` / `public_fundamentals_snapshot` envelopes (floor must land before the note) | One 2–4 sentence presence/absence note (§3d). Rendered only when the enable condition in §3d holds. |
| F2 | `## Events and filings context` (future, design-forward) | **News Analyst (dormant live note)** | new deterministic block from `sec_recent_filings_metadata` / `economic_awareness_context` metadata rows | One 2–4 sentence metadata presence/absence note (§3d). Same enable condition pattern. |

Placement of F1/F2 when enabled: between `## Market context` and
`## Risk and scope notes` (public context before private-scope caveats,
matching the v4 reading order). Until enabled, the composer renders neither
heading — no empty sections (v4 §5 formatting rule).

---

## 3. Verbatim prompts — `p35-role-note-v2` (deliverable 2)

### Design shape: shared core + role block

v2 keeps ONE shared system prompt template but replaces the playbook
sentence with a structured **role block** interpolated near the top. Two
rules govern the split, chosen for small-model robustness (§5):

- The **shared core** owns every hard ban, exactly once. Role blocks never
  restate ban lists.
- **Role blocks are positive instructions** (what the note is, where it
  sits, what expertise it applies, what good looks like), plus at most ONE
  role-characteristic negative — the single failure mode most typical of
  that role that the gates cover only after the fact.

Mechanically for Codex C: `_live_role_playbook(role_name)` (runner:389–392)
becomes `_live_role_prompt_block(role_name)` returning the blocks below, and
it must **fail closed**: an unmapped role raises (no live request is built)
instead of inheriting another role's framing — this removes the silent
risk-sentence fallback defect (§1 item 2).

Every hard constraint of v1 is retained in the shared core below; the
mapping is audited line-by-line in §4.1.

### (a) Shared system prompt (verbatim; `{role_display_name}` and `{role_block}` are the only slots)

```text
You are {role_display_name} on a read-only portfolio review team. A
deterministic system has already written every number, table, and threshold
in this report. You add exactly one short note of sentence-level context on
top of it. Your note answers one question only: what would a manual reviewer
acting right now overlook in the saved evidence?

{role_block}

Output shape: exactly one note of two to four plain-language sentences.
Plain prose only — no headings, no tables, no lists, no bullets, no field
names, no code words, no words joined with underscores. When something is
absent, say "not reviewed" or "not available" in plain words; caveat codes
are not categories.

Numbers: either copy a number character-for-character from a supplied
envelope value, or write no number at all. Never compute, convert,
aggregate, estimate, round, or combine values into a new number. Do not
write dollar signs or percent signs. Use freshness and availability words
only exactly as the envelopes categorize each item.

Never name the reviewed instrument, the account, or any user-specific
label. Never describe the size of the portfolio, a position, exposure,
allocation, or cash — not in digits, not in words, not by comparison.
Describe saved evidence only: no advice, no action instructions other than
plain verification steps, no urgency, no ranking, no predictions, no target
prices, no support or resistance levels, no filing interpretation, no macro
interpretation, no likelihood or probability claims, no return, payout, or
break-even figures, no verdicts, no links.
```

### (b) Role block — `technical_analyst` (Market context note)

```text
Your note appears under the report's "Market context" heading, directly
below a deterministic table of saved end-of-day values for the reviewed
symbol. Your expertise is reading saved price context: where the latest
close sits in the saved 52-week range and relative to its saved moving
averages, using only the relationship labels and values already in your
envelopes, such as "above the 200-day average". Connect two or three of
those saved relationships into one plain observation that a reviewer
glancing only at today's price would miss, and state the freshness category
of the saved values exactly as your envelopes give it. Do not describe
trends continuing, momentum building, or what prices may do next.
```

### (c) Role block — `risk_management_agent` (Risk and scope note)

```text
Your note appears under the report's "Risk and scope notes" heading, below
a deterministic list of saved caveats and scope limits. Your expertise is
judging which saved caveats most affect trust in this review's inputs. Pick
the one or two caveats from your envelopes that a reviewer would most
regret overlooking — for example that holdings figures come from a saved
sync rather than a live connection, or that quote freshness is manual — and
say in plain words what each one means for reading this report. Your
envelopes carry no numeric values, so your note contains no numbers. End
with one plain verification step in the imperative, such as "re-verify the
exposure math at your broker before relying on it".
```

### (d) Role blocks — `fundamentals_analyst` and `news_analyst` (DESIGN-FORWARD; ship dormant)

These two prompts are specified now so the per-agent contract is complete,
but they must **not** be wired live in this phase. They ship as inert
entries in `_live_role_prompt_block`, and the enable condition is explicit:

**Enable condition (all four required, per role):**
1. The role's public evidence sources are enabled and its envelopes are
   value-carrying in the saved package — for fundamentals:
   `public_company_profile` / `public_fundamentals_snapshot` with
   availability "available"; for news: `sec_recent_filings_metadata` /
   `economic_awareness_context` with reviewed metadata rows present.
   (In the rejected T18 run, fundamentals was `skipped` with
   `no_reviewed_public_evidence` and news carried only
   not-available findings — under this condition neither would enable.)
2. The composer has gained the role's deterministic floor section
   (§2 rows F1/F2) — the note is connective prose on a floor, never a
   floor substitute.
3. The founder flips the live-role allowlist (runner:216) to include the
   role, and for news the SEC/FRED deterministic pins (runner:213,
   `_sec_event_finding_stays_deterministic` /
   `_fred_economic_finding_stays_deterministic`) are re-reviewed in their
   own task — this doc does not change them.
4. The structure gate's role set (`_structure_contract_flag`,
   `auditing/live_report_gates.py:250`, which today hard-blocks any role
   outside {technical, risk}) is extended to the enabled role in the same
   change.

**Fundamentals Analyst → "Company context" note:**

```text
Your note appears under the report's "Company context" heading, below a
deterministic summary of which public company facts were reviewed. Your
expertise is naming what reviewed public company context is present and
what is absent, using only the profile facts, snapshot categories, and
freshness categories in your envelopes. Connect that presence or absence
into one plain observation about what a reviewer relying on price alone
would miss. Describe what was reviewed or not reviewed only; do not
evaluate the company or interpret what any fact means for it.
```

**News Analyst → "Events and filings context" note:**

```text
Your note appears under the report's "Events and filings context" heading,
below a deterministic list of reviewed filing and release metadata. Your
expertise is reading that metadata trail: which filing form types, filing
dates, release names, and release dates exist in the saved evidence, and
which context is absent, using only the metadata in your envelopes. Connect
that presence or absence into one plain observation about what a reviewer
would miss by not checking the public record. Metadata only: do not
describe, guess at, or interpret the contents of any filing or release.
```

### (e) Portfolio Manager: stays deterministic — no PM live prose

Restated as a binding line of this contract: the PM/synthesis layer is the
**deterministic document composer** (`_synthesis_markdown`, runner:1147;
`final_synthesis_authored_by: "deterministic_template"`, runner:1010–1011)
and gets **no prompt in v2**. There is no PM entry in
`_live_role_prompt_block`, and the fail-closed unmapped-role behavior (§3
design shape) makes an accidental PM live call impossible. This preserves
v4 §4 and Claude G decision D-PM from the T4 review.

---

## 4. Gate-compatibility analysis per prompt (deliverable 3)

Gates in force on every live note (`auditing/live_report_gates.py`):
structure (`_structure_contract_flag`:249 — role allowlist, non-empty, no
heading/table/list lines, 1–4 sentences), numeric consistency
(`_numeric_consistency_flag`:270 — every numeral must be an envelope value
or a structural numeral from an indicator name), category consistency
(`_category_consistency_flag`:286 — freshness/availability assertions must
match envelope categories), portfolio-claim (`_portfolio_claim_flag`:266 —
digit + spelled-cardinal + comparative-magnitude forms inside an 8-word
portfolio-context window, `PORTFOLIO_WINDOW_RE`:98), display-token
(`find_internal_display_tokens`), and the report-level §7 ban and P35
pattern set (`safety/report_output_safety.py:104–211`) with the
instruction-vs-description matcher (imperative-only bans; verification
imperatives whitelisted).

### 4.1 Shared core (a) — constraint mapping and gate alignment

Every v1 constraint survives into v2 (v1 text at runner:349–361):

| v1 constraint | v2 shared-core sentence |
|---|---|
| "Answer only: what would be ignored…" | "Your note answers one question only: what would a manual reviewer acting right now overlook…" |
| one note, 2–4 sentences | "exactly one note of two to four plain-language sentences" |
| no headings/tables/lists/bullets/field names | "Plain prose only — no headings, no tables, no lists, no bullets, no field names…" |
| numbers copied character-for-character; never compute/convert/aggregate/estimate | Numbers paragraph, verbatim intent, plus "or write no number at all" (new positive exit) |
| freshness/availability words only as categorized | retained verbatim intent |
| caveat codes are not categories; name absence plainly | "say 'not reviewed' or 'not available' in plain words; caveat codes are not categories" |
| no portfolio magnitude / personal allocation size | strengthened: "not in digits, not in words, not by comparison" — now matches the R1-amended gate vocabulary (digit + cardinal + comparative-magnitude) instead of lagging it |
| no instrument name / user-specific label | retained |
| no advice/instructions/urgency/ranking/prediction/targets/support-resistance/filing interpretation/macro interpretation/likelihood/return-payout-breakeven/verdicts/URLs/$%/invented sections | retained, with one deliberate refinement: "no action instructions **other than plain verification steps**" — this aligns the prompt with the §7 instruction-vs-description matcher (verify/check/confirm/review/re-sync/compare are whitelisted imperatives) instead of contradicting the risk exemplar the T4 review confirmed (rider R3a) |

New in v2, each lowering drop risk: the "deterministic system already wrote
every number" frame (tells a small model *why* it must not compute — the
strongest known steer away from numeric-gate violations), "no words joined
with underscores" (plain-language phrasing of the display-token gate; v1
never mentioned it), and the positive absence vocabulary "not reviewed /
not available" (matches `ALWAYS_ALLOWED_BARE_GAP_TOKENS`, gates:111).

**Flagged residual risk (shared core):** "say 'not reviewed' or 'not
available' in plain words" invites those exact phrases; both are the
always-allowed gap tokens, so this is aligned by construction. No shared-core
line invites gated content.

### 4.2 Technical block (b)

- **Numeric gate:** "above the 200-day average" and "52-week range" rely on
  structural numerals from indicator fact keys (sma200, high_52_week), which
  `_allowed_numbers` admits (T17A design; gates:351). Instructing "labels
  and values already in your envelopes" plus the shared numbers paragraph
  keeps any copied value inside the allowed set. Aligned.
- **Category gate:** "state the freshness category of the saved values
  exactly as your envelopes give it" is phrased to make the model echo the
  envelope's category token, which is precisely what
  `ASSERTION_CATEGORY_RE` (gates:70) verifies. Aligned. (A v1-style
  paraphrase like "the data is end-of-day" was deliberately NOT used as an
  example, because a paraphrased category in assertion position is exactly
  what the gate drops.)
- **Portfolio-claim gate:** the block never mentions portfolio/account
  terms, and the shared core bans them; the note's subject (price context)
  keeps it outside the context window by topic. Aligned.
- **§7 bans:** the one role-negative ("trends continuing, momentum
  building, what prices may do next") targets the technical role's
  characteristic failure (prediction), which the shared core and
  `P35_PROHIBITED_REPORT_PATTERNS` (likely/probability/target) also cover —
  belt and suspenders on the highest-frequency failure. Aligned.
- **Flagged drop-risk line:** "such as 'above the 200-day average'" — a
  model whose envelopes lack the sma200 relationship could echo the example
  verbatim, and a relationship label absent from the envelopes is not
  numeric-gate-protected (it is a label, not a numeral; 200 is structural).
  Mitigation kept in-prompt: "already in your envelopes" immediately before
  the example. Residual risk accepted and eval-covered (§6 of the T4 matrix
  covers wrong-relationship drops via category/numeric gates only
  partially) — flagging per the task instruction. If Claude G prefers zero
  example risk, the example clause can be cut without weakening the block.

### 4.3 Risk block (c)

- **Portfolio-claim gate (R1 vocabulary):** the examples were chosen to
  survive the window regex: "holdings figures come from a saved sync"
  places no magnitude term (digit, cardinal, double/most/majority/bulk/
  dominant/concentrat\*) within 8 words of "holdings"; "re-verify the
  exposure math at your broker" likewise. The block's "no numbers" sentence
  plus the shared magnitude ban steer away from "most of the portfolio"
  phrasing. **Flagged residual risk:** the topic (caveats about the
  portfolio) lives permanently inside the gate's context vocabulary, so any
  slip into magnitude words drops the note — this is the intended
  fail-closed direction, but expect a higher baseline drop rate for this
  role than for technical; the deterministic floor is unaffected.
- **§7 instruction-vs-description matcher:** the imperative exemplar
  "re-verify the exposure math at your broker before relying on it" trips
  none of the imperative bans (add/trim/rebalance/buy/sell/hold/wait/spread
  and consider-forms; safety:206–210) and matches the whitelisted
  verification imperatives — it is the rider-R3a compliant exemplar,
  imported verbatim in spirit from the T4 §2 contract. "Should" appears
  nowhere in any v2 prompt. Aligned.
- **Numeric gate:** "your envelopes carry no numeric values, so your note
  contains no numbers" states the true envelope property (risk envelopes
  are label/caveat-only) as a positive rule — the strongest possible
  numeric-gate alignment.
- **Category gate:** "quote freshness is manual" as an in-prompt example is
  assertion-shaped; it is safe only because "manual" is a real
  `FRESHNESS_CATEGORY_VOCABULARY` member and the risk role's envelopes carry
  the quote-freshness category. **Flagged:** if a future package categorizes
  quote freshness differently, a model echoing the example verbatim gets
  dropped by the category gate — acceptable (fail-closed), and the "for
  example" framing plus "from your envelopes" bounds it.

### 4.4 Dormant blocks (d)

- Both are presence/absence notes: no numerals except copied dates/form
  metadata (news), which arrive as envelope value labels
  (`prompt_fact_labels_for_tool_result` passes form_type/filing_date/
  release_name/release_date, gates:226–235) and therefore sit in the
  numeric allowed set. Aligned.
- Neither block names portfolio-context terms; public-context topics keep
  them naturally outside the portfolio-claim window. Aligned.
- The news block's single negative ("do not describe, guess at, or
  interpret the contents") targets filing/macro interpretation — its
  §7-banned characteristic failure. The fundamentals block's single
  negative ("do not evaluate the company") deliberately does NOT enumerate
  evaluative vocabulary (cheap/expensive/strong/weak): listing ban words in
  a prompt plants them in a small model's context, and the P35 pattern set
  already hard-blocks them. This is the §5 negative-instruction principle
  applied.
- **Blocking dependency, restated:** these prompts must not go live before
  their §3d enable conditions — most importantly the structure gate's role
  set (gates:250) currently returns `STRUCTURE_FLAG` for any role outside
  {technical, risk}, so premature allowlisting produces 100% drops, and the
  required-headings table for these roles (gates:43–52) is v3-legacy that
  the enabling task must reconcile.

---

## 5. Live-model robustness (deliverable 4)

Notes will run on live Gemini flash-class models from now on (founder
directive). Candidate list per founder: gemini 3.5 flash (new), 3.1 flash
lite, 3 flash — configured via `POA_LLM_MODEL_CANDIDATES` through the
existing chain. One standing non-blocking note: at the 2026-07-06 check of
the official model docs, `gemini-3-flash` was a preview id
(`gemini-3-flash-preview`), not a stable bare id; the founder verifies real
ids at config time — prompts must therefore survive the **smallest**
candidate (flash-lite class), which is the design bar used here.

Applied principles (visible in §3):

1. **Structure before rules.** Identity → single question → role block →
   output shape → number rules → bans. A small model weights early tokens;
   v1 buried the task under the ban block. The role block sits second.
2. **One idea per paragraph, four short paragraphs.** v1's single ~140-word
   run-on is the format small models drop clauses from first.
3. **Positive instructions where gates enforce the negative.** "Write no
   number at all", "say 'not reviewed' in plain words", "your note contains
   no numbers" replace stacked don'ts; the full ban list appears exactly
   once (shared core), and role blocks carry at most one targeted negative.
   Gates remain the enforcement; prompts are the steering.
4. **No meta-reasoning demands.** No "think step by step", no
   self-verification loops, no long conditional trees — nothing a
   flash-lite model will half-execute into malformed prose.
5. **Concrete good examples over abstract rules** ("above the 200-day
   average"; the imperative verification exemplar), each vetted against the
   gates in §4 and each flagged where it carries residual echo risk.
6. **Unchanged user message.** The envelopes-only user message
   (runner:364–373: `allowed_evidence_refs`, `tool_result_envelopes`,
   `output_rule`) is part of the input contract and stays byte-identical in
   v2. Only the system prompt and the version string change. This keeps the
   v2 diff reviewable and the eval deltas attributable to prompt text alone.

---

## 6. Token budgets and temperature (deliverable 5)

Recommendation: **temperature stays 0.0; `LIVE_ROLE_MAX_TOKENS` stays 600
for all roles; no change.** Justification, since the founder asked:

- **Temperature 0.0.** Every gate assumes exact echoes (numbers
  character-for-character, category tokens verbatim). Sampling entropy only
  raises drop probability and adds nothing a 2–4 sentence connective note
  needs. Determinism also keeps live smokes comparable across the model
  chain.
- **max_tokens 600, not lowered to fit the 2–4 sentence target
  (~60–120 tokens).** The failure mode of a tight budget is worse than the
  failure mode of a loose one: a response cut off at max_tokens ends in a
  dangling sentence fragment with no terminal punctuation, which the
  structure gate's sentence counter (gates:260, counts `[.!?]`) does **not**
  count — a truncated note can therefore pass the 1–4 sentence check with a
  garbage tail and reach the report. An over-long but complete response is
  the safe direction: 5+ sentences → `STRUCTURE_FLAG` → clean drop to the
  deterministic floor. 600 tokens makes truncation practically unreachable
  for a note-shaped completion at negligible cost. The per-role dict
  (`models.py:75–80`) stays as the tuning seam.
- **Deferred hardening (not this task):** treat a length-truncated finish
  reason as `unavailable` in `_live_provider_role_findings` so a truncated
  note can never be evaluated as content. Listed under deferred polish, not
  scope.

---

## 7. Implementation seams for Codex C (when the founder green-lights T7c implementation)

1. `orchestration/models.py:74` — `LIVE_PROMPT_VERSION = "p35-role-note-v2"`.
2. `orchestration/tool_mediated_runner.py:349–361` — replace the inline
   system-prompt block with the §3a shared core (module-level template
   constant, `{role_display_name}` + `{role_block}` interpolation).
3. `tool_mediated_runner.py:389–392` — `_live_role_playbook` →
   `_live_role_prompt_block` with explicit entries for all four roles
   (§3b/c/d) and fail-closed raise for unmapped roles; the live allowlist
   (line 216) is unchanged, so fundamentals/news entries ship dormant.
4. No change to: the user message (runner:364–373), the allowlist
   (runner:216), the SEC/FRED pins (runner:213), any gate, the composer,
   temperature/max_tokens/timeout (runner:382–384).
5. Tests: prompt-content unit tests (each hard constraint phrase present in
   the built request; role block routed per role; unmapped role raises);
   version-string assertions on provider_runs; existing live-note eval
   matrix re-run under v2 with mock provider; drop-rate smoke on live
   Gemini stays a founder-run acceptance step.
6. Deferred polish (visible while citing seams, not in scope): stale
   `request_id=f"p34a_{role_name}_tool_mediated"` (runner:376) should become
   p35; length-truncation finish-reason guard (§6); v3-legacy
   `ROLE_REQUIRED_HEADINGS` for fundamentals/news (gates:43–52) reconciled
   in the enabling task.

---

## 8. Decisions requested from Claude G (PASS/BLOCKED ask)

- **D1 — Ownership map (§2):** confirm the steward assignments, PM-as-
  composer ownership of Summary / If you proceed, and the F1/F2 future
  placement between Market context and Risk and scope notes.
- **D2 — Shared core + role block split (§3a):** confirm the v1→v2
  constraint mapping in §4.1 is complete (no dropped hard constraint) and
  that "no action instructions other than plain verification steps" is the
  correct prompt-side statement of the §7 instruction-vs-description
  matcher.
- **D3 — In-prompt examples (§4.2/4.3 flagged lines):** accept the two
  flagged example risks ("above the 200-day average"; "quote freshness is
  manual") as eval-covered fail-closed residuals, or direct their removal.
- **D4 — Dormant prompts (§3d):** confirm the four-part enable condition
  (including the structure-gate role-set extension and SEC/FRED pin
  re-review) is sufficient to ship the fundamentals/news blocks as inert
  text now.
- **D5 — No-change recommendation (§6):** confirm temperature 0.0 and
  max_tokens 600 stand, with the truncation-guard as deferred polish.
