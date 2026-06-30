# Phase 34A-T2 — Live Role Prompt, Planner, and Evidence Auditor Design

Status: design-only (no implementation).
Owner: Claude E. Reviewer: Codex B. Stop for Codex B review before implementation.
Inputs: P34A-T0 contract
(`docs/codex-b-architecture/PHASE_34A_LIVE_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`);
P34A-T1 live runner gate (PASS, in
`backend/app/services/agent_team/tool_mediated_report.py`); P33A-T2 design
(`PHASE_33A_T2_PLANNER_AUDITOR_ROLE_DESIGN.md`) and its pinned
`usable_content_by_role` map.

Locked product question (unchanged): **"What would I be ignoring if I acted
manually now?"** — never "should I trade?". No AI-stock-picker posture.

Scope: M1 only — live LLM role prose over the seven already-reviewed
saved-evidence tools. No new sources, no LangGraph, no MCP, no public-news
expansion.

---

## 0. Framing (the load-bearing decision)

P34A-T1 made one excellent structural choice that this design endorses and builds
on:

> **The LLM authors *prose*; the backend owns *citations*.** In the T1 seam
> (`_live_provider_role_findings`, `tool_mediated_report.py:448`), the live role
> output replaces a deterministic finding's `claim_text` with model prose but
> keeps the deterministic `evidence_refs` and `caveat_codes`. The LLM never
> selects evidence, never sees raw values, and cannot cite outside the boundary —
> because it does not control `evidence_refs` at all.

Two consequences shape everything below:

1. **The deterministic finding is the safety floor.** Every live role already has
   a P33A-validated deterministic finding underneath it (refs within
   `usable_content[role] ∩ available`, no advice, no numbers). The live prose is
   an *enhancement layer* on top of that floor.
2. **Therefore fail-closed should mean "fall back to the deterministic finding,"
   not "skip."** T1 currently degrades a failed/unsafe live role to `skipped`
   (`_live_provider_skipped:577`), which loses coverage. This design recommends
   degrading to the **deterministic finding** (safe and already audited) plus a
   warning code. The live report is then *never worse than* the P33A
   deterministic report, and never unsafe. (Codex B decision **Q3**.)

This makes the live prototype genuinely "live" (real model prose, real reviewed
data) while keeping the citation graph, privacy boundary, and no-verdict posture
exactly as strong as the deterministic prototype.

---

## 1. Live prompt design

### 1.1 Shared prompt boundary (all roles)

