from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput, UserConfirmationMetadata
from app.schemas.reports import SavedEvidenceSectionRead
from app.schemas.trade_review_workspace import (
    PortfolioContextSelectionRequest,
    PortfolioScopeRead,
    ReportScopeMetadataRead,
    ReviewAccountRead,
    ReviewAccountSelectionRequest,
    TradeReviewPortfolioPreviewRequest,
    TradeReviewWorkspaceRead,
    validate_trade_review_workspace_payload,
)
from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.models.user import User
from app.services.broker_import.statuses import DATA_FRESHNESS_STATUSES
from app.services.agents import PortfolioAgentTeamOrchestrator
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.risk.violations import RiskRuleViolation
from app.services.trade_review import frontend_read as frontend_read_service
from app.services.trade_review import AgentSafePortfolioImpact, PortfolioReviewContext, StockPositionContext
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability
from app.services.trade_review.frontend_read import (
    build_trade_review_workspace_portfolio_preview,
    build_trade_review_workspace_read,
    get_account_details_for_user,
    get_dashboard_account_summary_for_user,
    _account_details_from_broker_rows,
    _broker_snapshot_status,
    _BrokerAccountDetailsRow,
    _NormalizedAccountMetrics,
    _latest_option_positions_by_contract,
    _latest_stock_positions_by_symbol,
    _opaque_account_reference,
    _option_average_cost_display_value,
    _option_cost_basis,
    _option_position_market_value,
    _option_tax_lot_rows,
    _review_account_for_broker_rows,
    _resolve_portfolio_context,
    _snapshot_freshness_status,
    _selected_account_details_from_broker_row,
)
from app.services.trade_review.payoff import PayoffReview, PayoffScenarioPoint
from app.services.trade_review.report import TradeReviewAgentProjection
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidationFinding, TradeIntentValidationResult
from app.services.trade_review.models import ETFTradeIntent, OptionStrategyIntent, StockTradeIntent
from app.services.symbols import SymbolRecord, SymbolService


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 21, 0, tzinfo=UTC)


class _StaticSymbolProvider:
    data_mode = "provider_reference"
    source_label = "Nasdaq Symbol Directory"
    as_of_label = "Nasdaq Symbol Directory file time 2026-05-20"

    def __init__(self, records: tuple[SymbolRecord, ...], *, fail: bool = False) -> None:
        self._records = records
        self._fail = fail

    def list_symbols(self) -> tuple[SymbolRecord, ...]:
        if self._fail:
            raise RuntimeError("synthetic directory unavailable")
        return self._records


def _reviewed_symbol_service() -> SymbolService:
    return SymbolService(
        _StaticSymbolProvider(
            (
                SymbolRecord(symbol="FUNDX", name="Synthetic Fund", asset_class="etf", exchange="NASDAQ"),
                SymbolRecord(symbol="OPCO", name="Synthetic Company", asset_class="stock", exchange="NASDAQ"),
                SymbolRecord(symbol="ADRX", name="Synthetic ADR", asset_class="adr", exchange="NASDAQ"),
            )
        )
    )


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
    assert read.scope_metadata is not None
    assert read.scope_metadata.portfolio_context_scope.context_reference == read.portfolio_context.context_reference
    assert read.scope_metadata.review_account is None
    assert read.scope_metadata.account_level_feasibility_evaluated is False
    assert "review_account_not_selected" in read.scope_metadata.scope_caveat_codes
    assert read.actionability.review_actionability_status == "manual_confirmation_required"
    assert read.actionability.broker_snapshot.freshness_scope == "broker_snapshot"
    assert read.actionability.market_quotes.freshness_scope == "market_quote"
    assert "account_snapshot_unavailable" not in {caveat.code for caveat in read.caveats}
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


@pytest.mark.parametrize(
    ("submitted_flow", "symbol", "resolved_flow", "intent_type", "resolved_kind"),
    (
        ("stock_buy", "FUNDX", "etf_buy", ETFTradeIntent, "etf_or_fund"),
        ("stock_sell_trim", "FUNDX", "etf_sell_trim", ETFTradeIntent, "etf_or_fund"),
        ("etf_buy", "OPCO", "stock_buy", StockTradeIntent, "operating_company_equity"),
        ("etf_sell_trim", "ADRX", "stock_sell_trim", StockTradeIntent, "operating_company_equity"),
    ),
)
def test_portfolio_preview_reconciles_stock_and_etf_identity_before_exposure_math(
    monkeypatch: pytest.MonkeyPatch,
    submitted_flow: str,
    symbol: str,
    resolved_flow: str,
    intent_type: type,
    resolved_kind: str,
) -> None:
    captured_intents: list[object] = []

    def _capture_exposure_intent(*, portfolio_context: object, intent: object) -> tuple[object, ...]:
        del portfolio_context
        captured_intents.append(intent)
        return ()

    monkeypatch.setattr(frontend_read_service, "try_build_exposure_evidence_sections", _capture_exposure_intent)
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow=submitted_flow,
            symbol=symbol,
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
        symbol_service=_reviewed_symbol_service(),
    )

    assert read.supported_flow == resolved_flow
    assert read.trade_intent_summary.supported_flow == resolved_flow
    assert read.trade_intent_summary.instrument_identity.resolved_instrument_kind == resolved_kind
    assert read.trade_intent_summary.instrument_identity.resolution_status == "mismatch_reconciled"
    assert read.trade_intent_summary.instrument_identity.source_label == "Nasdaq Symbol Directory"
    assert isinstance(captured_intents[0], intent_type)
    assert "instrument_type_reconciled" in {caveat.code for caveat in read.caveats}


def test_portfolio_preview_preserves_declared_flow_when_directory_is_unavailable() -> None:
    unavailable_service = SymbolService(_StaticSymbolProvider((), fail=True))
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="FUNDX",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
        symbol_service=unavailable_service,
    )

    identity = read.trade_intent_summary.instrument_identity
    assert read.supported_flow == "stock_buy"
    assert identity.resolved_instrument_kind == "operating_company_equity"
    assert identity.resolution_status == "declared_only"
    assert identity.source_label == "Submitted trade-review flow"
    assert "instrument_type_reconciled" not in {caveat.code for caveat in read.caveats}


def test_portfolio_preview_keeps_unmatched_directory_identity_unresolved() -> None:
    unmatched = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="etf_buy",
            symbol="MISSX",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
        symbol_service=_reviewed_symbol_service(),
    )
    assert unmatched.supported_flow == "etf_buy"
    assert unmatched.trade_intent_summary.instrument_identity.resolution_status == "unresolved"
    assert unmatched.trade_intent_summary.instrument_identity.resolved_instrument_kind == "unknown"


@pytest.mark.parametrize(
    ("is_supported", "is_test_issue"),
    (
        (False, False),
        (True, True),
    ),
)
def test_portfolio_preview_does_not_reconcile_from_unsupported_directory_records(
    is_supported: bool,
    is_test_issue: bool,
) -> None:
    service = SymbolService(
        _StaticSymbolProvider(
            (
                SymbolRecord(
                    symbol="FUNDX",
                    name="Synthetic Unsupported Fund",
                    asset_class="etf",
                    exchange="NASDAQ",
                    is_supported=is_supported,
                    is_test_issue=is_test_issue,
                ),
            )
        )
    )
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="FUNDX",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
        symbol_service=service,
    )

    assert read.supported_flow == "stock_buy"
    assert read.trade_intent_summary.asset_class == "stock"
    assert read.trade_intent_summary.instrument_identity.resolution_status == "unresolved"
    assert read.trade_intent_summary.instrument_identity.resolved_instrument_kind == "unknown"
    assert "instrument_type_reconciled" not in {caveat.code for caveat in read.caveats}


