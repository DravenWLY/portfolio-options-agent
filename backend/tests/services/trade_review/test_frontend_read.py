from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput, UserConfirmationMetadata
from app.schemas.trade_review_workspace import (
    TradeReviewPortfolioPreviewRequest,
    TradeReviewWorkspaceRead,
    validate_trade_review_workspace_payload,
)
from app.services.agents import PortfolioAgentTeamOrchestrator
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.risk.violations import RiskRuleViolation
from app.services.trade_review import AgentSafePortfolioImpact, PortfolioReviewContext, StockPositionContext
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability
from app.services.trade_review.frontend_read import (
    build_trade_review_workspace_portfolio_preview,
    build_trade_review_workspace_read,
    get_dashboard_account_summary_for_user,
    _resolve_portfolio_context,
)
from app.services.trade_review.payoff import PayoffReview, PayoffScenarioPoint
from app.services.trade_review.report import TradeReviewAgentProjection
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidationFinding, TradeIntentValidationResult


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 21, 0, tzinfo=UTC)


def _option_leg(*, option_type: str, leg_action: str) -> dict:
    return {
        "underlying_symbol": "XYZ",
        "option_type": option_type,
        "leg_action": leg_action,
        "expiration_date": date(2026, 6, 19),
        "strike": "50",
        "quantity": "1",
        "premium": "2",
        "multiplier": "100",
        "occ_symbol": "XYZ260619C00050000" if option_type == "call" else "XYZ260619P00050000",
        "support_status": "supported",
    }


@pytest.mark.parametrize(
    ("intent_summary", "expected_flow"),
    (
        (
            {
                "intent_id": "stock-buy-1",
                "asset_class": "stock",
                "intent_type": "stock_buy",
                "status": "ready_for_review",
                "symbol": "XYZ",
                "action": "buy",
                "quantity": "3",
                "price_assumption": "50",
            },
            "stock_buy",
        ),
        (
            {
                "intent_id": "etf-trim-1",
                "asset_class": "etf",
                "intent_type": "etf_trim",
                "status": "ready_for_review",
                "symbol": "QQQ",
                "action": "trim",
                "quantity": "2",
                "price_assumption": "100",
            },
            "etf_sell_trim",
        ),
        (
            {
                "intent_id": "covered-call-1",
                "asset_class": "option",
                "intent_type": "option_strategy",
                "status": "ready_for_review",
                "strategy_type": "covered_call",
                "underlying_symbol": "XYZ",
                "legs": (_option_leg(option_type="call", leg_action="sell_to_open"),),
            },
            "covered_call",
        ),
        (
            {
                "intent_id": "csp-1",
                "asset_class": "option",
                "intent_type": "option_strategy",
                "status": "ready_for_review",
                "strategy_type": "cash_secured_put",
                "underlying_symbol": "XYZ",
                "legs": (_option_leg(option_type="put", leg_action="sell_to_open"),),
            },
            "cash_secured_put",
        ),
    ),
)
def test_workspace_read_contract_supports_phase_18a_flows(intent_summary, expected_flow) -> None:
    read = build_trade_review_workspace_read(
        projection=_projection(intent_summary=intent_summary),
        actionability=_normal_actionability(),
    )

    assert read.supported_flow == expected_flow
    assert read.trade_intent_summary.supported_flow == expected_flow
    assert read.actionability.review_actionability_status == "normal_review"
    assert read.actionability.broker_snapshot.freshness_scope == "broker_snapshot"
    assert read.actionability.market_quotes.freshness_scope == "market_quote"
    assert read.deterministic_review.scenario_payoff_summary.points
    assert read.deterministic_review.cash_collateral_impact.projected_free_cash_state == "not_exposed"
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)


