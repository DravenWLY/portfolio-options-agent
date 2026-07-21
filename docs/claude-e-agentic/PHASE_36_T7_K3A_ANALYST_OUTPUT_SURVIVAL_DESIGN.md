# Phase 36 T7-K3A — Analyst Analysis-Survival Redesign

Status: approved (K3A-R2) — Codex B contract review PASS; Claude G
architecture/privacy review PASS with three required edits, applied in place
2026-07-21 (persistence target named as `live_report_markdown`; rule 5
substring matching bounded; F-4.6 coverage extended to backend-owned lines).
Cleared for Codex C implementation.
Owner: Claude E (gate/eval + agentic systems design)
Mode: design only. No implementation, no live calls, no gate changes.

## 0. What this replaces, and why prompt tuning is not the answer

The authorized live run produced zero accepted analyst sections. Two rounds of
prompt tuning (K2A/K2B wording, K3E offline validation) preceded it. K3E
proved the gates accept guidance-compliant prose and reject near-misses at the
right flag — and I stated at its closeout that no live model had yet written
under the tuned prompts, and that first live prose might still drop. It did.

A third wording round is the wrong response. The evidence says the failure is
**structural, not lexical**: the current contract asks one model turn to do
three jobs at once —

1. produce analysis (the job we want),
2. restate backend-owned facts exactly (numbers, dates, labels, sources),
3. emit a byte-exact markdown layout (heading sequence, table header, word
   bounds).

Every failure code in the run comes from jobs 2 and 3.

**Correction (Codex B, K3A-R1) — what the missing advice flag does and does not
mean.** An earlier revision of this document claimed the absence of
`advice_boundary_blocked` proved the model respected the no-advice boundary.
That inference is unsound and is withdrawn. The gates short-circuit on the
first failure: `validate_p36_public_analysis_section` returns the F-5/F-6 value
flag before `_advice_boundary_flag` is ever called
(`v3_value_gates.py:299-304`), and the risk path is ordered the same way. On
every attempt that returned `numeric_provenance_blocked`, **the advice gate
provably never executed**; on the Fundamentals attempts that ended in
`live_provider_safety_fallback`, no gate ran at all. The correct statement is:
*no advice-boundary failure was recorded before another gate ended
validation.* We have **no evidence** about the model's advice behavior in this
run, in either direction.

The redesign does not rest on that withdrawn claim. It rests on the failures
that *were* recorded, all of which are mechanical. And because the model's
advice behavior is now explicitly unmeasured, every advice-boundary validator
and canary is retained unchanged (§3.1 rule 8, §7-C) — this design tightens
that surface and assumes nothing about it.

This design deletes jobs 2 and 3 from the model's responsibilities. The model
returns a small typed note containing *no facts at all*; the backend — which
already owns every value, label, date, and reference — composes the section.
The safety boundary is unchanged and the gates are untouched.

**Precedent, not invention:** the PM surface is the one live surface designed
this way (typed JSON, sentence-bounded fields, no markdown), and it is the one
analyst-adjacent surface that has never been dropped by a structure or
provenance gate. K3A extends the proven pattern to the four analysts.

## 1. Root-cause map: failure code → contract change