@pytest.mark.parametrize(
    "unsafe_as_of_label",
    (
        "Nasdaq Symbol Directory provider_account_id=acct-12345",
        "Nasdaq Symbol Directory account_number=987654321",
        "Nasdaq Symbol Directory sk-proj-abcdefghijklmnopqrstuvwxyz123456",
        "Nasdaq Symbol Directory http:example.invalid",
        "Nasdaq Symbol Directory file:raw-directory",
        "Nasdaq Symbol Directory file time 2026-05-20\u2028raw",
        "Nasdaq Symbol Directory\vfile time 2026-05-20",
        "https://example.invalid/raw-directory-path",
    ),
)
def test_portfolio_preview_rejects_private_or_secret_like_directory_metadata(
    unsafe_as_of_label: str,
) -> None:
    provider = _StaticSymbolProvider(
        (SymbolRecord(symbol="FUNDX", name="Synthetic Fund", asset_class="etf", exchange="NASDAQ"),)
    )
    provider.as_of_label = unsafe_as_of_label
    safe = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="etf_buy",
            symbol="FUNDX",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
        symbol_service=SymbolService(provider),
    )
    assert safe.trade_intent_summary.instrument_identity.as_of_label == (
        "Nasdaq Symbol Directory as-of unavailable"
    )
    assert unsafe_as_of_label not in repr(safe.model_dump(mode="python"))


def test_options_flow_keeps_strategy_while_freezing_underlying_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_intents: list[object] = []

    def _capture_exposure_intent(*, portfolio_context: object, intent: object) -> tuple[object, ...]:
        del portfolio_context
        captured_intents.append(intent)
        return ()

    monkeypatch.setattr(frontend_read_service, "try_build_exposure_evidence_sections", _capture_exposure_intent)
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="cash_secured_put",
            option_leg={
                "underlying_symbol": "FUNDX",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": "2026-06-19",
                "strike": "50",
                "quantity": "1",
                "premium": "2",
            },
        ),
        generated_at=NOW,
        symbol_service=_reviewed_symbol_service(),
    )

    identity = read.trade_intent_summary.instrument_identity
    assert read.supported_flow == "cash_secured_put"
    assert identity.resolved_instrument_kind == "etf_or_fund"
    assert identity.resolution_status == "confirmed"
    assert isinstance(captured_intents[0], OptionStrategyIntent)
    assert "instrument_type_reconciled" not in {caveat.code for caveat in read.caveats}


def test_portfolio_preview_service_resolves_selected_review_account_separately_from_context() -> None:
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
            review_account_selection={
                "mode": "selected_account",
                "account_reference": "acctref_demo_primary",
            },
        ),
        generated_at=NOW,
    )

    assert read.portfolio_context is not None
    assert read.scope_metadata is not None
    assert read.scope_metadata.review_account is not None
    assert read.scope_metadata.review_account.account_reference == "acctref_demo_primary"
    assert read.scope_metadata.review_account.is_account_level_feasibility_source is True
    assert read.scope_metadata.portfolio_context_scope.context_reference == "ctx_demo_latest"
    assert read.scope_metadata.account_level_feasibility_evaluated is True
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_real_broker_covered_call_review_is_analysis_only_without_validated_position_truth() -> None:
    read = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "covered-real-broker",
                "asset_class": "option",
                "intent_type": "option_strategy",
                "strategy_type": "covered_call",
                "status": "ready_for_review",
                "underlying_symbol": "XYZ",
                "legs": (_option_leg(option_type="call", leg_action="sell_to_open"),),
            },
            assignment_share_delta=Decimal("-100"),
        ),
        actionability=_normal_actionability(),
        supported_flow="covered_call",
        scope_metadata=_real_broker_scope_metadata(),
        generated_at=NOW,
    )

    caveat_codes = {caveat.code for caveat in read.caveats}
    warning_codes = {warning.code for warning in read.deterministic_review.missing_data_warnings}
    assert read.actionability.review_actionability_status == "analysis_only"
    assert read.actionability.broker_snapshot.freshness_scope == "broker_snapshot"
    assert read.actionability.market_quotes.freshness_scope == "market_quote"
    assert read.scope_metadata is not None
    assert read.scope_metadata.review_account is not None
    assert read.scope_metadata.review_account.is_account_level_feasibility_source is False
    assert read.scope_metadata.account_level_feasibility_evaluated is False
    assert "current_position_truth_unstable" in caveat_codes
    assert "covered_call_coverage_unverified" in caveat_codes
    assert "account_level_feasibility_not_evaluated" in caveat_codes
    assert "current_position_truth_unstable" in warning_codes
    assert "covered_call_coverage_unverified" in warning_codes
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_real_broker_csp_review_does_not_use_unreviewed_collateral_policy() -> None:
    read = build_trade_review_workspace_read(
        projection=_projection(
            intent_summary={
                "intent_id": "csp-real-broker",
                "asset_class": "option",
                "intent_type": "option_strategy",
                "strategy_type": "cash_secured_put",
                "status": "ready_for_review",
                "underlying_symbol": "XYZ",
                "legs": (_option_leg(option_type="put", leg_action="sell_to_open"),),
            },
            assignment_share_delta=Decimal("100"),
        ),
        actionability=_normal_actionability(),
        supported_flow="cash_secured_put",
        scope_metadata=_real_broker_scope_metadata(),
        generated_at=NOW,
    )

    caveat_codes = {caveat.code for caveat in read.caveats}
    warning_codes = {warning.code for warning in read.deterministic_review.missing_data_warnings}
    assert read.actionability.review_actionability_status == "analysis_only"
    assert read.deterministic_review.options_exposure.cash_secured_put_collateral_model == "generic_rule_only"
    assert read.scope_metadata is not None
    assert read.scope_metadata.account_level_feasibility_evaluated is False
    assert "buying_power_display_only" in read.scope_metadata.scope_caveat_codes
    assert "cash_collateral_policy_not_reviewed" in read.scope_metadata.scope_caveat_codes
    assert "cash_collateral_policy_not_reviewed" in caveat_codes
    assert "buying_power_display_only" in caveat_codes
    assert "csp_collateral_unverified" in caveat_codes
    assert "current_position_truth_unstable" in caveat_codes
    assert "cash_collateral_policy_not_reviewed" in warning_codes
    assert "buying_power_display_only" in warning_codes
    assert "csp_collateral_unverified" in warning_codes
    assert "current_position_truth_unstable" in warning_codes
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    rendered = repr(read.model_dump(mode="python")).lower()
    assert "sufficient collateral" not in rendered
    assert "ready to trade" not in rendered
    assert "safe to trade" not in rendered


