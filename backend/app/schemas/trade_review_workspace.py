from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.actionability import (
    PortfolioActionabilityDecision,
    ReviewActionabilityStatus,
)
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys
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

FORBIDDEN_TRADE_REVIEW_WORKSPACE_FIELDS = FORBIDDEN_PRIVATE_CONTEXT_KEYS | {
    "provider_contract_id",
    "provider_contract_ids",
    "provider_symbol",
    "provider_symbols",
    "account_values",
    "raw_account_values",
}
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
    actionability: PortfolioActionabilityDecision
    deterministic_review: DeterministicTradeReviewRead
    agent_orchestration: AgentOrchestrationSummaryRead | None = None
    report_output: AnalysisOnlyReportOutputRead | None = None
    caveats: tuple[WorkspaceCaveatRead, ...]

    @model_validator(mode="after")
    def workspace_payload_must_be_safe(self) -> "TradeReviewWorkspaceRead":
        validate_trade_review_workspace_payload(self.model_dump(mode="python"))
        return self


def validate_trade_review_workspace_payload(payload: object) -> None:
    """Reject private broker fields and advice-like wording in frontend payloads."""

    forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_FIELDS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"trade review workspace payload contains forbidden private fields: {blocked}")

    rendered = repr(payload).lower()
    for phrase in PROHIBITED_TRADE_REVIEW_WORKSPACE_PHRASES:
        if phrase in rendered:
            raise ValueError(f"trade review workspace payload contains prohibited phrase: {phrase}")