The prompt the provider receives must contain **only** (per contract "Live Prompt
Boundary"):

- role name + role-safe instructions;
- the locked product question;
- the **sanitized** `ToolResult` envelopes for that role (the T1
  `_prompt_tool_result_envelope`, `tool_mediated_report.py:536`, which keeps only
  `tool_name, status, evidence_tier, data_mode, source_key, source_label,
  availability, freshness, caveat_codes, evidence_refs, is_mock` and passes
  `validate_tool_payload`);
- the `allowed_evidence_refs` list (the deterministic finding's refs);
- the output rule (one short qualitative sentence per finding, no numbers).

The prompt must **never** contain: raw saved-artifact payloads, raw
`summary_payload`, scope values, `as_of` timestamps, account details, provider
payloads, source URLs, traces, secrets, config, or any example with real private
data. The envelope sent to the model already strips `summary_payload`, `scope`,
`as_of`, `payload`, `latency_ms`, `estimated_cost` — keep it that way.

### 1.2 Output contract returned by the model

Recommend a tight JSON-or-markdown output: for each `allowed_evidence_ref` group,
one **qualitative background-context sentence** (digit-free, non-directional). The
model may not return refs; refs are reattached by the backend. Recommended
refinement over T1: **per-finding prose** (one sentence per deterministic
finding, preserving each finding's exact refs) rather than one collapsed sentence
per role — this keeps the citation graph at finding granularity. One-sentence-
per-role (T1's current shape) is an acceptable fallback. (Codex B decision **Q5**.)

### 1.3 Per-tool framing the model may rely on (M1 catalog)

The model sees these envelopes and must treat each as *labels/availability/
caveats only*, never as values to quote:

| tool | what the model may say about it | what it must never do |
| --- | --- | --- |
| `trade_intent_summary` | name the reviewed instrument/flow as the subject of review | restate or infer position size, value, or intent beyond the label |
| `portfolio_scope_context` | note scope mode and that account-feasibility caveats exist | infer holdings, balances, buying power, or account identity |
| `deterministic_review_findings` | note that deterministic risk/impact/concentration/collateral/option-exposure flags exist and could be overlooked | reproduce or compute any severity number, ratio, collateral, or Greek |
| `broker_snapshot_freshness` | note the freshness *category* (e.g. stale) as a manual-review caveat | quote a timestamp or compute staleness |
| `market_quote_freshness` | note quote-freshness *category* as public context | quote a price, level, or time |
| `public_company_profile` | note reviewed company identity/listing context as background | infer valuation, fundamentals values, or a view |
| `evidence_gap_inspector` | name which sections are *unavailable* as open gaps | treat an unavailable section as if it had content; cite it as evidence |

---

## 2. Role behavior

Citation sets are inherited unchanged from P33A `usable_content_by_role` (already
pinned and tested); the live layer changes only prose focus and prohibitions. A
role that is **deterministically `skipped`** (empty findings) gets **no live
call** — there is nothing to enhance and a call would waste budget (T1 already
short-circuits this, `tool_mediated_report.py:454`). Keep that.

| role | tier | live prose focus | must ignore / never say | citable (from P33A) |
| --- | --- | --- | --- | --- |
| `fundamentals_analyst` | public | reviewed public company identity/listing context as background that could be overlooked; flag unreviewed fundamentals/events as a gap | valuation, any number, directional view, portfolio/account framing | trade_intent_summary, public_company_profile |
| `news_analyst` | public | in M1 usually `skipped` → states reviewed news/event/macro context was not available (gap); **no live call when skipped** | inventing news, citing a toolless section | trade_intent_summary |
| `technical_analyst` | public | quote-freshness as non-directional public context that could be overlooked | levels, targets, indicator values, directional calls | trade_intent_summary, market_quote_freshness |
| `risk_management_agent` | agent_safe | qualitatively elaborate what deterministic risk/freshness/scope-feasibility/option-structure caveats could be overlooked | computing collateral/Greeks/concentration; advice; feasibility verdicts | trade_intent_summary, scope_state, actionability, freshness, portfolio_impact_summary, concentration_risk_drift, liquidity_collateral_caveats, options_exposure_summary, market_quote_freshness |
| `portfolio_manager_agent` | agent_safe | **deterministic synthesis in M1** (see Q2) — four-bucket "what you'd be ignoring" over audited findings + open questions | any verdict, ranking, target, action; introducing a ref no role surfaced | union of audited refs ∩ PM usable |

**`portfolio_manager_agent` stays deterministic in M1.** It is a reduction over
already-audited, already-cited findings; making it live adds hallucination surface
at the most visible output with **no new evidence**. Recommend enabling live PM
synthesis only as an M1.5 follow-up once eval validates role-prose quality. (Codex
B decision **Q2**.)

---

## 3. Evidence Auditor behavior (live)

The auditor runs over the (now model-authored) findings exactly as in P33A
(`audit_findings`, `tool_mediated_report.py:589`), with these live-specific
points. **All checks operate on the finding after the LLM prose is attached**, so
model prose is fully re-validated.

1. **Citation completeness** — every finding's `evidence_refs ⊆ received refs`.
   Passes by construction in M1 (refs are backend-owned), but enforced as defense
   in depth for any future model-proposed-ref path.
2. **Role evidence boundary** — `evidence_refs ⊆ usable_content[role]`.
3. **Unavailable/gap refs not cited** — refs filtered to availability ∈
   {available, limited}; gap sections appear only as warning codes/prose, never as
   citations.
4. **Contradiction detection — base it on structured signals, not prose.**
   Recommend M1 detects contradictions on **`caveat_codes` / `availability` of the
   same `evidence_ref` across roles** (reliable, deterministic), not on LLM prose
   tokens (the current `_opposing_stance` lexical check, `:825`, is brittle once
   prose is free-form). A contradiction becomes an **open question**; neither side
   is dropped for being contradictory. (Codex B decision **Q4**.)
5. **Private-data rejection** — `validate_llm_provider_output` on the raw response
   (already in T1, `:468`) **plus** `_hard_block_flag` (forbidden keys/values,
   secret patterns) on the assembled finding. Fail-closed: never re-pass a leak.
6. **Advice / actionability rejection** — `_hard_block_flag` over
   `REPORT_PROHIBITED_PHRASES + TOOL_PROHIBITED_PHRASES + find_prohibited_llm_phrases`.
   Fail-closed.
7. **Invented-number / generated-metric / level / source-URL rejection** —
   `_hard_block_flag` over `TOOL_GENERATED_METRIC_PATTERNS + INVENTED_LEVEL_PATTERNS
   + SOURCE_LEAK_PATTERNS`. Fail-closed.
8. **One bounded re-pass** — only for *fixable* failures (unsupported / citable-
   boundary / availability filtered, or a contradiction that a tightened
   instruction could resolve). The live re-pass re-issues the provider call **once**
   with a corrective instruction ("restrict strictly to these refs; one
   qualitative sentence; no numbers"). Hard-block failures (5–7) are **never**
   re-passed.

### 3.1 Fail-closed = deterministic fallback (recommended)

On any live failure — hard-block, invalid/empty response, provider error, or a
fixable failure that survives the single re-pass — the role degrades to its
**deterministic finding** (the safety floor from §0), not to an empty skip,
**unless** the deterministic finding is itself empty (then skip honestly). Emit a
warning code recording why:

- `live_provider_reasoning_used` — live prose accepted;
- `live_provider_safety_fallback` — live prose hard-blocked → deterministic used;
- `live_provider_unsupported_fallback` — fixable failure survived re-pass →
  deterministic used;
- `live_provider_unavailable` / `live_provider_provider_timeout` /
  `live_provider_rate_limited` / `live_provider_quota_exceeded` /
  `live_provider_provider_auth_error` — provider failure → deterministic used (or
  skip if no floor).

This changes T1's current skip-on-failure to fallback-on-failure (Q3); it is
strictly safer-and-more-useful and reuses content that already passed every P33A
validator.

---

## 4. Output shape

### 4.1 Role findings before persistence

`RoleFindingSet` unchanged in shape (P33A): `role_name`, `role_status`
(`completed` when live prose or deterministic floor present; `skipped` only when
no floor), `findings[*]` with `claim_text` = validated live prose **or**
deterministic prose, `evidence_refs` = backend-owned (within usable ∩ available),
`caveat_codes` = deterministic, `warning_codes` per §3.1.

### 4.2 warning_codes / caveat_codes

- **warning_codes** (role/run): the `live_provider_*` codes (§3.1); P33A coverage
  codes (`public_evidence_roles_included|partial_coverage|skipped`); `<section>_unavailable`
  gap codes; auditor eval_flags (`private_leak_blocked`, `advice_wording_blocked`,
  `invented_metric_blocked`, `unsupported_claim`, `citable_boundary_filtered`,
  `unavailable_ref_filtered`, `contradiction_open_question`).
- **caveat_codes**: backend-owned, copied from the deterministic evidence
  sections (`evidence.caveat_codes`, `scope_caveat_codes`,
  `options_exposure_summary.caveat_codes`). The LLM never authors caveat codes.

### 4.3 Run-state only (never persisted, never frontend)

- the raw `LLMProviderRequest` messages (prompt text) and the raw
  `LLMProviderResponse` object;
- any provider config / resolution / secrets / API keys;
- the catalog's internal availability map beyond what is frozen;
- the auditor's internal `dropped_claims` reasons may stay run-state (or freeze as
  opaque codes — Codex B choice), but are **not** frontend fields.

### 4.4 Should freeze into `tool_run_artifact`

Everything P33A already freezes (`SavedToolMediatedRunArtifactRead`, `reports.py:512`)
**plus** `provider_mode = "tool_mediated_live"` and, **new**, *safe provider
metadata per role*: `provider`, `model`, `prompt_version`, `status`, `tokens_in`,
`tokens_out`, `estimated_cost`, `is_mock`. This requires an **additive schema
field** (e.g. `provider_runs: tuple[SafeProviderRunMetaRead, ...]`) — the contract
anticipates "freeze includes safe provider metadata, not raw provider payloads,"
but the exact field needs Codex B sign-off (Codex B decision **Q1**). The frozen
`claim_text` is the validated live prose, so readback shows live output **without
re-running the provider** (contract requirement).

### 4.5 Never shown to frontend

Raw prompts, raw responses, provider config/secrets, token/cost internals, plan
internals, and (until a separate Codex-B-reviewed T6 read contract) the
`tool_run_artifact` itself. Frontend continues to show only the sanitized role
summaries + synthesis + citations + gaps/caveats.

---

## 5. Test / eval matrix for Codex C (fake/injected provider; default offline)

Use a fake `LLMProvider` whose `complete()` returns canned `LLMProviderResponse`s.
Default tests never call a live provider.

**Live prose happy path**
- L1: fake returns a safe qualitative sentence → role `completed`, `claim_text`
  == model prose, `evidence_refs` == deterministic union (unchanged), warning
  `live_provider_reasoning_used`; full summary passes
  `validate_agent_team_report_output`.
- L2: citation integrity — model output cannot change refs; assert live
  `evidence_refs` ⊆ `usable_content[role] ∩ available` and identical to the
  deterministic finding's refs.

**Fail-closed (deterministic fallback)**
- L3: fake returns `you should buy` → finding falls back to deterministic prose;
  warning `live_provider_safety_fallback`; eval_flag `advice_wording_blocked`;
  summary clean; **no re-pass**.
- L4: fake returns `$1,200` / `30%` / `support at 45` (3 sub-cases) → deterministic
  fallback; `invented_metric_blocked`; summary clean.
- L5: fake returns text containing `buying_power` → deterministic fallback;
  `private_leak_blocked`; summary clean.
- L6: fake returns empty / `status != ok` → deterministic fallback; warning
  `live_provider_unavailable` (or specific code).
- L7: fake raises timeout / auth error → role degrades; other roles still
  complete; report `partially_completed` or `completed` with the warning; no crash.

**Prompt boundary**
- L8: capture the `LLMProviderRequest.messages`; assert they contain only
  sanitized envelope fields (no `summary_payload`, `scope`, `as_of`, payload),
  pass `validate_tool_payload`, and contain no forbidden key/value/secret/URL.

**Auditor**
- L9: contradiction on the same ref via opposing `caveat_codes`/`availability`
  across two roles → `contradictions` ≥1, `open_questions` non-empty, both sides
  survive (structured detection, §3.4).
- L10: bounded re-pass — a fixable failure triggers exactly one provider re-call;
  if it still fails, deterministic fallback; assert provider `complete` called ≤2
  for that role.

**Reproducibility**
- L11: frozen `tool_run_artifact` contains the validated live `claim_text` + safe
  provider metadata; re-validating / reopening the saved summary calls the
  provider **zero** times (assert call count unchanged after readback).
- L12: regeneration policy is explicit — a re-run with live enabled produces a new
  artifact; readback of a saved report never re-runs (frozen-on-readback, not
  identical-on-re-run).

**Gate / regression**
- L13: default (live disabled) → byte-stable deterministic path unchanged; the
  full P33A `test_tool_mediated_report.py` and T5 eval suites still pass.
- L14: provider config snapshot carries no secret values (assert no api key /
  token in any frozen or logged metadata).

Extend the P33A-T5 `agent_eval` harness with a `live_provider` scenario group
reusing these fakes, so the existing rubric (privacy, citation, auditor,
reproducibility) also scores live runs.

---

## 6. Blockers / Codex B decisions

- **Q1 (schema):** approve the additive `provider_runs` safe-metadata field on
  `SavedToolMediatedRunArtifactRead` (provider/model/prompt_version/status/tokens/
  cost/is_mock). Anticipated by the contract; needs Codex B sign-off as a
  read-contract change.
- **Q2:** `portfolio_manager_agent` synthesis stays **deterministic in M1** (live
  PM synthesis deferred to M1.5). Recommend confirm.
- **Q3:** live failure degrades to the **deterministic finding** (not skip).
  Recommend confirm (changes T1 behavior; strictly safer-and-more-useful).
- **Q4:** contradiction detection uses **structured signals**
  (`caveat_codes`/`availability`), not LLM prose tokens. Recommend confirm.
- **Q5:** **per-finding** live prose vs T1's one-sentence-per-role. Recommend
  per-finding; one-per-role acceptable.
- **Q6 (sequencing):** the contract's P34A-T3 is the *real saved-evidence tool
  pack*. The T2 prompt/auditor refinements (Q2–Q5) are tightly coupled to it.
  Recommend folding both into T3, or splitting into T3a (prompt/auditor impl) +
  T3b (tool pack). Codex B to choose.

No hard blockers to the design; all six are confirmations/sequencing.

---

## 7. Return summary

- **Status: PASS** — live role-prompt / planner / auditor design is ready for
  Codex C, pending Codex B Q1–Q6. The design preserves the locked question and
  no-verdict posture, keeps citations backend-owned, treats the deterministic
  finding as a safety floor, and freezes live output for re-run-free readback.
- **Key contributions over the T1 seam:** deterministic-fallback (not skip) on
  failure; structured-signal contradiction detection; per-finding prose;
  deterministic PM synthesis in M1; the safe-provider-metadata freeze field.
- **Open risks:** (R-a) semantic faithfulness of prose vs cited section is not
  fully checkable deterministically — mitigated by forcing qualitative, digit-
  free, label-only framing + the hard-block scans + the deterministic floor;
  (R-b) Q1 schema field must land before live freeze can persist provider
  metadata; (R-c) live cost/latency — bounded by the contract's
  timeout/retry/token-budget/partial-fallback, with mock default.
- **Files changed:** this design memo only. No code.
