"""Tool-use governance and safe tool result envelopes.

This module defines the app-owned tool boundary for the Agent Team. It makes
**no** external / provider / broker / market-data / news / LLM / MCP calls. It
implements **no** MCP. Per ADR 0008 and P33A:

- three evidence tiers: ``public``, ``agent_safe``, ``private_forbidden``;
- **private-tier tools are prohibited** — constructing a registry entry or a
  result at the private tier raises;
- ``agent_safe`` tools may only be allowlisted to portfolio-aware roles; public
  roles must never be wired to non-public tools;
- the executable M1 tools are in-process, read-only projections over the frozen
  ``SavedEvidencePackageRead`` passed into the executor;
- every envelope (request, registry entry, result, audit record) validates against the
  privacy / wording / invented-metric boundary;
- audit records carry status/latency/cost only — never inputs, outputs, or
  payloads.
"""

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
import re
from typing import Literal

from app.schemas.reports import (
    SavedEvidencePackageRead,
    SavedEvidenceSectionRead,
    SavedPublicEvidenceSectionRead,
    validate_saved_review_artifact_payload,
    validate_saved_review_reference,
    validate_saved_review_source_reference,
)
from app.services.agent_team.llm_provider import AGENT_TEAM_ROLES, AgentTeamRole
from app.services.agent_team.prompt_safety import validate_agent_team_text
from app.services.agent_team.roles import PORTFOLIO_AWARE_ROLES, PUBLIC_ANALYST_ROLES
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


EvidenceTier = Literal["public", "agent_safe", "private_forbidden"]
ToolMode = Literal["mock", "sync"]
ToolStatus = Literal["ok", "unavailable", "timeout", "rate_limited", "blocked", "budget_exceeded"]
ToolDataMode = Literal["public", "synthetic", "agent_safe"]
ToolAvailability = Literal["available", "limited", "not_available", "not_reviewed", "not_applicable"]
ToolName = Literal[
    "trade_intent_summary",
    "portfolio_scope_context",
    "deterministic_review_findings",
    "broker_snapshot_freshness",
    "market_quote_freshness",
    "public_company_profile",
    "economic_awareness_context",
    "evidence_gap_inspector",
]

PRIVATE_TIER = "private_forbidden"
TOOL_EVIDENCE_TIERS: tuple[str, ...] = ("public", "agent_safe", "private_forbidden")
ALLOWED_TOOL_EVIDENCE_TIERS: tuple[str, ...] = ("public", "agent_safe")
TOOL_MODES: tuple[str, ...] = ("mock", "sync")
TOOL_STATUSES: tuple[str, ...] = ("ok", "unavailable", "timeout", "rate_limited", "blocked", "budget_exceeded")
TOOL_DATA_MODES: tuple[str, ...] = ("public", "synthetic", "agent_safe")
TOOL_AVAILABILITIES: tuple[str, ...] = (
    "available",
    "limited",
    "not_available",
    "not_reviewed",
    "not_applicable",
)
TOOL_DEGRADED_STATUSES: tuple[str, ...] = ("unavailable", "timeout", "rate_limited", "blocked", "budget_exceeded")
P33A_TOOL_CONTRACT_VERSION = "p33a_tool_result_v1"
FRED_ECONOMIC_AWARENESS_SOURCE_KEY = "fred_macro_calendar_metadata"
FRED_ECONOMIC_AWARENESS_SOURCE_LABEL = "FRED macro calendar metadata · economic context only"
FRED_ECONOMIC_AWARENESS_ATTRIBUTION = (
    "Source: FRED, Federal Reserve Bank of St. Louis. Economic release/calendar metadata only. "
    "Not investment advice or a trading signal."
)
FRED_ECONOMIC_AWARENESS_NOTICE = (
    "This product uses the FRED API but is not endorsed or certified by the Federal Reserve Bank of St. Louis."
)
FRED_ECONOMIC_AWARENESS_CAVEAT = (
    "FRED aggregates data from multiple sources; releases may lag, revise, or be subject to "
    "source-specific rights. Portfolio Copilot does not use this as a trade recommendation."
)
FRED_ECONOMIC_AWARENESS_APPROVAL_CODES = frozenset(
    {
        "fred_macro_calendar_metadata",
        "fred_economic_awareness_approved",
    }
)