def test_real_review_account_selection_resolves_from_app_owned_broker_rows_only() -> None:
    user_id = uuid4()
    connection = BrokerConnection(
        id=uuid4(),
        user_id=user_id,
        provider="snaptrade",
        broker_name="Fidelity account 1234 should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Raw taxable account ending 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
        raw_payload={"holdings": [{"symbol": "XYZ", "quantity": "999"}]},
    )
    selection = ReviewAccountSelectionRequest(
        mode="selected_account",
        account_reference=_opaque_account_reference(broker_account.id),
    )

    review_account = _review_account_for_broker_rows(
        review_account_selection=selection,
        rows=(
            _BrokerAccountDetailsRow(
                broker_account=broker_account,
                broker_connection=connection,
                latest_sync_run=None,
                metrics=_NormalizedAccountMetrics(),
            ),
        ),
    )

    assert review_account is not None
    payload = review_account.model_dump(mode="python")
    assert review_account.account_reference == selection.account_reference
    assert review_account.display_label == "Fidelity taxable"
    assert review_account.is_review_account is True
    assert review_account.is_included_in_portfolio_scope is False
    assert review_account.is_account_level_feasibility_source is False
    rendered = repr(payload).lower()
    assert "provider_account_id_secret_456" not in rendered
    assert "provider_connection_id_secret_123" not in rendered
    assert "raw taxable account ending" not in rendered
    assert "1234" not in rendered
    assert "quantity" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_unknown_real_review_account_selection_does_not_resolve() -> None:
    selection = ReviewAccountSelectionRequest(
        mode="selected_account",
        account_reference="acctref_demo_missing",
    )

    review_account = _review_account_for_broker_rows(review_account_selection=selection, rows=())

    assert review_account is None


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
    assert read.scope_metadata is not None
    assert read.scope_metadata.review_account is None
    assert read.scope_metadata.portfolio_context_scope.scope_mode == "unavailable"
    assert read.scope_metadata.account_level_feasibility_evaluated is False
    assert read.actionability.review_actionability_status == "blocked_unknown_freshness"
    assert any(warning.code == "unknown_freshness" for warning in read.deterministic_review.missing_data_warnings)
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_portfolio_preview_exposure_adapter_failure_does_not_break_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def _raise_from_adapter(**kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("adapter failure should not fail preview")

    monkeypatch.setattr(frontend_read_service, "try_build_exposure_evidence_sections", _raise_from_adapter)

    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
    )

    assert calls == 1
    assert read.supported_flow == "stock_buy"
    assert read.deterministic_review.portfolio_impact.concentration_symbol == "XYZ"
    assert not find_forbidden_keys(read.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_portfolio_preview_surfaces_funding_shortfall_caveat_from_frozen_exposure_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sections = (
        SavedEvidenceSectionRead(
            section_key="before_after_portfolio_impact",
            section_label="Before/after portfolio impact",
            availability="available",
            summary_label="Synthetic frozen before/after impact.",
            caveat_codes=("funding_shortfall_detected",),
        ),
        SavedEvidenceSectionRead(
            section_key="concentration_risk_drift",
            section_label="Concentration and risk drift",
            availability="available",
            summary_label="Synthetic frozen concentration impact.",
            caveat_codes=("funding_shortfall_detected",),
        ),
    )
    monkeypatch.setattr(
        frontend_read_service,
        "try_build_exposure_evidence_sections",
        lambda **_kwargs: sections,
    )

    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
        ),
        generated_at=NOW,
    )

    shortfall = next(caveat for caveat in read.caveats if caveat.code == "funding_shortfall_detected")
    assert shortfall.severity == "warning"
    assert shortfall.applies_to == "cash_collateral_impact"
    assert "external funding was assumed" in shortfall.message


def test_selected_account_snapshot_resolver_projects_only_safe_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synced_at = datetime(2026, 5, 17, 15, 30, tzinfo=UTC)
    user_id = uuid4()
    account_id = uuid4()
    connection = BrokerConnection(
        id=uuid4(),
        user_id=user_id,
        provider="snaptrade",
        broker_name="Provider brokerage name should not render",
        provider_connection_id="provider_connection_id_projection_secret",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="stale",
        last_successful_sync_at=synced_at,
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        account_id=account_id,
        provider_account_id="provider_account_id_projection_secret",
        display_name="Provider account ending 1234 should not render",
        user_nickname="Growth Demo Account",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="stale",
        last_successful_sync_at=synced_at,
        raw_payload={"provider_account_id": "provider_account_id_projection_secret"},
    )
    sync_run = BrokerSyncRun(
        id=uuid4(),
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=synced_at,
        completed_at=synced_at,
        provider_request_id="provider_request_id_projection_secret",
        accounts_count=1,
        positions_count=2,
        transactions_count=0,
    )
    cash_row = CashBalance(
        account_id=account_id,
        sync_run_id=sync_run.id,
        total_cash=Decimal("600.00"),
        available_cash=Decimal("500.00"),
        buying_power=Decimal("900.00"),
        reserved_collateral_cash=Decimal("0.00"),
        free_cash=Decimal("500.00"),
        premium_income_cash=Decimal("0.00"),
        dca_cash=Decimal("0.00"),
        source="snaptrade",
        source_ref="provider_cash_projection_secret",
        data_freshness_status="stale",
        as_of=synced_at,
    )
    stock_rows = (
        StockPosition(
            account_id=account_id,
            sync_run_id=sync_run.id,
            symbol="XYZ",
            asset_type="stock",
            quantity=Decimal("7"),
            market_value=Decimal("840.00"),
            source="snaptrade",
            source_ref="provider_stock_projection_secret",
            data_freshness_status="stale",
            raw_provider_payload={"quantity": "7", "provider_account_id": "provider_account_id_projection_secret"},
            as_of=synced_at,
        ),
        StockPosition(
            account_id=account_id,
            sync_run_id=sync_run.id,
            symbol="QQQ",
            asset_type="etf",
            quantity=Decimal("2"),
            market_value=None,
            source="snaptrade",
            source_ref="provider_stock_missing_value_projection_secret",
            data_freshness_status="stale",
            as_of=synced_at,
        ),
    )

    class _SnapshotSession:
        def scalar(self, _statement):
            return cash_row

        def scalars(self, _statement):
            return stock_rows

        def execute(self, _statement):
            return ()

    row = _BrokerAccountDetailsRow(
        broker_account=broker_account,
        broker_connection=connection,
        latest_sync_run=sync_run,
        metrics=_NormalizedAccountMetrics(),
    )
    monkeypatch.setattr(
        frontend_read_service,
        "_broker_account_detail_row_for_account_reference",
        lambda *_args, **_kwargs: row,
    )
    selection = ReviewAccountSelectionRequest(
        mode="selected_account",
        account_reference=_opaque_account_reference(broker_account.id),
    )
    resolved = _resolve_portfolio_context(
        PortfolioContextSelectionRequest(),
        generated_at=NOW,
        review_account_selection=selection,
        db=_SnapshotSession(),
        current_user_id=user_id,
    )

    assert resolved.summary is not None
    assert resolved.summary.context_source == "account_snapshot"
    assert resolved.summary.label == "Growth Demo Account"
    assert resolved.account_snapshot_unavailable is False
    assert resolved.broker_snapshot.freshness_status == "stale"
    context_payload = asdict(resolved.context)
    assert not find_forbidden_keys(context_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    rendered_context = repr(context_payload).lower()
    assert "provider_account_id_projection_secret" not in rendered_context
    assert "provider_connection_id_projection_secret" not in rendered_context
    assert "provider_stock_projection_secret" not in rendered_context
    assert "quantity" not in rendered_context
    assert "buying_power" not in rendered_context

    sections = frontend_read_service.try_build_exposure_evidence_sections(
        portfolio_context=resolved.context,
        intent=frontend_read_service._preview_intent(
            TradeReviewPortfolioPreviewRequest(
                supported_flow="stock_buy",
                symbol="XYZ",
                quantity=Decimal("3"),
                price_assumption=Decimal("50"),
            ),
            generated_at=NOW,
        ),
    )
    assert any("position_market_value_unavailable" in section.caveat_codes for section in sections)


@pytest.mark.parametrize("freshness_status", ("cached", "delayed"))
def test_selected_account_snapshot_preserves_canonical_broker_freshness_for_actionability(
    monkeypatch: pytest.MonkeyPatch,
    freshness_status: str,
) -> None:
    synced_at = datetime(2026, 5, 17, 15, 30, tzinfo=UTC)
    user_id = uuid4()
    connection = BrokerConnection(
        id=uuid4(),
        user_id=user_id,
        provider="snaptrade",
        broker_name="Synthetic Broker",
        provider_connection_id="synthetic_connection",
        connection_status="connected",
        sync_status="succeeded",
        data_freshness_status=freshness_status,
        last_successful_sync_at=synced_at,
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        account_id=uuid4(),
        provider_account_id="synthetic_account",
        display_name="Synthetic account",
        user_nickname="Synthetic review account",
        account_type="taxable_individual",
        sync_status="succeeded",
        data_freshness_status=freshness_status,
        last_successful_sync_at=synced_at,
    )
    sync_run = BrokerSyncRun(
        id=uuid4(),
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=synced_at,
        completed_at=synced_at,
        accounts_count=1,
        positions_count=0,
        transactions_count=0,
    )

    class _SnapshotSession:
        def scalar(self, _statement):
            return None

        def scalars(self, _statement):
            return ()

        def execute(self, _statement):
            return ()

    row = _BrokerAccountDetailsRow(
        broker_account=broker_account,
        broker_connection=connection,
        latest_sync_run=sync_run,
        metrics=_NormalizedAccountMetrics(),
    )
    monkeypatch.setattr(
        frontend_read_service,
        "_broker_account_detail_row_for_account_reference",
        lambda *_args, **_kwargs: row,
    )

    resolved = _resolve_portfolio_context(
        PortfolioContextSelectionRequest(),
        generated_at=NOW,
        review_account_selection=ReviewAccountSelectionRequest(
            mode="selected_account",
            account_reference=_opaque_account_reference(broker_account.id),
        ),
        db=_SnapshotSession(),
        current_user_id=user_id,
    )

    assert resolved.broker_snapshot.freshness_status == freshness_status
    unconfirmed = evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=resolved.broker_snapshot,
            market_quotes=resolved.market_quotes,
        ),
        evaluated_at=NOW,
    )
    confirmed = evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=resolved.broker_snapshot,
            market_quotes=resolved.market_quotes,
            user_confirmation=UserConfirmationMetadata(
                state="confirmed",
                confirmed_at=NOW,
                expires_at=NOW + timedelta(minutes=30),
            ),
        ),
        evaluated_at=NOW,
    )

    assert unconfirmed.review_actionability_status == "manual_confirmation_required"
    assert not unconfirmed.review_actionability_status.startswith("blocked_")
    assert confirmed.review_actionability_status == "analysis_only"
    assert confirmed.can_run_agent_explanation is True


