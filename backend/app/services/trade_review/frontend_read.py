"""Frontend-safe projection for the first Trade Review Workspace."""

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Any, Callable, Protocol
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, object_session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.services.broker_import.statuses import DATA_FRESHNESS_STATUSES
from app.schemas.actionability import (
    ActionabilityReason,
    BrokerSnapshotMetadata,
    MarketQuotesMetadata,
    PortfolioActionabilityDecision,
    PortfolioActionabilityInput,
)
from app.schemas.trade_review_workspace import (
    AccountDetailAccountRead,
    AccountCashDisplayRowRead,
    AccountDetailsRead,
    AccountDetailsReadinessCaveatRead,
    AccountEquityPositionDisplayRowRead,
    AccountOptionPositionDisplayRowRead,
    AccountTaxLotDisplayRowRead,
    AccountTaxLotPaginationRead,
    AgentOrchestrationSummaryRead,
    AnalysisOnlyReportOutputRead,
    CashCollateralImpactRead,
    ConcentrationAllocationImpactRead,
    DashboardAccountSummaryRead,
    DashboardSummaryDisplaySectionRead,
    DeterministicTradeReviewRead,
    InstrumentIdentityRead,
    MissingDataWarningRead,
    OptionsExposureRead,
    AgentProviderReadinessRead,
    BrokerSnapshotReadinessRead,
    MarketQuoteReadinessRead,
    PortfolioContextSelectionRequest,
    PortfolioContextActionabilityPreviewRead,
    PortfolioContextDetailRead,
    PortfolioContextFreshnessRead,
    PortfolioContextListRead,
    PortfolioContextRead,
    PortfolioContextShapeRead,
    PortfolioContextSummaryRead,
    PortfolioScopeRead,
    PortfolioImpactSummaryRead,
    ReportScopeMetadataRead,
    ReviewReadinessRead,
    ReviewAccountRead,
    ReviewAccountCandidateListRead,
    ReviewAccountCandidateRead,
    ReviewAccountSelectionRequest,
    RiskAlertItemRead,
    RiskAlertListRead,
    RiskRuleViolationSummaryRead,
    ScenarioPayoffPointRead,
    ScenarioPayoffSummaryRead,
    SelectedAccountDetailsRead,
    SelectedAccountSummaryLabelsRead,
    SupportedTradeReviewFlow,
    TradeReviewListItemRead,
    TradeReviewListRead,
    TradeReviewPreviewOptionLeg,
    TradeIntentSummaryRead,
    TradeReviewWorkspaceRead,
    TradeReviewWorkspacePreviewRequest,
    TradeReviewPortfolioPreviewRequest,
    validate_account_reference,
    WorkspaceCaveatRead,
    WorkspaceOptionLegSummaryRead,
    validate_portfolio_context_reference,
    validate_trade_review_workspace_payload,
)
from app.services.agents.orchestrator import AgentTeamOrchestrationResult, DEFAULT_AGENT_WORKFLOW_STAGES
from app.services.agents.report_composer import ReportComposerAgentOutput
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability
from app.services.trade_review.context import (
    CashContext,
    OptionPositionContext,
    PortfolioReviewContext,
    StockPositionContext,
)
from app.services.trade_review.exposure_adapter import (
    FUNDING_SHORTFALL_CAVEAT_CODE,
    try_build_exposure_evidence_sections,
    unavailable_exposure_evidence_sections,
)
from app.services.trade_review.models import (
    ETFTradeIntent,
    OptionLeg,
    OptionStrategyIntent,
    StockTradeIntent,
    TradeIntent,
    TradeIntentFreshnessSnapshot,
)
from app.services.trade_review.payoff import PayoffScenarioEngine
from app.services.trade_review.portfolio_impact import PortfolioImpactEngine
from app.services.trade_review.report import TradeReviewAgentProjection, build_trade_review_report, to_agent_safe_projection
from app.services.trade_review.risk import TradeReviewRiskEngine
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidator
from app.services.symbols import SymbolService


_LATEST_CONTEXT_REFERENCE = "ctx_demo_latest"
_STALE_CONTEXT_REFERENCE = "ctx_demo_stale"
_MISSING_MARKET_CONTEXT_REFERENCE = "ctx_demo_missing"
_NO_CONTEXT_REFERENCE = "ctx_demo_empty"

_DEMO_REVIEW_ACCOUNT_REFERENCE = "acctref_demo_primary"
_DEMO_SECONDARY_ACCOUNT_REFERENCE = "acctref_demo_longterm"
_DEMO_SCOPE_SELECTED_REFERENCE = "scope_demo_selected"
_DEMO_SCOPE_COMBINED_REFERENCE = "scope_demo_combined"
_DEMO_SCOPE_UNAVAILABLE_REFERENCE = "scope_demo_unavailable"
_DEMO_EMPTY_USER_REFERENCE = "00000000-0000-0000-0000-000000000000"
_PHASE20B_DEMO_NOTICE = "demo · not yet connected"
# This is the existing Account Details display vocabulary.  The selected-account
# snapshot resolver separately preserves canonical broker freshness for the
# actionability schema without widening this frontend read contract.
_BROKER_FRESHNESS_STATUS_READ_VALUES = {"fresh", "manual_review", "stale", "unknown", "unavailable"}
_POSITION_DEPENDENT_REAL_BROKER_FLOWS = {
    "stock_sell_trim",
    "etf_sell_trim",
    "covered_call",
    "cash_secured_put",
}


class _ExposureReviewContext(Protocol):
    """The deliberately small surface used by deterministic impact consumers."""

    summary_as_of: datetime
    cash: Any
    stock_positions: tuple[Any, ...]
    option_positions: tuple[Any, ...]


@dataclass(frozen=True)
class _ResolvedPortfolioContext:
    context: _ExposureReviewContext
    summary: PortfolioContextSummaryRead | None
    broker_snapshot: BrokerSnapshotMetadata
    market_quotes: MarketQuotesMetadata
    account_snapshot_unavailable: bool = False


@dataclass(frozen=True)
class _SelectedAccountSnapshotResolution:
    """Keep selected-account resolution failures distinct from demo selection."""

    resolved: _ResolvedPortfolioContext | None = None
    requested_but_unavailable: bool = False


@dataclass(frozen=True)
class _ResolvedPreviewInstrumentIdentity:
    supported_flow: SupportedTradeReviewFlow
    identity: InstrumentIdentityRead


@dataclass(frozen=True)
class _BrokerAccountDetailsRow:
    broker_account: BrokerAccount
    broker_connection: BrokerConnection
    latest_sync_run: BrokerSyncRun | None
    metrics: "_NormalizedAccountMetrics"


@dataclass(frozen=True)
class _NormalizedAccountMetrics:
    cash_total: Decimal | None = None
    reserved_collateral_cash: Decimal | None = None
    stock_etf_market_value: Decimal | None = None
    options_market_value: Decimal | None = None
    stock_position_count: int | None = None
    option_position_count: int | None = None


@dataclass(frozen=True)
class _SelectedAccountCashSnapshot:
    """Transient, lossy funding input for deterministic portfolio review."""

    available_funding_value: Decimal
    snapshot_as_of: datetime

    @property
    def free_cash(self) -> Decimal:
        """Expose only the adapter-compatible value; it is never serialized."""

        return self.available_funding_value


@dataclass(frozen=True)
class _SelectedAccountEquityExposure:
    """Position projection without identity, quantity, cost, or payload fields."""

    symbol: str
    asset_type: str
    market_value: Decimal | None
    snapshot_as_of: datetime


@dataclass(frozen=True)
class _SelectedAccountOptionExposure:
    """Options remain an aggregate-compatible asset-class input only."""

    symbol: str
    asset_type: str
    market_value: Decimal | None
    snapshot_as_of: datetime


@dataclass(frozen=True)
class _SelectedAccountSnapshotContext:
    """Safe account-snapshot view consumed by impact and exposure calculations.

    The persisted broker rows are intentionally reduced before this point.  The
    properties below retain compatibility with the existing deterministic
    consumers without adding their private field names to the context dump.
    """

    snapshot_as_of: datetime
    funding_snapshot: _SelectedAccountCashSnapshot | None
    equity_exposures: tuple[_SelectedAccountEquityExposure, ...]
    option_exposures: tuple[_SelectedAccountOptionExposure, ...]

    @property
    def summary_as_of(self) -> datetime:
        return self.snapshot_as_of

    @property
    def cash(self) -> _SelectedAccountCashSnapshot | None:
        return self.funding_snapshot

    @property
    def stock_positions(self) -> tuple[_SelectedAccountEquityExposure, ...]:
        return self.equity_exposures

    @property
    def option_positions(self) -> tuple[_SelectedAccountOptionExposure, ...]:
        return self.option_exposures


