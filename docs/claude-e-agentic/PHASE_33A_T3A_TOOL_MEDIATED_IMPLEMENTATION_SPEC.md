# Phase 33A-T3A — Tool-Mediated Planner/Auditor Implementation Spec (for Codex C)

Status: implementation spec (design-to-implementation handoff; no code written here).
Owner of spec: Claude E. Implementer: Codex C. Reviewer: Codex B.
Approved input: P33A-T2 design (Codex B PASS),
`docs/claude-e-agentic/PHASE_33A_T2_PLANNER_AUDITOR_ROLE_DESIGN.md`.
Contract: `docs/codex-b-architecture/PHASE_33A_TOOL_MEDIATED_AGENT_TEAM_CONTRACT.md`.

This spec is precise enough to implement P33A-T3 without further design decisions.
It defines exact module layout, dataclasses, the `USABLE_CONTENT_BY_ROLE` map,
planner/role/auditor/synthesis behavior, the reduction to the existing saved
report schema, and a test matrix with expected outcomes.

---

## 0. Framing decisions (locked)

1. **T3 is fully deterministic — no LLM provider, no orchestrator, no prompts.**
   The planner, role-finding builders, auditor, and synthesis are pure Python
   over `ToolResult` envelopes. Claim text comes from digit-free, advice-free
   deterministic templates (the same style as the existing
   `_PUBLIC_ROLE_TEMPLATES` / `_risk_manager_markdown` in
   `agent_team_report.py`). Live-LLM prose is a later, separately gated slice.
   *Rationale:* "mock-first", "no live LLM", byte-stable tests. The value T3
   proves is the tool-mediated **plumbing + audit + real citation graph**, not
   model prose. (Codex B confirmation item — section 9.)
2. **Zero schema / read-contract change.** Output is the existing
   `SavedAgentTeamSummaryRead` / `SavedAgentTeamRoleSummaryRead`
   (`reports.py:302,334`). Reuse existing enum values only:
   `report_status="full_agent_report"`, `final_synthesis_authored_by=
   "deterministic_template"`, `run_status` / `role_status` from their existing
   Literals. `provider_mode` is a free `str` → use `"tool_mediated_mock"`.
3. **`planner` and `evidence_auditor` stay out of `AGENT_TEAM_ROLES`.** They are
   pure functions, never a `ToolRequest.requesting_role` or `ToolResult.role_name`.
   `options_structure_analyst` is **not** added.
4. **No persistence of tool-result envelopes / citation graph in T3.** They live
   in run-state only. Freezing into the saved package is **P33A-T4**. T3 persists
   only the existing `agent_summary` field (as the current builder already does),
   if wired into the route at all (the builder + tests are the T3 deliverable;
   route wiring may be a thin follow-up within T3 but must not change existing
   route behavior).
5. **Gaps are never citations.** The existing backstop `_validate_reference_set`
   (`report_output_safety.py:247`) rejects any `evidence_references` entry whose
   section availability ∉ {available, limited}. Therefore **a missing/unavailable
   section is surfaced as a `warning_code` + prose, never added to
   `evidence_references`.** `evidence_gap_inspector` output drives warning codes
   and prose, not citations.

---

## 1. File layout (small, reviewable)

Add **one** service module and **one** test module. Reuse everything else.

```
backend/app/services/agent_team/tool_mediated_report.py     # NEW (all T3 logic)
backend/tests/services/agent_team/test_tool_mediated_report.py  # NEW (test matrix)
```

Reused (imported, not modified):
- `tools.py`: `default_tool_registry`, `execute_tool_request`, `ToolRequest`,
  `ToolResult`, `validate_tool_payload`, `_unavailable_evidence_refs` (or
  re-derive the gappable set — see 4.3).
- `report_output_safety.py`: `validate_agent_team_report_output`,
  `ROLE_ALLOWED_EVIDENCE_KEYS`, `CANONICAL_EVIDENCE_KEYS`,
  `REPORT_PROHIBITED_PHRASES`, `INVENTED_LEVEL_PATTERNS`, `SOURCE_LEAK_PATTERNS`.