def test_selected_account_snapshot_freshness_mapping_keeps_successful_sync_rescue_and_fails_closed() -> None:
    connection = BrokerConnection(
        id=uuid4(),
        user_id=uuid4(),
        provider="snaptrade",
        broker_name="Synthetic Broker",
        provider_connection_id="synthetic_connection",
        connection_status="connected",
        sync_status="succeeded",
        data_freshness_status="unknown",
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        account_id=uuid4(),
        provider_account_id="synthetic_account",
        display_name="Synthetic account",
        account_type="taxable_individual",
        sync_status="succeeded",
        data_freshness_status="unknown",
    )

    assert set(DATA_FRESHNESS_STATUSES) >= {"cached", "delayed"}
    rescued = _broker_snapshot_status(
        broker_account,
        connection,
        has_successful_sync=True,
        preserve_canonical_sync_freshness=True,
    )
    assert rescued == "manual_review"
    assert _snapshot_freshness_status(rescued) == "cached"

    broker_account.data_freshness_status = "unrecognized_status"
    assert _broker_snapshot_status(
        broker_account,
        connection,
        has_successful_sync=False,
        preserve_canonical_sync_freshness=True,
    ) == "unknown"


@pytest.mark.parametrize("failure_mode", ("unmatched", "no_completed_sync", "query_error"))
def test_selected_account_snapshot_resolution_failure_never_uses_demo_exposure(
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
) -> None:
    user_id = uuid4()
    account_reference = _opaque_account_reference(uuid4())
    selection = ReviewAccountSelectionRequest(
        mode="selected_account",
        account_reference=account_reference,
    )
    review_account = (
        ReviewAccountRead(
            account_reference=account_reference,
            display_label="Growth Demo Account",
            account_kind_label="Taxable brokerage",
            is_review_account=True,
            is_included_in_portfolio_scope=False,
            is_account_level_feasibility_source=False,
        )
        if failure_mode == "no_completed_sync"
        else None
    )
    monkeypatch.setattr(
        frontend_read_service,
        "_review_account_for_workspace_selection",
        lambda *_args, **_kwargs: review_account,
    )
    if failure_mode == "unmatched":
        monkeypatch.setattr(
            frontend_read_service,
            "_broker_account_detail_row_for_account_reference",
            lambda *_args, **_kwargs: None,
        )
    elif failure_mode == "no_completed_sync":
        connection = BrokerConnection(
            id=uuid4(),
            user_id=user_id,
            provider="snaptrade",
            broker_name="Synthetic broker",
            provider_connection_id="provider_connection_id_no_sync_secret",
            connection_status="connected",
            sync_status="idle",
            data_freshness_status="unknown",
        )
        broker_account = BrokerAccount(
            id=uuid4(),
            broker_connection_id=connection.id,
            account_id=uuid4(),
            provider_account_id="provider_account_id_no_sync_secret",
            display_name="Provider account should not render",
            user_nickname="Growth Demo Account",
            account_type="taxable_individual",
            sync_status="idle",
            data_freshness_status="unknown",
        )
        row = _BrokerAccountDetailsRow(
            broker_account=broker_account,
            broker_connection=connection,
            latest_sync_run=None,
            metrics=_NormalizedAccountMetrics(),
        )
        monkeypatch.setattr(
            frontend_read_service,
            "_broker_account_detail_row_for_account_reference",
            lambda *_args, **_kwargs: row,
        )
    else:
        def _raise_query_error(*_args, **_kwargs):
            raise SQLAlchemyError("synthetic selected-account query failure")

        monkeypatch.setattr(
            frontend_read_service,
            "_broker_account_detail_row_for_account_reference",
            _raise_query_error,
        )

    captured_sections: list[SavedEvidenceSectionRead] = []
    read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
            review_account_selection=selection,
        ),
        generated_at=NOW,
        db=object(),
        current_user_id=user_id,
        derived_exposure_sections_callback=captured_sections.extend,
    )

    assert read.portfolio_context is not None
    assert read.portfolio_context.context_source == "account_snapshot"
    assert read.portfolio_context.label == "Account snapshot unavailable"
    assert read.portfolio_context.stock_position_count == 0
    assert read.portfolio_context.option_position_count == 0
    assert read.portfolio_context.cash_state == "unavailable"
    assert captured_sections
    assert {section.availability for section in captured_sections} == {"not_available"}
    assert all("account_snapshot_unavailable" in section.caveat_codes for section in captured_sections)
    assert all(not section.detail_labels for section in captured_sections)
    frozen_sections = repr(tuple(section.model_dump(mode="python") for section in captured_sections))
    assert "$5,000.00" not in frozen_sections
    assert "$4,000.00" not in frozen_sections
    assert "ctx_demo_latest" not in frozen_sections

    assert read.scope_metadata is not None
    scope = read.scope_metadata.portfolio_context_scope
    assert scope.scope_mode == "unavailable"
    assert scope.display_label == "Account snapshot unavailable"
    assert scope.included_account_labels == ()
    assert "account_snapshot_unavailable" in scope.caveat_codes
    expected_scope_summary = (
        "Review account selected · Context scope: Account snapshot unavailable."
        if failure_mode == "no_completed_sync"
        else "Review account unresolved · Context scope: Account snapshot unavailable."
    )
    assert read.scope_metadata.scope_summary_label == expected_scope_summary
    assert "account_snapshot_unavailable" in {caveat.code for caveat in read.caveats}
    if failure_mode == "no_completed_sync":
        assert read.scope_metadata.review_account is not None
        assert read.scope_metadata.review_account.display_label == "Growth Demo Account"
        assert read.scope_metadata.review_account.is_included_in_portfolio_scope is False
        assert repr(read.scope_metadata.model_dump(mode="python")).lower().count("growth demo account") == 1
    else:
        assert read.scope_metadata.review_account is None


