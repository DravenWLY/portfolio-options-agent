# Phase 29B-T2 Public Role Agentic Design

Status: design accepted (design-only; no code in this task). Codex B
review-only PASS 2026-06-15.
Owner: Claude E (agentic-system design)
Reviewer: Codex B (architecture/privacy/safety)
Related plan: `docs/shared/implementation_plan.md` Phase 29B, task `P29B-T2`
Builds on (shipped):
- `docs/codex-b-architecture/PHASE_29B_PUBLIC_AGENT_EVIDENCE_CONTRACT.md` (P29B-T0)
- P29B-T1 backend public evidence contract (Codex C): `SavedPublicEvidencePackageRead`,
  `SavedPublicEvidenceSectionRead`, `SavedPublicEvidenceFactRead`,
  `backend/app/services/reports/public_evidence.py`
- `docs/claude-e-agentic/PHASE_29A_T2_AGENT_TEAM_REPORT_OUTPUT_CONTRACT.md`
- Implemented validator: `backend/app/services/agent_team/report_output_safety.py`
- Generation path: `backend/app/services/reports/agent_team_report.py`

## 1. Scope

Design how `fundamentals_analyst`, `news_analyst`, and `technical_analyst`
consume the reviewed P29B public evidence sections and produce safe, degraded,
saveable Agent Team report output. Design-only; no backend/frontend code, no
runtime tools, no provider/LLM/market-data/broker/TradingAgents calls, no
private MCP. The default public-evidence projection is offline/not-reviewed
(`NoReviewedPublicEvidenceProvider`); this design works with synthetic reviewed
evidence and must keep saved reports reproducible.

The implemented T1 validator already carries per-role public allowlists and
recursive nested-section availability enforcement. This design **ratifies and
documents** that contract from the agentic side, fills the role behavior /
degradation / projection / eval gaps, and specifies the exact preservation rules
T3 must follow. It proposes **no required** new report-output fields (one
optional, additive, deferred field is noted in section 8).

## 2. Public Evidence Inputs (from P29B-T1, preserved verbatim)

Section keys (`SavedPublicEvidenceSectionKey`):
`public_company_profile`, `public_fundamentals_snapshot`,
`public_news_snapshot`, `public_events_calendar`, `public_technical_context`,
`public_market_context`.

Each `SavedPublicEvidenceSectionRead` carries only sanitized fields:
`section_key`, `section_label`, `availability`
(`available|limited|not_available|not_reviewed|not_applicable`),
`freshness_category` (`fresh|stale|unknown|not_available|not_reviewed`),
`freshness_label`, `source_label`, `rights_status`
(`reviewed|internal_demo_only|not_reviewed`), optional `as_of`/`collected_at`,
`summary_label`, bounded `facts` (`fact_key`, `fact_label`, `value_label`,
`as_of_label`, `source_label`), `limitations`, `caveat_codes`. The section
validator already forbids `available`/`limited` with `not_reviewed` rights, and
`validate_public_evidence_payload` rejects private keys, raw source/payload
hints, URLs, article bodies, prompts, traces, secrets, and unsafe wording.

`SavedPublicEvidencePackageRead` is nested inside `SavedEvidencePackageRead`
(field `public_evidence`), defaulting to `.not_reviewed(...)`. The report-output
validator's `_collect_section_availability` recurses into it, so when the
package is passed to the validator the public-section availabilities are
enforced.

## 3. Per-Role Evidence Projection Rules

T3 builds, backend-side and before any prompt assembly, a **role-scoped public
evidence projection** per public role. It is a strict narrowing of
`SavedPublicEvidencePackageRead` to the role's allowlist, carrying only the
already-sanitized section fields above plus minimal instrument context. No other
sections, no portfolio/account data, no raw payloads/URLs/bodies, no prompts or
traces ever enter a public-role projection.

Illustrative shape (design sketch; T3 chooses the concrete type, may extend the
existing `prompt_inputs.AgentTeamPromptInput.public_context`):

    PublicRoleEvidenceProjection:
      role_name: AgentTeamRole                # public role only
      instrument_context:                      # identify the reviewed instrument only
        symbol_or_underlying: str | None
        review_flow_label: str
      allowed_section_keys: tuple[str, ...]    # the role's allowlist (section 4)
      sections: tuple[SavedPublicEvidenceSectionRead, ...]  # ONLY allowed keys
      citable_section_keys: tuple[str, ...]    # subset with availability in {available, limited}
      degrade_reason: str | None               # set when citable_section_keys is empty