- `llm_provider.py`: `AGENT_TEAM_ROLES`, `validate_llm_provider_payload`,
  `find_forbidden_string_values`, `find_prohibited_llm_phrases`,
  `find_secret_like_values`.
- `roles.py`: `role_registry`, `role_definition`, `PUBLIC_ANALYST_ROLES`,
  `PORTFOLIO_AWARE_ROLES`.
- `privacy.py`: `find_forbidden_keys`, `FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS`.
- `reports/public_evidence.py`: `build_public_role_evidence_projection`
  (already enforces the public-role citable boundary + availability).
- `reports/agent_team_report.py`: `_validate_or_fallback` (reuse the exact
  fail-closed validation wrapper; if not importable cleanly, replicate its body
  verbatim into the new module).

Do **not** modify `agent_team_report.py`'s existing functions or external
behavior.

---

## 2. Public API (exact signatures)

```python
def build_tool_mediated_agent_team_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime | None = None,
    registry: dict[str, ToolRegistryEntry] | None = None,
    role_finding_override: Callable[[str, RoleFindingSet], RoleFindingSet] | None = None,
) -> SavedAgentTeamSummaryRead:
    """Deterministic, tool-mediated Agent Team report from saved evidence only."""
```

- `registry` defaults to `default_tool_registry()`.
- `role_finding_override` is a **test-only seam** (default `None`) used to inject
  a malformed/fixed finding to exercise the auditor re-pass; production callers
  never pass it.
- Returns a validated `SavedAgentTeamSummaryRead`; on any safety failure it
  returns the fail-closed `validation_failed` summary (reuse `_validate_or_fallback`).

Internal run-state entry point (also public for tests):

```python
def run_tool_mediated_agent_team(
    evidence: SavedEvidencePackageRead,
    *,
    registry: dict[str, ToolRegistryEntry],
    role_finding_override=None,
) -> ToolMediatedRunState: ...
```

---

## 3. Run-state dataclasses (exact fields, all `frozen=True`)

```python
@dataclass(frozen=True)
class EvidenceCatalogTool:
    tool_name: str
    display_name: str
    evidence_tier: str
    role_allowlist: tuple[str, ...]

@dataclass(frozen=True)
class EvidenceCatalogSection:
    section_key: str
    availability: str            # available | limited | not_available | not_reviewed | not_applicable
    evidence_tier: str           # public | agent_safe
    freshness_category: str | None   # category label only, never a timestamp/value
    caveat_codes: tuple[str, ...]

@dataclass(frozen=True)
class EvidenceCatalog:
    tools: tuple[EvidenceCatalogTool, ...]
    sections: tuple[EvidenceCatalogSection, ...]
    locked_question: str = "what_would_be_ignored"

@dataclass(frozen=True)
class PlannedToolRequest:
    tool_name: str
    args: dict[str, str]         # subset of TOOL_REQUEST_ARG_KEYS only

@dataclass(frozen=True)
class RolePlan:
    role_name: str
    tool_requests: tuple[PlannedToolRequest, ...]
    rationale_code: str

@dataclass(frozen=True)
class PlannerPlan:
    plan_version: str            # "p33a_plan_v1"
    dimensions: tuple[str, ...]
    role_plan: tuple[RolePlan, ...]

FindingType = Literal["ignored_risk", "missing_context", "contradiction", "open_question"]

@dataclass(frozen=True)
class RoleFinding:
    finding_type: FindingType
    claim_text: str              # qualitative, digit-free, advice-free
    evidence_refs: tuple[str, ...]
    caveat_codes: tuple[str, ...] = ()

@dataclass(frozen=True)
class RoleFindingSet:
    role_name: str
    role_status: str             # completed | skipped | unavailable | gated
    findings: tuple[RoleFinding, ...]
    warning_codes: tuple[str, ...]
    unavailable_reason: str | None = None

@dataclass(frozen=True)
class Contradiction:
    evidence_ref: str
    role_a: str
    role_b: str
    description: str

@dataclass(frozen=True)
class AuditorRecord:
    audit_version: str           # "p33a_audit_v1"
    role_verdicts: tuple[tuple[str, bool], ...]   # (role_name, citation_complete)
    contradictions: tuple[Contradiction, ...]
    dropped_claims: tuple[str, ...]   # reason-coded
    repass_triggered: bool
    eval_flags: tuple[str, ...]

@dataclass(frozen=True)
class ToolMediatedRunState:
    catalog: EvidenceCatalog
    plan: PlannerPlan
    tool_results: tuple[ToolResult, ...]
    audited_findings: tuple[RoleFindingSet, ...]
    auditor: AuditorRecord
    open_questions: tuple[str, ...]
```