def test_selected_account_snapshot_context_is_lossy_and_replaces_demo_scope(
    db_session,
) -> None:
    synced_at = datetime(2026, 5, 17, 15, 30, tzinfo=UTC)
    user = User(display_name="Snapshot User", email="snapshot-user@example.com")
    db_session.add(user)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Synthetic Broker",
        account_type="taxable_individual",
        display_name="Internal snapshot account should not render",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Provider brokerage name should not render",
        provider_connection_id="provider_connection_id_snapshot_secret",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="stale",
        last_successful_sync_at=synced_at,
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="provider_account_id_snapshot_secret",
        display_name="Provider account ending 1234 should not render",
        user_nickname="Growth Demo Account",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="stale",
        last_successful_sync_at=synced_at,
        raw_payload={"provider_account_id": "provider_account_id_snapshot_secret"},
    )
    db_session.add(broker_account)
    db_session.flush()
    sync_run = BrokerSyncRun(
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=synced_at,
        completed_at=synced_at,
        provider_request_id="provider_request_id_snapshot_secret",
        accounts_count=1,
        positions_count=2,
        transactions_count=0,
    )
    db_session.add(sync_run)
    db_session.flush()
    db_session.add_all(
        (
            CashBalance(
                account_id=account.id,
                sync_run_id=sync_run.id,
                total_cash=Decimal("600.00"),
                available_cash=Decimal("500.00"),
                buying_power=Decimal("900.00"),
                reserved_collateral_cash=Decimal("0.00"),
                free_cash=Decimal("500.00"),
                premium_income_cash=Decimal("0.00"),
                dca_cash=Decimal("0.00"),
                source="snaptrade",
                source_ref="provider_cash_snapshot_secret",
                data_freshness_status="stale",
                as_of=synced_at,
            ),
            StockPosition(
                account_id=account.id,
                sync_run_id=sync_run.id,
                symbol="XYZ",
                asset_type="stock",
                quantity=Decimal("7"),
                market_value=Decimal("840.00"),
                source="snaptrade",
                source_ref="provider_stock_snapshot_secret",
                data_freshness_status="stale",
                raw_provider_payload={"quantity": "7", "provider_account_id": "provider_account_id_snapshot_secret"},
                as_of=synced_at,
            ),
            StockPosition(
                account_id=account.id,
                sync_run_id=sync_run.id,
                symbol="QQQ",
                asset_type="etf",
                quantity=Decimal("2"),
                market_value=None,
                source="snaptrade",
                source_ref="provider_stock_missing_value_secret",
                data_freshness_status="stale",
                raw_provider_payload={"quantity": "2", "provider_account_id": "provider_account_id_snapshot_secret"},
                as_of=synced_at,
            ),
        )
    )
    db_session.commit()

    account_reference = _opaque_account_reference(broker_account.id)
    selection = ReviewAccountSelectionRequest(
        mode="selected_account",
        account_reference=account_reference,
    )
    resolved = _resolve_portfolio_context(
        PortfolioContextSelectionRequest(),
        generated_at=NOW,
        review_account_selection=selection,
        db=db_session,
        current_user_id=user.id,
    )

    assert resolved.summary is not None
    assert resolved.summary.context_source == "account_snapshot"
    assert resolved.summary.context_reference.startswith("ctx_")
    assert str(broker_account.id) not in resolved.summary.context_reference
    assert resolved.summary.label == "Growth Demo Account"
    assert resolved.broker_snapshot.freshness_status == "stale"
    context_payload = asdict(resolved.context)
    assert not find_forbidden_keys(context_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    rendered_context = repr(context_payload).lower()
    assert "provider_account_id_snapshot_secret" not in rendered_context
    assert "provider_connection_id_snapshot_secret" not in rendered_context
    assert "provider_stock_snapshot_secret" not in rendered_context
    assert "quantity" not in rendered_context
    assert "buying_power" not in rendered_context

    captured_sections: list[SavedEvidenceSectionRead] = []
    stock_read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity=Decimal("3"),
            price_assumption=Decimal("50"),
            review_account_selection=selection,
        ),
        generated_at=NOW,
        db=db_session,
        current_user_id=user.id,
        derived_exposure_sections_callback=captured_sections.extend,
    )
    csp_read = build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="cash_secured_put",
            option_leg=_option_leg(option_type="put", leg_action="sell_to_open"),
            review_account_selection=selection,
        ),
        generated_at=NOW,
        db=db_session,
        current_user_id=user.id,
    )

    assert stock_read.portfolio_context is not None
    assert stock_read.portfolio_context.context_source == "account_snapshot"
    assert stock_read.portfolio_context.label == "Growth Demo Account"
    assert stock_read.scope_metadata is not None
    scope = stock_read.scope_metadata.portfolio_context_scope
    assert scope.scope_mode == "single_account"
    assert scope.display_label == "Selected account snapshot"
    assert scope.included_account_labels == ("Selected review account",)
    assert "review_account_scope_membership_unknown" not in scope.caveat_codes
    assert stock_read.scope_metadata.review_account is not None
    assert stock_read.scope_metadata.review_account.display_label == "Growth Demo Account"
    assert stock_read.scope_metadata.review_account.is_included_in_portfolio_scope is True
    assert stock_read.scope_metadata.account_level_feasibility_evaluated is False
    assert stock_read.scope_metadata.scope_summary_label == (
        "Review account selected · Context scope: Selected account snapshot."
    )
    assert repr(stock_read.scope_metadata.model_dump(mode="python")).lower().count("growth demo account") == 1
    assert any("position_market_value_unavailable" in section.caveat_codes for section in captured_sections)
    assert "position_market_value_unavailable" in {caveat.code for caveat in stock_read.caveats}
    assert csp_read.portfolio_context is not None
    assert csp_read.portfolio_context.context_source == "account_snapshot"
    assert "cash_secured_put_collateral_generic" in {caveat.code for caveat in csp_read.caveats}
    rendered_workspace = repr(stock_read.model_dump(mode="python")).lower()
    assert "provider_account_id_snapshot_secret" not in rendered_workspace
    assert "provider_connection_id_snapshot_secret" not in rendered_workspace
    assert "provider_stock_snapshot_secret" not in rendered_workspace
    assert "1234" not in rendered_workspace
    assert not find_forbidden_keys(
        stock_read.model_dump(mode="python"),
        forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS,
    )


