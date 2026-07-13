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
from app.services.agent_team.llm_clients.contracts import AGENT_TEAM_ROLES, AgentTeamRole
from app.services.agent_team.safety.prompt_safety import validate_agent_team_text
from app.services.agent_team.agents.roles import PORTFOLIO_AWARE_ROLES, PUBLIC_ANALYST_ROLES
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
    "market_context_snapshot",
    "public_company_profile",
    "economic_awareness_context",
    "sec_recent_filings_metadata",
    "evidence_gap_inspector",
    "calc_exposure_delta",
    "calc_concentration_metrics",
    "calc_cash_impact",
    "calc_option_structure",
    "calc_scenario_exposure",
    "calc_price_range_position",
    "calc_return_windows",
    "calc_drawdown_stats",
    "calc_volatility_stats",
    "calc_ma_relationships",
    "calc_financial_ratios",
    "calc_period_change",
    "calc_macro_series_change",
    "calc_event_window",
    "calc_freshness_inventory",
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
P36_CALC_TOOL_CONTRACT_VERSION = "p36_calc_envelope_v1"
P36_CALC_TOOL_NAMES = frozenset(
    {
        "calc_exposure_delta",
        "calc_concentration_metrics",
        "calc_cash_impact",
        "calc_option_structure",
        "calc_scenario_exposure",
        "calc_price_range_position",
        "calc_return_windows",
        "calc_drawdown_stats",
        "calc_volatility_stats",
        "calc_ma_relationships",
        "calc_financial_ratios",
        "calc_period_change",
        "calc_macro_series_change",
        "calc_event_window",
        "calc_freshness_inventory",
    }
)
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
FRED_ECONOMIC_AWARENESS_FACT_KEYS = frozenset(
    {
        "release_name",
        "event_name",
        "release_date",
        "event_date",
    }
)
FRED_ECONOMIC_AWARENESS_FORBIDDEN_FACT_KEYS = frozenset(
    {
        "actual",
        "actual_label",
        "forecast",
        "forecast_label",
        "observation",
        "observation_label",
        "observations",
        "previous",
        "previous_label",
        "raw_observation",
        "value",
        "value_label",
    }
)
FRED_ECONOMIC_AWARENESS_FORBIDDEN_VALUE_TOKENS = frozenset(
    {
        "actual",
        "forecast",
        "observation",
        "previous",
        "value",
        "beat",
        "miss",
        "surprise",
    }
)
FRED_ECONOMIC_AWARENESS_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FRED_ECONOMIC_AWARENESS_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .,&'()/-]{2,119}$")
SEC_RECENT_FILINGS_SOURCE_KEY = "sec_edgar_recent_filings"
SEC_RECENT_FILINGS_SOURCE_LABEL = "SEC EDGAR recent filing metadata - company events only"
SEC_RECENT_FILINGS_ATTRIBUTION = (
    "Source: SEC EDGAR submissions/index metadata. Recent filing metadata only. "
    "Not investment advice or a trading signal."
)
SEC_RECENT_FILINGS_CAVEAT = (
    "EDGAR filing metadata may lag, be corrected, or omit filings that are not available through EDGAR. "
    "Portfolio Copilot does not interpret filing contents or treat filing metadata as a trading signal."
)
SEC_RECENT_FILINGS_NON_ENDORSEMENT = (
    "Use of SEC EDGAR data does not imply endorsement by the U.S. Securities and Exchange Commission."
)
SEC_RECENT_FILINGS_FACT_KEYS = frozenset({"form_type", "filing_date", "filing_reference"})
SEC_NORMALIZED_FILING_REFERENCE_RE = re.compile(r"^filref_[a-z0-9][a-z0-9_-]{5,79}$")
# The filename alternative requires a letter-initial extension (htm, txt,
# xml, ...). A digit-only "extension" is a decimal number, not a file: v3
# live reports legitimately cite frozen values like 187.42, and those must
# not be blocked as raw SEC paths (P34A-T18 field fix; file/path coverage
# is unchanged for every real extension).
SEC_RAW_PATH_OR_FILE_RE = re.compile(
    r"(/archives/|\\archives\\|edgar/data|(?:^|[\\/\s])[a-z0-9][a-z0-9_.-]*\.[a-z][a-z0-9]{1,7}\b)",
    re.IGNORECASE,
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
    "article_body",
    "exhibit_text",
    "filing_body",
    "filing_text",
    "forecast_label",
    "html",
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
    "newsapi",
    "benzinga",
    "finnhub",
    "polygon news",
    "gdelt",
    "web search",
    "scraping",
    "filing text",
    "filing body",
    "exhibit text",
    "raw sec payload",
    "sec file path",
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


def validate_tool_payload(
    value: object,
    *,
    label: str,
    allow_p36_calculation_values: bool = False,
) -> None:
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
    metric_paths = _find_generated_metric_strings(
        value,
        allow_quantity_units=allow_p36_calculation_values,
    )
    if metric_paths:
        raise ValueError(f"{label} contains invented/generated metric text: {sorted(metric_paths)}")
    validate_saved_review_artifact_payload(value)


def _find_generated_metric_strings(
    value: object,
    *,
    prefix: str = "",
    allow_quantity_units: bool = False,
) -> set[str]:
    if isinstance(value, str):
        patterns = TOOL_GENERATED_METRIC_PATTERNS
        if allow_quantity_units:
            patterns = tuple(
                pattern
                for pattern in TOOL_GENERATED_METRIC_PATTERNS
                if "shares?" not in pattern.pattern and "contracts?" not in pattern.pattern
            )
        if any(pattern.search(value) for pattern in patterns):
            return {prefix or "<value>"}
        return set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(
                _find_generated_metric_strings(
                    item,
                    prefix=key_path,
                    allow_quantity_units=allow_quantity_units,
                )
            )
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(
                _find_generated_metric_strings(
                    item,
                    prefix=item_path,
                    allow_quantity_units=allow_quantity_units,
                )
            )
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
        if self.tool_name in P36_CALC_TOOL_NAMES:
            # F-12: plain topic vocabulary belongs to the p36 identifier
            # boundary. The calculation registry is never a legacy prompt
            # payload, so keep its compound-key/secret/advice checks without
            # applying the legacy bare-word scanner.
            validate_tool_payload(
                asdict(self),
                label="p36 calculation registry entry",
                allow_p36_calculation_values=True,
            )
        else:
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
        is_p36_calculation = self.contract_version == P36_CALC_TOOL_CONTRACT_VERSION
        if self.contract_version not in {P33A_TOOL_CONTRACT_VERSION, P36_CALC_TOOL_CONTRACT_VERSION}:
            raise ValueError("unsupported tool result contract version")
        if is_p36_calculation:
            _validate_p36_calculation_result(self)
        validate_tool_payload(
            asdict(self),
            label="tool result",
            allow_p36_calculation_values=is_p36_calculation,
        )


def _validate_p36_calculation_result(result: ToolResult) -> None:
    """Validate the value-bearing P36 envelope without widening legacy tools."""

    if result.tool_name not in P36_CALC_TOOL_NAMES:
        raise ValueError("p36 calculation contract is restricted to approved calculation tools")
    public_calculations = {
        "calc_price_range_position", "calc_return_windows", "calc_drawdown_stats", "calc_volatility_stats",
        "calc_ma_relationships", "calc_financial_ratios", "calc_period_change", "calc_macro_series_change",
        "calc_event_window", "calc_freshness_inventory",
    }
    expected_tier = "public" if result.tool_name in public_calculations else "agent_safe"
    if result.evidence_tier != expected_tier or result.data_mode != expected_tier:
        raise ValueError("p36 calculation result tier does not match its reviewed tool contract")
    payload = result.summary_payload
    required = {"calc_name", "inputs_used", "value_labels", "method_label", "as_of_labels", "caveats", "outcome"}
    if set(payload) != required:
        raise ValueError("p36 calculation payload must use the approved envelope keys")
    if payload.get("calc_name") != result.tool_name:
        raise ValueError("p36 calculation payload calc_name must match tool_name")
    if not isinstance(payload.get("inputs_used"), (tuple, list)) or not all(
        isinstance(item, str) and item.strip() for item in payload["inputs_used"]
    ):
        raise ValueError("p36 calculation inputs_used must contain frozen evidence references")
    if not isinstance(payload.get("method_label"), str) or not payload["method_label"].strip():
        raise ValueError("p36 calculation method_label is required")
    if not isinstance(payload.get("as_of_labels"), (tuple, list)) or not all(
        isinstance(item, str) and item.strip() for item in payload["as_of_labels"]
    ):
        raise ValueError("p36 calculation as_of_labels must be a non-empty string sequence")
    if not isinstance(payload.get("caveats"), (tuple, list)) or not all(
        isinstance(item, str) and item.strip() for item in payload["caveats"]
    ):
        raise ValueError("p36 calculation caveats must be a string sequence")
    if payload.get("outcome") not in {"available", "limited", "unable_to_verify", "not_applicable"}:
        raise ValueError("p36 calculation outcome is not approved")
    labels = payload.get("value_labels")
    if not isinstance(labels, (tuple, list)):
        raise ValueError("p36 calculation value_labels must be a sequence")
    for row in labels:
        if not isinstance(row, dict) or set(row) != {"fact_key", "value_label", "unit_label"}:
            raise ValueError("p36 calculation value labels require fact_key, value_label, and unit_label")
        fact_key = row.get("fact_key")
        value_label = row.get("value_label")
        unit_label = row.get("unit_label")
        if not all(isinstance(item, str) and item.strip() for item in (fact_key, value_label, unit_label)):
            raise ValueError("p36 calculation value labels must contain safe non-empty text")
        if re.fullmatch(r"[a-z][a-z0-9_]{0,79}", fact_key) is None:
            raise ValueError("p36 calculation fact_key must be a safe machine label")


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