| Observed code | Role(s) | Mechanism | K3A change that removes it |
| --- | --- | --- | --- |
| `numeric_provenance_blocked` | News, Technical, Risk | Model restated a value/date that did not match its surfaced facts, or hit the long-date (`Capitalized-word + digits`) or spelled-magnitude traps (`v3_value_gates.py:549,567,129`) | §3 no-facts rule: model output is **digit-free and date-free**; backend supplies every value. F-5 becomes vacuously satisfiable for the model's contribution, and is *strictly tightened* on it |
| `attribution_required_blocked` | Risk | Per-sentence rule: any sentence with a trigger word (`trend`, `elevated`, `drawdown`, `concentration`, …) must itself contain an attribution marker (`:239,641`) | §4 backend-owned sentence frame: the backend renders every model clause inside a marker-bearing sentence, deterministically. Attribution is true by construction, not by model recall |
| `structure_contract_blocked` | Technical, Risk | Exact heading sequence, exact table header, word bounds (`_public_structure_flag`, `_risk_structure_flag`) | §4 backend composition: the model emits no markdown. Headings, table, and bounds are backend-owned and cannot fail from model behavior |
| `live_provider_safety_fallback` | Fundamentals, Risk | Loop exhausted or two consecutive unparseable responses (`tool_mediated_runner.py:875-899`) | §3 typed contract: one small strict-JSON object is far easier to satisfy than a multi-heading markdown section; §6 makes the remaining fallback an explicit, honest failure state |
| `final_synthesis_authored_by=deterministic_template` | PM | **Cascade, not a demonstrated PM defect:** with zero accepted analyst sections the PM had nothing to synthesize | No PM change (requirement 7). Accepted analyst notes are a *precondition* for PM authorship, never a proxy for it — the PM must still produce its own accepted typed synthesis, asserted independently in §7-F |

Because a single validation returns only its first flag, the multi-code
listings for Technical and Risk reflect different attempts within the bounded
loop, not one section failing three ways at once. Read every row as "this gate
ended validation on at least one attempt", never as a complete account of what
a section contained.

## 2. Design principle

> The deterministic floor owns every fact. The model owns only judgment about
> those facts, expressed in language that cannot carry a fact.

This is the existing P36 doctrine, applied one level further. Today the model
is trusted to *repeat* facts and gated when it repeats them wrong. Under K3A
the model is never in a position to repeat a fact at all, so the class of
failure disappears rather than being policed.

Analysis quality is preserved because the analytical contribution was never the
numbers: it is *which evidence matters, what its limits are, and what a
reviewer should check.* The backend prints the table; the analyst says what to
make of it.

## 3. The typed output contract (`AnalystNote`)

One shape for all four analysts; role distinctness comes from framing, evidence
menu, and backend projection (§5).

```json
{
  "observation": ["clause", "clause", "clause"],
  "why_it_matters": ["clause"],
  "what_to_verify": ["imperative sentence"]
}
```

Bounds (F-1 structural parse; whole-note fail-closed on any violation):

| Field | Type | Bounds |
| --- | --- | --- |
| `observation` | list of clauses | 2–4 items, each 8–40 words |
| `why_it_matters` | list of clauses | 1–3 items, each 8–40 words |
| `what_to_verify` | list of sentences | 1–4 items, each one sentence |

**Exactly three keys. Citations are not among them (Codex B, K3A-R1).** An
earlier revision let the model select `evidence_refs` from a closed backend
menu. That is withdrawn: the model must not select, rank, or attach evidence
references at all, even from a closed set, because ref selection is itself a
factual claim about which evidence supports which statement. **The backend
attaches each role's approved evidence references deterministically after note
validation** (§4.1), from the role's own lane. A note containing any fourth key
— `evidence_refs` included — fails the structural parse and drops.

### 3.1 The no-facts rule (allowed language)

Applied to every string in `observation`, `why_it_matters`, `what_to_verify`.
Each is a **structural check on the model's own text**, evaluated before
composition. Any violation drops the whole note.

1. **No digits.** `\d` anywhere → drop. (Strictly stronger than F-5.)
2. **No spelled quantities.** Reuse `_SPELLED_MAGNITUDE_RE` semantics: a
   spelled cardinal before percent/dollars/points/basis points/shares/
   contracts/days → drop.
3. **No dates in any form**, including month names and quarter/fiscal-period
   labels.
4. **No proper nouns naming a source, issuer, symbol, form type, or venue.**
   Identity is backend-owned. (Check: no capitalized token outside sentence
   start, plus a closed denylist of source words.)
5. **No verbatim label copying.** No supplied `value_label` or `fact_key`
   appears in any field. Match on whole tokens or whole phrases,
   case-insensitive, only for labels of at least two tokens or twelve
   characters; availability, freshness, and status category words are excluded
   from this check (they remain governed by rules 1–4 and 6). Plain substring
   matching is forbidden here: supplied labels include ordinary words such as
   `available`, and substring matching would drop honest clauses like "the
   statement record is not available", reintroducing the brittle-drop class
   this redesign exists to remove (Claude G, K3A-R2).