def test_workspace_read_adds_coverage_and_collateral_caveats_for_option_flows() -> None:
    covered_call = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "covered-call-1",
                "asset_class": "option",
                "intent_type": "option_strategy",
                "status": "ready_for_review",
                "strategy_type": "covered_call",
                "underlying_symbol": "XYZ",
                "legs": (_option_leg(option_type="call", leg_action="sell_to_open"),),
            },
            assignment_share_delta=Decimal("-100"),
        ),
        actionability=_normal_actionability(),
    )
    csp = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "csp-1",
                "asset_class": "option",
                "intent_type": "option_strategy",
                "status": "ready_for_review",
                "strategy_type": "cash_secured_put",
                "underlying_symbol": "XYZ",
                "legs": (_option_leg(option_type="put", leg_action="sell_to_open"),),
            },
            assignment_share_delta=Decimal("100"),
        ),
        actionability=_normal_actionability(),
    )

    assert covered_call.deterministic_review.options_exposure.covered_call_coverage_model == "not_fully_modelled"
    assert "covered_call_coverage_not_fully_modelled" in {caveat.code for caveat in covered_call.caveats}
    assert csp.deterministic_review.options_exposure.cash_secured_put_collateral_model == "generic_rule_only"
    assert "cash_secured_put_collateral_generic" in {caveat.code for caveat in csp.caveats}


def test_workspace_read_preserves_analysis_only_and_stale_actionability_warnings() -> None:
    analysis_only = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "manual-stock-1",
                "asset_class": "stock",
                "intent_type": "stock_buy",
                "status": "ready_for_review",
                "symbol": "XYZ",
                "action": "buy",
                "quantity": "3",
                "price_assumption": "50",
            }
        ),
        actionability=_manual_confirmed_actionability(),
    )
    stale = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "stale-stock-1",
                "asset_class": "stock",
                "intent_type": "stock_buy",
                "status": "ready_for_review",
                "symbol": "XYZ",
                "action": "buy",
                "quantity": "3",
                "price_assumption": "50",
            },
            broker_freshness_status="stale",
        ),
        actionability=_stale_broker_actionability(),
    )

    assert analysis_only.actionability.review_actionability_status == "analysis_only"
    assert "analysis_only_actionability" in {caveat.code for caveat in analysis_only.caveats}
    assert stale.actionability.review_actionability_status == "blocked_stale_broker_snapshot"
    assert any(warning.code == "broker_snapshot_stale" for warning in stale.deterministic_review.missing_data_warnings)


def test_workspace_read_includes_safe_orchestration_summary_without_envelopes() -> None:
    projection = _projection(
        intent_summary={
            "intent_id": "stock-buy-1",
            "asset_class": "stock",
            "intent_type": "stock_buy",
            "status": "ready_for_review",
            "symbol": "XYZ",
            "action": "buy",
            "quantity": "3",
            "price_assumption": "50",
        }
    )
    actionability = _normal_actionability()
    orchestration = PortfolioAgentTeamOrchestrator().run(
        run_reference="workspace-run-1",
        portfolio_context=_portfolio_context(),
        trade_review_projection=projection,
        actionability=actionability,
        generated_at=NOW,
    )

    read = build_trade_review_workspace_read(
        projection=projection,
        actionability=actionability,
        orchestration_result=orchestration,
    )

    assert read.agent_orchestration is not None
    assert read.agent_orchestration.stage_order
    assert read.agent_orchestration.stage_statuses["validate_trade_intent"] == "completed"
    assert read.agent_orchestration.unavailable_stages["retrieve_public_research_evidence"]
    serialized = repr(read.agent_orchestration.model_dump())
    assert "payload" not in serialized
    assert "output_envelope" not in serialized


