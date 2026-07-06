"""Shared run-state models + constants for the tool-mediated runner (P34A-T11E).

Foundation module: dataclasses (findings, plan, catalog, run state, auditor
record) and pipeline constants. Depends only on the tool/safety/contract
layers — never on the runner or auditor — so it breaks the runner<->auditor
type cycle. No behavior change from the pre-split module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re
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
LIVE_PROMPT_VERSION = "p34a-tool-mediated-role-v2"
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
    "sec_recent_filings_metadata": ("public_events_calendar",),
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
LIVE_CONNECTIVE_DIGIT_RE = re.compile(r"\d")
SECTION_READABLE_LABELS: dict[str, str] = {
    "portfolio_impact_summary": "portfolio impact summary",
    "before_after_portfolio_impact": "before/after portfolio impact",
    "concentration_risk_drift": "concentration risk drift",
    "liquidity_collateral_caveats": "liquidity and collateral caveats",
    "options_exposure_summary": "options exposure summary",
    "market_quote_freshness": "market quote freshness",
    "economic_awareness_snapshot": "FRED macro calendar metadata",
    "market_mood_snapshot": "Market Mood snapshot",
    "public_company_profile": "public company profile",
    "public_fundamentals_snapshot": "public fundamentals snapshot",
    "public_news_snapshot": "public news snapshot",
    "public_events_calendar": "public events calendar",
    "public_technical_context": "public technical context",
    "public_market_context": "public market context",
}
SCOPE_CAVEAT_LABELS: dict[str, str] = {
    "account_level_feasibility_not_evaluated": "account-level feasibility was not evaluated",
    "selected_account_scope": "scope is limited to the selected account",
    "selected_context_scope": "scope is limited to the selected portfolio context",
    "portfolio_scope_not_latest": "portfolio scope may not reflect the latest account snapshot",
    "broker_position_truth_unstable": "broker position truth is not authoritative for deterministic feasibility",
    "current_position_truth_not_reviewed": "current-position truth was not reviewed",
    "cash_collateral_policy_not_reviewed": "cash collateral policy was not reviewed",
    "buying_power_display_only": "buying-power labels are display-only",
}


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
    model_chain_position: int | None = None
    attempted_models: tuple[str, ...] = ()

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
