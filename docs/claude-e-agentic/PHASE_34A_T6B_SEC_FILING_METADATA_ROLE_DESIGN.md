# Phase 34A-T6B — Agent Role Behavior for SEC Recent Filing Metadata

Status: design-only (no implementation).
Owner: Claude E. Reviewer: Codex B.
Inputs: P34A-T6 source-rights gate
(`docs/codex-b-architecture/PHASE_34A_T6_PUBLIC_NEWS_EVENT_SOURCE_RIGHTS_GATE.md`),
P34A-T6A tool (already implemented:
`tools.py:_tool_sec_recent_filings_metadata:832`,
`SEC_RECENT_FILINGS_*` constants, registry entry `:512`), P34A-T2 live
role/auditor design, P33A-T2 citation boundary.

Locked product question (unchanged): **"What would I be ignoring if I acted
manually now?"** SEC filing metadata is *company-event context*, never a signal,
recommendation, interpretation, or conclusion.

---

## 0. What already exists (so this memo only designs role behavior)

- The tool `sec_recent_filings_metadata` is built, public-tier,
  `role_allowlist=all_roles`, `is_mock=False`, `mode="sync"`
  (`tools.py:512`). Its `ToolResult.evidence_refs` **reduces to
  `public_events_calendar`** (`tools.py:858`; `tool_mediated_report.py:92`).
- The result's `summary_payload.reviewed_filing_metadata` is a list of safe rows
  `{fact_key ∈ {form_type, filing_date, filing_reference}, fact_label,
  value_label}` (`_safe_sec_filing_metadata:939`), already filtered to drop raw
  paths/files and non-normalized `filref_…` references. Attribution, caveat, and
  non-endorsement strings are attached.
- Approval predicate `_is_approved_sec_recent_filings_section:905` requires
  `section_key=="public_events_calendar"`, `source_key=="sec_edgar_recent_filings"`,
  availability ∈ {available, limited}; otherwise `_public_events_unavailable_result`
  (availability `not_available`, `evidence_refs=()`).
- A deterministic `news_analyst` branch already emits a context finding when
  `public_events_calendar` (and/or `economic_awareness_snapshot`) is received
  (`tool_mediated_report.py:907`), citing `public_events_calendar` with caveat
  `sec_edgar_recent_filings_metadata_only`.
- Output-safety already carries SEC attribution/caveat/"does not interpret filing
  contents or treat filing metadata as a trading signal" wording
  (`report_output_safety.py:159`).
- Citation boundary: only `news_analyst` and `portfolio_manager_agent` have
  `public_events_calendar` in their `usable_content` (P33A map);
  fundamentals/technical/risk do **not**.

So T6B designs the **role reasoning layer** over an already-safe tool, and the one
real open decision below.

---

## 1. The crux decision: who lists the filing facts

The gate permits the LLM to *receive* normalized form-type/date labels. But the
live prompt envelope (`_prompt_tool_result_envelope:536`) **strips
`summary_payload`** — so today the LLM sees only `availability`, `caveat_codes`,
`source_label`, and `evidence_refs`, **not** the form types/dates. This memo
recommends keeping it that way and resolving the crux as:

> **D1 (recommended): the deterministic backend owns the neutral filing-metadata
> listing (form_type, filing_date); the live LLM never receives or restates
> specific filing facts.** The LLM may only contribute neutral availability/gap
> framing.

Rationale (consistent with the whole architecture's spine — *deterministic
backend owns all facts; the LLM does qualitative framing only*):

- The LLM cannot misinterpret, rank, or assign materiality/urgency to filings it
  never sees.
- The auditor cannot semantically verify an LLM restatement of filing facts;
  removing that surface removes the risk.
- form_type/filing_date are **facts**, exactly the class the backend already owns
  (like every number/metric). They belong in deterministic rendering.

The task's "news_analyst may … list neutral metadata context" is therefore a
**backend-rendered listing**, not LLM-authored prose. (Codex B: **Q1**.)

