from datetime import datetime
import re
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.trade_review_workspace import InstrumentIdentityRead, ReportScopeMetadataRead
from app.services.agent_team.llm_clients.contracts import find_secret_like_values
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys

ReportThreadStatus = Literal["draft", "running", "completed", "failed", "cancelled"]
ReportMessageSender = Literal["user", "system", "agent", "tool"]
ReportMessageType = Literal[
    "user_input",
    "system_event",
    "agent_output",
    "tool_output",
    "error",
    "retry_notice",
    "final_report",
    "markdown_report",
]
ReportMessageVisibility = Literal["private", "internal", "public_demo"]
SavedReviewSourceKind = Literal["trade_review_workspace", "agent_team_run"]
SavedReviewArtifactStatus = Literal["saved", "unavailable"]
SavedReviewAgentRunStatus = Literal["completed", "partially_completed", "failed"]
SavedEvidenceAvailability = Literal["available", "limited", "not_available", "not_reviewed", "not_applicable"]
SavedPublicEvidenceRightsStatus = Literal["reviewed", "internal_demo_only", "not_reviewed"]
SavedPublicEvidenceFreshnessCategory = Literal["fresh", "stale", "unknown", "not_available", "not_reviewed"]
SavedPublicEvidenceMode = Literal["not_reviewed", "synthetic_demo", "provider_reference"]
PublicEvidenceReadiness = Literal["ready", "partial", "not_ready"]
PublicEvidenceState = Literal["prepared", "frozen"]
AgentTeamGenerationRefusalReadiness = Literal["partial", "not_ready"]
AgentTeamGenerationNotReadyReasonCode = Literal[
    "public_evidence_not_prepared",
    "instrument_kind_not_confirmed",
    "instrument_kind_unresolved",
    "required_evidence_unavailable",
    "etf_evidence_contract_not_available",
    "evidence_privacy_validation_failed",
    "frozen_evidence_replacement_forbidden",
]
PublicEvidenceLaneRequirement = Literal["required", "optional", "not_applicable"]
PublicEvidenceReadinessCaveatCode = Literal[
    "instrument_kind_not_confirmed",
    "instrument_kind_unresolved",
    "etf_evidence_contract_not_available",
    "evidence_limited",
    "evidence_not_available",
    "evidence_not_reviewed",
]
PublicEvidenceLaneKey = Literal[
    "instrument_identity",
    "eod_history",
    "company_profile",
    "company_recent_filings",
    "company_fundamentals",
    "etf_profile",
    "etf_holdings",
    "etf_fund_events",
]
SavedPublicEvidenceSectionKey = Literal[
    "public_company_profile",
    "public_fundamentals_snapshot",
    "fred_macro_series_snapshot",
    "public_news_snapshot",
    "public_events_calendar",
    "public_technical_context",
    "public_market_context",
]
SavedPublicEvidenceSourceKey = Literal[
    "sec_edgar_submissions",
    "sec_edgar_recent_filings",
    "fmp_eod_history",
    "fmp_reported_statement_facts",
    "fred_macro_series",
]
_FMP_EOD_HISTORY_FACT_KEYS = frozenset({"eod_ohlcv_bar"})
_FMP_FUNDAMENTALS_FACT_KEYS = frozenset(
    {
        "income_statement_revenue",
        "income_statement_gross_profit",
        "income_statement_operating_income",
        "income_statement_net_income",
        "income_statement_earnings_per_share",
        "balance_sheet_total_assets",
        "balance_sheet_total_liabilities",
        "balance_sheet_total_debt",
        "balance_sheet_current_assets",
        "balance_sheet_current_liabilities",
        "cash_flow_operating_cash_flow",
        "cash_flow_capital_expenditure",
        "cash_flow_free_cash_flow",
    }
)
_FRED_MACRO_SERIES_FACT_KEYS = frozenset(
    {
        "fred_consumer_price_index",
        "fred_core_personal_consumption_expenditures",
        "fred_unemployment_rate",
        "fred_federal_funds_rate",
        "fred_ten_year_treasury_yield",
        "fred_yield_curve_spread",
    }
)
AgentTeamPublicRoleName = Literal["fundamentals_analyst", "news_analyst", "technical_analyst"]
AgentTeamReportStatus = Literal[
    "source_snapshot",
    "deterministic_draft",
    "full_agent_report",
    "agent_unavailable",
    "validation_failed",
]
AgentTeamReportRunCompleteness = Literal["full", "partial", "none"]
AgentTeamReportRoleStatus = Literal["completed", "unavailable", "skipped", "gated", "validation_failed"]
AgentTeamReportSynthesisAuthor = Literal["portfolio_manager_agent", "deterministic_template"]

_OPAQUE_SAVED_REVIEW_REFERENCE_RE = re.compile(r"^svrev_[a-z0-9][a-z0-9_-]{5,79}$")
_OPAQUE_SAVED_REVIEW_SOURCE_REFERENCE_RE = re.compile(
    r"^(trrev|workspace|agentrun)_[a-z0-9][a-z0-9_-]{5,79}$"
)
_INTERNAL_DISPLAY_TOKEN_RE = re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b")
_DERIVED_EXPOSURE_SECTION_KEYS = frozenset(
    {"before_after_portfolio_impact", "concentration_risk_drift"}
)
_SAVED_REVIEW_FORBIDDEN_KEYS = FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS | {
    "broker_id",
    "broker_ids",
    "broker_account_id",
    "provider_id",
    "provider_ids",
    "provider_trace_id",
    "provider_trace_ids",
    "quantity",
    "quantities",
    "tax_lot",
    "tax_lots",
    "transaction",
    "transactions",
    "order",
    "orders",
    "prompt",
    "prompts",
    "llm_trace",
    "llm_traces",
}
_SAVED_REVIEW_PROHIBITED_PHRASES = (
    "you should",
    "i recommend",
    "financial advice",
    "investment advice",
    "trading advice",
    "trade advice",
    "trade recommendation",
    "investment recommendation",
    "recommendation to buy",
    "recommendation to sell",
    "recommend buying",
    "recommend selling",
    "safe to trade",
    "ready to trade",
    "guaranteed",
    "guaranteed return",
    "place order",
    "submit order",
    "execute trade",
)
_SAVED_REVIEW_ALLOWED_NEGATED_DISCLOSURES = (
    (
        "source: fred, federal reserve bank of st. louis. economic release/calendar metadata only. "
        "not investment advice or a trading signal."
    ),
    (
        "fred aggregates data from multiple sources; releases may lag, revise, or be subject to "
        "source-specific rights. portfolio copilot does not use this as a trade recommendation."
    ),
    (
        "source: sec edgar submissions/index metadata. recent filing metadata only. "
        "not investment advice or a trading signal."
    ),
    (
        "edgar filing metadata may lag, be corrected, or omit filings that are not available through edgar. "
        "portfolio copilot does not interpret filing contents or treat filing metadata as a trading signal."
    ),
)
_SAVED_REVIEW_FORBIDDEN_REFERENCE_TOKENS = (
    "account",
    "acct",
    "broker",
    "provider",
    "snaptrade",
    "secret",
    "token",
    "cash",
    "holding",
    "position",
    "raw",
    "payload",
    "number",
    "taxlot",
    "tax_lot",
    "transaction",
    "order",
    "prompt",
    "trace",
)
_SAVED_REVIEW_FORBIDDEN_VALUE_TOKENS = (
    "provider_account_id",
    "broker_account_id",
    "account_number",
    "raw_payload",
    "raw_provider_payload",
    "raw_holdings",
    "raw_positions",
    "tax_lot",
    "tax lots",
    "raw_balance",
    "buying_power",
    "api_key",
    "access_token",
    "raw_prompt",
    "prompt text",
    "prompt:",
    "llm_trace",
    "provider_trace_id",
)
_PUBLIC_EVIDENCE_FORBIDDEN_KEYS = {
    "article_body",
    "article_bodies",
    "body",
    "completion",
    "completions",
    "html",
    "page_html",
    "prompt",
    "prompts",
    "raw_metadata",
    "raw_payload",
    "raw_provider_payload",
    "raw_response",
    "source_url",
    "source_urls",
    "trace",
    "traces",
    "url",
    "urls",
}
_PUBLIC_EVIDENCE_FORBIDDEN_VALUE_TOKENS = (
    "api_key",
    "access_token",
    "article body",
    "full article",
    "http://",
    "https://",
    "<html",
    "raw payload",
    "raw provider",
    "source_url",
)
_SAVED_TOOL_FREEZE_FORBIDDEN_VALUE_TOKENS = (
    "http://",
    "https://",
    "source_url",
    "raw url",
    "raw payload",
    "provider_account_id",
    "broker_account_id",
    "account_number",
    "buying_power",
    "raw_holdings",
    "raw_positions",
    "tax_lot",
    "trace",
)
_SAVED_TOOL_FREEZE_FORBIDDEN_KEYS = {
    "source_url",
    "source_urls",
    "url",
    "urls",
    "prompt",
    "prompts",
    "raw_prompt",
    "raw_prompts",
    "prompt_text",
    "prompt_messages",
    "trace",
    "traces",
}
_SAVED_TOOL_FREEZE_GENERATED_METRIC_PATTERNS = (
    re.compile(r"(?<![A-Za-z])\$[0-9][0-9,]*(?:\.[0-9]+)?"),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s?%"),
    re.compile(r"\bprice target\b", re.IGNORECASE),
    re.compile(r"\b(?:roi|yield|breakeven|break-even)\b", re.IGNORECASE),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s*(?:shares?|contracts?)\b", re.IGNORECASE),
)
_P36_CALC_TOOL_CONTRACT_VERSION = "p36_calc_envelope_v1"
_P36_TOOL_RUN_ARTIFACT_SCHEMA_VERSION = "p36_tool_run_freeze_v1"


