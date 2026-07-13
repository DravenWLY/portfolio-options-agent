"""Tool-mediated Agent Team runner (relocated from tool_mediated_report, P34A-T11E).

Catalog + deterministic planner + backend tool execution + role findings +
live-prose overlay + PM synthesis + summary/freeze assembly. Delegates the
Evidence Auditor to ``auditing.evidence_auditor`` and shares dataclasses via
``orchestration.models``. No behavior change from the pre-split module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import re
from time import monotonic
from typing import Callable, Literal

from app.schemas.reports import (
    SavedAgentTeamRoleSummaryRead,
    SavedAgentTeamSummaryRead,
    SavedEvidencePackageRead,
    SavedToolMediatedRunArtifactRead,
    validate_saved_tool_freeze_payload,
)
from app.services.agent_team.llm_clients.contracts import (
    AGENT_TEAM_ROLES,
    AgentTeamRole,
    LLMProvider,
    LLMProviderMessage,
    LLMProviderRequest,
    LLMProviderResponse,
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
    register_static_system_prompts,
)
from app.services.agent_team.safety.output_safety import validate_llm_provider_output
from app.services.agent_team.llm_clients.factory import LLMProviderResolution
from app.services.agent_team.safety.report_output_safety import (
    INVENTED_LEVEL_PATTERNS,
    REPORT_PROHIBITED_PHRASES,
    ROLE_ALLOWED_EVIDENCE_KEYS,
    SOURCE_LEAK_PATTERNS,
)
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES, role_definition
from app.services.agent_team.tools import (
    TOOL_FORBIDDEN_KEYS,
    TOOL_GENERATED_METRIC_PATTERNS,
    TOOL_PROHIBITED_PHRASES,
    SEC_RAW_PATH_OR_FILE_RE,
)
from app.services.agent_team.tools import (
    ToolRegistryEntry,
    ToolRequest,
    ToolResult,
    blocked_tool_result,
    default_tool_registry,
    execute_tool_request,
    validate_tool_payload,
)
from app.services.market_data.eod_history import (
    MarketContextExecutionContext,
    default_market_context_execution_context,
)
from app.services.privacy import find_forbidden_keys
from app.services.reports.agent_team_report import _deterministic_draft_summary, _validate_or_fallback
from app.services.reports.display_labels import (
    FACT_DISPLAY_LABELS,
    display_label_for_code,
    display_label_for_section,
    display_labels_for_codes,
    find_internal_display_tokens,
    replace_internal_display_tokens,
    render_display_list,
)
from app.services.reports.public_evidence import build_public_role_evidence_projection



from app.services.agent_team.orchestration.models import *  # noqa: F401,F403
from app.services.agent_team.auditing.evidence_auditor import audit_findings
from app.services.agent_team.auditing.live_report_gates import (
    freshness_category_from_label,
    prompt_fact_labels_for_tool_result,
)
from app.services.agent_team.auditing.v3_value_gates import (
    P36_ARTIFACT_SCHEMA_VERSION,
    P36_ROLE_PROMPT_VERSION,
)
from app.services.agent_team.orchestration.p36_risk_prompt import P36_RISK_SYSTEM_PROMPT

LIVE_ROLE_SYSTEM_PROMPT_TEMPLATE = (
    "You are {role_display_name} on a read-only portfolio review team. A\n"
    "deterministic system has already written every number, table, and threshold\n"
    "in this report. You add exactly one short note of sentence-level context on\n"
    "top of it. Your note answers one question only: what would a manual reviewer\n"
    "acting right now overlook in the saved evidence?\n"
    "\n"
    "{role_block}\n"
    "\n"
    "Output shape: exactly one note of two to four plain-language sentences.\n"
    "Plain prose only — no headings, no tables, no lists, no bullets, no field\n"
    "names, no code words, no words joined with underscores. When something is\n"
    "absent, say \"not reviewed\" or \"not available\" in plain words; caveat codes\n"
    "are not categories.\n"
    "\n"
    "Numbers: either copy a number character-for-character from a supplied\n"
    "envelope value, or write no number at all. Never compute, convert,\n"
    "aggregate, estimate, round, or combine values into a new number. Do not\n"
    "write dollar signs or percent signs. Use freshness and availability words\n"
    "only exactly as the envelopes categorize each item.\n"
    "\n"
    "Never name the reviewed instrument, the account, or any user-specific\n"
    "label. Never describe the size of the portfolio, a position, exposure,\n"
    "allocation, or cash — not in digits, not in words, not by comparison.\n"
    "Describe saved evidence only: no advice, no action instructions other than\n"
    "plain verification steps, no urgency, no ranking, no predictions, no target\n"
    "prices, no support or resistance levels, no filing interpretation, no macro\n"
    "interpretation, no likelihood or probability claims, no return, payout, or\n"
    "break-even figures, no verdicts, no links."
)

LIVE_ROLE_PROMPT_BLOCKS: dict[str, str] = {
    "technical_analyst": (
        "Your note appears under the report's \"Market context\" heading, directly\n"
        "below a deterministic table of saved end-of-day values for the reviewed\n"
        "symbol. Your expertise is reading saved price context: where the latest\n"
        "close sits in the saved 52-week range and relative to its saved moving\n"
        "averages, using only the relationship labels and values already in your\n"
        "envelopes, such as \"above the 200-day average\". Connect two or three of\n"
        "those saved relationships into one plain observation that a reviewer\n"
        "glancing only at today's price would miss, and state the freshness category\n"
        "of the saved values exactly as your envelopes give it. Do not describe\n"
        "trends continuing, momentum building, or what prices may do next."
    ),
    "risk_management_agent": (
        "Your note appears under the report's \"Risk and scope notes\" heading, below\n"
        "a deterministic list of saved caveats and scope limits. Your expertise is\n"
        "judging which saved caveats most affect trust in this review's inputs. Pick\n"
        "the one or two caveats from your envelopes that a reviewer would most\n"
        "regret overlooking — for example that holdings figures come from a saved\n"
        "sync rather than a live connection, or that quote freshness is manual — and\n"
        "say in plain words what each one means for reading this report. Your\n"
        "envelopes carry no numeric values, so your note contains no numbers. End\n"
        "with one plain verification step in the imperative, such as \"re-verify the\n"
        "exposure math at your broker before relying on it\"."
    ),
    "fundamentals_analyst": (
        "Your note appears under the report's \"Company context\" heading, below a\n"
        "deterministic summary of which public company facts were reviewed. Your\n"
        "expertise is naming what reviewed public company context is present and\n"
        "what is absent, using only the profile facts, snapshot categories, and\n"
        "freshness categories in your envelopes. Connect that presence or absence\n"
        "into one plain observation about what a reviewer relying on price alone\n"
        "would miss. Describe what was reviewed or not reviewed only; do not\n"
        "evaluate the company or interpret what any fact means for it."
    ),
    "news_analyst": (
        "Your note appears under the report's \"Events and filings context\" heading,\n"
        "below a deterministic list of reviewed filing and release metadata. Your\n"
        "expertise is reading that metadata trail: which filing form types, filing\n"
        "dates, release names, and release dates exist in the saved evidence, and\n"
        "which context is absent, using only the metadata in your envelopes. Connect\n"
        "that presence or absence into one plain observation about what a reviewer\n"
        "would miss by not checking the public record. Metadata only: do not\n"
        "describe, guess at, or interpret the contents of any filing or release."
    ),
}


def _live_role_prompt_block(role_name: str) -> str:
    """Return the approved role prompt block or fail closed for every unmapped role."""

    try:
        return LIVE_ROLE_PROMPT_BLOCKS[role_name]
    except KeyError as exc:
        raise ValueError(f"unmapped live role prompt block: {role_name}") from exc


def _render_live_role_system_prompt(role_name: str) -> str:
    role_block = _live_role_prompt_block(role_name)
    role = role_definition(role_name)  # type: ignore[arg-type]
    return LIVE_ROLE_SYSTEM_PROMPT_TEMPLATE.format(
        role_display_name=role.display_name,
        role_block=role_block,
    )


LIVE_ROLE_SYSTEM_PROMPTS = frozenset(
    _render_live_role_system_prompt(role_name) for role_name in LIVE_ROLE_PROMPT_BLOCKS
)
register_static_system_prompts(LIVE_ROLE_SYSTEM_PROMPTS)

# P35 keeps the public-role blocks registered for reviewed future activation,
# but only Technical and Risk are live-enabled on the legacy connective path.
# P36 Risk uses its own branch below and does not consult this allowlist.
LEGACY_LIVE_ROLE_ALLOWLIST = frozenset({"technical_analyst", "risk_management_agent"})



def build_evidence_catalog(
    evidence: SavedEvidencePackageRead,
    registry: dict[str, ToolRegistryEntry] | None = None,
) -> EvidenceCatalog:
    active_registry = registry or default_tool_registry()
    tools = tuple(
        EvidenceCatalogTool(
            tool_name=entry.tool_name,
            display_name=entry.display_name,
            evidence_tier=entry.evidence_tier,
            role_allowlist=tuple(entry.role_allowlist),
        )
        for entry in active_registry.values()
    )
    sections = (
        EvidenceCatalogSection(
            section_key="trade_intent_summary",
            availability="available",
            evidence_tier="public",
            freshness_category=None,
            caveat_codes=(),
        ),
        EvidenceCatalogSection(
            section_key="scope_state",
            availability="available",
            evidence_tier="agent_safe",
            freshness_category=None,
            caveat_codes=evidence.scope_state.scope_caveat_codes,
        ),
        EvidenceCatalogSection(
            section_key="freshness",
            availability="available",
            evidence_tier="agent_safe",
            freshness_category=_freshness_category(evidence.freshness.broker_snapshot_freshness_label),
            caveat_codes=(),
        ),
        EvidenceCatalogSection(
            section_key="actionability",
            availability="available",
            evidence_tier="agent_safe",
            freshness_category=None,
            caveat_codes=(),
        ),
        *tuple(_catalog_section_for_saved_section(section, tier="agent_safe") for section in _agent_safe_sections(evidence)),
        *tuple(_catalog_section_for_public_section(section) for section in _public_sections(evidence)),
    )
    return EvidenceCatalog(tools=tools, sections=sections)


def build_planner_plan(catalog: EvidenceCatalog) -> PlannerPlan:
    registry_order = tuple(tool.tool_name for tool in catalog.tools)
    role_plans: list[RolePlan] = []
    usable = usable_content_by_role(_registry_from_catalog(catalog))
    for role in AGENT_TEAM_ROLES:
        requests: list[PlannedToolRequest] = []
        if role != "portfolio_manager_agent":
            for tool_name in registry_order:
                refs = TOOL_FIXED_CONTENT_REFS.get(tool_name, ())
                if refs and set(refs).intersection(usable[role]):
                    requests.append(PlannedToolRequest(tool_name=tool_name, args={}))
            if role == "risk_management_agent":
                requests.append(PlannedToolRequest(tool_name="evidence_gap_inspector", args={}))
        role_plans.append(
            RolePlan(
                role_name=role,
                tool_requests=tuple(requests[:MAX_TOOL_CALLS_PER_ROLE]),
                rationale_code=f"{role}_usable_evidence_plan",
            )
        )
    clamped = tuple(role_plans[:MAX_ROLES])
    total = 0
    final_plans: list[RolePlan] = []
    for role_plan in clamped:
        remaining = MAX_TOOL_CALLS_TOTAL - total
        requests = role_plan.tool_requests[: max(0, remaining)]
        total += len(requests)
        final_plans.append(
            RolePlan(
                role_name=role_plan.role_name,
                tool_requests=requests,
                rationale_code=role_plan.rationale_code,
            )
        )
    return PlannerPlan(plan_version=PLAN_VERSION, dimensions=PLAN_DIMENSIONS, role_plan=tuple(final_plans))


def run_tool_mediated_agent_team(
    evidence: SavedEvidencePackageRead,
    *,
    registry: dict[str, ToolRegistryEntry],
    role_finding_override: Callable[[str, RoleFindingSet], RoleFindingSet] | None = None,
    llm_provider: LLMProvider | None = None,
    live_provider_enabled: bool = False,
    p36_risk_live_enabled: bool = False,
    market_context: MarketContextExecutionContext | None = None,
) -> ToolMediatedRunState:
    catalog = build_evidence_catalog(evidence, registry)
    plan = build_planner_plan(catalog)
    active_market_context = market_context or default_market_context_execution_context()
    tool_results: list[ToolResult] = []
    by_role: dict[str, tuple[ToolResult, ...]] = {}
    for role_plan in plan.role_plan:
        role_results: list[ToolResult] = []
        for planned in role_plan.tool_requests:
            result = execute_tool_request(
                ToolRequest(tool_name=planned.tool_name, requesting_role=role_plan.role_name, args=planned.args),
                evidence=evidence,
                registry=registry,
                market_context=active_market_context,
            )
            if role_plan.role_name in PUBLIC_ANALYST_ROLES and result.evidence_tier == "agent_safe":
                result = execute_tool_request(
                    ToolRequest(tool_name="not_allowed", requesting_role=role_plan.role_name),
                    evidence=evidence,
                    registry=registry,
                    market_context=active_market_context,
                )
            role_results.append(result)
            tool_results.append(result)
        by_role[role_plan.role_name] = tuple(role_results)

    if p36_risk_live_enabled:
        # The legacy P33A planner has a smaller global cap and can starve the
        # last role. P36 Risk receives this fixed, reviewed envelope floor
        # before it enters its own bounded calculation loop.
        risk_results = list(by_role.get("risk_management_agent", ()))
        present_tools = {result.tool_name for result in risk_results}
        for tool_name in P36_RISK_BASELINE_TOOLS:
            if tool_name in present_tools:
                continue
            result = execute_tool_request(
                ToolRequest(tool_name=tool_name, requesting_role="risk_management_agent"),
                evidence=evidence,
                registry=registry,
                market_context=active_market_context,
            )
            risk_results.append(result)
            tool_results.append(result)
        by_role["risk_management_agent"] = tuple(risk_results)

    raw_findings = tuple(
        build_role_findings(role, by_role.get(role, ()), evidence) for role in AGENT_TEAM_ROLES if role != "portfolio_manager_agent"
    )
    provider_mode = PROVIDER_MODE
    provider_runs: list[ProviderRunMeta] = []
    if p36_risk_live_enabled and llm_provider is not None:
        provider_mode = LIVE_PROVIDER_MODE
        p36_findings: list[RoleFindingSet] = []
        for finding in raw_findings:
            if finding.role_name != "risk_management_agent":
                p36_findings.append(finding)
                continue
            live_finding, loop_results, loop_runs = _run_p36_risk_loop(
                finding,
                by_role.get("risk_management_agent", ()),
                evidence=evidence,
                registry=registry,
                provider=llm_provider,
                market_context=active_market_context,
            )
            p36_findings.append(live_finding)
            if loop_results:
                by_role["risk_management_agent"] = (*by_role.get("risk_management_agent", ()), *loop_results)
                tool_results.extend(loop_results)
            provider_runs.extend(loop_runs)
        raw_findings = tuple(p36_findings)
    elif live_provider_enabled and llm_provider is not None:
        provider_mode = LIVE_PROVIDER_MODE
        live_findings: list[RoleFindingSet] = []
        for finding in raw_findings:
            if (
                finding.role_name not in LEGACY_LIVE_ROLE_ALLOWLIST
                or _sec_event_finding_stays_deterministic(finding)
                or _fred_economic_finding_stays_deterministic(finding)
            ):
                live_findings.append(finding)
                continue
            live_result = _live_provider_role_findings(
                finding,
                by_role.get(finding.role_name, ()),
                provider=llm_provider,
            )
            live_findings.append(live_result.finding_set)
            if live_result.provider_run is not None:
                provider_runs.append(live_result.provider_run)
        raw_findings = tuple(live_findings)
    if role_finding_override is not None:
        raw_findings = tuple(role_finding_override(finding.role_name, finding) for finding in raw_findings)
    received = _received_refs_by_role(by_role)
    audit = audit_findings(raw_findings, by_role, received, p36_risk_mode=p36_risk_live_enabled)
    audited_findings = audit[1]
    auditor = audit[0]
    open_questions = _open_questions_from_contradictions(auditor.contradictions)

    if auditor.repass_triggered and role_finding_override is not None:
        repass_findings = tuple(role_finding_override(finding.role_name, finding) for finding in audited_findings)
        repass_auditor, audited_findings = audit_findings(
            repass_findings,
            by_role,
            received,
            repass=True,
            p36_risk_mode=p36_risk_live_enabled,
        )
        auditor = AuditorRecord(
            audit_version=AUDIT_VERSION,
            role_verdicts=repass_auditor.role_verdicts,
            contradictions=repass_auditor.contradictions,
            dropped_claims=tuple(dict.fromkeys((*auditor.dropped_claims, *repass_auditor.dropped_claims))),
            repass_triggered=True,
            eval_flags=tuple(dict.fromkeys((*auditor.eval_flags, *repass_auditor.eval_flags))),
        )
        open_questions = _open_questions_from_contradictions(auditor.contradictions)

    pm_finding = _portfolio_manager_finding_set(audited_findings, open_questions)
    return ToolMediatedRunState(
        catalog=catalog,
        plan=plan,
        tool_results=tuple(tool_results),
        audited_findings=(*audited_findings, pm_finding),
        auditor=auditor,
        open_questions=open_questions,
        provider_mode=provider_mode,
        provider_runs=tuple(provider_runs),
    )


def build_role_findings(
    role_name: str,
    role_results: tuple[ToolResult, ...],
    evidence: SavedEvidencePackageRead,
) -> RoleFindingSet:
    if role_name in PUBLIC_ANALYST_ROLES:
        return _public_role_findings(role_name, role_results, evidence)
    if role_name == "risk_management_agent":
        return _risk_role_findings(role_results, evidence)
    return RoleFindingSet(
        role_name=role_name,
        role_status="skipped",
        findings=(),
        warning_codes=("role_not_planned",),
        unavailable_reason="role_not_planned",
    )


P36_RISK_CALC_TOOLS = frozenset(
    {
        "calc_exposure_delta",
        "calc_concentration_metrics",
        "calc_cash_impact",
        "calc_option_structure",
        "calc_scenario_exposure",
        "calc_freshness_inventory",
    }
)
P36_RISK_CALC_TOOL_IDS = {
    "C1": "calc_exposure_delta",
    "C2": "calc_concentration_metrics",
    "C3": "calc_cash_impact",
    "C4": "calc_option_structure",
    "C5": "calc_scenario_exposure",
    "C15": "calc_freshness_inventory",
}
P36_RISK_BASELINE_TOOLS = (
    "trade_intent_summary",
    "portfolio_scope_context",
    "deterministic_review_findings",
    "broker_snapshot_freshness",
    "market_quote_freshness",
    "evidence_gap_inspector",
)
# These aliases make the Risk-only loop readable while keeping the Tier 1
# configuration in orchestration.models for the later multi-role run.
P36_RISK_MAX_ITERATIONS = P36_RISK_MAX_PROVIDER_CALLS


def _run_p36_risk_loop(
    deterministic: RoleFindingSet,
    initial_results: tuple[ToolResult, ...],
    *,
    evidence: SavedEvidencePackageRead,
    registry: dict[str, ToolRegistryEntry],
    provider: LLMProvider,
    market_context: MarketContextExecutionContext,
) -> tuple[RoleFindingSet, tuple[ToolResult, ...], tuple[ProviderRunMeta, ...]]:
    """Run the bounded, backend-mediated P36 Risk loop without tool bindings."""

    if deterministic.role_status == "skipped" or not deterministic.findings:
        return deterministic, (), ()
    evidence_refs = _ordered_refs(_union_refs(deterministic.findings))
    if not evidence_refs:
        return deterministic, (), ()

    loop_results: list[ToolResult] = []
    provider_runs: list[ProviderRunMeta] = []
    consecutive_refusals = 0
    reserved_tokens = 0
    started_at = monotonic()
    provider_call_cap = min(P36_RISK_MAX_ITERATIONS, P36_LLM_CALLS_HARD_CAP)
    tool_request_cap = min(P36_RISK_MAX_TOOL_REQUESTS, P36_TOOL_REQUESTS_HARD_CAP)
    for iteration in range(1, provider_call_cap + 1):
        if monotonic() - started_at > P36_RISK_WALL_CLOCK_SECONDS:
            return _live_provider_fallback(deterministic, "unavailable"), tuple(loop_results), tuple(provider_runs)
        role_results = (*initial_results, *loop_results)
        request: LLMProviderRequest | None = None
        try:
            request = _p36_risk_provider_request(
                role_results,
                evidence_refs=evidence_refs,
                provider=provider,
                iteration=iteration,
            )
            reserved_tokens += request.max_tokens
            if reserved_tokens > P36_RISK_TOKEN_CEILING:
                return _live_provider_fallback(deterministic, "safety_fallback"), tuple(loop_results), tuple(provider_runs)
            response = provider.complete(request)
            response_payload = _provider_response_payload(response)
            provider_runs.append(_provider_run_meta(response_payload, fallback_request=request))
            status = str(response_payload.get("status") or "failed")
            if status != "ok" or response_payload.get("finish_reason") == "length":
                return _live_provider_fallback(deterministic, "unavailable"), tuple(loop_results), tuple(provider_runs)
            content = str(response_payload.get("content_markdown") or "").strip()
            parsed = _parse_p36_risk_response(content)
            if parsed is None:
                loop_results.append(
                    blocked_tool_result(
                        tool_name="calc_request_refused",
                        role_name="risk_management_agent",
                        evidence_tier="agent_safe",
                    )
                )
                consecutive_refusals += 1
                if consecutive_refusals >= 2:
                    return _live_provider_fallback(
                        deterministic,
                        "safety_fallback",
                        eval_flag="live_provider_validation_failed",
                    ), tuple(loop_results), tuple(provider_runs)
                continue
            tool_requests, section_markdown = parsed
            if section_markdown is not None:
                return (
                    RoleFindingSet(
                        role_name="risk_management_agent",
                        role_status="completed",
                        findings=deterministic.findings,
                        warning_codes=tuple(dict.fromkeys((*deterministic.warning_codes, "live_provider_reasoning_used"))),
                        live_report_markdown=section_markdown,
                    ),
                    tuple(loop_results),
                    tuple(provider_runs),
                )
            if iteration == provider_call_cap:
                return _live_provider_fallback(deterministic, "safety_fallback"), tuple(loop_results), tuple(provider_runs)
            executed = 0
            for raw_request in tool_requests:
                if len(loop_results) >= tool_request_cap:
                    return _live_provider_fallback(deterministic, "safety_fallback"), tuple(loop_results), tuple(provider_runs)
                validated = _validate_p36_risk_calc_request(raw_request, registry=registry)
                if validated is None:
                    tool_name = str(raw_request.get("tool_id") if isinstance(raw_request, dict) else "calc_request_refused")
                    loop_results.append(
                        blocked_tool_result(
                            tool_name=tool_name,
                            role_name="risk_management_agent",
                            evidence_tier="agent_safe",
                        )
                    )
                    continue
                loop_results.append(
                    execute_tool_request(
                        validated,
                        evidence=evidence,
                        registry=registry,
                        market_context=market_context,
                    )
                )
                executed += 1
            consecutive_refusals = consecutive_refusals + 1 if executed == 0 else 0
            if consecutive_refusals >= 2:
                return _live_provider_fallback(deterministic, "safety_fallback"), tuple(loop_results), tuple(provider_runs)
        except TimeoutError:
            return _live_provider_fallback(deterministic, "provider_timeout"), tuple(loop_results), tuple(provider_runs)
        except (TypeError, ValueError, AttributeError, json.JSONDecodeError):
            return _live_provider_fallback(
                deterministic,
                "safety_fallback",
                eval_flag="live_provider_validation_failed",
            ), tuple(loop_results), tuple(provider_runs)
    return _live_provider_fallback(deterministic, "safety_fallback"), tuple(loop_results), tuple(provider_runs)


def _p36_risk_provider_request(
    role_results: tuple[ToolResult, ...],
    *,
    evidence_refs: tuple[str, ...],
    provider: LLMProvider,
    iteration: int,
) -> LLMProviderRequest:
    envelopes = tuple(_prompt_tool_result_envelope(result) for result in role_results)
    messages = (
        LLMProviderMessage(role="system", content=P36_RISK_SYSTEM_PROMPT),
        LLMProviderMessage(
            role="user",
            content=repr(
                {
                    "iteration": iteration,
                    "allowed_evidence_refs": evidence_refs,
                    "tool_result_envelopes": envelopes,
                    "available_calculation_ids": tuple(P36_RISK_CALC_TOOL_IDS),
                    "response_contract": (
                        "Return either JSON object {'tool_requests': [{'tool_id': <approved calculation ID>, "
                        "'args': {}}]} or the final markdown analysis section. Tool arguments may use only "
                        "the enum scope_category single_name, industry, or sector for C1."
                    ),
                }
            ),
        ),
    )
    return LLMProviderRequest(
        request_id=f"p36_risk_management_agent_iteration_{iteration}",
        role_name="risk_management_agent",
        messages=messages,
        provider=provider.provider_name,
        model=provider.model,
        prompt_version=P36_ROLE_PROMPT_VERSION,
        max_tokens=P36_ANALYST_MAX_TOKENS_PER_ITERATION,
        timeout_seconds=30,
        temperature=0.0,
        metadata={"runner_mode": LIVE_PROVIDER_MODE},
    )


def _parse_p36_risk_response(content: str) -> tuple[tuple[dict[str, object], ...], str | None] | None:
    if not content:
        return None
    if content.startswith("#### Risk and exposure analysis"):
        return (), content
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or set(parsed) != {"tool_requests"}:
        return None
    requests = parsed.get("tool_requests")
    if not isinstance(requests, list) or not requests or not all(isinstance(item, dict) for item in requests):
        return None
    return tuple(requests), None


def _validate_p36_risk_calc_request(
    raw_request: dict[str, object],
    *,
    registry: dict[str, ToolRegistryEntry],
) -> ToolRequest | None:
    if set(raw_request) != {"tool_id", "args"}:
        return None
    tool_id = raw_request.get("tool_id")
    args = raw_request.get("args")
    if not isinstance(tool_id, str):
        return None
    tool_name = P36_RISK_CALC_TOOL_IDS.get(tool_id)
    if tool_name is None:
        return None
    entry = registry.get(tool_name)
    if entry is None or not entry.allows_role("risk_management_agent"):
        return None
    if not isinstance(args, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in args.items()):
        return None
    if any(any(character.isdigit() for character in value) for value in args.values()):
        return None
    if tool_name == "calc_exposure_delta":
        if set(args) - {"scope_category"}:
            return None
        category = args.get("scope_category", "industry")
        if category not in {"single_name", "industry", "sector"}:
            return None
    elif args:
        return None
    try:
        return ToolRequest(tool_name=tool_name, requesting_role="risk_management_agent", args=dict(args))
    except ValueError:
        return None


def _live_provider_role_findings(
    deterministic: RoleFindingSet,
    role_results: tuple[ToolResult, ...],
    *,
    provider: LLMProvider,
) -> LiveRoleResult:
    if deterministic.role_status == "skipped" or not deterministic.findings:
        return LiveRoleResult(deterministic, None)
    evidence_refs = _ordered_refs(_union_refs(deterministic.findings))
    if not evidence_refs:
        return LiveRoleResult(deterministic, None)
    request: LLMProviderRequest | None = None
    try:
        request = _live_provider_request(
            deterministic.role_name,
            role_results,
            evidence_refs=evidence_refs,
            provider=provider,
        )
        response = provider.complete(request)
        response_payload = _provider_response_payload(response)
        provider_run = _provider_run_meta(response_payload, fallback_request=request)
        status = str(response_payload.get("status") or "failed")
        if status != "ok":
            return LiveRoleResult(
                _live_provider_fallback(deterministic, status),
                provider_run,
            )
        if response_payload.get("finish_reason") == "length":
            return LiveRoleResult(
                _live_provider_fallback(deterministic, "unavailable", eval_flag="live_note_truncated_dropped"),
                provider_run,
            )
        content = str(response_payload.get("content_markdown") or "").strip()
        if not content:
            return LiveRoleResult(
                _live_provider_fallback(deterministic, "unavailable"),
                provider_run,
            )
        return LiveRoleResult(
            RoleFindingSet(
                role_name=deterministic.role_name,
                role_status="completed",
                findings=deterministic.findings,
                warning_codes=tuple(dict.fromkeys((*deterministic.warning_codes, "live_provider_reasoning_used"))),
                live_report_markdown=content,
            ),
            provider_run,
        )
    except TimeoutError:
        return LiveRoleResult(
            _live_provider_fallback(deterministic, "provider_timeout"),
            _provider_run_meta(None, fallback_request=request, fallback_status="provider_timeout"),
        )
    except (TypeError, ValueError, AttributeError):
        return LiveRoleResult(
            _live_provider_fallback(deterministic, "safety_fallback", eval_flag="live_provider_validation_failed"),
            _provider_run_meta(None, fallback_request=request, fallback_status="safety_validation_failed"),
        )


def _live_provider_request(
    role_name: str,
    role_results: tuple[ToolResult, ...],
    *,
    evidence_refs: tuple[str, ...],
    provider: LLMProvider,
) -> LLMProviderRequest:
    sanitized_results = tuple(_prompt_tool_result_envelope(result) for result in role_results)
    messages = (
        LLMProviderMessage(
            role="system",
            content=_render_live_role_system_prompt(role_name),
        ),
        LLMProviderMessage(
            role="user",
            content=repr(
                {
                    "allowed_evidence_refs": evidence_refs,
                    "tool_result_envelopes": sanitized_results,
                    "output_rule": "one connective note only; two to four sentences; no heading, table, list, symbol, or portfolio magnitude",
                }
            ),
        ),
    )
    return LLMProviderRequest(
        request_id=f"p35_{role_name}_tool_mediated",
        role_name=role_name,  # type: ignore[arg-type]
        messages=messages,
        provider=provider.provider_name,
        model=provider.model,
        prompt_version=LIVE_PROMPT_VERSION,
        max_tokens=LIVE_ROLE_MAX_TOKENS.get(role_name, 600),
        timeout_seconds=30,
        temperature=0.0,
        metadata={"runner_mode": LIVE_PROVIDER_MODE},
)


def _prompt_tool_result_envelope(result: ToolResult) -> dict[str, object]:
    if result.contract_version == "p36_calc_envelope_v1":
        return _p36_calculation_prompt_envelope(result)
    envelope = {
        "tool_name": result.tool_name,
        "status": result.status,
        "evidence_tier": result.evidence_tier,
        "data_mode": result.data_mode,
        "source_key": result.source_key,
        "source_label": result.source_label,
        "availability": result.availability,
        "freshness": result.freshness,
        "caveat_codes": result.caveat_codes,
        "evidence_refs": result.evidence_refs,
        "fact_labels": prompt_fact_labels_for_tool_result(result),
        "is_mock": result.is_mock,
    }
    validate_tool_payload(
        envelope,
        label="live provider prompt tool result envelope",
        allow_p36_calculation_values=result.contract_version == "p36_calc_envelope_v1",
    )
    return envelope


def _p36_calculation_prompt_envelope(result: ToolResult) -> dict[str, object]:
    """Project value-bearing calculations without legacy private-topic tokens.

    The Risk static prompt is the reviewed semantic catalogue. Its dynamic
    envelope receives only opaque calculation/value references and the frozen
    values themselves, so the legacy input scanner stays strict for every
    runtime message. F-5 later admits report numerals from the original frozen
    result, not from these aliases.
    """

    calculation_id = next(
        (identifier for identifier, tool_name in P36_RISK_CALC_TOOL_IDS.items() if tool_name == result.tool_name),
        "C0",
    )
    values: list[dict[str, str]] = []
    payload_rows = result.summary_payload.get("value_labels")
    if isinstance(payload_rows, (tuple, list)):
        for index, row in enumerate(payload_rows, start=1):
            if not isinstance(row, dict):
                continue
            value = row.get("value_label")
            if not isinstance(value, str) or not value.strip():
                continue
            # A result value such as a bucket name may itself be a forbidden
            # private topic word. The calculation remains frozen and usable by
            # F-5, but that single value never enters the dynamic prompt.
            if find_forbidden_string_values(value):
                continue
            values.append({"value_ref": f"{calculation_id}V{index}", "value": value})
    envelope = {
        "calculation_id": calculation_id,
        "status": result.status,
        "availability": result.availability,
        "freshness": result.freshness,
        "as_of": result.as_of.date().isoformat() if result.as_of is not None else None,
        "values": tuple(values),
    }
    validate_tool_payload(
        envelope,
        label="p36 live provider calculation envelope",
        allow_p36_calculation_values=True,
    )
    return envelope


def _provider_response_payload(response: LLMProviderResponse | object) -> dict[str, object]:
    if isinstance(response, LLMProviderResponse):
        return asdict(response)
    return {
        "request_id": getattr(response, "request_id"),
        "role_name": getattr(response, "role_name"),
        "status": getattr(response, "status"),
        "provider": getattr(response, "provider"),
        "model": getattr(response, "model"),
        "prompt_version": getattr(response, "prompt_version"),
        "content_markdown": getattr(response, "content_markdown"),
        "is_mock": getattr(response, "is_mock"),
        "finish_reason": getattr(response, "finish_reason", None),
        "generated_at": getattr(response, "generated_at", None),
        "error_code": getattr(response, "error_code", None),
        "error_message": getattr(response, "error_message", None),
        "tokens_in": getattr(response, "tokens_in", None),
        "tokens_out": getattr(response, "tokens_out", None),
        "estimated_cost": getattr(response, "estimated_cost", None),
        "metadata": getattr(response, "metadata", {}),
        "contract_version": getattr(response, "contract_version", "llm-provider-contract-v1"),
    }


def _provider_run_meta(
    response_payload: dict[str, object] | None,
    *,
    fallback_request: LLMProviderRequest | None,
    fallback_status: str | None = None,
) -> ProviderRunMeta | None:
    if response_payload is None and fallback_request is None:
        return None
    role_name = str(
        (response_payload or {}).get("role_name")
        or (fallback_request.role_name if fallback_request is not None else "")
    )
    if not role_name:
        return None
    provider = str(
        (response_payload or {}).get("provider")
        or (fallback_request.provider if fallback_request is not None else "unavailable")
    )
    model = str(
        (response_payload or {}).get("model")
        or (fallback_request.model if fallback_request is not None else "unavailable")
    )
    prompt_version = str(
        (response_payload or {}).get("prompt_version")
        or (fallback_request.prompt_version if fallback_request is not None else LIVE_PROMPT_VERSION)
    )
    chain_position, attempted_models = _chain_metadata((response_payload or {}).get("metadata"))
    return ProviderRunMeta(
        role_name=role_name,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        status=str((response_payload or {}).get("status") or fallback_status or "failed"),
        tokens_in=_optional_int((response_payload or {}).get("tokens_in")),
        tokens_out=_optional_int((response_payload or {}).get("tokens_out")),
        estimated_cost=_optional_str((response_payload or {}).get("estimated_cost")),
        is_mock=bool((response_payload or {}).get("is_mock", False)),
        model_chain_position=chain_position,
        attempted_models=attempted_models,
    )


def _chain_metadata(metadata: object) -> tuple[int | None, tuple[str, ...]]:
    """Extract safe model-chain freeze fields from provider response metadata.

    Only plain model-id strings and a non-negative position survive; anything
    malformed degrades to absent so freeze validation stays strict.
    """

    if not isinstance(metadata, dict):
        return None, ()
    raw_position = metadata.get("model_chain_position")
    position: int | None = None
    if isinstance(raw_position, str) and raw_position.strip().isdigit():
        position = int(raw_position.strip())
    raw_attempted = metadata.get("attempted_models")
    attempted: tuple[str, ...] = ()
    if isinstance(raw_attempted, str):
        attempted = tuple(item.strip() for item in raw_attempted.split(",") if item.strip())
    return position, attempted


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _live_provider_fallback(
    deterministic: RoleFindingSet,
    status: str,
    *,
    eval_flag: str | None = None,
) -> RoleFindingSet:
    if not deterministic.findings:
        return _live_provider_skipped(deterministic.role_name, status, eval_flag=eval_flag)
    warning_code = _live_provider_warning_code(status)
    warning_codes = tuple(
        dict.fromkeys(
            (
                *deterministic.warning_codes,
                warning_code,
                *((eval_flag,) if eval_flag else ()),
            )
        )
    )
    return RoleFindingSet(
        role_name=deterministic.role_name,
        role_status="completed",
        findings=deterministic.findings,
        warning_codes=warning_codes,
        unavailable_reason=None,
    )


def _live_provider_skipped(
    role_name: str,
    status: str,
    *,
    eval_flag: str | None = None,
) -> RoleFindingSet:
    warning_code = _live_provider_warning_code(status)
    return RoleFindingSet(
        role_name=role_name,
        role_status="skipped",
        findings=(),
        warning_codes=tuple(dict.fromkeys((warning_code, *((eval_flag,) if eval_flag else ())))),
        unavailable_reason=warning_code,
    )


def _live_provider_warning_code(status: str) -> str:
    if status in {"provider_auth_error", "provider_timeout", "rate_limited", "quota_exceeded"}:
        return f"live_provider_{status}"
    if status == "safety_fallback":
        return "live_provider_safety_fallback"
    return "live_provider_unavailable"


def build_tool_mediated_agent_team_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime | None = None,
    registry: dict[str, ToolRegistryEntry] | None = None,
    role_finding_override: Callable[[str, RoleFindingSet], RoleFindingSet] | None = None,
    llm_provider: LLMProvider | None = None,
    live_provider_enabled: bool = False,
    p36_risk_live_enabled: bool = False,
    market_context: MarketContextExecutionContext | None = None,
) -> SavedAgentTeamSummaryRead:
    generated_at = report_generated_at or _now_utc()
    if evidence.actionability.review_actionability_status.startswith("blocked_"):
        return _deterministic_draft_summary(evidence, report_generated_at=generated_at)
    active_registry = registry or default_tool_registry()
    try:
        run_state = run_tool_mediated_agent_team(
            evidence,
            registry=active_registry,
            role_finding_override=role_finding_override,
            llm_provider=llm_provider,
            live_provider_enabled=live_provider_enabled,
            p36_risk_live_enabled=p36_risk_live_enabled,
            market_context=market_context,
        )
        payload = _summary_payload_from_run_state(run_state, evidence, report_generated_at=generated_at)
        return _validate_or_fallback(payload, evidence, report_generated_at=generated_at)
    except (TypeError, ValueError):
        return _validate_or_fallback(
            {"run_status": "failed", "provider_mode": PROVIDER_MODE, "role_summaries": ()},
            evidence,
            report_generated_at=generated_at,
        )


def build_tool_mediated_agent_team_summary_from_provider_resolution(
    evidence: SavedEvidencePackageRead,
    *,
    provider_resolution: LLMProviderResolution,
    report_generated_at: datetime | None = None,
    registry: dict[str, ToolRegistryEntry] | None = None,
    p36_risk_live_enabled: bool = False,
    market_context: MarketContextExecutionContext | None = None,
) -> SavedAgentTeamSummaryRead:
    """Build a tool-mediated summary using the reviewed provider-factory seam.

    Live role reasoning is active only when the resolved provider is non-mock
    and explicit backend configuration supplied a provider object. Unavailable
    live provider shims still run through the same path so roles degrade to
    skipped/unavailable without re-reading current account state.
    """

    provider = provider_resolution.provider
    live_enabled = provider is not None and provider_resolution.provider_name != "mock"
    return build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=report_generated_at,
        registry=registry,
        llm_provider=provider,
        live_provider_enabled=live_enabled,
        p36_risk_live_enabled=p36_risk_live_enabled and live_enabled,
        market_context=market_context,
    )


def _public_role_findings(
    role_name: str,
    role_results: tuple[ToolResult, ...],
    evidence: SavedEvidencePackageRead,
) -> RoleFindingSet:
    projection = build_public_role_evidence_projection(evidence, role_name=role_name)  # type: ignore[arg-type]
    received = _received_refs(role_results)
    if role_name == "technical_analyst" and (
        "market_quote_freshness" in received or "public_market_context" in received
    ):
        refs = tuple(ref for ref in ("market_quote_freshness", "public_market_context") if ref in received)
        warning_codes = (
            ("eod_not_live_prices",)
            if any(result.tool_name == "market_context_snapshot" and result.availability in {"available", "limited"} for result in role_results)
            else ()
        )
        return RoleFindingSet(
            role_name=role_name,
            role_status="completed",
            findings=(
                RoleFinding(
                    finding_type="missing_context",
                    claim_text=_technical_market_context_claim(role_results),
                    evidence_refs=("trade_intent_summary", *refs),
                    caveat_codes=warning_codes,
                ),
            ),
            warning_codes=warning_codes,
        )
    if role_name == "news_analyst" and (
        "economic_awareness_snapshot" in received
        or "public_events_calendar" in received
        or _fred_economic_awareness_unavailable(role_results)
        or _sec_recent_filings_unavailable(role_results)
    ):
        fred_listing = _fred_economic_awareness_listing(role_results)
        fred_unavailable = fred_listing is None and _fred_economic_awareness_unavailable(role_results)
        sec_listing = _sec_recent_filings_listing(role_results)
        sec_unavailable = sec_listing is None and _sec_recent_filings_unavailable(role_results)
        context_refs = tuple(
            ref
            for ref in ("economic_awareness_snapshot", "public_events_calendar")
            if ref in received
            and (
                (ref == "economic_awareness_snapshot" and fred_listing is not None)
                or (ref == "public_events_calendar" and sec_listing is not None)
            )
        )
        warnings = tuple(
            code
            for code, ref in (
                ("fred_economic_awareness_context_only", "economic_awareness_snapshot"),
                ("sec_edgar_recent_filings_metadata_only", "public_events_calendar"),
            )
            if ref in context_refs
        )
        if fred_unavailable:
            warnings = tuple(dict.fromkeys((*warnings, "fred_economic_awareness_not_available")))
        if sec_unavailable:
            warnings = tuple(dict.fromkeys((*warnings, "sec_edgar_recent_filings_not_available")))
        claim_sentences: list[str] = []
        if fred_listing is not None:
            claim_sentences.append(fred_listing)
        elif fred_unavailable:
            claim_sentences.append(
                "FRED macro calendar metadata was not available or not reviewed in the saved evidence."
            )
        if sec_listing is not None:
            claim_sentences.append(sec_listing)
        elif sec_unavailable:
            claim_sentences.append(
                "Recent SEC EDGAR filing metadata was not available or not reviewed for this instrument."
            )
        claim_sentences.append("Filing contents and general public news interpretation remain unreviewed.")
        return RoleFindingSet(
            role_name=role_name,
            role_status="completed",
            findings=(
                RoleFinding(
                    finding_type="missing_context",
                    claim_text=" ".join(claim_sentences),
                    evidence_refs=("trade_intent_summary", *context_refs),
                    caveat_codes=warnings,
                ),
            ),
            warning_codes=warnings,
        )
    citable = tuple(ref for ref in projection.citable_section_keys if ref in received)
    if not citable:
        reason = _public_unavailable_reason(role_name, projection.degrade_reason)
        return RoleFindingSet(
            role_name=role_name,
            role_status="skipped",
            findings=(),
            warning_codes=(reason,),
            unavailable_reason=reason,
        )
    limited = any(section.availability == "limited" for section in projection.sections if section.section_key in citable)
    return RoleFindingSet(
        role_name=role_name,
        role_status="completed",
        findings=(
            RoleFinding(
                finding_type="missing_context",
                claim_text=_public_claim_text(role_name, limited=limited),
                evidence_refs=tuple(dict.fromkeys(("trade_intent_summary", *citable))),
                caveat_codes=("public_evidence_limited",) if limited else (),
            ),
        ),
        warning_codes=("public_evidence_limited",) if limited else (),
    )


def _sec_event_finding_stays_deterministic(finding_set: RoleFindingSet) -> bool:
    if finding_set.role_name != "news_analyst":
        return False
    return any(code.startswith("sec_edgar_recent_filings") for code in finding_set.warning_codes)


def _fred_economic_finding_stays_deterministic(finding_set: RoleFindingSet) -> bool:
    if finding_set.role_name != "news_analyst":
        return False
    return any(code.startswith("fred_economic_awareness") for code in finding_set.warning_codes)


def _fred_economic_awareness_unavailable(role_results: tuple[ToolResult, ...]) -> bool:
    return any(
        result.tool_name == "economic_awareness_context"
        and result.availability not in {"available", "limited"}
        for result in role_results
    )


def _sec_recent_filings_unavailable(role_results: tuple[ToolResult, ...]) -> bool:
    return any(
        result.tool_name == "sec_recent_filings_metadata"
        and result.availability not in {"available", "limited"}
        for result in role_results
    )


def _fred_economic_awareness_listing(role_results: tuple[ToolResult, ...]) -> str | None:
    for result in role_results:
        if (
            result.tool_name == "economic_awareness_context"
            and result.source_key == "fred_macro_calendar_metadata"
            and result.availability in {"available", "limited"}
            and "economic_awareness_snapshot" in result.evidence_refs
        ):
            rows = result.summary_payload.get("reviewed_release_metadata", ())
            items = _fred_release_items(rows)
            if items:
                return f"FRED macro calendar entries (metadata only): {'; '.join(items)}."
            return "FRED macro calendar metadata was checked and is available as economic context only."
    return None


def _fred_release_items(rows: object) -> tuple[str, ...]:
    if not isinstance(rows, (tuple, list)):
        return ()
    names: list[str] = []
    dates: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        fact_key = str(row.get("fact_key") or "")
        value_label = str(row.get("value_label") or "").strip()
        if not value_label:
            continue
        if fact_key in {"release_name", "event_name"}:
            names.append(value_label)
        elif fact_key in {"release_date", "event_date"}:
            dates.append(value_label)
    count = max(len(names), len(dates))
    items: list[str] = []
    for index in range(count):
        name = names[index] if index < len(names) else "FRED calendar entry"
        date = dates[index] if index < len(dates) else ""
        items.append(f"{name} ({date})" if date else name)
    return tuple(items)


def _sec_recent_filings_listing(role_results: tuple[ToolResult, ...]) -> str | None:
    for result in role_results:
        if (
            result.tool_name == "sec_recent_filings_metadata"
            and result.availability in {"available", "limited"}
            and "public_events_calendar" in result.evidence_refs
        ):
            rows = result.summary_payload.get("reviewed_filing_metadata", ())
            items = _sec_recent_filing_items(rows)
            if items:
                return f"Recent SEC EDGAR filings (metadata only): {'; '.join(items)}."
            return "Recent SEC EDGAR filing metadata was checked and is available as company-event context only."
    return None


def _sec_recent_filing_items(rows: object) -> tuple[str, ...]:
    if not isinstance(rows, (tuple, list)):
        return ()
    forms: list[str] = []
    dates: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        fact_key = str(row.get("fact_key") or "")
        value_label = str(row.get("value_label") or "").strip()
        if not value_label:
            continue
        if fact_key == "form_type":
            forms.append(value_label)
        elif fact_key == "filing_date":
            dates.append(value_label)
    count = max(len(forms), len(dates))
    items: list[str] = []
    for index in range(count):
        form = forms[index] if index < len(forms) else "Recent filing"
        date = dates[index] if index < len(dates) else ""
        items.append(f"{form} ({date})" if date else form)
    return tuple(items)


def _risk_role_findings(role_results: tuple[ToolResult, ...], evidence: SavedEvidencePackageRead) -> RoleFindingSet:
    available = _received_refs(role_results)
    findings: list[RoleFinding] = []
    if {"actionability", "portfolio_impact_summary", "concentration_risk_drift"}.issubset(available):
        findings.append(
            RoleFinding(
                finding_type="ignored_risk",
                claim_text=(
                    "Saved deterministic risk flags, portfolio impact, and concentration drift are context "
                    "that could be overlooked during manual review."
                ),
                evidence_refs=("actionability", "portfolio_impact_summary", "concentration_risk_drift"),
                caveat_codes=evidence.caveat_codes,
            )
        )
    freshness_refs = tuple(ref for ref in ("freshness", "market_quote_freshness") if ref in available)
    if freshness_refs:
        findings.append(
            RoleFinding(
                finding_type="missing_context",
                claim_text=_freshness_specificity_claim(role_results),
                evidence_refs=freshness_refs,
            )
        )
    if any(result.tool_name == "market_context_snapshot" and result.availability in {"available", "limited"} for result in role_results):
        findings.append(
            RoleFinding(
                finding_type="missing_context",
                claim_text=(
                    "FMP end-of-day market context was frozen as public background; "
                    "indicator values are end-of-day context and not live prices."
                ),
                evidence_refs=("public_market_context",),
                caveat_codes=("eod_not_live_prices",),
            )
        )
    if "scope_state" in available:
        findings.append(
            RoleFinding(
                finding_type="missing_context",
                claim_text=_scope_specificity_claim(evidence.scope_state.scope_caveat_codes),
                evidence_refs=("scope_state",),
                caveat_codes=evidence.scope_state.scope_caveat_codes,
            )
        )
    if "options_exposure_summary" in available:
        findings.append(
            RoleFinding(
                finding_type="ignored_risk",
                claim_text=(
                    "Option-structure caveats around collateral, assignment, exercise, and expiry remain "
                    "qualitative review context."
                ),
                evidence_refs=("options_exposure_summary",),
                caveat_codes=evidence.options_exposure_summary.caveat_codes,
            )
        )
    gap_refs = _gap_refs(role_results)
    warnings = tuple(dict.fromkeys((*evidence.caveat_codes, *(_gap_warning(ref) for ref in gap_refs))))
    if gap_refs:
        anchors = tuple(ref for ref in ("trade_intent_summary", "scope_state") if ref in available)
        findings.append(
            RoleFinding(
                finding_type="missing_context",
                claim_text=_gap_specificity_claim(gap_refs),
                evidence_refs=anchors or ("trade_intent_summary",),
            )
        )
    return RoleFindingSet(
        role_name="risk_management_agent",
        role_status="completed",
        findings=tuple(findings),
        warning_codes=warnings,
    )


def _freshness_specificity_claim(role_results: tuple[ToolResult, ...]) -> str:
    clauses: list[str] = []
    for result in role_results:
        if result.tool_name == "broker_snapshot_freshness" and "freshness" in result.evidence_refs:
            category = _freshness_category(result.freshness)
            clauses.append(f"Saved broker snapshot freshness is categorized as {_category_text(category)}.")
        elif result.tool_name == "market_quote_freshness" and "market_quote_freshness" in result.evidence_refs:
            category = _freshness_category(result.freshness)
            clauses.append(f"Market quote freshness is categorized as {_category_text(category)}.")
    if clauses:
        return " ".join(clauses)
    return "Freshness categories should be checked because saved evidence may age before manual review."


def _market_quote_freshness_claim(role_results: tuple[ToolResult, ...]) -> str:
    for result in role_results:
        if result.tool_name == "market_quote_freshness" and "market_quote_freshness" in result.evidence_refs:
            category = _freshness_category(result.freshness)
            return (
                f"Market quote freshness is categorized as {_category_text(category)} in the saved evidence; "
                "saved quotes are not live prices."
            )
    return "Market quote freshness is public context that could be overlooked during manual review."


def _technical_market_context_claim(role_results: tuple[ToolResult, ...]) -> str:
    clauses = [_market_quote_freshness_claim(role_results)]
    if any(result.tool_name == "market_context_snapshot" and result.availability in {"available", "limited"} for result in role_results):
        clauses.append(
            "FMP end-of-day market context is available as internal-evaluation background; "
            "the saved values are end-of-day, not live prices."
        )
    return " ".join(clauses)


def _scope_specificity_claim(scope_caveat_codes: tuple[str, ...]) -> str:
    clauses = _readable_scope_caveats(scope_caveat_codes)
    if not clauses:
        return "Saved scope and account-feasibility caveats remain important manual-review context."
    return f"Saved scope caveats: {render_display_list(clauses)}."


def _readable_scope_caveats(scope_caveat_codes: tuple[str, ...]) -> tuple[str, ...]:
    return display_labels_for_codes(code for code in scope_caveat_codes if code.strip()).labels


def _gap_specificity_claim(gap_refs: tuple[str, ...]) -> str:
    labels = _readable_section_labels(gap_refs)
    if not labels:
        return "Evidence sections outside the saved package remain open context gaps for manual review."
    return f"Evidence sections not available in the saved package: {render_display_list(labels)}."


def _readable_section_labels(section_refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(display_label_for_section(ref) for ref in section_refs))


def _category_text(category: str | None) -> str:
    return display_label_for_code(category or "unknown")


def _summary_payload_from_run_state(
    run_state: ToolMediatedRunState,
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime,
) -> dict:
    role_summaries = tuple(_role_summary_from_findings(item) for item in run_state.audited_findings)
    synthesis_refs = _synthesis_evidence_references(run_state.audited_findings)
    synthesis = _synthesis_markdown(
        evidence,
        run_state.audited_findings,
        synthesis_refs,
        run_state.open_questions,
        tool_results=run_state.tool_results,
        report_generated_at=report_generated_at,
        live_provider_mode=run_state.provider_mode == LIVE_PROVIDER_MODE,
    )
    terminal = {"completed", "skipped"}
    run_status = "completed" if all(summary.role_status in terminal for summary in role_summaries) else "partially_completed"
    warning_codes = _top_level_warning_codes(role_summaries, run_state.auditor)
    tool_run_artifact = _tool_run_artifact_payload(
        run_state,
        synthesis_refs=synthesis_refs,
        warning_codes=warning_codes,
        frozen_at=report_generated_at,
    )
    return {
        "run_status": run_status,
        "provider_mode": run_state.provider_mode,
        "report_generated_at": report_generated_at,
        "role_summaries": tuple(summary.model_dump(mode="python") for summary in role_summaries),
        "warning_codes": warning_codes,
        "report_status": "full_agent_report",
        "final_synthesis_markdown": synthesis,
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": evidence.evidence_schema_version,
        "evidence_references": synthesis_refs,
        "tool_run_artifact": tool_run_artifact.model_dump(mode="python"),
    }


def _tool_run_artifact_payload(
    run_state: ToolMediatedRunState,
    *,
    synthesis_refs: tuple[str, ...],
    warning_codes: tuple[str, ...],
    frozen_at: datetime,
) -> SavedToolMediatedRunArtifactRead:
    return SavedToolMediatedRunArtifactRead(
        artifact_schema_version=(
            P36_ARTIFACT_SCHEMA_VERSION
            if any(result.contract_version == "p36_calc_envelope_v1" for result in run_state.tool_results)
            or any(provider_run.prompt_version == P36_ROLE_PROMPT_VERSION for provider_run in run_state.provider_runs)
            else "p33a_tool_run_freeze_v1"
        ),
        provider_mode=run_state.provider_mode,  # type: ignore[arg-type]
        plan_version=run_state.plan.plan_version,
        audit_version=run_state.auditor.audit_version,
        locked_question=run_state.catalog.locked_question,
        dimensions=run_state.plan.dimensions,
        role_plan=tuple(asdict(role_plan) for role_plan in run_state.plan.role_plan),
        tool_results=tuple(_frozen_tool_result(result) for result in run_state.tool_results),
        audited_findings=tuple(_frozen_finding_set(finding_set) for finding_set in run_state.audited_findings),
        auditor=asdict(run_state.auditor),
        provider_runs=tuple(asdict(provider_run) for provider_run in run_state.provider_runs),
        open_questions=run_state.open_questions,
        synthesis_evidence_references=synthesis_refs,
        warning_codes=warning_codes,
        tool_result_count=len(run_state.tool_results),
        frozen_at=frozen_at,
    )


def _frozen_tool_result(result: ToolResult) -> dict:
    return {
        "tool_name": result.tool_name,
        "role_name": result.role_name,
        "status": result.status,
        "evidence_tier": result.evidence_tier,
        "data_mode": result.data_mode,
        "source_key": result.source_key,
        "source_label": result.source_label,
        "availability": result.availability,
        "freshness": result.freshness,
        "as_of": result.as_of,
        "scope": result.scope,
        "caveat_codes": result.caveat_codes,
        "evidence_refs": result.evidence_refs,
        "summary_payload": result.summary_payload,
        "provenance": result.provenance,
        "latency_ms": result.latency_ms,
        "estimated_cost": result.estimated_cost,
        "is_mock": result.is_mock,
        "contract_version": result.contract_version,
    }


def _frozen_finding_set(finding_set: RoleFindingSet) -> dict:
    return {
        "role_name": finding_set.role_name,
        "role_status": finding_set.role_status,
        "findings": tuple(
            {
                "finding_type": finding.finding_type,
                "claim_text": replace_internal_display_tokens(finding.claim_text) or "",
                "evidence_refs": finding.evidence_refs,
                "caveat_codes": finding.caveat_codes,
            }
            for finding in finding_set.findings
        ),
        "warning_codes": finding_set.warning_codes,
        "unavailable_reason": finding_set.unavailable_reason,
        "live_report_markdown": replace_internal_display_tokens(finding_set.live_report_markdown),
    }


def _role_summary_from_findings(finding_set: RoleFindingSet) -> SavedAgentTeamRoleSummaryRead:
    role = role_definition(finding_set.role_name)  # type: ignore[arg-type]
    refs = _ordered_refs(_union_refs(finding_set.findings))
    if finding_set.role_status == "skipped" and finding_set.role_name in PUBLIC_ANALYST_ROLES:
        refs = ("trade_intent_summary",)
    summary = None
    if finding_set.findings:
        summary = replace_internal_display_tokens(" ".join(finding.claim_text for finding in finding_set.findings))
    provider_status = "ok" if finding_set.role_status == "completed" else "skipped"
    return SavedAgentTeamRoleSummaryRead(
        role_name=finding_set.role_name,
        display_name=role.display_name,
        role_status=finding_set.role_status,  # type: ignore[arg-type]
        provider_status=provider_status,
        summary_markdown=summary,
        live_report_markdown=replace_internal_display_tokens(finding_set.live_report_markdown),
        evidence_references=refs,
        warning_codes=finding_set.warning_codes,
        unavailable_reason=finding_set.unavailable_reason,
    )


def _portfolio_manager_finding_set(
    audited_findings: tuple[RoleFindingSet, ...],
    open_questions: tuple[str, ...],
) -> RoleFindingSet:
    refs = _synthesis_evidence_references(audited_findings)
    event_clauses = [
        (
            "Company-event metadata was included as background only."
            if "public_events_calendar" in refs
            else "Reviewed company-event metadata remains an uncited context gap."
        ),
        (
            "FRED macro calendar metadata was included as background only."
            if "economic_awareness_snapshot" in refs
            else "FRED macro calendar metadata remains unavailable or uncited context."
        ),
        *((("FMP end-of-day market context was included as background only.",) if "public_market_context" in refs else ())),
    ]
    return RoleFindingSet(
        role_name="portfolio_manager_agent",
        role_status="completed",
        findings=(
            RoleFinding(
                finding_type="ignored_risk",
                claim_text=(
                    "Portfolio Manager synthesis groups deterministic risk flags, freshness gaps, "
                    "scope caveats, and context not reviewed."
                )
                + " "
                + " ".join(event_clauses)
                + (" Open questions remain for manual review." if open_questions else ""),
                evidence_refs=refs,
            ),
        ),
        warning_codes=(),
    )


def _synthesis_markdown(
    evidence: SavedEvidencePackageRead,
    audited_findings: tuple[RoleFindingSet, ...],
    evidence_refs: tuple[str, ...],
    open_questions: tuple[str, ...],
    *,
    tool_results: tuple[ToolResult, ...],
    report_generated_at: datetime,
    live_provider_mode: bool = False,
) -> str:
    before_after = evidence.before_after_portfolio_impact
    concentration = evidence.concentration_risk_drift
    groups = before_after.trade_impact_narrative_groups
    proceed_statements = groups.proceed_statements if groups is not None else ()
    not_reviewed_statement = groups.not_reviewed_statement if groups is not None else None
    verify_statement = groups.verify_statement if groups is not None else None
    title = _trade_review_title(evidence, report_generated_at=report_generated_at)
    headline = _summary_headline(proceed_statements, before_after)
    technical_note_lines = _live_note_lines(
        audited_findings,
        "technical_analyst",
        live_provider_mode=live_provider_mode,
    )
    risk_note_lines = _live_note_lines(
        audited_findings,
        "risk_management_agent",
        live_provider_mode=live_provider_mode,
    )
    sections = (
        title,
        "",
        "_Read-only analysis for your manual review. Not advice, not a recommendation, and not an instruction to trade._",
        "",
        "## Summary",
        "What would I be ignoring if I acted manually now? What you would be ignoring is organized below from frozen saved evidence only.",
        _summary_paragraph(evidence, headline=headline),
        "",
        "## If you proceed",
        *_markdown_paragraphs(
            proceed_statements
            or (
                "Trade-impact narrative statements were not frozen with this saved package, so this section cannot be reconstructed without recomputation.",
            )
        ),
        "",
        "## Exposure before and after",
        *_exposure_table_blocks(before_after),
        "",
        "## Reference points",
        *_reference_point_lines(concentration),
        "",
        "## Market context",
        *_market_context_lines(tool_results),
        *technical_note_lines,
        "",
        "## Risk and scope notes",
        *_risk_scope_lines(evidence, cited_refs=evidence_refs),
        *risk_note_lines,
        "",
        *(("## Open questions", *open_questions, "") if open_questions else ()),
        "## What was not reviewed",
        *_markdown_paragraphs(
            (
                not_reviewed_statement
                or "Fund holdings, public events, taxes, and accounts outside the reviewed scope were not reviewed in the saved package.",
            )
        ),
        *_markdown_list_items(_unavailable_inventory(evidence, cited_refs=evidence_refs)),
        "",
        "## Verify before acting",
        *_markdown_paragraphs(
            (
                verify_statement
                or "Verify the saved scope, confirm the latest broker snapshot, check current prices, and review any missing public context.",
            )
        ),
        "",
        "---",
        _document_footer(evidence),
    )
    document = "\n".join(line for line in sections if line is not None)
    document = replace_internal_display_tokens(document) or ""
    if find_internal_display_tokens(document):
        raise ValueError("tool-mediated document contains an internal display token")
    return document


def _trade_review_title(evidence: SavedEvidencePackageRead, *, report_generated_at: datetime) -> str:
    action = _trade_action_label(evidence)
    account_label = evidence.scope_state.review_account_display_label or "reviewed account"
    return f"# Trade review: {action} - {account_label} - {_long_date(report_generated_at)}"


def _trade_action_label(evidence: SavedEvidencePackageRead) -> str:
    symbol = (evidence.trade_intent_summary.symbol_or_underlying or "instrument").upper()
    flow = evidence.trade_intent_summary.supported_flow
    if flow in {"stock_buy", "etf_buy"}:
        return f"Buy {symbol}"
    if flow == "stock_sell_trim":
        return f"Review stock trim for {symbol}"
    if flow == "etf_sell_trim":
        return f"Review ETF trim for {symbol}"
    return f"{evidence.trade_intent_summary.review_flow_label} for {symbol}"


def _long_date(value: datetime) -> str:
    return value.strftime("%B %d, %Y").replace(" 0", " ")


def _summary_headline(
    proceed_statements: tuple[str, ...],
    before_after: object,
) -> str:
    for statement in proceed_statements:
        if "semiconductor-classified holdings" in statement.lower() or "position" in statement.lower():
            return statement
    summary = getattr(before_after, "summary_label", None)
    if summary:
        return str(summary)
    return "The saved exposure impact was unavailable, so this report names the gap instead of reconstructing it."


def _summary_paragraph(evidence: SavedEvidencePackageRead, *, headline: str) -> str:
    account_label = evidence.scope_state.review_account_display_label or "reviewed account"
    flow_label = evidence.trade_intent_summary.review_flow_label.removesuffix(" review").lower()
    return (
        f"This saved report covers the saved {flow_label} "
        f"for {account_label} using frozen evidence only. **{headline}**"
    )


def _markdown_paragraphs(lines: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line.strip() for line in lines if line and line.strip())


def _markdown_list_items(lines: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"- {line.strip()}" for line in lines if line and line.strip())


def _exposure_table_blocks(section) -> tuple[str, ...]:
    if section.availability not in {"available", "limited"}:
        return (
            section.summary_label
            or "Your account positions were not available for this run, so exposure could not be computed.",
        )
    labels = tuple(section.detail_labels)
    tables: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_rows: list[str] = []
    for label in labels:
        if label == "Trade-impact narrative:":
            break
        if ": Row | Before $ | Before % | Trade Delta $ | After $ | After %." in label:
            if current_title is not None:
                tables.append((current_title, current_rows))
            current_title = label.split(": Row |", 1)[0]
            current_rows = []
            continue
        if current_title is not None and " | " in label:
            current_rows.append(label)
    if current_title is not None:
        tables.append((current_title, current_rows))
    blocks: list[str] = []
    if section.summary_label:
        blocks.append(section.summary_label)
    for title, rows in tables:
        blocks.extend(_markdown_exposure_table(title, rows))
    if not tables:
        blocks.append("Frozen before/after table rows were not available in this saved package.")
    return tuple(blocks)


def _markdown_exposure_table(title: str, row_labels: list[str]) -> tuple[str, ...]:
    rows: list[str] = []
    for label in row_labels:
        cells = tuple(cell.strip().rstrip(".") for cell in label.split(" | "))
        if len(cells) != 6:
            continue
        rows.append(f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {cells[4]} | {cells[5]} |")
    if not rows:
        return (f"{title}: no frozen rows were available.",)
    return (
        f"{title}.",
        "| Row | Before $ | Before % | Trade Delta $ | After $ | After % |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *rows,
    )


def _reference_point_lines(section) -> tuple[str, ...]:
    if section.availability not in {"available", "limited"}:
        return (section.summary_label or "Reference-point findings were not available in this saved package.",)
    lines = [section.summary_label] if section.summary_label else []
    lines.extend(label for label in section.detail_labels if label)
    if not lines:
        lines.append("Reference-point findings were not available in this saved package.")
    return tuple(lines)


def _market_context_lines(tool_results: tuple[ToolResult, ...]) -> tuple[str, ...]:
    result = next(
        (
            item
            for item in tool_results
            if item.tool_name == "market_context_snapshot" and item.availability in {"available", "limited"}
        ),
        None,
    )
    if result is None:
        return ("Saved end-of-day market context was not available for this report run.",)
    rows = _market_context_display_rows(result)
    if not rows:
        return ("Saved end-of-day market context was available, but no reviewed indicator rows were frozen.",)
    return (
        "FMP end-of-day market context is frozen background only; it is not live pricing.",
        "| Indicator | Frozen value or category |",
        "| --- | ---: |",
        *rows,
    )


def _market_context_display_rows(result: ToolResult) -> list[str]:
    """Render only reviewed display-mapped market facts, without duplicate metadata."""

    rows: list[str] = []
    seen_semantics: set[str] = set()
    omitted_unmapped = False
    aliases = {
        "market_context_as_of_date": "as_of_date",
        "market_context_freshness_category": "freshness_category",
    }
    for fact in prompt_fact_labels_for_tool_result(result):
        fact_key = str(fact["fact_key"])
        semantic_key = aliases.get(fact_key, fact_key)
        if semantic_key in seen_semantics:
            continue
        display_label = FACT_DISPLAY_LABELS.get(fact_key)
        if display_label is None:
            omitted_unmapped = True
            continue
        seen_semantics.add(semantic_key)
        value = replace_internal_display_tokens(fact["value_label"]) or "Unlabeled review detail."
        rows.append(f"| {display_label} | {value} |")
    if omitted_unmapped:
        rows.append("| Omitted indicator | A reviewed indicator was omitted because its display label was unavailable. |")
    return rows


def _risk_scope_lines(
    evidence: SavedEvidencePackageRead,
    *,
    cited_refs: tuple[str, ...],
) -> tuple[str, ...]:
    scope_labels = display_labels_for_codes(evidence.scope_state.scope_caveat_codes).labels
    account_line = (
        "Account-level feasibility was evaluated in the saved scope."
        if evidence.scope_state.account_level_feasibility_evaluated
        else "Account-level feasibility was not evaluated in the saved scope."
    )
    lines = [
        account_line,
        f"Scope caveats: {render_display_list(scope_labels) if scope_labels else 'none'}.",
    ]
    if evidence.freshness.broker_snapshot_freshness_label:
        lines.append(_sentence(evidence.freshness.broker_snapshot_freshness_label))
    if evidence.freshness.market_quote_freshness_label:
        lines.append(_sentence(evidence.freshness.market_quote_freshness_label))
    if "public_events_calendar" in cited_refs:
        lines.append("Company-event metadata was included as background only.")
    if "economic_awareness_snapshot" in cited_refs:
        lines.append("FRED macro calendar metadata was included as economic context only.")
    if "public_market_context" in cited_refs:
        lines.append("FMP end-of-day market context was included as background only.")
    gaps = _unavailable_inventory(evidence, cited_refs=cited_refs)
    if gaps:
        lines.append(f"Unavailable or not-reviewed context: {render_display_list(gaps)}.")
    return tuple(lines)


def _live_note_for_role(audited_findings: tuple[RoleFindingSet, ...], role_name: str) -> str | None:
    for finding_set in audited_findings:
        if finding_set.role_name != role_name or not finding_set.live_report_markdown:
            continue
        return replace_internal_display_tokens(finding_set.live_report_markdown)
    return None


def _live_note_lines(
    audited_findings: tuple[RoleFindingSet, ...],
    role_name: str,
    *,
    live_provider_mode: bool,
) -> tuple[str, ...]:
    note = _live_note_for_role(audited_findings, role_name)
    display_name = role_definition(role_name).display_name  # type: ignore[arg-type]
    if note:
        return (f"**{display_name}**", note)
    if live_provider_mode:
        return (f"No {display_name} note is available in this saved report.",)
    return ()


def _document_footer(evidence: SavedEvidencePackageRead) -> str:
    broker_freshness = evidence.freshness.broker_snapshot_freshness_label or "saved account sync"
    market_freshness = evidence.freshness.market_quote_freshness_label or "saved end-of-day prices"
    return (
        "_Reference points are common rule-of-thumb levels used to organize this report. "
        "They are not personalized limits, targets, or recommendations. "
        f"{_sentence(broker_freshness)} {_sentence(market_freshness)} End-of-day prices are not live._"
    )


def _sentence(value: str) -> str:
    text = value.strip()
    return text if text.endswith((".", "!", "?")) else f"{text}."


def _role_digest_lines(audited_findings: tuple[RoleFindingSet, ...]) -> tuple[str, ...]:
    lines: list[str] = []
    for finding_set in audited_findings:
        if finding_set.role_name == "portfolio_manager_agent":
            continue
        role = role_definition(finding_set.role_name)  # type: ignore[arg-type]
        if finding_set.findings:
            digest = _first_sentence(
                replace_internal_display_tokens(" ".join(finding.claim_text for finding in finding_set.findings))
                or ""
            )
        elif finding_set.unavailable_reason:
            digest = display_label_for_code(finding_set.unavailable_reason)
        else:
            digest = "no citable saved evidence was available"
        lines.append(f"{role.display_name}: {digest}")
    return tuple(lines)


def _first_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return "no summary available"
    match = re.search(r"(?<=[.!?])\s", cleaned)
    if match:
        return cleaned[: match.start()].strip()
    return cleaned


def _unavailable_inventory(
    evidence: SavedEvidencePackageRead,
    *,
    cited_refs: tuple[str, ...] = (),
) -> tuple[str, ...]:
    unavailable: list[str] = []
    for section in (
        evidence.before_after_portfolio_impact,
        evidence.market_quote_freshness,
        evidence.economic_awareness_snapshot,
        evidence.market_mood_snapshot,
    ):
        if section.availability not in {"available", "limited"}:
            unavailable.append(display_label_for_section(section.section_key))
    if evidence.public_evidence is not None:
        for section in (
            evidence.public_evidence.public_fundamentals_snapshot,
            evidence.public_evidence.public_news_snapshot,
            evidence.public_evidence.public_events_calendar,
            evidence.public_evidence.public_technical_context,
            evidence.public_evidence.public_market_context,
        ):
            if section.section_key in cited_refs:
                continue
            if section.availability not in {"available", "limited"}:
                unavailable.append(display_label_for_section(section.section_key))
    if not unavailable:
        return ("No unavailable saved-evidence sections were flagged by the deterministic inventory.",)
    return tuple(dict.fromkeys(unavailable))


def _received_refs_by_role(results_by_role: dict[str, tuple[ToolResult, ...]]) -> dict[str, frozenset[str]]:
    return {role: frozenset(_received_refs(results)) for role, results in results_by_role.items()}


def _received_refs(results: tuple[ToolResult, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for result in results:
        if result.availability in {"available", "limited"}:
            refs.extend(result.evidence_refs)
    return tuple(dict.fromkeys(refs))


def _gap_refs(role_results: tuple[ToolResult, ...]) -> tuple[str, ...]:
    for result in role_results:
        if result.tool_name == "evidence_gap_inspector":
            refs = result.summary_payload.get("unavailable_evidence_refs", ())
            if isinstance(refs, tuple):
                return tuple(str(ref) for ref in refs if str(ref) in GAPPABLE_SECTIONS)
            if isinstance(refs, list):
                return tuple(str(ref) for ref in refs if str(ref) in GAPPABLE_SECTIONS)
    return ()


def _gap_warning(ref: str) -> str:
    return f"{ref}_unavailable"


def _public_unavailable_reason(role_name: str, degrade_reason: str | None) -> str:
    if role_name == "news_analyst":
        return "public_news_context_unavailable"
    if role_name == "technical_analyst":
        return "public_technical_context_unavailable"
    if degrade_reason:
        return degrade_reason
    return "public_fundamentals_context_unavailable"


def _public_claim_text(role_name: str, *, limited: bool) -> str:
    limited_sentence = " Some public evidence is limited and remains background context." if limited else ""
    if role_name == "fundamentals_analyst":
        return (
            "Reviewed public company profile context is background that could be overlooked."
            f"{limited_sentence}"
        )
    if role_name == "technical_analyst":
        return "Market quote freshness is public context that could be overlooked during manual review."
    return "Reviewed public context is background that could be overlooked during manual review."


def _public_sections(evidence: SavedEvidencePackageRead):
    if evidence.public_evidence is None:
        return ()
    return (
        evidence.public_evidence.public_company_profile,
        evidence.public_evidence.public_fundamentals_snapshot,
        evidence.public_evidence.public_news_snapshot,
        evidence.public_evidence.public_events_calendar,
        evidence.public_evidence.public_technical_context,
        evidence.public_evidence.public_market_context,
    )


def _agent_safe_sections(evidence: SavedEvidencePackageRead):
    return (
        evidence.portfolio_impact_summary,
        evidence.before_after_portfolio_impact,
        evidence.concentration_risk_drift,
        evidence.cash_collateral_caveats,
        evidence.options_exposure_summary,
        evidence.market_quote_freshness,
        evidence.economic_awareness_snapshot,
        evidence.market_mood_snapshot,
    )


def _catalog_section_for_saved_section(section, *, tier: str) -> EvidenceCatalogSection:
    return EvidenceCatalogSection(
        section_key=section.section_key,
        availability=section.availability,
        evidence_tier=(
            "public" if section.section_key in {"market_quote_freshness", "economic_awareness_snapshot"} else tier
        ),
        freshness_category=_freshness_category(section.summary_label),
        caveat_codes=section.caveat_codes,
    )


def _catalog_section_for_public_section(section) -> EvidenceCatalogSection:
    return EvidenceCatalogSection(
        section_key=section.section_key,
        availability=section.availability,
        evidence_tier="public",
        freshness_category=getattr(section, "freshness_category", None),
        caveat_codes=section.caveat_codes,
    )


def _freshness_category(label: str | None) -> str | None:
    # T18-F2: delegates to the shared gate-module helper so the deterministic
    # floor wording and the category-gate vocabulary can never drift apart.
    return freshness_category_from_label(label)


def _registry_from_catalog(catalog: EvidenceCatalog) -> dict[str, ToolRegistryEntry]:
    default = default_tool_registry()
    return {tool.tool_name: default[tool.tool_name] for tool in catalog.tools if tool.tool_name in default}


def _open_questions_from_contradictions(contradictions: tuple[Contradiction, ...]) -> tuple[str, ...]:
    return tuple(
        f"{display_label_for_section(item.evidence_ref)} has conflicting freshness or availability framing across reviewed roles."
        for item in contradictions
    )


def _union_refs(findings: tuple[RoleFinding, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for finding in findings:
        refs.extend(finding.evidence_refs)
    return tuple(dict.fromkeys(refs))


def _synthesis_evidence_references(finding_sets: tuple[RoleFindingSet, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for finding_set in finding_sets:
        if finding_set.role_name == "portfolio_manager_agent":
            continue
        for finding in finding_set.findings:
            refs.extend(finding.evidence_refs)
    allowed = usable_content_by_role()["portfolio_manager_agent"]
    return _ordered_refs(tuple(ref for ref in refs if ref in allowed))


def _ordered_refs(refs: tuple[str, ...]) -> tuple[str, ...]:
    unique = set(refs)
    return tuple(ref for ref in CANONICAL_EVIDENCE_ORDER if ref in unique)


def _top_level_warning_codes(
    role_summaries: tuple[SavedAgentTeamRoleSummaryRead, ...],
    auditor: AuditorRecord,
) -> tuple[str, ...]:
    public_roles = [summary for summary in role_summaries if summary.role_name in PUBLIC_ANALYST_ROLES]
    completed = [summary for summary in public_roles if summary.role_status == "completed"]
    if not completed:
        coverage = "public_evidence_roles_skipped"
    elif len(completed) < len(public_roles):
        coverage = "public_evidence_partial_coverage"
    else:
        coverage = "public_evidence_roles_included"
    warnings: list[str] = [coverage]
    warnings.extend(auditor.eval_flags)
    return tuple(dict.fromkeys(warnings))


__all__ = [
    "AUDIT_VERSION",
    "GAPPABLE_SECTIONS",
    "MAX_PLANNER_REPASSES",
    "MAX_ROLES",
    "MAX_TOOL_CALLS_PER_ROLE",
    "MAX_TOOL_CALLS_TOTAL",
    "PLAN_VERSION",
    "PROVIDER_MODE",
    "AuditorRecord",
    "Contradiction",
    "EvidenceCatalog",
    "EvidenceCatalogSection",
    "EvidenceCatalogTool",
    "PlannerPlan",
    "PlannedToolRequest",
    "RoleFinding",
    "RoleFindingSet",
    "RolePlan",
    "ToolMediatedRunState",
    "audit_findings",
    "build_evidence_catalog",
    "build_planner_plan",
    "build_role_findings",
    "build_tool_mediated_agent_team_summary",
    "build_tool_mediated_agent_team_summary_from_provider_resolution",
    "run_tool_mediated_agent_team",
    "usable_content_by_role",
]
