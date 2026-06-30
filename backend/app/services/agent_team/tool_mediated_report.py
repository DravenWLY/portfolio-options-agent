"""Deterministic tool-mediated Agent Team report builder (P33A-T3).

This module is deliberately in-process and offline. It executes only the
reviewed P33A tool registry against an existing ``SavedEvidencePackageRead`` and
reduces audited findings into the existing saved Agent Team summary schema.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Callable, Literal

from app.schemas.reports import (
    SavedAgentTeamRoleSummaryRead,
    SavedAgentTeamSummaryRead,
    SavedEvidencePackageRead,
    SavedToolMediatedRunArtifactRead,
    validate_saved_tool_freeze_payload,
)
from app.services.agent_team.llm_provider import (
    AGENT_TEAM_ROLES,
    AgentTeamRole,
    LLMProvider,
    LLMProviderMessage,
    LLMProviderRequest,
    LLMProviderResponse,
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.output_safety import validate_llm_provider_output
from app.services.agent_team.provider_factory import LLMProviderResolution
from app.services.agent_team.report_output_safety import (
    INVENTED_LEVEL_PATTERNS,
    REPORT_PROHIBITED_PHRASES,
    ROLE_ALLOWED_EVIDENCE_KEYS,
    SOURCE_LEAK_PATTERNS,
)
from app.services.agent_team.roles import PUBLIC_ANALYST_ROLES, role_definition
from app.services.agent_team.tools import (
    TOOL_FORBIDDEN_KEYS,
    TOOL_GENERATED_METRIC_PATTERNS,
    TOOL_PROHIBITED_PHRASES,
)
from app.services.agent_team.tools import (
    ToolRegistryEntry,
    ToolRequest,
    ToolResult,
    default_tool_registry,
    execute_tool_request,
    validate_tool_payload,
)
from app.services.privacy import find_forbidden_keys
from app.services.reports.agent_team_report import _deterministic_draft_summary, _validate_or_fallback
from app.services.reports.public_evidence import build_public_role_evidence_projection

FindingType = Literal["ignored_risk", "missing_context", "contradiction", "open_question"]

MAX_TOOL_CALLS_PER_ROLE = 8
MAX_TOOL_CALLS_TOTAL = 16
MAX_ROLES = len(AGENT_TEAM_ROLES)
MAX_PLANNER_REPASSES = 1
PLAN_VERSION = "p33a_plan_v1"
AUDIT_VERSION = "p33a_audit_v1"
PROVIDER_MODE = "tool_mediated_mock"
LIVE_PROVIDER_MODE = "tool_mediated_live"
QUESTION = "what_would_be_ignored"
LIVE_PROMPT_VERSION = "p34a-tool-mediated-role-v1"
PLAN_DIMENSIONS = (
    "risk_freshness",
    "scope_feasibility",
    "public_company_context",
    "public_market_context",
    "evidence_gaps",
)

TOOL_FIXED_CONTENT_REFS: dict[str, tuple[str, ...]] = {
    "trade_intent_summary": ("trade_intent_summary",),
    "portfolio_scope_context": ("scope_state",),
    "deterministic_review_findings": (
        "actionability",
        "portfolio_impact_summary",
        "concentration_risk_drift",
        "liquidity_collateral_caveats",
        "options_exposure_summary",
    ),
    "broker_snapshot_freshness": ("freshness",),
    "market_quote_freshness": ("market_quote_freshness",),
    "public_company_profile": ("public_company_profile",),
    "economic_awareness_context": ("economic_awareness_snapshot",),
    "evidence_gap_inspector": (),
}

GAPPABLE_SECTIONS: tuple[str, ...] = (
    "portfolio_impact_summary",
    "before_after_portfolio_impact",
    "concentration_risk_drift",
    "liquidity_collateral_caveats",
    "options_exposure_summary",
    "market_quote_freshness",
    "economic_awareness_snapshot",
    "market_mood_snapshot",
    "public_company_profile",
    "public_fundamentals_snapshot",
    "public_news_snapshot",
    "public_events_calendar",
    "public_technical_context",
    "public_market_context",
)

CANONICAL_EVIDENCE_ORDER: tuple[str, ...] = (
    "trade_intent_summary",
    "scope_state",
    "freshness",
    "actionability",
    "portfolio_impact_summary",
    "before_after_portfolio_impact",
    "concentration_risk_drift",
    "liquidity_collateral_caveats",
    "options_exposure_summary",
    "market_quote_freshness",
    "economic_awareness_snapshot",
    "market_mood_snapshot",
    "public_company_profile",
    "public_fundamentals_snapshot",
    "public_news_snapshot",
    "public_events_calendar",
    "public_technical_context",
    "public_market_context",
)

AUDITOR_EVAL_WARNING_CODES = frozenset(
    {
        "private_leak_blocked",
        "advice_wording_blocked",
        "invented_metric_blocked",
        "live_provider_validation_failed",
    }
)
STRUCTURED_NEGATIVE_SIGNAL_TOKENS = (
    "stale",
    "unavailable",
    "not_available",
    "not_reviewed",
    "unknown",
    "not_evaluated",
    "caveated",
    "unverified",
    "limited",
)
STRUCTURED_POSITIVE_SIGNAL_TOKENS = (
    "fresh",
    "verified",
    "available_ok",
    "reviewed_ok",
)


@dataclass(frozen=True)
class EvidenceCatalogTool:
    tool_name: str
    display_name: str
    evidence_tier: str
    role_allowlist: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="evidence catalog tool")


@dataclass(frozen=True)
class EvidenceCatalogSection:
    section_key: str
    availability: str
    evidence_tier: str
    freshness_category: str | None
    caveat_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="evidence catalog section")


@dataclass(frozen=True)
class EvidenceCatalog:
    tools: tuple[EvidenceCatalogTool, ...]
    sections: tuple[EvidenceCatalogSection, ...]
    locked_question: str = QUESTION

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="evidence catalog")


@dataclass(frozen=True)
class PlannedToolRequest:
    tool_name: str
    args: dict[str, str]

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="planned tool request")


@dataclass(frozen=True)
class RolePlan:
    role_name: str
    tool_requests: tuple[PlannedToolRequest, ...]
    rationale_code: str

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="role plan")


@dataclass(frozen=True)
class PlannerPlan:
    plan_version: str
    dimensions: tuple[str, ...]
    role_plan: tuple[RolePlan, ...]

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="planner plan")


@dataclass(frozen=True)
class RoleFinding:
    finding_type: FindingType
    claim_text: str
    evidence_refs: tuple[str, ...]
    caveat_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoleFindingSet:
    role_name: str
    role_status: str
    findings: tuple[RoleFinding, ...]
    warning_codes: tuple[str, ...]
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class Contradiction:
    evidence_ref: str
    role_a: str
    role_b: str
    description: str

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="contradiction")


@dataclass(frozen=True)
class AuditorRecord:
    audit_version: str
    role_verdicts: tuple[tuple[str, bool], ...]
    contradictions: tuple[Contradiction, ...]
    dropped_claims: tuple[str, ...]
    repass_triggered: bool
    eval_flags: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_tool_payload(asdict(self), label="auditor record")


@dataclass(frozen=True)
class ProviderRunMeta:
    role_name: str
    provider: str
    model: str
    prompt_version: str
    status: str
    tokens_in: int | None
    tokens_out: int | None
    estimated_cost: str | None
    is_mock: bool

    def __post_init__(self) -> None:
        validate_saved_tool_freeze_payload(asdict(self))


@dataclass(frozen=True)
class LiveRoleResult:
    finding_set: RoleFindingSet
    provider_run: ProviderRunMeta | None


@dataclass(frozen=True)
class ToolMediatedRunState:
    catalog: EvidenceCatalog
    plan: PlannerPlan
    tool_results: tuple[ToolResult, ...]
    audited_findings: tuple[RoleFindingSet, ...]
    auditor: AuditorRecord
    open_questions: tuple[str, ...]
    provider_mode: str = PROVIDER_MODE
    provider_runs: tuple[ProviderRunMeta, ...] = ()

    def __post_init__(self) -> None:
        validate_saved_tool_freeze_payload(asdict(self))


def _now_utc() -> datetime:
    return datetime.now(UTC)


def usable_content_by_role(
    registry: dict[str, ToolRegistryEntry] | None = None,
) -> dict[str, frozenset[str]]:
    active_registry = registry or default_tool_registry()
    usable: dict[str, frozenset[str]] = {}
    for role in AGENT_TEAM_ROLES:
        receivable: set[str] = set()
        for entry in active_registry.values():
            if entry.allows_role(role):
                receivable.update(TOOL_FIXED_CONTENT_REFS.get(entry.tool_name, ()))
        usable[role] = frozenset(receivable.intersection(ROLE_ALLOWED_EVIDENCE_KEYS[role]))
    return usable


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
) -> ToolMediatedRunState:
    catalog = build_evidence_catalog(evidence, registry)
    plan = build_planner_plan(catalog)
    tool_results: list[ToolResult] = []
    by_role: dict[str, tuple[ToolResult, ...]] = {}
    for role_plan in plan.role_plan:
        role_results: list[ToolResult] = []
        for planned in role_plan.tool_requests:
            result = execute_tool_request(
                ToolRequest(tool_name=planned.tool_name, requesting_role=role_plan.role_name, args=planned.args),
                evidence=evidence,
                registry=registry,
            )
            if role_plan.role_name in PUBLIC_ANALYST_ROLES and result.evidence_tier == "agent_safe":
                result = execute_tool_request(
                    ToolRequest(tool_name="not_allowed", requesting_role=role_plan.role_name),
                    evidence=evidence,
                    registry=registry,
                )
            role_results.append(result)
            tool_results.append(result)
        by_role[role_plan.role_name] = tuple(role_results)

    raw_findings = tuple(
        build_role_findings(role, by_role.get(role, ()), evidence) for role in AGENT_TEAM_ROLES if role != "portfolio_manager_agent"
    )
    provider_mode = PROVIDER_MODE
    provider_runs: list[ProviderRunMeta] = []
    if live_provider_enabled and llm_provider is not None:
        provider_mode = LIVE_PROVIDER_MODE
        live_findings: list[RoleFindingSet] = []
        for finding in raw_findings:
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
    audit = audit_findings(raw_findings, by_role, received)
    audited_findings = audit[1]
    auditor = audit[0]
    open_questions = _open_questions_from_contradictions(auditor.contradictions)

    if auditor.repass_triggered and role_finding_override is not None:
        repass_findings = tuple(role_finding_override(finding.role_name, finding) for finding in audited_findings)
        repass_auditor, audited_findings = audit_findings(repass_findings, by_role, received, repass=True)
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
        content = str(response_payload.get("content_markdown") or "").strip()
        if not content:
            return LiveRoleResult(
                _live_provider_fallback(deterministic, "unavailable"),
                provider_run,
            )
        proposed_finding = RoleFinding(
            finding_type=deterministic.findings[0].finding_type,
            claim_text=content,
            evidence_refs=evidence_refs,
            caveat_codes=tuple(dict.fromkeys(code for finding in deterministic.findings for code in finding.caveat_codes)),
        )
        hard_block = _hard_block_flag(proposed_finding)
        if hard_block is not None:
            return LiveRoleResult(
                _live_provider_fallback(deterministic, "safety_fallback", eval_flag=hard_block),
                provider_run,
            )
        validate_llm_provider_output(response_payload, label="tool-mediated live provider response")
        return LiveRoleResult(
            RoleFindingSet(
                role_name=deterministic.role_name,
                role_status="completed",
                findings=(proposed_finding,),
                warning_codes=tuple(dict.fromkeys((*deterministic.warning_codes, "live_provider_reasoning_used"))),
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
    role = role_definition(role_name)  # type: ignore[arg-type]
    sanitized_results = tuple(_prompt_tool_result_envelope(result) for result in role_results)
    messages = (
        LLMProviderMessage(
            role="system",
            content=(
                f"You are {role.display_name}. Provide read-only context for the locked question: "
                "what could be overlooked during manual review. Use only supplied evidence refs. "
                "Do not provide action instructions, rankings, generated metrics, or conclusions about whether to act."
            ),
        ),
        LLMProviderMessage(
            role="user",
            content=repr(
                {
                    "allowed_evidence_refs": evidence_refs,
                    "tool_result_envelopes": sanitized_results,
                    "output_rule": "one concise background-context sentence with no numeric metrics",
                }
            ),
        ),
    )
    return LLMProviderRequest(
        request_id=f"p34a_{role_name}_tool_mediated",
        role_name=role_name,  # type: ignore[arg-type]
        messages=messages,
        provider=provider.provider_name,
        model=provider.model,
        prompt_version=LIVE_PROMPT_VERSION,
        max_tokens=320,
        timeout_seconds=30,
        temperature=0.0,
        metadata={"runner_mode": LIVE_PROVIDER_MODE},
    )


def _prompt_tool_result_envelope(result: ToolResult) -> dict[str, object]:
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
        "is_mock": result.is_mock,
    }
    validate_tool_payload(envelope, label="live provider prompt tool result envelope")
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
    )


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


def audit_findings(
    finding_sets: tuple[RoleFindingSet, ...],
    results_by_role: dict[str, tuple[ToolResult, ...]],
    received_refs_by_role: dict[str, frozenset[str]],
    *,
    repass: bool = False,
) -> tuple[AuditorRecord, tuple[RoleFindingSet, ...]]:
    availability_by_role = _availability_by_role(results_by_role)
    usable = usable_content_by_role()
    dropped: list[str] = []
    flags: list[str] = []
    audited: list[RoleFindingSet] = []
    fixable_failure = False
    for finding_set in finding_sets:
        flags.extend(code for code in finding_set.warning_codes if code in AUDITOR_EVAL_WARNING_CODES)
        findings: list[RoleFinding] = []
        for finding in finding_set.findings:
            blocked_flag = _hard_block_flag(finding)
            if blocked_flag is not None:
                dropped.append(blocked_flag)
                flags.append(blocked_flag)
                continue
            refs = tuple(ref for ref in finding.evidence_refs if ref in received_refs_by_role.get(finding_set.role_name, frozenset()))
            if not refs:
                dropped.append("unsupported_claim")
                fixable_failure = True
                continue
            filtered = tuple(ref for ref in refs if ref in usable[finding_set.role_name])
            if len(filtered) != len(refs):
                dropped.append("citable_boundary_filtered")
                fixable_failure = True
            available = tuple(
                ref
                for ref in filtered
                if availability_by_role.get(finding_set.role_name, {}).get(ref) in {"available", "limited"}
            )
            if len(available) != len(filtered):
                dropped.append("unavailable_ref_filtered")
                fixable_failure = True
            if not available:
                continue
            findings.append(
                RoleFinding(
                    finding_type=finding.finding_type,
                    claim_text=finding.claim_text,
                    evidence_refs=available,
                    caveat_codes=finding.caveat_codes,
                )
            )
        audited.append(
            RoleFindingSet(
                role_name=finding_set.role_name,
                role_status=finding_set.role_status,
                findings=tuple(findings),
                warning_codes=tuple(dict.fromkeys((*finding_set.warning_codes, *flags))),
                unavailable_reason=finding_set.unavailable_reason,
            )
        )
    contradictions = _detect_contradictions(tuple(audited))
    if contradictions:
        flags.append("contradiction_open_question")
    verdicts = tuple((item.role_name, bool(item.findings) or item.role_status == "skipped") for item in audited)
    return (
        AuditorRecord(
            audit_version=AUDIT_VERSION,
            role_verdicts=verdicts,
            contradictions=contradictions,
            dropped_claims=tuple(dict.fromkeys(dropped)),
            repass_triggered=(fixable_failure or bool(contradictions)) and not repass,
            eval_flags=tuple(dict.fromkeys(flags)),
        ),
        tuple(audited),
    )


def build_tool_mediated_agent_team_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime | None = None,
    registry: dict[str, ToolRegistryEntry] | None = None,
    role_finding_override: Callable[[str, RoleFindingSet], RoleFindingSet] | None = None,
    llm_provider: LLMProvider | None = None,
    live_provider_enabled: bool = False,
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
    )


def _public_role_findings(
    role_name: str,
    role_results: tuple[ToolResult, ...],
    evidence: SavedEvidencePackageRead,
) -> RoleFindingSet:
    projection = build_public_role_evidence_projection(evidence, role_name=role_name)  # type: ignore[arg-type]
    received = _received_refs(role_results)
    if role_name == "technical_analyst" and "market_quote_freshness" in received:
        return RoleFindingSet(
            role_name=role_name,
            role_status="completed",
            findings=(
                RoleFinding(
                    finding_type="missing_context",
                    claim_text=_public_claim_text(role_name, limited=False),
                    evidence_refs=("trade_intent_summary", "market_quote_freshness"),
                ),
            ),
            warning_codes=(),
        )
    if role_name == "news_analyst" and "economic_awareness_snapshot" in received:
        return RoleFindingSet(
            role_name=role_name,
            role_status="completed",
            findings=(
                RoleFinding(
                    finding_type="missing_context",
                    claim_text=(
                        "FRED macro calendar metadata is available as economic context only; "
                        "public news/event interpretation remains unreviewed."
                    ),
                    evidence_refs=("trade_intent_summary", "economic_awareness_snapshot"),
                    caveat_codes=("fred_economic_awareness_context_only",),
                ),
            ),
            warning_codes=("fred_economic_awareness_context_only",),
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
                claim_text="Freshness categories should be checked because saved evidence may age before manual review.",
                evidence_refs=freshness_refs,
            )
        )
    if "scope_state" in available:
        findings.append(
            RoleFinding(
                finding_type="missing_context",
                claim_text="Saved scope and account-feasibility caveats remain important manual-review context.",
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
                claim_text="Evidence sections outside the saved package remain open context gaps for manual review.",
                evidence_refs=anchors or ("trade_intent_summary",),
            )
        )
    return RoleFindingSet(
        role_name="risk_management_agent",
        role_status="completed",
        findings=tuple(findings),
        warning_codes=warnings,
    )


def _summary_payload_from_run_state(
    run_state: ToolMediatedRunState,
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime,
) -> dict:
    role_summaries = tuple(_role_summary_from_findings(item) for item in run_state.audited_findings)
    synthesis_refs = _synthesis_evidence_references(run_state.audited_findings)
    synthesis = _synthesis_markdown(evidence, synthesis_refs, run_state.open_questions)
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
        provider_mode=run_state.provider_mode,  # type: ignore[arg-type]
        plan_version=run_state.plan.plan_version,
        audit_version=run_state.auditor.audit_version,
        locked_question=run_state.catalog.locked_question,
        dimensions=run_state.plan.dimensions,
        role_plan=tuple(asdict(role_plan) for role_plan in run_state.plan.role_plan),
        tool_results=tuple(_frozen_tool_result(result) for result in run_state.tool_results),
        audited_findings=tuple(asdict(finding_set) for finding_set in run_state.audited_findings),
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


def _role_summary_from_findings(finding_set: RoleFindingSet) -> SavedAgentTeamRoleSummaryRead:
    role = role_definition(finding_set.role_name)  # type: ignore[arg-type]
    refs = _ordered_refs(_union_refs(finding_set.findings))
    if finding_set.role_status == "skipped" and finding_set.role_name in PUBLIC_ANALYST_ROLES:
        refs = ("trade_intent_summary",)
    summary = None
    if finding_set.findings:
        summary = " ".join(finding.claim_text for finding in finding_set.findings)
    provider_status = "ok" if finding_set.role_status == "completed" else "skipped"
    return SavedAgentTeamRoleSummaryRead(
        role_name=finding_set.role_name,
        display_name=role.display_name,
        role_status=finding_set.role_status,  # type: ignore[arg-type]
        provider_status=provider_status,
        summary_markdown=summary,
        evidence_references=refs,
        warning_codes=finding_set.warning_codes,
        unavailable_reason=finding_set.unavailable_reason,
    )


def _portfolio_manager_finding_set(
    audited_findings: tuple[RoleFindingSet, ...],
    open_questions: tuple[str, ...],
) -> RoleFindingSet:
    refs = _synthesis_evidence_references(audited_findings)
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
                + (" Open questions remain for manual review." if open_questions else ""),
                evidence_refs=refs,
            ),
        ),
        warning_codes=(),
    )


def _synthesis_markdown(
    evidence: SavedEvidencePackageRead,
    evidence_refs: tuple[str, ...],
    open_questions: tuple[str, ...],
) -> str:
    open_question_clause = ""
    if open_questions:
        open_question_clause = " Open questions for manual review: " + " ".join(open_questions)
    account_clause = ""
    if not evidence.scope_state.account_level_feasibility_evaluated:
        account_clause = " Account-level feasibility was not evaluated in the saved scope."
    market_clause = ""
    if "market_quote_freshness" not in evidence_refs:
        market_clause = " Market quote freshness is unavailable or not cited in the saved evidence."
    return (
        "What you would be ignoring if you acted manually now: deterministic risk flags; "
        "data freshness and availability gaps; scope and feasibility caveats; and context not reviewed "
        "in the saved package."
        f"{market_clause}{account_clause}{open_question_clause} "
        "Manual verification checklist: review saved scope, freshness categories, feasibility caveats, "
        "option-leg mechanics, and missing public context before acting on your own. "
        "This is read-only context for manual review, not an instruction or judgment about whether to act."
    )


def _hard_block_flag(finding: RoleFinding) -> str | None:
    payload = asdict(finding)
    if find_forbidden_keys(payload, forbidden_keys=TOOL_FORBIDDEN_KEYS) or find_forbidden_string_values(payload):
        return "private_leak_blocked"
    rendered = repr(payload).lower()
    if any(phrase in rendered for phrase in (*REPORT_PROHIBITED_PHRASES, *TOOL_PROHIBITED_PHRASES)):
        return "advice_wording_blocked"
    if find_prohibited_llm_phrases(payload):
        return "advice_wording_blocked"
    if find_secret_like_values(payload):
        return "private_leak_blocked"
    if any(pattern.search(rendered) for pattern in (*TOOL_GENERATED_METRIC_PATTERNS, *INVENTED_LEVEL_PATTERNS, *SOURCE_LEAK_PATTERNS)):
        return "invented_metric_blocked"
    return None


def _detect_contradictions(finding_sets: tuple[RoleFindingSet, ...]) -> tuple[Contradiction, ...]:
    by_ref: dict[str, list[tuple[str, RoleFinding]]] = {}
    for finding_set in finding_sets:
        for finding in finding_set.findings:
            for ref in finding.evidence_refs:
                by_ref.setdefault(ref, []).append((finding_set.role_name, finding))
    contradictions: list[Contradiction] = []
    for ref, findings in by_ref.items():
        for index, (role_a, finding_a) in enumerate(findings):
            for role_b, finding_b in findings[index + 1 :]:
                if _opposing_structured_signal(finding_a, finding_b):
                    contradictions.append(
                        Contradiction(
                            evidence_ref=ref,
                            role_a=role_a,
                            role_b=role_b,
                            description="Roles surfaced conflicting freshness or availability stance.",
                        )
                    )
    return tuple(contradictions)


def _opposing_structured_signal(a: RoleFinding, b: RoleFinding) -> bool:
    a_signal = _structured_signal(a.caveat_codes)
    b_signal = _structured_signal(b.caveat_codes)
    return {a_signal, b_signal} == {"positive", "negative"}


def _structured_signal(caveat_codes: tuple[str, ...]) -> str | None:
    rendered = repr(caveat_codes).lower()
    negative = any(token in rendered for token in STRUCTURED_NEGATIVE_SIGNAL_TOKENS)
    positive = any(token in rendered for token in STRUCTURED_POSITIVE_SIGNAL_TOKENS)
    if negative and not positive:
        return "negative"
    if positive and not negative:
        return "positive"
    return None


def _received_refs_by_role(results_by_role: dict[str, tuple[ToolResult, ...]]) -> dict[str, frozenset[str]]:
    return {role: frozenset(_received_refs(results)) for role, results in results_by_role.items()}


def _received_refs(results: tuple[ToolResult, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for result in results:
        if result.availability in {"available", "limited"}:
            refs.extend(result.evidence_refs)
    return tuple(dict.fromkeys(refs))


def _availability_by_role(results_by_role: dict[str, tuple[ToolResult, ...]]) -> dict[str, dict[str, str]]:
    availability: dict[str, dict[str, str]] = {}
    for role, results in results_by_role.items():
        availability[role] = {}
        for result in results:
            for ref in result.evidence_refs:
                availability[role][ref] = result.availability
    return availability


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
    lowered = (label or "").lower()
    if "stale" in lowered:
        return "stale"
    if "unavailable" in lowered or "not available" in lowered:
        return "not_available"
    if "unknown" in lowered:
        return "unknown"
    if label:
        return "fresh"
    return None


def _registry_from_catalog(catalog: EvidenceCatalog) -> dict[str, ToolRegistryEntry]:
    default = default_tool_registry()
    return {tool.tool_name: default[tool.tool_name] for tool in catalog.tools if tool.tool_name in default}


def _open_questions_from_contradictions(contradictions: tuple[Contradiction, ...]) -> tuple[str, ...]:
    return tuple(
        f"{item.evidence_ref} has conflicting freshness or availability framing across reviewed roles."
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
