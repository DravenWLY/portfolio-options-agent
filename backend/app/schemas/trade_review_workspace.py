from datetime import date, datetime
from decimal import Decimal
import re
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.actionability import (
    BrokerSnapshotMetadata,
    PortfolioActionabilityDecision,
    ReviewActionabilityStatus,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.risk.violations import RiskSeverity


SupportedTradeReviewFlow: TypeAlias = Literal[
    "stock_buy",
    "stock_sell_trim",
    "etf_buy",
    "etf_sell_trim",
    "covered_call",
    "cash_secured_put",
]
WorkspaceCaveatSeverity: TypeAlias = Literal["info", "warning", "blocker"]
PortfolioContextSelectionMode: TypeAlias = Literal["latest_available", "selected_context"]
ReviewAccountSelectionMode: TypeAlias = Literal["unselected", "selected_account"]
PortfolioContextSource: TypeAlias = Literal["snaptrade", "manual", "csv", "synthetic_mock"]
PortfolioContextSourceKind: TypeAlias = Literal["broker_snapshot", "manual", "csv", "synthetic_demo"]
PortfolioCashState: TypeAlias = Literal["available", "unavailable", "not_exposed"]
PortfolioScopeMode: TypeAlias = Literal[
    "all_connected_accounts",
    "single_account",
    "selected_account_group",
    "selected_context",
    "unavailable",
]
AccountDetailsDataMode: TypeAlias = Literal["synthetic_demo", "private_real_source", "unavailable"]
AccountDetailSourceKind: TypeAlias = Literal["snaptrade", "manual", "csv", "synthetic_demo", "unknown"]
AccountScopeRole: TypeAlias = Literal["review_account", "included_in_scope", "excluded_from_scope"]
TradeReviewReportStatus: TypeAlias = Literal["preview_only", "saved", "generated", "unavailable"]
TradeReviewListSourceMode: TypeAlias = Literal["synthetic_preview", "portfolio_preview", "saved_review"]
Phase20BDataMode: TypeAlias = Literal["synthetic_demo", "persisted"]
DashboardAccountSummaryDataMode: TypeAlias = Literal["synthetic_demo", "private_real_source", "unavailable"]
DashboardAccountDisplayScope: TypeAlias = Literal[
    "selected_context",
    "selected_account",
    "combined_portfolio",
    "manual_csv",
    "synthetic_demo",
    "unavailable",
]
DashboardValuationBasis: TypeAlias = Literal[
    "market_value",
    "book_value",
    "mixed",
    "indicative",
    "delayed",
    "unavailable",
]
DashboardMarketDataMode: TypeAlias = Literal["synthetic", "indicative", "delayed", "unavailable", "live"]
DashboardPrivacyDisplayMode: TypeAlias = Literal["amounts_visible", "amounts_hidden"]
RiskAlertCategory: TypeAlias = Literal[
    "concentration",
    "cash_collateral",
    "stale_broker_snapshot",
    "stale_market_quote",
    "missing_data",
    "agent_provider",
]
RiskAlertFreshnessScope: TypeAlias = Literal["broker_snapshot", "market_quote", "agent_provider", "review"]
ReviewReadinessMode: TypeAlias = Literal["normal_review", "analysis_only", "manual_confirmation_required", "blocked"]
ReadinessSnapshotStatus: TypeAlias = Literal["fresh", "manual_review", "stale", "unknown", "unavailable"]
AgentProviderMode: TypeAlias = Literal["mock", "live", "unavailable"]
ReadinessAgentProviderStatus: TypeAlias = Literal["available", "unavailable", "error", "mock_default"]
DashboardDisplaySectionKind: TypeAlias = Literal["summary", "freshness", "shape", "caveats"]

_OPAQUE_CONTEXT_REFERENCE_RE = re.compile(r"^ctx_[a-z0-9][a-z0-9_-]{5,79}$")
_OPAQUE_ACCOUNT_REFERENCE_RE = re.compile(r"^acctref_[a-z0-9][a-z0-9_-]{5,79}$")
_OPAQUE_SCOPE_REFERENCE_RE = re.compile(r"^scope_[a-z0-9][a-z0-9_-]{5,79}$")
_OPAQUE_SAVED_REVIEW_SOURCE_REFERENCE_RE = re.compile(r"^trrev_[a-z0-9][a-z0-9_-]{5,79}$")
_FORBIDDEN_CONTEXT_REFERENCE_TOKENS = (
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
    "portfolio",
)
_FORBIDDEN_ACCOUNT_REFERENCE_TOKENS = (
    "account",
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
)
_FORBIDDEN_SAVED_REVIEW_SOURCE_REFERENCE_TOKENS = (
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

PROHIBITED_TRADE_REVIEW_WORKSPACE_PHRASES = (
    "you should",
    "i recommend",
    "recommend buying",
    "recommend selling",
    "guaranteed",
    "guaranteed return",
    "safe to trade",
    "ready to trade",
)


def validate_portfolio_context_reference(context_reference: str) -> str:
    """Validate opaque app-owned portfolio-context references."""

    ref = context_reference.strip()
    if ref != context_reference or _OPAQUE_CONTEXT_REFERENCE_RE.fullmatch(ref) is None:
        raise ValueError("context_reference must be an opaque app-generated context reference")
    lowered = ref.lower()
    if any(token in lowered for token in _FORBIDDEN_CONTEXT_REFERENCE_TOKENS):
        raise ValueError("context_reference must not contain broker, account, provider, or private-data hints")
    return ref


def validate_account_reference(account_reference: str) -> str:
    """Validate opaque app-owned account references."""

    ref = account_reference.strip()
    if ref != account_reference or _OPAQUE_ACCOUNT_REFERENCE_RE.fullmatch(ref) is None:
        raise ValueError("account_reference must be an opaque app-generated account reference")
    suffix = ref.removeprefix("acctref_").lower()
    if any(token in suffix for token in _FORBIDDEN_ACCOUNT_REFERENCE_TOKENS):
        raise ValueError("account_reference must not contain broker, provider, account, or private-data hints")
    return ref


def validate_scope_reference(scope_reference: str) -> str:
    """Validate opaque app-owned portfolio-scope references."""

    ref = scope_reference.strip()
    if ref != scope_reference or _OPAQUE_SCOPE_REFERENCE_RE.fullmatch(ref) is None:
        raise ValueError("scope_reference must be an opaque app-generated scope reference")
    return ref


def validate_trade_review_saved_source_reference(source_reference: str) -> str:
    """Validate opaque app-owned saved-review source references exposed to frontend."""

    ref = source_reference.strip()
    if ref != source_reference or _OPAQUE_SAVED_REVIEW_SOURCE_REFERENCE_RE.fullmatch(ref) is None:
        raise ValueError("saved_review_source_reference must be an opaque trrev_ reference")
    suffix = ref.removeprefix("trrev_").lower()
    if any(token in suffix for token in _FORBIDDEN_SAVED_REVIEW_SOURCE_REFERENCE_TOKENS):
        raise ValueError(
            "saved_review_source_reference must not contain broker, account, provider, or private-data hints"
        )
    return ref


class WorkspaceOptionLegSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    underlying_symbol: str
    option_type: Literal["call", "put"]
    leg_action: str
    expiration_date: date
    strike: str
    quantity: str
    premium: str | None = None
    multiplier: str
    occ_symbol: str | None = None
    support_status: str
    unsupported_reason: str | None = None


class TradeReviewPreviewOptionLeg(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    underlying_symbol: str
    option_type: Literal["call", "put"]
    leg_action: Literal["buy_to_open", "sell_to_open", "buy_to_close", "sell_to_close"]
    expiration_date: date
    strike: Decimal = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    premium: Decimal | None = Field(default=None, ge=0)
    multiplier: Decimal = Field(default=Decimal("100"), gt=0)
    occ_symbol: str | None = None
    support_status: Literal["supported", "manual_review_required", "unsupported"] = "supported"
    unsupported_reason: str | None = None


class TradeReviewWorkspacePreviewRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    supported_flow: SupportedTradeReviewFlow
    symbol: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    price_assumption: Decimal | None = Field(default=None, gt=0)
    option_leg: TradeReviewPreviewOptionLeg | None = None

    @model_validator(mode="after")
    def preview_request_must_match_flow(self) -> "TradeReviewWorkspacePreviewRequest":
        if self.supported_flow in {"stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"}:
            missing = []
            if self.symbol is None:
                missing.append("symbol")
            if self.quantity is None:
                missing.append("quantity")
            if self.price_assumption is None:
                missing.append("price_assumption")
            if missing:
                raise ValueError(f"{self.supported_flow} requires: {', '.join(missing)}")
            if self.option_leg is not None:
                raise ValueError(f"{self.supported_flow} must not include option_leg")
        else:
            if self.option_leg is None:
                raise ValueError(f"{self.supported_flow} requires option_leg")
            if self.symbol is not None or self.quantity is not None or self.price_assumption is not None:
                raise ValueError(f"{self.supported_flow} must use option_leg instead of stock/ETF fields")
        return self


class PortfolioContextSelectionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    mode: PortfolioContextSelectionMode = "latest_available"
    context_reference: str | None = Field(default=None, min_length=10, max_length=84)

    @model_validator(mode="after")
    def context_reference_must_be_opaque(self) -> "PortfolioContextSelectionRequest":
        if self.mode == "latest_available":
            if self.context_reference is not None:
                raise ValueError("latest_available must not include context_reference")
            return self
        if self.context_reference is None:
            raise ValueError("selected_context requires context_reference")
        validate_portfolio_context_reference(self.context_reference)
        return self


class ReviewAccountSelectionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    mode: ReviewAccountSelectionMode = "unselected"
    account_reference: str | None = Field(default=None, min_length=14, max_length=90)

    @model_validator(mode="after")
    def account_reference_must_be_opaque(self) -> "ReviewAccountSelectionRequest":
        if self.mode == "unselected":
            if self.account_reference is not None:
                raise ValueError("unselected review account must not include account_reference")
            return self
        if self.account_reference is None:
            raise ValueError("selected_account requires account_reference")
        validate_account_reference(self.account_reference)
        return self


class TradeReviewPortfolioPreviewRequest(TradeReviewWorkspacePreviewRequest):
    portfolio_context_selection: PortfolioContextSelectionRequest = Field(
        default_factory=PortfolioContextSelectionRequest
    )
    review_account_selection: ReviewAccountSelectionRequest = Field(default_factory=ReviewAccountSelectionRequest)


class PortfolioContextSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    context_reference: str
    context_source: PortfolioContextSource
    selection_mode: PortfolioContextSelectionMode
    summary_as_of: datetime | None
    latest_snapshot_as_of: datetime | None
    broker_snapshot: BrokerSnapshotMetadata
    stock_position_count: int = Field(ge=0)
    option_position_count: int = Field(ge=0)
    cash_state: PortfolioCashState
    label: str | None = None


class ReviewAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    account_reference: str
    display_label: str
    account_kind_label: str | None = None
    is_review_account: bool
    is_included_in_portfolio_scope: bool
    is_account_level_feasibility_source: bool

    @model_validator(mode="after")
    def review_account_payload_must_be_safe(self) -> "ReviewAccountRead":
        validate_account_reference(self.account_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class PortfolioScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    scope_reference: str
    scope_mode: PortfolioScopeMode
    display_label: str
    selection_mode: PortfolioContextSelectionMode | None = None
    context_reference: str | None = None
    included_account_labels: tuple[str, ...]
    excluded_account_labels: tuple[str, ...]
    account_level_feasibility_evaluated: bool
    account_level_feasibility_label: str
    caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def portfolio_scope_payload_must_be_safe(self) -> "PortfolioScopeRead":
        validate_scope_reference(self.scope_reference)
        if self.context_reference is not None:
            validate_portfolio_context_reference(self.context_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class ReportScopeMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_account: ReviewAccountRead | None = None
    portfolio_context_scope: PortfolioScopeRead
    scope_summary_label: str
    account_level_feasibility_evaluated: bool
    scope_caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def report_scope_payload_must_be_safe(self) -> "ReportScopeMetadataRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class TradeIntentSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    intent_id: str
    supported_flow: SupportedTradeReviewFlow
    asset_class: Literal["stock", "etf", "option"]
    intent_type: str
    status: str
    symbol: str | None = None
    action: str | None = None
    quantity: str | None = None
    price_assumption: str | None = None
    strategy_type: str | None = None
    underlying_symbol: str | None = None
    legs: tuple[WorkspaceOptionLegSummaryRead, ...] = ()


class ScenarioPayoffPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    label: str
    underlying_price: str
    net_cash_flow: str
    scenario_value: str
    scenario_pnl: str
    description: str


class ScenarioPayoffSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    points: tuple[ScenarioPayoffPointRead, ...]
    max_loss: str | None
    max_gain: str | None
    calculation_notes: tuple[str, ...]


class PortfolioImpactSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    broker_freshness_status: str
    market_freshness_status: str
    market_manual_review_required: bool
    concentration_symbol: str | None
    notes: tuple[str, ...]


class CashCollateralImpactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    estimated_trade_cash_change: str | None
    estimated_premium_cash_change: str | None
    estimated_collateral_requirement_change: str | None
    projected_free_cash_state: Literal["not_exposed"]
    notes: tuple[str, ...]


class ConcentrationAllocationImpactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    concentration_symbol: str | None
    estimated_concentration_value_change: str | None
    allocation_drift_status: Literal["not_modelled_in_phase_18a"]
    notes: tuple[str, ...]


class OptionsExposureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    underlying_symbol: str | None
    assignment_share_delta: str
    exercise_share_delta: str
    covered_call_coverage_model: Literal["not_applicable", "not_fully_modelled"]
    cash_secured_put_collateral_model: Literal["not_applicable", "generic_rule_only"]
    notes: tuple[str, ...]


class RiskRuleViolationSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: str
    severity: RiskSeverity
    message: str
    source: str
    metric: str | None = None
    actual: str | None = None
    policy_label: str | None = None


class MissingDataWarningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: str
    scope: str
    severity: Literal["info", "warning", "blocker"]
    message: str


class DeterministicTradeReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    highest_severity: RiskSeverity | None
    has_blocker: bool
    portfolio_impact: PortfolioImpactSummaryRead
    cash_collateral_impact: CashCollateralImpactRead
    concentration_allocation_impact: ConcentrationAllocationImpactRead
    options_exposure: OptionsExposureRead
    risk_rule_violations: tuple[RiskRuleViolationSummaryRead, ...]
    missing_data_warnings: tuple[MissingDataWarningRead, ...]
    scenario_payoff_summary: ScenarioPayoffSummaryRead


class AgentOrchestrationSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    run_reference: str
    workflow_version: str
    review_actionability_status: ReviewActionabilityStatus | None
    stage_order: tuple[str, ...]
    stage_statuses: dict[str, str]
    unavailable_stages: dict[str, str]
    source_agent_names: tuple[str, ...]
    report_composed: bool


class AnalysisOnlyReportOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    title: str
    content_markdown: str
    deterministic_sections: tuple[str, ...]
    llm_generated_sections: tuple[str, ...]
    source_agent_names: tuple[str, ...]


class WorkspaceCaveatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: str
    severity: WorkspaceCaveatSeverity
    applies_to: str
    message: str


class TradeReviewWorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_reference: str
    saved_review_source_reference: str | None = None
    generated_at: datetime
    calculation_version: str
    supported_flow: SupportedTradeReviewFlow
    trade_intent_summary: TradeIntentSummaryRead
    portfolio_context: PortfolioContextSummaryRead | None = None
    scope_metadata: ReportScopeMetadataRead | None = None
    actionability: PortfolioActionabilityDecision
    deterministic_review: DeterministicTradeReviewRead
    agent_orchestration: AgentOrchestrationSummaryRead | None = None
    report_output: AnalysisOnlyReportOutputRead | None = None
    caveats: tuple[WorkspaceCaveatRead, ...]

    @model_validator(mode="after")
    def workspace_payload_must_be_safe(self) -> "TradeReviewWorkspaceRead":
        if self.saved_review_source_reference is not None:
            validate_trade_review_saved_source_reference(self.saved_review_source_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class TradeReviewListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_reference: str
    created_at: datetime
    supported_flow: SupportedTradeReviewFlow
    review_flow_label: str
    symbol_or_underlying: str
    review_actionability_status: ReviewActionabilityStatus
    highest_severity: RiskSeverity | None
    report_status: TradeReviewReportStatus
    source_mode: TradeReviewListSourceMode
    broker_snapshot_freshness_label: str | None = None
    market_quote_freshness_label: str | None = None


class TradeReviewListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: Phase20BDataMode
    demo_notice: str | None = None
    items: tuple[TradeReviewListItemRead, ...]

    @model_validator(mode="after")
    def list_payload_must_be_safe(self) -> "TradeReviewListRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class PortfolioContextShapeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stock_position_count: int = Field(ge=0)
    option_position_count: int = Field(ge=0)


class PortfolioContextFreshnessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    freshness_scope: Literal["broker_snapshot", "market_quote"]
    status: ReadinessSnapshotStatus
    as_of_label: str | None = None
    display_label: str
    reason_codes: tuple[str, ...]
    is_blocking: bool


class PortfolioContextActionabilityPreviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_actionability_status: ReviewActionabilityStatus
    overall_review_mode: ReviewReadinessMode
    display_label: str
    is_blocking: bool


class PortfolioContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    context_reference: str
    context_label: str
    source_kind: PortfolioContextSourceKind
    portfolio_shape: PortfolioContextShapeRead
    cash_state: PortfolioCashState
    cash_state_label: str
    broker_snapshot_freshness: PortfolioContextFreshnessRead
    market_quote_freshness: PortfolioContextFreshnessRead | None = None
    market_data_unavailable: bool
    actionability_preview: PortfolioContextActionabilityPreviewRead
    available_flows: tuple[SupportedTradeReviewFlow, ...]
    caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def context_payload_must_be_safe(self) -> "PortfolioContextRead":
        validate_portfolio_context_reference(self.context_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class PortfolioContextListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: Phase20BDataMode
    demo_notice: str | None = None
    items: tuple[PortfolioContextRead, ...]

    @model_validator(mode="after")
    def context_list_payload_must_be_safe(self) -> "PortfolioContextListRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class PortfolioContextDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: Phase20BDataMode
    demo_notice: str | None = None
    context: PortfolioContextRead

    @model_validator(mode="after")
    def context_detail_payload_must_be_safe(self) -> "PortfolioContextDetailRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountDetailsReadinessCaveatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: str
    severity: WorkspaceCaveatSeverity
    title: str
    message: str

    @model_validator(mode="after")
    def account_readiness_caveat_payload_must_be_safe(self) -> "AccountDetailsReadinessCaveatRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountDetailAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    account_reference: str
    display_label: str
    account_kind_label: str
    source_kind: AccountDetailSourceKind
    source_label: str
    connection_status_label: str
    last_successful_sync_label: str | None = None
    privacy_display_mode: DashboardPrivacyDisplayMode
    broker_snapshot_freshness: PortfolioContextFreshnessRead
    market_quote_freshness: PortfolioContextFreshnessRead | None = None
    portfolio_shape: PortfolioContextShapeRead
    cash_state: PortfolioCashState
    cash_state_label: str
    total_value_label: str | None = None
    cash_label: str | None = None
    stock_etf_exposure_label: str | None = None
    options_exposure_label: str | None = None
    collateral_usage_label: str | None = None
    scope_roles: tuple[AccountScopeRole, ...]
    account_level_feasibility_evaluated: bool
    readiness_caveats: tuple[AccountDetailsReadinessCaveatRead, ...] = ()
    caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def account_detail_payload_must_be_safe(self) -> "AccountDetailAccountRead":
        validate_account_reference(self.account_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountDetailsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: AccountDetailsDataMode
    demo_notice: str | None = None
    generated_at: datetime
    details_reference: str = Field(pattern=r"^ad_[a-z0-9][a-z0-9_-]{5,79}$")
    source_label: str
    privacy_display_mode: DashboardPrivacyDisplayMode
    portfolio_scope: PortfolioScopeRead
    review_account: ReviewAccountRead | None = None
    accounts: tuple[AccountDetailAccountRead, ...]
    readiness_caveats: tuple[AccountDetailsReadinessCaveatRead, ...] = ()
    caveat_codes: tuple[str, ...]

    @model_validator(mode="after")
    def account_details_payload_must_be_safe(self) -> "AccountDetailsRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountDetailsSyncRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    account_reference: str
    status: Literal["succeeded", "partially_succeeded", "failed", "running"]
    message: str
    generated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def account_details_sync_payload_must_be_safe(self) -> "AccountDetailsSyncRead":
        validate_account_reference(self.account_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class SelectedAccountSummaryLabelsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    total_value_label: str | None = None
    cash_label: str | None = None
    cash_state_label: str
    stock_etf_exposure_label: str | None = None
    options_exposure_label: str | None = None
    collateral_usage_label: str | None = None

    @model_validator(mode="after")
    def selected_account_summary_payload_must_be_safe(self) -> "SelectedAccountSummaryLabelsRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountCashDisplayRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    row_reference: str = Field(pattern=r"^row_[a-z0-9][a-z0-9_-]{5,79}$")
    currency_label: str
    cash_amount_label: str
    available_cash_label: str | None = None
    buying_power_label: str | None = None
    balance_source_label: str | None = None
    cash_state_label: str
    freshness_label: str
    as_of_label: str | None = None
    caveat_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def cash_row_payload_must_be_safe(self) -> "AccountCashDisplayRowRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountTaxLotPaginationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    total_count: int = Field(ge=0)
    displayed_count: int = Field(ge=0)
    has_more: bool = False

    @model_validator(mode="after")
    def tax_lot_pagination_payload_must_be_safe(self) -> "AccountTaxLotPaginationRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountTaxLotDisplayRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    lot_reference: str = Field(pattern=r"^lotref_[a-z0-9][a-z0-9_-]{5,79}$")
    acquired_date_label: str | None = None
    term_label: Literal["short", "long", "unknown"] = "unknown"
    quantity_label: str | None = None
    purchase_price_label: str | None = None
    average_cost_label: str | None = None
    cost_basis_label: str | None = None
    current_value_label: str | None = None
    total_gain_loss_label: str | None = None
    gain_loss_percent_label: str | None = None
    source_label: str = "Broker-reported tax lot"

    @model_validator(mode="after")
    def tax_lot_payload_must_be_safe(self) -> "AccountTaxLotDisplayRowRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountEquityPositionDisplayRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    row_reference: str = Field(pattern=r"^row_[a-z0-9][a-z0-9_-]{5,79}$")
    symbol_label: str
    instrument_name_label: str | None = None
    asset_class_label: str
    quantity_label: str
    last_price_label: str | None = None
    market_value_label: str | None = None
    average_cost_label: str | None = None
    cost_basis_label: str | None = None
    total_gain_loss_label: str | None = None
    gain_loss_percent_label: str | None = None
    valuation_source_label: str | None = None
    tax_lot_rows: tuple[AccountTaxLotDisplayRowRead, ...] = ()
    tax_lot_pagination: AccountTaxLotPaginationRead | None = None
    freshness_label: str
    as_of_label: str | None = None
    caveat_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def equity_row_payload_must_be_safe(self) -> "AccountEquityPositionDisplayRowRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class AccountOptionPositionDisplayRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    row_reference: str = Field(pattern=r"^row_[a-z0-9][a-z0-9_-]{5,79}$")
    underlying_symbol_label: str
    contract_label: str
    option_type_label: str
    strike_label: str
    expiration_label: str
    side_label: str
    quantity_label: str
    last_price_label: str | None = None
    market_value_label: str | None = None
    average_cost_label: str | None = None
    cost_basis_label: str | None = None
    total_gain_loss_label: str | None = None
    gain_loss_percent_label: str | None = None
    multiplier_label: str | None = None
    valuation_source_label: str | None = None
    tax_lot_rows: tuple[AccountTaxLotDisplayRowRead, ...] = ()
    tax_lot_pagination: AccountTaxLotPaginationRead | None = None
    freshness_label: str
    as_of_label: str | None = None
    caveat_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def option_row_payload_must_be_safe(self) -> "AccountOptionPositionDisplayRowRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class SelectedAccountDetailsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: Literal["private_real_source", "unavailable"]
    generated_at: datetime
    account_reference: str
    display_label: str
    account_kind_label: str
    source_kind: AccountDetailSourceKind
    source_label: str
    connection_status_label: str
    last_successful_sync_label: str | None = None
    privacy_display_mode: DashboardPrivacyDisplayMode
    broker_snapshot_freshness: PortfolioContextFreshnessRead
    market_quote_freshness: PortfolioContextFreshnessRead | None = None
    summary_labels: SelectedAccountSummaryLabelsRead
    cash_rows: tuple[AccountCashDisplayRowRead, ...]
    equity_position_rows: tuple[AccountEquityPositionDisplayRowRead, ...]
    option_position_rows: tuple[AccountOptionPositionDisplayRowRead, ...]
    caveat_codes: tuple[str, ...]
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def selected_account_details_payload_must_be_safe(self) -> "SelectedAccountDetailsRead":
        validate_account_reference(self.account_reference)
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class DashboardSummaryDisplaySectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    section_key: DashboardDisplaySectionKind
    title: str
    display_label: str


class DashboardAccountSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: DashboardAccountSummaryDataMode
    demo_notice: str | None = None
    generated_at: datetime
    summary_reference: str = Field(pattern=r"^das_[a-z0-9][a-z0-9_-]{5,79}$")
    display_scope: DashboardAccountDisplayScope
    source_label: str
    valuation_basis: DashboardValuationBasis
    broker_snapshot_freshness: PortfolioContextFreshnessRead
    market_quote_freshness: PortfolioContextFreshnessRead | None = None
    market_data_mode: DashboardMarketDataMode
    privacy_display_mode: DashboardPrivacyDisplayMode
    market_data_unavailable: bool
    portfolio_shape: PortfolioContextShapeRead
    cash_state: PortfolioCashState
    cash_state_label: str
    total_value_label: str | None = None
    cash_label: str | None = None
    stock_etf_exposure_label: str | None = None
    options_exposure_label: str | None = None
    collateral_usage_label: str | None = None
    portfolio_shape_label: str
    position_count_label: str
    stock_exposure_label: str | None = None
    option_exposure_label: str | None = None
    caveat_codes: tuple[str, ...]
    display_sections: tuple[DashboardSummaryDisplaySectionRead, ...]

    @model_validator(mode="after")
    def dashboard_summary_payload_must_be_safe(self) -> "DashboardAccountSummaryRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class RiskAlertItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    alert_reference: str
    generated_at: datetime
    severity: RiskSeverity
    category: RiskAlertCategory
    title: str
    summary: str
    related_symbol_or_underlying: str | None = None
    related_review_reference: str | None = None
    freshness_scope: RiskAlertFreshnessScope | None = None
    is_blocking: bool


class RiskAlertListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: Phase20BDataMode
    demo_notice: str | None = None
    items: tuple[RiskAlertItemRead, ...]

    @model_validator(mode="after")
    def risk_alert_payload_must_be_safe(self) -> "RiskAlertListRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


class BrokerSnapshotReadinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    freshness_scope: Literal["broker_snapshot"] = "broker_snapshot"
    status: ReadinessSnapshotStatus
    as_of_label: str | None = None
    reason_codes: tuple[str, ...]
    display_label: str
    is_blocking: bool


class MarketQuoteReadinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    freshness_scope: Literal["market_quote"] = "market_quote"
    status: ReadinessSnapshotStatus
    as_of_label: str | None = None
    reason_codes: tuple[str, ...]
    display_label: str
    is_blocking: bool


class AgentProviderReadinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    provider_mode: AgentProviderMode
    provider_status: ReadinessAgentProviderStatus
    is_mock_default: bool
    last_checked_at: datetime | None = None
    display_label: str
    is_blocking: bool


class ReviewReadinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: Phase20BDataMode
    demo_notice: str | None = None
    generated_at: datetime
    overall_review_mode: ReviewReadinessMode
    broker_snapshot: BrokerSnapshotReadinessRead
    market_quotes: MarketQuoteReadinessRead
    agent_provider: AgentProviderReadinessRead
    recommended_user_action_label: str

    @model_validator(mode="after")
    def readiness_payload_must_be_safe(self) -> "ReviewReadinessRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


def validate_trade_review_workspace_payload(payload: object) -> None:
    """Reject private broker fields and advice-like wording in frontend payloads."""

    forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"trade review workspace payload contains forbidden private fields: {blocked}")

    rendered = repr(payload).lower()
    for phrase in PROHIBITED_TRADE_REVIEW_WORKSPACE_PHRASES:
        if phrase in rendered:
            raise ValueError(f"trade review workspace payload contains prohibited phrase: {phrase}")
