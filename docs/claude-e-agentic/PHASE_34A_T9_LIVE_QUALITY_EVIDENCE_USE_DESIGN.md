# Phase 34A-T9 — Current-Runner Live Agent Team Quality and Evidence-Use Design

Status: design-only (no implementation).
Owner: Claude E. Reviewer: Codex B. Stop for Codex B review before implementation.
Scope: the existing app-owned tool-mediated runner only. LangGraph deferred.
No new sources, no news providers, no market-data expansion, no frontend, no
MCP/web/TradingAgents, no direct LLM tool calls. Deterministic backend keeps
ownership of all numbers and citations.

Locked product question (unchanged): **"What would I be ignoring if I acted
manually now?"**

Grounding: `backend/app/services/agent_team/tool_mediated_report.py`,
`tools.py`, `report_output_safety.py`, `roles.py`, `prompts.py` (legacy P19
path), eval harness at
`backend/tests/services/agent_eval/test_tool_mediated_eval.py`, and the
P34A-T2/T6B design decisions.

---

## 1. Current live quality assessment — why reports feel shallow

The safety architecture is right; the *information yield* is capped by four
code-level choices, all fixable inside the current runner:

1. **One-sentence-per-role collapse.** `_live_provider_role_findings`
   (`tool_mediated_report.py:533`) merges all of a role's deterministic
   findings into a single finding with unioned refs and one prose sentence.
   The Risk Manager deterministically produces up to five distinct findings
   (risk flags, freshness, scope, options mechanics, gaps); live mode fuses
   them into one blob. Structure is the product — this is the single biggest
   quality loss.
2. **Generic deterministic claim texts.** Outside the SEC listing shipped in
   T6C, the deterministic floor is fixed boilerplate: "Reviewed public
   context is background that could be overlooked during manual review"
   (`_public_claim_text`), "Freshness categories should be checked…"
   (`_risk_role_findings`). The claim never names *which* freshness category,
   *which* scope caveat, *which* gap. The T6C SEC listing ("Recent SEC EDGAR
   filings (metadata only): 8-K (2026-06-28)") proves the fix pattern:
   deterministic, fact-key-allowlisted, metadata-only listings are safe and
   immediately more useful.
3. **A one-size-fits-all live prompt.** `_live_provider_request` sends every
   role the same system sentence and the output rule "one concise
   background-context sentence with no numeric metrics." The model sees only
   envelope metadata — which *does* include `availability`, `freshness`, and
   `caveat_codes`, so it could name categories — but nothing in the prompt
   asks it to be specific, so it emits safe filler.
4. **Fixed-template PM synthesis.** `_synthesis_markdown` is one static
   paragraph with three conditional clauses. Two different runs over very
   different evidence read nearly identically, which reads as "the AI didn't
   actually look."

Useful ≠ more data. Within approved evidence, "useful" means: **name the
specific ignorable things** — the stale category, the unevaluated account
feasibility, the 8-K filed last week, the sections never reviewed — instead
of asserting that unspecified context exists.

## 2. Role-by-role target behavior

All roles answer the locked question through their lens; none may rank,
predict, or advise.

| Role | Target contribution ("what you'd be ignoring…") | Primary evidence |
| --- | --- | --- |
| Fundamentals Analyst | Which company-level context was reviewed vs not: profile reviewed/limited, fundamentals snapshot not reviewed; company-event metadata exists but is uncited by this role | `trade_intent_summary`, `public_company_profile`, (`public_fundamentals_snapshot` when present) |
| News Analyst | Event awareness inventory: deterministic SEC filing listing (T6C, unchanged); deterministic FRED release-calendar listing when frozen metadata exists; explicit statement that news content itself is unreviewed | `trade_intent_summary`, `public_events_calendar` (SEC), `economic_awareness_snapshot` (FRED) |
| Technical Analyst | Quote-timing risk: the market-quote freshness *category by name* (fresh/stale/unknown/not_available) and that saved quotes are not live prices | `trade_intent_summary`, `market_quote_freshness` |
| Risk Manager | The specific deterministic flags: freshness categories by name for broker snapshot and quotes; scope caveat codes rendered readably; option-mechanics caveats; **named** gap sections from `evidence_gap_inspector` | all agent_safe sections + gap inspector |
| Portfolio Manager | Compositional synthesis (still deterministic): per-role digest, an explicit "not reviewed / unavailable" inventory, open questions, manual verification checklist, read-only clause | audited findings + gap refs |

## 3. Prompt/prose changes needed

Two layers, in priority order:

**Layer 1 — deterministic specificity (no prompt-boundary change, next
slice).** Extend the reviewed T6C listing pattern:

- Freshness claims name the category: "The saved broker snapshot is
  categorized as stale." / "Market quote freshness is categorized as
  unknown." (category values come from the existing `_freshness_category`
  vocabulary — no numbers).