Every dataclass that holds text must pass `validate_tool_payload` (privacy /
wording / invented-metric) in a `__post_init__` or at build boundaries.

---

## 4. Planner (exact behavior)

### 4.1 Catalog (input)

`build_evidence_catalog(evidence, registry) -> EvidenceCatalog`:
- `tools`: project each `ToolRegistryEntry` → `EvidenceCatalogTool` (name,
  display_name, tier, role_allowlist). **No execution.**
- `sections`: from `evidence`, emit one `EvidenceCatalogSection` per canonical
  section using **labels only** — `availability`, `evidence_tier`,
  `freshness_category` (a category string such as `fresh`/`stale`/`unknown`/
  `not_available`, **derived from the freshness label, never the raw timestamp /
  `as_of` / numeric value**), and `caveat_codes`. **Never** copy
  `summary_payload`, scope values, balances, or `as_of`.
- The whole catalog must pass `validate_tool_payload(asdict(catalog),
  label="evidence catalog")`.

### 4.2 `USABLE_CONTENT_BY_ROLE` (the single binding map)

Compute it (do not hardcode) so it cannot drift, then **pin it with a test**
(test U1). It is the intersection of *content-producible refs* and *citable refs*:

`usable_content[role] = content_receivable[role] ∩ ROLE_ALLOWED_EVIDENCE_KEYS[role]`

where `content_receivable[role]` = union of the **fixed** `evidence_refs` of the
non-gap tools the role may call (`entry.allows_role(role)`):

| tool | tier | fixed content evidence_refs |
| --- | --- | --- |
| trade_intent_summary | public | trade_intent_summary |
| portfolio_scope_context | agent_safe | scope_state |
| deterministic_review_findings | agent_safe | actionability, portfolio_impact_summary, concentration_risk_drift, liquidity_collateral_caveats, options_exposure_summary |
| broker_snapshot_freshness | agent_safe | freshness |
| market_quote_freshness | public | market_quote_freshness |
| public_company_profile | public | public_company_profile |
| evidence_gap_inspector | agent_safe | *(gap tool — contributes NO content refs; see 4.3)* |

**Pinned expected `usable_content` (test U1 asserts exactly this):**

```
fundamentals_analyst   = {trade_intent_summary, public_company_profile}
news_analyst           = {trade_intent_summary}
technical_analyst      = {trade_intent_summary, market_quote_freshness}
risk_management_agent  = {trade_intent_summary, scope_state, actionability, freshness,
                          portfolio_impact_summary, concentration_risk_drift,
                          liquidity_collateral_caveats, options_exposure_summary,
                          market_quote_freshness}
portfolio_manager_agent = {trade_intent_summary, scope_state, actionability, freshness,
                          portfolio_impact_summary, concentration_risk_drift,
                          liquidity_collateral_caveats, options_exposure_summary,
                          market_quote_freshness, public_company_profile}
```

Citable-but-toolless refs (`account_readiness`, `before_after_portfolio_impact`,
and the public snapshots `public_fundamentals_snapshot`, `public_news_snapshot`,
`public_events_calendar`, `public_technical_context`, `public_market_context`,
`economic_awareness_snapshot`, `market_mood_snapshot`) are **never cited** in T3;
their absence is surfaced as warning codes + prose only.

### 4.3 Gappable set (for warning codes, not citations)

