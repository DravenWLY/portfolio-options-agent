"""Frontend-safe projection for the first Trade Review Workspace."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from app.schemas.actionability import (
    BrokerSnapshotMetadata,
    MarketQuotesMetadata,
    PortfolioActionabilityDecision,
    PortfolioActionabilityInput,
)
from app.schemas.trade_review_workspace import (
    AgentOrchestrationSummaryRead,
    AnalysisOnlyReportOutputRead,
    CashCollateralImpactRead,
    ConcentrationAllocationImpactRead,
    DeterministicTradeReviewRead,
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
    PortfolioImpactSummaryRead,
    ReviewReadinessRead,
    RiskAlertItemRead,
    RiskAlertListRead,
    RiskRuleViolationSummaryRead,
    ScenarioPayoffPointRead,
    ScenarioPayoffSummaryRead,
    SupportedTradeReviewFlow,
    TradeReviewListItemRead,
    TradeReviewListRead,
    TradeReviewPreviewOptionLeg,
    TradeIntentSummaryRead,
    TradeReviewWorkspaceRead,
    TradeReviewWorkspacePreviewRequest,
    TradeReviewPortfolioPreviewRequest,
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


_LATEST_CONTEXT_REFERENCE = "ctx_demo_latest"
_STALE_CONTEXT_REFERENCE = "ctx_demo_stale"
_MISSING_MARKET_CONTEXT_REFERENCE = "ctx_demo_missing"
_NO_CONTEXT_REFERENCE = "ctx_demo_empty"

_DEMO_EMPTY_USER_REFERENCE = "00000000-0000-0000-0000-000000000000"
_PHASE20B_DEMO_NOTICE = "demo · not yet connected"


@dataclass(frozen=True)
class _ResolvedPortfolioContext:
    context: PortfolioReviewContext
    summary: PortfolioContextSummaryRead | None
    broker_snapshot: BrokerSnapshotMetadata
    market_quotes: MarketQuotesMetadata


def build_trade_review_workspace_read(
    *,
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
    review_reference: str | None = None,
    supported_flow: SupportedTradeReviewFlow | None = None,
    orchestration_result: AgentTeamOrchestrationResult | None = None,
    report_output: ReportComposerAgentOutput | None = None,
    portfolio_context_summary: PortfolioContextSummaryRead | None = None,
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
    summary = _intent_summary(projection.intent_summary, supported_flow=flow)
    read = TradeReviewWorkspaceRead(
        review_reference=review_reference or projection.intent_id,
        generated_at=generated_at or projection.generated_at or datetime.now(UTC),
        calculation_version=projection.calculation_version,
        supported_flow=flow,
        trade_intent_summary=summary,
        portfolio_context=portfolio_context_summary,
        actionability=actionability,
        deterministic_review=DeterministicTradeReviewRead(
            highest_severity=projection.highest_severity,
            has_blocker=projection.has_blocker,
            portfolio_impact=_portfolio_impact(projection),
            cash_collateral_impact=_cash_collateral_impact(summary),
            concentration_allocation_impact=_concentration_allocation_impact(projection),
            options_exposure=_options_exposure(summary, projection, supported_flow=flow),
            risk_rule_violations=_risk_rule_violations(projection),
            missing_data_warnings=_missing_data_warnings(projection, actionability),
            scenario_payoff_summary=_scenario_payoff_summary(projection),
        ),
        agent_orchestration=_agent_orchestration(orchestration_result),
        report_output=_report_output(report_output or (orchestration_result.report_output if orchestration_result else None)),
        caveats=_caveats(projection, actionability, flow),
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
    intent = _preview_intent(payload, generated_at=generated)
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
    return build_trade_review_workspace_read(
        projection=to_agent_safe_projection(report),
        actionability=actionability,
        review_reference=report.intent_id,
        supported_flow=payload.supported_flow,
        generated_at=generated,
    )


def _portfolio_context_detail(context: PortfolioContextRead) -> PortfolioContextDetailRead:
    read = PortfolioContextDetailRead(
        data_mode="synthetic_demo",
        demo_notice=_PHASE20B_DEMO_NOTICE,
        context=context,
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
) -> TradeReviewWorkspaceRead:
    """Build a portfolio-backed preview from server-owned sanitized context."""

    generated = generated_at or datetime.now(UTC)
    resolved = _resolve_portfolio_context(payload.portfolio_context_selection, generated_at=generated)
    actionability = evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=resolved.broker_snapshot,
            market_quotes=resolved.market_quotes,
            user_confirmation=None,
        ),
        evaluated_at=generated,
    )
    intent = _preview_intent(
        payload,
        generated_at=generated,
        user_id=resolved.context.user_id,
        account_id=resolved.context.account_id,
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
    return build_trade_review_workspace_read(
        projection=to_agent_safe_projection(report),
        actionability=actionability,
        review_reference=report.intent_id,
        supported_flow=payload.supported_flow,
        portfolio_context_summary=resolved.summary,
        generated_at=generated,
    )


def _intent_summary(
    intent_summary: dict[str, Any],
    *,
    supported_flow: SupportedTradeReviewFlow,
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


def _caveats(
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
    supported_flow: SupportedTradeReviewFlow,
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
                message="Cash-secured-put collateral uses generic deterministic rules, not broker-specific margin treatment.",
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
) -> _ResolvedPortfolioContext:
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