def test_selected_account_without_synced_snapshot_returns_unavailable_context(
    db_session,
) -> None:
    user = User(display_name="Fallback User", email="fallback-user@example.com")
    db_session.add(user)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Provider brokerage name should not render",
        provider_connection_id="provider_connection_id_fallback_secret",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(connection)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Synthetic Broker",
        account_type="taxable_individual",
        display_name="Internal fallback account should not render",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="provider_account_id_fallback_secret",
        display_name="Provider account should not render",
        user_nickname="Fallback Demo Account",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(broker_account)
    db_session.commit()

    resolved = _resolve_portfolio_context(
        PortfolioContextSelectionRequest(),
        generated_at=NOW,
        review_account_selection=ReviewAccountSelectionRequest(
            mode="selected_account",
            account_reference=_opaque_account_reference(broker_account.id),
        ),
        db=db_session,
        current_user_id=user.id,
    )

    assert resolved.summary is not None
    assert resolved.account_snapshot_unavailable is True
    assert resolved.summary.context_reference != "ctx_demo_latest"
    assert resolved.summary.context_source == "account_snapshot"
    assert resolved.summary.label == "Account snapshot unavailable"
    assert resolved.summary.cash_state == "unavailable"


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


def test_account_details_contract_separates_scope_from_account_feasibility() -> None:
    read = get_account_details_for_user(
        "11111111-1111-1111-1111-111111111111",
        generated_at=NOW,
    )
    payload = read.model_dump(mode="python")

    assert read.data_mode == "synthetic_demo"
    assert read.privacy_display_mode == "amounts_hidden"
    assert read.portfolio_scope.scope_mode == "all_connected_accounts"
    assert read.portfolio_scope.display_label == "Portfolio scope: All connected accounts"
    assert read.portfolio_scope.account_level_feasibility_evaluated is False
    assert read.review_account is not None
    assert read.review_account.is_review_account is True
    assert read.review_account.is_account_level_feasibility_source is False
    assert len(read.accounts) == 2
    assert read.accounts[0].scope_roles == ("review_account", "included_in_scope")
    assert read.accounts[0].source_kind == "synthetic_demo"
    assert read.accounts[0].source_label == "Synthetic demo"
    assert read.accounts[0].connection_status_label == "Demo connection not active"
    assert read.accounts[0].last_successful_sync_label is None
    assert {caveat.code for caveat in read.readiness_caveats} >= {
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
        "current_position_review_caveated",
    }
    assert {caveat.code for caveat in read.accounts[0].readiness_caveats} >= {
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
    }
    assert any(caveat.title == "Cash is broker-reported" for caveat in read.readiness_caveats)
    assert read.accounts[0].broker_snapshot_freshness.freshness_scope == "broker_snapshot"
    assert read.accounts[0].market_quote_freshness is not None
    assert read.accounts[0].market_quote_freshness.freshness_scope == "market_quote"
    assert read.accounts[0].total_value_label == "Total value hidden · demo not connected"
    assert read.accounts[0].account_level_feasibility_evaluated is False
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_account_details_projection_uses_real_broker_rows_without_raw_private_values() -> None:
    synced_at = datetime(2026, 5, 28, 14, 45, tzinfo=UTC)
    connection = BrokerConnection(
        id=uuid4(),
        user_id=uuid4(),
        provider="snaptrade",
        broker_name="Fidelity raw name should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
        last_successful_sync_at=synced_at,
        raw_metadata={"raw_payload": "raw_metadata_should_not_render"},
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Taxable account ending 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
        last_successful_sync_at=synced_at,
        raw_payload={"positions": [{"symbol": "XYZ", "quantity": "999"}], "cash_balance": "777777"},
    )
    sync_run = BrokerSyncRun(
        id=uuid4(),
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=synced_at,
        completed_at=synced_at,
        provider_request_id="provider_request_id_secret_789",
        accounts_count=1,
        positions_count=6,
        transactions_count=0,
        summary={"stock_positions_count": 4, "option_positions_count": 2},
    )

    read = _account_details_from_broker_rows(
        user_id=connection.user_id,
        generated_at=NOW,
        rows=(
            _BrokerAccountDetailsRow(
                broker_account=broker_account,
                broker_connection=connection,
                latest_sync_run=sync_run,
                metrics=_NormalizedAccountMetrics(
                    cash_total=Decimal("5000.00"),
                    reserved_collateral_cash=Decimal("1500.00"),
                    stock_etf_market_value=Decimal("10000.00"),
                    options_market_value=Decimal("3250.00"),
                    stock_position_count=4,
                    option_position_count=2,
                ),
            ),
        ),
    )

    assert read is not None
    payload = read.model_dump(mode="python")
    assert read.data_mode == "private_real_source"
    assert read.privacy_display_mode == "amounts_visible"
    assert "amounts_hidden" not in read.caveat_codes
    assert "some_amounts_hidden" in read.caveat_codes
    assert read.portfolio_scope.scope_mode == "all_connected_accounts"
    assert read.portfolio_scope.account_level_feasibility_evaluated is False
    assert read.accounts[0].display_label == "Fidelity taxable"
    assert read.portfolio_scope.included_account_labels == ("Fidelity taxable",)
    assert read.accounts[0].source_kind == "snaptrade"
    assert read.accounts[0].source_label == "SnapTrade"
    assert read.accounts[0].connection_status_label == "Connected"
    assert read.accounts[0].last_successful_sync_label == "Last successful sync 2026-05-28 14:45 UTC"
    assert read.accounts[0].privacy_display_mode == "amounts_visible"
    assert read.accounts[0].total_value_label == "Total value hidden in overview"
    assert read.accounts[0].cash_label == "Cash $5,000.00"
    assert read.accounts[0].stock_etf_exposure_label == "Stock/ETF exposure shown as count only"
    assert read.accounts[0].options_exposure_label == "Options exposure shown as count only"
    assert read.accounts[0].collateral_usage_label == "Collateral usage not fully modeled"
    assert "$18,250.00" not in repr(payload)
    assert "$10,000.00" not in repr(payload)
    assert "$3,250.00" not in repr(payload)
    assert "$1,500.00" not in repr(payload)
    assert {caveat.code for caveat in read.readiness_caveats} >= {
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
        "stale_local_rows_possible",
        "current_position_review_caveated",
    }
    assert {caveat.code for caveat in read.accounts[0].readiness_caveats} >= {
        "broker_snapshot_fresh",
        "market_quote_unavailable",
        "some_amounts_hidden",
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
        "stale_local_rows_possible",
        "current_position_review_caveated",
    }
    assert any(
        caveat.message == "Buying power, free cash, and option collateral treatment are not fully modeled yet."
        for caveat in read.accounts[0].readiness_caveats
    )
    assert read.accounts[0].broker_snapshot_freshness.as_of_label == "Last successful sync 2026-05-28 14:45 UTC"
    assert read.accounts[0].market_quote_freshness is not None
    assert read.accounts[0].market_quote_freshness.as_of_label == "Market quotes unavailable"
    assert read.accounts[0].market_quote_freshness.display_label == "Market quotes unavailable"
    assert read.accounts[0].portfolio_shape.stock_position_count == 4
    assert read.accounts[0].portfolio_shape.option_position_count == 2
    assert read.accounts[0].cash_state == "available"
    rendered = repr(payload).lower()
    rendered_values = " ".join(_collect_string_values(payload)).lower()
    assert "demo" not in rendered_values
    assert "not connected" not in rendered_values
    assert "provider_account_id_secret_456" not in rendered
    assert "provider_connection_id_secret_123" not in rendered
    assert "provider_request_id_secret_789" not in rendered
    assert "taxable account ending 1234" not in rendered
    assert "raw_metadata_should_not_render" not in rendered
    assert "777777" not in rendered
    assert "quantity" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_account_details_projection_keeps_private_real_source_amounts_hidden_without_metrics() -> None:
    connection = BrokerConnection(
        id=uuid4(),
        user_id=uuid4(),
        provider="snaptrade",
        broker_name="Webull account 9999 should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="unknown",
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Margin account 9999 should not render",
        account_type="margin",
        sync_status="idle",
        data_freshness_status="unknown",
        raw_payload={"cash_balance": "777777"},
    )

    read = _account_details_from_broker_rows(
        user_id=connection.user_id,
        generated_at=NOW,
        rows=(
            _BrokerAccountDetailsRow(
                broker_account=broker_account,
                broker_connection=connection,
                latest_sync_run=None,
                metrics=_NormalizedAccountMetrics(),
            ),
        ),
    )

    assert read is not None
    payload = read.model_dump(mode="python")
    assert read.data_mode == "private_real_source"
    assert read.privacy_display_mode == "amounts_hidden"
    assert "amounts_hidden" in read.caveat_codes
    assert "some_amounts_hidden" not in read.caveat_codes
    assert read.accounts[0].display_label == "Webull margin"
    assert read.accounts[0].privacy_display_mode == "amounts_hidden"
    assert read.accounts[0].total_value_label == "Total value hidden"
    assert read.accounts[0].cash_label == "Cash amount hidden"
    assert {caveat.code for caveat in read.readiness_caveats} >= {
        "amounts_hidden",
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
    }
    assert {caveat.code for caveat in read.accounts[0].readiness_caveats} >= {
        "amounts_hidden",
        "broker_snapshot_unknown",
        "market_quote_unavailable",
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
    }
    assert read.accounts[0].broker_snapshot_freshness.as_of_label == "Broker snapshot sync time unavailable"
    assert read.accounts[0].broker_snapshot_freshness.display_label == "Broker snapshot freshness unknown"
    assert read.accounts[0].cash_state == "not_exposed"
    rendered_values = " ".join(_collect_string_values(payload)).lower()
    assert "demo" not in rendered_values
    assert "not connected" not in rendered_values
    assert "9999" not in repr(payload)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_selected_account_detail_without_normalized_session_returns_empty_display_rows() -> None:
    connection = BrokerConnection(
        id=uuid4(),
        user_id=uuid4(),
        provider="snaptrade",
        broker_name="Fidelity raw name should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    broker_account = BrokerAccount(
        id=uuid4(),
        account_id=uuid4(),
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Raw taxable account ending 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
        raw_payload={"positions": [{"symbol": "XYZ", "quantity": "999"}]},
    )
    read = _selected_account_details_from_broker_row(
        generated_at=NOW,
        account_reference=_opaque_account_reference(broker_account.id),
        row=_BrokerAccountDetailsRow(
            broker_account=broker_account,
            broker_connection=connection,
            latest_sync_run=None,
            metrics=_NormalizedAccountMetrics(),
        ),
    )

    payload = read.model_dump(mode="python")
    assert read.data_mode == "private_real_source"
    assert read.display_label == "Fidelity taxable"
    assert read.cash_rows == ()
    assert read.equity_position_rows == ()
    assert read.option_position_rows == ()
    assert "normalized_account_session_unavailable" in read.caveat_codes
    assert "purchase_history_unavailable" in read.caveat_codes
    assert "Purchase history unavailable from broker snapshot." in read.limitations
    rendered = repr(payload).lower()
    assert "provider_account_id_secret_456" not in rendered
    assert "provider_connection_id_secret_123" not in rendered
    assert "raw taxable account ending" not in rendered
    assert "quantity" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_latest_stock_positions_by_symbol_keeps_only_first_latest_snapshot() -> None:
    account_id = uuid4()
    newer = StockPosition(
        id=uuid4(),
        account_id=account_id,
        symbol="XYZ",
        asset_type="stock",
        quantity=Decimal("10"),
        market_value=Decimal("500.00"),
        as_of=datetime(2026, 5, 28, 14, 45, tzinfo=UTC),
    )
    older = StockPosition(
        id=uuid4(),
        account_id=account_id,
        symbol="xyz",
        asset_type="stock",
        quantity=Decimal("99"),
        market_value=Decimal("4851.00"),
        as_of=datetime(2026, 5, 27, 14, 45, tzinfo=UTC),
    )

    latest = _latest_stock_positions_by_symbol([newer, older])

    assert latest == [newer]
    assert latest[0].quantity == Decimal("10")
    assert latest[0].market_value == Decimal("500.00")