6. **No URLs, paths, accession-style tokens, identifiers, or evidence-reference
   ids** (existing identifier/secret/source-leak scans continue to apply
   unchanged; a note that names a reference id in prose drops).
7. **`what_to_verify` items must begin with a verification imperative** from
   the existing F-2 whitelist (`verify, check, confirm, review, re-sync,
   compare`) and must contain no interpretation-trigger word.
8. **All existing advice-boundary classes continue to apply unchanged** to
   every field — the safety boundary is untouched (requirement 4), and, per the
   §0 correction, is now the surface about which this run gave us no evidence
   whatsoever.

Rules 1–6 are what make the section survivable; rule 8 is what keeps it safe.
Note the asymmetry: this is **more** restrictive on the model than today's
contract, never less.

### 3.2 Clauses, not sentences — and why

`observation` and `why_it_matters` carry **lowercase clauses that complete a
backend-owned sentence frame** (§4.2). This is what makes F-4.6 attribution
deterministic: the marker lives in the frame the backend controls, so every
rendered sentence carries true attribution regardless of what the model wrote.
The prompt instruction is concrete: *write each item as a lowercase clause that
completes the sentence "Computed from the saved evidence, …".*

### 3.3 Per-role framing (the distinctness driver)

Same schema, four different questions over four different evidence sets. The
role still *receives* its sanitized envelopes and calculation results as today
— it reasons over them — but it never names or cites them; the backend attaches
references from the same lane after validation.

- **Fundamentals — business/fundamental evidence context.** What the reported
  record does and does not cover, and how current it is. Evidence supplied:
  profile, statement facts, ratio/period-change results, freshness.
- **News — filing/event context and evidence gaps.** What kind of dated record
  exists, what is absent, and which gap most limits reading it. Evidence
  supplied: filing metadata, event calendar, macro series, event-window/
  series-change results, freshness.
- **Technical — end-of-day context, recency, and verification questions.**
  What the saved price window can and cannot support, and how its recency
  bounds the reading. Evidence supplied: range/return/drawdown/volatility/MA
  results, quote freshness.
- **Risk — portfolio/scope risks, uncertainty, and verification priorities.**
  Which scope and freshness limits most undermine the run's figures, and what
  to re-check first. Evidence supplied: scope, deterministic findings,
  exposure/concentration/cash results, snapshot freshness, evidence-gap
  inventory.

## 4. Backend projection model

The backend composes the section; the model never emits markdown.

### 4.1 Composition order (per role, deterministic)

1. Backend title with the reviewed symbol.
2. Role heading set in the required order (unchanged from today's contracts,
   including the fundamentals/news variant headings).
3. Under the analytical headings: the framed model clauses (§4.2).
4. Under the gap/recency heading: framed clauses plus backend-owned freshness
   and availability facts.
5. `##### What was verified`: backend-composed from the calculations actually
   used and their as-of dates, followed by the model's `what_to_verify` items
   rendered as sentences.
6. The closing evidence table: **entirely backend-owned**, built from tool
   results through the existing approved display-label path (K2C mapping
   honored).
7. **Evidence references: attached deterministically by the backend** from the
   role's own lane, after note validation. The model contributes nothing to
   this step — it neither selects, ranks, orders, nor names a reference.

Composition happens in the **orchestration runner**, and the composed markdown
is **persisted** on the artifact. Readback renders exactly the persisted bytes
and never recomposes (Codex B binding decision, §9).

**Persistence target (Claude G, K3A-R2).** The composed section is persisted in
the existing `live_report_markdown` field, which K1R's `Analysis` renders
verbatim. No new markdown field is authorized; if the composed section cannot
be persisted there, stop and return the conflict rather than adding a field.

Because steps 1, 2, 5, and 6 are backend-owned, `structure_contract_blocked`
and `what_was_verified_blocked` cannot be caused by model behavior, and every
number in the section carries real provenance because the backend put it there.

### 4.2 Sentence frames (attribution by construction)