Projection rules:

- Include only sections whose `section_key` is in the role's allowlist
  (section 4). Drop every other section entirely — a public role never even
  sees out-of-boundary evidence.
- `citable_section_keys` = allowed sections with `availability ∈ {available,
  limited}`. Only these may be cited in output (section 5/6).
- Carry the sanitized section fields as-is; never re-summarize numbers, never
  add fields. Facts are passed as their bounded label/value-label pairs only.
- Instrument context is limited to `symbol_or_underlying` and the
  `review_flow_label` (both already display-safe) so the role can name the
  instrument. No account/scope/portfolio fields for public roles.
- Map to the existing seam: `build_agent_team_prompt_input` already sets
  `portfolio_evidence_allowed=False` and `output_mode="analysis_only_public_evidence"`
  for public roles and validates the whole input via `validate_agent_team_text`.
  T3 replaces the legacy `PublicEvidenceBundle`/`_availability` stub in
  `public_context` with this reviewed projection (or threads it alongside), and
  must keep the input passing `validate_agent_team_text`.

## 4. Per-Role Citation Allowlists (ratifies implemented `ROLE_ALLOWED_EVIDENCE_KEYS`)

These match `report_output_safety.ROLE_ALLOWED_EVIDENCE_KEYS` exactly and align
with the P29B-T1 section keys. `trade_intent_summary` is always citable
(package-level category, not availability-gated).

| role | citable public/macro sections | rationale |
| --- | --- | --- |
| `fundamentals_analyst` | `public_company_profile`, `public_fundamentals_snapshot`, `public_events_calendar` | company/fund identity + reviewed fundamentals labels + events that affect company understanding |
| `news_analyst` | `public_news_snapshot`, `public_events_calendar`, `public_market_context`, `economic_awareness_snapshot`, `market_mood_snapshot` | reviewed news/event metadata + approved macro/market context |
| `technical_analyst` | `public_technical_context`, `public_market_context`, `market_quote_freshness` | reviewed market/technical context labels + quote freshness category |

Notes:
- `economic_awareness_snapshot` / `market_mood_snapshot` / `market_quote_freshness`
  are P29A package sections (not public-evidence sections); they remain
  availability-gated and are `not_reviewed`/`not_available` by default, so they
  degrade exactly like the public sections until separately reviewed.
- No public role may cite portfolio-aware sections
  (`scope_state`, `account_readiness`, `portfolio_impact_summary`,
  `before_after_portfolio_impact`, `concentration_risk_drift`,
  `liquidity_collateral_caveats`, `options_exposure_summary`). The validator
  enforces this; the projection never supplies them.
- The `portfolio_manager_agent` allowlist already includes all public-evidence
  keys, so the PM may reference public sections in synthesis (section 7).

## 5. What Each Role May / Must Not Output

All public roles: analysis-only, non-directional, qualitative; cite only
`citable_section_keys`; state unknown/stale/unavailable honestly; never invent
numbers; never produce advice/order/execution/guaranteed/safe-or-ready-to-trade/
buy-sell wording.

- **Fundamentals Analyst** — may: qualitative framing of what reviewed public
  company/fund evidence says; explicit unknowns/limitations; non-directional
  context. Must not: invented valuation metrics, price targets, buy/sell/hold,
  "cheap/overvalued/undervalued" as a verdict, any portfolio/account
  interpretation.
- **News Analyst** — may: neutral event/news summaries from reviewed metadata
  and licensed short summaries; what is known/unknown/stale/unavailable; topics
  the user may verify manually. Must not: price-move predictions,
  "trade before/after event" framing, article bodies/long excerpts, urgency or
  fear/greed language, unlicensed source text.
- **Technical Analyst** — may: neutral market-context framing from backend-owned
  labels; freshness/limitation notes; non-directional observations. Must not:
  entry/exit instructions, LLM-invented support/resistance or price targets,
  indicator values not backend/source-provided under reviewed rights,
  "signal says buy/sell" language.

## 6. Degradation Semantics

Role output uses the existing `SavedAgentTeamRoleSummaryRead`
(`role_name`, `display_name`, `role_status`, `provider_status`,
`summary_markdown`, `evidence_references`, `warning_codes`, `unavailable_reason`).
`role_status ∈ {completed, unavailable, skipped, gated, validation_failed}`
(existing `AgentTeamReportRoleStatus`). Degradation is honest and fail-closed.