TOOL_REQUEST_ARG_KEYS = frozenset({"section_key", "symbol_or_underlying", "role_key", "scope_category"})
TOOL_FORBIDDEN_KEYS = FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS | {
    "account_number",
    "broker_account_number",
    "provider_account_number",
    "broker_id",
    "provider_id",
    "quantity",
    "quantities",
    "lot",
    "lots",
    "tax_lot",
    "tax_lots",
    "prompt",
    "prompts",
    "trace",
    "traces",
    "llm_trace",
    "llm_traces",
    "log",
    "logs",
    "url",
    "urls",
    "source_url",
    "source_urls",
    "actual_label",
    "forecast_label",
    "previous_label",
    "observation",
    "observations",
    "raw_observation",
    "raw_observations",
    "api_key",
}
TOOL_FORBIDDEN_VALUE_TOKENS = (
    "account_id",
    "broker_account_id",
    "provider_account_id",
    "provider_connection_id",
    "provider_contract_id",
    "account_number",
    "raw_balance",
    "raw balances",
    "buying_power",
    "buying power",
    "raw_holdings",
    "raw holdings",
    "raw_positions",
    "raw positions",
    "raw_payload",
    "raw payload",
    "tax_lot",
    "tax lot",
    "tax lots",
    "api_key",
    "access_token",
    "secret",
    "prompt",
    "trace",
    "source_url",
    "http://",
    "https://",
    "fmp economic calendar",
    "cnn-derived",
    "fear & greed",
)
TOOL_PROHIBITED_PHRASES = (
    "you should",
    "i recommend",
    "recommend buying",
    "recommend selling",
    "place order",
    "place an order",
    "submit order",
    "submit an order",
    "execute trade",
    "execute the trade",
    "safe to trade",
    "ready to trade",
    "guaranteed return",
)
TOOL_GENERATED_METRIC_PATTERNS = (
    re.compile(r"(?<![A-Za-z])\$[0-9][0-9,]*(?:\.[0-9]+)?"),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s?%"),
    re.compile(r"\bprice target\b", re.IGNORECASE),
    re.compile(r"\b(probability|odds|chance)\s+(?:of|is|are)\b", re.IGNORECASE),
    re.compile(r"\b(?:roi|yield|breakeven|break-even)\b", re.IGNORECASE),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s*(?:shares?|contracts?)\b", re.IGNORECASE),
)