def build_trade_review_workspace_read(
    *,
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
    review_reference: str | None = None,
    supported_flow: SupportedTradeReviewFlow | None = None,
    orchestration_result: AgentTeamOrchestrationResult | None = None,
    report_output: ReportComposerAgentOutput | None = None,
    portfolio_context_summary: PortfolioContextSummaryRead | None = None,
    scope_metadata: ReportScopeMetadataRead | None = None,
    instrument_identity: InstrumentIdentityRead | None = None,
    generated_at: datetime | None = None,
) -> TradeReviewWorkspaceRead:
    """Build a sanitized read contract for the Phase 18A workspace.

    The mapper intentionally consumes the Phase 15 agent-safe projection rather
    than the raw deterministic report, because the raw report carries internal
    account ids and absolute cash/account values for owner-only persistence.
    """

    _reject_forbidden_input(projection.intent_summary, label="intent_summary")
    _reject_forbidden_input(projection.data_freshness_snapshot, label="data_freshness_snapshot")
    _reject_forbidden_input(asdict(projection.portfolio_impact), label="portfolio_impact")

    flow = supported_flow or _infer_supported_flow(projection.intent_summary)
    resolved_scope_metadata = scope_metadata or _report_scope_metadata_for_workspace(
        portfolio_context_summary=portfolio_context_summary,
    )
    effective_actionability = _gate_real_broker_position_truth(
        actionability,
        supported_flow=flow,
        scope_metadata=resolved_scope_metadata,
    )
    summary = _intent_summary(
        projection.intent_summary,
        supported_flow=flow,
        instrument_identity=instrument_identity,
    )
    read = TradeReviewWorkspaceRead(
        review_reference=review_reference or projection.intent_id,
        generated_at=generated_at or projection.generated_at or datetime.now(UTC),
        calculation_version=projection.calculation_version,
        supported_flow=flow,
        trade_intent_summary=summary,
        portfolio_context=portfolio_context_summary,
        scope_metadata=resolved_scope_metadata,
        actionability=effective_actionability,
        deterministic_review=DeterministicTradeReviewRead(
            highest_severity=projection.highest_severity,
            has_blocker=projection.has_blocker,
            portfolio_impact=_portfolio_impact(projection),
            cash_collateral_impact=_cash_collateral_impact(summary),
            concentration_allocation_impact=_concentration_allocation_impact(projection),
            options_exposure=_options_exposure(summary, projection, supported_flow=flow),
            risk_rule_violations=_risk_rule_violations(projection),
            missing_data_warnings=_missing_data_warnings(projection, effective_actionability),
            scenario_payoff_summary=_scenario_payoff_summary(projection),
        ),
        agent_orchestration=_agent_orchestration(orchestration_result),
        report_output=_report_output(report_output or (orchestration_result.report_output if orchestration_result else None)),
        caveats=_caveats(projection, effective_actionability, flow, scope_metadata=resolved_scope_metadata),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def list_recent_trade_reviews_for_user(
    user_id: object,
    *,
    generated_at: datetime | None = None,
) -> TradeReviewListRead:
    """Return a frontend-safe recent-review list.

    Phase 20B starts with a synthetic read contract because preview runs are
    still stateless. The payload is intentionally list-only and excludes raw
    intents, report bodies, account values, quantities, cash, and provider data.
    """

    user_reference = str(user_id)
    if user_reference == _DEMO_EMPTY_USER_REFERENCE:
        return TradeReviewListRead(
            data_mode="synthetic_demo",
            demo_notice=_PHASE20B_DEMO_NOTICE,
            items=(),
        )

    generated = generated_at or datetime.now(UTC)
    items = (
        TradeReviewListItemRead(
            review_reference="trv_demo_stock_buy_review",
            created_at=generated,
            supported_flow="stock_buy",
            review_flow_label=_review_flow_label("stock_buy"),
            symbol_or_underlying="XYZ",
            review_actionability_status="manual_confirmation_required",
            highest_severity="warning",
            report_status="preview_only",
            source_mode="synthetic_preview",
            broker_snapshot_freshness_label="Broker snapshot: manual review",
            market_quote_freshness_label="Market quotes: manual review",
        ),
        TradeReviewListItemRead(
            review_reference="trv_demo_etf_trim_review",
            created_at=generated,
            supported_flow="etf_sell_trim",
            review_flow_label=_review_flow_label("etf_sell_trim"),
            symbol_or_underlying="QQQ",
            review_actionability_status="analysis_only",
            highest_severity="info",
            report_status="generated",
            source_mode="portfolio_preview",
            broker_snapshot_freshness_label="Broker snapshot: user-confirmed",
            market_quote_freshness_label="Market quotes: manual",
        ),
        TradeReviewListItemRead(
            review_reference="trv_demo_covered_call_review",
            created_at=generated,
            supported_flow="covered_call",
            review_flow_label=_review_flow_label("covered_call"),
            symbol_or_underlying="XYZ",
            review_actionability_status="blocked_unknown_freshness",
            highest_severity="blocker",
            report_status="unavailable",
            source_mode="saved_review",
            broker_snapshot_freshness_label="Broker snapshot: unknown",
            market_quote_freshness_label="Market quotes: unknown",
        ),
    )
    read = TradeReviewListRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        items=items,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def list_risk_alerts_for_user(
    user_id: object,
    *,
    generated_at: datetime | None = None,
) -> RiskAlertListRead:
    """Return a frontend-safe aggregate risk-alert list.

    Phase 20B exposes synthetic alert rows only. Alerts are display summaries,
    not raw risk-rule violations, raw report content, or account-specific
    thresholds.
    """

    user_reference = str(user_id)
    if user_reference == _DEMO_EMPTY_USER_REFERENCE:
        return RiskAlertListRead(
            data_mode="synthetic_demo",
            demo_notice=_PHASE20B_DEMO_NOTICE,
            items=(),
        )

    generated = generated_at or datetime.now(UTC)
    items = (
        RiskAlertItemRead(
            alert_reference="rsk_demo_broker_snapshot_stale",
            generated_at=generated,
            severity="blocker",
            category="stale_broker_snapshot",
            title="Broker snapshot needs review",
            summary="Broker snapshot freshness is stale in this demo alert. Confirm portfolio context before relying on account-specific review output.",
            related_symbol_or_underlying=None,
            related_review_reference="trv_demo_covered_call_review",
            freshness_scope="broker_snapshot",
            is_blocking=True,
        ),
        RiskAlertItemRead(
            alert_reference="rsk_demo_market_quote_stale",
            generated_at=generated,
            severity="warning",
            category="stale_market_quote",
            title="Market quote freshness needs review",
            summary="Market quote freshness is stale in this demo alert. Treat the related review as analysis-only until quote data is refreshed or confirmed.",
            related_symbol_or_underlying="XYZ",
            related_review_reference="trv_demo_stock_buy_review",
            freshness_scope="market_quote",
            is_blocking=False,
        ),
        RiskAlertItemRead(
            alert_reference="rsk_demo_agent_provider_unavailable",
            generated_at=generated,
            severity="info",
            category="agent_provider",
            title="Optional agent provider unavailable",
            summary="Optional analysis provider output is unavailable in this demo alert. Deterministic backend review remains the source of review facts.",
            related_symbol_or_underlying=None,
            related_review_reference=None,
            freshness_scope="agent_provider",
            is_blocking=False,
        ),
    )
    read = RiskAlertListRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        items=items,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def get_review_readiness_for_user(
    user_id: object,
    *,
    generated_at: datetime | None = None,
) -> ReviewReadinessRead:
    """Return a frontend-safe aggregate review-readiness summary."""

    generated = generated_at or datetime.now(UTC)
    read = ReviewReadinessRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        generated_at=generated,
        overall_review_mode="analysis_only",
        broker_snapshot=BrokerSnapshotReadinessRead(
            status="stale",
            as_of_label="Demo broker snapshot needs review",
            reason_codes=("broker_snapshot_stale",),
            display_label="Broker snapshot requires review",
            is_blocking=True,
        ),
        market_quotes=MarketQuoteReadinessRead(
            status="manual_review",
            as_of_label="Demo market quotes require review",
            reason_codes=("market_quote_manual_review",),
            display_label="Market quote freshness requires review",
            is_blocking=False,
        ),
        agent_provider=AgentProviderReadinessRead(
            provider_mode="mock",
            provider_status="mock_default",
            is_mock_default=True,
            last_checked_at=generated,
            display_label="Mock agent provider active",
            is_blocking=False,
        ),
        recommended_user_action_label="Analysis-only: data limitations are present.",
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def get_dashboard_account_summary_for_user(
    user_id: object,
    *,
    generated_at: datetime | None = None,
) -> DashboardAccountSummaryRead:
    """Return a display-ready Dashboard account summary read contract."""

    generated = generated_at or datetime.now(UTC)
    if str(user_id) == _DEMO_EMPTY_USER_REFERENCE:
        read = _dashboard_account_summary_read(
            generated_at=generated,
            summary_reference="das_demo_unavailable",
            display_scope="unavailable",
            source_label="Synthetic demo summary unavailable",
            valuation_basis="unavailable",
            market_data_mode="unavailable",
            privacy_display_mode="amounts_hidden",
            stock_position_count=0,
            option_position_count=0,
            cash_state="unavailable",
            broker_status="unknown",
            broker_display_label="Broker snapshot unavailable",
            broker_reason_codes=("broker_snapshot_unavailable",),
            broker_is_blocking=True,
            market_status=None,
            market_display_label=None,
            market_reason_codes=(),
            market_is_blocking=True,
            total_value_label="Total value hidden · demo not connected",
            cash_label="Cash amount hidden · demo not connected",
            stock_etf_exposure_label="Stock/ETF exposure hidden · demo not connected",
            options_exposure_label="Options exposure hidden · demo not connected",
            collateral_usage_label="Collateral usage hidden · demo not connected",
            portfolio_shape_label="Portfolio shape unavailable",
            position_count_label="No portfolio context available",
            caveat_codes=(
                "summary_demo_only",
                "amounts_hidden",
                "portfolio_context_unavailable",
                "market_data_unavailable",
            ),
        )
    else:
        read = _dashboard_account_summary_read(
            generated_at=generated,
            summary_reference="das_demo_current",
            display_scope="synthetic_demo",
            source_label="Synthetic demo portfolio summary",
            valuation_basis="unavailable",
            market_data_mode="synthetic",
            privacy_display_mode="amounts_hidden",
            stock_position_count=2,
            option_position_count=1,
            cash_state="available",
            broker_status="stale",
            broker_display_label="Broker snapshot requires review",
            broker_reason_codes=("broker_snapshot_stale",),
            broker_is_blocking=True,
            market_status="manual_review",
            market_display_label="Market quote freshness requires review",
            market_reason_codes=("market_quote_manual_review",),
            market_is_blocking=False,
            total_value_label="Total value hidden · demo not connected",
            cash_label="Cash amount hidden · demo not connected",
            stock_etf_exposure_label="Stock/ETF exposure hidden · demo not connected",
            options_exposure_label="Options exposure hidden · demo not connected",
            collateral_usage_label="Collateral usage hidden · demo not connected",
            portfolio_shape_label="2 stock/ETF positions · 1 option position · counts only",
            position_count_label="3 positions · counts only",
            caveat_codes=(
                "summary_demo_only",
                "amounts_hidden",
                "synthetic_demo",
                "broker_snapshot_stale",
                "market_quote_manual_review",
            ),
        )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def get_account_details_for_user(
    user_id: object,
    *,
    db: Session | None = None,
    generated_at: datetime | None = None,
) -> AccountDetailsRead:
    """Return sanitized Account Details rows for selectable portfolio scope."""

    generated = generated_at or datetime.now(UTC)
    if db is not None:
        real_read = _real_account_details_for_user(db, user_id=user_id, generated_at=generated)
        if real_read is not None:
            return real_read

    if str(user_id) == _DEMO_EMPTY_USER_REFERENCE:
        read = AccountDetailsRead(
            data_mode="synthetic_demo",
            demo_notice=_PHASE20B_DEMO_NOTICE,
            generated_at=generated,
            details_reference="ad_demo_unavailable",
            source_label="Synthetic demo account details unavailable",
            privacy_display_mode="amounts_hidden",
            portfolio_scope=_portfolio_scope_read(
                scope_reference=_DEMO_SCOPE_UNAVAILABLE_REFERENCE,
                scope_mode="unavailable",
                display_label="No portfolio scope available",
                selection_mode=None,
                context_reference=None,
                included_account_labels=(),
                excluded_account_labels=(),
                account_level_feasibility_evaluated=False,
                account_level_feasibility_label="Account-level feasibility not evaluated",
                caveat_codes=("portfolio_scope_unavailable",),
            ),
            review_account=None,
            accounts=(),
            readiness_caveats=_account_readiness_caveats(
                ("portfolio_scope_unavailable", "amounts_hidden")
            ),
            caveat_codes=("account_details_demo_only", "portfolio_scope_unavailable", "amounts_hidden"),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        return read

    review_account = _review_account_read(
        account_reference=_DEMO_REVIEW_ACCOUNT_REFERENCE,
        display_label="Primary demo account",
        account_kind_label="Taxable brokerage",
        is_review_account=True,
        is_included_in_portfolio_scope=True,
        is_account_level_feasibility_source=False,
    )
    read = AccountDetailsRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        generated_at=generated,
        details_reference="ad_demo_current",
        source_label="Synthetic demo account details",
        privacy_display_mode="amounts_hidden",
        portfolio_scope=_portfolio_scope_read(
            scope_reference=_DEMO_SCOPE_COMBINED_REFERENCE,
            scope_mode="all_connected_accounts",
            display_label="Portfolio scope: All connected accounts",
            selection_mode=None,
            context_reference=None,
            included_account_labels=("Primary demo account", "Long-term demo account"),
            excluded_account_labels=(),
            account_level_feasibility_evaluated=False,
            account_level_feasibility_label="Aggregate context shown; account-level feasibility not evaluated",
            caveat_codes=("all_connected_accounts_scope_display_only", "account_level_feasibility_not_evaluated"),
        ),
        review_account=review_account,
        accounts=(
            _account_detail_account_read(
                account_reference=_DEMO_REVIEW_ACCOUNT_REFERENCE,
                display_label="Primary demo account",
                account_kind_label="Taxable brokerage",
                source_kind="synthetic_demo",
                stock_position_count=2,
                option_position_count=1,
                cash_state="available",
                broker_status="stale",
                broker_display_label="Broker snapshot requires review",
                broker_reason_codes=("broker_snapshot_stale",),
                broker_is_blocking=True,
                market_status="manual_review",
                market_display_label="Market quote freshness requires review",
                market_reason_codes=("market_quote_manual_review",),
                market_is_blocking=False,
                scope_roles=("review_account", "included_in_scope"),
                account_level_feasibility_evaluated=False,
                caveat_codes=(
                    "amounts_hidden",
                    "broker_snapshot_stale",
                    "market_quote_manual_review",
                    "cash_broker_reported",
                    "cash_collateral_not_fully_modeled",
                    "position_details_limited",
                ),
            ),
            _account_detail_account_read(
                account_reference=_DEMO_SECONDARY_ACCOUNT_REFERENCE,
                display_label="Long-term demo account",
                account_kind_label="Retirement brokerage",
                source_kind="synthetic_demo",
                stock_position_count=1,
                option_position_count=0,
                cash_state="not_exposed",
                broker_status="manual_review",
                broker_display_label="Broker snapshot requires review",
                broker_reason_codes=("broker_snapshot_manual_review",),
                broker_is_blocking=False,
                market_status="manual_review",
                market_display_label="Market quote freshness requires review",
                market_reason_codes=("market_quote_manual_review",),
                market_is_blocking=False,
                scope_roles=("included_in_scope",),
                account_level_feasibility_evaluated=False,
                caveat_codes=(
                    "amounts_hidden",
                    "account_level_feasibility_not_evaluated",
                    "cash_broker_reported",
                    "cash_collateral_not_fully_modeled",
                    "position_details_limited",
                ),
            ),
        ),
        readiness_caveats=_account_readiness_caveats(
            (
                "account_details_demo_only",
                "amounts_hidden",
                "all_connected_accounts_scope_display_only",
                "account_level_feasibility_not_evaluated",
                "cash_broker_reported",
                "cash_collateral_not_fully_modeled",
                "position_details_limited",
                "current_position_review_caveated",
            )
        ),
        caveat_codes=("account_details_demo_only", "amounts_hidden", "all_connected_accounts_scope_display_only"),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def list_review_account_candidates_for_user(
    user_id: object,
    *,
    db: Session,
    generated_at: datetime | None = None,
) -> ReviewAccountCandidateListRead:
    """Return safe selectable review-account candidates for Trade Review."""

    generated = generated_at or datetime.now(UTC)
    real_read = _real_account_details_for_user(db, user_id=user_id, generated_at=generated)
    if real_read is None:
        read = ReviewAccountCandidateListRead(
            data_mode="unavailable",
            generated_at=generated,
            candidates=(),
            caveat_codes=("review_account_candidates_unavailable",),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        return read

    candidates = tuple(
        ReviewAccountCandidateRead(
            account_reference=account.account_reference,
            display_label=account.display_label,
            account_kind_label=account.account_kind_label,
            source_kind=account.source_kind,
            source_label=account.source_label,
            connection_status_label=account.connection_status_label,
            last_successful_sync_label=account.last_successful_sync_label,
            broker_snapshot_freshness=account.broker_snapshot_freshness,
            market_quote_freshness=account.market_quote_freshness,
            portfolio_shape=account.portfolio_shape,
            cash_state_label=account.cash_state_label,
            account_level_feasibility_evaluated=account.account_level_feasibility_evaluated,
            account_level_feasibility_label="Account-level feasibility not evaluated",
            caveat_codes=account.caveat_codes,
        )
        for account in real_read.accounts
    )
    read = ReviewAccountCandidateListRead(
        data_mode=real_read.data_mode,
        generated_at=generated,
        candidates=candidates,
        caveat_codes=real_read.caveat_codes,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def update_account_details_nickname_for_user(
    user_id: object,
    account_reference: str,
    nickname: str | None,
    *,
    db: Session,
    generated_at: datetime | None = None,
) -> ReviewAccountCandidateRead:
    """Update a user-owned nickname for an opaque Account Details account ref."""

    resolved_reference = validate_account_reference(account_reference)
    row = _broker_account_detail_row_for_account_reference(
        db,
        user_id=user_id,
        account_reference=resolved_reference,
    )
    if row is None:
        raise LookupError("Account details not found")

    row.broker_account.user_nickname = nickname
    try:
        candidates = list_review_account_candidates_for_user(
            user_id,
            db=db,
            generated_at=generated_at,
        )
        selected = next(
            (
                candidate
                for candidate in candidates.candidates
                if candidate.account_reference == resolved_reference
            ),
            None,
        )
        if selected is None:
            raise LookupError("Account details not found")
    except Exception:
        db.rollback()
        raise

    db.commit()
    return selected


def get_selected_account_details_for_user(
    user_id: object,
    account_reference: str,
    *,
    db: Session,
    generated_at: datetime | None = None,
) -> SelectedAccountDetailsRead:
    """Return private display rows for one selected account owned by a user."""

    resolved_reference = validate_account_reference(account_reference)
    generated = generated_at or datetime.now(UTC)
    row = _broker_account_detail_row_for_account_reference(
        db,
        user_id=user_id,
        account_reference=resolved_reference,
    )
    if row is None:
        raise LookupError("account details not found")
    return _selected_account_details_from_broker_row(
        generated_at=generated,
        account_reference=resolved_reference,
        row=row,
    )


def resolve_broker_account_id_for_account_details_sync(
    user_id: object,
    account_reference: str,
    *,
    db: Session,
) -> UUID:
    """Resolve an opaque Account Details reference to an owned broker account id."""

    resolved_reference = validate_account_reference(account_reference)
    row = _broker_account_detail_row_for_account_reference(
        db,
        user_id=user_id,
        account_reference=resolved_reference,
    )
    if row is None:
        raise LookupError("account details not found")
    return row.broker_account.id


def _real_account_details_for_user(
    db: Session,
    *,
    user_id: object,
    generated_at: datetime,
) -> AccountDetailsRead | None:
    detail_rows = _broker_account_detail_rows_for_user(db, user_id=user_id)
    if not detail_rows:
        return None
    return _account_details_from_broker_rows(
        user_id=user_id,
        generated_at=generated_at,
        rows=detail_rows,
    )


def _broker_account_detail_rows_for_user(
    db: Session,
    *,
    user_id: object,
) -> tuple[_BrokerAccountDetailsRow, ...] | None:
    try:
        rows = list(
            db.execute(
                select(BrokerAccount, BrokerConnection)
                .join(BrokerConnection, BrokerAccount.broker_connection_id == BrokerConnection.id)
                .where(
                    BrokerConnection.user_id == user_id,
                    BrokerConnection.deleted_at.is_(None),
                    BrokerAccount.deleted_at.is_(None),
                )
                .order_by(
                    BrokerConnection.created_at.asc(),
                    BrokerAccount.created_at.asc(),
                    BrokerAccount.id.asc(),
                )
            )
        )
    except SQLAlchemyError:
        return None
    if not rows:
        return ()

    detail_rows = []
    for row in rows:
        broker_account, broker_connection = row
        try:
            latest_run = _latest_sync_run_for_broker_account(db, broker_account.id)
        except SQLAlchemyError:
            latest_run = None
        metrics = _normalized_account_metrics(
            db,
            broker_account.account_id,
            sync_run_id=latest_run.id if latest_run is not None else None,
        )
        detail_rows.append(
            _BrokerAccountDetailsRow(
                broker_account=broker_account,
                broker_connection=broker_connection,
                latest_sync_run=latest_run,
                metrics=metrics,
            )
        )
    return tuple(detail_rows)


def _broker_account_detail_row_for_account_reference(
    db: Session,
    *,
    user_id: object,
    account_reference: str,
) -> _BrokerAccountDetailsRow | None:
    rows = _broker_account_detail_rows_for_user(db, user_id=user_id)
    if not rows:
        return None
    for row in rows:
        if _opaque_account_reference(row.broker_account.id) == account_reference:
            return row
    return None


def _selected_account_details_from_broker_row(
    *,
    generated_at: datetime,
    account_reference: str,
    row: _BrokerAccountDetailsRow,
) -> SelectedAccountDetailsRead:
    broker_account = row.broker_account
    broker_connection = row.broker_connection
    account_display_label = _account_display_label(
        broker_connection=broker_connection,
        broker_account=broker_account,
        fallback_index=1,
        existing_labels=(),
    )
    sync_label = _last_successful_sync_label(
        broker_account.last_successful_sync_at or broker_connection.last_successful_sync_at
    )
    broker_status = _broker_snapshot_status(
        broker_account,
        broker_connection,
        has_successful_sync=sync_label is not None,
    )
    value_labels = _private_value_labels(row.metrics)
    cash_rows, equity_rows, option_rows, row_caveats = _selected_account_display_rows(row)
    purchase_history_available = any(
        display_row.tax_lot_rows for display_row in (*equity_rows, *option_rows)
    )
    read = SelectedAccountDetailsRead(
        data_mode="private_real_source",
        generated_at=generated_at,
        account_reference=account_reference,
        display_label=account_display_label,
        account_kind_label=_account_kind_label(broker_account.account_type),
        source_kind=_source_kind_for_broker_connection(broker_connection),
        source_label=_source_label_for_broker_connection(broker_connection),
        connection_status_label=_connection_status_label(broker_connection),
        last_successful_sync_label=sync_label,
        privacy_display_mode=value_labels["privacy_display_mode"],
        broker_snapshot_freshness=PortfolioContextFreshnessRead(
            freshness_scope="broker_snapshot",
            status=broker_status,
            as_of_label=sync_label or "Broker snapshot sync time unavailable",
            display_label=_broker_snapshot_display_label(broker_status),
            reason_codes=(f"broker_snapshot_{broker_status}",),
            is_blocking=broker_status in {"stale", "unknown", "unavailable"},
        ),
        market_quote_freshness=PortfolioContextFreshnessRead(
            freshness_scope="market_quote",
            status="unavailable",
            as_of_label="Market quotes unavailable",
            display_label="Market quotes unavailable",
            reason_codes=("market_quote_unavailable",),
            is_blocking=False,
        ),
        summary_labels=SelectedAccountSummaryLabelsRead(
            total_value_label=value_labels["total_value_label"],
            cash_label=value_labels["cash_label"],
            cash_state_label=_cash_state_label("available" if row.metrics.cash_total is not None else "not_exposed"),
            stock_etf_exposure_label=value_labels["stock_etf_exposure_label"],
            options_exposure_label=value_labels["options_exposure_label"],
            collateral_usage_label=value_labels["collateral_usage_label"],
        ),
        cash_rows=cash_rows,
        equity_position_rows=equity_rows,
        option_position_rows=option_rows,
        caveat_codes=(
            value_labels["caveat_code"],
            "market_quote_unavailable",
            *row_caveats,
            *(() if purchase_history_available else ("purchase_history_unavailable",)),
        ),
        limitations=(
            "Private account detail display uses normalized app-owned rows only.",
            "Normalized broker-reported tax-lot display rows may be shown when available; raw lot IDs, raw provider payloads, transactions, and orders are not exposed.",
            *(() if purchase_history_available else ("Purchase history unavailable from broker snapshot.",)),
        ),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _selected_account_display_rows(
    row: _BrokerAccountDetailsRow,
) -> tuple[
    tuple[AccountCashDisplayRowRead, ...],
    tuple[AccountEquityPositionDisplayRowRead, ...],
    tuple[AccountOptionPositionDisplayRowRead, ...],
    tuple[str, ...],
]:
    account_id = row.broker_account.account_id
    if account_id is None:
        return (), (), (), ("normalized_account_link_unavailable",)
    db = object_session(row.broker_account)
    if db is None:
        return (), (), (), ("normalized_account_session_unavailable",)
    latest_sync_run_id = row.latest_sync_run.id if row.latest_sync_run is not None else None
    cash_rows = _selected_account_cash_rows(db, account_id, sync_run_id=latest_sync_run_id)
    equity_rows = _selected_account_equity_rows(db, account_id, sync_run_id=latest_sync_run_id)
    option_rows = _selected_account_option_rows(db, account_id, sync_run_id=latest_sync_run_id)
    caveats = []
    if not cash_rows:
        caveats.append("cash_rows_unavailable")
    if not equity_rows:
        caveats.append("equity_position_rows_empty")
    if not option_rows:
        caveats.append("option_position_rows_empty")
    return cash_rows, equity_rows, option_rows, tuple(caveats)


def _selected_account_cash_rows(
    db: Session,
    account_id: object,
    *,
    sync_run_id: object | None,
) -> tuple[AccountCashDisplayRowRead, ...]:
    if sync_run_id is None:
        return ()
    try:
        cash = db.scalar(
            select(CashBalance)
            .where(CashBalance.account_id == account_id, CashBalance.sync_run_id == sync_run_id)
            .order_by(CashBalance.as_of.desc(), CashBalance.created_at.desc(), CashBalance.id.desc())
            .limit(1)
        )
    except SQLAlchemyError:
        return ()
    if cash is None:
        return ()
    read = AccountCashDisplayRowRead(
        row_reference=_opaque_row_reference(("cash", cash.id)),
        currency_label=(cash.currency or "USD").strip().upper(),
        cash_amount_label=_amount_value_or_hidden(cash.total_cash),
        available_cash_label=_amount_value_or_none(cash.available_cash),
        buying_power_label=_amount_value_or_none(cash.buying_power),
        balance_source_label="Broker-reported balance snapshot",
        cash_state_label=_cash_state_label("available"),
        freshness_label=_freshness_status_label(cash.data_freshness_status),
        as_of_label=_as_of_label(cash.as_of),
        caveat_codes=tuple(() if cash.buying_power is not None else ("buying_power_unavailable",)),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return (read,)


def _selected_account_equity_rows(
    db: Session,
    account_id: object,
    *,
    sync_run_id: object | None,
) -> tuple[AccountEquityPositionDisplayRowRead, ...]:
    if sync_run_id is None:
        return ()
    try:
        positions = list(
            db.scalars(
                select(StockPosition)
                .where(StockPosition.account_id == account_id, StockPosition.sync_run_id == sync_run_id)
                .order_by(
                    StockPosition.symbol.asc(),
                    StockPosition.as_of.desc(),
                    StockPosition.created_at.desc(),
                    StockPosition.id.desc(),
                )
            )
        )
    except SQLAlchemyError:
        return ()
    positions = _latest_stock_positions_by_symbol(positions)
    reads = []
    for position in positions:
        read = AccountEquityPositionDisplayRowRead(
            row_reference=_opaque_row_reference(("equity", position.id)),
            symbol_label=position.symbol.strip().upper(),
            instrument_name_label=position.instrument_name,
            asset_class_label=_asset_class_label(position.asset_type),
            quantity_label=_quantity_label(position.quantity, singular="share", plural="shares"),
            last_price_label=_amount_value_or_none(position.market_price),
            market_value_label=_amount_value_or_none(position.market_value),
            average_cost_label=_amount_value_or_none(position.average_price),
            cost_basis_label=_amount_value_or_none(position.cost_basis),
            total_gain_loss_label=_amount_value_or_none(position.open_pnl),
            gain_loss_percent_label=_gain_loss_percent_label(position.open_pnl, position.cost_basis),
            valuation_source_label=_valuation_source_label(position),
            tax_lot_rows=_tax_lot_rows(position),
            tax_lot_pagination=_tax_lot_pagination(position),
            freshness_label=_freshness_status_label(position.data_freshness_status),
            as_of_label=_as_of_label(position.as_of),
            caveat_codes=tuple(() if position.market_value is not None else ("market_value_unavailable",)),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        reads.append(read)
    return tuple(reads)


def _selected_account_option_rows(
    db: Session,
    account_id: object,
    *,
    sync_run_id: object | None,
) -> tuple[AccountOptionPositionDisplayRowRead, ...]:
    if sync_run_id is None:
        return ()
    try:
        rows = list(
            db.execute(
                select(OptionPosition, OptionContract)
                .join(OptionContract, OptionPosition.option_contract_id == OptionContract.id)
                .where(
                    OptionPosition.account_id == account_id,
                    OptionPosition.status == "open",
                    OptionPosition.sync_run_id == sync_run_id,
                    OptionContract.expiration_date >= date.today(),
                )
                .order_by(
                    OptionPosition.option_contract_id.asc(),
                    OptionPosition.as_of.desc(),
                    OptionPosition.created_at.desc(),
                    OptionPosition.id.desc(),
                )
            )
        )
    except SQLAlchemyError:
        return ()
    rows = _latest_option_position_rows_by_contract(rows)
    reads = []
    for option_position, contract in rows:
        market_value = _option_position_market_value(option_position, contract)
        cost_basis = _option_cost_basis(option_position, contract)
        average_cost = _option_average_cost_display_value(option_position, contract)
        read = AccountOptionPositionDisplayRowRead(
            row_reference=_opaque_row_reference(("option", option_position.id)),
            underlying_symbol_label=contract.underlying_symbol.strip().upper(),
            contract_label=_option_contract_label(contract),
            option_type_label=_option_type_label(contract.option_type),
            strike_label=_strike_label(contract.strike),
            expiration_label=contract.expiration_date.isoformat(),
            side_label=_position_side_label(option_position.position_side),
            quantity_label=_quantity_label(abs(Decimal(option_position.quantity)), singular="contract", plural="contracts"),
            last_price_label=_amount_value_or_none(option_position.market_price),
            market_value_label=_amount_value_or_none(market_value),
            average_cost_label=_amount_value_or_none(average_cost),
            cost_basis_label=_amount_value_or_none(cost_basis),
            total_gain_loss_label=_amount_value_or_none(option_position.open_pnl),
            gain_loss_percent_label=_gain_loss_percent_label(option_position.open_pnl, cost_basis),
            multiplier_label=_multiplier_label(contract.multiplier),
            valuation_source_label=_valuation_source_label(option_position),
            tax_lot_rows=_option_tax_lot_rows(option_position, contract),
            tax_lot_pagination=_option_tax_lot_pagination(option_position),
            freshness_label=_freshness_status_label(option_position.data_freshness_status),
            as_of_label=_as_of_label(option_position.as_of),
            caveat_codes=tuple(() if market_value is not None else ("market_value_unavailable",)),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        reads.append(read)
    return tuple(reads)


def _latest_stock_positions_by_symbol(positions: list[StockPosition]) -> list[StockPosition]:
    latest: dict[str, StockPosition] = {}
    for position in positions:
        symbol_key = position.symbol.strip().upper()
        if symbol_key not in latest:
            latest[symbol_key] = position
    return list(latest.values())


def _latest_option_position_rows_by_contract(rows: list[Any]) -> list[Any]:
    latest: dict[object, Any] = {}
    for row in rows:
        option_position = row[0]
        contract_key = option_position.option_contract_id
        if contract_key not in latest:
            latest[contract_key] = row
    return list(latest.values())


def _account_details_from_broker_rows(
    *,
    user_id: object,
    generated_at: datetime,
    rows: tuple[_BrokerAccountDetailsRow, ...],
) -> AccountDetailsRead | None:
    if not rows:
        return None

    account_labels: tuple[str, ...] = ()
    account_reads = []
    for index, row in enumerate(rows, start=1):
        broker_account = row.broker_account
        broker_connection = row.broker_connection
        account_display_label = _account_display_label(
            broker_connection=broker_connection,
            broker_account=broker_account,
            fallback_index=index,
            existing_labels=account_labels,
        )
        stock_count, option_count, count_caveats = _safe_position_type_counts(row.latest_sync_run)
        if row.metrics.stock_position_count is not None or row.metrics.option_position_count is not None:
            count_caveats = ()
            stock_count = row.metrics.stock_position_count or 0
            option_count = row.metrics.option_position_count or 0
        sync_label = _last_successful_sync_label(
            broker_account.last_successful_sync_at or broker_connection.last_successful_sync_at
        )
        broker_status = _broker_snapshot_status(
            broker_account,
            broker_connection,
            has_successful_sync=sync_label is not None,
        )
        value_labels = _account_overview_value_labels(row.metrics)
        account_reads.append(
            _account_detail_account_read(
                account_reference=_opaque_account_reference(broker_account.id),
                display_label=account_display_label,
                account_kind_label=_account_kind_label(broker_account.account_type),
                source_kind=_source_kind_for_broker_connection(broker_connection),
                source_label=_source_label_for_broker_connection(broker_connection),
                connection_status_label=_connection_status_label(broker_connection),
                last_successful_sync_label=sync_label,
                stock_position_count=stock_count,
                option_position_count=option_count,
                cash_state="available" if row.metrics.cash_total is not None else "not_exposed",
                broker_status=broker_status,
                broker_display_label=_broker_snapshot_display_label(broker_status),
                broker_as_of_label=sync_label or "Broker snapshot sync time unavailable",
                broker_reason_codes=(f"broker_snapshot_{broker_status}",),
                broker_is_blocking=broker_status in {"stale", "unknown", "unavailable"},
                market_status="unavailable",
                market_as_of_label="Market quotes unavailable",
                market_display_label="Market quotes unavailable",
                market_reason_codes=("market_quote_unavailable",),
                market_is_blocking=False,
                privacy_display_mode=value_labels["privacy_display_mode"],
                total_value_label=value_labels["total_value_label"],
                cash_label=value_labels["cash_label"],
                stock_etf_exposure_label=value_labels["stock_etf_exposure_label"],
                options_exposure_label=value_labels["options_exposure_label"],
                collateral_usage_label=value_labels["collateral_usage_label"],
                scope_roles=("included_in_scope",),
                account_level_feasibility_evaluated=False,
                caveat_codes=(
                    value_labels["caveat_code"],
                    f"broker_snapshot_{broker_status}",
                    "market_quote_unavailable",
                    "cash_broker_reported",
                    "cash_collateral_not_fully_modeled",
                    "position_details_limited",
                    "stale_local_rows_possible",
                    "current_position_review_caveated",
                    *count_caveats,
                ),
            )
        )
        account_labels += (account_display_label,)

    portfolio_scope = _portfolio_scope_read(
        scope_reference=_opaque_scope_reference(user_id),
        scope_mode="all_connected_accounts",
        display_label="Portfolio scope: All connected accounts",
        selection_mode=None,
        context_reference=None,
        included_account_labels=account_labels,
        excluded_account_labels=(),
        account_level_feasibility_evaluated=False,
        account_level_feasibility_label="Aggregate context shown; account-level feasibility not evaluated",
        caveat_codes=("all_connected_accounts_scope_display_only", "account_level_feasibility_not_evaluated"),
    )
    read = AccountDetailsRead(
        data_mode="private_real_source",
        demo_notice=None,
        generated_at=generated_at,
        details_reference=_opaque_account_details_reference(user_id),
        source_label="Connected broker snapshots",
        privacy_display_mode=_account_details_privacy_display_mode(tuple(account_reads)),
        portfolio_scope=portfolio_scope,
        review_account=None,
        accounts=tuple(account_reads),
        readiness_caveats=_account_readiness_caveats(
            (
                *_account_details_privacy_caveat_codes(tuple(account_reads)),
                "all_connected_accounts_scope_display_only",
                "account_level_feasibility_not_evaluated",
                "cash_broker_reported",
                "cash_collateral_not_fully_modeled",
                "position_details_limited",
                "stale_local_rows_possible",
                "current_position_review_caveated",
            )
        ),
        caveat_codes=(
            *_account_details_privacy_caveat_codes(tuple(account_reads)),
            "all_connected_accounts_scope_display_only",
        ),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def list_portfolio_contexts_for_user(
    user_id: object,
    *,
    generated_at: datetime | None = None,
) -> PortfolioContextListRead:
    """Return sanitized standalone portfolio-context cards for a user."""

    user_reference = str(user_id)
    if user_reference == _DEMO_EMPTY_USER_REFERENCE:
        return PortfolioContextListRead(
            data_mode="synthetic_demo",
            demo_notice=_PHASE20B_DEMO_NOTICE,
            items=(),
        )

    generated = generated_at or datetime.now(UTC)
    read = PortfolioContextListRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        items=tuple(_portfolio_context_catalog(generated).values()),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def get_latest_portfolio_context_for_user(
    user_id: object,
    *,
    generated_at: datetime | None = None,
) -> PortfolioContextDetailRead:
    """Return the latest sanitized portfolio-context detail."""

    user_reference = str(user_id)
    generated = generated_at or datetime.now(UTC)
    if user_reference == _DEMO_EMPTY_USER_REFERENCE:
        context = _empty_portfolio_context_read(generated)
    else:
        context = _portfolio_context_catalog(generated)[_LATEST_CONTEXT_REFERENCE]
    return _portfolio_context_detail(context)


def get_portfolio_context_for_user(
    user_id: object,
    context_reference: str,
    *,
    generated_at: datetime | None = None,
) -> PortfolioContextDetailRead:
    """Return one sanitized portfolio-context detail by opaque reference."""

    reference = validate_portfolio_context_reference(context_reference)
    generated = generated_at or datetime.now(UTC)
    if reference == _NO_CONTEXT_REFERENCE:
        return _portfolio_context_detail(_empty_portfolio_context_read(generated))
    if str(user_id) == _DEMO_EMPTY_USER_REFERENCE:
        raise LookupError("portfolio context not found")
    catalog = _portfolio_context_catalog(generated)
    if reference not in catalog:
        raise LookupError("portfolio context not found")
    return _portfolio_context_detail(catalog[reference])


def build_trade_review_workspace_preview(
    payload: TradeReviewWorkspacePreviewRequest,
    *,
    generated_at: datetime | None = None,
    symbol_service: SymbolService | None = None,
) -> TradeReviewWorkspaceRead:
    """Build a stateless synthetic preview for the Phase 18A API route."""

    generated = generated_at or datetime.now(UTC)
    actionability = evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=_default_preview_broker_snapshot(),
            market_quotes=_default_preview_market_quotes(),
            user_confirmation=None,
        ),
        evaluated_at=generated,
    )
    resolved_identity = _resolve_preview_instrument_identity(payload, symbol_service=symbol_service)
    reconciled_payload = payload.model_copy(update={"supported_flow": resolved_identity.supported_flow})
    intent = _preview_intent(reconciled_payload, generated_at=generated)
    market_snapshot = TradeReviewMarketSnapshot(
        report_market_snapshot=None,
        missing_symbols=() if actionability.market_quotes.actionability_status == "actionable_snapshot" else (_intent_symbol(intent),),
        manual_review_required=actionability.market_quotes.actionability_status != "actionable_snapshot",
    )
    validation = TradeIntentValidator().validate(intent, today=generated.date())
    payoff = PayoffScenarioEngine().evaluate(intent)
    portfolio_context = PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=generated,
        latest_snapshot_as_of=generated,
        total_internal_value=Decimal("0"),
        data_sources=("synthetic_preview",),
        data_freshness_statuses=(actionability.broker_snapshot.freshness_status,),
        cash=None,
        stock_positions=(),
        option_positions=(),
    )
    impact = PortfolioImpactEngine().calculate(
        intent=intent,
        portfolio_context=portfolio_context,
        market_snapshot=market_snapshot,
        payoff=payoff,
    )
    risk = TradeReviewRiskEngine().evaluate(
        validation=validation,
        portfolio_impact=impact,
        market_snapshot=market_snapshot,
    )
    report = build_trade_review_report(
        intent=intent,
        generated_at=generated,
        validation=validation,
        payoff=payoff,
        portfolio_impact=impact,
        risk=risk,
        market_snapshot=market_snapshot,
    )
    workspace = build_trade_review_workspace_read(
        projection=to_agent_safe_projection(report),
        actionability=actionability,
        review_reference=report.intent_id,
        supported_flow=resolved_identity.supported_flow,
        instrument_identity=resolved_identity.identity,
        generated_at=generated,
    )
    return _workspace_with_instrument_reconciliation_caveat(workspace)


def _workspace_with_exposure_caveats(
    workspace: TradeReviewWorkspaceRead,
    sections: tuple[Any, ...],
) -> TradeReviewWorkspaceRead:
    section_caveat_codes = {
        code
        for section in sections
        for code in tuple(getattr(section, "caveat_codes", ()))
    }
    additions = {
        FUNDING_SHORTFALL_CAVEAT_CODE: WorkspaceCaveatRead(
            code=FUNDING_SHORTFALL_CAVEAT_CODE,
            severity="warning",
            applies_to="cash_collateral_impact",
            message=(
                "The reviewed cash snapshot did not cover the proposed purchase; "
                "external funding was assumed for deterministic exposure math."
            ),
        ),
        "position_market_value_unavailable": WorkspaceCaveatRead(
            code="position_market_value_unavailable",
            severity="warning",
            applies_to="portfolio_impact",
            message=(
                "Some reviewed position values were unavailable, so deterministic exposure math excludes those inputs."
            ),
        ),
        "account_snapshot_unavailable": WorkspaceCaveatRead(
            code="account_snapshot_unavailable",
            severity="warning",
            applies_to="scope_metadata",
            message=(
                "The selected account's synced snapshot was unavailable, so exposure impact was not computed."
            ),
        ),
    }
    new_caveats = tuple(
        caveat
        for code, caveat in additions.items()
        if code in section_caveat_codes and not any(existing.code == code for existing in workspace.caveats)
    )
    if not new_caveats:
        return workspace
    return workspace.model_copy(
        update={
            "caveats": (
                *workspace.caveats,
                *new_caveats,
            )
        }
    )


def _workspace_with_instrument_reconciliation_caveat(
    workspace: TradeReviewWorkspaceRead,
) -> TradeReviewWorkspaceRead:
    if workspace.trade_intent_summary.instrument_identity.resolution_status != "mismatch_reconciled":
        return workspace
    if any(caveat.code == "instrument_type_reconciled" for caveat in workspace.caveats):
        return workspace
    return workspace.model_copy(
        update={
            "caveats": (
                *workspace.caveats,
                WorkspaceCaveatRead(
                    code="instrument_type_reconciled",
                    severity="info",
                    applies_to="trade_intent",
                    message=(
                        "The submitted stock or ETF flow was reconciled to the reviewed symbol-directory "
                        "instrument type before deterministic calculations."
                    ),
                ),
            )
        }
    )


def _portfolio_context_detail(context: PortfolioContextRead) -> PortfolioContextDetailRead:
    read = PortfolioContextDetailRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        context=context,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _dashboard_account_summary_read(
    *,
    generated_at: datetime,
    summary_reference: str,
    display_scope: str,
    source_label: str,
    valuation_basis: str,
    market_data_mode: str,
    privacy_display_mode: str,
    stock_position_count: int,
    option_position_count: int,
    cash_state: str,
    broker_status: str,
    broker_display_label: str,
    broker_reason_codes: tuple[str, ...],
    broker_is_blocking: bool,
    market_status: str | None,
    market_display_label: str | None,
    market_reason_codes: tuple[str, ...],
    market_is_blocking: bool,
    total_value_label: str,
    cash_label: str,
    stock_etf_exposure_label: str,
    options_exposure_label: str,
    collateral_usage_label: str,
    portfolio_shape_label: str,
    position_count_label: str,
    caveat_codes: tuple[str, ...],
) -> DashboardAccountSummaryRead:
    market_quote_freshness = None
    if market_status is not None:
        market_quote_freshness = PortfolioContextFreshnessRead(
            freshness_scope="market_quote",
            status=market_status,
            as_of_label="Demo market quotes require review",
            display_label=market_display_label or "Market quote freshness unavailable",
            reason_codes=market_reason_codes,
            is_blocking=market_is_blocking,
        )

    read = DashboardAccountSummaryRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        generated_at=generated_at,
        summary_reference=summary_reference,
        display_scope=display_scope,
        source_label=source_label,
        valuation_basis=valuation_basis,
        broker_snapshot_freshness=PortfolioContextFreshnessRead(
            freshness_scope="broker_snapshot",
            status=broker_status,
            as_of_label="Demo broker snapshot needs review",
            display_label=broker_display_label,
            reason_codes=broker_reason_codes,
            is_blocking=broker_is_blocking,
        ),
        market_quote_freshness=market_quote_freshness,
        market_data_mode=market_data_mode,
        privacy_display_mode=privacy_display_mode,
        market_data_unavailable=market_quote_freshness is None,
        portfolio_shape=PortfolioContextShapeRead(
            stock_position_count=stock_position_count,
            option_position_count=option_position_count,
        ),
        cash_state=cash_state,
        cash_state_label=_cash_state_label(cash_state),
        total_value_label=total_value_label,
        cash_label=cash_label,
        stock_etf_exposure_label=stock_etf_exposure_label,
        options_exposure_label=options_exposure_label,
        collateral_usage_label=collateral_usage_label,
        portfolio_shape_label=portfolio_shape_label,
        position_count_label=position_count_label,
        stock_exposure_label=stock_etf_exposure_label,
        option_exposure_label=options_exposure_label,
        caveat_codes=caveat_codes,
        display_sections=(
            DashboardSummaryDisplaySectionRead(
                section_key="summary",
                title="Portfolio summary",
                display_label="Synthetic demo account summary",
            ),
            DashboardSummaryDisplaySectionRead(
                section_key="freshness",
                title="Data freshness",
                display_label="Broker and market freshness are tracked separately",
            ),
            DashboardSummaryDisplaySectionRead(
                section_key="shape",
                title="Portfolio shape",
                display_label="Counts only; detailed rows are not exposed",
            ),
        ),
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _review_account_read(
    *,
    account_reference: str,
    display_label: str,
    account_kind_label: str,
    is_review_account: bool,
    is_included_in_portfolio_scope: bool,
    is_account_level_feasibility_source: bool,
) -> ReviewAccountRead:
    read = ReviewAccountRead(
        account_reference=account_reference,
        display_label=display_label,
        account_kind_label=account_kind_label,
        is_review_account=is_review_account,
        is_included_in_portfolio_scope=is_included_in_portfolio_scope,
        is_account_level_feasibility_source=is_account_level_feasibility_source,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _latest_sync_run_for_broker_account(db: Session, broker_account_id: object) -> BrokerSyncRun | None:
    return db.scalar(
        select(BrokerSyncRun)
        .where(
            BrokerSyncRun.broker_account_id == broker_account_id,
            BrokerSyncRun.status.in_(("succeeded", "partially_succeeded")),
        )
        .order_by(
            func.coalesce(BrokerSyncRun.completed_at, BrokerSyncRun.created_at).desc(),
            BrokerSyncRun.created_at.desc(),
            BrokerSyncRun.id.desc(),
        )
        .limit(1)
    )


def _account_details_privacy_display_mode(accounts: tuple[AccountDetailAccountRead, ...]) -> str:
    if any(account.privacy_display_mode == "amounts_visible" for account in accounts):
        return "amounts_visible"
    return "amounts_hidden"


def _account_details_privacy_caveat_codes(accounts: tuple[AccountDetailAccountRead, ...]) -> tuple[str, ...]:
    if any("some_amounts_hidden" in account.caveat_codes for account in accounts):
        return ("some_amounts_hidden",)
    row_modes = {account.privacy_display_mode for account in accounts}
    if row_modes == {"amounts_visible"}:
        return ()
    if row_modes == {"amounts_hidden", "amounts_visible"}:
        return ("some_amounts_hidden",)
    return ("amounts_hidden",)


def _account_readiness_caveats(caveat_codes: tuple[str, ...]) -> tuple[AccountDetailsReadinessCaveatRead, ...]:
    """Map compatibility caveat codes to display-ready Account Details messages."""

    catalog: dict[str, tuple[str, str, str]] = {
        "account_details_demo_only": (
            "info",
            "Demo account details",
            "Account Details is showing synthetic demo rows until connected broker data is available.",
        ),
        "portfolio_scope_unavailable": (
            "warning",
            "Portfolio scope unavailable",
            "No portfolio scope is available for this account overview.",
        ),
        "amounts_hidden": (
            "info",
            "Amounts hidden",
            "Private amount labels are hidden or unavailable for this account overview.",
        ),
        "some_amounts_hidden": (
            "info",
            "Some amounts hidden",
            "Some private amount labels are hidden or unavailable for this account overview.",
        ),
        "all_connected_accounts_scope_display_only": (
            "info",
            "All connected accounts scope",
            "This overview summarizes connected accounts and does not select an account for trade feasibility.",
        ),
        "account_level_feasibility_not_evaluated": (
            "info",
            "Account-level feasibility not evaluated",
            "Aggregate Account Details does not evaluate whether a single account can support a trade.",
        ),
        "cash_broker_reported": (
            "info",
            "Cash is broker-reported",
            "Cash labels come from the broker snapshot and may not match settled or withdrawable cash.",
        ),
        "cash_collateral_not_fully_modeled": (
            "warning",
            "Cash and collateral need review",
            "Buying power, free cash, and option collateral treatment are not fully modeled yet.",
        ),
        "position_details_limited": (
            "warning",
            "Position details limited",
            "Position detail display is temporarily limited while latest-sync membership is verified.",
        ),
        "stale_local_rows_possible": (
            "warning",
            "Local row history may include stale records",
            "Older normalized rows may remain in storage; overview counts use the latest verified sync boundary.",
        ),
        "current_position_review_caveated": (
            "warning",
            "Current-position review caveated",
            "Current-position review remains caveated until sync membership and option status semantics are fully reviewed.",
        ),
        "market_quote_unavailable": (
            "info",
            "Market quotes unavailable",
            "Broker snapshot freshness and market quote freshness are tracked separately; market quotes are unavailable here.",
        ),
        "market_quote_manual_review": (
            "info",
            "Market quotes need review",
            "Market quote freshness is separate from broker snapshot freshness and needs review.",
        ),
        "broker_snapshot_fresh": (
            "info",
            "Broker snapshot available",
            "Broker snapshot data is available; it is broker-reported data, not live market data.",
        ),
        "broker_snapshot_manual_review": (
            "warning",
            "Broker snapshot needs review",
            "Broker snapshot freshness needs manual review before relying on portfolio-specific output.",
        ),
        "broker_snapshot_stale": (
            "warning",
            "Broker snapshot stale",
            "Broker snapshot may be stale; refresh or confirm it before relying on portfolio-specific output.",
        ),
        "broker_snapshot_unknown": (
            "warning",
            "Broker snapshot freshness unknown",
            "Broker snapshot freshness is unknown for this account overview.",
        ),
        "broker_snapshot_unavailable": (
            "warning",
            "Broker snapshot unavailable",
            "Broker snapshot data is unavailable for this account overview.",
        ),
        "position_type_counts_unavailable": (
            "warning",
            "Position counts unavailable",
            "Broker-reported position type counts are unavailable for this account overview.",
        ),
    }
    severity_fallback: dict[str, str] = {
        "fresh": "info",
        "available": "info",
        "hidden": "info",
        "unavailable": "warning",
        "unknown": "warning",
        "stale": "warning",
    }

    reads: list[AccountDetailsReadinessCaveatRead] = []
    seen: set[str] = set()
    for code in caveat_codes:
        if code in seen:
            continue
        seen.add(code)
        severity, title, message = catalog.get(
            code,
            (
                next((value for key, value in severity_fallback.items() if key in code), "info"),
                code.replace("_", " ").capitalize(),
                "Additional broker readiness caveat is available for this account overview.",
            ),
        )
        reads.append(
            AccountDetailsReadinessCaveatRead(
                code=code,
                severity=severity,
                title=title,
                message=message,
            )
        )
    return tuple(reads)


def _normalized_account_metrics(
    db: Session,
    account_id: object | None,
    *,
    sync_run_id: object | None = None,
) -> _NormalizedAccountMetrics:
    if account_id is None or sync_run_id is None:
        return _NormalizedAccountMetrics()
    try:
        cash = db.scalar(
            select(CashBalance)
            .where(CashBalance.account_id == account_id, CashBalance.sync_run_id == sync_run_id)
            .order_by(CashBalance.as_of.desc(), CashBalance.created_at.desc(), CashBalance.id.desc())
            .limit(1)
        )
        stock_positions = list(
            db.scalars(
                select(StockPosition)
                .where(StockPosition.account_id == account_id, StockPosition.sync_run_id == sync_run_id)
                .order_by(
                    StockPosition.symbol.asc(),
                    StockPosition.as_of.desc(),
                    StockPosition.created_at.desc(),
                    StockPosition.id.desc(),
                )
            )
        )
        option_position_rows = list(
            db.execute(
                select(OptionPosition)
                .add_columns(OptionContract)
                .join(OptionContract, OptionPosition.option_contract_id == OptionContract.id)
                .where(
                    OptionPosition.account_id == account_id,
                    OptionPosition.status == "open",
                    OptionPosition.sync_run_id == sync_run_id,
                    OptionContract.expiration_date >= date.today(),
                )
                .order_by(
                    OptionPosition.option_contract_id.asc(),
                    OptionPosition.as_of.desc(),
                    OptionPosition.created_at.desc(),
                    OptionPosition.id.desc(),
                )
            )
        )
    except SQLAlchemyError:
        return _NormalizedAccountMetrics()

    latest_stock_positions = _latest_stock_positions_by_symbol(stock_positions)
    latest_option_rows = _latest_option_position_rows_by_contract(option_position_rows)
    return _NormalizedAccountMetrics(
        cash_total=cash.total_cash if cash is not None else None,
        reserved_collateral_cash=cash.reserved_collateral_cash if cash is not None else None,
        stock_etf_market_value=_sum_position_market_values(latest_stock_positions),
        options_market_value=_sum_option_position_market_values(latest_option_rows),
        stock_position_count=len(latest_stock_positions),
        option_position_count=len(latest_option_rows),
    )


def _sum_position_market_values(positions: list[StockPosition] | list[OptionPosition]) -> Decimal | None:
    if not positions:
        return Decimal("0")
    return _sum_optional_decimals(position.market_value for position in positions)


def _sum_option_position_market_values(rows: list[Any]) -> Decimal | None:
    if not rows:
        return Decimal("0")
    return _sum_optional_decimals(_option_position_market_value(position, contract) for position, contract in rows)


def _latest_option_positions_by_contract(positions: list[OptionPosition]) -> list[OptionPosition]:
    latest: dict[object, OptionPosition] = {}
    for position in positions:
        contract_key = position.option_contract_id
        if contract_key not in latest:
            latest[contract_key] = position
    return list(latest.values())


def _sum_optional_decimals(values: object) -> Decimal | None:
    total = Decimal("0")
    found = False
    for value in values:
        if value is None:
            continue
        total += Decimal(value)
        found = True
    return total if found else None


def _safe_position_type_counts(sync_run: BrokerSyncRun | None) -> tuple[int, int, tuple[str, ...]]:
    summary = sync_run.summary if sync_run is not None and isinstance(sync_run.summary, dict) else {}
    stock_count = _safe_non_negative_int(summary.get("stock_positions_count"))
    option_count = _safe_non_negative_int(summary.get("option_positions_count"))
    caveats: tuple[str, ...] = ()
    if stock_count is None and option_count is None:
        caveats = ("position_type_counts_unavailable",)
    return stock_count or 0, option_count or 0, caveats


def _safe_non_negative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _source_kind_for_broker_connection(connection: BrokerConnection) -> str:
    if connection.provider.strip().lower() == "snaptrade":
        return "snaptrade"
    return "unknown"


def _source_label_for_broker_connection(connection: BrokerConnection) -> str:
    if connection.provider.strip().lower() == "snaptrade":
        return "SnapTrade"
    return "Connected broker"


def _connection_status_label(connection: BrokerConnection) -> str:
    statuses = {connection.connection_status, connection.sync_status, connection.data_freshness_status}
    normalized = {status.strip().lower() for status in statuses if status}
    if "reauth_required" in normalized:
        return "Reconnect required"
    if normalized & {"error", "failed"}:
        return "Connection needs attention"
    if "disabled" in normalized:
        return "Connection disabled"
    if connection.connection_status.strip().lower() in {"connected", "active", "ok"}:
        return "Connected"
    return "Connection status unknown"


def _last_successful_sync_label(synced_at: datetime | None) -> str | None:
    if synced_at is None:
        return None
    return f"Last successful sync {synced_at.astimezone(UTC):%Y-%m-%d %H:%M UTC}"


def _broker_snapshot_status(
    account: BrokerAccount,
    connection: BrokerConnection,
    *,
    has_successful_sync: bool = False,
    preserve_canonical_sync_freshness: bool = False,
) -> str:
    status = account.data_freshness_status.strip().lower()
    if status == "unknown" and has_successful_sync:
        return "manual_review"
    allowed_statuses = DATA_FRESHNESS_STATUSES if preserve_canonical_sync_freshness else _BROKER_FRESHNESS_STATUS_READ_VALUES
    if status in allowed_statuses:
        return status
    connection_statuses = {
        connection.connection_status.strip().lower(),
        connection.sync_status.strip().lower(),
        connection.data_freshness_status.strip().lower(),
    }
    if connection_statuses & {"error", "failed", "reauth_required", "disabled"}:
        return "unavailable"
    return "unknown"


def _broker_snapshot_display_label(status: str) -> str:
    labels = {
        "fresh": "Broker snapshot available",
        "manual_review": "Broker snapshot synced; review freshness",
        "stale": "Broker snapshot is stale",
        "unknown": "Broker snapshot freshness unknown",
        "unavailable": "Broker snapshot unavailable",
    }
    return labels.get(status, "Broker snapshot freshness unknown")


def _private_value_labels(metrics: _NormalizedAccountMetrics) -> dict[str, str]:
    stock_value = metrics.stock_etf_market_value
    option_value = metrics.options_market_value
    cash_total = metrics.cash_total
    collateral = metrics.reserved_collateral_cash
    total_value = None
    if cash_total is not None and stock_value is not None and option_value is not None:
        total_value = cash_total + stock_value + option_value

    if total_value is None and cash_total is None and stock_value is None and option_value is None and collateral is None:
        return {
            "privacy_display_mode": "amounts_hidden",
            "caveat_code": "amounts_hidden",
            "total_value_label": "Total value hidden",
            "cash_label": "Cash amount hidden",
            "stock_etf_exposure_label": "Stock/ETF exposure hidden",
            "options_exposure_label": "Options exposure hidden",
            "collateral_usage_label": "Collateral usage hidden",
        }

    return {
        "privacy_display_mode": "amounts_visible",
        "caveat_code": "amounts_visible",
        "total_value_label": _amount_or_hidden("Total value", total_value),
        "cash_label": _amount_or_hidden("Cash", cash_total),
        "stock_etf_exposure_label": _amount_or_hidden("Stock/ETF exposure", stock_value),
        "options_exposure_label": _amount_or_hidden("Options exposure", option_value),
        "collateral_usage_label": _amount_or_hidden("Collateral usage", collateral),
    }


def _account_overview_value_labels(metrics: _NormalizedAccountMetrics) -> dict[str, str]:
    """Return V1 overview labels without mirroring portfolio value/exposure amounts."""

    labels = _private_value_labels(metrics)
    if labels["privacy_display_mode"] == "amounts_hidden":
        return labels
    return {
        "privacy_display_mode": "amounts_visible",
        "caveat_code": "some_amounts_hidden",
        "total_value_label": "Total value hidden in overview",
        "cash_label": labels["cash_label"],
        "stock_etf_exposure_label": "Stock/ETF exposure shown as count only",
        "options_exposure_label": "Options exposure shown as count only",
        "collateral_usage_label": "Collateral usage not fully modeled",
    }


def _amount_or_hidden(label: str, value: Decimal | None) -> str:
    if value is None:
        return f"{label} hidden"
    return f"{label} {_format_money(value)}"


def _amount_or_none(label: str, value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{label} {_format_money(value)}"


def _amount_value_or_hidden(value: Decimal | None) -> str:
    if value is None:
        return "Hidden"
    return _format_money(value)


def _amount_value_or_none(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _format_money(value)


def _option_position_market_value(position: OptionPosition, contract: OptionContract) -> Decimal | None:
    quantity = _optional_decimal(position.quantity)
    multiplier = _optional_decimal(contract.multiplier) or Decimal("100")
    price = _optional_decimal(position.market_price)
    if quantity is not None and price is not None:
        value = abs(quantity) * abs(price) * multiplier
        if _is_short_option_position(position):
            value = -value
        return value
    return _optional_decimal(position.market_value)


def _option_cost_basis(position: OptionPosition, contract: OptionContract) -> Decimal | None:
    quantity = _optional_decimal(position.quantity)
    average_price = _optional_decimal(position.average_price)
    if quantity is None or average_price is None:
        return None
    if str(position.source or "").strip().lower() == "snaptrade":
        return abs(quantity) * average_price
    multiplier = _optional_decimal(contract.multiplier) or Decimal("100")
    return abs(quantity) * average_price * multiplier


def _option_average_cost_display_value(position: OptionPosition, contract: OptionContract) -> Decimal | None:
    average_price = _optional_decimal(position.average_price)
    if average_price is None:
        return None
    if str(position.source or "").strip().lower() == "snaptrade":
        multiplier = _optional_decimal(contract.multiplier)
        if multiplier is None or multiplier == 0:
            return None
        return average_price / multiplier
    return average_price


def _option_lot_average_cost_display_value(
    position: OptionPosition,
    contract: OptionContract,
    purchase_price: Decimal | None,
) -> Decimal | None:
    if purchase_price is None:
        return None
    if str(position.source or "").strip().lower() == "snaptrade":
        multiplier = _optional_decimal(contract.multiplier)
        if multiplier is None or multiplier == 0:
            return None
        return purchase_price / multiplier
    return purchase_price


def _option_lot_cost_basis(
    position: OptionPosition,
    contract: OptionContract,
    quantity: Decimal | None,
    purchase_price: Decimal | None,
    cost_basis_value: object,
) -> Decimal | None:
    cost_basis = _safe_decimal_from_lot(cost_basis_value)
    if cost_basis is not None:
        return cost_basis
    if quantity is None or purchase_price is None:
        return None
    if str(position.source or "").strip().lower() == "snaptrade":
        return abs(quantity) * purchase_price
    multiplier = _optional_decimal(contract.multiplier) or Decimal("100")
    return abs(quantity) * purchase_price * multiplier


def _valuation_source_label(position: object) -> str:
    source = str(getattr(position, "source", "") or "").strip().lower()
    freshness = str(getattr(position, "data_freshness_status", "") or "").strip().lower()
    if source == "snaptrade":
        if freshness:
            return f"Broker-reported snapshot ({_freshness_status_label(freshness).lower()})"
        return "Broker-reported snapshot"
    return "Backend-owned normalized snapshot"


def _gain_loss_percent_label(gain_loss: Decimal | None, basis: Decimal | None) -> str | None:
    gain = _optional_decimal(gain_loss)
    base = _optional_decimal(basis)
    if gain is None or base is None or base == 0:
        return None
    return f"{(gain / abs(base) * Decimal('100')):.2f}%"


def _multiplier_label(value: Decimal | None) -> str | None:
    multiplier = _optional_decimal(value)
    if multiplier is None:
        return None
    text = format(multiplier.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text} multiplier"


def _tax_lot_rows(position: StockPosition, *, limit: int = 25) -> tuple[AccountTaxLotDisplayRowRead, ...]:
    lots = position.tax_lots or []
    rows: list[AccountTaxLotDisplayRowRead] = []
    for index, lot in enumerate(lots[:limit]):
        quantity = _safe_decimal_from_lot(lot.get("quantity"))
        purchase_price = _safe_decimal_from_lot(lot.get("purchase_price"))
        cost_basis = _safe_decimal_from_lot(lot.get("cost_basis"))
        current_value = _safe_decimal_from_lot(lot.get("current_value"))
        gain_loss = _tax_lot_gain_loss(current_value, cost_basis)
        acquired_date = _tax_lot_acquired_date(lot.get("acquired_date"))
        read = AccountTaxLotDisplayRowRead(
            lot_reference=_opaque_lot_reference((position.id, index)),
            acquired_date_label=acquired_date.isoformat() if acquired_date is not None else None,
            term_label=_tax_lot_term_label(acquired_date, position.as_of.date() if position.as_of else None),
            quantity_label=_quantity_label(quantity, singular="share", plural="shares") if quantity is not None else None,
            purchase_price_label=_amount_value_or_none(purchase_price),
            average_cost_label=_amount_value_or_none(purchase_price),
            cost_basis_label=_amount_value_or_none(cost_basis),
            current_value_label=_amount_value_or_none(current_value),
            total_gain_loss_label=_amount_value_or_none(gain_loss),
            gain_loss_percent_label=_gain_loss_percent_label(gain_loss, cost_basis),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        rows.append(read)
    return tuple(rows)


def _tax_lot_pagination(position: StockPosition, *, limit: int = 25) -> AccountTaxLotPaginationRead | None:
    lots = position.tax_lots or []
    if not lots:
        return None
    read = AccountTaxLotPaginationRead(
        total_count=len(lots),
        displayed_count=min(len(lots), limit),
        has_more=len(lots) > limit,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _option_tax_lot_rows(
    position: OptionPosition,
    contract: OptionContract,
    *,
    limit: int = 25,
) -> tuple[AccountTaxLotDisplayRowRead, ...]:
    lots = position.tax_lots or []
    rows: list[AccountTaxLotDisplayRowRead] = []
    for index, lot in enumerate(lots[:limit]):
        quantity = _safe_decimal_from_lot(lot.get("quantity"))
        purchase_price = _safe_decimal_from_lot(lot.get("purchase_price"))
        average_cost = _option_lot_average_cost_display_value(position, contract, purchase_price)
        cost_basis = _option_lot_cost_basis(position, contract, quantity, purchase_price, lot.get("cost_basis"))
        current_value = _safe_decimal_from_lot(lot.get("current_value"))
        gain_loss = _tax_lot_gain_loss(current_value, cost_basis)
        acquired_date = _tax_lot_acquired_date(lot.get("acquired_date"))
        read = AccountTaxLotDisplayRowRead(
            lot_reference=_opaque_lot_reference((position.id, index)),
            acquired_date_label=acquired_date.isoformat() if acquired_date is not None else None,
            term_label=_tax_lot_term_label(acquired_date, position.as_of.date() if position.as_of else None),
            quantity_label=_quantity_label(abs(quantity), singular="contract", plural="contracts") if quantity is not None else None,
            purchase_price_label=_amount_value_or_none(average_cost),
            average_cost_label=_amount_value_or_none(average_cost),
            cost_basis_label=_amount_value_or_none(cost_basis),
            current_value_label=_amount_value_or_none(current_value),
            total_gain_loss_label=_amount_value_or_none(gain_loss),
            gain_loss_percent_label=_gain_loss_percent_label(gain_loss, cost_basis),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        rows.append(read)
    return tuple(rows)


def _option_tax_lot_pagination(position: OptionPosition, *, limit: int = 25) -> AccountTaxLotPaginationRead | None:
    lots = position.tax_lots or []
    if not lots:
        return None
    read = AccountTaxLotPaginationRead(
        total_count=len(lots),
        displayed_count=min(len(lots), limit),
        has_more=len(lots) > limit,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _tax_lot_gain_loss(current_value: Decimal | None, cost_basis: Decimal | None) -> Decimal | None:
    if current_value is None or cost_basis is None:
        return None
    return current_value - cost_basis


def _tax_lot_acquired_date(value: object) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _tax_lot_term_label(acquired_date: date | None, as_of_date: date | None) -> str:
    if acquired_date is None or as_of_date is None:
        return "unknown"
    return "long" if (as_of_date - acquired_date).days > 365 else "short"


def _safe_decimal_from_lot(value: object) -> Decimal | None:
    try:
        return _optional_decimal(value)
    except ValueError:
        return None


def _is_short_option_position(position: OptionPosition) -> bool:
    side = (position.position_side or "").strip().lower()
    quantity = _optional_decimal(position.quantity)
    return side == "short" or (quantity is not None and quantity < 0)


def _format_money(value: Decimal) -> str:
    return f"${Decimal(value):,.2f}"


def _quantity_label(value: Decimal, *, singular: str, plural: str) -> str:
    quantity = Decimal(value)
    normalized = quantity.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    unit = singular if abs(quantity) == Decimal("1") else plural
    return f"{text} {unit}"


def _asset_class_label(asset_type: str) -> str:
    normalized = asset_type.strip().lower()
    labels = {
        "stock": "Stock",
        "equity": "Stock",
        "etf": "ETF",
        "fund": "Fund",
        "mutual_fund": "Fund",
        "adr": "ADR",
    }
    return labels.get(normalized, "Security")


def _freshness_status_label(status: str) -> str:
    normalized = status.strip().lower()
    labels = {
        "fresh": "Fresh",
        "cached": "Cached",
        "stale": "Stale",
        "manual_review": "Needs review",
        "unknown": "Freshness unknown",
        "unavailable": "Freshness unavailable",
    }
    return labels.get(normalized, "Freshness unknown")


def _as_of_label(value: datetime | None) -> str | None:
    if value is None:
        return None
    return f"As of {value.astimezone(UTC):%Y-%m-%d %H:%M UTC}"


def _option_contract_label(contract: OptionContract) -> str:
    return (
        f"{contract.underlying_symbol.strip().upper()} "
        f"{contract.expiration_date.isoformat()} "
        f"{_strike_label(contract.strike)} "
        f"{_option_type_label(contract.option_type)}"
    )


def _option_type_label(option_type: str) -> str:
    normalized = option_type.strip().lower()
    if normalized == "call":
        return "Call"
    if normalized == "put":
        return "Put"
    return "Option"


def _strike_label(value: Decimal) -> str:
    return f"Strike {_format_money(Decimal(value))}"


def _position_side_label(position_side: str) -> str:
    normalized = position_side.strip().lower()
    if normalized == "short":
        return "Short"
    if normalized == "long":
        return "Long"
    return "Position side unknown"


def _account_display_label(
    *,
    broker_connection: BrokerConnection,
    broker_account: BrokerAccount,
    fallback_index: int,
    existing_labels: tuple[str, ...],
) -> str:
    nickname = (broker_account.user_nickname or "").strip()
    if nickname:
        label = nickname
    else:
        broker_label = _broker_display_label(broker_connection.broker_name)
        kind_label = _short_account_kind_label(broker_account.account_type)
        base_label = (
            f"{broker_label} {kind_label}"
            if broker_label != "Connected broker"
            else f"Connected broker {kind_label}"
        )
        label = base_label.strip()
    if not label:
        label = f"Connected account {fallback_index}"
    if label not in existing_labels:
        return label
    suffix = 2
    while f"{label} {suffix}" in existing_labels:
        suffix += 1
    return f"{label} {suffix}"


def _broker_display_label(broker_name: str) -> str:
    normalized = broker_name.strip().lower()
    if "fidelity" in normalized:
        return "Fidelity"
    if "robinhood" in normalized:
        return "Robinhood"
    if "webull" in normalized:
        return "Webull"
    if "schwab" in normalized:
        return "Schwab"
    if "etrade" in normalized or "e-trade" in normalized:
        return "E*TRADE"
    if "interactive" in normalized:
        return "Interactive Brokers"
    return "Connected broker"


def _short_account_kind_label(account_type: str) -> str:
    normalized = account_type.strip().lower()
    if "ira" in normalized or "retirement" in normalized:
        return "retirement"
    if "margin" in normalized:
        return "margin"
    if "tax" in normalized or "individual" in normalized:
        return "taxable"
    return "brokerage"


def _account_kind_label(account_type: str) -> str:
    normalized = account_type.strip().lower()
    if "ira" in normalized or "retirement" in normalized:
        return "Retirement brokerage"
    if "tax" in normalized or "individual" in normalized:
        return "Taxable brokerage"
    if "margin" in normalized:
        return "Margin brokerage"
    return "Brokerage account"


def _opaque_account_reference(value: object) -> str:
    return f"acctref_{_opaque_digest(value)}"


def _opaque_scope_reference(value: object) -> str:
    return f"scope_{_opaque_digest(value)}"


def _opaque_account_details_reference(value: object) -> str:
    return f"ad_{_opaque_digest(value)}"


def _opaque_row_reference(value: object) -> str:
    return f"row_{_opaque_digest(value)}"


def _opaque_lot_reference(value: object) -> str:
    return f"lotref_{_opaque_digest(value)}"


def _opaque_digest(value: object) -> str:
    return hashlib.blake2s(str(value).encode("utf-8"), digest_size=10).hexdigest()


def _portfolio_scope_read(
    *,
    scope_reference: str,
    scope_mode: str,
    display_label: str,
    selection_mode: str | None,
    context_reference: str | None,
    included_account_labels: tuple[str, ...],
    excluded_account_labels: tuple[str, ...],
    account_level_feasibility_evaluated: bool,
    account_level_feasibility_label: str,
    caveat_codes: tuple[str, ...],
) -> PortfolioScopeRead:
    read = PortfolioScopeRead(
        scope_reference=scope_reference,
        scope_mode=scope_mode,
        display_label=display_label,
        selection_mode=selection_mode,
        context_reference=context_reference,
        included_account_labels=included_account_labels,
        excluded_account_labels=excluded_account_labels,
        account_level_feasibility_evaluated=account_level_feasibility_evaluated,
        account_level_feasibility_label=account_level_feasibility_label,
        caveat_codes=caveat_codes,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _report_scope_metadata_for_workspace(
    *,
    portfolio_context_summary: PortfolioContextSummaryRead | None,
    review_account_selection: ReviewAccountSelectionRequest | None = None,
    db: Session | None = None,
    current_user_id: UUID | None = None,
    account_snapshot_unavailable: bool = False,
) -> ReportScopeMetadataRead:
    if portfolio_context_summary is None:
        scope = _portfolio_scope_read(
            scope_reference=_DEMO_SCOPE_UNAVAILABLE_REFERENCE,
            scope_mode="unavailable",
            display_label="No portfolio context scope available",
            selection_mode=None,
            context_reference=None,
            included_account_labels=(),
            excluded_account_labels=(),
            account_level_feasibility_evaluated=False,
            account_level_feasibility_label="Account-level feasibility not evaluated",
            caveat_codes=("portfolio_scope_unavailable",),
        )
        read = ReportScopeMetadataRead(
            review_account=None,
            portfolio_context_scope=scope,
            scope_summary_label="No portfolio context was selected for this review.",
            account_level_feasibility_evaluated=False,
            scope_caveat_codes=("portfolio_scope_unavailable",),
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        return read

    review_account = _review_account_for_workspace_selection(
        review_account_selection,
        db=db,
        current_user_id=current_user_id,
    )
    if account_snapshot_unavailable:
        scope_caveat_codes = (
            "selected_context_scope",
            "account_snapshot_unavailable",
            "account_level_feasibility_not_evaluated",
            *(() if review_account is not None else ("review_account_unresolved",)),
        )
        scope = _portfolio_scope_read(
            scope_reference=_opaque_scope_reference(("review_snapshot_unavailable", portfolio_context_summary.context_reference)),
            scope_mode="unavailable",
            display_label="Account snapshot unavailable",
            selection_mode=portfolio_context_summary.selection_mode,
            context_reference=portfolio_context_summary.context_reference,
            included_account_labels=(),
            excluded_account_labels=(),
            account_level_feasibility_evaluated=False,
            account_level_feasibility_label="Account-level feasibility not evaluated",
            caveat_codes=scope_caveat_codes,
        )
        read = ReportScopeMetadataRead(
            review_account=review_account,
            portfolio_context_scope=scope,
            scope_summary_label=(
                "Review account selected · Context scope: Account snapshot unavailable."
                if review_account is not None
                else "Review account unresolved · Context scope: Account snapshot unavailable."
            ),
            account_level_feasibility_evaluated=False,
            scope_caveat_codes=scope_caveat_codes,
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        return read

    is_account_snapshot_scope = portfolio_context_summary.context_source == "account_snapshot"
    if is_account_snapshot_scope:
        if review_account is not None:
            review_account = review_account.model_copy(
                update={
                    "is_included_in_portfolio_scope": True,
                }
            )
        account_level_feasibility_label = "Account-level feasibility not evaluated"
        scope_summary_label = "Review account selected · Context scope: Selected account snapshot."
        scope_caveat_codes = (
            "selected_context_scope",
            "account_level_feasibility_not_evaluated",
            "cash_collateral_policy_not_reviewed",
            "cash_collateral_not_fully_modeled",
        )
        scope = _portfolio_scope_read(
            scope_reference=_opaque_scope_reference(("review_snapshot", portfolio_context_summary.context_reference)),
            scope_mode="single_account",
            display_label="Selected account snapshot",
            selection_mode=portfolio_context_summary.selection_mode,
            context_reference=portfolio_context_summary.context_reference,
            included_account_labels=("Selected review account",) if review_account is not None else (),
            excluded_account_labels=(),
            account_level_feasibility_evaluated=False,
            account_level_feasibility_label=account_level_feasibility_label,
            caveat_codes=scope_caveat_codes,
        )
        read = ReportScopeMetadataRead(
            review_account=review_account,
            portfolio_context_scope=scope,
            scope_summary_label=scope_summary_label,
            account_level_feasibility_evaluated=False,
            scope_caveat_codes=scope_caveat_codes,
        )
        validate_trade_review_workspace_payload(read.model_dump(mode="python"))
        return read

    account_level_feasibility_evaluated = (
        review_account is not None and review_account.is_account_level_feasibility_source
    )
    if account_level_feasibility_evaluated:
        account_level_feasibility_label = "Selected review account evaluated for account-level feasibility"
        scope_summary_label = "Review account selected · Context scope: Selected demo portfolio context."
        scope_caveat_codes = (
            "selected_context_scope",
            *(() if review_account.is_included_in_portfolio_scope else ("review_account_scope_membership_unknown",)),
        )
    elif (
        review_account_selection is not None
        and review_account_selection.mode == "selected_account"
        and review_account_selection.account_reference is not None
        and review_account is not None
    ):
        account_level_feasibility_label = "Account-level feasibility not evaluated"
        scope_summary_label = "Review account selected · Context scope: Selected demo portfolio context."
        scope_caveat_codes = (
            "selected_context_scope",
            "account_level_feasibility_not_evaluated",
            "current_position_truth_unstable",
            "buying_power_display_only",
            "cash_collateral_policy_not_reviewed",
            "cash_collateral_not_fully_modeled",
            *(() if review_account.is_included_in_portfolio_scope else ("review_account_scope_membership_unknown",)),
        )
    elif (
        review_account_selection is not None
        and review_account_selection.mode == "selected_account"
        and review_account_selection.account_reference is not None
    ):
        account_level_feasibility_label = "Account-level feasibility not evaluated"
        scope_summary_label = "Review account unresolved · Context scope: Selected demo portfolio context."
        scope_caveat_codes = ("selected_context_scope", "review_account_unresolved")
    else:
        account_level_feasibility_label = "Account-level feasibility not evaluated"
        scope_summary_label = "Review account not selected · Context scope: Selected demo portfolio context."
        scope_caveat_codes = ("selected_context_scope", "review_account_not_selected")

    included_account_labels = (
        ("Selected review account",)
        if review_account is not None and review_account.is_included_in_portfolio_scope
        else ()
    )
    excluded_account_labels = ("Other demo account",) if _is_synthetic_review_account(review_account) else ()
    scope = _portfolio_scope_read(
        scope_reference=_DEMO_SCOPE_SELECTED_REFERENCE,
        scope_mode="selected_context",
        display_label="Selected demo portfolio context",
        selection_mode=portfolio_context_summary.selection_mode,
        context_reference=portfolio_context_summary.context_reference,
        included_account_labels=included_account_labels,
        excluded_account_labels=excluded_account_labels,
        account_level_feasibility_evaluated=account_level_feasibility_evaluated,
        account_level_feasibility_label=account_level_feasibility_label,
        caveat_codes=scope_caveat_codes,
    )
    read = ReportScopeMetadataRead(
        review_account=review_account,
        portfolio_context_scope=scope,
        scope_summary_label=scope_summary_label,
        account_level_feasibility_evaluated=account_level_feasibility_evaluated,
        scope_caveat_codes=scope_caveat_codes,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _review_account_for_workspace_selection(
    review_account_selection: ReviewAccountSelectionRequest | None,
    *,
    db: Session | None = None,
    current_user_id: UUID | None = None,
) -> ReviewAccountRead | None:
    if review_account_selection is None or review_account_selection.mode == "unselected":
        return None
    if db is not None and current_user_id is not None:
        rows = _broker_account_detail_rows_for_user(db, user_id=current_user_id)
        if rows:
            return _review_account_for_broker_rows(
                review_account_selection=review_account_selection,
                rows=rows,
            )
        return None
    if review_account_selection.account_reference != _DEMO_REVIEW_ACCOUNT_REFERENCE:
        return None
    return _review_account_read(
        account_reference=_DEMO_REVIEW_ACCOUNT_REFERENCE,
        display_label="Primary demo account",
        account_kind_label="Taxable brokerage",
        is_review_account=True,
        is_included_in_portfolio_scope=True,
        is_account_level_feasibility_source=True,
    )


def _review_account_for_broker_rows(
    *,
    review_account_selection: ReviewAccountSelectionRequest,
    rows: tuple[_BrokerAccountDetailsRow, ...],
) -> ReviewAccountRead | None:
    if review_account_selection.mode != "selected_account" or review_account_selection.account_reference is None:
        return None

    account_labels: tuple[str, ...] = ()
    for index, row in enumerate(rows, start=1):
        account_display_label = _account_display_label(
            broker_connection=row.broker_connection,
            broker_account=row.broker_account,
            fallback_index=index,
            existing_labels=account_labels,
        )
        account_reference = _opaque_account_reference(row.broker_account.id)
        if account_reference == review_account_selection.account_reference:
            return _review_account_read(
                account_reference=account_reference,
                display_label=account_display_label,
                account_kind_label=_account_kind_label(row.broker_account.account_type),
                is_review_account=True,
                is_included_in_portfolio_scope=False,
                is_account_level_feasibility_source=False,
            )
        account_labels += (account_display_label,)
    return None


def _is_synthetic_review_account(review_account: ReviewAccountRead | None) -> bool:
    return review_account is not None and review_account.account_reference == _DEMO_REVIEW_ACCOUNT_REFERENCE


def _account_detail_account_read(
    *,
    account_reference: str,
    display_label: str,
    account_kind_label: str,
    source_kind: str,
    stock_position_count: int,
    option_position_count: int,
    cash_state: str,
    broker_status: str,
    broker_display_label: str,
    broker_reason_codes: tuple[str, ...],
    broker_is_blocking: bool,
    market_status: str | None,
    market_display_label: str | None,
    market_reason_codes: tuple[str, ...],
    market_is_blocking: bool,
    scope_roles: tuple[str, ...],
    account_level_feasibility_evaluated: bool,
    caveat_codes: tuple[str, ...],
    source_label: str = "Synthetic demo",
    connection_status_label: str = "Demo connection not active",
    last_successful_sync_label: str | None = None,
    privacy_display_mode: str = "amounts_hidden",
    broker_as_of_label: str = "Demo broker snapshot needs review",
    market_as_of_label: str = "Demo market quotes require review",
    total_value_label: str = "Total value hidden · demo not connected",
    cash_label: str = "Cash amount hidden · demo not connected",
    stock_etf_exposure_label: str = "Stock/ETF exposure hidden · demo not connected",
    options_exposure_label: str = "Options exposure hidden · demo not connected",
    collateral_usage_label: str = "Collateral usage hidden · demo not connected",
) -> AccountDetailAccountRead:
    market_quote_freshness = None
    if market_status is not None:
        market_quote_freshness = PortfolioContextFreshnessRead(
            freshness_scope="market_quote",
            status=market_status,
            as_of_label=market_as_of_label,
            display_label=market_display_label or "Market quote freshness unavailable",
            reason_codes=market_reason_codes,
            is_blocking=market_is_blocking,
        )

    read = AccountDetailAccountRead(
        account_reference=account_reference,
        display_label=display_label,
        account_kind_label=account_kind_label,
        source_kind=source_kind,
        source_label=source_label,
        connection_status_label=connection_status_label,
        last_successful_sync_label=last_successful_sync_label,
        privacy_display_mode=privacy_display_mode,
        broker_snapshot_freshness=PortfolioContextFreshnessRead(
            freshness_scope="broker_snapshot",
            status=broker_status,
            as_of_label=broker_as_of_label,
            display_label=broker_display_label,
            reason_codes=broker_reason_codes,
            is_blocking=broker_is_blocking,
        ),
        market_quote_freshness=market_quote_freshness,
        portfolio_shape=PortfolioContextShapeRead(
            stock_position_count=stock_position_count,
            option_position_count=option_position_count,
        ),
        cash_state=cash_state,
        cash_state_label=_cash_state_label(cash_state),
        total_value_label=total_value_label,
        cash_label=cash_label,
        stock_etf_exposure_label=stock_etf_exposure_label,
        options_exposure_label=options_exposure_label,
        collateral_usage_label=collateral_usage_label,
        scope_roles=scope_roles,
        account_level_feasibility_evaluated=account_level_feasibility_evaluated,
        readiness_caveats=_account_readiness_caveats(caveat_codes),
        caveat_codes=caveat_codes,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _portfolio_context_catalog(generated_at: datetime) -> dict[str, PortfolioContextRead]:
    return {
        _LATEST_CONTEXT_REFERENCE: _portfolio_context_read(
            context_reference=_LATEST_CONTEXT_REFERENCE,
            context_label="Latest demo portfolio context",
            source_kind="manual",
            stock_position_count=2,
            option_position_count=1,
            cash_state="available",
            broker_status="fresh",
            broker_as_of_label="Demo manual snapshot",
            broker_display_label="Broker snapshot requires manual review",
            broker_reason_codes=("broker_snapshot_manual_review",),
            broker_is_blocking=False,
            market_status="manual_review",
            market_as_of_label="Demo market quotes require review",
            market_display_label="Market quote freshness requires review",
            market_reason_codes=("market_quote_manual_review",),
            market_is_blocking=False,
            actionability_status="manual_confirmation_required",
            overall_review_mode="manual_confirmation_required",
            actionability_display_label="Manual confirmation required",
            actionability_is_blocking=False,
            available_flows=_all_supported_flows(),
            caveat_codes=("demo_context", "market_quote_manual_review"),
        ),
        _STALE_CONTEXT_REFERENCE: _portfolio_context_read(
            context_reference=_STALE_CONTEXT_REFERENCE,
            context_label="Stale demo broker snapshot context",
            source_kind="broker_snapshot",
            stock_position_count=2,
            option_position_count=1,
            cash_state="available",
            broker_status="stale",
            broker_as_of_label="Demo broker snapshot is stale",
            broker_display_label="Broker snapshot is stale",
            broker_reason_codes=("broker_snapshot_stale",),
            broker_is_blocking=True,
            market_status="manual_review",
            market_as_of_label="Demo market quotes require review",
            market_display_label="Market quote freshness requires review",
            market_reason_codes=("market_quote_manual_review",),
            market_is_blocking=False,
            actionability_status="blocked_stale_broker_snapshot",
            overall_review_mode="blocked",
            actionability_display_label="Blocked by stale broker snapshot",
            actionability_is_blocking=True,
            available_flows=_all_supported_flows(),
            caveat_codes=("demo_context", "broker_snapshot_stale", "market_quote_manual_review"),
        ),
        _MISSING_MARKET_CONTEXT_REFERENCE: _portfolio_context_read(
            context_reference=_MISSING_MARKET_CONTEXT_REFERENCE,
            context_label="Demo context with unavailable market data",
            source_kind="csv",
            stock_position_count=2,
            option_position_count=1,
            cash_state="available",
            broker_status="fresh",
            broker_as_of_label="Demo imported snapshot",
            broker_display_label="Broker snapshot available for demo",
            broker_reason_codes=("broker_snapshot_demo",),
            broker_is_blocking=False,
            market_status=None,
            market_as_of_label=None,
            market_display_label=None,
            market_reason_codes=(),
            market_is_blocking=True,
            actionability_status="blocked_unknown_freshness",
            overall_review_mode="blocked",
            actionability_display_label="Blocked by unavailable market data",
            actionability_is_blocking=True,
            available_flows=("stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"),
            caveat_codes=("demo_context", "market_data_unavailable"),
        ),
    }


def _empty_portfolio_context_read(generated_at: datetime) -> PortfolioContextRead:
    return _portfolio_context_read(
        context_reference=_NO_CONTEXT_REFERENCE,
        context_label="No portfolio context available",
        source_kind="synthetic_demo",
        stock_position_count=0,
        option_position_count=0,
        cash_state="unavailable",
        broker_status="unknown",
        broker_as_of_label="No demo broker snapshot",
        broker_display_label="Broker snapshot unavailable",
        broker_reason_codes=("broker_snapshot_unavailable",),
        broker_is_blocking=True,
        market_status=None,
        market_as_of_label=None,
        market_display_label=None,
        market_reason_codes=(),
        market_is_blocking=True,
        actionability_status="blocked_unknown_freshness",
        overall_review_mode="blocked",
        actionability_display_label="Blocked until portfolio context is available",
        actionability_is_blocking=True,
        available_flows=(),
        caveat_codes=("context_unavailable", "market_data_unavailable"),
    )


def _portfolio_context_read(
    *,
    context_reference: str,
    context_label: str,
    source_kind: str,
    stock_position_count: int,
    option_position_count: int,
    cash_state: str,
    broker_status: str,
    broker_as_of_label: str | None,
    broker_display_label: str,
    broker_reason_codes: tuple[str, ...],
    broker_is_blocking: bool,
    market_status: str | None,
    market_as_of_label: str | None,
    market_display_label: str | None,
    market_reason_codes: tuple[str, ...],
    market_is_blocking: bool,
    actionability_status: str,
    overall_review_mode: str,
    actionability_display_label: str,
    actionability_is_blocking: bool,
    available_flows: tuple[SupportedTradeReviewFlow, ...],
    caveat_codes: tuple[str, ...],
) -> PortfolioContextRead:
    market_quote_freshness = None
    if market_status is not None:
        market_quote_freshness = PortfolioContextFreshnessRead(
            freshness_scope="market_quote",
            status=market_status,
            as_of_label=market_as_of_label,
            display_label=market_display_label or "Market quote freshness unavailable",
            reason_codes=market_reason_codes,
            is_blocking=market_is_blocking,
        )
    read = PortfolioContextRead(
        context_reference=context_reference,
        context_label=context_label,
        source_kind=source_kind,
        portfolio_shape=PortfolioContextShapeRead(
            stock_position_count=stock_position_count,
            option_position_count=option_position_count,
        ),
        cash_state=cash_state,
        cash_state_label=_cash_state_label(cash_state),
        broker_snapshot_freshness=PortfolioContextFreshnessRead(
            freshness_scope="broker_snapshot",
            status=broker_status,
            as_of_label=broker_as_of_label,
            display_label=broker_display_label,
            reason_codes=broker_reason_codes,
            is_blocking=broker_is_blocking,
        ),
        market_quote_freshness=market_quote_freshness,
        market_data_unavailable=market_quote_freshness is None,
        actionability_preview=PortfolioContextActionabilityPreviewRead(
            review_actionability_status=actionability_status,
            overall_review_mode=overall_review_mode,
            display_label=actionability_display_label,
            is_blocking=actionability_is_blocking,
        ),
        available_flows=available_flows,
        caveat_codes=caveat_codes,
    )
    validate_trade_review_workspace_payload(read.model_dump(mode="python"))
    return read


def _all_supported_flows() -> tuple[SupportedTradeReviewFlow, ...]:
    return (
        "stock_buy",
        "stock_sell_trim",
        "etf_buy",
        "etf_sell_trim",
        "covered_call",
        "cash_secured_put",
    )


def _cash_state_label(cash_state: str) -> str:
    labels = {
        "available": "Cash state available",
        "unavailable": "Cash state unavailable",
        "not_exposed": "Cash state not exposed",
    }
    return labels[cash_state]


def build_trade_review_workspace_portfolio_preview(
    payload: TradeReviewPortfolioPreviewRequest,
    *,
    generated_at: datetime | None = None,
    db: Session | None = None,
    current_user_id: UUID | None = None,
    derived_exposure_sections_callback: Callable[[tuple[Any, ...]], None] | None = None,
    symbol_service: SymbolService | None = None,
) -> TradeReviewWorkspaceRead:
    """Build a portfolio-backed preview from server-owned sanitized context."""

    generated = generated_at or datetime.now(UTC)
    resolved = _resolve_portfolio_context(
        payload.portfolio_context_selection,
        generated_at=generated,
        review_account_selection=payload.review_account_selection,
        db=db,
        current_user_id=current_user_id,
    )
    actionability = evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=resolved.broker_snapshot,
            market_quotes=resolved.market_quotes,
            user_confirmation=None,
        ),
        evaluated_at=generated,
    )
    preview_user_id = getattr(resolved.context, "user_id", None)
    preview_account_id = getattr(resolved.context, "account_id", None)
    resolved_identity = _resolve_preview_instrument_identity(payload, symbol_service=symbol_service)
    reconciled_payload = payload.model_copy(update={"supported_flow": resolved_identity.supported_flow})
    intent = _preview_intent(
        reconciled_payload,
        generated_at=generated,
        # A lossy selected-account context intentionally carries no account
        # identity. Its transient intent ids are redacted before saving.
        user_id=preview_user_id or uuid4(),
        account_id=preview_account_id or uuid4(),
        broker_portfolio_status=resolved.broker_snapshot.freshness_status,
        market_quote_status=resolved.market_quotes.freshness_status,
        intent_prefix="portfolio-preview",
    )
    market_snapshot = TradeReviewMarketSnapshot(
        report_market_snapshot=None,
        missing_symbols=()
        if actionability.market_quotes.actionability_status == "actionable_snapshot"
        else (_intent_symbol(intent),),
        manual_review_required=actionability.market_quotes.actionability_status != "actionable_snapshot",
    )
    validation = TradeIntentValidator().validate(intent, today=generated.date())
    payoff = PayoffScenarioEngine().evaluate(intent)
    impact = PortfolioImpactEngine().calculate(
        intent=intent,
        portfolio_context=resolved.context,
        market_snapshot=market_snapshot,
        payoff=payoff,
    )
    derived_exposure_sections: tuple[Any, ...] = ()
    if resolved.account_snapshot_unavailable:
        derived_exposure_sections = unavailable_exposure_evidence_sections(("account_snapshot_unavailable",))
    else:
        try:
            derived_exposure_sections = try_build_exposure_evidence_sections(
                portfolio_context=resolved.context,
                intent=intent,
            )
        except Exception:
            derived_exposure_sections = ()
    if derived_exposure_sections_callback is not None:
        try:
            derived_exposure_sections_callback(derived_exposure_sections)
        except Exception:
            pass
    risk = TradeReviewRiskEngine().evaluate(
        validation=validation,
        portfolio_impact=impact,
        market_snapshot=market_snapshot,
    )
    report = build_trade_review_report(
        intent=intent,
        generated_at=generated,
        validation=validation,
        payoff=payoff,
        portfolio_impact=impact,
        risk=risk,
        market_snapshot=market_snapshot,
    )
    workspace = build_trade_review_workspace_read(
        projection=to_agent_safe_projection(report),
        actionability=actionability,
        review_reference=report.intent_id,
        supported_flow=resolved_identity.supported_flow,
        portfolio_context_summary=resolved.summary,
        scope_metadata=_report_scope_metadata_for_workspace(
            portfolio_context_summary=resolved.summary,
            review_account_selection=payload.review_account_selection,
            db=db,
            current_user_id=current_user_id,
            account_snapshot_unavailable=resolved.account_snapshot_unavailable,
        ),
        instrument_identity=resolved_identity.identity,
        generated_at=generated,
    )
    workspace = _workspace_with_exposure_caveats(workspace, derived_exposure_sections)
    return _workspace_with_instrument_reconciliation_caveat(workspace)


def _intent_summary(
    intent_summary: dict[str, Any],
    *,
    supported_flow: SupportedTradeReviewFlow,
    instrument_identity: InstrumentIdentityRead | None = None,
) -> TradeIntentSummaryRead:
    legs = tuple(_option_leg_summary(leg) for leg in intent_summary.get("legs", ()))
    return TradeIntentSummaryRead(
        intent_id=str(intent_summary["intent_id"]),
        supported_flow=supported_flow,
        asset_class=intent_summary["asset_class"],
        intent_type=str(intent_summary.get("intent_type", supported_flow)),
        status=str(intent_summary.get("status", "ready_for_review")),
        symbol=_optional_text(intent_summary.get("symbol")),
        action=_optional_text(intent_summary.get("action")),
        quantity=_optional_decimal_text(intent_summary.get("quantity")),
        price_assumption=_optional_decimal_text(intent_summary.get("price_assumption")),
        strategy_type=_optional_text(intent_summary.get("strategy_type")),
        underlying_symbol=_optional_text(intent_summary.get("underlying_symbol")),
        legs=legs,
        instrument_identity=instrument_identity or InstrumentIdentityRead(),
    )


def _option_leg_summary(leg: dict[str, Any]) -> WorkspaceOptionLegSummaryRead:
    _reject_forbidden_input(leg, label="option_leg")
    return WorkspaceOptionLegSummaryRead(
        underlying_symbol=str(leg["underlying_symbol"]),
        option_type=leg["option_type"],
        leg_action=str(leg["leg_action"]),
        expiration_date=leg["expiration_date"],
        strike=_decimal_text(leg["strike"]),
        quantity=_decimal_text(leg["quantity"]),
        premium=_optional_decimal_text(leg.get("premium")),
        multiplier=_decimal_text(leg.get("multiplier", "100")),
        occ_symbol=_optional_text(leg.get("occ_symbol")),
        support_status=str(leg.get("support_status", "supported")),
        unsupported_reason=_optional_text(leg.get("unsupported_reason")),
    )


def _portfolio_impact(projection: TradeReviewAgentProjection) -> PortfolioImpactSummaryRead:
    impact = projection.portfolio_impact
    return PortfolioImpactSummaryRead(
        broker_freshness_status=impact.broker_freshness_status,
        market_freshness_status=impact.market_freshness_status,
        market_manual_review_required=impact.market_manual_review_required,
        concentration_symbol=impact.concentration_symbol,
        notes=impact.notes,
    )


def _cash_collateral_impact(summary: TradeIntentSummaryRead) -> CashCollateralImpactRead:
    trade_cash_change: Decimal | None = None
    premium_change = Decimal("0")
    collateral_change = Decimal("0")
    notes: list[str] = ["Estimated cash/collateral fields are derived from the reviewed intent, not raw account balances."]

    if summary.asset_class in {"stock", "etf"}:
        price = _optional_decimal(summary.price_assumption)
        quantity = _optional_decimal(summary.quantity)
        if price is not None and quantity is not None and summary.action is not None:
            gross = price * quantity
            trade_cash_change = -gross if summary.action == "buy" else gross
        notes.append("Projected free cash is intentionally not exposed in the frontend-readiness contract.")
    else:
        for leg in summary.legs:
            premium = _optional_decimal(leg.premium)
            quantity = _optional_decimal(leg.quantity) or Decimal("0")
            multiplier = _optional_decimal(leg.multiplier) or Decimal("100")
            strike = _optional_decimal(leg.strike) or Decimal("0")
            if premium is not None:
                gross_premium = premium * quantity * multiplier
                premium_change += gross_premium if leg.leg_action.startswith("sell") else -gross_premium
            if leg.leg_action == "sell_to_open" and leg.option_type == "put":
                collateral_change += strike * quantity * multiplier
        trade_cash_change = premium_change
        notes.append("Short-put collateral uses generic strike * multiplier * contracts rules.")

    return CashCollateralImpactRead(
        estimated_trade_cash_change=_optional_decimal_text(trade_cash_change),
        estimated_premium_cash_change=_decimal_text(premium_change),
        estimated_collateral_requirement_change=_decimal_text(collateral_change),
        projected_free_cash_state="not_exposed",
        notes=tuple(notes),
    )


def _concentration_allocation_impact(projection: TradeReviewAgentProjection) -> ConcentrationAllocationImpactRead:
    return ConcentrationAllocationImpactRead(
        concentration_symbol=projection.portfolio_impact.concentration_symbol,
        estimated_concentration_value_change=None,
        allocation_drift_status="not_modelled_in_phase_18a",
        notes=(
            "Phase 18A exposes concentration symbol and deterministic risk findings, not raw allocation or account values.",
            *projection.portfolio_impact.notes,
        ),
    )


def _options_exposure(
    summary: TradeIntentSummaryRead,
    projection: TradeReviewAgentProjection,
    *,
    supported_flow: SupportedTradeReviewFlow,
) -> OptionsExposureRead:
    coverage_model = "not_fully_modelled" if supported_flow == "covered_call" else "not_applicable"
    collateral_model = "generic_rule_only" if supported_flow == "cash_secured_put" else "not_applicable"
    notes = ["Share deltas come from deterministic option-leg scenario rules."]
    if coverage_model == "not_fully_modelled":
        notes.append("Covered-call stock coverage is not fully netted in Phase 18A and must be displayed as a caveat.")
    if collateral_model == "generic_rule_only":
        notes.append("Cash-secured-put collateral uses generic requirements and omits broker-specific margin treatment.")
    return OptionsExposureRead(
        underlying_symbol=summary.underlying_symbol,
        assignment_share_delta=_decimal_text(projection.portfolio_impact.assignment_share_delta),
        exercise_share_delta=_decimal_text(projection.portfolio_impact.exercise_share_delta),
        covered_call_coverage_model=coverage_model,
        cash_secured_put_collateral_model=collateral_model,
        notes=tuple(notes),
    )


def _risk_rule_violations(projection: TradeReviewAgentProjection) -> tuple[RiskRuleViolationSummaryRead, ...]:
    return tuple(
        RiskRuleViolationSummaryRead(
            code=violation.code,
            severity=violation.severity,
            message=violation.message,
            source=violation.source,
            metric=violation.metric,
            actual=_optional_value_text(violation.actual),
            policy_label=_policy_label(violation),
        )
        for violation in projection.risk_rule_violations
    )


def _missing_data_warnings(
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
) -> tuple[MissingDataWarningRead, ...]:
    warnings = [
        MissingDataWarningRead(
            code=reason.code,
            scope=reason.scope,
            severity=reason.severity,
            message=reason.message,
        )
        for reason in actionability.reasons
        if reason.severity in {"warning", "blocker"}
    ]
    for symbol in projection.market_snapshot.missing_symbols:
        warnings.append(
            MissingDataWarningRead(
                code="market_symbol_missing",
                scope="market_quote",
                severity="warning",
                message=f"Market data is missing for synthetic symbol {symbol}.",
            )
        )
    for finding in projection.validation.findings:
        if finding.severity in {"warning", "blocker"}:
            warnings.append(
                MissingDataWarningRead(
                    code=f"validation_{finding.code}",
                    scope="review",
                    severity="blocker" if finding.severity == "blocker" else "warning",
                    message=finding.message,
                )
            )
    return tuple(warnings)


def _scenario_payoff_summary(projection: TradeReviewAgentProjection) -> ScenarioPayoffSummaryRead:
    return ScenarioPayoffSummaryRead(
        points=tuple(
            ScenarioPayoffPointRead(
                label=point.label,
                underlying_price=_decimal_text(point.underlying_price),
                net_cash_flow=_decimal_text(point.net_cash_flow),
                scenario_value=_decimal_text(point.scenario_value),
                scenario_pnl=_decimal_text(point.scenario_pnl),
                description=point.description,
            )
            for point in projection.payoff.points
        ),
        max_loss=_optional_decimal_text(projection.payoff.max_loss),
        max_gain=_optional_decimal_text(projection.payoff.max_gain),
        calculation_notes=projection.payoff.calculation_notes,
    )


def _agent_orchestration(result: AgentTeamOrchestrationResult | None) -> AgentOrchestrationSummaryRead | None:
    if result is None:
        return None
    summary = result.summary_snapshot()
    unavailable = {
        stage.stage: stage.unavailable_reason
        for stage in result.stage_outputs
        if stage.unavailable_reason is not None
    }
    return AgentOrchestrationSummaryRead(
        run_reference=result.run_reference,
        workflow_version=result.contract.workflow_version,
        review_actionability_status=result.contract.actionability_status,
        stage_order=tuple(DEFAULT_AGENT_WORKFLOW_STAGES),
        stage_statuses=dict(summary["stage_statuses"]),
        unavailable_stages=unavailable,
        source_agent_names=tuple(summary["source_agent_names"]),
        report_composed=bool(summary["report_composed"]),
    )


def _report_output(output: ReportComposerAgentOutput | None) -> AnalysisOnlyReportOutputRead | None:
    if output is None:
        return None
    return AnalysisOnlyReportOutputRead(
        title=output.title,
        content_markdown=output.markdown,
        deterministic_sections=output.deterministic_sections,
        llm_generated_sections=output.llm_generated_sections,
        source_agent_names=output.source_agent_names,
    )


def _gate_real_broker_position_truth(
    actionability: PortfolioActionabilityDecision,
    *,
    supported_flow: SupportedTradeReviewFlow,
    scope_metadata: ReportScopeMetadataRead | None,
) -> PortfolioActionabilityDecision:
    if not _requires_real_broker_position_truth_gate(supported_flow, scope_metadata):
        return actionability

    reasons = (
        *actionability.reasons,
        ActionabilityReason(
            code="current_position_truth_unstable",
            scope="review",
            severity="warning",
            message=(
                "Real broker position rows are not treated as authoritative current position truth "
                "for this position-dependent review."
            ),
        ),
        ActionabilityReason(
            code="account_level_feasibility_not_evaluated",
            scope="review",
            severity="warning",
            message="Selected review account metadata is resolved, but account-level feasibility is not evaluated.",
        ),
    )
    if supported_flow == "cash_secured_put":
        reasons = (
            *reasons,
            ActionabilityReason(
                code="cash_collateral_policy_not_reviewed",
                scope="review",
                severity="warning",
                message="Short-put collateral review does not rely on broker capacity or collateral fields yet.",
            ),
            ActionabilityReason(
                code="buying_power_display_only",
                scope="review",
                severity="warning",
                message="Broker capacity labels are private display labels only and are not feasibility inputs.",
            ),
            ActionabilityReason(
                code="csp_collateral_unverified",
                scope="review",
                severity="warning",
                message="Short-put collateral remains unverified for the selected account.",
            ),
        )
    if supported_flow == "covered_call":
        reasons = (
            *reasons,
            ActionabilityReason(
                code="covered_call_coverage_unverified",
                scope="review",
                severity="warning",
                message="Covered-call coverage does not rely on broker stock or option rows yet.",
            ),
        )

    if actionability.review_actionability_status == "normal_review":
        return actionability.model_copy(
            update={
                "review_actionability_status": "analysis_only",
                "can_run_deterministic_review": True,
                "can_run_agent_explanation": True,
                "requires_user_confirmation": False,
                "language_tier": "analysis_only",
                "reasons": reasons,
            }
        )
    return actionability.model_copy(update={"reasons": reasons})


def _requires_real_broker_position_truth_gate(
    supported_flow: SupportedTradeReviewFlow,
    scope_metadata: ReportScopeMetadataRead | None,
) -> bool:
    if supported_flow not in _POSITION_DEPENDENT_REAL_BROKER_FLOWS or scope_metadata is None:
        return False
    review_account = scope_metadata.review_account
    if review_account is None or _is_synthetic_review_account(review_account):
        return False
    return True


def _caveats(
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
    supported_flow: SupportedTradeReviewFlow,
    *,
    scope_metadata: ReportScopeMetadataRead | None = None,
) -> tuple[WorkspaceCaveatRead, ...]:
    caveats: list[WorkspaceCaveatRead] = [
        WorkspaceCaveatRead(
            code="review_only_no_execution",
            severity="info",
            applies_to="workspace",
            message="This workspace is review and scenario analysis only; it does not place, route, or manage trades.",
        )
    ]
    if actionability.language_tier != "normal_review":
        caveats.append(
            WorkspaceCaveatRead(
                code="analysis_only_actionability",
                severity="warning",
                applies_to="actionability",
                message="The actionability policy limits this review because broker or market data is not fully actionable.",
            )
        )
    if supported_flow == "covered_call":
        caveats.append(
            WorkspaceCaveatRead(
                code="covered_call_coverage_not_fully_modelled",
                severity="warning",
                applies_to="options_exposure",
                message="Covered-call stock coverage is not fully netted against current holdings in this frontend contract.",
            )
        )
    if supported_flow == "cash_secured_put":
        caveats.append(
        WorkspaceCaveatRead(
            code="cash_secured_put_collateral_generic",
            severity="warning",
            applies_to="cash_collateral_impact",
            message="Short-put collateral uses generic deterministic rules, not broker-specific margin treatment.",
        )
        )
    if _requires_real_broker_position_truth_gate(supported_flow, scope_metadata):
        caveats.append(
            WorkspaceCaveatRead(
                code="current_position_truth_unstable",
                severity="warning",
                applies_to="scope_metadata",
                message=(
                    "Real broker position rows are not treated as authoritative current position truth "
                    "for this position-dependent review."
                ),
            )
        )
        caveats.append(
            WorkspaceCaveatRead(
                code="account_level_feasibility_not_evaluated",
                severity="warning",
                applies_to="scope_metadata",
                message="Selected review account metadata is resolved, but account-level feasibility is not evaluated.",
            )
        )
        if supported_flow == "covered_call":
            caveats.append(
                WorkspaceCaveatRead(
                    code="covered_call_coverage_unverified",
                    severity="warning",
                    applies_to="options_exposure",
                    message="Covered-call coverage does not rely on broker stock or option rows yet.",
                )
            )
        if supported_flow == "cash_secured_put":
            caveats.append(
                WorkspaceCaveatRead(
                    code="cash_collateral_policy_not_reviewed",
                    severity="warning",
                    applies_to="cash_collateral_impact",
                    message="Short-put collateral review does not rely on broker capacity or collateral fields yet.",
                )
            )
            caveats.append(
                WorkspaceCaveatRead(
                    code="buying_power_display_only",
                    severity="warning",
                    applies_to="scope_metadata",
                    message="Broker capacity labels are private display labels only and are not feasibility inputs.",
                )
            )
            caveats.append(
                WorkspaceCaveatRead(
                    code="csp_collateral_unverified",
                    severity="warning",
                    applies_to="cash_collateral_impact",
                    message="Short-put collateral remains unverified for the selected account.",
                )
            )
    if projection.portfolio_impact.market_manual_review_required:
        caveats.append(
            WorkspaceCaveatRead(
                code="market_data_manual_review_required",
                severity="warning",
                applies_to="market_quotes",
                message="Market data is missing, stale, manual, or otherwise requires review before using account-specific outputs.",
            )
        )
    return tuple(caveats)


def _infer_supported_flow(intent_summary: dict[str, Any]) -> SupportedTradeReviewFlow:
    asset_class = intent_summary.get("asset_class")
    if asset_class == "stock":
        return "stock_buy" if intent_summary.get("action") == "buy" else "stock_sell_trim"
    if asset_class == "etf":
        return "etf_buy" if intent_summary.get("action") == "buy" else "etf_sell_trim"
    if asset_class == "option":
        strategy_type = intent_summary.get("strategy_type")
        if strategy_type == "covered_call":
            return "covered_call"
        if strategy_type == "cash_secured_put":
            return "cash_secured_put"
    raise ValueError("unsupported Phase 18A trade-review flow")


def _review_flow_label(flow: SupportedTradeReviewFlow) -> str:
    labels: dict[SupportedTradeReviewFlow, str] = {
        "stock_buy": "Stock buy review",
        "stock_sell_trim": "Stock sell/trim review",
        "etf_buy": "ETF buy review",
        "etf_sell_trim": "ETF sell/trim review",
        "covered_call": "Covered call review",
        "cash_secured_put": "Cash-secured put review",
    }
    return labels[flow]


def _resolve_preview_instrument_identity(
    payload: TradeReviewWorkspacePreviewRequest,
    *,
    symbol_service: SymbolService | None = None,
) -> _ResolvedPreviewInstrumentIdentity:
    flow = payload.supported_flow
    is_equity_flow = flow in {"stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"}
    symbol = payload.symbol if is_equity_flow else getattr(payload.option_leg, "underlying_symbol", None)
    if not symbol:
        return _ResolvedPreviewInstrumentIdentity(
            supported_flow=flow,
            identity=InstrumentIdentityRead(),
        )

    try:
        validation = (symbol_service or SymbolService()).validate(symbol)
    except Exception:
        validation = None
    if validation is None or validation.data_mode != "provider_reference":
        if not is_equity_flow:
            return _ResolvedPreviewInstrumentIdentity(
                supported_flow=flow,
                identity=InstrumentIdentityRead(),
            )
        return _ResolvedPreviewInstrumentIdentity(
            supported_flow=flow,
            identity=InstrumentIdentityRead(
                resolved_instrument_kind=_declared_instrument_kind(flow),
                resolution_status="declared_only",
                source_label="Submitted trade-review flow",
                as_of_label="Declared for this saved review",
            ),
        )

    directory_kind = {
        "stock": "operating_company_equity",
        "adr": "operating_company_equity",
        "etf": "etf_or_fund",
    }.get(validation.asset_class if validation.is_found and validation.is_supported else "")
    directory_as_of = _safe_symbol_directory_as_of_label(validation.as_of_label)
    if directory_kind is None:
        return _ResolvedPreviewInstrumentIdentity(
            supported_flow=flow,
            identity=InstrumentIdentityRead(
                source_label="Nasdaq Symbol Directory",
                as_of_label=directory_as_of,
            ),
        )

    if not is_equity_flow:
        return _ResolvedPreviewInstrumentIdentity(
            supported_flow=flow,
            identity=InstrumentIdentityRead(
                resolved_instrument_kind=directory_kind,
                resolution_status="confirmed",
                source_label="Nasdaq Symbol Directory",
                as_of_label=directory_as_of,
            ),
        )

    reconciled_flow = _flow_for_resolved_instrument_kind(flow, directory_kind)
    return _ResolvedPreviewInstrumentIdentity(
        supported_flow=reconciled_flow,
        identity=InstrumentIdentityRead(
            resolved_instrument_kind=directory_kind,
            resolution_status="mismatch_reconciled" if reconciled_flow != flow else "confirmed",
            source_label="Nasdaq Symbol Directory",
            as_of_label=directory_as_of,
        ),
    )


def _declared_instrument_kind(flow: SupportedTradeReviewFlow) -> str:
    return "etf_or_fund" if flow in {"etf_buy", "etf_sell_trim"} else "operating_company_equity"


def _flow_for_resolved_instrument_kind(
    flow: SupportedTradeReviewFlow,
    resolved_kind: str,
) -> SupportedTradeReviewFlow:
    is_buy = flow in {"stock_buy", "etf_buy"}
    if resolved_kind == "etf_or_fund":
        return "etf_buy" if is_buy else "etf_sell_trim"
    return "stock_buy" if is_buy else "stock_sell_trim"


def _safe_symbol_directory_as_of_label(value: str) -> str:
    label = value.strip()
    try:
        InstrumentIdentityRead(
            source_label="Nasdaq Symbol Directory",
            as_of_label=label,
        )
    except ValueError:
        return "Nasdaq Symbol Directory as-of unavailable"
    return label


def _preview_intent(
    payload: TradeReviewWorkspacePreviewRequest,
    *,
    generated_at: datetime,
    user_id=None,
    account_id=None,
    broker_portfolio_status: str = "fresh",
    market_quote_status: str = "manual",
    intent_prefix: str = "preview",
) -> TradeIntent:
    freshness = TradeIntentFreshnessSnapshot(
        broker_portfolio_status=broker_portfolio_status,
        market_quote_status=market_quote_status,
    )
    common = {
        "intent_id": f"{intent_prefix}-{uuid4().hex}",
        "user_id": user_id or uuid4(),
        "account_id": account_id or uuid4(),
        "created_at": generated_at,
        "calculation_version": "trade-review-preview-v1",
        "data_freshness_snapshot": freshness,
        "status": "ready_for_review",
    }
    if payload.supported_flow in {"stock_buy", "stock_sell_trim"}:
        return StockTradeIntent(
            **common,
            asset_class="stock",
            intent_type=payload.supported_flow,
            symbol=payload.symbol or "",
            action="buy" if payload.supported_flow == "stock_buy" else "trim",
            quantity=payload.quantity or Decimal("0"),
            price_assumption=payload.price_assumption,
        )
    if payload.supported_flow in {"etf_buy", "etf_sell_trim"}:
        return ETFTradeIntent(
            **common,
            asset_class="etf",
            intent_type=payload.supported_flow,
            symbol=payload.symbol or "",
            action="buy" if payload.supported_flow == "etf_buy" else "trim",
            quantity=payload.quantity or Decimal("0"),
            price_assumption=payload.price_assumption,
        )
    leg = _preview_option_leg(payload.option_leg)
    return OptionStrategyIntent(
        **common,
        asset_class="option",
        intent_type="option_strategy",
        strategy_type=payload.supported_flow,
        underlying_symbol=leg.underlying_symbol,
        legs=(leg,),
    )


def _preview_option_leg(payload: TradeReviewPreviewOptionLeg | None) -> OptionLeg:
    if payload is None:
        raise ValueError("option_leg is required")
    return OptionLeg(
        underlying_symbol=payload.underlying_symbol,
        option_type=payload.option_type,
        leg_action=payload.leg_action,
        expiration_date=payload.expiration_date,
        strike=payload.strike,
        quantity=payload.quantity,
        premium=payload.premium,
        multiplier=payload.multiplier,
        occ_symbol=payload.occ_symbol,
        support_status=payload.support_status,
        unsupported_reason=payload.unsupported_reason,
    )


def _intent_symbol(intent: TradeIntent) -> str:
    return getattr(intent, "symbol", None) or getattr(intent, "underlying_symbol", "UNKNOWN")


def _default_preview_broker_snapshot() -> BrokerSnapshotMetadata:
    return BrokerSnapshotMetadata(
        source="synthetic_mock",
        freshness_status="fresh",
        provider_status="not_applicable",
    )


def _default_preview_market_quotes() -> MarketQuotesMetadata:
    return MarketQuotesMetadata(
        freshness_status="manual",
        data_mode="manual",
        actionability_status="manual_review_required",
        provider_status="not_applicable",
    )


def _resolve_portfolio_context(
    selection: PortfolioContextSelectionRequest,
    *,
    generated_at: datetime,
    review_account_selection: ReviewAccountSelectionRequest | None = None,
    db: Session | None = None,
    current_user_id: UUID | None = None,
) -> _ResolvedPortfolioContext:
    selected_account_snapshot = _resolve_selected_account_snapshot_context(
        selection=selection,
        review_account_selection=review_account_selection,
        db=db,
        current_user_id=current_user_id,
        generated_at=generated_at,
    )
    if selected_account_snapshot.resolved is not None:
        return selected_account_snapshot.resolved
    if selected_account_snapshot.requested_but_unavailable:
        return _unavailable_selected_account_snapshot_context(
            selection=selection,
            review_account_selection=review_account_selection,
            generated_at=generated_at,
        )

    reference = _LATEST_CONTEXT_REFERENCE if selection.mode == "latest_available" else selection.context_reference
    if reference == _NO_CONTEXT_REFERENCE:
        return _resolved_context(
            reference=reference,
            selection=selection,
            generated_at=generated_at,
            context_source="synthetic_mock",
            label=None,
            broker_snapshot=BrokerSnapshotMetadata(
                source="synthetic_mock",
                freshness_status="unknown",
                provider_status="not_applicable",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="unknown",
                data_mode="unknown",
                actionability_status="blocked_unknown_quote",
                provider_status="not_applicable",
            ),
            include_summary=False,
            stock_position_count=0,
            option_position_count=0,
            cash_available=False,
        )
    if reference == _STALE_CONTEXT_REFERENCE:
        return _resolved_context(
            reference=reference,
            selection=selection,
            generated_at=generated_at,
            context_source="manual",
            label="Manual context snapshot",
            broker_snapshot=BrokerSnapshotMetadata(
                source="manual",
                freshness_status="stale",
                as_of=generated_at,
                received_at=generated_at,
                provider_status="not_applicable",
            ),
            market_quotes=_default_portfolio_market_quotes(generated_at),
            stock_position_count=2,
            option_position_count=1,
            cash_available=True,
        )
    if reference == _MISSING_MARKET_CONTEXT_REFERENCE:
        return _resolved_context(
            reference=reference,
            selection=selection,
            generated_at=generated_at,
            context_source="manual",
            label="Manual context snapshot",
            broker_snapshot=BrokerSnapshotMetadata(
                source="manual",
                freshness_status="fresh",
                as_of=generated_at,
                received_at=generated_at,
                provider_status="not_applicable",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="unknown",
                data_mode="unknown",
                actionability_status="blocked_unknown_quote",
                provider_status="not_applicable",
            ),
            stock_position_count=2,
            option_position_count=1,
            cash_available=True,
        )
    if selection.mode == "selected_context" and reference != _LATEST_CONTEXT_REFERENCE:
        return _resolved_context(
            reference=reference,
            selection=selection,
            generated_at=generated_at,
            context_source="synthetic_mock",
            label=None,
            broker_snapshot=BrokerSnapshotMetadata(
                source="synthetic_mock",
                freshness_status="unknown",
                provider_status="not_applicable",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="unknown",
                data_mode="unknown",
                actionability_status="blocked_unknown_quote",
                provider_status="not_applicable",
            ),
            include_summary=False,
            stock_position_count=0,
            option_position_count=0,
            cash_available=False,
        )
    return _resolved_context(
        reference=_LATEST_CONTEXT_REFERENCE,
        selection=selection,
        generated_at=generated_at,
        context_source="manual",
        label="Manual context snapshot",
        broker_snapshot=BrokerSnapshotMetadata(
            source="manual",
            freshness_status="fresh",
            as_of=generated_at,
            received_at=generated_at,
            provider_status="not_applicable",
        ),
        market_quotes=_default_portfolio_market_quotes(generated_at),
        stock_position_count=2,
        option_position_count=1,
        cash_available=True,
    )


def _resolve_selected_account_snapshot_context(
    *,
    selection: PortfolioContextSelectionRequest,
    review_account_selection: ReviewAccountSelectionRequest | None,
    db: Session | None,
    current_user_id: UUID | None,
    generated_at: datetime,
) -> _SelectedAccountSnapshotResolution:
    """Project the selected account's latest synced rows into a lossy context.

    This boundary reads local synchronized records only.  It does not trigger a
    broker sync or pass ORM instances, identifiers, quantities, cost basis, or
    provider payloads to the review context.
    """

    if (
        db is None
        or current_user_id is None
        or review_account_selection is None
        or review_account_selection.mode != "selected_account"
        or review_account_selection.account_reference is None
    ):
        return _SelectedAccountSnapshotResolution()
    try:
        row = _broker_account_detail_row_for_account_reference(
            db,
            user_id=current_user_id,
            account_reference=review_account_selection.account_reference,
        )
    except SQLAlchemyError:
        return _SelectedAccountSnapshotResolution(requested_but_unavailable=True)
    if row is None or row.broker_account.account_id is None or row.latest_sync_run is None:
        return _SelectedAccountSnapshotResolution(requested_but_unavailable=True)

    broker_account = row.broker_account
    latest_sync_run = row.latest_sync_run
    try:
        cash_row = db.scalar(
            select(CashBalance)
            .where(
                CashBalance.account_id == broker_account.account_id,
                CashBalance.sync_run_id == latest_sync_run.id,
            )
            .order_by(CashBalance.as_of.desc(), CashBalance.created_at.desc(), CashBalance.id.desc())
            .limit(1)
        )
        stock_rows = list(
            db.scalars(
                select(StockPosition)
                .where(
                    StockPosition.account_id == broker_account.account_id,
                    StockPosition.sync_run_id == latest_sync_run.id,
                )
                .order_by(
                    StockPosition.symbol.asc(),
                    StockPosition.as_of.desc(),
                    StockPosition.created_at.desc(),
                    StockPosition.id.desc(),
                )
            )
        )
        option_rows = list(
            db.execute(
                select(OptionPosition, OptionContract)
                .join(OptionContract, OptionPosition.option_contract_id == OptionContract.id)
                .where(
                    OptionPosition.account_id == broker_account.account_id,
                    OptionPosition.sync_run_id == latest_sync_run.id,
                    OptionPosition.status == "open",
                    OptionContract.expiration_date >= generated_at.date(),
                )
                .order_by(
                    OptionPosition.option_contract_id.asc(),
                    OptionPosition.as_of.desc(),
                    OptionPosition.created_at.desc(),
                    OptionPosition.id.desc(),
                )
            )
        )
    except SQLAlchemyError:
        return _SelectedAccountSnapshotResolution(requested_but_unavailable=True)

    latest_stock_rows = _latest_stock_positions_by_symbol(stock_rows)
    latest_option_rows = _latest_option_position_rows_by_contract(option_rows)
    snapshot_times = [
        value
        for value in (
            cash_row.as_of if cash_row is not None else None,
            *(position.as_of for position in latest_stock_rows),
            *(position.as_of for position, _contract in latest_option_rows),
            latest_sync_run.completed_at,
            latest_sync_run.started_at,
            broker_account.last_successful_sync_at,
            row.broker_connection.last_successful_sync_at,
        )
        if value is not None
    ]
    snapshot_as_of = max(snapshot_times, default=generated_at)
    broker_snapshot_as_of = (
        latest_sync_run.completed_at
        or latest_sync_run.started_at
        or broker_account.last_successful_sync_at
        or row.broker_connection.last_successful_sync_at
        or snapshot_as_of
    )
    funding_snapshot = (
        _SelectedAccountCashSnapshot(
            available_funding_value=Decimal(cash_row.free_cash),
            snapshot_as_of=cash_row.as_of,
        )
        if cash_row is not None
        else None
    )
    equity_exposures = tuple(
        _SelectedAccountEquityExposure(
            symbol=position.symbol.strip().upper(),
            asset_type=position.asset_type,
            market_value=Decimal(position.market_value) if position.market_value is not None else None,
            snapshot_as_of=position.as_of,
        )
        for position in latest_stock_rows
        if position.symbol.strip()
    )
    option_exposures = tuple(
        _SelectedAccountOptionExposure(
            symbol=contract.underlying_symbol.strip().upper(),
            asset_type="option",
            market_value=Decimal(position.market_value) if position.market_value is not None else None,
            snapshot_as_of=position.as_of,
        )
        for position, contract in latest_option_rows
        if contract.underlying_symbol.strip()
    )
    broker_status = _snapshot_freshness_status(
        _broker_snapshot_status(
            broker_account,
            row.broker_connection,
            has_successful_sync=True,
            preserve_canonical_sync_freshness=True,
        )
    )
    broker_snapshot = BrokerSnapshotMetadata(
        source="snaptrade" if row.broker_connection.provider.strip().lower() == "snaptrade" else "manual",
        freshness_status=broker_status,
        sync_status=latest_sync_run.status,
        as_of=broker_snapshot_as_of,
        received_at=latest_sync_run.completed_at,
        last_successful_sync_at=(
            broker_account.last_successful_sync_at or row.broker_connection.last_successful_sync_at
        ),
        provider_status="available",
    )
    nickname = (broker_account.user_nickname or "").strip()
    account_label = nickname or "Reviewed account"
    context_reference = f"ctx_{_opaque_digest(('review_snapshot', broker_account.id, latest_sync_run.id))}"
    return _SelectedAccountSnapshotResolution(
        resolved=_ResolvedPortfolioContext(
            context=_SelectedAccountSnapshotContext(
                snapshot_as_of=snapshot_as_of,
                funding_snapshot=funding_snapshot,
                equity_exposures=equity_exposures,
                option_exposures=option_exposures,
            ),
            summary=PortfolioContextSummaryRead(
                context_reference=context_reference,
                context_source="account_snapshot",
                selection_mode=selection.mode,
                summary_as_of=snapshot_as_of,
                latest_snapshot_as_of=snapshot_as_of,
                broker_snapshot=broker_snapshot,
                stock_position_count=len(equity_exposures),
                option_position_count=len(option_exposures),
                cash_state="available" if funding_snapshot is not None else "unavailable",
                label=account_label,
            ),
            broker_snapshot=broker_snapshot,
            market_quotes=_default_portfolio_market_quotes(generated_at),
        )
    )


def _unavailable_selected_account_snapshot_context(
    *,
    selection: PortfolioContextSelectionRequest,
    review_account_selection: ReviewAccountSelectionRequest | None,
    generated_at: datetime,
) -> _ResolvedPortfolioContext:
    """Keep a failed selected-account request from inheriting demo values."""

    account_reference = review_account_selection.account_reference if review_account_selection is not None else None
    context_reference = f"ctx_{_opaque_digest(('review_snapshot_unavailable', account_reference))}"
    broker_snapshot = BrokerSnapshotMetadata(
        source="snaptrade",
        freshness_status="unknown",
        provider_status="unavailable",
    )
    market_quotes = MarketQuotesMetadata(
        freshness_status="unknown",
        data_mode="unknown",
        actionability_status="blocked_unknown_quote",
        provider_status="unknown",
    )
    return _ResolvedPortfolioContext(
        context=_SelectedAccountSnapshotContext(
            snapshot_as_of=generated_at,
            funding_snapshot=None,
            equity_exposures=(),
            option_exposures=(),
        ),
        summary=PortfolioContextSummaryRead(
            context_reference=context_reference,
            context_source="account_snapshot",
            selection_mode=selection.mode,
            summary_as_of=None,
            latest_snapshot_as_of=None,
            broker_snapshot=broker_snapshot,
            stock_position_count=0,
            option_position_count=0,
            cash_state="unavailable",
            label="Account snapshot unavailable",
        ),
        broker_snapshot=broker_snapshot,
        market_quotes=market_quotes,
        account_snapshot_unavailable=True,
    )


def _snapshot_freshness_status(status: str) -> str:
    """Map account-detail freshness labels into the actionability schema safely."""

    return {
        "manual_review": "cached",
        "unavailable": "error",
    }.get(status, status if status in DATA_FRESHNESS_STATUSES else "unknown")


def _default_portfolio_market_quotes(generated_at: datetime) -> MarketQuotesMetadata:
    return MarketQuotesMetadata(
        freshness_status="manual",
        data_mode="manual",
        actionability_status="manual_review_required",
        as_of_min=generated_at,
        as_of_max=generated_at,
        received_at_min=generated_at,
        received_at_max=generated_at,
        provider_status="not_applicable",
    )


def _resolved_context(
    *,
    reference: str | None,
    selection: PortfolioContextSelectionRequest,
    generated_at: datetime,
    context_source: str,
    label: str | None,
    broker_snapshot: BrokerSnapshotMetadata,
    market_quotes: MarketQuotesMetadata,
    stock_position_count: int,
    option_position_count: int,
    cash_available: bool,
    include_summary: bool = True,
) -> _ResolvedPortfolioContext:
    stock_positions = _synthetic_stock_positions(
        count=stock_position_count,
        generated_at=generated_at,
        freshness_status=broker_snapshot.freshness_status,
        source=context_source,
    )
    option_positions = _synthetic_option_positions(
        count=option_position_count,
        generated_at=generated_at,
        freshness_status=broker_snapshot.freshness_status,
        source=context_source,
    )
    cash = (
        CashContext(
            total_cash=Decimal("12000"),
            free_cash=Decimal("10000"),
            reserved_collateral_cash=Decimal("2000"),
            data_freshness_status=broker_snapshot.freshness_status,
            as_of=generated_at,
            source=context_source,
        )
        if cash_available
        else None
    )
    context = PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=generated_at,
        latest_snapshot_as_of=broker_snapshot.as_of,
        total_internal_value=_synthetic_total_internal_value(
            cash=cash,
            stock_positions=stock_positions,
            option_positions=option_positions,
        ),
        data_sources=(context_source,),
        data_freshness_statuses=(broker_snapshot.freshness_status,),
        cash=cash,
        stock_positions=stock_positions,
        option_positions=option_positions,
    )
    summary = None
    if include_summary and reference is not None:
        summary = PortfolioContextSummaryRead(
            context_reference=reference,
            context_source=context_source,
            selection_mode=selection.mode,
            summary_as_of=generated_at,
            latest_snapshot_as_of=broker_snapshot.as_of,
            broker_snapshot=broker_snapshot,
            stock_position_count=stock_position_count,
            option_position_count=option_position_count,
            cash_state="available" if cash_available else "unavailable",
            label=label,
        )
    return _ResolvedPortfolioContext(
        context=context,
        summary=summary,
        broker_snapshot=broker_snapshot,
        market_quotes=market_quotes,
    )


def _synthetic_stock_positions(
    *,
    count: int,
    generated_at: datetime,
    freshness_status: str,
    source: str,
) -> tuple[StockPositionContext, ...]:
    templates = (
        ("XYZ", "stock", Decimal("100"), Decimal("5000")),
        ("QQQ", "etf", Decimal("10"), Decimal("4000")),
    )
    return tuple(
        StockPositionContext(
            symbol=symbol,
            asset_type=asset_type,
            quantity=quantity,
            market_value=market_value,
            data_freshness_status=freshness_status,
            as_of=generated_at,
            source=source,
        )
        for symbol, asset_type, quantity, market_value in templates[:count]
    )


def _synthetic_option_positions(
    *,
    count: int,
    generated_at: datetime,
    freshness_status: str,
    source: str,
) -> tuple[OptionPositionContext, ...]:
    return tuple(
        OptionPositionContext(
            option_contract_id=uuid4(),
            position_side="short",
            quantity=Decimal("1"),
            market_value=Decimal("-200"),
            status="open",
            data_freshness_status=freshness_status,
            as_of=generated_at,
            source=source,
        )
        for _ in range(count)
    )


def _synthetic_total_internal_value(
    *,
    cash: CashContext | None,
    stock_positions: tuple[StockPositionContext, ...],
    option_positions: tuple[OptionPositionContext, ...],
) -> Decimal:
    total = Decimal("0")
    if cash is not None:
        total += cash.total_cash
    total += sum((position.market_value or Decimal("0") for position in stock_positions), Decimal("0"))
    total += sum((position.market_value or Decimal("0") for position in option_positions), Decimal("0"))
    return total


def _reject_forbidden_input(payload: object, *, label: str) -> None:
    forbidden = find_forbidden_keys(
        payload,
        forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS,
    )
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{label} contains forbidden private fields: {blocked}")


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal_text(value: object) -> str:
    decimal_value = _optional_decimal(value)
    if decimal_value is None:
        raise ValueError("decimal value is required")
    return str(decimal_value)


def _optional_decimal_text(value: object) -> str | None:
    decimal_value = _optional_decimal(value)
    if decimal_value is None:
        return None
    return str(decimal_value)


def _optional_value_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _policy_label(violation) -> str | None:
    if violation.threshold is None:
        return None
    metric = violation.metric or "threshold"
    return f"{metric}_policy"


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal value: {value}") from exc
