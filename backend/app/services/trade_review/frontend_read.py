"""Frontend-safe projection for the first Trade Review Workspace."""

from dataclasses import asdict
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
    PortfolioImpactSummaryRead,
    RiskRuleViolationSummaryRead,
    ScenarioPayoffPointRead,
    ScenarioPayoffSummaryRead,
    SupportedTradeReviewFlow,
    TradeReviewPreviewOptionLeg,
    TradeIntentSummaryRead,
    TradeReviewWorkspaceRead,
    TradeReviewWorkspacePreviewRequest,
    WorkspaceCaveatRead,
    WorkspaceOptionLegSummaryRead,
    validate_trade_review_workspace_payload,
)
from app.services.agents.orchestrator import AgentTeamOrchestrationResult, DEFAULT_AGENT_WORKFLOW_STAGES
from app.services.agents.report_composer import ReportComposerAgentOutput
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability
from app.services.trade_review.context import PortfolioReviewContext
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


def build_trade_review_workspace_read(
    *,
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
    review_reference: str | None = None,
    supported_flow: SupportedTradeReviewFlow | None = None,
    orchestration_result: AgentTeamOrchestrationResult | None = None,
    report_output: ReportComposerAgentOutput | None = None,
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


def _preview_intent(payload: TradeReviewWorkspacePreviewRequest, *, generated_at: datetime) -> TradeIntent:
    freshness = TradeIntentFreshnessSnapshot(
        broker_portfolio_status="fresh",
        market_quote_status="manual",
    )
    common = {
        "intent_id": f"preview-{uuid4().hex}",
        "user_id": uuid4(),
        "account_id": uuid4(),
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


def _reject_forbidden_input(payload: object, *, label: str) -> None:
    forbidden = find_forbidden_keys(
        payload,
        forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS
        | {"provider_contract_id", "provider_contract_ids", "provider_symbol", "provider_symbols"},
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