def validate_tool_payload(value: object, *, label: str) -> None:
    """Reject private data, unsafe wording, and invented metrics in tool shapes."""

    forbidden = find_forbidden_keys(value, forbidden_keys=TOOL_FORBIDDEN_KEYS)
    if forbidden:
        raise ValueError(f"{label} contains forbidden private fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for token in TOOL_FORBIDDEN_VALUE_TOKENS:
        if token in rendered:
            raise ValueError(f"{label} contains forbidden private value: {token}")
    for phrase in TOOL_PROHIBITED_PHRASES:
        if phrase in rendered:
            raise ValueError(f"{label} contains prohibited advice or execution wording: {phrase}")
    metric_paths = _find_generated_metric_strings(value)
    if metric_paths:
        raise ValueError(f"{label} contains invented/generated metric text: {sorted(metric_paths)}")
    validate_saved_review_artifact_payload(value)


def _find_generated_metric_strings(value: object, *, prefix: str = "") -> set[str]:
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in TOOL_GENERATED_METRIC_PATTERNS):
            return {prefix or "<value>"}
        return set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(_find_generated_metric_strings(item, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(_find_generated_metric_strings(item, prefix=item_path))
        return found
    return set()


def assert_tool_tier_allowed(evidence_tier: str) -> None:
    """Reject the private tier; the private tier may never back a tool."""

    if evidence_tier not in TOOL_EVIDENCE_TIERS:
        raise ValueError(f"unknown evidence tier: {evidence_tier}")
    if evidence_tier == PRIVATE_TIER:
        raise ValueError("private-tier (broker-data) tools are prohibited")


def assert_role_tier_allowed(evidence_tier: str, role_name: str) -> None:
    """Enforce the evidence-tier <-> role boundary for EVERY tool shape.

    - ``private_forbidden`` is prohibited for all shapes;
    - ``agent_safe`` may be used only by portfolio-aware roles;
    - ``public`` may be used by any known role.

    Shared by ``ToolResult``, ``ToolAuditRecord``, and the degraded-result
    builders so a public role can never construct an agent-safe (or private)
    tool artifact, matching the ``ToolRegistryEntry`` allowlist rule.
    """

    assert_tool_tier_allowed(evidence_tier)
    if role_name not in AGENT_TEAM_ROLES:
        raise ValueError(f"unknown role: {role_name}")
    if evidence_tier == "agent_safe" and role_name not in PORTFOLIO_AWARE_ROLES:
        raise ValueError(f"agent_safe tool tier is not permitted for public role: {role_name}")


def assert_role_data_mode_allowed(role_name: str, data_mode: str) -> None:
    """Public roles must never carry agent-safe data on a tool result."""

    if role_name in PUBLIC_ANALYST_ROLES and data_mode == "agent_safe":
        raise ValueError(f"agent_safe data mode is not permitted for public role: {role_name}")


@dataclass(frozen=True)
class ToolRegistryEntry:
    """Governance metadata for one approved (future) tool. No execution."""

    tool_name: str
    display_name: str
    evidence_tier: str
    role_allowlist: tuple[AgentTeamRole, ...]
    mode: str = "mock"
    timeout_seconds: int = 10
    max_retries: int = 0
    per_call_token_budget: int | None = None
    per_call_cost_cap: str | None = None
    is_mock: bool = True

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("tool_name must not be empty")
        assert_tool_tier_allowed(self.evidence_tier)
        if self.mode not in TOOL_MODES:
            raise ValueError(f"unsupported tool mode: {self.mode}")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if self.per_call_token_budget is not None and self.per_call_token_budget < 0:
            raise ValueError("per_call_token_budget must not be negative")
        if not self.role_allowlist:
            raise ValueError("role_allowlist must not be empty")
        unknown = [role for role in self.role_allowlist if role not in AGENT_TEAM_ROLES]
        if unknown:
            raise ValueError(f"unknown role(s) in allowlist: {', '.join(unknown)}")
        if self.evidence_tier == "agent_safe":
            leaked = [role for role in self.role_allowlist if role not in PORTFOLIO_AWARE_ROLES]
            if leaked:
                raise ValueError(
                    f"agent_safe tools may only be allowlisted to portfolio-aware roles; "
                    f"public role(s) not allowed: {', '.join(leaked)}"
                )
        validate_agent_team_text(asdict(self), label="tool registry entry")

    def allows_role(self, role_name: str) -> bool:
        return role_name in self.role_allowlist


@dataclass(frozen=True)
class ToolRequest:
    """Structured app-owned tool request. No free-form tool calls."""

    tool_name: str
    requesting_role: AgentTeamRole
    saved_source_reference: str | None = None
    saved_artifact_reference: str | None = None
    args: dict[str, str] = field(default_factory=dict)
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("tool_name must not be empty")
        if self.requesting_role not in AGENT_TEAM_ROLES:
            raise ValueError(f"unknown requesting_role: {self.requesting_role}")
        if self.saved_source_reference is not None:
            validate_saved_review_source_reference(self.saved_source_reference)
        if self.saved_artifact_reference is not None:
            validate_saved_review_reference(self.saved_artifact_reference)
        unknown_args = sorted(set(self.args) - TOOL_REQUEST_ARG_KEYS)
        if unknown_args:
            raise ValueError(f"tool request contains unsupported arg(s): {', '.join(unknown_args)}")
        validate_tool_payload(asdict(self), label="tool request")


@dataclass(frozen=True)
class ToolResult:
    """Safe P33A envelope for a tool result. Validated; private tier rejected."""

    tool_name: str
    role_name: AgentTeamRole
    status: str
    evidence_tier: str
    data_mode: str
    source_key: str = "saved_evidence"
    source_label: str = "Saved evidence package"
    availability: str = "available"
    freshness: str | None = None
    as_of: datetime | None = None
    scope: dict[str, object] = field(default_factory=dict)
    caveat_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    summary_payload: dict[str, object] = field(default_factory=dict)
    payload: dict[str, object] = field(default_factory=dict)
    provenance: str = "synthetic"
    latency_ms: int = 0
    estimated_cost: str = "0"
    is_mock: bool = True
    contract_version: str = P33A_TOOL_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.status not in TOOL_STATUSES:
            raise ValueError(f"unsupported tool status: {self.status}")
        if self.data_mode not in TOOL_DATA_MODES:
            raise ValueError(f"unsupported tool data mode: {self.data_mode}")
        if self.availability not in TOOL_AVAILABILITIES:
            raise ValueError(f"unsupported tool availability: {self.availability}")
        assert_role_tier_allowed(self.evidence_tier, self.role_name)
        assert_role_data_mode_allowed(self.role_name, self.data_mode)
        if self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        if not self.summary_payload and self.payload:
            object.__setattr__(self, "summary_payload", dict(self.payload))
        validate_tool_payload(asdict(self), label="tool result")


@dataclass(frozen=True)
class ToolAuditRecord:
    """Safe audit log entry. Status/latency/cost only — never inputs or payloads."""

    run_reference: str
    tool_name: str
    role_name: AgentTeamRole
    status: str
    evidence_tier: str
    latency_ms: int = 0
    estimated_cost: str = "0"
    is_mock: bool = True

    def __post_init__(self) -> None:
        if self.status not in TOOL_STATUSES:
            raise ValueError(f"unsupported tool status: {self.status}")
        assert_role_tier_allowed(self.evidence_tier, self.role_name)
        if self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        validate_agent_team_text(asdict(self), label="tool audit record")


def tool_audit_record_field_names() -> tuple[str, ...]:
    """Expose the audit shape so reviewers can confirm no payload/input fields."""

    return tuple(f.name for f in fields(ToolAuditRecord))


def build_tool_registry(entries: tuple[ToolRegistryEntry, ...]) -> dict[str, ToolRegistryEntry]:
    """Index approved entries by name. Raises on duplicate tool names."""

    registry: dict[str, ToolRegistryEntry] = {}
    for entry in entries:
        if entry.tool_name in registry:
            raise ValueError(f"duplicate tool_name: {entry.tool_name}")
        registry[entry.tool_name] = entry
    return registry


def is_tool_allowed_for_role(entry: ToolRegistryEntry, role_name: str) -> bool:
    return entry.allows_role(role_name)


def default_tool_registry() -> dict[str, ToolRegistryEntry]:
    """Return the P34A-M1 saved-evidence-backed offline tool allowlist."""

    all_roles = tuple(AGENT_TEAM_ROLES)
    portfolio_roles = tuple(PORTFOLIO_AWARE_ROLES)
    return build_tool_registry(
        (
            ToolRegistryEntry(
                tool_name="trade_intent_summary",
                display_name="Trade intent summary",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="portfolio_scope_context",
                display_name="Portfolio scope context",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="deterministic_review_findings",
                display_name="Deterministic review findings",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="broker_snapshot_freshness",
                display_name="Broker snapshot freshness",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="market_quote_freshness",
                display_name="Market quote freshness",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="public_company_profile",
                display_name="Public company profile",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="economic_awareness_context",
                display_name="Economic awareness context",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="evidence_gap_inspector",
                display_name="Evidence gap inspector",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
        )
    )


def execute_tool_request(
    request: ToolRequest,
    *,
    evidence: SavedEvidencePackageRead,
    registry: dict[str, ToolRegistryEntry] | None = None,
) -> ToolResult:
    """Execute one reviewed offline tool over the provided frozen saved evidence package."""

    active_registry = registry or default_tool_registry()
    entry = active_registry.get(request.tool_name)
    if entry is None:
        return _request_blocked_result(
            tool_name=request.tool_name,
            role_name=request.requesting_role,
            reason="Requested tool is not in the reviewed allowlist.",
        )
    if not entry.allows_role(request.requesting_role):
        return _request_blocked_result(
            tool_name=entry.tool_name,
            role_name=request.requesting_role,
            reason="Requesting role is not allowed to receive this tool tier.",
        )
    if entry.evidence_tier == "agent_safe" and request.requesting_role in PUBLIC_ANALYST_ROLES:
        return _request_blocked_result(
            tool_name=entry.tool_name,
            role_name=request.requesting_role,
            reason="Public roles cannot receive portfolio-aware evidence.",
        )

    builders = {
        "trade_intent_summary": _tool_trade_intent_summary,
        "portfolio_scope_context": _tool_portfolio_scope_context,
        "deterministic_review_findings": _tool_deterministic_review_findings,
        "broker_snapshot_freshness": _tool_broker_snapshot_freshness,
        "market_quote_freshness": _tool_market_quote_freshness,
        "public_company_profile": _tool_public_company_profile,
        "economic_awareness_context": _tool_economic_awareness_context,
        "evidence_gap_inspector": _tool_evidence_gap_inspector,
    }
    return builders[entry.tool_name](request=request, evidence=evidence, entry=entry)


def _degraded_result(
    *,
    tool_name: str,
    role_name: AgentTeamRole,
    evidence_tier: str,
    status: str,
    source_key: str = "tool_policy",
    source_label: str = "Tool policy",
    summary_payload: dict[str, object] | None = None,
) -> ToolResult:
    if status not in TOOL_DEGRADED_STATUSES:
        raise ValueError(f"not a degraded status: {status}")
    # Enforce the role <-> tier boundary up front (also enforced by ToolResult),
    # so a public role can never produce an agent-safe/private degraded result.
    assert_role_tier_allowed(evidence_tier, role_name)
    return ToolResult(
        tool_name=tool_name,
        role_name=role_name,
        status=status,
        evidence_tier=evidence_tier,
        data_mode="synthetic",
        source_key=source_key,
        source_label=source_label,
        availability="not_available",
        evidence_refs=(),
        summary_payload=summary_payload or {},
        payload={},
        provenance="degraded_no_data",
        freshness=None,
        latency_ms=0,
        estimated_cost="0",
        is_mock=True,
    )


def _request_blocked_result(*, tool_name: str, role_name: AgentTeamRole, reason: str) -> ToolResult:
    """Return a public/synthetic blocked result for a rejected request.

    This avoids constructing an ``agent_safe`` artifact for public roles while
    still giving the runner an honest ToolResult envelope.
    """

    return ToolResult(
        tool_name=tool_name,
        role_name=role_name,
        status="blocked",
        evidence_tier="public",
        data_mode="synthetic",
        source_key="tool_policy",
        source_label="Tool policy",
        availability="not_available",
        summary_payload={"summary": reason},
        provenance="degraded_no_data",
        is_mock=True,
    )


def _tool_trade_intent_summary(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    summary = evidence.trade_intent_summary
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_trade_intent_summary",
        source_label="Saved trade intent summary",
        availability="available",
        evidence_refs=("trade_intent_summary",),
        summary_payload={
            "supported_flow": summary.supported_flow,
            "review_flow_label": summary.review_flow_label,
            "symbol_or_underlying": summary.symbol_or_underlying,
        },
    )


def _tool_portfolio_scope_context(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    scope = evidence.scope_state
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_scope_state",
        source_label="Saved portfolio scope context",
        availability="available",
        evidence_refs=("scope_state",),
        caveat_codes=scope.scope_caveat_codes,
        scope={
            "portfolio_scope_mode": scope.portfolio_scope_mode,
            "portfolio_selection_mode": scope.portfolio_selection_mode,
        },
        summary_payload={
            "review_account_selected": scope.review_account_selected,
            "review_account_included_in_portfolio_scope": scope.review_account_included_in_portfolio_scope,
            "review_account_is_feasibility_source": scope.review_account_is_feasibility_source,
            "account_level_feasibility_evaluated": scope.account_level_feasibility_evaluated,
        },
    )


def _tool_deterministic_review_findings(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    actionability = evidence.actionability
    citable_refs = ["actionability"]
    for section in (
        evidence.portfolio_impact_summary,
        evidence.concentration_risk_drift,
        evidence.cash_collateral_caveats,
        evidence.options_exposure_summary,
    ):
        if section.availability in {"available", "limited"}:
            citable_refs.append(section.section_key)
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_deterministic_review",
        source_label="Saved deterministic review findings",
        availability="limited",
        evidence_refs=tuple(dict.fromkeys(citable_refs)),
        caveat_codes=evidence.caveat_codes,
        summary_payload={
            "review_actionability_status": actionability.review_actionability_status,
            "actionability_label": actionability.actionability_label,
            "highest_severity": actionability.highest_severity,
            "report_status": actionability.report_status,
            "portfolio_impact_availability": evidence.portfolio_impact_summary.availability,
            "liquidity_collateral_availability": evidence.cash_collateral_caveats.availability,
            "options_exposure_availability": evidence.options_exposure_summary.availability,
        },
    )


def _tool_broker_snapshot_freshness(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    label = evidence.freshness.broker_snapshot_freshness_label
    return _section_result(
        request=request,
        entry=entry,
        section_key="freshness",
        source_key="saved_broker_snapshot_freshness",
        source_label="Saved broker snapshot freshness",
        availability="available" if label else "not_available",
        freshness=label,
        summary_payload={
            "freshness_label": label,
            "summary": (
                "Broker snapshot freshness label is available from saved evidence."
                if label
                else "Broker snapshot freshness label is not available in saved evidence."
            ),
        },
    )


def _tool_market_quote_freshness(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = evidence.market_quote_freshness
    return _section_result(
        request=request,
        entry=entry,
        section_key="market_quote_freshness",
        source_key="saved_market_quote_freshness",
        source_label="Saved market quote freshness",
        availability=section.availability,
        freshness=section.summary_label,
        caveat_codes=section.caveat_codes,
        summary_payload={
            "summary_label": section.summary_label,
            "section_label": section.section_label,
        },
    )


def _tool_public_company_profile(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    if evidence.public_evidence is None:
        return _unavailable_saved_section_result(
            request=request,
            entry=entry,
            source_key="saved_public_company_profile",
            source_label="Saved public company profile",
            evidence_ref="public_company_profile",
            summary="Public company profile was not attached to this saved evidence package.",
        )
    section = evidence.public_evidence.public_company_profile
    if section.availability not in {"available", "limited"}:
        return _public_section_result(
            request=request,
            entry=entry,
            section=section,
            status="unavailable",
        )
    return _public_section_result(request=request, entry=entry, section=section, status="ok")


def _tool_economic_awareness_context(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = evidence.economic_awareness_snapshot
    if not _is_approved_fred_economic_awareness_section(section):
        return _section_result(
            request=request,
            entry=entry,
            section_key="economic_awareness_snapshot",
            source_key=FRED_ECONOMIC_AWARENESS_SOURCE_KEY,
            source_label=FRED_ECONOMIC_AWARENESS_SOURCE_LABEL,
            availability="not_available",
            freshness=None,
            caveat_codes=("fred_economic_awareness_not_available",),
            summary_payload={
                "summary": "Approved FRED economic awareness metadata was not attached to this saved evidence package.",
                "availability": section.availability,
            },
        )
    return _section_result(
        request=request,
        entry=entry,
        section_key="economic_awareness_snapshot",
        source_key=FRED_ECONOMIC_AWARENESS_SOURCE_KEY,
        source_label=FRED_ECONOMIC_AWARENESS_SOURCE_LABEL,
        availability=section.availability,
        freshness=section.summary_label,
        caveat_codes=tuple(dict.fromkeys((*section.caveat_codes, "fred_economic_awareness_context_only"))),
        summary_payload={
            "reviewed_release_event_labels": section.detail_labels,
            "attribution": FRED_ECONOMIC_AWARENESS_ATTRIBUTION,
            "notice": FRED_ECONOMIC_AWARENESS_NOTICE,
            "caveat": FRED_ECONOMIC_AWARENESS_CAVEAT,
        },
    )


def _tool_evidence_gap_inspector(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    unavailable = _unavailable_evidence_refs(evidence)
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_evidence_gap_inspector",
        source_label="Saved evidence gap inspector",
        availability="limited" if unavailable else "available",
        evidence_refs=("trade_intent_summary", "scope_state"),
        caveat_codes=evidence.caveat_codes,
        summary_payload={
            "summary": (
                "Saved evidence has unavailable or unreviewed sections."
                if unavailable
                else "Saved evidence sections available to this tool have no unavailable gaps."
            ),
            "unavailable_evidence_refs": unavailable,
        },
    )


def _is_approved_fred_economic_awareness_section(section: SavedEvidenceSectionRead) -> bool:
    if section.section_key != "economic_awareness_snapshot":
        return False
    if section.availability not in {"available", "limited"}:
        return False
    caveat_tokens = {code.lower() for code in section.caveat_codes}
    return bool(FRED_ECONOMIC_AWARENESS_APPROVAL_CODES.intersection(caveat_tokens))


def _ok_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    source_key: str,
    source_label: str,
    availability: str,
    evidence_refs: tuple[str, ...],
    summary_payload: dict[str, object],
    caveat_codes: tuple[str, ...] = (),
    freshness: str | None = None,
    as_of: datetime | None = None,
    scope: dict[str, object] | None = None,
) -> ToolResult:
    citable_refs = evidence_refs if availability in {"available", "limited"} else ()
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status="ok" if availability in {"available", "limited"} else "unavailable",
        evidence_tier=entry.evidence_tier,
        data_mode="public" if entry.evidence_tier == "public" else "agent_safe",
        source_key=source_key,
        source_label=source_label,
        availability=availability,
        freshness=freshness,
        as_of=as_of,
        scope=scope or {},
        caveat_codes=caveat_codes,
        evidence_refs=citable_refs,
        summary_payload=summary_payload,
        provenance="saved_evidence_package",
        is_mock=entry.is_mock,
    )


def _section_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section_key: str,
    source_key: str,
    source_label: str,
    availability: str,
    summary_payload: dict[str, object],
    freshness: str | None = None,
    caveat_codes: tuple[str, ...] = (),
) -> ToolResult:
    return _ok_result(
        request=request,
        entry=entry,
        source_key=source_key,
        source_label=source_label,
        availability=availability,
        freshness=freshness,
        evidence_refs=(section_key,),
        caveat_codes=caveat_codes,
        summary_payload=summary_payload,
    )


def _public_section_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section: SavedPublicEvidenceSectionRead,
    status: str,
) -> ToolResult:
    citable_refs = (section.section_key,) if section.availability in {"available", "limited"} else ()
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status=status,
        evidence_tier=entry.evidence_tier,
        data_mode="public",
        source_key=section.source_key or "saved_public_evidence",
        source_label=section.source_label,
        availability=section.availability,
        freshness=section.freshness_label,
        as_of=section.as_of,
        caveat_codes=section.caveat_codes,
        evidence_refs=citable_refs,
        summary_payload={
            "section_key": section.section_key,
            "section_label": section.section_label,
            "summary_label": section.summary_label,
            "fact_keys_present": tuple(fact.fact_key for fact in section.facts),
            "rights_status": section.rights_status,
        },
        provenance="saved_public_evidence",
        is_mock=entry.is_mock,
    )


def _unavailable_saved_section_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    source_key: str,
    source_label: str,
    evidence_ref: str,
    summary: str,
) -> ToolResult:
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status="unavailable",
        evidence_tier=entry.evidence_tier,
        data_mode="public" if entry.evidence_tier == "public" else "agent_safe",
        source_key=source_key,
        source_label=source_label,
        availability="not_available",
        evidence_refs=(),
        summary_payload={"summary": summary},
        provenance="saved_evidence_package",
        is_mock=entry.is_mock,
    )