def test_workspace_read_rejects_forbidden_private_fields_and_prohibited_language() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        build_trade_review_workspace_read(
            projection=_projection(
                intent_summary={
                    "intent_id": "bad-1",
                    "asset_class": "stock",
                    "intent_type": "stock_buy",
                    "status": "ready_for_review",
                    "symbol": "XYZ",
                    "action": "buy",
                    "quantity": "3",
                    "price_assumption": "50",
                    "provider_account_id": "provider-private",
                }
            ),
            actionability=_normal_actionability(),
        )

    with pytest.raises(ValueError, match="forbidden private fields"):
        build_trade_review_workspace_read(
            projection=_projection(
                intent_summary={
                    "intent_id": "bad-2",
                    "asset_class": "option",
                    "intent_type": "option_strategy",
                    "status": "ready_for_review",
                    "strategy_type": "covered_call",
                    "underlying_symbol": "XYZ",
                    "legs": (
                        {
                            **_option_leg(option_type="call", leg_action="sell_to_open"),
                            "provider_contract_id": "provider-contract-private",
                        },
                    ),
                }
            ),
            actionability=_normal_actionability(),
        )

    with pytest.raises(ValueError, match="forbidden private fields"):
        validate_trade_review_workspace_payload({"raw_account_values": {"total": "12345"}})

    with pytest.raises(ValueError, match="prohibited phrase"):
        validate_trade_review_workspace_payload({"message": "You should buy this now."})

    with pytest.raises(ValueError, match="prohibited phrase"):
        payload = build_trade_review_workspace_read(
            projection=_projection(
                intent_summary={
                    "intent_id": "stock-buy-1",
                    "asset_class": "stock",
                    "intent_type": "stock_buy",
                    "status": "ready_for_review",
                    "symbol": "XYZ",
                    "action": "buy",
                    "quantity": "3",
                    "price_assumption": "50",
                }
            ),
            actionability=_normal_actionability(),
        ).model_dump()
        payload["caveats"] = (
            {
                "code": "bad",
                "severity": "warning",
                "applies_to": "workspace",
                "message": "Guaranteed return language is blocked.",
            },
        )
        TradeReviewWorkspaceRead(
            **payload,
        )


def test_workspace_read_exposes_risk_findings_and_validation_warnings_without_raw_values() -> None:
    read = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "stock-buy-1",
                "asset_class": "stock",
                "intent_type": "stock_buy",
                "status": "manual_review_required",
                "symbol": "XYZ",
                "action": "buy",
                "quantity": "3",
                "price_assumption": "50",
            },
            validation_findings=(
                TradeIntentValidationFinding(
                    code="price_assumption_manual",
                    severity="warning",
                    message="Price assumption requires review.",
                    field="price_assumption",
                ),
            ),
            risk_violations=(
                RiskRuleViolation(
                    code="market_quote_manual_review_required",
                    severity="warning",
                    message="Market quote requires review.",
                    source="market_quote",
                    actual="manual_review_required",
                    metric="account_specific_limit",
                    threshold=Decimal("777777"),
                ),
            ),
        ),
        actionability=_manual_confirmed_actionability(),
    )

    assert read.deterministic_review.risk_rule_violations[0].actual == "manual_review_required"
    assert read.deterministic_review.risk_rule_violations[0].policy_label == "account_specific_limit_policy"
    assert "threshold" not in _collect_keys(read.model_dump(mode="python"))
    assert "777777" not in repr(read.model_dump(mode="python"))
    assert any(warning.code == "validation_price_assumption_manual" for warning in read.deterministic_review.missing_data_warnings)
    assert "account_id" not in _collect_keys(read.model_dump(mode="python"))


def test_portfolio_preview_service_returns_safe_context_summary() -> None:
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
    )

    assert read.portfolio_context is not None
    assert read.portfolio_context.context_reference == "ctx_demo_latest"
    assert read.portfolio_context.cash_state == "available"
    assert read.actionability.review_actionability_status == "manual_confirmation_required"
    assert read.actionability.broker_snapshot.freshness_scope == "broker_snapshot"
    assert read.actionability.market_quotes.freshness_scope == "market_quote"
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_portfolio_preview_resolved_context_matches_safe_summary_counts_and_cash_state() -> None:
    resolved = _resolve_portfolio_context(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ).portfolio_context_selection,
        generated_at=NOW,
    )

    assert resolved.summary is not None
    assert len(resolved.context.stock_positions) == resolved.summary.stock_position_count
    assert len(resolved.context.option_positions) == resolved.summary.option_position_count
    assert resolved.summary.cash_state == "available"
    assert resolved.context.cash is not None
    assert resolved.context.total_internal_value != Decimal("0")
    assert resolved.context.data_freshness_statuses == (resolved.summary.broker_snapshot.freshness_status,)


def test_portfolio_preview_csp_uses_available_cash_context_without_missing_cash_blocker() -> None:
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="cash_secured_put",
            option_leg={
                "underlying_symbol": "XYZ",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": date(2026, 6, 19),
                "strike": Decimal("50"),
                "quantity": Decimal("1"),
                "premium": Decimal("2"),
            },
        ),
        generated_at=NOW,
    )

    assert read.portfolio_context is not None
    assert read.portfolio_context.cash_state == "available"
    assert read.deterministic_review.cash_collateral_impact.estimated_collateral_requirement_change == "5000"
    assert "cash_secured_put_collateral_generic" in {caveat.code for caveat in read.caveats}
    assert "cash_context_missing_for_collateral" not in {
        violation.code for violation in read.deterministic_review.risk_rule_violations
    }