| condition | role_status | provider_status | summary_markdown | evidence_references | warning_codes / unavailable_reason |
| --- | --- | --- | --- | --- | --- |
| ≥1 allowed section `available`/`limited` | `completed` | `ok` | neutral narrative citing only citable sections; explicit notes for missing/stale ones | the cited section keys (+ `trade_intent_summary`) | limited/stale → e.g. `public_evidence_limited`; none |
| all allowed sections `not_reviewed` | `skipped` | `skipped` | `None` | `("trade_intent_summary",)` or `()` | `no_reviewed_public_evidence` |
| all allowed sections `not_available` | `skipped` | `skipped` | `None` | `()` | `public_evidence_not_available` |
| all allowed sections `not_applicable` (e.g. fund w/o single-company profile) | `skipped` | `skipped` | `None` | `()` | `public_evidence_not_applicable` |
| public-evidence assembly/provider failed (distinct from review state) | `unavailable` | `provider_unavailable` | `None` | `()` | `public_evidence_provider_unavailable` |
| generated narrative fails the output validator | `validation_failed` | `safety_validation_failed` | `None` (offending text never persisted) | `()` | `agent_output_failed_safety_validation` |
| blocked actionability gates all roles | `gated` | `skipped` | `None` | `()` | `blocked_actionability_llm_roles_skipped` |

Rules:
- **`limited` ≠ fresh.** A `limited`/`stale` section may be cited only with an
  explicit staleness/limitation note carried from `freshness_label`/
  `limitations`; the role must not present stale data as current.
- **Partial coverage is honest, not an error.** A `completed` role that could
  cite only some of its allowed sections must name what was unavailable, without
  defect or trading-readiness framing.
- **Distinguish review-state from provider-failure.** `not_reviewed`
  (rights/review not done) and `not_available` (reviewed but no data) are
  honest skips; `provider_unavailable` is an assembly failure. They get distinct
  warning codes so the report and frontend can be honest.
- **Validation failure is per-unit and fail-closed.** A single role failing
  validation degrades only that role; the report can still be
  `full_agent_report` with that role `validation_failed`. If every role/synthesis
  narrative fails, the report falls back to `validation_failed`
  (existing report-level behavior in `agent_team_report.py`).
- Today (default `not_reviewed` projection) all three public roles resolve to
  `skipped` with `no_reviewed_public_evidence` — the current shipped behavior —
  and the report remains `full_agent_report` from portfolio-aware roles.

## 7. Portfolio Manager Synthesis With Public Summaries

The PM role may consume **validated** public role summaries (its allowlist
already includes the public keys) and may reference public sections it is
allowed to cite. It must:

- treat public summaries as context, never as recommendations or a decision
  verdict; no "best path", allocation advice, or buy/sell/hold conclusion;
- state public-role coverage honestly (which public roles contributed vs.
  skipped/unavailable), reusing the role warning codes;
- introduce no new numbers/metrics and cite only sections in
  `PORTFOLIO_MANAGER_SYNTHESIS_EVIDENCE_KEYS` whose availability is
  `available`/`limited`.

When all public roles are skipped, synthesis notes the limited public coverage
and proceeds from the portfolio-aware roles only.

## 8. Report-Output Contract Changes

**No required additive fields.** The existing `SavedAgentTeamRoleSummaryRead`
shape (with `role_status`, `unavailable_reason`, section-key `evidence_references`)
is sufficient. Citations stay at section-key granularity; fact-level detail
lives in the sanitized narrative text, not in a new reference field — this keeps
the validator boundary simple and unchanged.

**Optional, additive, deferred (frontend convenience only):** a nullable
`public_evidence_coverage` descriptor on `SavedAgentTeamSummaryRead` (e.g.
counts/labels of contributed vs. skipped public roles) so the P29B-T4 frontend
need not infer coverage. If added it must be additive, backward-compatible,
default-null, derivable from `role_summaries`, and pass the existing validators.
Recommendation: derive coverage from `role_summaries` in T3/T4 and add this
field only if inference proves insufficient (carried from the P29A-T5 policy's
coverage-disclosure note).

**Two recommended validator tightenings for T3** (additive; close real gaps):

