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
PortfolioContextSource: TypeAlias = Literal["snaptrade", "manual", "csv", "synthetic_mock"]
PortfolioContextSourceKind: TypeAlias = Literal["broker_snapshot", "manual", "csv", "synthetic_demo"]
PortfolioCashState: TypeAlias = Literal["available", "unavailable", "not_exposed"]
TradeReviewReportStatus: TypeAlias = Literal["preview_only", "saved", "generated", "unavailable"]
TradeReviewListSourceMode: TypeAlias = Literal["synthetic_preview", "portfolio_preview", "saved_review"]
Phase20BDataMode: TypeAlias = Literal["synthetic_demo", "persisted"]
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

_OPAQUE_CONTEXT_REFERENCE_RE = re.compile(r"^ctx_[a-z0-9][a-z0-9_-]{5,79}$")
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


class TradeReviewPortfolioPreviewRequest(TradeReviewWorkspacePreviewRequest):
    portfolio_context_selection: PortfolioContextSelectionRequest = Field(
        default_factory=PortfolioContextSelectionRequest
    )


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
    generated_at: datetime
    calculation_version: str
    supported_flow: SupportedTradeReviewFlow
    trade_intent_summary: TradeIntentSummaryRead
    portfolio_context: PortfolioContextSummaryRead | None = None
    actionability: PortfolioActionabilityDecision
    deterministic_review: DeterministicTradeReviewRead
    agent_orchestration: AgentOrchestrationSummaryRead | None = None
    report_output: AnalysisOnlyReportOutputRead | None = None
    caveats: tuple[WorkspaceCaveatRead, ...]

    @model_validator(mode="after")
    def workspace_payload_must_be_safe(self) -> "TradeReviewWorkspaceRead":
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
