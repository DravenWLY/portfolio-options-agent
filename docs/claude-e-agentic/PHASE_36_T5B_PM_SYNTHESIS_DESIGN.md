# Phase 36-T5B — Portfolio Manager Synthesis: Role Block, Typed Contract, Gate Mechanics

- Owner: Claude E (role-block + gate-contract finalization; design §10 assembles
  the verbatim block with Claude E at implementation review).
- Status: APPROVED WITH BINDING CONDITION (Claude G, 2026-07-13) — PASS on the
  block/SHAPE, §4 gate map, §5 verify-not-recompute; RULING-T5B-1 (§6.1)
  APPROVED. **Binding condition (§4a/§7):** the freeform-field
  verdict-incapability in §2 depends on a subject-noun boundary that is **not
  yet implemented**; it must be built as a real PM-specific F-4 pattern and the
  §7.1/§7.3 pairs must actually drop from the freeform fields before T5B is
  accepted. Each assembled prompt still needs its per-prompt registration
  sign-off.
- Purpose: durable source of truth for the PM synthesis surface — the verbatim
  block + SHAPE-PM, the typed `PmSynthesis` contract and its verdict-incapability
  argument, whole-block fail-closed behavior, the F-1..F-13 mechanics over a
  typed non-section surface, PM calc-verification access, one new gate collision
  routed to Claude G, and the eval families. Mirrors
  [PHASE_36_T5A2_PUBLIC_ROLE_BLOCKS.md](PHASE_36_T5A2_PUBLIC_ROLE_BLOCKS.md).
- Reviewed inputs: design §9 (charter, inputs, typed schema §9.3, rendered
  shape §9.4, degradation §9.5), §10 (assembly), §11 (budgets), §12 (F-1/F-2/
  F-3); compat review §8.1 (PM typed output), §6.2.3 (suitability anchored to
  trade/position nouns), §13.3 (PM probes); activation §2 (gated live PM);
  the live tier code (`calculations.py` `_PUBLIC_CALC_TOOL_NAMES`,
  `reports.py` `AgentTeamReportSynthesisAuthor`).

## Assembly

The `p36-pm-synthesis-v1` system prompt is assembled, in order, exactly as the
analysts (design §10) — only the SHAPE differs:

    CORE-A  (verbatim, design §10 — shared; only role_display_name interpolated)
    {pm_role_block}   ← §1.1 below, interpolated here
    SHAPE-PM  (§1.2 below — a typed-JSON contract, NOT the analyst SHAPE-A)
    CORE-B  (verbatim, design §10 — shared; carries the verdict/advice bans onto the PM)

The assembled `(portfolio_manager_agent, p36-pm-synthesis-v1)` prompt is its own
`ReviewedStaticSystemPrompt` allowlist entry and needs its own Claude E +
Claude G prompt review before registration (RULING-T5A1-1 exempt-unit rule).
Temperature 0.0; token budget 1600 (design §11); the truncation
finish-reason guard applies as to every v3 call. Shared attribution markers and
the F-4 banned classes are unchanged — **except** the PM-specific
attribution-marker need surfaced in §6.1.

---

## 1. The PM synthesis prompt

### 1.1 Role block (verbatim)