def _unavailable_evidence_refs(evidence: SavedEvidencePackageRead) -> tuple[str, ...]:
    unavailable: list[str] = []
    sections: tuple[SavedEvidenceSectionRead, ...] = (
        evidence.portfolio_impact_summary,
        evidence.before_after_portfolio_impact,
        evidence.concentration_risk_drift,
        evidence.cash_collateral_caveats,
        evidence.options_exposure_summary,
        evidence.market_quote_freshness,
        evidence.economic_awareness_snapshot,
        evidence.market_mood_snapshot,
    )
    for section in sections:
        if section.availability not in {"available", "limited"}:
            unavailable.append(section.section_key)
    if evidence.public_evidence is not None:
        for section in (
            evidence.public_evidence.public_company_profile,
            evidence.public_evidence.public_fundamentals_snapshot,
            evidence.public_evidence.public_news_snapshot,
            evidence.public_evidence.public_events_calendar,
            evidence.public_evidence.public_technical_context,
            evidence.public_evidence.public_market_context,
        ):
            if section.availability not in {"available", "limited"}:
                unavailable.append(section.section_key)
    return tuple(dict.fromkeys(unavailable))


def blocked_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    """Conceptual degrade-to-blocked (e.g. role not allowlisted). No execution."""

    return _degraded_result(tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="blocked")


def unavailable_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    return _degraded_result(tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="unavailable")


def timeout_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    return _degraded_result(tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="timeout")


def budget_exceeded_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    return _degraded_result(
        tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="budget_exceeded"
    )


def tool_result_for_disallowed_role(entry: ToolRegistryEntry, role_name: AgentTeamRole) -> ToolResult:
    """Return a safe ``blocked`` result when a role is not allowlisted. No execution."""

    if entry.allows_role(role_name):
        raise ValueError("role is allowed; no blocked result needed")
    return blocked_tool_result(
        tool_name=entry.tool_name, role_name=role_name, evidence_tier=entry.evidence_tier
    )