def validate_saved_review_artifact_payload(value: object) -> None:
    forbidden = find_forbidden_keys(value, forbidden_keys=_SAVED_REVIEW_FORBIDDEN_KEYS)
    if forbidden:
        raise ValueError(f"saved review artifact contains forbidden private fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for token in _SAVED_REVIEW_FORBIDDEN_VALUE_TOKENS:
        if token in rendered:
            raise ValueError(f"saved review artifact contains forbidden private value: {token}")
    for disclosure in _SAVED_REVIEW_ALLOWED_NEGATED_DISCLOSURES:
        rendered = rendered.replace(disclosure, "")
    for phrase in _SAVED_REVIEW_PROHIBITED_PHRASES:
        if phrase in rendered:
            raise ValueError(f"saved review artifact contains prohibited wording: {phrase}")


def validate_saved_tool_freeze_payload(
    value: object,
    *,
    allow_p36_calculation_values: bool = False,
    allow_p36_live_markdown: bool = False,
    allow_p36_pm_synthesis: bool = False,
) -> None:
    """Validate frozen tool-mediated run artifacts before saved-report persistence."""

    validate_saved_review_artifact_payload(value)
    forbidden = find_forbidden_keys(value, forbidden_keys=_SAVED_TOOL_FREEZE_FORBIDDEN_KEYS)
    if forbidden:
        raise ValueError(f"saved tool-mediated run artifact contains forbidden raw-source fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for token in _SAVED_TOOL_FREEZE_FORBIDDEN_VALUE_TOKENS:
        if token in rendered:
            raise ValueError(f"saved tool-mediated run artifact contains forbidden value: {token}")
    metric_paths = _find_saved_tool_freeze_metric_strings(
        value,
        allow_quantity_units=allow_p36_calculation_values,
        allow_value_bearing_live_markdown=allow_p36_live_markdown,
        allow_p36_pm_synthesis=allow_p36_pm_synthesis,
    )
    if metric_paths:
        raise ValueError(f"saved tool-mediated run artifact contains generated metric text: {sorted(metric_paths)}")


def _find_saved_tool_freeze_metric_strings(
    value: object,
    *,
    prefix: str = "",
    allow_quantity_units: bool = False,
    allow_value_bearing_live_markdown: bool = False,
    allow_p36_pm_synthesis: bool = False,
) -> set[str]:
    if isinstance(value, str):
        patterns = _SAVED_TOOL_FREEZE_GENERATED_METRIC_PATTERNS
        if allow_quantity_units:
            patterns = tuple(
                pattern
                for pattern in _SAVED_TOOL_FREEZE_GENERATED_METRIC_PATTERNS
                if "shares?" not in pattern.pattern and "contracts?" not in pattern.pattern
            )
        if any(pattern.search(value) for pattern in patterns):
            return {prefix or "<value>"}
        return set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if allow_value_bearing_live_markdown and str(key) == "live_report_markdown":
                continue
            if allow_p36_pm_synthesis and str(key) in {
                "evidence_weighting",
                "evidence_tensions",
                "verification_priorities",
                "trust_assessment",
            }:
                continue
            found.update(
                _find_saved_tool_freeze_metric_strings(
                    item,
                    prefix=key_path,
                    allow_quantity_units=allow_quantity_units,
                    allow_value_bearing_live_markdown=allow_value_bearing_live_markdown,
                    allow_p36_pm_synthesis=allow_p36_pm_synthesis,
                )
            )
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(
                _find_saved_tool_freeze_metric_strings(
                    item,
                    prefix=item_path,
                    allow_quantity_units=allow_quantity_units,
                    allow_value_bearing_live_markdown=allow_value_bearing_live_markdown,
                    allow_p36_pm_synthesis=allow_p36_pm_synthesis,
                )
            )
        return found
    return set()


def validate_saved_review_reference(value: str) -> None:
    ref = value.strip()
    if ref != value or _OPAQUE_SAVED_REVIEW_REFERENCE_RE.fullmatch(ref) is None:
        raise ValueError("saved review artifact reference must be an opaque svrev_ reference")
    suffix = ref.removeprefix("svrev_").lower()
    if any(token in suffix for token in _SAVED_REVIEW_FORBIDDEN_REFERENCE_TOKENS):
        raise ValueError("saved review artifact reference must not contain broker, account, provider, or private-data hints")


def validate_saved_review_source_reference(value: str) -> None:
    ref = value.strip()
    if ref != value or _OPAQUE_SAVED_REVIEW_SOURCE_REFERENCE_RE.fullmatch(ref) is None:
        raise ValueError("saved review source reference must be an opaque app-owned source reference")
    suffix = re.sub(r"^(trrev|workspace|agentrun)_", "", ref.lower(), count=1)
    if any(token in suffix for token in _SAVED_REVIEW_FORBIDDEN_REFERENCE_TOKENS):
        raise ValueError("saved review source reference must not contain broker, account, provider, or private-data hints")


def validate_public_evidence_payload(value: object) -> None:
    validate_saved_review_artifact_payload(value)
    forbidden = find_forbidden_keys(value, forbidden_keys=_PUBLIC_EVIDENCE_FORBIDDEN_KEYS)
    if forbidden:
        raise ValueError(f"public evidence contains forbidden raw-source fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for token in _PUBLIC_EVIDENCE_FORBIDDEN_VALUE_TOKENS:
        if token in rendered:
            raise ValueError(f"public evidence contains forbidden raw-source value: {token}")


class ReportThreadCreate(BaseModel):
    account_id: UUID | None = None
    title: str = Field(min_length=1, max_length=200)
    report_type: str = Field(default="portfolio_report", min_length=1, max_length=80)
    status: ReportThreadStatus = "draft"


class ReportPublicEvidenceAttributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    section_key: Literal["public_company_profile"]
    source_key: Literal["sec_edgar_submissions"]
    source_label: Literal["SEC EDGAR metadata - company profile only"]
    availability: Literal["available", "limited"]
    has_sic_label: bool

    @model_validator(mode="after")
    def attribution_must_be_safe(self) -> "ReportPublicEvidenceAttributionRead":
        validate_public_evidence_payload(self.model_dump(mode="python"))
        return self


class ReportThreadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID | None
    title: str
    report_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    scope_metadata: ReportScopeMetadataRead | None = None
    agent_summary: "SavedAgentTeamSummaryRead | None" = None
    public_evidence_attribution: ReportPublicEvidenceAttributionRead | None = None


class ReportMessageCreate(BaseModel):
    sender_type: ReportMessageSender
    message_type: ReportMessageType
    content_markdown: str | None = None
    content_json: dict[str, Any] | None = None
    sequence: int = Field(ge=1)
    visibility: ReportMessageVisibility = "private"


class ReportMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    sender_type: str
    message_type: str
    content_markdown: str | None
    content_json: dict[str, Any] | None
    sequence: int
    visibility: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ReportThreadDetailRead(ReportThreadRead):
    messages: list[ReportMessageRead] = Field(default_factory=list)


class SavedDeterministicReviewSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    supported_flow: str
    review_flow_label: str
    symbol_or_underlying: str | None = None
    review_actionability_status: str
    actionability_label: str
    highest_severity: str | None = None
    report_status: str
    broker_snapshot_freshness_label: str | None = None
    market_quote_freshness_label: str | None = None
    caveat_codes: tuple[str, ...]
    derived_exposure_sections: tuple["SavedEvidenceSectionRead", ...] = ()
    instrument_identity: InstrumentIdentityRead = Field(default_factory=InstrumentIdentityRead)

    @model_validator(mode="after")
    def deterministic_summary_must_be_safe(self) -> "SavedDeterministicReviewSummaryRead":
        _validate_derived_exposure_sections(self.derived_exposure_sections)
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedAgentTeamRoleSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: str
    display_name: str
    role_status: AgentTeamReportRoleStatus = "completed"
    provider_status: str
    summary_markdown: str | None = None
    live_report_markdown: str | None = None
    evidence_references: tuple[str, ...] = ()
    warning_codes: tuple[str, ...]
    unavailable_reason: str | None = None

    @model_validator(mode="after")
    def agent_role_summary_must_be_safe(self) -> "SavedAgentTeamRoleSummaryRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output

        validate_agent_team_report_output(
            {
                "role_sections": (
                    {
                        "role_name": self.role_name,
                        "section_markdown": self.summary_markdown,
                        "live_report_markdown": self.live_report_markdown,
                        "evidence_references": self.evidence_references,
                    },
                )
            },
            label="agent-team role summary",
            allow_p36_live_markdown=True,
        )
        return self


class SavedToolMediatedPlannedToolRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    tool_name: str
    args: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def planned_tool_request_must_be_safe(self) -> "SavedToolMediatedPlannedToolRequestRead":
        validate_saved_tool_freeze_payload(self.model_dump(mode="python"))
        return self


class SavedToolMediatedRolePlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: str
    tool_requests: tuple[SavedToolMediatedPlannedToolRequestRead, ...]
    rationale_code: str

    @model_validator(mode="after")
    def role_plan_must_be_safe(self) -> "SavedToolMediatedRolePlanRead":
        validate_saved_tool_freeze_payload(self.model_dump(mode="python"))
        return self


class SavedToolMediatedToolResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    tool_name: str
    role_name: str
    status: str
    evidence_tier: str
    data_mode: str
    source_key: str
    source_label: str
    availability: SavedEvidenceAvailability
    freshness: str | None = None
    as_of: datetime | None = None
    scope: dict[str, Any] = Field(default_factory=dict)
    caveat_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    summary_payload: dict[str, Any] = Field(default_factory=dict)
    provenance: str
    latency_ms: int = Field(ge=0)
    estimated_cost: str
    is_mock: bool
    contract_version: str

    @model_validator(mode="after")
    def tool_result_must_be_safe(self) -> "SavedToolMediatedToolResultRead":
        validate_saved_tool_freeze_payload(
            self.model_dump(mode="python"),
            allow_p36_calculation_values=self.contract_version == _P36_CALC_TOOL_CONTRACT_VERSION,
        )
        if self.contract_version == _P36_CALC_TOOL_CONTRACT_VERSION:
            # P36 results are value-bearing. Reconstruct the app-owned envelope
            # on readback so a persisted artifact cannot bypass the same exact
            # shape, tier, privacy, and legacy-scanner reconciliation used when
            # the calculation was first frozen.
            from app.services.agent_team.tools.envelopes import ToolResult

            ToolResult(**self.model_dump(mode="python"))
        return self


class SavedToolMediatedRoleFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    finding_type: str
    claim_text: str
    evidence_refs: tuple[str, ...]
    caveat_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def role_finding_must_be_safe(self) -> "SavedToolMediatedRoleFindingRead":
        validate_saved_tool_freeze_payload(self.model_dump(mode="python"))
        return self


class SavedToolMediatedRoleFindingSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: str
    role_status: AgentTeamReportRoleStatus
    findings: tuple[SavedToolMediatedRoleFindingRead, ...]
    warning_codes: tuple[str, ...]
    unavailable_reason: str | None = None
    live_report_markdown: str | None = None

    @model_validator(mode="after")
    def role_finding_set_must_be_safe(self) -> "SavedToolMediatedRoleFindingSetRead":
        validate_saved_tool_freeze_payload(
            self.model_dump(mode="python"),
            allow_p36_live_markdown=True,
        )
        return self


class SavedToolMediatedContradictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    evidence_ref: str
    role_a: str
    role_b: str
    description: str

    @model_validator(mode="after")
    def contradiction_must_be_safe(self) -> "SavedToolMediatedContradictionRead":
        validate_saved_tool_freeze_payload(self.model_dump(mode="python"))
        return self


class SavedToolMediatedAuditorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    audit_version: str
    role_verdicts: tuple[tuple[str, bool], ...]
    contradictions: tuple[SavedToolMediatedContradictionRead, ...]
    dropped_claims: tuple[str, ...]
    repass_triggered: bool
    eval_flags: tuple[str, ...]

    @model_validator(mode="after")
    def auditor_must_be_safe(self) -> "SavedToolMediatedAuditorRead":
        validate_saved_tool_freeze_payload(self.model_dump(mode="python"))
        return self


class SavedToolMediatedProviderRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: str
    provider: str
    model: str
    prompt_version: str
    status: str
    tokens_in: int | None = Field(default=None, ge=0)
    tokens_out: int | None = Field(default=None, ge=0)
    estimated_cost: str | None = None
    is_mock: bool
    model_chain_position: int | None = Field(default=None, ge=0)
    attempted_models: tuple[str, ...] = ()

    @model_validator(mode="after")
    def provider_run_must_be_safe(self) -> "SavedToolMediatedProviderRunRead":
        validate_saved_tool_freeze_payload(self.model_dump(mode="python"))
        return self


class SavedP36PmSynthesisRead(BaseModel):
    """Frozen typed PM content; the composer owns all list/heading markup."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    evidence_weighting: str = Field(min_length=1)
    evidence_tensions: tuple[str, ...] = ()
    verification_priorities: tuple[str, ...] = ()
    trust_assessment: str = Field(min_length=1)

    @model_validator(mode="after")
    def pm_synthesis_must_be_safe(self) -> "SavedP36PmSynthesisRead":
        validate_saved_tool_freeze_payload(
            self.model_dump(mode="python"),
            allow_p36_pm_synthesis=True,
        )
        return self


class SavedToolMediatedRunArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    artifact_schema_version: Literal["p33a_tool_run_freeze_v1", "p36_tool_run_freeze_v1"] = "p33a_tool_run_freeze_v1"
    provider_mode: Literal["tool_mediated_mock", "tool_mediated_live"]
    plan_version: str
    audit_version: str
    locked_question: str
    dimensions: tuple[str, ...]
    role_plan: tuple[SavedToolMediatedRolePlanRead, ...]
    tool_results: tuple[SavedToolMediatedToolResultRead, ...]
    audited_findings: tuple[SavedToolMediatedRoleFindingSetRead, ...]
    auditor: SavedToolMediatedAuditorRead
    provider_runs: tuple[SavedToolMediatedProviderRunRead, ...] = ()
    pm_synthesis: SavedP36PmSynthesisRead | None = None
    open_questions: tuple[str, ...]
    synthesis_evidence_references: tuple[str, ...]
    warning_codes: tuple[str, ...]
    tool_result_count: int = Field(ge=0)
    frozen_at: datetime

    @model_validator(mode="after")
    def tool_run_artifact_must_be_safe(self) -> "SavedToolMediatedRunArtifactRead":
        if self.tool_result_count != len(self.tool_results):
            raise ValueError("tool_result_count must match frozen tool results")
        if self.pm_synthesis is not None and not any(
            run.role_name == "portfolio_manager_agent" and run.prompt_version == "p36-pm-synthesis-v1"
            for run in self.provider_runs
        ):
            raise ValueError("frozen P36 PM synthesis requires its matching PM provider run")
        validate_saved_tool_freeze_payload(
            self.model_dump(mode="python"),
            allow_p36_calculation_values=self.artifact_schema_version == _P36_TOOL_RUN_ARTIFACT_SCHEMA_VERSION,
            allow_p36_live_markdown=self.artifact_schema_version == _P36_TOOL_RUN_ARTIFACT_SCHEMA_VERSION,
            allow_p36_pm_synthesis=self.artifact_schema_version == _P36_TOOL_RUN_ARTIFACT_SCHEMA_VERSION,
        )
        from app.services.agent_team.auditing.v3_value_gates import validate_frozen_artifact_gate_set

        validate_frozen_artifact_gate_set(self)
        return self


class SavedAgentTeamSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    run_status: SavedReviewAgentRunStatus
    provider_mode: str
    report_generated_at: datetime | None = None
    role_summaries: tuple[SavedAgentTeamRoleSummaryRead, ...]
    warning_codes: tuple[str, ...]
    report_status: AgentTeamReportStatus | None = None
    final_synthesis_markdown: str | None = None
    final_synthesis_authored_by: AgentTeamReportSynthesisAuthor | None = None
    evidence_schema_version: str | None = None
    evidence_references: tuple[str, ...] = ()
    tool_run_artifact: SavedToolMediatedRunArtifactRead | None = None

    @model_validator(mode="after")
    def agent_summary_must_be_safe(self) -> "SavedAgentTeamSummaryRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output

        validate_agent_team_report_output(self.model_dump(mode="python"), label="agent-team summary")
        return self


class SavedReviewArtifactCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_kind: SavedReviewSourceKind
    source_reference: str
    title: str = Field(min_length=1, max_length=200)
    report_type: str = Field(default="saved_review_artifact", min_length=1, max_length=80)
    scope_metadata: ReportScopeMetadataRead | None = None
    deterministic_summary: SavedDeterministicReviewSummaryRead | None = None
    agent_summary: SavedAgentTeamSummaryRead | None = None
    generated_at: datetime | None = None
    review_pipeline_label: str = Field(default="Portfolio Copilot review pipeline", min_length=1, max_length=120)
    limitations: tuple[str, ...] = (
        "Saved review snapshot generated from reviewed data available at the time.",
    )
    caveat_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def saved_review_create_request_must_be_safe(self) -> "SavedReviewArtifactCreateRequest":
        validate_saved_review_source_reference(self.source_reference)
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedReviewReportMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    report_reference: str
    title: str
    report_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def saved_report_metadata_must_be_safe(self) -> "SavedReviewReportMetadataRead":
        validate_saved_review_reference(self.report_reference)
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedReviewArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    artifact_reference: str
    source_kind: SavedReviewSourceKind | None = None
    source_reference: str | None = None
    status: SavedReviewArtifactStatus
    report: SavedReviewReportMetadataRead
    scope_metadata: ReportScopeMetadataRead | None = None
    deterministic_summary: SavedDeterministicReviewSummaryRead | None = None
    agent_summary: SavedAgentTeamSummaryRead | None = None
    public_evidence: "SavedPublicEvidencePackageRead | None" = None
    generated_at: datetime
    saved_at: datetime
    review_pipeline_label: str
    limitations: tuple[str, ...]
    caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def saved_review_artifact_must_be_safe(self) -> "SavedReviewArtifactRead":
        validate_saved_review_reference(self.artifact_reference)
        if self.source_reference is not None:
            validate_saved_review_source_reference(self.source_reference)
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedEvidenceSourceSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    source_kind: SavedReviewSourceKind
    source_reference: str | None = None
    artifact_reference: str
    generated_at: datetime
    saved_at: datetime

    @model_validator(mode="after")
    def source_snapshot_must_be_safe(self) -> "SavedEvidenceSourceSnapshotRead":
        if self.source_reference is not None:
            validate_saved_review_source_reference(self.source_reference)
        validate_saved_review_reference(self.artifact_reference)
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedEvidenceTradeIntentSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    supported_flow: str
    review_flow_label: str
    symbol_or_underlying: str | None = None
    instrument_identity: InstrumentIdentityRead = Field(default_factory=InstrumentIdentityRead)

    @model_validator(mode="after")
    def trade_intent_must_be_safe(self) -> "SavedEvidenceTradeIntentSummaryRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedEvidenceScopeStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_account_selected: bool
    review_account_display_label: str | None = None
    review_account_included_in_portfolio_scope: bool | None = None
    review_account_is_feasibility_source: bool
    account_level_feasibility_evaluated: bool
    portfolio_scope_mode: str
    portfolio_selection_mode: str | None = None
    scope_caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def scope_state_must_be_safe(self) -> "SavedEvidenceScopeStateRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedEvidenceFreshnessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    broker_snapshot_freshness_label: str | None = None
    market_quote_freshness_label: str | None = None

    @model_validator(mode="after")
    def freshness_must_be_safe(self) -> "SavedEvidenceFreshnessRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedEvidenceActionabilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_actionability_status: str
    actionability_label: str
    highest_severity: str | None = None
    report_status: str

    @model_validator(mode="after")
    def actionability_must_be_safe(self) -> "SavedEvidenceActionabilityRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedTradeImpactNarrativeGroupsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    proceed_statements: tuple[str, ...] = ()
    not_reviewed_statement: str | None = None
    verify_statement: str | None = None

    @model_validator(mode="after")
    def narrative_groups_must_be_safe(self) -> "SavedTradeImpactNarrativeGroupsRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class SavedEvidenceSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    section_key: str
    section_label: str
    availability: SavedEvidenceAvailability
    summary_label: str | None = None
    detail_labels: tuple[str, ...] = ()
    caveat_codes: tuple[str, ...] = ()
    trade_impact_narrative_groups: SavedTradeImpactNarrativeGroupsRead | None = None

    @model_validator(mode="after")
    def section_must_be_safe(self) -> "SavedEvidenceSectionRead":
        if (
            self.trade_impact_narrative_groups is not None
            and self.section_key != "before_after_portfolio_impact"
        ):
            raise ValueError("trade-impact narrative groups are only approved for before/after exposure sections")
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


def _validate_derived_exposure_sections(sections: tuple[SavedEvidenceSectionRead, ...]) -> None:
    seen: set[str] = set()
    for section in sections:
        if section.section_key not in _DERIVED_EXPOSURE_SECTION_KEYS:
            raise ValueError("derived exposure section key is not approved for saved review artifacts")
        if section.section_key in seen:
            raise ValueError("derived exposure sections must not contain duplicates")
        seen.add(section.section_key)


def _safe_derived_exposure_sections(
    sections: tuple[SavedEvidenceSectionRead, ...],
) -> dict[str, SavedEvidenceSectionRead]:
    try:
        _validate_derived_exposure_sections(sections)
    except ValueError:
        return {}
    safe: dict[str, SavedEvidenceSectionRead] = {}
    for section in sections:
        if _stored_exposure_section_is_safe(section):
            safe[section.section_key] = section
    return safe


def _stored_exposure_section_is_safe(section: SavedEvidenceSectionRead) -> bool:
    payload = section.model_dump(mode="python")
    if find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS):
        return False
    if find_secret_like_values(payload):
        return False
    if _display_text_has_internal_token(section):
        return False
    try:
        validate_saved_review_artifact_payload(payload)
    except ValueError:
        return False
    return True


def _safe_review_account_display_label(value: str | None) -> str | None:
    """Keep only a reviewed nickname that remains safe for saved-report prose."""

    if not value:
        return None
    label = value.strip()
    if not label or _INTERNAL_DISPLAY_TOKEN_RE.search(label):
        return None
    payload = {"review_account_display_label": label}
    if find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS):
        return None
    if find_secret_like_values(payload):
        return None
    try:
        validate_saved_review_artifact_payload(payload)
    except ValueError:
        return None
    return label


def _display_text_has_internal_token(section: SavedEvidenceSectionRead) -> bool:
    group = section.trade_impact_narrative_groups
    if group is not None and not isinstance(group, SavedTradeImpactNarrativeGroupsRead):
        return True
    display_text = " ".join(
        value
        for value in (
            section.section_label,
            section.summary_label or "",
            *section.detail_labels,
            *((group.proceed_statements if group is not None else ())),
            *((group.not_reviewed_statement,) if group is not None and group.not_reviewed_statement else ()),
            *((group.verify_statement,) if group is not None and group.verify_statement else ()),
        )
        if value
    )
    return _INTERNAL_DISPLAY_TOKEN_RE.search(display_text) is not None


def _stub_before_after_portfolio_impact_section() -> SavedEvidenceSectionRead:
    return SavedEvidenceSectionRead(
        section_key="before_after_portfolio_impact",
        section_label="Before/after portfolio impact",
        availability="not_available",
        summary_label="Before/after portfolio-impact details were not included in this saved source.",
    )


def _stub_concentration_risk_drift_section(
    *,
    highest_severity: str,
    caveat_codes: tuple[str, ...],
) -> SavedEvidenceSectionRead:
    return SavedEvidenceSectionRead(
        section_key="concentration_risk_drift",
        section_label="Concentration and risk drift",
        availability="limited",
        summary_label=f"Highest deterministic severity: {highest_severity}.",
        caveat_codes=caveat_codes,
    )


class SavedPublicEvidenceFactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    fact_key: str
    fact_label: str
    value_label: str | None = None
    as_of_label: str | None = None
    source_label: str | None = None

    @model_validator(mode="after")
    def public_fact_must_be_safe(self) -> "SavedPublicEvidenceFactRead":
        validate_public_evidence_payload(self.model_dump(mode="python"))
        return self


class SavedPublicEvidenceSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    section_key: SavedPublicEvidenceSectionKey
    section_label: str
    availability: SavedEvidenceAvailability
    freshness_category: SavedPublicEvidenceFreshnessCategory
    freshness_label: str
    source_label: str
    source_key: SavedPublicEvidenceSourceKey | None = None
    rights_status: SavedPublicEvidenceRightsStatus
    as_of: datetime | None = None
    collected_at: datetime | None = None
    summary_label: str | None = None
    facts: tuple[SavedPublicEvidenceFactRead, ...] = ()
    limitations: tuple[str, ...]
    caveat_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def public_section_must_be_safe(self) -> "SavedPublicEvidenceSectionRead":
        validate_public_evidence_payload(self.model_dump(mode="python"))
        if self.availability in {"available", "limited"} and self.rights_status == "not_reviewed":
            raise ValueError("available public evidence requires reviewed or internal-demo source rights")
        _validate_p36_source_snapshot_section(self)
        return self


def _validate_p36_source_snapshot_section(section: SavedPublicEvidenceSectionRead) -> None:
    source_contracts = {
        "fmp_reported_statement_facts": (
            "public_fundamentals_snapshot",
            _FMP_FUNDAMENTALS_FACT_KEYS,
            "FMP normalized reported statement facts",
            "Source: Financial Modeling Prep normalized reported statement facts, with labeled fiscal periods and report dates.",
        ),
        "fmp_eod_history": (
            "public_market_context",
            _FMP_EOD_HISTORY_FACT_KEYS,
            "FMP end-of-day data (internal evaluation use)",
            "Source: Financial Modeling Prep normalized end-of-day OHLCV history. Historical end-of-day data only.",
        ),
        "fred_macro_series": (
            "fred_macro_series_snapshot",
            _FRED_MACRO_SERIES_FACT_KEYS,
            "FRED normalized macro series observations",
            "Source: Federal Reserve Economic Data (FRED), normalized series observations and dates.",
        ),
    }
    contract = source_contracts.get(section.source_key)
    if contract is None:
        return
    expected_section_key, allowed_fact_keys, expected_source_label, required_attribution = contract
    if section.section_key != expected_section_key:
        raise ValueError("source snapshot was attached to an unapproved public evidence section")
    if section.source_label != expected_source_label:
        raise ValueError("source snapshot did not use the reviewed source label")
    fact_keys = {fact.fact_key for fact in section.facts}
    if not fact_keys.issubset(allowed_fact_keys):
        raise ValueError("source snapshot contains an unapproved normalized fact")
    if section.availability in {"available", "limited"}:
        if not section.facts:
            raise ValueError("available source snapshot requires normalized facts")
        if any(
            not fact.value_label or not fact.as_of_label or not fact.source_label
            for fact in section.facts
        ):
            raise ValueError("normalized source snapshot facts require value, as-of, and source labels")
        if required_attribution not in section.limitations:
            raise ValueError("available source snapshot requires the reviewed attribution")
    elif section.facts:
        raise ValueError("unavailable source snapshot must not retain normalized facts")


class SavedPublicEvidencePackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    public_evidence_schema_version: str = "p29b_public_v1"
    public_evidence_mode: SavedPublicEvidenceMode
    symbol_or_underlying: str | None = None
    public_company_profile: SavedPublicEvidenceSectionRead
    public_fundamentals_snapshot: SavedPublicEvidenceSectionRead
    # Optional so pre-P36 frozen packages remain readable without migration.
    fred_macro_series_snapshot: SavedPublicEvidenceSectionRead | None = None
    public_news_snapshot: SavedPublicEvidenceSectionRead
    public_events_calendar: SavedPublicEvidenceSectionRead
    public_technical_context: SavedPublicEvidenceSectionRead
    public_market_context: SavedPublicEvidenceSectionRead
    limitations: tuple[str, ...]

    @classmethod
    def not_reviewed(cls, symbol_or_underlying: str | None = None) -> "SavedPublicEvidencePackageRead":
        return cls(
            public_evidence_mode="not_reviewed",
            symbol_or_underlying=symbol_or_underlying,
            public_company_profile=_not_reviewed_public_section(
                "public_company_profile",
                "Public company profile",
                "No reviewed public company profile is attached to this saved report.",
            ),
            public_fundamentals_snapshot=_not_reviewed_public_section(
                "public_fundamentals_snapshot",
                "Public fundamentals snapshot",
                "No reviewed public fundamentals snapshot is attached to this saved report.",
            ),
            fred_macro_series_snapshot=_not_reviewed_public_section(
                "fred_macro_series_snapshot",
                "FRED macro series snapshot",
                "No reviewed FRED macro series snapshot is attached to this saved report.",
            ),
            public_news_snapshot=_not_reviewed_public_section(
                "public_news_snapshot",
                "Public news snapshot",
                "No reviewed public news snapshot is attached to this saved report.",
            ),
            public_events_calendar=_not_reviewed_public_section(
                "public_events_calendar",
                "Public events calendar",
                "No reviewed public event calendar is attached to this saved report.",
            ),
            public_technical_context=_not_reviewed_public_section(
                "public_technical_context",
                "Public technical context",
                "No reviewed public technical context is attached to this saved report.",
            ),
            public_market_context=_not_reviewed_public_section(
                "public_market_context",
                "Public market context",
                "No reviewed public market context is attached to this saved report.",
            ),
            limitations=(
                "Public analyst evidence was not reviewed or attached when this saved evidence package was built.",
            ),
        )

    @model_validator(mode="after")
    def public_package_must_be_safe(self) -> "SavedPublicEvidencePackageRead":
        validate_public_evidence_payload(self.model_dump(mode="python"))
        return self


class PublicEvidenceLaneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    lane_key: PublicEvidenceLaneKey
    requirement: PublicEvidenceLaneRequirement
    availability: SavedEvidenceAvailability
    caveat_codes: tuple[PublicEvidenceReadinessCaveatCode, ...] = ()

    @model_validator(mode="after")
    def lane_readiness_must_be_safe(self) -> "PublicEvidenceLaneRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class PublicEvidencePreparationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    resolved_instrument_kind: Literal["operating_company_equity", "etf_or_fund", "unknown"]
    resolution_status: Literal["confirmed", "declared_only", "mismatch_reconciled", "unresolved"]
    readiness: PublicEvidenceReadiness
    evidence_state: PublicEvidenceState
    lanes: tuple[PublicEvidenceLaneRead, ...]

    @model_validator(mode="after")
    def preparation_readiness_must_be_safe(self) -> "PublicEvidencePreparationRead":
        lane_keys = tuple(lane.lane_key for lane in self.lanes)
        if len(lane_keys) != len(set(lane_keys)):
            raise ValueError("public evidence readiness contains duplicate lanes")
        lanes = {lane.lane_key: lane for lane in self.lanes}
        for lane in self.lanes:
            if lane.requirement == "not_applicable":
                if lane.availability != "not_applicable" or lane.caveat_codes:
                    raise ValueError("not-applicable readiness lanes must not carry availability or caveats")
            elif lane.availability == "not_applicable":
                raise ValueError("applicable readiness lanes must not use not-applicable availability")
            if lane.lane_key in {
                "eod_history",
                "company_profile",
                "company_recent_filings",
                "company_fundamentals",
            } and lane.requirement != "not_applicable":
                expected_caveats = {
                    "available": (),
                    "limited": ("evidence_limited",),
                    "not_available": ("evidence_not_available",),
                    "not_reviewed": ("evidence_not_reviewed",),
                }.get(lane.availability)
                if expected_caveats is None or lane.caveat_codes != expected_caveats:
                    raise ValueError("source readiness caveats must match the provider-neutral availability state")

        if self.resolution_status in {"declared_only", "unresolved"}:
            expected_caveat = (
                "instrument_kind_not_confirmed"
                if self.resolution_status == "declared_only"
                else "instrument_kind_unresolved"
            )
            identity_lane = lanes.get("instrument_identity")
            if (
                set(lanes) != {"instrument_identity"}
                or identity_lane is None
                or identity_lane.requirement != "required"
                or identity_lane.availability != "not_available"
                or identity_lane.caveat_codes != (expected_caveat,)
                or self.readiness != "not_ready"
            ):
                raise ValueError("unconfirmed instrument readiness must use the reviewed identity gap")
            if self.resolution_status == "unresolved" and self.resolved_instrument_kind != "unknown":
                raise ValueError("unresolved readiness must use unknown instrument kind")
            if self.resolution_status == "declared_only" and self.resolved_instrument_kind == "unknown":
                raise ValueError("declared readiness requires a submitted instrument kind")
        elif self.resolved_instrument_kind == "operating_company_equity":
            required_keys = {
                "eod_history",
                "company_profile",
                "company_recent_filings",
                "company_fundamentals",
            }
            not_applicable_keys = {"etf_profile", "etf_holdings", "etf_fund_events"}
            if set(lanes) != required_keys | not_applicable_keys:
                raise ValueError("operating-company readiness requires the complete reviewed lane matrix")
            if any(lanes[key].requirement != "required" for key in required_keys):
                raise ValueError("operating-company source lanes must be required")
            if any(lanes[key].requirement != "not_applicable" for key in not_applicable_keys):
                raise ValueError("ETF lanes must be not applicable for an operating company")
            available_count = sum(
                lanes[key].availability in {"available", "limited"} for key in required_keys
            )
            expected_readiness = (
                "ready"
                if available_count == len(required_keys)
                else "partial"
                if available_count
                else "not_ready"
            )
            if self.readiness != expected_readiness:
                raise ValueError("operating-company readiness must be derived from required lane availability")
        elif self.resolved_instrument_kind == "etf_or_fund":
            expected_keys = {
                "eod_history",
                "company_profile",
                "company_recent_filings",
                "company_fundamentals",
                "etf_profile",
                "etf_holdings",
                "etf_fund_events",
            }
            if set(lanes) != expected_keys:
                raise ValueError("ETF readiness requires the complete reviewed lane matrix")
            if lanes["eod_history"].requirement != "required":
                raise ValueError("ETF end-of-day evidence must remain required")
            if any(
                lanes[key].requirement != "not_applicable"
                for key in {"company_profile", "company_recent_filings", "company_fundamentals"}
            ):
                raise ValueError("operating-company lanes must be not applicable for an ETF")
            if any(lanes[key].requirement != "required" for key in {"etf_profile", "etf_holdings"}):
                raise ValueError("ETF profile and holdings evidence must remain required")
            if lanes["etf_fund_events"].requirement != "optional":
                raise ValueError("ETF fund-event evidence must remain optional")
            for key in {"etf_profile", "etf_holdings", "etf_fund_events"}:
                if (
                    lanes[key].availability != "not_reviewed"
                    or lanes[key].caveat_codes != ("etf_evidence_contract_not_available",)
                ):
                    raise ValueError("ETF-specific evidence remains unavailable until its contract is implemented")
            if self.readiness != "not_ready":
                raise ValueError("ETF readiness remains not ready until its evidence contract is implemented")
        else:
            raise ValueError("confirmed readiness requires a reviewed instrument kind")
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class AgentTeamGenerationNotReadyDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: Literal["agent_team_generation_not_ready"] = "agent_team_generation_not_ready"
    readiness: AgentTeamGenerationRefusalReadiness
    reason_codes: tuple[AgentTeamGenerationNotReadyReasonCode, ...]

    @model_validator(mode="after")
    def refusal_must_use_closed_consistent_reasons(self) -> "AgentTeamGenerationNotReadyDetailRead":
        if not self.reason_codes or len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("generation readiness refusal requires unique closed reason codes")
        if self.readiness == "partial" and self.reason_codes != ("required_evidence_unavailable",):
            raise ValueError("partial readiness may only report unavailable required evidence")
        return self


class AgentTeamGenerationNotReadyResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    detail: AgentTeamGenerationNotReadyDetailRead


class SavedPublicRoleInstrumentContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    symbol_or_underlying: str | None = None
    review_flow_label: str

    @model_validator(mode="after")
    def instrument_context_must_be_safe(self) -> "SavedPublicRoleInstrumentContextRead":
        validate_public_evidence_payload(self.model_dump(mode="python"))
        return self


class SavedPublicRoleEvidenceProjectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: AgentTeamPublicRoleName
    instrument_context: SavedPublicRoleInstrumentContextRead
    allowed_section_keys: tuple[SavedPublicEvidenceSectionKey, ...]
    sections: tuple[SavedPublicEvidenceSectionRead, ...]
    citable_section_keys: tuple[SavedPublicEvidenceSectionKey, ...]
    degrade_reason: str | None = None

    @model_validator(mode="after")
    def public_role_projection_must_be_safe(self) -> "SavedPublicRoleEvidenceProjectionRead":
        validate_public_evidence_payload(self.model_dump(mode="python"))
        allowed = set(self.allowed_section_keys)
        section_keys = {section.section_key for section in self.sections}
        citable = set(self.citable_section_keys)
        if not section_keys.issubset(allowed) or not citable.issubset(allowed):
            raise ValueError("public role projection contains evidence outside the role boundary")
        availability_by_key = {section.section_key: section.availability for section in self.sections}
        if any(availability_by_key.get(section_key) not in {"available", "limited"} for section_key in citable):
            raise ValueError("public role projection cites unavailable public evidence")
        return self


def _not_reviewed_public_section(
    section_key: SavedPublicEvidenceSectionKey,
    section_label: str,
    summary_label: str,
) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key=section_key,
        section_label=section_label,
        availability="not_reviewed",
        freshness_category="not_reviewed",
        freshness_label="Not reviewed for this saved report",
        source_label="No reviewed public source attached",
        rights_status="not_reviewed",
        summary_label=summary_label,
        limitations=("Public source rights and retention were not reviewed for this section.",),
    )


class SavedEvidencePackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    evidence_schema_version: str = "p29a_t1_v1"
    source_snapshot: SavedEvidenceSourceSnapshotRead
    trade_intent_summary: SavedEvidenceTradeIntentSummaryRead
    scope_state: SavedEvidenceScopeStateRead
    account_readiness: SavedEvidenceSectionRead
    freshness: SavedEvidenceFreshnessRead
    actionability: SavedEvidenceActionabilityRead
    portfolio_impact_summary: SavedEvidenceSectionRead
    before_after_portfolio_impact: SavedEvidenceSectionRead
    concentration_risk_drift: SavedEvidenceSectionRead
    cash_collateral_caveats: SavedEvidenceSectionRead
    options_exposure_summary: SavedEvidenceSectionRead
    market_quote_freshness: SavedEvidenceSectionRead
    economic_awareness_snapshot: SavedEvidenceSectionRead
    market_mood_snapshot: SavedEvidenceSectionRead
    public_evidence: SavedPublicEvidencePackageRead | None = None
    caveat_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    requires_runtime_tools: Literal[False] = False

    @classmethod
    def from_saved_review_artifact(cls, artifact: SavedReviewArtifactRead) -> "SavedEvidencePackageRead":
        if artifact.scope_metadata is None or artifact.deterministic_summary is None:
            raise ValueError("saved evidence package requires saved scope metadata and deterministic summary")

        scope = artifact.scope_metadata
        review_account = scope.review_account
        portfolio_scope = scope.portfolio_context_scope
        deterministic = artifact.deterministic_summary
        caveat_codes = tuple(dict.fromkeys((*deterministic.caveat_codes, *artifact.caveat_codes)))
        limitations = tuple(artifact.limitations)
        account_level_label = (
            "Account-level feasibility evaluated from saved review scope."
            if scope.account_level_feasibility_evaluated
            else "Account-level feasibility was not evaluated in the saved review scope."
        )
        highest_severity = deterministic.highest_severity or "not provided"
        frozen_exposure_sections = _safe_derived_exposure_sections(deterministic.derived_exposure_sections)
        before_after_section = frozen_exposure_sections.get("before_after_portfolio_impact")
        concentration_section = frozen_exposure_sections.get("concentration_risk_drift")

        return cls(
            source_snapshot=SavedEvidenceSourceSnapshotRead(
                source_kind=artifact.source_kind or "trade_review_workspace",
                source_reference=artifact.source_reference,
                artifact_reference=artifact.artifact_reference,
                generated_at=artifact.generated_at,
                saved_at=artifact.saved_at,
            ),
            trade_intent_summary=SavedEvidenceTradeIntentSummaryRead(
                supported_flow=deterministic.supported_flow,
                review_flow_label=deterministic.review_flow_label,
                symbol_or_underlying=deterministic.symbol_or_underlying,
                instrument_identity=deterministic.instrument_identity,
            ),
            scope_state=SavedEvidenceScopeStateRead(
                review_account_selected=review_account is not None,
                review_account_display_label=_safe_review_account_display_label(
                    review_account.display_label if review_account is not None else None
                ),
                review_account_included_in_portfolio_scope=(
                    review_account.is_included_in_portfolio_scope if review_account is not None else None
                ),
                review_account_is_feasibility_source=(
                    review_account.is_account_level_feasibility_source if review_account is not None else False
                ),
                account_level_feasibility_evaluated=scope.account_level_feasibility_evaluated,
                portfolio_scope_mode=portfolio_scope.scope_mode,
                portfolio_selection_mode=portfolio_scope.selection_mode,
                scope_caveat_codes=scope.scope_caveat_codes,
            ),
            account_readiness=SavedEvidenceSectionRead(
                section_key="account_readiness",
                section_label="Account readiness",
                availability="available",
                summary_label=account_level_label,
                caveat_codes=scope.scope_caveat_codes,
            ),
            freshness=SavedEvidenceFreshnessRead(
                broker_snapshot_freshness_label=deterministic.broker_snapshot_freshness_label,
                market_quote_freshness_label=deterministic.market_quote_freshness_label,
            ),
            actionability=SavedEvidenceActionabilityRead(
                review_actionability_status=deterministic.review_actionability_status,
                actionability_label=deterministic.actionability_label,
                highest_severity=deterministic.highest_severity,
                report_status=deterministic.report_status,
            ),
            portfolio_impact_summary=SavedEvidenceSectionRead(
                section_key="portfolio_impact_summary",
                section_label="Portfolio impact summary",
                availability="limited",
                summary_label="Saved deterministic portfolio-impact summary is available as reviewed labels and caveats.",
                caveat_codes=caveat_codes,
            ),
            before_after_portfolio_impact=before_after_section or _stub_before_after_portfolio_impact_section(),
            concentration_risk_drift=concentration_section or _stub_concentration_risk_drift_section(
                highest_severity=highest_severity,
                caveat_codes=caveat_codes,
            ),
            cash_collateral_caveats=SavedEvidenceSectionRead(
                section_key="liquidity_collateral_caveats",
                section_label="Liquidity and collateral caveats",
                availability="limited",
                summary_label="Liquidity and collateral model caveats are available without raw private amounts.",
                caveat_codes=caveat_codes,
            ),
            options_exposure_summary=SavedEvidenceSectionRead(
                section_key="options_exposure_summary",
                section_label="Options exposure summary",
                availability="limited",
                summary_label="Options feasibility caveats are available as reviewed saved-source labels.",
                caveat_codes=caveat_codes,
            ),
            market_quote_freshness=SavedEvidenceSectionRead(
                section_key="market_quote_freshness",
                section_label="Market quote freshness",
                availability="available" if deterministic.market_quote_freshness_label else "not_available",
                summary_label=deterministic.market_quote_freshness_label,
            ),
            economic_awareness_snapshot=SavedEvidenceSectionRead(
                section_key="economic_awareness_snapshot",
                section_label="Economic awareness snapshot",
                availability="not_reviewed",
                summary_label="Economic awareness was not included in this saved source.",
            ),
            market_mood_snapshot=SavedEvidenceSectionRead(
                section_key="market_mood_snapshot",
                section_label="Market Mood snapshot",
                availability="not_reviewed",
                summary_label="Market Mood was not included in this saved source.",
            ),
            public_evidence=(
                artifact.public_evidence
                if artifact.public_evidence is not None
                else SavedPublicEvidencePackageRead.not_reviewed(deterministic.symbol_or_underlying)
            ),
            caveat_codes=caveat_codes,
            limitations=limitations,
        )

    @model_validator(mode="after")
    def evidence_package_must_be_safe(self) -> "SavedEvidencePackageRead":
        validate_saved_review_artifact_payload(self.model_dump(mode="python"))
        return self


class AgentTeamReportRoleSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: str
    display_name: str
    role_status: AgentTeamReportRoleStatus
    provider_status: str
    section_markdown: str | None = None
    evidence_references: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()
    unavailable_reason: str | None = None

    @model_validator(mode="after")
    def role_section_must_be_safe(self) -> "AgentTeamReportRoleSectionRead":
        from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output

        validate_agent_team_report_output(
            {"role_sections": (self.model_dump(mode="python"),)},
            label="agent-team report role section",
        )
        return self


class AgentTeamReportSynthesisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    synthesis_markdown: str | None = None
    authored_by: AgentTeamReportSynthesisAuthor
    evidence_references: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def synthesis_must_be_safe(self) -> "AgentTeamReportSynthesisRead":
        from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output

        validate_agent_team_report_output(self.model_dump(mode="python"), label="agent-team report synthesis")
        return self


class AgentTeamReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    report_schema_version: str = "p29a_t2_v1"
    report_status: AgentTeamReportStatus
    run_completeness: AgentTeamReportRunCompleteness
    source_snapshot: SavedEvidenceSourceSnapshotRead
    evidence_schema_version: str
    report_headline: str | None = None
    role_sections: tuple[AgentTeamReportRoleSectionRead, ...] = ()
    final_synthesis: AgentTeamReportSynthesisRead | None = None
    evidence_references: tuple[str, ...] = ()
    limitations: tuple[str, ...]
    caveat_codes: tuple[str, ...]
    provider_mode: str
    warning_codes: tuple[str, ...] = ()
    safety_flags: tuple[str, ...] = ()
    generated_at: datetime
    report_generated_at: datetime | None = None
    report_built_at: datetime

    @classmethod
    def from_saved_review_artifact(cls, artifact: SavedReviewArtifactRead) -> "AgentTeamReportRead":
        evidence = SavedEvidencePackageRead.from_saved_review_artifact(artifact)
        built_at = datetime.now(tz=artifact.saved_at.tzinfo)
        if artifact.agent_summary is None:
            return cls(
                report_status="source_snapshot",
                run_completeness="none",
                source_snapshot=evidence.source_snapshot,
                evidence_schema_version=evidence.evidence_schema_version,
                role_sections=(),
                final_synthesis=None,
                evidence_references=(),
                limitations=evidence.limitations,
                caveat_codes=evidence.caveat_codes,
                provider_mode="not_run",
                warning_codes=("agent_team_not_generated",),
                safety_flags=("analysis_only", "deterministic_metrics_owned_by_backend"),
                generated_at=artifact.generated_at,
                report_generated_at=None,
                report_built_at=built_at,
            )

        summary = artifact.agent_summary
        role_sections = tuple(
            AgentTeamReportRoleSectionRead(
                role_name=role.role_name,
                display_name=role.display_name,
                role_status=role.role_status,
                provider_status=role.provider_status,
                section_markdown=role.summary_markdown,
                evidence_references=role.evidence_references,
                warning_codes=role.warning_codes,
                unavailable_reason=role.unavailable_reason,
            )
            for role in summary.role_summaries
        )
        final_synthesis = (
            AgentTeamReportSynthesisRead(
                synthesis_markdown=summary.final_synthesis_markdown,
                authored_by=summary.final_synthesis_authored_by,
                evidence_references=summary.evidence_references,
                warning_codes=summary.warning_codes,
            )
            if summary.final_synthesis_authored_by is not None
            else None
        )
        report_status = summary.report_status or _agent_team_report_status_from_summary(summary)
        return cls(
            report_status=report_status,
            run_completeness=_agent_team_run_completeness(role_sections),
            source_snapshot=evidence.source_snapshot,
            evidence_schema_version=summary.evidence_schema_version or evidence.evidence_schema_version,
            report_headline=_agent_team_report_headline(report_status),
            role_sections=role_sections,
            final_synthesis=final_synthesis,
            evidence_references=summary.evidence_references,
            limitations=evidence.limitations,
            caveat_codes=evidence.caveat_codes,
            provider_mode=summary.provider_mode,
            warning_codes=summary.warning_codes,
            safety_flags=("analysis_only", "deterministic_metrics_owned_by_backend"),
            generated_at=artifact.generated_at,
            report_generated_at=summary.report_generated_at,
            report_built_at=built_at,
        )

    @model_validator(mode="after")
    def agent_team_report_must_be_safe(self) -> "AgentTeamReportRead":
        from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output

        validate_agent_team_report_output(self.model_dump(mode="python"), label="agent-team report")
        return self


def _agent_team_report_status_from_summary(summary: SavedAgentTeamSummaryRead) -> AgentTeamReportStatus:
    if summary.run_status == "failed":
        return "agent_unavailable"
    if summary.final_synthesis_markdown:
        return "full_agent_report"
    return "deterministic_draft"


def _agent_team_run_completeness(
    role_sections: tuple[AgentTeamReportRoleSectionRead, ...],
) -> AgentTeamReportRunCompleteness:
    if not role_sections:
        return "none"
    completed = sum(1 for section in role_sections if section.role_status == "completed")
    if completed == len(role_sections):
        return "full"
    if completed > 0:
        return "partial"
    return "none"


def _agent_team_report_headline(status: AgentTeamReportStatus) -> str | None:
    if status == "full_agent_report":
        return "Agent Team analysis generated from the saved evidence package."
    if status == "deterministic_draft":
        return "Deterministic evidence is available; Agent Team narrative is not generated."
    if status == "agent_unavailable":
        return "Agent Team narrative is unavailable; deterministic evidence remains available."
    if status == "validation_failed":
        return "Agent Team narrative was withheld by safety validation."
    return None