def test_portfolio_preview_csp_flags_missing_cash_context_when_context_unavailable() -> None:
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="cash_secured_put",
            option_leg={
                "underlying_symbol": "XYZ",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": date(2026, 6, 19),
                "strike": Decimal("50"),
                "quantity": Decimal("1"),
                "premium": Decimal("2"),
            },
            portfolio_context_selection={
                "mode": "selected_context",
                "context_reference": "ctx_demo_empty",
            },
        ),
        generated_at=NOW,
    )

    assert read.portfolio_context is None
    assert "cash_secured_put_collateral_generic" in {caveat.code for caveat in read.caveats}
    assert "cash_context_missing_for_collateral" in {
        violation.code for violation in read.deterministic_review.risk_rule_violations
    }


def test_portfolio_preview_service_preserves_no_context_available_state() -> None:
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
            portfolio_context_selection={
                "mode": "selected_context",
                "context_reference": "ctx_demo_empty",
            },
        ),
        generated_at=NOW,
    )

    assert read.portfolio_context is None
    assert read.actionability.review_actionability_status == "blocked_unknown_freshness"
    assert any(warning.code == "unknown_freshness" for warning in read.deterministic_review.missing_data_warnings)
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_dashboard_account_summary_contract_uses_hidden_display_labels_only() -> None:
    read = get_dashboard_account_summary_for_user(
        "11111111-1111-1111-1111-111111111111",
        generated_at=NOW,
    )

    payload = read.model_dump(mode="python")
    assert read.data_mode == "synthetic_demo"
    assert read.display_scope == "synthetic_demo"
    assert read.valuation_basis == "unavailable"
    assert read.market_data_mode == "synthetic"
    assert read.privacy_display_mode == "amounts_hidden"
    assert read.total_value_label == "Total value hidden · demo not connected"
    assert read.cash_label == "Cash amount hidden · demo not connected"
    assert read.stock_etf_exposure_label == "Stock/ETF exposure hidden · demo not connected"
    assert read.options_exposure_label == "Options exposure hidden · demo not connected"
    assert read.collateral_usage_label == "Collateral usage hidden · demo not connected"
    assert read.stock_exposure_label == read.stock_etf_exposure_label
    assert read.option_exposure_label == read.options_exposure_label
    assert read.broker_snapshot_freshness.freshness_scope == "broker_snapshot"
    assert read.market_quote_freshness is not None
    assert read.market_quote_freshness.freshness_scope == "market_quote"
    assert "amounts_hidden" in read.caveat_codes
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_dashboard_account_summary_empty_state_stays_unavailable_and_hidden() -> None:
    read = get_dashboard_account_summary_for_user(
        "00000000-0000-0000-0000-000000000000",
        generated_at=NOW,
    )

    assert read.data_mode == "synthetic_demo"
    assert read.display_scope == "unavailable"
    assert read.valuation_basis == "unavailable"
    assert read.market_data_mode == "unavailable"
    assert read.privacy_display_mode == "amounts_hidden"
    assert read.market_quote_freshness is None
    assert read.market_data_unavailable is True
    assert read.portfolio_shape.stock_position_count == 0
    assert read.portfolio_shape.option_position_count == 0
    assert read.portfolio_shape_label == "Portfolio shape unavailable"
    assert read.position_count_label == "No portfolio context available"
    assert "market_data_unavailable" in read.caveat_codes