`gappable_sections` = the section keys `evidence_gap_inspector` can report as
unavailable (re-derive from `_unavailable_evidence_refs` semantics): {
portfolio_impact_summary, before_after_portfolio_impact, concentration_risk_drift,
liquidity_collateral_caveats, options_exposure_summary, market_quote_freshness,
economic_awareness_snapshot, market_mood_snapshot, public_company_profile,
public_fundamentals_snapshot, public_news_snapshot, public_events_calendar,
public_technical_context, public_market_context }. These drive **warning codes**,
never `evidence_references`.

### 4.4 Plan output (deterministic)

`build_planner_plan(catalog) -> PlannerPlan`. Rules:
- Role order = `AGENT_TEAM_ROLES`. Tool order within a role = registry insertion
  order.
- For each non-PM role, include a tool **iff** it yields ≥1 ref in
  `usable_content[role]` (so `public_company_profile` is dropped for
  news/technical/risk; `market_quote_freshness` dropped for fundamentals).
- Always add `evidence_gap_inspector` to **`risk_management_agent`** (keystone
  "what's missing" tool; portfolio-aware, so allowed).
- `portfolio_manager_agent` plans **no tools** (`tool_requests=()`); it
  synthesizes from audited findings (its synthesis citations come from the union
  of other roles' audited refs — section 7).
- `dimensions` = `("risk_freshness", "scope_feasibility",
  "public_company_context", "public_market_context", "evidence_gaps")`.
- `args` use only `TOOL_REQUEST_ARG_KEYS`; default to `{}` (or
  `{"symbol_or_underlying": evidence.trade_intent_summary.symbol_or_underlying}`
  for `public_company_profile`).

**Pinned expected plan (test P3 asserts exactly this), tool counts in ():**

```
fundamentals_analyst    -> (trade_intent_summary, public_company_profile)            (2)
news_analyst            -> (trade_intent_summary,)                                   (1)
technical_analyst       -> (trade_intent_summary, market_quote_freshness)           (2)
risk_management_agent   -> (trade_intent_summary, portfolio_scope_context,
                            deterministic_review_findings, broker_snapshot_freshness,
                            market_quote_freshness, evidence_gap_inspector)          (6)
portfolio_manager_agent -> ()                                                        (0)
Total tool calls = 11
```

### 4.5 Caps (module constants)

```
MAX_TOOL_CALLS_PER_ROLE = 8     # risk uses 6
MAX_TOOL_CALLS_TOTAL    = 16    # plan uses 11
MAX_ROLES               = len(AGENT_TEAM_ROLES)  # 5
MAX_PLANNER_REPASSES    = 1
```

(This corrects the T2 memo's illustrative `4/16` to `8/16`, justified by the
actual plan: risk needs 6 content+gap tools.) The runner clamps any plan
exceeding caps; the deterministic plan never exceeds them.

---

## 5. Tool execution (runner)

For each `RolePlan`, for each `PlannedToolRequest`, build a `ToolRequest(
tool_name, requesting_role=role_name, args=...)` and call
`execute_tool_request(request, evidence=evidence, registry=registry)`. Collect
results into `tool_results`. Build the per-role **received-refs set** =
union of `result.evidence_refs` over that role's results **where
`result.availability ∈ {available, limited}`** (gap/unavailable results
contribute warning codes, not citable refs). The tier gate is already enforced
inside `execute_tool_request`; the runner re-asserts public roles received no
`agent_safe` result (defense in depth).

---

## 6. Role-finding builders (role by role)

`build_role_findings(role_name, role_results, evidence) -> RoleFindingSet`.
Common rules: every emitted `evidence_ref` must be in
`usable_content[role] ∩ received_refs(role)`; claim_text is templated, digit-free,
advice-free; an unavailable input becomes a warning code + prose, never a cited
ref.

### 6.1 Public roles (fundamentals, news, technical) — reuse the projection

Use `build_public_role_evidence_projection(evidence, role_name=role)` (it already
intersects `_PUBLIC_ROLE_SECTION_KEYS[role]` with `ROLE_ALLOWED_EVIDENCE_KEYS[role]`
and filters to available/limited). Then:
- `citable = projection.citable_section_keys`.
- If `citable` is empty → `role_status="skipped"`,
  `findings=()`, `evidence_references=("trade_intent_summary",)` (anchor),
  `warning_codes=(projection.degrade_reason or "<role>_public_context_unavailable",)`,
  `unavailable_reason=that code`. (Identical semantics to `_public_role_summary`.)
- Else → `role_status="completed"`; emit one `ignored_risk`/`missing_context`
  finding whose `claim_text` reuses the existing role template
  (`_PUBLIC_ROLE_TEMPLATES` / `_fundamentals_company_profile_markdown`) and whose
  `evidence_refs = ("trade_intent_summary", *citable)`; add
  `"public_evidence_limited"` warning if any cited section is `limited`.
- **news_analyst** on the standard full-evidence fixture has no citable public
  sections backed by a T1 tool → it lands in the `skipped` branch with
  `evidence_references=("trade_intent_summary",)` and a
  `public_news_context_unavailable`-style warning. This is the intended
  gap-reporting behavior (ratified in T2).

### 6.2 risk_management_agent (portfolio-aware, primary)

From its results, emit findings (each `ignored_risk` or `missing_context`):
1. **Deterministic risk flags** — claim cites `actionability`,
   `portfolio_impact_summary`, `concentration_risk_drift` (those present and
   available); template like the existing `_risk_manager_markdown` body.
2. **Freshness gaps** — claim cites `freshness` and/or `market_quote_freshness`;
   if `market_quote_freshness` is unavailable, do **not** cite it — emit warning
   `market_quote_freshness_unavailable` + the existing `_market_quote_gap_sentence`.
3. **Scope/feasibility** — claim cites `scope_state`; if
   `account_level_feasibility_evaluated` is false, add the existing
   `_account_feasibility_sentence`.
4. **Option-structure caveat** — claim cites `options_exposure_summary`; qualitative
   collateral/assignment/exercise/expiry framing, **no Greeks/number**. This keeps
   option-structure analysis under `risk_management_agent` (no new role).
5. **Evidence gaps** — from the `evidence_gap_inspector` result's
   `summary_payload["unavailable_evidence_refs"]`, emit `warning_codes` (one per
   unavailable section) + a single `missing_context` finding anchored on
   `trade_intent_summary`/`scope_state`; **do not cite** the unavailable refs.
- `role_status="completed"`; `warning_codes` = `evidence.caveat_codes` + gap codes.

### 6.3 portfolio_manager_agent (synthesizer) — see section 7.

---

## 7. Auditor + synthesis

### 7.1 `audit_findings(findings, received_refs_by_role) -> (AuditorRecord, audited_findings)`

For every finding of every role, in order, apply the six checks; a check failure
either **filters the offending ref** or **drops the finding**, recorded in
`dropped_claims` with a reason code:

1. **Citation completeness** — `finding.evidence_refs` non-empty and every ref ∈
   `received_refs(role)`. Missing-ref → drop (reason `unsupported_claim`).
2. **Citable-boundary** — every ref ∈ `usable_content[role]`. Out-of-boundary
   refs are **removed** from the finding (reason `citable_boundary_filtered`); if
   that empties the finding, drop it.
3. **Availability** — every cited ref's producing `ToolResult.availability ∈
   {available, limited}`. Else remove the ref (reason `unavailable_ref_filtered`).
4. **Private leak** — run `find_forbidden_keys(... TOOL_FORBIDDEN_KEYS)`,
   `find_forbidden_string_values`, `find_secret_like_values` over the finding.
   Any hit → **drop finding, never re-pass**, eval_flag `private_leak_blocked`.
5. **Advice/order/safe-to-trade** — `REPORT_PROHIBITED_PHRASES` +
   `TOOL_PROHIBITED_PHRASES` + `find_prohibited_llm_phrases`. Any hit → **drop,
   never re-pass**, eval_flag `advice_wording_blocked`.
6. **Invented number/level** — `TOOL_GENERATED_METRIC_PATTERNS` +
   `INVENTED_LEVEL_PATTERNS` + `SOURCE_LEAK_PATTERNS`. Any hit → **drop, never
   re-pass**, eval_flag `invented_metric_blocked`.

**Contradiction detection:** two roles emit findings on the **same
`evidence_ref`** with opposing stance (for T3, "opposing" = one finding caveat
set marks the ref fresh/available and another marks it stale/unavailable).
Record a `Contradiction`; **do not drop either**; convert to an `open_question`
string for synthesis. (On the deterministic golden path this does not occur —
all roles share frozen results — so it is exercised by a direct unit test, A7.)

**Bounded one-pass re-pass:** if any check 1–3 dropped/filtered a *fixable*
finding (not a leak/advice/number failure) **or** a contradiction was found, and
`repasses_used < MAX_PLANNER_REPASSES`, re-run the affected role's
`build_role_findings` **once** and re-audit. `role_finding_override` (test seam)
lets a test return a fixed finding on the second pass. After the single re-pass,
any still-failing finding is dropped and an eval_flag recorded. Checks 4–6 are
**never** re-passed.

### 7.2 Synthesis (portfolio_manager_agent)

`build_synthesis(audited_findings, open_questions, evidence) ->
(final_synthesis_markdown, synthesis_evidence_references, pm_role_summary)`:
- `synthesis_evidence_references = dedup(union of audited content refs across all
  roles) ∩ usable_content[portfolio_manager_agent]`, ordered by
  `CANONICAL_EVIDENCE_KEYS` iteration → stable. **It cannot introduce a ref no
  role surfaced.**
- `final_synthesis_markdown` = the four-bucket "what you'd be ignoring" text
  (reuse `_portfolio_manager_synthesis_markdown` shape): (a) deterministic risk
  flags, (b) data freshness/availability gaps, (c) scope/feasibility caveats, (d)
  unreviewed public context, + the manual-verification-checklist sentence + the
  "read-only context, not an instruction" sentence. Append `open_questions` as a
  neutral "open questions" clause (never a pick).
- The PM **role summary** (one of the five `role_summaries`) reuses the existing
  `_portfolio_manager_role_markdown` shape; its `evidence_references =
  synthesis_evidence_references`.

---

## 8. Reduction to the existing saved schema (exact mapping)

`RoleFindingSet -> SavedAgentTeamRoleSummaryRead`:

| target field | value |
| --- | --- |
| role_name | `role_name` |
| display_name | `role_definition(role_name).display_name` |
| role_status | `role_status` (completed/skipped/unavailable/gated) |
| provider_status | `"ok"` if completed else `"skipped"`/`"provider_unavailable"` |
| summary_markdown | findings rendered to one markdown string; `None` if skipped/unavailable |
| evidence_references | dedup(union of surviving `finding.evidence_refs`), ordered by `CANONICAL_EVIDENCE_KEYS` |
| warning_codes | `warning_codes` (caveat + gap + eval) |
| unavailable_reason | `unavailable_reason` |

`ToolMediatedRunState -> SavedAgentTeamSummaryRead`:

| target field | value |
| --- | --- |
| run_status | `"completed"` if all 5 role_status=="completed" else `"partially_completed"`; `"failed"` on validation fallback |
| provider_mode | `"tool_mediated_mock"` |
| report_generated_at | `report_generated_at` |
| role_summaries | the 5 reduced summaries, in `AGENT_TEAM_ROLES` order |
| warning_codes | top-level coverage code (reuse `_public_coverage_code` semantics) + run eval_flags |
| report_status | `"full_agent_report"` on success; `"deterministic_draft"` if actionability blocked (parity with `_deterministic_draft_summary`); `"validation_failed"` on safety fallback |
| final_synthesis_markdown | synthesis markdown; `None` on blocked/failed |
| final_synthesis_authored_by | `"deterministic_template"` |
| evidence_schema_version | `evidence.evidence_schema_version` |
| evidence_references | `synthesis_evidence_references` |

Final guard: pass the assembled `payload` through the **reused**
`_validate_or_fallback(payload, evidence, report_generated_at=...)` so the
behavior is identical to the existing builder — on any
`validate_agent_team_report_output` failure it returns the `validation_failed`
summary (fail closed, no leak).

Blocked-actionability path: if
`evidence.actionability.review_actionability_status.startswith("blocked_")`,
**skip the tool-mediated run** and return the existing
`_deterministic_draft_summary(evidence, ...)` (import/reuse) — exact parity, no
new behavior.

---

## 9. Codex B decision still needed before Codex C starts

Only **one** substantive confirmation; the rest are restatements of T2 PASS:

- **D1 (confirm): T3 roles/synthesis are deterministic templates (no LLM
  provider).** Section 0.1. The contract says "mock-first"; T2 deferred live-LLM
  prose. This spec assumes deterministic. If Codex B wants the mock **LLM
  provider** wired instead, the role-finding builders change to provider calls
  (still no live provider) and tests lose byte-stability — a materially different
  T3. Recommend confirming deterministic.

Low-risk confirmations (already implied by T2 PASS; flag only):
- D2: reuse `report_status="full_agent_report"` + `authored_by=
  "deterministic_template"` + `provider_mode="tool_mediated_mock"` (no enum
  change).
- D3: gaps surfaced via warning_codes + prose, never `evidence_references`
  (forced by `_validate_reference_set`).
- D4: `USABLE_CONTENT_BY_ROLE` pinned values (section 4.2) are the binding map.

---

## 10. Test matrix for Codex C (exact cases + expected outcomes)

All offline/deterministic. Use a synthetic `SavedEvidencePackageRead` fixture
with full available portfolio sections + a `public_company_profile` available;
a second fixture with `public_evidence=None`; a third with
`review_actionability_status` blocked; a fourth with
`market_quote_freshness.availability="not_available"`.

**Map / catalog**
- U1: `usable_content_by_role()` equals the pinned section-4.2 dict exactly.
- C1: `build_evidence_catalog` passes `validate_tool_payload`; contains no
  `summary_payload`, no `as_of`, no balance/scope values. Injecting a forbidden
  token into a section label raises.

**Planner**
- P1: `build_planner_plan(catalog)` is deterministic — two calls return equal
  `PlannerPlan`.
- P2: role order == `AGENT_TEAM_ROLES`; per-role tool order == registry order.
- P3: plan equals the pinned section-4.4 plan exactly (incl. PM == `()`,
  `evidence_gap_inspector` in risk only, total == 11).
- P4: no role plans a tool yielding only non-usable refs — assert
  `public_company_profile ∉` news/technical/risk plans;
  `market_quote_freshness ∉` fundamentals plan.
- P5: caps respected — every role ≤ 8 tools, total ≤ 16.

**Roles**
- R1: for every role, `finding.evidence_refs ⊆ usable_content[role] ∩
  received_refs(role)` and every cited ref's result availability ∈
  {available,limited}.
- R2 (news gap): news `role_status=="skipped"`,
  `evidence_references==("trade_intent_summary",)`, a
  `*_public_context_unavailable` warning code, and **no**
  `public_company_profile`/`market_quote_freshness` citation.
- R3 (option caveat): risk findings include a claim citing
  `options_exposure_summary`; `TOOL_GENERATED_METRIC_PATTERNS` find nothing in
  risk claim_text (no Greeks/number).
- R4 (tier): no public role's received results contain
  `evidence_tier=="agent_safe"`. A `ToolRequest("portfolio_scope_context",
  requesting_role="news_analyst")` through `execute_tool_request` returns a
  `blocked` result (already true in T1; assert it).
- R5 (public_evidence=None): fundamentals degrades to `skipped` with
  `("trade_intent_summary",)` only; no crash.

**Auditor**
- A1: empty-`evidence_refs` finding → dropped (`unsupported_claim`); a finding
  citing a never-received ref → dropped.
- A2: inject (via `role_finding_override`) a risk finding citing
  `public_company_profile` → ref filtered out (`citable_boundary_filtered`);
  finding dropped if emptied.
- A3: inject a finding citing a ref whose result availability is `not_available`
  → ref filtered (`unavailable_ref_filtered`).
- A4: claim_text containing `buying_power` → finding dropped,
  `private_leak_blocked` eval_flag, `repass_triggered` stays False.
- A5: claim_text `you should buy` and `safe to trade` → dropped,
  `advice_wording_blocked`, no re-pass.
- A6: claim_text `$1,200`, `30%`, `support at 45` (separate cases) → dropped,
  `invented_metric_blocked`, no re-pass.
- A7 (contradiction): two synthetic `RoleFindingSet`s with opposing stance on the
  same `evidence_ref` → `AuditorRecord.contradictions` length 1; both findings
  survive; an `open_question` string is produced.
- A8 (re-pass): `role_finding_override` returns a malformed finding on pass 1 and
  a valid one on pass 2 → `repass_triggered True`, `repasses_used==1`, final
  findings include the fixed claim. A permanently-malformed finding → dropped
  after exactly one re-pass with an eval_flag.

**Synthesis**
- S1: `synthesis_evidence_references ⊆ dedup(union audited refs) ∩
  usable_content[portfolio_manager_agent]`; with a stubbed union of only
  `{trade_intent_summary, scope_state}`, synthesis refs ⊆ that set.
- S2: synthesis markdown contains the four buckets + manual-verification sentence
  + the "not an instruction" sentence; passes `validate_agent_team_report_output`.
- S3: an A7 contradiction surfaces as an "open questions" clause in synthesis,
  not a chosen side.

**End-to-end / safety / determinism**
- E1: `build_tool_mediated_agent_team_summary(full_fixture)` →
  `run_status=="completed"`, `report_status=="full_agent_report"`,
  `provider_mode=="tool_mediated_mock"`,
  `final_synthesis_authored_by=="deterministic_template"`; passes
  `validate_agent_team_report_output(payload, label=..., evidence_package=
  full_fixture)` (backstop never raises).
- E2: byte-stable — two builds (same fixture, same `report_generated_at`) →
  equal `model_dump(mode="json")`.
- E3: recursive `find_forbidden_keys` + `find_forbidden_string_values` +
  `find_secret_like_values` over plan, all `tool_results`, all
  `audited_findings`, `auditor`, and the final payload → all empty.
- E4: blocked-actionability fixture → `report_status=="deterministic_draft"`,
  all roles `gated`, parity with existing `_deterministic_draft_summary`.
- E5: `market_quote_freshness` unavailable fixture → that ref never appears in
  any `evidence_references`; risk emits `market_quote_freshness_unavailable`
  warning; report still `full_agent_report`.
- E6: feed an unsafe injected finding through the full builder →
  `_validate_or_fallback` returns the `validation_failed` summary
  (`report_status=="validation_failed"`, `role_summaries==()`, no leak).

---

## 11. Hard constraints (block on violation)

- Use existing saved evidence only. No live providers, new sources, web, EDGAR
  fetch, MCP, TradingAgents runtime, or LangGraph.
- No schema / read-contract change. Reuse existing enum values. `planner` /
  `evidence_auditor` stay out of `AGENT_TEAM_ROLES`; `options_structure_analyst`
  not added.
- No persistence/freeze of tool envelopes (that is T4). No frontend work.
- No raw account/provider/broker data, balances, holdings, positions,
  quantities, lots, payloads, URLs, prompts, traces, secrets, or logs anywhere.
- Deterministic backend owns all numbers; findings cite refs, never reproduce
  numbers/levels/Greeks/probabilities.
- No advice/recommendation/order/execution/safe-or-ready-to-trade/
  guaranteed-return wording. Existing `agent_team_report.py` external behavior
  must not change.

---

## 12. Return summary

- **Status: PASS** — ready for Codex C implementation, pending Codex B
  confirmation **D1** (deterministic vs mock-LLM). D2–D4 are restatements of the
  T2 PASS and need only acknowledgement.
- **Spec scope:** one new service module + one new test module; zero schema
  change; deterministic; reuses the T1 tool layer, the public-evidence
  projection, and the existing validation/fallback wrapper.
- **Open risks:** (R-a) if D1 flips to mock-LLM, the role/synthesis builders and
  byte-stability tests change — re-spec needed; (R-b) `usable_content` drift if
  either source map changes — mitigated by the pinned U1 test.