---

## 2. Role-by-role evidence use

| role | uses SEC filing metadata? | citable ref | behavior |
| --- | --- | --- | --- |
| `news_analyst` | **yes** (primary) | `public_events_calendar` | backend-rendered neutral listing + neutral framing; see §3 | 
| `portfolio_manager_agent` | **yes** (background only) | `public_events_calendar` | may mention presence/absence as a context/gap bucket point; never lists or interprets filings | 
| `fundamentals_analyst` | **no** | — | uses `public_company_profile` (identity) only; if it ever received the SEC result, the ref is filtered (not in its `usable_content`) |
| `technical_analyst` | **no** | — | filtered as above |
| `risk_management_agent` | **no** | — | filtered as above |

The planner already routes the SEC tool only to roles whose `usable_content`
contains `public_events_calendar` (news_analyst); PM consumes it via news's
audited finding. The `all_roles` allowlist on the tool is harmless because the
auditor filters the ref for any role outside the citable set (defense in depth).

---

## 3. Allowed vs disallowed wording

### 3.1 news_analyst — allowed (backend-rendered, deterministic)

- "Recent SEC EDGAR filing metadata was checked for this instrument."
- A neutral listing of normalized facts only, e.g. "Recent filings (metadata
  only): Form 10-Q (2026-05-01); Form 8-K (2026-04-15)."
- "This is company-event metadata only; filing contents are not reviewed."
- "Filing metadata is not a trading signal and is not investment advice."
- Availability/gap states: "available", "limited", "not available", "not
  reviewed".
- The attached attribution, caveat, and non-endorsement strings.

### 3.2 news_analyst — live LLM may add (only neutral framing, no facts)

- "Reviewed filing activity is background context you might overlook; its
  contents are not reviewed here." (Qualitative framing only; the LLM never sees
  or emits the specific form types/dates — those come from the backend listing.)

### 3.3 Disallowed for every role (auditor hard-blocks — §4)

- interpretation: "signals", "bullish/bearish", "material/materiality",
  "significant", "catalyst", "implies", "suggests", "priced in", "reaction",
  "beat/miss", "guidance", "positive/negative for the stock";
- urgency: "urgent", "act now", "time-sensitive", "before earnings";
- filing-content: "the filing states/says/discloses/reveals/reports", "according
  to the filing", quotes or paraphrase of contents, exhibits, XBRL facts;
- any advice/order/execution/safe-or-ready-to-trade/recommendation wording;
- any generated number/metric/level/price/probability tied to the filing;
- raw URLs, raw SEC paths, accession numbers as URLs, file names;
- SEC endorsement wording ("approved by", "endorsed by the SEC").

### 3.4 PM synthesis — allowed

- "Recent company-event metadata (SEC EDGAR filing metadata) was reviewed as
  background." / "No reviewed company-event metadata was available — a context
  gap." Never lists or interprets specific filings.

---

## 4. Evidence Auditor rejection rules (SEC-specific, on top of P34A-T2)

Applied to any finding citing `public_events_calendar` sourced from
`sec_edgar_recent_filings` (and as a safety net, to all findings):

1. **Interpretation guard (new):** flag a new `SEC_INTERPRETATION_TOKENS` block
   list (the §3.3 interpretation + urgency + filing-content tokens). Any hit →
   **fail-closed**: drop the finding and fall back to the deterministic SEC
   listing (per P34A-T2 §3.1); eval_flag `sec_interpretation_blocked`. Never
   re-passed.