| Field | Rendered as |
| --- | --- |
| `observation` item | `Computed from the saved evidence, {clause}.` |
| `why_it_matters` item | `Per this run's review scope, {clause}.` |
| `what_to_verify` item | rendered verbatim as its own sentence (trigger-free by rule 7) |

Both frames contain an exact `P36_ATTRIBUTION_MARKERS` substring, so every
sentence that could contain a trigger word satisfies F-4.6 deterministically.
The attribution is *accurate*: the clause is a reading of this run's saved
evidence, which is what the marker asserts.

### 4.3 What the gates then see

The composed markdown runs through the **existing, unmodified** gate stack.
Expected outcome by construction: F-5 passes (every number is backend-surfaced),
F-4.6 passes (frames), F-8/F-9 pass (backend layout), F-4 advice classes remain
a real check on the model's clauses, F-6/F-11 and the document scan unchanged.

**Backend-owned lines are scanned too (Claude G, K3A-R2).** The F-4.6
per-sentence attribution scan exempts **only heading lines**
(`v3_value_gates.py:678-683`); backend-owned table rows and freshness lines are
scanned like any other prose, and several approved display labels contain
trigger words (`drawdown`, `trend`, `concentration`). The composed section as a
whole — including backend-owned table rows and freshness lines — must satisfy
F-4.6 for every role and every lane variant, asserted directly (§7-D) rather
than assumed from the frames. Under this design a trip there is a backend
defect, not model variance.

**No validator is weakened.** The model additionally faces the §3.1 no-facts
rule, which has no counterpart today.

## 5. Accepted-analysis status (requirement 6)

Today `role_status` (`completed|unavailable|skipped|gated|validation_failed`)
and `provider_status` both exist, and the renderer infers acceptance from
`role_status == "completed"` **plus a non-null `live_report_markdown`**
(`reports.py:1758-1764`). Acceptance is implicit in a null check — which is
exactly how a completed provider call got read as a successful role.

Add one explicit, additive, **nullable** field to the frozen source model and
the read projection alike:

```python
analysis_status: Literal[
    "accepted",              # a typed note passed every check and was composed
    "withheld_by_review",    # note produced but dropped by a gate/no-facts rule
    "provider_unavailable",  # loop/provider failure; no note produced
    "no_evidence",           # role had no reviewed evidence to analyze
] | None = None
```

**Legacy safety (Codex B, K3A-R1).** The field must **not** default to
`no_evidence`: a historical artifact frozen before K3 carries no such state,
and stamping one would retroactively assert a status that was never evaluated.
The default is `None`, and:

- **Historical artifacts (`None`) retain the existing K1-compatible projection
  behavior exactly** — the renderer falls back to today's `role_status` +
  non-null-markdown logic (`reports.py:1758-1764`). No migration, no
  backfill, no re-derivation (§9).
- **Every newly generated K3 role must write a non-null value.** This is an
  invariant asserted in the eval matrix (§7-B2), not merely a convention.
- The same nullable field is added to the read projection so the UI reads one
  field rather than re-deriving acceptance.

`analysis_status == "accepted"` is the **only** signal the acceptance gate (§8)
may read for a K3 run. A completed provider request is explicitly not
sufficient. This one additive field is the entire authorized read-contract
expansion; see the amendment recorded in
`PHASE_36_T7_AGENT_SECTION_CONTENT_CONTRACT.md`.

## 6. UI and readback rule (requirement 5)

Binding, and consistent with the K1R content contract:

- `analysis_status is None` (historical, pre-K3) → **unchanged K1 behavior.**
  The renderer uses today's logic verbatim; this design changes nothing about
  how an existing frozen report projects.
- `analysis_status == "accepted"` → `## Analysis` renders the composed section
  verbatim, nothing else.
- Any other non-null value → `## Analysis` renders **exactly one** honest line
  and nothing else:
  - `withheld_by_review` → "Live analysis was withheld by review safeguards."
  - `provider_unavailable` → "Live analysis was unavailable for this saved
    report."
  - `no_evidence` → "Analysis was not available from the frozen evidence
    package."