```text
You are the desk head reviewing the team's finished work: the accepted analyst
sections, the deterministic findings and their figures, the evidence-gap
inventory, and the auditor's flags. Your synthesis is the reading a careful
desk head gives that evidence — which parts carry the most weight for reading
this report, where the sections pull against each other, what a reviewer should
re-check first, and how much trust the inputs can bear. You judge the evidence;
you never judge the trade. You reach no conclusion about whether to act, and you
resolve no tension into a direction.

You work only from what the team surfaced. Every section you weigh, every figure
you cite, and every tension you name must already be present in the accepted
sections, the deterministic findings, or a calculation you request to re-verify
a figure the team already reported. You may re-run a portfolio calculation to
confirm a number before you lean on it, but a re-run only confirms a figure the
report already carries; it never adds a figure the team did not surface, and you
never introduce a fact, a number, or a source that no section grounded.

Return your synthesis as the four required fields, each doing only its own job.
Evidence weighting: which parts of the saved evidence matter most for reading
this report and why, judged on freshness, coverage, and how much of the report
leans on each input — about the evidence, never about the trade. Evidence
tensions: the places where the sections or findings pull in different directions
or rest on different vintages of data, each named and left unresolved, with what
would resolve it — describing the tension, never picking a side. Verification
priorities: what the reviewer should check before relying on this report, each a
plain verification instruction and nothing else. Trust assessment: how much
weight the inputs can bear and which caveats dominate that judgment — the
trustworthiness of the saved evidence, never the likelihood of any outcome.

Attribute every interpretation to the section or finding it came from — name the
section, for example "the technical section", "the risk section", or "the
deterministic findings", whenever you carry its reading forward, so that no
interpretation reads as a new claim of your own. Two judgments are never yours:
whether the trade is a good idea, and what the reviewer should do about it. Weigh
the evidence, name the tensions, order the checks, and state the trust; leave
every should-I-act question, and every resolution of a tension into a direction,
to the reviewer.
```

### 1.2 SHAPE-PM (verbatim)

```text
Return one strict JSON object and nothing else — no prose before or after it, no
markdown, no code fence. The object has exactly these four keys and no others:
    "evidence_weighting": a string of three to six sentences.
    "evidence_tensions": a list of zero to three strings, each one or two
        sentences; use an empty list when the evidence is consistent.
    "verification_priorities": a list of two to five strings, ordered most
        important first, each one plain imperative sentence that uses only
        verification wording (verify, check, confirm, review, re-sync, compare).
    "trust_assessment": a string of two to four sentences.
Every number in any field must already appear in an accepted section, in the
deterministic findings, or in a calculation result returned to you in this run.
Use no nested objects, no extra keys, and no markdown list or heading syntax
inside any string.
```

---

## 2. The typed `PmSynthesis` contract — why each field is verdict-incapable

The claim to defend is stronger than "the prompt steers away from a verdict."
The claim is: **the output contract has no verdict-bearing slot, and every slot's
gate rejects verdict content whole-block.** I make that claim honestly — two
fields are structurally verdict-incapable by their admitted grammar/contract;
two are freeform prose whose guarantee is gate-enforcement plus whole-block drop,
not schema shape. Distinguishing them is the point: overclaiming schema-magic on
the freeform fields would hide where the real enforcement lives.

| Field | Type | Why a buy/sell/hold/rating/suitability verdict cannot survive here |
| --- | --- | --- |
| `verification_priorities` | `list[str]`, 2–5, ordered | **Structural (closed vocabulary).** Each item must begin with a whitelisted verification imperative — the closed set {verify, check, confirm, review, re-sync, compare} (F-2, list unchanged). A recommendation is an imperative too ("reduce the position", "buy"), but its verb is not in the whitelist, so the item fails F-2 → whole-block drop. This field uses the exact grammar a recommendation would use, and the whitelist is precisely what separates "re-sync the broker snapshot" from "trim the position." There is no admitted phrasing of an action recommendation. |
| `evidence_tensions` | `list[str]`, 0–3 | **Structural (contract forbids resolution).** The field's semantic contract is *named tension, left unresolved*. A verdict is a resolution; the tension-resolution drop (F-4 + the mandatory §7 eval) fails any item that resolves a tension into a directional takeaway ("…so weight the technical view"). The field cannot hold a concluded direction by contract. |
| `evidence_weighting` | `str`, 3–6 sentences | **Enforced ONLY once §4a is built — not schema-structural, and not covered by today's gates.** Freeform prose — a model *could* type "buy" or the softer "the trade holds up well". The existing F-4 five classes catch hard rating words, but Claude G verified there is **no** subject-noun/directional-lean pattern today, so a soft verdict here would survive. The guarantee is real only after the §4a PM-specific F-4 pattern lands; the §7 families are its falsification test. |
| `trust_assessment` | `str`, 2–4 sentences | **Enforced with a helpful anchor, but same §4a dependency.** Its semantic anchor — "how much weight the **inputs** can bear" — aligns with `_F4_SUITABILITY_RE` being anchored to trade/position/portfolio/risk nouns (compat §6.2.3), so "the inputs can bear little weight" passes and "the position size is reasonable" drops **today**. But a directional trust-verdict ("the evidence points the right way") needs §4a to drop. Guarantee is gate + whole-block drop, contingent on §4a. |