1. **Technical/levels guard.** `GENERATED_METRIC_PATTERNS` catches `$`/`%`/price
   target/Greeks/share-counts, but a bare-number invented level (e.g. "support
   at 145", "resistance near 160", "target of 172") may pass. Add a small
   additive pattern set for public/technical output rejecting
   support/resistance/price-target/level phrasing with adjacent bare numbers.
   The projection supplies no such numbers, so this only hardens against LLM
   invention.
2. **Excerpt/quote guard (news).** The projection contains no article bodies or
   URLs (the public-evidence validator strips them at the evidence layer, so the
   LLM has nothing to copy), and URLs are caught by existing patterns. As
   defense-in-depth, T3 may add a bounded-length / quote-ratio guard on
   `news_analyst` `summary_markdown` to reject long verbatim excerpts. Optional.

Both are additive hardening, not contract breaks.

## 9. How P29B-T3 Must Preserve evidence_package-Aware Validation

This is the load-bearing safety seam. T3 must follow all of the below:

1. **Always pass the package.** Keep the package-level call
   `validate_agent_team_report_output(payload, label=..., evidence_package=evidence)`
   on the full assembled report payload (role summaries + final synthesis +
   top-level `evidence_references`) before persistence, exactly as
   `agent_team_report.py:257` (`_validate_or_fallback`) does today. The per-model
   `SavedAgentTeamRoleSummaryRead` validator runs **without** the package, so it
   enforces role boundary but **not** availability; availability enforcement
   exists only at this package-level call. Dropping or bypassing it would let a
   public role cite a `not_reviewed`/`not_available` section.
2. **Same package for projection, validation, and persistence.** The
   `SavedEvidencePackageRead` used to build the public-role projections must be
   the **same** instance passed to the validator and the same one persisted /
   reproducible. If T3 introduces a non-default (synthetic reviewed) public
   provider, that populated `public_evidence` must flow into projection-building,
   the validator call, and the saved artifact. A mismatch (e.g. validating
   against the default `not_reviewed` package while projecting from a populated
   one) would wrongly reject valid citations — or, worse, wrongly accept them.
3. **Persist generation-time public sections for reproducibility.** Today
   `SavedEvidencePackageRead.from_saved_review_artifact` hardcodes
   `public_evidence = SavedPublicEvidencePackageRead.not_reviewed(...)`. For
   public roles to contribute *and* stay reproducible, T3 (with Codex C) must
   persist the generation-time public sections in the saved artifact and have
   `from_saved_review_artifact` read them back, **never** re-fetch or
   re-derive from a current provider on read. Reopening an old report must
   reproduce the same availability/freshness/citations it had at generation.
4. **Fail closed.** On any validation failure, withhold the offending narrative
   (`summary_markdown=None`), set the role/report to the `validation_failed`
   path, persist no offending text, and fall back to deterministic evidence —
   reuse the existing `_validate_or_fallback` / `_validation_failed_summary`
   behavior.

### 9.1 Clarifications for the T3 implementer (from review)

- `trade_intent_summary` (and `scope_state`/`freshness`/`actionability`) are
  package-level categories with no `section_key`/`availability`, so
  `_collect_section_availability` never records them and the availability gate
  never applies to them. That is why the shipped skipped-role builder can keep
  `evidence_references=("trade_intent_summary",)` even when every public section
  is `not_reviewed`. "Always citable" is **package-wide**, not public-role-wide:
  `ALWAYS_CITABLE_EVIDENCE_KEYS` includes `scope_state`/`freshness`/`actionability`,
  but those are not in any public role's allowlist, so public roles still cannot
  cite them — only `trade_intent_summary` is both always-citable and inside the
  public-role allowlists.
- Shape note: the per-model `SavedAgentTeamRoleSummaryRead` validator constructs
  a `role_sections`-shaped payload (no package) for the role-boundary check,
  whereas the package-level `_validate_or_fallback` call validates the real
  `role_summaries` + `final_synthesis` + top-level `evidence_references` **with**
  the package. Only the latter enforces availability — do not conflate the two.

## 10. Validation / Evaluation Plan (synthetic, offline, deterministic)

All cases use synthetic public evidence and the fake/offline provider only; no
real sources, no network. Two layers: (a) the `validate_agent_team_report_output`
gate (boundary, availability, wording, private-data, metrics), and (b) the
existing `agent_eval` faithfulness/boundary harness for narrative quality.

Positive cases (expected to pass and to produce the stated role_status):

- POS-1 Fundamentals available: `public_company_profile` + `public_fundamentals_snapshot`
  `available` → `completed`, cites exactly those keys (+ `trade_intent_summary`),
  neutral framing, zero metrics/advice.
- POS-2 News limited+stale: `public_news_snapshot` `limited`/`stale` +
  `public_events_calendar` `available` → `completed`, narrative notes staleness,
  cites both.
- POS-3 Technical available: `public_technical_context` + `public_market_context`
  `available` → `completed`, non-directional, cites both.
- POS-4 All not_reviewed (default today): all three public roles `skipped` with
  `no_reviewed_public_evidence`; PM synthesis notes limited public coverage;
  report stays `full_agent_report` from portfolio-aware roles.
- POS-5 Mixed: fundamentals `available`, news/technical `not_reviewed` →
  fundamentals `completed`, others `skipped`; coverage accurate.
- POS-6 PM synthesis with one validated public summary → neutral synthesis, no
  verdict, cites only allowed available sections.

Negative cases (must be rejected/fail closed):

- NEG-1 Boundary: `fundamentals_analyst` cites `public_news_snapshot` →
  rejected ("evidence outside the role boundary").
- NEG-2 Availability: any role cites a `not_reviewed`/`not_available` section
  while `evidence_package` is passed → rejected ("cites unavailable evidence").
- NEG-3 Invented metric: output contains `$210 price target` / `P/E of 15` /
  `+12%` → rejected by `GENERATED_METRIC_PATTERNS`.
- NEG-4 Advice wording: `you should buy` / `buy now` / `ready to trade` →
  rejected by `REPORT_PROHIBITED_PHRASES`.
- NEG-5 Source leak: a URL, article body, or `raw_payload`/`provider_response`
  token in output → rejected by private-value/forbidden-key patterns.
- NEG-6 Invented technical level: `support at 145` / `resistance near 160` →
  rejected by the recommended technical-levels guard (section 8.1).
- NEG-7 Provider-unavailable consistency: `provider_unavailable` role still
  carrying `summary_markdown` → coerced to `unavailable` with null narrative.
- NEG-8 Private data: account/holdings/quantity/balance token in public output
  → rejected by forbidden keys/value tokens.

Each case is a focused unit test over `validate_agent_team_report_output` and/or
the generation builder, plus `agent_eval` assertions on POS narratives. Default
suite is offline and deterministic.

## 11. Safety / Privacy Confirmations

- Public roles receive only their role-scoped sanitized projection +
  instrument context; never account/scope/portfolio fields, balances, holdings,
  positions, quantities, lots, transactions, orders, thresholds, IDs, raw
  payloads, URLs, article bodies, prompts, traces, or secrets.
- Citations restricted to the role's allowlist and to `available`/`limited`
  sections; enforced by the package-level validator call.
- Generated output passes `validate_saved_review_artifact_payload`,
  `validate_llm_provider_output`, and `REPORT_PROHIBITED_PHRASES`; advice/
  order/execution/guaranteed/safe-or-ready-to-trade/buy-sell wording rejected.
- PM synthesis uses validated public summaries as context only, never as
  recommendations or verdicts.
- Saved reports remain reproducible from generation-time evidence; no silent
  re-fetch or recomputation from current providers on read.
- No runtime agent tools, live web search, private MCP, broker tools, or
  TradingAgents execution introduced.

## 12. Codex B Review Result

Codex B review (review-only sub-agent, architecture/privacy/safety): **PASS**,
2026-06-15. No blockers, no important issues. All seven acceptance criteria were
verified line-by-line against the shipped P29B-T1 code:

- the per-role allowlists and section keys match `ROLE_ALLOWED_EVIDENCE_KEYS` /
  `SavedPublicEvidenceSectionKey` exactly;
- the degradation matrix uses only the five `AgentTeamReportRoleStatus` values
  and is fail-closed;
- availability is confirmed to be enforced only at the package-level
  `validate_agent_team_report_output(..., evidence_package=evidence)` call
  (`agent_team_report.py`), not at the per-model role-summary validator;
- the reproducibility finding is correct — `from_saved_review_artifact`
  hardcodes `public_evidence=not_reviewed`, so the T3 persist-generation-time
  requirement is necessary;
- no private data / unsafe wording / non-additive contract change is introduced.

Three review clarity notes were folded into section 9.1 (the
`trade_intent_summary` always-citable mechanism, the `role_sections` vs
`role_summaries` validator-shape difference, and "always citable is package-wide
not public-role-wide"). Plan status line applied to
`docs/shared/implementation_plan.md` P29B-T2.