2. **Filing-content / raw-path guard:** reuse `SEC_RAW_PATH_OR_FILE_RE` and the
   forbidden value tokens (`filing_body`, `filing_text`, "filing text", "filing
   body") + `SOURCE_LEAK_PATTERNS` over the finding text. Any hit → drop +
   `private_leak_blocked`/`source_leak_blocked`; never re-passed.
3. **Citation rule:** a SEC content finding must cite `public_events_calendar`
   and only when the SEC result availability ∈ {available, limited}; an
   unavailable/not-approved result is a **gap** citing `trade_intent_summary`
   only — `public_events_calendar` must not appear in `evidence_references`
   (enforced by the existing availability filter).
4. **Role boundary:** only `news_analyst` and `portfolio_manager_agent` may cite
   `public_events_calendar`; for any other role the ref is filtered
   (`citable_boundary_filtered`).
5. **No generated numbers:** the existing `TOOL_GENERATED_METRIC_PATTERNS` /
   `INVENTED_LEVEL_PATTERNS` still apply. **Verification point:** the
   backend-rendered listing of `form_type` (e.g. "10-Q") and `filing_date`
   ("2026-05-01") must be confirmed *not* to trip these guards (they are not
   currency/percent/level/share tokens). If a future form/date format risks a
   false positive, normalize the rendering; do not relax the guard.

All SEC hard-blocks are **never** re-passed (P34A-T2 §3); on block, fall back to
the deterministic listing finding, or to the gap finding if no listing is
available.

---

## 5. Degradation behavior

| condition | result | role behavior |
| --- | --- | --- |
| SEC section unavailable / not approved (`_is_approved_…` false) | `_public_events_unavailable_result` (availability `not_available`, `evidence_refs=()`) | news emits gap: "Recent SEC EDGAR filing metadata was not available or not reviewed for this instrument," cites `trade_intent_summary` only; warning `sec_edgar_recent_filings_not_available`; PM notes the gap |
| `public_evidence` is None | unavailable result (`tools.py:838`) | same gap; no crash |
| source-rights revoked (future) | result `status=blocked` / `source_rights_not_approved` | same gap framing; **never** fall back to NewsAPI/GDELT/FMP/Benzinga/Finnhub/Polygon/web/scraping (gate §Failure) |
| live provider fails on news | unaffected — news SEC listing is deterministic (Q2) | listing still rendered |

Absence of EDGAR metadata is always a **gap/context point, never a signal**.

---

## 6. Output shape / freeze / frontend

- **news finding (pre-persist):** `finding_type="missing_context"`, `claim_text`
  = backend listing + neutral framing, `evidence_refs=("trade_intent_summary",
  "public_events_calendar")`, `caveat_codes` includes
  `sec_edgar_recent_filings_metadata_only`. Reduces to the existing
  `SavedAgentTeamRoleSummaryRead` (no schema change).
- **freeze:** the SEC `ToolResult` (incl. safe normalized
  `reviewed_filing_metadata`, attribution, caveat, non-endorsement) freezes into
  `tool_run_artifact.tool_results` via the existing `_frozen_tool_result`. Allowed
  by the gate. Confirm the freeze contains **no** raw URL/path/body (already
  stripped at the tool boundary). Readback re-runs nothing.
- **run-state only / never frontend:** raw SEC payload (never persisted), the LLM
  prompt/response, provider config, and (until a T-later reviewed read contract)
  the `tool_run_artifact` itself. The eventual frontend shows only the neutral
  listing + caveats + attribution, never interpretation.
- **no new schema/read-contract field** (Q4): the listing lives in the existing
  `claim_text`; a structured filings field on the read model would be a separate
  Codex-B-reviewed change — not recommended now.

---

## 7. Test matrix for Codex C

Offline/deterministic, synthetic EDGAR metadata only (no real filings, no
network). Extend `test_tool_mediated_report.py` / `test_tools.py` and the
`agent_eval` SEC scenario group.

- **SEC-1 available:** approved SEC section → news finding cites
  `public_events_calendar`, backend-lists form_type+filing_date, caveat
  `sec_edgar_recent_filings_metadata_only`; full summary passes
  `validate_agent_team_report_output`.
- **SEC-2 guard-safe listing:** the rendered listing "Form 10-Q (2026-05-01); …"
  passes `_hard_block_flag` (no `TOOL_GENERATED_METRIC_PATTERNS` /
  `INVENTED_LEVEL_PATTERNS` / `SOURCE_LEAK_PATTERNS` false positive).
- **SEC-3 unavailable:** not-approved/limited-unavailable section → news gap cites
  `trade_intent_summary` only; warning `sec_edgar_recent_filings_not_available`;
  `public_events_calendar` absent from all `evidence_references`.
- **SEC-4 no public evidence:** `public_evidence=None` → unavailable result → gap;
  no crash.
- **SEC-5 raw-path/body injected:** a fact value containing an EDGAR path / file
  / `filing_body` is stripped by `_safe_sec_filing_metadata`; if injected into a
  finding it is dropped by the raw-path/source-leak guard; summary clean.
- **SEC-6 interpretation injected:** a finding claiming "8-K signals a bullish
  catalyst" / "material event" / "act before earnings" → dropped via
  `sec_interpretation_blocked`; fall back to deterministic listing; summary clean.
- **SEC-7 filing-content injected:** "the filing states revenue rose" → dropped
  (filing-content guard); summary clean.
- **SEC-8 role boundary:** a fundamentals/technical/risk finding citing
  `public_events_calendar` → filtered (`citable_boundary_filtered`); not cited.
- **SEC-9 PM background:** PM synthesis mentions presence/absence of company-event
  metadata; cites `public_events_calendar` only when news surfaced it (∈ PM
  usable); never interprets or lists filings.
- **SEC-10 live boundary:** with live enabled, the prompt messages for every role
  contain **no** `reviewed_filing_metadata`/`summary_payload` (assert the SEC
  envelope in the prompt has only safe label fields); the news SEC listing stays
  deterministic (not overwritten) per Q2.
- **SEC-11 freeze:** frozen `tool_run_artifact` SEC result carries only safe
  normalized metadata (no URL/path/body); reopening calls the provider/tool zero
  times.
- **SEC-12 attribution:** SEC attribution + caveat + non-endorsement present;
  SEC-endorsement wording absent.

---

## 8. Blockers / Codex B decisions

- **Q1 (crux):** confirm the neutral filing-metadata listing is
  **backend-deterministic** and the LLM prompt envelope stays stripped of
  `summary_payload` (LLM never sees/restates filing facts). Recommend confirm.
- **Q2:** confirm `news_analyst`'s SEC/event finding is **not live-overwritten**
  in M1 (stays deterministic so the fact listing survives); the live layer may
  enhance only non-factual framing. Recommend keep deterministic for M1.
- **Q3:** confirm extending the current generic "metadata available" phrasing to
  an actual **backend listing of form_type/filing_date** is in scope for Codex C
  (a deterministic rendering change). The task asks news to "list neutral metadata
  context," so recommend yes.
- **Q4:** confirm **no new schema/read-contract field** (listing in existing
  `claim_text`; reuse `public_events_calendar`). A structured filings field is a
  separate future Codex B review. Recommend no change now.
- New auditor constant `SEC_INTERPRETATION_TOKENS` is additive backend code (no
  schema/read-contract impact).

No hard blockers; all four are confirmations.

---

## 9. Return summary

- **Status: PASS** — role-behavior design ready for Codex C, pending Q1–Q4.
- **Design decisions:** deterministic backend owns the filing-fact listing; LLM
  contributes only neutral framing and never sees filing facts; only news (content)
  and PM (background) may cite `public_events_calendar`; a new interpretation guard
  + the existing content/path/number guards fail-closed to the deterministic
  listing or gap; absence is always a gap, never a signal; no new schema.
- **Open risks:** (R-a) the backend listing contains digits (form numbers/dates)
  and must be proven guard-safe (SEC-2); (R-b) if Q1 flips to LLM-authored listing,
  the prompt envelope widens and the auditor needs a semantic faithfulness path —
  re-spec required.
- **Files changed:** this design memo only. No code.