**The structural core, stated once (corrected per Claude G):** none of the four
field *jobs* is "conclude what to do" — the jobs are weigh-evidence,
name-tensions, order-checks, assess-trust. The schema has no recommendation
field. A verdict smuggled into `verification_priorities` fails the closed
whitelist **today**, and into `evidence_tensions` reads as a banned resolution
**today**. But smuggled into either freeform field it survives **today** — the
subject-noun/directional-lean gate I cited above does not exist yet. So the
no-verdict guarantee is real for two fields now and for all four **only once §4a
lands**. My original §2 overstated the freeform fields as already-enforced; that
was the gap Claude G caught, and §4a + the §7 acceptance test close it.

---

## 3. Whole-block fail-closed

- The synthesis is all-or-nothing. `F-1` parses fail-closed: JSON parse → exactly
  the four keys, correct types → per-field bounds (§1.2) → each
  `verification_priorities` item opens with a whitelisted imperative (F-2) →
  the concatenated field text runs F-4, F-5, F-6, F-11 with the PM allowed sets
  (§4, §5). **Any** failure drops the entire block; there is no field-level
  salvage and hard blocks are never re-passed (design §9.5).
- The flip is the existing enum: `final_synthesis_authored_by`
  (`Literal["portfolio_manager_agent", "deterministic_template"]`,
  `reports.py:86`). Accepted synthesis → `portfolio_manager_agent` and the
  composer appends the attributed block (§9.4 shape). Any drop/failure →
  `deterministic_template`, and the composer renders **only** the deterministic
  `## Summary` headline + paragraph floor. No partial render, no half-populated
  synthesis block.
- Fallback lines (design §9.5, verbatim): gate drop —
  "A live Portfolio Manager synthesis was generated for this report but did not
  pass its safety checks and was omitted. The summary above is deterministic.";
  call failure / timeout / unparseable —
  "A live Portfolio Manager synthesis was not available for this run. The summary
  above is deterministic."
- The PM never runs in blocked / deterministic-draft states, and analyst
  failures never block the PM — it synthesizes over what survived (minimum:
  findings + gaps), and if nothing usable survives it falls to the deterministic
  floor.

---

## 4. Gate mechanics over the PM surface (F-1..F-13)

- **F-1 / F-2 / F-3 (own the structure; F-8/F-9 do NOT apply to the PM).** The PM
  is typed JSON, not a heading/table section, so the analyst F-8 heading/word/
  table contract and the F-9 "What was verified" subsection **do not apply**. F-1
  (typed shape + bounds) replaces F-8; the verification content that F-9 checks on
  analysts lives here in `verification_priorities` + `trust_assessment`, gated by
  F-2 and F-4, not by a subsection check. F-3: the composer renders the numbered/
  bulleted list structure from the typed items, so the list markup never comes
  from the model — a `-` or `#` inside a typed item is an F-1 structure failure
  (this also keeps `INVENTED_LEVEL_PATTERNS` / display-token scanners from
  false-tripping on a model-authored "1." level).