- **Deterministic status text is never rendered as analysis.** Deterministic
  `summary_markdown`, warning labels, freshness narration, and status codes
  live only under `## Frozen debugging details`, humanized through the
  existing display-label path.
- Frozen readback renders exactly the saved state, with zero provider or
  source calls.

The failure state is legible as a failure. It never impersonates analysis.

## 7. Offline acceptance matrix (synthetic frozen evidence only)

All fake-provider; no live provider, market, or EDGAR calls.

**A. Accepted path (per role, ×4).** A guidance-compliant typed note over
active-lane fixtures → note validation passes → composed section passes the
full existing gate stack → `analysis_status == "accepted"` → section non-empty
and contains backend facts the model never wrote.

**B. No-facts rule canaries (per role, one per rule 1–7).** Digit; spelled
quantity; date; month name; source proper noun; verbatim label copy;
reference-id token in prose; `what_to_verify` item without an imperative or
containing a trigger word. Plus a **fourth-key canary**: a note carrying
`evidence_refs` (or any other extra key) fails the structural parse. Each →
whole-note drop, `analysis_status == "withheld_by_review"`, no partial render.

**B2. Status invariants (Codex B, K3A-R1).**
- Every newly generated K3 role writes a **non-null** `analysis_status` — for
  each of the four roles, across accepted, withheld, unavailable, and
  no-evidence paths.
- A **historical frozen role with `analysis_status = None`** projects exactly
  as it does today (K1-compatible), asserted against the pre-K3 rendering for
  the same fixture. No migration or backfill occurs.

**C. Safety-boundary canaries (per role).** Every existing advice class, plus
the news-inherited absolutes and PM-proven soft-verdict shapes, asserted inside
`observation`/`why_it_matters` → `advice_boundary_blocked`, whole-note drop.
These prove the boundary survived the redesign.

**D. Structure invariance.** With a valid note, the composed section satisfies
heading order, table header, and word bounds for every role and every
lane-variant (profile-only fundamentals, no-macro news) — asserted directly,
proving `structure_contract_blocked` is unreachable from model behavior.
**Additionally (Claude G, K3A-R2): assert that the whole composed section —
backend-owned table rows and freshness lines included, not only the framed
model clauses — passes F-4.6 for every role and lane variant.** A backend
display label carrying a trigger word without an attribution marker in its own
sentence must be caught here, offline, rather than dropping a live section.

**E. Distinctness and backend-owned citation (requirement 1).** The four
accepted sections are pairwise non-substitutable: no role's `observation` or
`why_it_matters` text appears in another role's section, and each role's
backend fact block is drawn only from its own lane. **Citation ownership is
asserted directly:** every attached evidence reference on every role traces to
that role's own lane and to the backend attachment step — no reference is
derived from, ordered by, or correlated with model output, and a note that
names a reference id in prose drops (§7-B rule 6).

**F. Cascade precondition and independent PM acceptance.** Four accepted
analyst notes are a *precondition*, never a proxy, for PM success. Assert
separately and in this order: (1) the PM receives the accepted sections; (2)
the PM produces its **own** accepted typed synthesis through the unchanged PM
gate stack; (3) only then `final_synthesis_authored_by ==
"portfolio_manager_agent"`. A companion fixture proves the negative: four
accepted analyst notes with a PM synthesis that fails its own gate → PM falls
back to `deterministic_template` while the four analyst sections remain
accepted. PM prompt SHA-256 pin unchanged; `p36-pm-synthesis-v1` untouched;
`p36_pm_prompt.py` zero-diff.

**G. Fail-closed and projection.** Starved package → notes still accepted where
honest (no facts to misstate) while number-bearing backend blocks degrade to
named gaps; any dropped note renders exactly one withheld line; frozen readback
byte-stable with zero provider reruns.

**H. Regression.** The full K3E matrix and all existing P36 suites stay green —
advice-boundary, privacy, URL, secret, identifier, document-scan,
readback-zero-rerun, and gate-regression tests included. The gates must still
reject the same near-misses at the same flags. Given the §0 correction, the
advice-boundary canaries carry extra weight here: they are the only evidence we
have about that surface.

