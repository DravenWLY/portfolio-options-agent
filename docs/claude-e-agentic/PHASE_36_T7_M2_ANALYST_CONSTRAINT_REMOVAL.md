# Phase 36 T7-M2 — Removing Invented Constraints from the K3 Analyst Note

Status: approved (M2-R3) — Codex B contract review PASS; Claude G
architecture/privacy review PASS with two required edits, applied in place
2026-07-21 (#14 kept for clauses, closing the third-party identity gap that
removing #7 and #14 together would have opened; 8b enforcement made precise now
that #17's removal lets verification lines carry trigger words). Cleared for
Codex C implementation of §2–§6.
Owner: Claude E
Mode: design revision, offline. No implementation, no live run, no gate change.

Supersedes, where they conflict: `PHASE_36_T7_K3A_..._DESIGN.md` §3 and §3.1
bounds, and `PHASE_36_T7_K3B_ANALYST_PROMPT_BLOCKS.md` §2.1 / §2.3. K3A's
architecture (typed note, no-facts principle, backend composition,
`analysis_status`) is unchanged and still governs.

## 0. What L2 established, and what I got wrong

L2 vindicated the K3 architecture. Every gate that killed L1 is absent from the
metadata: no `numeric_provenance_blocked`, no `attribution_required_blocked`,
no `structure_contract_blocked`, no `live_provider_safety_fallback`. The PM
authored a clean synthesis. Gemini returned well-formed typed notes that
parsed. **Every remaining failure is in a validator we wrote ourselves.**

I own a specific part of this. K3B §2.3 recommended the role-scoped maxima
(22 public / 27 risk) that F2 adopted, on top of the 15-word minimum Claude G
had set in K3B-R2. I checked the *aggregate* envelope against the composed
ceiling and never checked the *per-item band*: 15–22 is a seven-word target a
model must hit on roughly nine consecutive items, or the whole note drops. Two
individually reasonable rules multiplied into an unwritable contract, and my
review is where that product should have been computed.

## 1. The justification test

> A restriction is justified only if removing it would cause a real gate
> failure or a real safety violation. Everything else is our preference and
> must go.

Applied below to every rule now implemented in
`auditing/analyst_note.py`. "Gate" means an existing P36 validator we are
forbidden to change; "safety" means a boundary in AGENTS.md/CLAUDE.md.

## 2. Removed-constraint list

| # | Constraint as implemented | Remove it — what actually breaks? | Verdict |
| --- | --- | --- | --- |
| 1 | Per-item minimum 15 words (`parse_analyst_note`) | Nothing. No gate measures a clause. The composed floor is enforced by the length precheck. | **REMOVE** |
| 2 | Per-item maximum 40 words | Nothing, same reason. | **REMOVE** |
| 3 | Role-scoped maxima 22/27 (`_ROLE_ITEM_MAX_WORDS`) | Nothing. This plus #1 is the seven-word band that dropped News and Technical. | **REMOVE** |
| 4 | `what_to_verify` 8–28 words | Nothing. | **REMOVE** |
| 5 | Item counts 4–5 / 2–3 / 2–4 | Only the degenerate case: an empty field leaves a heading with no prose, which risks the structure gate and renders a hollow subsection. Counts above one buy nothing the precheck does not already enforce. | **REPLACE** with "each field is a non-empty list" |
| 6 | Exactly three keys, set-equality (a fourth key drops the note) | Nothing — **provided "ignored" means provably discarded, not merely unread** (§3.1). | **RELAX** to "the three required keys must be present"; record only the *count* of unrecognized keys (never names or values) |
| 7 | Clause must be entirely lowercase (`_is_lowercase_clause`) | Nothing — capitalisation mid-sentence is cosmetic, and the composer can lowercase the first character deterministically when framing. | **NARROW** — drop the case rule |
| 7b | Clause must not end with terminal punctuation | **A real gate failure.** F-4.6 splits composed prose on `[.!?]\s+`; a period inside a clause splits the framed sentence and strands the fragment without its attribution marker. | **KEEP**, widened to "no `.`/`!`/`?` anywhere in a clause" |
| 8 | Verification item must begin with a whitelisted imperative | Nothing. A non-imperative verification line fails no gate; genuinely advisory phrasing ("should") is already caught by F-4. | **REMOVE from the validator**; keep as prompt guidance |
| 8b | Verification item is a single sentence | **A real gate failure** — same F-4.6 splitting reason as 7b. Load-bearing in a new way once #17 is removed: a verification line may now legally contain `concentration` or `drawdown`, so a second sentence would render past the frame and lose its attribution marker. | **KEEP**, enforced precisely (Claude G, M2-R3): no `.`/`!`/`?` internal to the item, at most one terminal mark at the end — the same precision §2 applies to 7b |
| 9 | No digits; no spelled magnitude before a unit word | **Real F-5 failure.** This is the core of the redesign. | **KEEP** |
| 10 | No month/quarter/fiscal-period names | **Real F-5 failure** (date provenance). | **KEEP** |
| 11 | Internal-key and snake_case token pattern; URLs and paths; secret-like values | **Real F-6 / source-leak / display-token failures.** | **KEEP** |
| 12 | Ticker regex and exact frozen-symbol match | No gate fires, but a model-emitted instrument identity can be **wrong**, and nothing downstream would catch a misidentified instrument in a financial report. That is a real harm even though no validator names it. | **KEEP** (narrow, as written) |
| 13 | Markdown syntax inside a clause | **Real structure failure** — model markdown inside a frame can forge a heading or table row in the composed section. | **KEEP** |
| 14 | `_has_noninitial_proper_noun` | **A real safety violation, once #7 is also removed.** The original reasoning — unreachable on clauses because clauses are lowercase — depends on the very rule #7 deletes. With both gone, nothing stops a model naming an unrelated issuer ("the company trails Microsoft in reported margins"): rule 11 catches system tokens and sources, rule 12 catches the reviewed symbol, neither catches an arbitrary third-party company. An unverifiable third-party identity claim in a financial report is the class K3 exists to prevent. | **KEEP for `observation` and `why_it_matters`** (Claude G, M2-R3) |
| 15 | `_copies_supplied_label` | Label reuse fails no gate. The genuine risk is narrower: a label containing document-fatal vocabulary (`annualized`, `yield`) would fail the whole-report scan — worse than a role drop. | **REPLACE** with a direct banned-vocabulary check (§4.2) |
| 16 | Advice-boundary classes (`_advice_boundary_flag`) | **Real F-4 failure and a real safety boundary.** | **KEEP unchanged** |
| 17 | Interpretation terms banned in `what_to_verify` | **A real F-4.6 failure today** — verification lines render unframed, so `concentration` or `drawdown` with no marker fails attribution. But the fix belongs in *our* composer, not in the model's vocabulary. | **REMOVE from the validator**, and frame verification lines (§4.1) |

Net effect: every length rule disappears except the composed-length precheck;
the no-facts core (F-5/F-6), the advice boundary (F-4), the two
sentence-integrity rules that protect F-4.6, and the third-party identity check
(#14) remain.

**Method note (Claude G, M2-R3).** Rows 7 and 14 were each justified in
isolation and, taken together, opened a hole neither one opens alone — the same
shape of error this document opens by owning at §0, where a 15-word minimum and
a 22-word maximum multiplied into an unwritable band. When a review removes
more than one rule, the removals must be evaluated as a set, not a list.

**Authorized additive surface after M2.** Two fields — `analysis_status` and
`pm_fallback_reason` — plus, under M2, one additional `analysis_status` enum
value (`note_incomplete_response`), one closed warning code
(`live_note_incomplete_response`), and one static availability line. Nothing
else is sanctioned; anything beyond this list is drift.

## 3. Revised note contract

```json
{
  "observation":     ["clause", "..."],
  "why_it_matters":  ["clause", "..."],
  "what_to_verify":  ["sentence", "..."]
}
```

- The three keys must be present and each must be a non-empty list of strings.
  Unrecognized keys are ignored, not fatal — under the containment rule in
  §3.1.
- **No length rule of any kind on items or counts.** The single length
  authority is the composed-length precheck against the existing role window.
- Clauses contain no `.`, `!`, or `?`. Verification lines are one sentence
  each.
- No-facts rules 9–13 and the advice boundary apply unchanged.

The prompt (K3B §3–§5) still *asks* for roughly four observations, two or three
why-it-matters clauses, and a few verification lines, and still asks for
clauses that complete the frame. **Guidance in the prompt, not a drop in the
validator** — that is the whole shape of this revision.

### 3.1 Extra-key containment (Codex B binding blocker 3)

"Ignored" is only safe if it means **provably discarded at the parse
boundary**. The parser constructs `AnalystNote` from the three recognized keys
alone; the raw decoded payload is not retained, not attached to the note, and
not passed onward. Unrecognized key names and values must never reach:

- backend composition or any composed markdown;
- a re-ask prompt (§5) — re-asks carry only the static instruction;
- any log, trace, or diagnostic record (§6) beyond the integer
  `unrecognized_key_count`;
- the frozen artifact, or anything rendered on readback.

**Correction (Codex B, M2-R2).** An earlier revision required a single canary
in which an *accepted* note carried a secret-like extra key. That state cannot
occur, and specifying it was a real defect: `LLMProviderResponse.__post_init__`
validates the whole response payload through `validate_llm_provider_output`
before the runner ever parses it (`llm_clients/contracts.py:229-243`), and that
scan raises on secret-like values found anywhere in the payload strings —
including inside the JSON text of `content_markdown`. A secret-like extra value
therefore never reaches `parse_analyst_note`. The impossible fixture is
withdrawn: an unsatisfiable test invites whoever implements it to bypass or
weaken the provider-output check in order to construct the state, which is the
opposite of what the canary is for.

Containment is proven by **two separate required tests**, one per boundary.

**Test 1 — provider-boundary rejection.** A provider response whose content
carries a *nested* secret-like extra value (a token-shaped string inside a
nested object) is rejected at the provider boundary, before parsing. Assert the
value reaches **no** parser result, composed markdown, frozen artifact,
readback projection, re-ask prompt, log, or diagnostic record. The role
degrades through the existing provider-failure path and, per §5, receives **no
re-ask** — this is not a note-validation failure. Provider-output safety is
exercised here, never relaxed to build the fixture.

**Test 2 — parser containment.** A *nested* URL-like but **non-secret** extra
value accompanies fully valid recognized fields, so it passes the provider
boundary and reaches the parser. This is the case the containment rule actually
governs: `validate_analyst_note` never inspects it, because it iterates only
the three recognized fields. Assert the parser accepts the note on those three
fields alone, discards the extra data, and the value appears **nowhere** in
composed markdown, the frozen artifact, the readback projection, the re-ask
prompt, or the diagnostic record. Only `unrecognized_key_count`, as an integer,
survives.

Both tests assert absence across the **serialized** payloads, not merely that
the composer did not read the value — serialization is where a retained raw
payload would actually leak.

## 4. Backend changes that absorb the removed constraints

### 4.1 Verification lines are framed too

Constraint 17 exists because verification lines render unframed. Frame them,
exactly as observation and why-it-matters are framed:

```
Per the saved scope: {verification sentence}
```

`the saved` is an exact `P36_ATTRIBUTION_MARKERS` substring, the colon keeps it
one sentence, and the imperative survives intact. Analysts regain their own
vocabulary — Risk can say `concentration`, Technical can say `drawdown` — with
attribution supplied deterministically by us.

### 4.2 Banned-vocabulary check replaces label copying

A single note-scoped check over the never-list already in K3B §5 ¶3 plus the
document-scan patterns. It converts a would-be whole-report failure into a
role-level withheld, which is the only reason a pre-emptive check is justified
at all. Referring to "the cash impact" stays legal; writing `annualized` does
not.

## 5. Bounded recovery

Today a failed note ends the role while budgeted calls sit unused
(`tool_mediated_runner.py:1031-1046` → `_k3_note_withheld`). Add re-ask:

**Budget (Codex B binding blocker 1).** Each analyst has a **total cap of three
provider calls**, and that cap counts **every** call the role makes — including
earlier mediated tool-request turns, not just note attempts. A re-ask consumes
a remaining slot or does not happen:

- an analyst that spent two calls on tool requests has **one** slot left, so it
  gets its note attempt and **no** re-ask;
- an analyst that requested no tools may use up to two re-asks;
- **no cap increase**, no new provider configuration, and **no additional
  source or tool fetch** may be triggered by a re-ask — a re-ask re-asks, it
  does not re-gather;
- **no retry at all** after a timeout, an auth failure, a provider-unavailable
  result, or a quota/rate-limit outcome. Those are provider-health states, not
  note-validation failures; the role degrades exactly as it does today. Re-asks
  exist solely for a response that arrived and failed *our* note validation.
- Feedback is a **static instruction selected by closed failure code**. The
  model's own text is never echoed back — echoing failed output would re-inject
  unvalidated content into the prompt — and validator internals (patterns,
  thresholds, rule names) are never disclosed.

| Failure code | Static re-ask instruction (verbatim) |
| --- | --- |
| `note_unparseable` | `Return only one strict JSON object with the three required keys and no other text.` |
| `note_field_empty` | `Each of the three keys must hold at least one entry. Return the complete object again.` |
| `note_clause_punctuation` | `Write each observation and why-it-matters entry as a clause with no period, question mark, or exclamation mark inside it.` |
| `note_verify_form` | `Write each verification entry as one single sentence.` |
| `no_facts_number` | `Write no digits and no spelled quantities. The system supplies every figure.` |
| `no_facts_date` | `Write no dates and no month, quarter, or fiscal-period names. The system supplies them.` |
| `no_facts_identity` | `Do not name a company, symbol, exchange, agency, or data source. Refer to the reviewed symbol, the company, or the portfolio.` |
| `no_facts_internal_token` | `Remove any link, path, code, or system field name.` |
| `no_facts_markup` | `Write plain sentences with no markdown, list, or table syntax.` |
| `no_facts_vocabulary` | `Rewrite without evaluative, forecasting, or recommending words.` |
| `advice_boundary` | `Rewrite without evaluative, forecasting, or recommending words.` |
| `length_below_window` | `Your note was too brief for this section. Write more fully in the same three fields.` |
| `length_above_window` | `Your note was too long for this section. Write more briefly in the same three fields.` |

After the final attempt the role records `withheld_by_review` exactly as today.
The re-ask instruction is appended as a fresh user turn; the system prompt is
unchanged and stays registry-exact.

## 6. Offline capture/replay diagnostic

Purpose: stop guessing which sub-rule fired. **Structural metadata only.**

Record, per attempt:

```
role_name, attempt_index, outcome_code, sub_rule_id,
field_item_counts {observation, why_it_matters, what_to_verify},
per_item_word_counts [int, ...]        # integers only
composed_projected_words, window_low, window_high,
unrecognized_key_count,                # integer only, never names or values
provider_status,                       # the EXISTING closed provider status
provider_finish_reason                 # closed enum: none | stop | length | unknown
```

**Vocabulary (Codex B binding blocker 2).** `provider_finish_reason` uses the
closed enum `none | stop | length | unknown`, which is not invented here: the
provider contract already constrains `finish_reason` to exactly
`(None, "length", "stop", "unknown")` (`llm_clients/contracts.py:229-232`), so
the diagnostic vocabulary is derived from the contract rather than parallel to
it —
`none` when the provider reported no finish reason, `unknown` for any value
outside the contract, so an unmapped provider string is never passed through
verbatim. The **existing closed `provider_status`** is recorded on every
record, which is what makes Ruling B measurable: a successful-but-truncated
response (`provider_status = ok`, `finish_reason = length`) becomes
distinguishable from a transport failure (`provider_status` in its error
values) instead of collapsing into one `provider_unavailable` bucket.

Hard rules: **no model prose, no clause text, no report content, no label
values, no identifiers, no provider payloads.** Every field is a closed code or
an integer. The record is produced by an offline test helper and by a replay
entry point that accepts a synthetic or sanitized response *shape* (same
structure, synthetic strings) and runs the real validator chain. It is never
persisted to a report artifact and never rendered. An offline canary asserts
the no-prose property by construction, not by inspection.

This is what turns the two rulings below from inference into measurement.

## 7. Ruling A — Risk `analyst_note_no_facts_blocked`

**Most likely trigger, in order: (1) `_INTERPRETATION_TERMS_RE` on a
`what_to_verify` line; (2) `_copies_supplied_label`.** Both are cases where the
role block instructs the model to write exactly what the validator forbids.

- `_INTERPRETATION_TERMS_RE` bans `concentration`, `leverage`, `drawdown`,
  `trend` in verification lines. Risk's entire domain is concentration and
  exposure, and its role block says "order the checks a reviewer should make".
  The natural check — confirm the concentration figures against a fresher
  snapshot — is illegal by construction. This is my first-choice explanation.
- `_copies_supplied_label` matches a whole-token phrase from any `fact_key` or
  `value_label`. Risk's role block tells it to discuss "the exposure changes,
  the concentration picture, the cash it consumes" — the same words the
  deterministic labels use. A two-token label like `cash_impact` makes "the
  cash impact" a drop.

Both are removed or replaced in §2 (#15, #17), and §4.1/§4.2 absorb the real
risk. **To be confirmed by the §6 diagnostic `sub_rule_id`, not assumed** — if
it reports something else, that rule gets the same justification test before
anything is changed.

## 8. Ruling B — Fundamentals `provider_unavailable` with `provider_status ok`

**This is a classification defect, and the underlying event is most likely a
truncated response, not an unavailable provider.**

The public loop maps `finish_reason == "length"` — and any non-`ok` payload
status — to `_live_provider_fallback(deterministic, "unavailable")`, which
emits `live_provider_unavailable`. The transport call succeeded, so
`provider_status` is recorded `ok`. That is exactly the contradiction observed:
a **content** outcome reported as an **availability** outcome.

Why truncation is plausible at `P36_ANALYST_MAX_TOKENS_PER_ITERATION = 2000`:
the note itself is small (~135 words minimum under the old bounds, well under
the budget), but reasoning/"thinking" tokens on current Gemini models are
charged against the same output budget, and the JSON is emitted last — so the
object gets cut mid-string and `finish_reason` returns `length`. Removing the
per-item minima (§2 #1) shortens the required output and reduces this pressure
as a side effect.

### 8.1 Codex B binding decision — `note_incomplete_response` APPROVED

Approved as an additive `analysis_status` value, **scoped strictly to
`finish_reason = length` outcomes** and nothing else:

- `analysis_status = "note_incomplete_response"` is set **only** when the
  provider returned a response whose finish reason is `length`. Every other
  outcome keeps its current classification; in particular a transport failure,
  auth error, timeout, or quota/rate-limit result remains
  `provider_unavailable`.
- One additive **closed warning code**: `live_note_incomplete_response`,
  alongside the existing live-gate warning codes.
- One additive **static readback availability line**, in the same register as
  the existing three: **"Live analysis was incomplete for this saved report."**
  It discloses no provider detail, no internals, and no blame.
- The K1 read-contract **enumeration and rendering table are amended** in
  `PHASE_36_T7_AGENT_SECTION_CONTENT_CONTRACT.md` to carry the new value and
  its line.
- **Historical artifacts remain `analysis_status = None` with unchanged
  behavior.** No migration, no backfill, no re-derivation.
- No gate, threshold, source, provider, PM prompt, or no-facts/advice/privacy
  rule changes as part of this.

**Still confirm before tuning.** The classification split makes truncation
*visible*; it does not establish that L2's Fundamentals failure was truncation.
The §6 diagnostic (`provider_status` + `provider_finish_reason` on every
record) settles that in one offline replay. A token-budget change remains a
provider/config change and stays out of bounds for this slice.

## 9. Unchanged

Gates, thresholds, validator constants, sources, providers, the PM prompt, the
frozen-artifact contract, `analysis_status` semantics, K1-compatible historical
projection, and the K3A no-facts principle. This slice removes **our**
constraints only.

## 10. Baseline acceptance

Per the founder directive, the target is a working baseline, not polish:

1. All four analysts reach `analysis_status = accepted` offline, on
   **realistic note shapes** — fixtures written as a model would plausibly
   write them, including natural role vocabulary (`concentration`,
   `drawdown`, "the cash impact"), not idealized strings tuned to pass.
2. Zero occurrences of `analyst_note_structure_blocked`,
   `analyst_note_no_facts_blocked`, or any L1-era gate code on those fixtures.
3. The recovery path is exercised: a first-attempt failure of each closed code
   recovers on re-ask, with the static instruction asserted. Budget canaries
   prove the §5 cap: a role that spent two calls on tool requests gets **no**
   re-ask, and none of timeout / auth / provider-unavailable / quota outcomes
   triggers a retry.
4. The diagnostic produces a record for every fixture, and its output contains
   no model-authored text (asserted, not assumed), with `provider_status` and
   the four-value `provider_finish_reason` present on every record.
4b. **Extra-key containment, two tests** (§3.1): the provider-boundary
   rejection test (nested secret-like value rejected before parsing, no
   re-ask) and the parser-containment test (nested URL-like non-secret value
   discarded at parse, appearing in no composed section, artifact, readback
   projection, re-ask prompt, or diagnostic record — only the integer count
   survives). Neither test may relax provider-output safety, the no-facts
   rules, the output gates, or the privacy checks to construct its fixture.
4c. `note_incomplete_response` is set for a `finish_reason = length` fixture
   and **not** for transport-failure, auth, timeout, or quota fixtures; its
   readback line renders; historical `None` rows are unchanged.
5. Existing suites stay green; gate and safety modules zero-diff; PM SHA-256
   pin green.
6. **No further tuning after this.** If the baseline holds offline, the next
   step is a founder-authorized live run — not another constraint round.

## 11. Handoff

Codex B contract review (§2 verdicts, §3 contract, §5 recovery codes, §6
diagnostic fields, §8 recommendation 1) → Claude G architecture/privacy review
(§4 framing, §5 no-echo property, §6 no-prose property) → Codex C implements
§2–§6. K3B §3–§5 prompt blocks need only the guidance edits implied by §3
(counts and lengths become suggestions); if Claude G judges those edits
material, they return through the static-prompt review path.