- **F-4 advice-boundary — review crux (a); see §4a for the required new pattern.**
  The five shared classes bind on the concatenated field text and catch hard
  rating words anywhere. They are **not sufficient** for the PM: Claude G
  verified F-4 has no `reduce/cut/lighten/pare/increase` and P35 has only
  `add/trim/rebalance/buy/sell/hold/wait/spread`, so a soft or indirect verdict
  in a freeform field ("the trade holds up well") survives today. §4a specifies
  the PM-specific pattern that closes this. The tension-resolution drop fails any
  `evidence_tensions` item that picks a direction.

### 4a. The PM-specific F-4 pattern (BINDING — Codex C implements; not verb whack-a-mole)

Two subject-anchored mechanisms, applied only on the PM surface, each firing a
whole-block drop. Neither enumerates action verbs — that is deliberate (a
`reduce|cut|lighten|pare` list is evadable by paraphrase and is exactly the
whack-a-mole Claude G rejected):

1. **Trade-subject frame.** A sentence/clause whose subject is a trade noun
   `{trade, position, setup, entry, idea, purchase, sale, order}` immediately
   followed by a copula or linking verb (`is/are/was/were/looks/seems/appears/
   holds/holds up/makes/works/stands/remains/checks out`) drops — regardless of
   the complement. This catches "the trade **is** attractive", "the setup
   **looks** solid", "the position **holds up** well", "the idea **makes** sense"
   without listing any of those adjectives. The PM has no legitimate
   trade-subject declarative (charter §9.1: every PM sentence is about the
   evidence); the only trade-directed sentences allowed are verification
   imperatives, which have no subject noun and are unaffected.
2. **Directional-lean predicate, subject-independent.** A lean can wear an
   *evidence* subject ("the evidence points the right way"), so the trade-subject
   frame alone is not enough. A second pattern catches directional/endorsement
   predicates regardless of subject: `points (the )?(right|wrong) way`,
   `favors (buying|selling|the purchase|the sale|acting|the trade)`,
   `leans (bullish|bearish|toward|for|against)`, `tilts (the balance|toward)`,
   `the (right|wrong|smart|safe) (move|call|decision|play)`,
   `supports (buying|selling|the purchase|acting|the trade)`,
   `(argues|makes the case) for`. This is a **living reviewed constant**, not a
   closed claim to completeness — §7 grows it, and human prompt-review + the
   complete-report eval score are the backstop (the Q-R6 principle: role
   emphasis lives in evals, the gate carries the falsifiable core).

Both patterns are PM-surface-only (they must not fire on analyst sections, which
legitimately discuss "the position's exposure" as an evidence subject — note the
frame requires the trade noun in **subject** position adjacent to a linking verb,
so "the position's exposure figure is stale" — head noun "figure" — does not
match). Acceptance test (Claude G): every §7.1/§7.3 canon canary drops from
`evidence_weighting` and `trust_assessment`, not only from
`verification_priorities`.
- **F-5 provenance.** Every numeral in the field text matches the PM allowed
  numeric set = {values in the accepted analyst sections} ∪ {deterministic
  finding values}. Note deliberately excluded: independent PM-calc-result values
  (see §5 — verify-not-recompute). Same normalized-match rules as the analysts.
- **F-6 identifier privacy.** Unchanged scan; the PM receives no raw identifiers
  (Tier 1 — §9.2 excludes them), so the scan is a backstop, applied identically.
- **F-11 grounding — review crux (b).** The PM received-refs = the accepted
  sections' refs + deterministic-finding refs + the PM's own frozen
  verification-calc refs. A section, category, or fact not in that set is
  ungrounded → whole-block drop. The structural consequence: the PM **cannot
  introduce a fact no analyst grounded** — it re-weights, tensions, and
  verification-orders what the team surfaced; it originates nothing. The relocated
  filing-contents patterns (`_F11_UNGROUNDED_RE`) apply here too.