## 8. Hard acceptance before another live run

All of the following, on one offline run of the matrix in §7 **and** on the
metadata of any subsequent authorized live attempt:

1. All four analysts produce non-empty, distinct accepted analysis
   (`analysis_status == "accepted"` ×4).
2. **Zero** occurrences of `live_provider_safety_fallback`,
   `numeric_provenance_blocked`, `attribution_required_blocked`,
   `structure_contract_blocked`, or any `live_*_dropped` code.
3. PM unchanged and PM-authored (`final_synthesis_authored_by ==
   "portfolio_manager_agent"`), confirming the cascade resolved.
4. Artifact freezes as `p36_tool_run_freeze_v1`; readback byte-stable, zero
   provider reruns.
5. Full offline suite green with gate modules zero-diff.

Item 2 is a *zero* threshold, not a rate: under this design those codes
indicate a structural defect, not model variance.

## 9. Contract decisions — RESOLVED (Codex B, K3A-R1; binding)

1. **Citations are backend-owned.** `evidence_refs` is removed from the model
   contract entirely (§3). The model does not select, rank, or attach
   references, even from a closed menu; the backend attaches each role's
   approved references after note validation (§4.1 step 7).
2. **Additive `analysis_status` field, nullable** (§5): `accepted |
   withheld_by_review | provider_unavailable | no_evidence | null`, default
   `None`, added to both the frozen source model and the read projection.
   Historical `null` retains K1-compatible projection; every new K3 role writes
   non-null. **This is the only authorized read-contract expansion** — recorded
   as an amendment in `PHASE_36_T7_AGENT_SECTION_CONTENT_CONTRACT.md`.
3. **Prompt-version key: keep `p36-role-analysis-v1`.** It remains the v3
   gate-family key, not a wording or shape identifier. No validator version-set
   edit. **No artifact migration.**
4. **Composition in the orchestration runner; composed markdown persisted;
   never recomposed on readback.**
5. **Authorized change surface, exhaustively:** the typed note contract and its
   validators (additive module), the four analyst prompts, the runner
   composition path, and the single `analysis_status` field. **No validator,
   source, provider, additional schema field, or PM-prompt change is
   authorized.** If implementation discovers a genuine gate conflict, Codex C
   stops and returns the precise conflict rather than adjusting any validator.

## 10. Implementation handoff (single owner: Codex C, after both reviews)

1. `AnalystNote` typed contract + parse/bounds validation (§3), mirroring the
   PmSynthesis pattern.
2. No-facts rule validators (§3.1) as a new note-scoped check module — additive
   only; no edits to `v3_value_gates.py` or `report_output_safety.py`.
3. Four reviewed static analyst prompts emitting the typed note (§3.3) —
   Claude E authors the verbatim blocks after this design passes review;
   Codex C registers them. `p36_pm_prompt.py` untouched.
4. Backend section composer **in the orchestration runner** (§4) with the
   sentence frames, backend-owned table, and backend-attached evidence
   references; persist the composed markdown on the artifact and never
   recompose on readback.
5. `analysis_status` plumbing (§5) end-to-end — nullable, default `None`,
   non-null on every new K3 role, K1-compatible projection preserved for
   historical `None`.
6. Runner loop: replace the markdown parse path with the typed-note path for
   the four analyst loops; keep bounded-loop, budget, and calc-request
   behavior unchanged.
7. The §7 offline matrix.
8. Verification: offline pytest only; report per-family counts and the
   zero-diff assertion for gate/safety modules and the PM prompt module. Do
   not commit until Codex B and Claude G both PASS.

## 11. What this design does not claim

It does not claim a live model will produce *good* analysis — only that the
mechanical failure classes that dropped every section are removed by
construction, and that the safety boundary is preserved and in places
tightened. Whether the resulting sections are analytically useful is a judgment
the founder should make on the first accepted output, and §7-E (distinctness)
is the strongest offline proxy available. As at K3E: no live model has yet
written under any K3A prompt.
