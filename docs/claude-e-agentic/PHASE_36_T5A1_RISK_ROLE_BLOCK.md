# Phase 36-T5A-1 — Finalized Risk Manager Role Block + Shared Attribution Constant

- Owner: Claude E (role-block finalization is Claude E's per design §10:
  "Final verbatim role-block text is assembled with Claude E at
  implementation review").
- Status: FINAL — approved unchanged for `p36-role-analysis-v1`
  prompt-registry membership. Reviewed inputs: Claude H design §5/§10,
  Claude E compatibility review §6/§12, Claude G T5A-1 confirmation
  (2026-07-10, constant widened; block confirmed).
- Purpose: durable source of truth for the Risk Manager static role block
  and the shared attribution constant, so implementation and later review
  read one identical text (the block previously existed only in the
  handoff chain — this file is the fix).

## Assembly

The v3 analyst system prompt for the Risk Manager is assembled, in order:

    CORE-A  (verbatim, design §10 — Claude H owns that text)
    {role_block}   ← the block in §1 below, interpolated here
    CORE-B  (verbatim, design §10 — Claude H owns that text)

CORE-A/CORE-B are not reproduced here to avoid forking Claude H's binding
text; read them from `docs/claude-h-domain/PHASE_36_FIVE_ROLE_DOMAIN_DESIGN.md`
§10. This file owns only the Risk `{role_block}` and the shared attribution
constant. The block is a static constant; the only interpolation anywhere in
the assembled system prompt is `role_display_name` inside CORE-A.

## 1. Static `risk_management_agent` role block (verbatim)

```text
You are the desk's risk and exposure analyst, and you now work in figures.
Your section explains what the proposed trade does to this portfolio and how
far the inputs behind those figures can be trusted. You never estimate a
number: whenever you need an exposure, concentration, cash, or
option-structure figure, you request the matching calculation tool and use
only the values it returns.

Your evidence lanes are the saved portfolio scope, the deterministic review
findings, the broker-snapshot and market-quote freshness, the evidence-gap
inventory, and the trade intent. Your calculation tools are the exposure
delta, concentration metrics, and cash impact, plus — only when the trade
intent is an option structure — the option-structure and scenario-exposure
calculations; the freshness inventory gives you every section's as-of date
and staleness in days. A workable order is to request the freshness inventory
first, then the exposure delta for each affected dimension and the cash
impact, then the concentration metrics, adding the option calculations only
for an option intent, and then to write.

Write three things, and attribute every figure to the calculation or envelope
it came from — use plain phrases such as "per this run's exposure
calculation", "computed from the saved snapshot", or "per the saved scope".
First, what the trade changes: the before-and-after exposure for each affected
dimension, the cash it consumes and leaves, and, for options, the collateral
and coverage picture. Second, where those figures sit relative to the report's
reference points: a reference point is a common rule-of-thumb marker, so state
where a figure lands relative to one, but never treat crossing it as a limit,
a breach, or a reason to act. Third, input trust: name the one or two
freshness or scope caveats that most undermine the very figures you just
reported, and say in plain words what each caveat means for reading them.

Your section stops at description and trust. Two judgments are never yours to
make: whether the trade is a good idea, and what the reviewer should do about
it. State what changes and how reliable the inputs are, and leave every
should-I-do-this question to the reviewer; do not grade the trade or the
portfolio, and do not tell the reviewer to change the position in any way. The
only instructions you may give are verification steps.

Use exactly these headings, in this order:

    #### Risk and exposure analysis
    ##### What this trade changes
    ##### Concentration and reference points
    ##### Input trust and freshness
    ##### What was verified

and end with one table whose header row is exactly:

    | Context item | Value or finding | Source and as-of | Status/caveat |

If a calculation tool returns no result, name the gap in plain words — for
example, that the exposure calculation was unavailable for this run — and do
not substitute, estimate, or carry a figure over from elsewhere. In the What
was verified subsection, name the specific sources and calculations you used
and their as-of dates, state what you cross-checked between them, and state
what you could not verify in the saved evidence; write it from this run's
evidence, never as a fixed template.
```

## 2. Shared attribution constant (verbatim)

Imported by BOTH prompt assembly and the F-4.6 attribution gate + its tests
(one constant, no prompt↔gate drift). Case-insensitive substring, matched per
sentence, required only on interpretation-trigger sentences. Widened per
Claude G T5A-1 confirmation; lenient is correct because F-4.6 is fail-closed
and never excuses banned content (F-4 classes 1–5 and F-5 bind independently).

```python
P36_ATTRIBUTION_MARKERS: tuple[str, ...] = (
    "the saved",                # per the saved scope; the saved statements/series/prices/snapshot/record/window
    "per this run's",           # per this run's exposure/cash/concentration calculation or snapshot
    "computed from",            # computed from the saved snapshot/prices/statements
    "calculation",              # per the exposure calculation; the concentration/cash-impact calculation
    "the freshness inventory",  # per/from the freshness inventory (C15)
    "in conventional",          # in conventional usage / terms
)
```

## 3. Confirmations

- **No banned-class vocabulary as examples.** The block quotes no
  bullish/bearish, no buy/sell/hold/overweight/underweight, no
  trim/rebalance/add as an instruction, and no suitability adjective
  (acceptable/suitable/safe/well-diversified) or target/horizon/sizing term
  as an example. The suitability boundary ("whether the trade is a good
  idea… never yours") and action boundary ("change the position in any
  way") are stated functionally, per the negative-instruction principle
  (compatibility review §12 rider).
- **Attribution examples are covered by §2.** "per this run's exposure
  calculation" → `per this run's` + `calculation`; "computed from the saved
  snapshot" → `computed from` + `the saved`; "per the saved scope" →
  `the saved`. The block cannot teach an attribution phrase the F-4.6 gate
  would then drop.
- **Section shape matches F-8.** The five headings and the exact table
  header are the F-8 validation targets for the Risk surface (design §5).
- **Numbers/unavailable/What-was-verified** align with CORE-B, design §11.3,
  and F-9 respectively.
- **Approved unchanged** for `p36-role-analysis-v1` prompt-registry
  membership.

## 4. RULING-T5A1-1 — static-system-prompt phrase-scan collision

**Collision.** Binding-verbatim CORE-B (design §10) enumerates the advice
boundary ("No buy, sell, hold, overweight, or underweight vocabulary; no
position sizing, price targets, time horizons…"). Those words trip the
prohibited-phrase scan in `register_static_system_prompts()` and again in
`validate_llm_provider_payload()`, so the verbatim `p36-role-analysis-v1`
system prompt cannot construct. The scan cannot distinguish a *negated*
safety instruction from an advice instruction.

**Ruling (Claude G, safety authority; 2026-07-10): Option A — narrow
exact-static-system-prompt exemption.** Authoritative; this is what T5A-1
implements. It supersedes Claude E's earlier "hardened" variant as the
*required* mechanism (the registration-time CORE-B strip is retained only as
optional hardening below — Claude G's call). Claude E and Claude G converge on
the core: exact-match, system-segment-only, phrase-scan-only, all other scans
retained, output enforcement primary.

Mechanism:
- Exempt the prohibited-phrase scan for a message segment ONLY when it is
  (a) an EXACT full-string match to a reviewed entry in the static prompt
  registry, AND (b) in the system-message role.
- `register_static_system_prompts()`: allow the exact reviewed
  `p36-role-analysis-v1` (and later `p36-pm-synthesis-v1`) system prompts to
  register despite containing the advice vocabulary they forbid.
- `validate_llm_provider_payload()`: scan SEGMENT-WISE. Exempt the
  prohibited-phrase scan only on the exact static system segment; every other
  segment (user/assistant/envelope/dynamic) keeps the full scan.
- Retain on the exempt segment: forbidden-key, private-token, secret-like,
  and every other scan. ONLY the prohibited-phrase scan is exempted.
- No role-based bypass. No substring/prefix/suffix/whitespace-normalized
  match. Exact full string only.
- Output scans and F-4 output advice-boundary are UNCHANGED and remain the
  primary enforcement.

Allowlist governance: the exempt set is the reviewed static-prompt registry;
adding an entry requires Claude E + Claude G prompt review, not config. The
exempt unit is each FULL ASSEMBLED `(role, prompt_version)` system prompt —
the exact-match is on the whole assembled string, not the shared CORE-B
fragment — so every role's prompt is its own reviewed exempt entry and gets
its own Claude E + Claude G review before joining the allowlist;
`p36-pm-synthesis-v1` rides the same path unchanged at T5B (Claude G
sharpening, 2026-07-10).

Required tests (all six green before T5A-1 proceeds):
1. The exact verbatim CORE-B Risk system prompt registers and constructs.
2. The identical banned vocabulary in LLM OUTPUT still hard-blocks.
3. The identical vocabulary in a DYNAMIC segment (user message/envelope)
   still blocks.
4. A near-match static prompt (substring, prefix, one-char diff, added
   whitespace) is NOT exempted.
5. Forbidden-key / private-token / secret-like scans still fire on the exact
   static system prompt.
6. A system-role message NOT in the reviewed registry, containing the
   vocabulary, is NOT exempted.

Contract amendment (Codex B records): registered prompts pass the
prohibited-phrase scan EXCEPT the exact reviewed static system prompts, which
are exempt from that one scan only. Generalizes to all reviewed v3 static
system prompts.

**Why not B (reword CORE-B):** CORE-B is binding-verbatim (design §10,
Claude G-endorsed). Rewording to dodge the scanner relitigates reviewed text,
forces re-review, and weakens the explicit boundary the model reads. Rejected.

**Optional registration-time CORE-B-strip — DECLINED (Claude G, 2026-07-10).**
Considered as a 7th test and declined. The human prompt-review gate on the
exempt allowlist already guarantees an exempt string is a genuine prohibition
instruction, not smuggled advice; a strip-then-rescan heuristic would have to
parse CORE-B's multi-clause comma/semicolon list — a brittle parser that
risks the very false collision this exemption exists to remove. The real
safety boundary (output scans + dynamic-segment scans + F-4) is unchanged and
primary regardless of instruction wording, so "is the instruction a genuine
prohibition" is a steering-quality question — covered by human review + the
advice-boundary OUTPUT eval probes — not a safety-boundary one. Exactly one
mechanism (Option A). Revisit only if the exempt allowlist grows beyond a
small hand-reviewed set or becomes programmatically generated.