- **F-10 budgets + PM calc-request validation.** PM loop budget 2 LLM / 6 tool
  (design §2, §11); wall-clock + token ceilings as the analysts; the PM
  calc-request validator (Codex C, analogous to `_validate_p36_public_calc_request`)
  enforces the verify-not-recompute constraint in §5.
- **F-12 legacy prose scan.** The rendered PM block is `final_synthesis_markdown`
  ∈ `REPORT_PROSE_KEYS`, so the document-level P35 advice/evaluative scan covers
  it (the T5A-2 F-12 narrowing keeps generated PM prose fully scanned). The
  yield/annualized document-scan treatment therefore reaches PM prose too (§6.2).
- **F-13 freeze/readback.** The four `PmSynthesis` fields freeze additively under
  `p36-pm-synthesis-v1`; readback re-runs F-1/F-4/F-5/F-6/F-11 over the frozen
  fields with **no** provider or tool re-run (PM verification calcs happen at
  generation time only), version-keyed, no mixed application.

---

## 5. PM calc-verification access (portfolio_role, verify-not-recompute)

- **The PM is `portfolio_manager_agent`, a portfolio role**, so it may receive
  agent-safe content and request the C1–C5 portfolio calculations. C1–C5 are
  `agent_safe` — they are absent from `_PUBLIC_CALC_TOOL_NAMES`
  (`calculations.py:33`, which lists only C6–C15), so `evidence_tier` resolves to
  `agent_safe` for them (`calculations.py:1036`). The T5A-2 public calc validator
  admits no C1–C5 id in any public role's map and re-checks `entry.allows_role()`;
  **that barring is unchanged** — this design adds no path from a public analyst
  to C1–C5.