- Scope claims render caveat codes readably: "Saved scope caveats:
  account-level feasibility not evaluated; scope limited to the selected
  account." (deterministic code→text map; codes remain in `caveat_codes`).
- Gap claims name sections: "Evidence sections not available in the saved
  package: before/after portfolio impact; public fundamentals snapshot;
  market mood snapshot." (from `evidence_gap_inspector` refs, which are
  already-safe section keys; keep the existing `{ref}_unavailable` warning
  codes).
- FRED deterministic listing mirroring SEC (see §5).

**Layer 2 — live prompt v2 (follow-up slice, provider seam).**

- Bump `LIVE_PROMPT_VERSION` to `p34a-tool-mediated-role-v2`.
- Per-role system prompts: role lens + the locked question verbatim + "use
  only the supplied envelope fields; when freshness, availability, or caveat
  codes are present, name them; do not emit generic filler such as 'context
  could be overlooked' without naming what" + the existing prohibitions
  (no metrics, no rankings, no action words, no interpretation of filings or
  macro releases).
- **Per-finding prose** (T2 Q5's preferred shape): the provider returns one
  sentence per deterministic finding (plain numbered lines); the backend
  splits, validates each sentence, and overlays each deterministic finding's
  `claim_text` individually, preserving that finding's own `evidence_refs`
  and `caveat_codes`. Any count mismatch, empty line, or per-sentence
  validation failure → that finding falls back to its deterministic floor
  (whole-role fallback stays for provider-level failure). Deterministic
  backend-authored listings (SEC, FRED) are never live-overwritten
  (extends the existing `_sec_event_finding_stays_deterministic` guard to a
  general "deterministic-listing findings are not overlaid" predicate).
- Note: the legacy `prompts.py` / `BASE_SYSTEM_RULES` path is the P19
  orchestrator, not the tool-mediated seam; changes land in
  `_live_provider_request`, not `prompts.py`.

The live envelope keeps exactly today's fields — `summary_payload`, `scope`,
`as_of` stay stripped. Any future "prompt-fact allowlist" that exposes
selected payload fields to the model is a **separate, Codex B-gated design
task** (candidate P34A-T9C), not assumed here; Layer 1 makes most of its
value unnecessary because specifics enter through deterministic claim text.

## 4. Evidence-use rules by role

Unchanged foundations: citations originate only from ToolResult envelopes;
`audit_findings` filters to received ∩ usable ∩ available;
`ROLE_ALLOWED_EVIDENCE_KEYS` stays the per-role boundary; the SEC role guard
(only `news_analyst` / `portfolio_manager_agent` cite SEC-sourced
`public_events_calendar`) stays. Additions:

- `economic_awareness_snapshot` is already scoped to `news_analyst` + PM in
  `ROLE_ALLOWED_EVIDENCE_KEYS`; add the same *source-specific* guard style as
  SEC so a future allowlist widening cannot silently expand FRED citation.
- `evidence_gap_inspector` remains risk-role-only as a tool; its named gaps
  flow to the PM inventory through the audited risk finding, not through a
  new PM tool call.
- Roles must not restate another role's evidence outside their allowlist —
  already enforced by the auditor; keep as an explicit eval case (§7).

## 5. FRED / SEC handling when frozen evidence exists

- **Existence gate:** both appear only when the frozen package holds
  approved sections (`source_key="sec_edgar_recent_filings"` /
  `source_key="fred_macro_calendar_metadata"`) with available/limited
  availability. No refetch at report time, ever.
- **SEC (unchanged from T6C):** deterministic listing of `form_type` +
  `filing_date` only; `filing_reference` stays opaque/audit-only;
  interpretation/urgency/source-path hard blocks stay; not live-overwritten.
- **FRED (new, mirrors SEC):** deterministic listing of release/calendar
  metadata using a backend fact-key allowlist (release/event name + date
  keys only — mirroring `SEC_RECENT_FILINGS_FACT_KEYS`); e.g. "Upcoming FRED
  macro calendar entries (metadata only): CPI release (2026-07-15);
  Employment Situation (2026-08-07)." If the frozen section holds no safe
  fact keys, keep today's availability sentence. `actual_label`,
  `forecast_label`, `previous_label`, `observation*` remain forbidden keys —
  **no values, no surprises/beats/misses, ever**.
- **Attribution:** existing FRED/SEC attribution + non-endorsement caveats
  keep flowing through backend-owned caveat text
  (`REPORT_ALLOWED_NEGATED_DISCLOSURES` already whitelists them).
- **Live prose:** may restate that filings/releases exist and their timing
  qualitatively ("a recent filing and an upcoming macro release are
  unreviewed context") but never interprets; add a FRED-interpretation hard
  block mirroring `SEC_INTERPRETATION_PATTERNS` (tokens like
  "cpi … suggests/signals", "rate cut/hike", "dovish", "hawkish",
  "inflation … bullish/bearish", "before the release").
- **PM synthesis:** extends the existing SEC event clause with a FRED
  clause: included-as-background vs uncited-context-gap, symmetric wording.

## 6. Failure / degradation behavior

- **Source unavailable (no frozen section / not approved / not_available):**
  the owning role emits a *named* gap sentence — SEC already has one; add
  the FRED twin: "FRED macro calendar metadata was not available or not
  reviewed in the saved evidence." Warning codes:
  `sec_edgar_recent_filings_not_available` (exists) and new
  `fred_economic_awareness_not_available`. Both sections are already in
  `GAPPABLE_SECTIONS`, so the gap inspector and PM inventory pick them up.
- **Never substitute:** no fallback to news providers, web search, or any
  other source; the existing forbidden value tokens already hard-block that
  wording.
- **Provider failure/timeout/unsafe output:** unchanged T2 Q3 behavior —
  fall back to the deterministic finding (now much richer after Layer 1),
  with the existing `live_provider_*` warning codes. Live prose is an
  enhancement layer; degradation must never lose the named specifics, which
  is exactly why specificity belongs in the deterministic floor.
- **Blocked actionability:** unchanged — deterministic draft, no
  `tool_run_artifact`.

## 7. Eval matrix (quality + safety, offline, fake/injected provider)

Extend `backend/tests/services/agent_eval/test_tool_mediated_eval.py`:

**Quality — live must beat the old baseline without becoming advice:**

| ID | Case | Assertion |
| --- | --- | --- |
| Q1 | Stale broker snapshot fixture | Risk summary and PM synthesis contain the word "stale"; category names appear for quote freshness when degraded |
| Q2 | Gaps present | Gap section names (readable form) appear in the risk finding and the PM "not reviewed" inventory; `{ref}_unavailable` codes intact |
| Q3 | SEC + FRED metadata present | Both deterministic listings render (form/date; release/date); listings are byte-stable across runs; live overlay never rewrites them |
| Q4 | Anti-boilerplate | When specific envelope facts exist (stale/caveats/gaps), no role summary equals the bare generic template; no two roles emit identical summary text |
| Q5 | Structure preservation | Audited live risk findings count == deterministic floor count (per-finding overlay, no collapse) once Layer 2 lands |
| Q6 | Determinism of floor | Same fixture → identical deterministic claim texts, refs, warning codes across runs |

**Safety — nothing new becomes advice or a leak:**

| ID | Case | Assertion |
| --- | --- | --- |
| S1 | Digit policy | LLM-authored sentences are digit-free; dates appear only inside backend-authored deterministic listings (which are never overlaid) |
| S2 | FRED interpretation injection | Injected provider output "the CPI release suggests a bullish setup" / "likely rate cut" → hard-blocked, deterministic fallback, eval flag recorded |
| S3 | Citation ownership | Injected output attempting to add refs/URLs/paths → refs unchanged; source-leak/interpretation blocks fire |
| S4 | No-substitution | SEC/FRED unavailable fixtures → named gap sentences + correct warning codes; no provider-substitution wording passes validators |
| S5 | Readback | Saved report list/detail readback re-runs neither tools nor provider (existing, keep) |
| S6 | Advice drift | Full prohibited-phrase sweep over the richer synthesis; read-only clause always present |

**Founder rubric (manual, per demo report, not CI):** (1) names ≥3 specific
ignorable items, (2) states freshness categories by name, (3) lists company/
macro events when present, (4) inventory of what was *not* reviewed, (5) zero
sentences that could be deleted without losing information.

## 8. Codex C implementation prompt — next backend slice (P34A-T9A)

Layer 1 only (deterministic specificity; no provider-seam changes — the
prompt-v2/per-finding overlay is the follow-up slice P34A-T9B after T9A
review):

```text
Agent: Codex C
Task: P34A-T9A - Deterministic specificity pack for tool-mediated Agent Team reports
Mode: backend implementation; one task; stop for Codex B review after.

Design reference: docs/claude-e-agentic/PHASE_34A_T9_LIVE_QUALITY_EVIDENCE_USE_DESIGN.md
(sections 3 Layer 1, 5, 6, 7).

Scope (all in backend/app/services/agent_team/ + tests; no schema/read-contract,
frontend, provider-seam, or new-source changes):

1. Freshness specificity: deterministic risk/technical claim texts name the
   freshness category ("categorized as stale/unknown/not available/fresh") for
   broker_snapshot_freshness and market_quote_freshness, using the existing
   _freshness_category vocabulary. No numbers.
2. Scope specificity: render scope_caveat_codes into readable clauses via a
   backend code->text map inside the risk role's scope finding; keep raw codes
   in caveat_codes.
3. Gap naming: the risk role's gap finding lists the unavailable section keys
   from evidence_gap_inspector in readable form; keep existing {ref}_unavailable
   warning codes.
4. FRED deterministic listing (mirror of the T6C SEC listing): when frozen
   economic_awareness_snapshot has source_key="fred_macro_calendar_metadata" and
   availability available/limited, render "Upcoming FRED macro calendar entries
   (metadata only): <name> (<date>); ..." from a new backend fact-key allowlist
   (release/event name + date keys only). actual/forecast/previous/observation
   keys remain forbidden. If no safe fact keys, keep the current availability
   sentence. Unavailable -> "FRED macro calendar metadata was not available or
   not reviewed in the saved evidence." + new warning code
   fred_economic_awareness_not_available. The FRED listing finding is
   deterministic and must not be live-overwritten (generalize the existing
   _sec_event_finding_stays_deterministic guard to cover it).
5. FRED interpretation hard block: additive backend-only pattern list mirroring
   SEC_INTERPRETATION_PATTERNS (macro-release interpretation/direction/urgency
   tokens near FRED/CPI/rate wording); wire into _hard_block_flag with eval flag
   fred_interpretation_blocked.
6. Compositional PM synthesis (still deterministic, no LLM): replace the fixed
   _synthesis_markdown template with deterministic assembly = locked-question
   intro + per-role one-line digests (from audited claim texts) + explicit
   "not reviewed / unavailable" inventory (gap refs + *_not_available codes) +
   open questions + manual verification checklist + the existing read-only
   closing clause. Must pass validate_agent_team_report_output; citations remain
   the audited synthesis_evidence_references (unchanged ownership).
7. Evals: add Q1-Q4, Q6, S2, S4, S6 from the design memo section 7 to
   tests/services/agent_eval/test_tool_mediated_eval.py and unit coverage in
   tests/services/agent_team/test_tool_mediated_report.py. Offline only;
   injected/fake providers; no live calls.

Boundaries: no LangGraph/LangChain/MCP/web/TradingAgents; no new sources or
providers; no frontend; no raw private values, URLs, prompts, traces, or
secrets; no advice/execution wording; deterministic backend owns all numbers
and citations; saved readback stays frozen.

Verification: cd backend && pytest (report counts for test_tools.py,
test_tool_mediated_report.py, test_tool_mediated_eval.py, report schema tests);
git diff --check.

Return per docs/shared/AGENT_REPORT_FORMAT.md with PASS/BLOCKED ask for Codex B.
```

Queued after T9A: **P34A-T9B** — live prompt v2 (per-role system prompts,
`p34a-tool-mediated-role-v2`) + per-finding prose overlay with per-sentence
validation and floor fallback (§3 Layer 2), plus eval Q5/S1/S3. Optional
later, Codex B-gated: **P34A-T9C** — prompt-fact allowlist exposing selected
qualitative payload fields to the live prompt, only if T9B reports still feel
thin.

## 9. Blockers / decisions for Codex B

1. Confirm the FRED deterministic listing (release name + date) is within the
   already-granted FRED metadata approval, or whether it re-opens the P34A-T4
   source-rights gate. (Design assumes it is the same normalized-metadata
   lane as display; if not, T9A item 4 splits out behind T4.)
2. Confirm the compositional PM synthesis stays within T2 Q2 ("PM synthesis
   deterministic in M1") — it does not add LLM authorship, only assembly.
3. Confirm `fred_interpretation_blocked` as a new eval flag value is
   acceptable in the frozen artifact vocabulary (additive).
4. T9B provider-seam changes need explicit Codex B review of the per-finding
   output contract before implementation.