def test_latest_option_positions_by_contract_keeps_only_first_latest_snapshot() -> None:
    account_id = uuid4()
    contract_id = uuid4()
    newer = OptionPosition(
        id=uuid4(),
        account_id=account_id,
        option_contract_id=contract_id,
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("-210.00"),
        status="open",
        as_of=datetime(2026, 5, 28, 14, 45, tzinfo=UTC),
    )
    older = OptionPosition(
        id=uuid4(),
        account_id=account_id,
        option_contract_id=contract_id,
        position_side="short",
        quantity=Decimal("5"),
        market_value=Decimal("-850.00"),
        status="open",
        as_of=datetime(2026, 5, 27, 14, 45, tzinfo=UTC),
    )

    latest = _latest_option_positions_by_contract([newer, older])

    assert latest == [newer]
    assert latest[0].quantity == Decimal("1")
    assert latest[0].market_value == Decimal("-210.00")


def test_option_position_market_value_uses_multiplier_and_short_sign() -> None:
    contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=contract.id,
        position_side="short",
        quantity=Decimal("1"),
        market_price=Decimal("3.47"),
        market_value=Decimal("-3.47"),
        status="open",
    )

    assert _option_position_market_value(position, contract) == Decimal("-347.00")


def test_option_cost_basis_uses_snaptrade_contract_total_without_double_multiplier() -> None:
    standard_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=standard_contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("200.00"),
        source="snaptrade",
        status="open",
    )

    assert _option_cost_basis(position, standard_contract) == Decimal("200.00")


def test_snaptrade_option_average_cost_displays_per_unit_premium() -> None:
    standard_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    mini_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("10"),
    )
    standard_position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=standard_contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("279.33"),
        source="snaptrade",
        status="open",
    )
    mini_position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=mini_contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("27.90"),
        source="snaptrade",
        status="open",
    )

    assert _option_average_cost_display_value(standard_position, standard_contract) == Decimal("2.7933")
    assert _option_cost_basis(standard_position, standard_contract) == Decimal("279.33")
    assert _option_average_cost_display_value(mini_position, mini_contract) == Decimal("2.79")
    assert _option_cost_basis(mini_position, mini_contract) == Decimal("27.90")


def test_option_cost_basis_uses_multiplier_for_app_owned_per_share_basis() -> None:
    standard_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    mini_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("10"),
    )
    position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=standard_contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("2.00"),
        source="manual",
        status="open",
    )

    assert _option_cost_basis(position, standard_contract) == Decimal("200.00")
    assert _option_cost_basis(position, mini_contract) == Decimal("20.00")
    assert _option_average_cost_display_value(position, standard_contract) == Decimal("2.00")