- **Verify-not-recompute is a structural F-5 property, not a steering hope.** The
  PM allowed numeric set (§4, F-5) is the analyst-surfaced + deterministic-finding
  values **only**; PM calc results are **not** admitted to F-5 as an independent
  source. So a PM re-run's role is to let the model *confirm* a figure before
  leaning on it — when the re-run reproduces a surfaced figure, that value is
  already citeable (via the analyst that surfaced it); when a re-run **diverges**,
  its value is not in the allowed set and any attempt to emit it fails F-5 →
  whole-block drop. The PM therefore **cannot emit a C1–C5 value the analysts did
  not surface.** A divergence is reportable only as a verification imperative
  ("re-check the exposure figure — a re-verification did not reproduce the risk
  section's value"), never as a new number.
- **CONFIRMED (Claude G, 2026-07-13):** the F-5 rule that PM-calc-result values
  are admitted only by match to an already-surfaced value (verify), not as an
  independent numeric source (recompute) — "correct and elegant." The alternative
  (admitting PM calc values independently) would let the PM originate figures and
  is rejected.

---

## 6. New gate/prompt collisions the PM prose surfaces

### 6.1 RULING NEEDED — F-4.6 attribution markers do not cover section-attribution

**Collision.** The F-4.6 attribution requirement drops any sentence containing an
interpretation trigger (downtrend, concentration, drawdown, easing, trend,
conventional, …) that lacks a `P36_ATTRIBUTION_MARKERS` substring. That marker set
— `"the saved"`, `"per this run's"`, `"computed from"`, `"calculation"`,
`"the freshness inventory"`, `"in conventional"` — was built for **analysts
attributing to calculations and saved evidence**. The PM's job is to attribute to
**sections**: "the technical section describes an established downtrend",
"the risk section reports rising concentration". Those sentences carry an
interpretation trigger ("downtrend", "concentration") but **no analyst marker**,
so the F-4.6 gate would false-drop the PM's core, correctly-attributed synthesis
sentences to the deterministic floor.

**Recommended resolution — Option 1: a governed PM-specific marker superset.**
Add `P36_PM_ATTRIBUTION_MARKERS` = `P36_ATTRIBUTION_MARKERS` ∪ section-attribution
phrases (`"section"`, `"the deterministic findings"`, `"the analysts"`,
`"per the"`), a reviewed governed constant applied **only** on the PM surface;
the analyst marker set is unchanged. This is not mere leniency — it turns F-4.6
into a *section-attribution requirement* for the PM (a trigger sentence must name
its source section), which **reinforces** the no-original-interpretation boundary:
the PM must say "the technical section shows a downtrend", never a bare "there is
a downtrend." Rejected alternatives: (a) widen the shared analyst constant —
leaks PM leniency onto analyst enforcement; (b) drop F-4.6 on the PM — removes a
check from the highest-stakes surface and loses the section-attribution
discipline. This is a gate-mechanic change on a safety surface → **Claude G's
call.**

**RULING-T5B-1 (Claude G, 2026-07-13): APPROVED.** Governed PM-only
`P36_PM_ATTRIBUTION_MARKERS` superset, analyst set unchanged, PM-surface-only.
It reinforces (not loosens) the boundary — the F-4.6 markers gate *attribution*
only, never the advice classes (§4a) or F-11. Condition: the §7.7 with/without-
marker probe is mandatory.

### 6.2 Inherited, already-ruled — no new ruling

- **yield / annualized document scan.** PM prose is `final_synthesis_markdown`
  ∈ `REPORT_PROSE_KEYS`, so if the PM carries forward a News FRED-series name
  ("…the 10-year Treasury yield…") or a method characterization it hits the same
  `report_output_safety.py:207` scan as News. This is **covered by RULING-T5A2-1**
  (the FRED display-string scrub is document-level and already reaches PM prose)
  and by the F-12 method-metadata separation. No new ruling — but the RULING-T5A2-1
  pre-activation label audit must include the PM surface in scope (it already is,
  being document-level).
- **F-5 PM-calc admission (§5)** — a confirm, not a collision, routed above.

### 6.3 RULING-T5B-2 — PM accepted-section dynamic-scan collision (Claude E specifies; Claude G ratifies)

**Collision.** T5B feeds the PM the accepted analyst sections verbatim (§9.2).
The accepted Risk section legitimately contains bare topic words — "portfolio",
"exposure", "cash", "holdings", "positions", "account" — that the
dynamic-message forbidden-string scan (`find_forbidden_string_values` /
`_find_forbidden_string_values_segmentwise`) flags before the PM request is
built. RULING-T5A1-1 deliberately kept user/envelope/dynamic segments strict,
so Codex C correctly held for a ruling rather than widen that boundary.

**Decision (Claude E): Option A, sharpened.** Approve a narrowly-scoped
accepted-section projection for the `p36-pm-synthesis-v1` PM evidence payload
that relaxes **only** the bare-plain-topic-token flag, for exactly the governed
F-6 vocabulary-only set, retaining every other scan.

- **Trust basis (why A is safe, not a general loosening).** The PM receives no
  external free-text. Its payload is runner-assembled entirely from
  already-validated internal material: accepted analyst sections (each already
  passed F-5/F-6/F-4/F-8/F-9/F-11 before acceptance — a section that failed was
  dropped and is never projected), deterministic findings, the gap inventory,
  and the deterministic trade-intent. The only tokens tripping the strict scan
  are the bare F-6 vocabulary-only words F-6 already cleared on that exact text.
- **Relaxed:** ONLY the bare-plain-topic-token flag, ONLY for a governed
  constant `P36_F6_VOCABULARY_ONLY_TOKENS = {account, holdings, cash, positions,
  portfolio, exposure, nickname}` — the single governed source for the PM
  projection relaxation (append-only; exact-7-members guard test; Claude E +
  Claude G governed).
- **F-6 import is behavior-preserving ONLY (BINDING, Claude G 2026-07-13).**
  Correction to my earlier "imported by both" framing: F-6 has **no** bare-word
  allowlist today — it passes all 7 words *implicitly* while blocking
  `account 48213` and `cash_balance`/`account_id`, and "account" is *also* in
  `_IDENTIFIER_CONTEXT_RE` (the ambiguous-proximity trigger). So the constant
  may **name/centralize** what F-6 already passes, but must NOT become a new F-6
  allowlist gate, must NOT remove any word from `_IDENTIFIER_CONTEXT_RE`, and
  must NOT short-circuit the ambiguous-proximity branch. **Mandatory F-6 parity
  canary:** with the constant in place, `the account 48213 was reviewed` STILL
  returns `identifier_privacy_blocked`, and each vocab word adjacent to a
  ≥5-digit number STILL flags. **If importing the constant changes ANY F-6
  decision on the Risk or three public surfaces, the F-6-import half is rejected
  for T5B — ship the exemption on the PM projection alone**, with the constant
  living solely as the PM-projection SSOT.
- **Retained, unconditional (every actual-leak mechanism):** forbidden-key
  scan; compound-token scan (`cash_balance`, `account_id`, `raw_balance`,
  `buying_power`, `raw_holdings`, `raw_positions`, `tax_lot`, `raw_payload`,
  provider/broker ids); identifier scan (account-number, masked, UUID,
  provider-id); secret-like scan; source-leak / path / raw-payload scan; and the
  prohibited-phrase scan. A bare "cash" passes; `cash_balance` and `account_id`
  still fail closed. **Blast radius = 7 bare English words**, none of which
  carries a private value — identical safety logic to the F-6 three-outcome
  vocabulary-only pass.
- **Scope:** structurally the `p36-pm-synthesis-v1` PM evidence payload only.
  Public-role and all other dynamic/user/envelope segments stay strict
  (RULING-T5A1-1 unchanged for them). The relaxation does not generalize.

**Why not B/C.** B (deterministic non-prose projection) guts the PM's design
contract — it must synthesize over the sections' verbatim prose to name tensions
("the technical section describes a downtrend while fundamentals shows a
one-quarter-old record"); reducing sections to labels contradicts §9.2 and
degrades the surface to a label-shuffler. C collapses into A for any variant
that still passes the required prose. A is the minimal principled relaxation.

**Authority. RATIFIED (Claude G, 2026-07-13)** — with the behavior-preserving
F-6-import binding condition above. Claude E specifies, Claude G ratifies, per
the established governance for safety-scanner changes.

**RULING-T5B-3 (Claude G, 2026-07-14):** the predicate-severing wrap
`"The filing is\nmaterial."` is a tolerated, canary-locked residual rather than
approved output; a future normalize-per-field pass may tighten it without
changing the accepted-output contract, while wrapped nominal materiality remains
blocked.

**Required tests:** accepted Risk section reaches the PM; `cash_balance` /
`account_id` / other compound tokens, identifiers, secrets, paths, and raw
payloads still fail closed in the PM payload; the relaxation does not apply
outside the `p36-pm-synthesis-v1` evidence payload; public-role dynamic messages
remain strict; **F-6 parity canary** — `the account 48213 was reviewed` still
flags `identifier_privacy_blocked`, and each vocab word adjacent to a ≥5-digit
number still flags, with F-6 decisions unchanged on Risk + the three public
surfaces; **exact-7-members guard** on `P36_F6_VOCABULARY_ONLY_TOKENS`; PM
readback reruns neither tools nor provider.

---

## 7. T5B eval families (synthetic only; extends compat §13.3)

The **no-verdict minimal pairs are mandatory and this is a LIVING set** (Claude G
condition): it grows as new soft/indirect verdict shapes are found, and §4a's
directional-lean constant grows with it. A synthesis that concludes a
recommendation — hard *or soft* — must drop to the deterministic template.

1. **No-verdict minimal pairs (MANDATORY, freeform-field acceptance test).**
   evidence-subject PASS ("the technical section carries the most weight because
   it is the freshest input") vs FAIL for each verdict shape, placed **inside
   `evidence_weighting` and `trust_assessment`** (not only
   `verification_priorities`): hard — "buy" / "the trade is attractive" /
   "reduce the position" / "this is a good entry"; **soft/indirect (the ones
   that survive today)** — "the trade holds up well" / "the setup looks solid" /
   "the evidence points the right way" / "the idea makes sense" / "on balance the
   position stands up". Every one drops whole-block with
   `final_synthesis_authored_by == deterministic_template` and the §9.5 gate-drop
   line rendered. **This is the Claude G acceptance test: the soft cases must
   drop from the freeform fields, proving §4a is real, not §2 hand-wave.**
2. **Tension-resolution failure (MANDATORY):** `evidence_tensions` item that
   resolves into a lean ("…the tension favors the downtrend — weight the technical
   view" FAIL) vs named-and-left-open ("…the tension is about recency and is
   unresolved; re-syncing would resolve it" PASS).
3. **`verification_priorities` whitelist:** "re-sync the broker snapshot" PASS vs
   "reduce the position by half" FAIL (F-2 closed vocabulary; the second is both
   a non-verification verb and a sizing verdict).
4. **`trust_assessment` suitability probe:** "the inputs can bear little weight"
   PASS vs "the position size is reasonable given the inputs" FAIL (compat §13.3).
5. **F-1 structured-shape probes:** 5 fields / wrong types / 4 tensions / a
   markdown `-` or `#` inside an item / non-JSON — all whole-block FAIL with the
   §9.5 fallback rendered; sentence-count under/over bounds FAIL.
6. **F-11 grounding / verify-not-recompute (per §5):** PM cites a section no
   analyst produced FAIL; PM emits a number absent from every accepted section and
   the findings FAIL; a PM re-run value that matches a surfaced figure PASS, a
   divergent re-run value emitted as a figure FAIL, and the divergence expressed
   only as a verification imperative PASS.
7. **PM section-attribution probe (per §6.1):** an interpretation-trigger sentence
   **with** a section-attribution marker PASS vs the same sentence **without** one
   FAIL (locks the F-4.6 PM-marker mechanic once §6.1 is ruled).
8. **Readback/versioning (F-13):** a frozen `p36-pm-synthesis-v1` block
   re-validates under the v3 PM gates with no re-run; a pre-v3 package renders the
   deterministic floor.

Scoring at complete-report level per P35-R1; canaries offline only.

---

## 8. Disposition (Claude G, 2026-07-13)

**PASS with one binding condition.** Confirmed: §1 block + SHAPE-PM; §4
F-1-replaces-F-8/F-9 and F-11 originates-nothing; §5 verify-not-recompute
(match-only F-5 admission). **RULING-T5B-1 (§6.1) APPROVED.**

**BINDING CONDITION (before T5B is accepted):** §2's freeform-field
verdict-incapability rested on a subject-noun test that is not implemented; a
soft verdict ("the trade holds up well") drops from `verification_priorities`
(F-2) but survives in `evidence_weighting` / `trust_assessment` today. §4a now
specifies the real PM-specific F-4 pattern (subject-noun frame +
subject-independent directional-lean set, not verb whack-a-mole); §7.1 is the
living mandatory acceptance test — the soft/indirect canaries must actually drop
from the freeform fields. §2 is corrected to stop claiming the test pre-existed.

**Doc-parity (Claude G):** this design AND the still-uncommitted
`PHASE_36_T5A2_PUBLIC_ROLE_BLOCKS.md` commit **with** the T5B implementation
(design travels with its code — the T5A1 precedent). Codex C's action; not an
auto-commit.

**Next step:** Codex C implements T5B (the PM loop, typed F-1 parse, PM calc
validator, §4a advice gate + §6.1 PM markers, composer append, freeze/readback)
with the binding condition folded in, reviewers Claude E (gate/eval) + Claude G
(architecture/safety). **T6 stays frozen** until the PM surface is accepted and
the founder gives the five-live-role go-ahead.
```
