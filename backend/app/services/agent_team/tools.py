"""Tool-use governance and safe tool result envelopes (P25A-T3, schema-only).

This module defines the GOVERNANCE SHAPES for a future agent tool layer. It
performs **no** tool execution and makes **no** external / provider / broker /
market-data / news / LLM / MCP calls. It implements **no** MCP. Per ADR 0008:

- three evidence tiers: ``public``, ``agent_safe``, ``private_forbidden``;
- **private-tier tools are prohibited** — constructing a registry entry or a
  result at the private tier raises;
- ``agent_safe`` tools may only be allowlisted to portfolio-aware roles; public
  roles must never be wired to non-public tools;
- only ``mock``/``sync`` modes exist now; async/queued is deferred;
- every envelope (registry entry, result, audit record) validates against the
  privacy / wording / invented-metric boundary;
- audit records carry status/latency/cost only — never inputs, outputs, or
  payloads.

Nothing here is invoked by the runtime runner; it is a reviewed schema seam.
"""

from dataclasses import asdict, dataclass, field, fields
from typing import Literal

from app.services.agent_team.llm_provider import AGENT_TEAM_ROLES, AgentTeamRole
from app.services.agent_team.output_safety import validate_llm_provider_output
from app.services.agent_team.prompt_safety import validate_agent_team_text
from app.services.agent_team.roles import PORTFOLIO_AWARE_ROLES, PUBLIC_ANALYST_ROLES


EvidenceTier = Literal["public", "agent_safe", "private_forbidden"]
ToolMode = Literal["mock", "sync"]
ToolStatus = Literal["ok", "unavailable", "timeout", "rate_limited", "blocked", "budget_exceeded"]
ToolDataMode = Literal["public", "synthetic", "agent_safe"]

PRIVATE_TIER = "private_forbidden"
TOOL_EVIDENCE_TIERS: tuple[str, ...] = ("public", "agent_safe", "private_forbidden")
ALLOWED_TOOL_EVIDENCE_TIERS: tuple[str, ...] = ("public", "agent_safe")
TOOL_MODES: tuple[str, ...] = ("mock", "sync")
TOOL_STATUSES: tuple[str, ...] = ("ok", "unavailable", "timeout", "rate_limited", "blocked", "budget_exceeded")
TOOL_DATA_MODES: tuple[str, ...] = ("public", "synthetic", "agent_safe")
TOOL_DEGRADED_STATUSES: tuple[str, ...] = ("unavailable", "timeout", "rate_limited", "blocked", "budget_exceeded")


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
class ToolResult:
    """Safe envelope for a (future) tool result. Validated; private tier rejected."""

    tool_name: str
    role_name: AgentTeamRole
    status: str
    evidence_tier: str
    data_mode: str
    payload: dict[str, object] = field(default_factory=dict)
    provenance: str = "synthetic"
    freshness: str | None = None
    latency_ms: int = 0
    estimated_cost: str = "0"
    is_mock: bool = True

    def __post_init__(self) -> None:
        if self.status not in TOOL_STATUSES:
            raise ValueError(f"unsupported tool status: {self.status}")
        if self.data_mode not in TOOL_DATA_MODES:
            raise ValueError(f"unsupported tool data mode: {self.data_mode}")
        assert_role_tier_allowed(self.evidence_tier, self.role_name)
        assert_role_data_mode_allowed(self.role_name, self.data_mode)
        if self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        validate_llm_provider_output(asdict(self), label="tool result")


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


def _degraded_result(
    *,
    tool_name: str,
    role_name: AgentTeamRole,
    evidence_tier: str,
    status: str,
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
        payload={},
        provenance="degraded_no_data",
        freshness=None,
        latency_ms=0,
        estimated_cost="0",
        is_mock=True,
    )


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