def _projection(
    *,
    intent_summary: dict,
    broker_freshness_status: str = "fresh",
    market_freshness_status: str = "fresh",
    assignment_share_delta: Decimal = Decimal("0"),
    exercise_share_delta: Decimal = Decimal("0"),
    validation_findings: tuple[TradeIntentValidationFinding, ...] = (),
    risk_violations: tuple[RiskRuleViolation, ...] = (),
) -> TradeReviewAgentProjection:
    highest_validation = "warning" if validation_findings else None
    return TradeReviewAgentProjection(
        intent_id=intent_summary["intent_id"],
        generated_at=NOW,
        calculation_version="trade-review-v1",
        intent_summary=intent_summary,
        validation=TradeIntentValidationResult(
            intent_id=intent_summary["intent_id"],
            findings=validation_findings,
            manual_review_required=bool(validation_findings),
            blocked=False,
            highest_severity=highest_validation,
            is_clean=not validation_findings,
        ),
        payoff=PayoffReview(
            intent_id=intent_summary["intent_id"],
            asset_class=intent_summary["asset_class"],
            points=(
                PayoffScenarioPoint(
                    label="unchanged",
                    underlying_price=Decimal("50"),
                    net_cash_flow=Decimal("-150"),
                    scenario_value=Decimal("150"),
                    scenario_pnl=Decimal("0"),
                    description="Synthetic deterministic scenario.",
                ),
            ),
            max_loss=Decimal("150") if intent_summary["asset_class"] == "option" else None,
            max_gain=None,
            calculation_notes=("Synthetic deterministic calculation; simple scenario review, not a forecast.",),
        ),
        portfolio_impact=AgentSafePortfolioImpact(
            broker_freshness_status=broker_freshness_status,
            market_freshness_status=market_freshness_status,
            market_manual_review_required=market_freshness_status != "fresh",
            assignment_share_delta=assignment_share_delta,
            exercise_share_delta=exercise_share_delta,
            concentration_symbol=intent_summary.get("symbol") or intent_summary.get("underlying_symbol"),
            notes=("Synthetic safe projection.",),
        ),
        risk_rule_violations=risk_violations,
        highest_severity=risk_violations[0].severity if risk_violations else None,
        has_blocker=any(violation.severity == "blocker" for violation in risk_violations),
        data_freshness_snapshot={
            "broker_portfolio_status": broker_freshness_status,
            "market_quote_status": market_freshness_status,
        },
        market_snapshot=TradeReviewMarketSnapshot(
            report_market_snapshot=None,
            missing_symbols=("XYZ",) if market_freshness_status != "fresh" else (),
            manual_review_required=market_freshness_status != "fresh",
        ),
    )


def _normal_actionability():
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="fresh",
                sync_status="succeeded",
                as_of=NOW,
                received_at=NOW,
                last_successful_sync_at=NOW,
                provider_status="available",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="fresh",
                data_mode="live",
                actionability_status="actionable_snapshot",
                as_of_min=NOW,
                as_of_max=NOW,
                received_at_min=NOW,
                received_at_max=NOW,
                provider_status="available",
            ),
        ),
        evaluated_at=NOW,
    )


def _manual_confirmed_actionability():
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=BrokerSnapshotMetadata(
                source="manual",
                freshness_status="fresh",
                provider_status="not_applicable",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="manual",
                data_mode="manual",
                actionability_status="manual_review_required",
                provider_status="not_applicable",
            ),
            user_confirmation=UserConfirmationMetadata(
                state="confirmed",
                confirmed_at=NOW,
                expires_at=NOW + timedelta(hours=2),
            ),
        ),
        evaluated_at=NOW,
    )


def _stale_broker_actionability():
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="stale",
                provider_status="available",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="fresh",
                data_mode="live",
                actionability_status="actionable_snapshot",
                provider_status="available",
            ),
        ),
        evaluated_at=NOW,
    )


def _portfolio_context() -> PortfolioReviewContext:
    return PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=NOW,
        latest_snapshot_as_of=NOW,
        total_internal_value=Decimal("1200"),
        data_sources=("synthetic",),
        data_freshness_statuses=("fresh",),
        cash=None,
        stock_positions=(
            StockPositionContext(
                symbol="XYZ",
                asset_type="stock",
                quantity=Decimal("3"),
                market_value=Decimal("300"),
                data_freshness_status="fresh",
                as_of=NOW,
                source="synthetic",
            ),
        ),
        option_positions=(),
    )


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {str(key) for key in value}
        for item in value.values():
            found.update(_collect_keys(item))
        return found
    if isinstance(value, (list, tuple)):
        found: set[str] = set()
        for item in value:
            found.update(_collect_keys(item))
        return found
    return set()