def test_option_tax_lot_rows_use_snaptrade_contract_total_purchase_price_units() -> None:
    standard_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    mini_contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("10"),
    )
    standard_position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=standard_contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("279.33"),
        source="snaptrade",
        status="open",
        as_of=datetime(2026, 5, 28, 14, 45, tzinfo=UTC),
        tax_lots=(
            {
                "acquired_date": "2026-01-15",
                "quantity": "1",
                "purchase_price": "279.33",
                "cost_basis": "279.33",
                "current_value": "347.00",
            },
        ),
    )
    mini_position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=mini_contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("27.90"),
        source="snaptrade",
        status="open",
        as_of=datetime(2026, 5, 28, 14, 45, tzinfo=UTC),
        tax_lots=(
            {
                "acquired_date": "2026-01-15",
                "quantity": "1",
                "purchase_price": "27.90",
                "cost_basis": "27.90",
                "current_value": "34.70",
            },
        ),
    )

    standard_row = _option_tax_lot_rows(standard_position, standard_contract)[0]
    mini_row = _option_tax_lot_rows(mini_position, mini_contract)[0]

    assert standard_row.purchase_price_label == "$2.79"
    assert standard_row.average_cost_label == "$2.79"
    assert standard_row.cost_basis_label == "$279.33"
    assert standard_row.total_gain_loss_label == "$67.67"
    assert standard_row.gain_loss_percent_label == "24.23%"
    assert mini_row.purchase_price_label == "$2.79"
    assert mini_row.average_cost_label == "$2.79"
    assert mini_row.cost_basis_label == "$27.90"


def test_option_tax_lot_rows_use_multiplier_for_manual_per_share_purchase_price() -> None:
    contract = OptionContract(
        id=uuid4(),
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    position = OptionPosition(
        id=uuid4(),
        account_id=uuid4(),
        option_contract_id=contract.id,
        position_side="long",
        quantity=Decimal("1"),
        average_price=Decimal("2.79"),
        source="manual",
        status="open",
        as_of=datetime(2026, 5, 28, 14, 45, tzinfo=UTC),
        tax_lots=(
            {
                "acquired_date": "2026-01-15",
                "quantity": "1",
                "purchase_price": "2.79",
                "current_value": "347.00",
            },
        ),
    )

    row = _option_tax_lot_rows(position, contract)[0]

    assert row.purchase_price_label == "$2.79"
    assert row.average_cost_label == "$2.79"
    assert row.cost_basis_label == "$279.00"
    assert row.total_gain_loss_label == "$68.00"
    assert row.gain_loss_percent_label == "24.37%"


def test_account_details_projection_marks_mixed_visibility_without_claiming_all_amounts_hidden() -> None:
    user_id = uuid4()
    connection = BrokerConnection(
        id=uuid4(),
        user_id=user_id,
        provider="snaptrade",
        broker_name="Fidelity",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    visible_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_visible",
        display_name="Visible account 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    hidden_account = BrokerAccount(
        id=uuid4(),
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_hidden",
        display_name="Hidden account 9999 should not render",
        account_type="margin",
        sync_status="idle",
        data_freshness_status="fresh",
    )

    read = _account_details_from_broker_rows(
        user_id=user_id,
        generated_at=NOW,
        rows=(
            _BrokerAccountDetailsRow(
                broker_account=visible_account,
                broker_connection=connection,
                latest_sync_run=None,
                metrics=_NormalizedAccountMetrics(
                    cash_total=Decimal("1000.00"),
                    reserved_collateral_cash=Decimal("0.00"),
                    stock_etf_market_value=Decimal("2000.00"),
                    options_market_value=Decimal("0.00"),
                    stock_position_count=1,
                    option_position_count=0,
                ),
            ),
            _BrokerAccountDetailsRow(
                broker_account=hidden_account,
                broker_connection=connection,
                latest_sync_run=None,
                metrics=_NormalizedAccountMetrics(),
            ),
        ),
    )

    assert read is not None
    assert read.privacy_display_mode == "amounts_visible"
    assert "amounts_hidden" not in read.caveat_codes
    assert "some_amounts_hidden" in read.caveat_codes
    assert read.accounts[0].privacy_display_mode == "amounts_visible"
    assert read.accounts[1].privacy_display_mode == "amounts_hidden"
    assert read.accounts[0].display_label == "Fidelity taxable"
    assert read.accounts[1].display_label == "Fidelity margin"
    assert "1234" not in repr(read.model_dump(mode="python"))
    assert "9999" not in repr(read.model_dump(mode="python"))


def test_account_details_empty_state_uses_unavailable_scope() -> None:
    read = get_account_details_for_user(
        "00000000-0000-0000-0000-000000000000",
        generated_at=NOW,
    )

    assert read.data_mode == "synthetic_demo"
    assert read.portfolio_scope.scope_mode == "unavailable"
    assert read.portfolio_scope.account_level_feasibility_evaluated is False
    assert read.review_account is None
    assert read.accounts == ()
    assert "portfolio_scope_unavailable" in read.caveat_codes


def test_selected_account_group_scope_mode_is_reserved_by_schema() -> None:
    scope = PortfolioScopeRead(
        scope_reference="scope_demo_group",
        scope_mode="selected_account_group",
        display_label="Portfolio scope: Selected account group",
        selection_mode=None,
        context_reference=None,
        included_account_labels=("Primary demo account",),
        excluded_account_labels=("Long-term demo account",),
        account_level_feasibility_evaluated=False,
        account_level_feasibility_label="Account-level feasibility not evaluated",
        caveat_codes=("account_group_scope_reserved",),
    )

    assert scope.scope_mode == "selected_account_group"


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


def _real_broker_scope_metadata() -> ReportScopeMetadataRead:
    review_account = ReviewAccountRead(
        account_reference="acctref_realfid01",
        display_label="Fidelity taxable",
        account_kind_label="Taxable brokerage",
        is_review_account=True,
        is_included_in_portfolio_scope=False,
        is_account_level_feasibility_source=False,
    )
    scope = PortfolioScopeRead(
        scope_reference="scope_realbroker1",
        scope_mode="selected_context",
        display_label="Selected portfolio context",
        selection_mode="latest_available",
        context_reference="ctx_demo_latest",
        included_account_labels=(),
        excluded_account_labels=(),
        account_level_feasibility_evaluated=False,
        account_level_feasibility_label="Account-level feasibility not evaluated",
        caveat_codes=(
            "selected_context_scope",
            "account_level_feasibility_not_evaluated",
            "current_position_truth_unstable",
            "buying_power_display_only",
            "cash_collateral_policy_not_reviewed",
            "cash_collateral_not_fully_modeled",
        ),
    )
    return ReportScopeMetadataRead(
        review_account=review_account,
        portfolio_context_scope=scope,
        scope_summary_label="Review account: Fidelity taxable · Context scope: Selected portfolio context.",
        account_level_feasibility_evaluated=False,
        scope_caveat_codes=(
            "selected_context_scope",
            "account_level_feasibility_not_evaluated",
            "current_position_truth_unstable",
            "buying_power_display_only",
            "cash_collateral_policy_not_reviewed",
            "cash_collateral_not_fully_modeled",
        ),
    )


def _collect_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        found: tuple[str, ...] = ()
        for item in value.values():
            found += _collect_string_values(item)
        return found
    if isinstance(value, (list, tuple)):
        found: tuple[str, ...] = ()
        for item in value:
            found += _collect_string_values(item)
        return found
    if isinstance(value, str):
        return (value,)
    return ()
