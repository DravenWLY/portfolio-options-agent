from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.agent_team.llm_clients.contracts import find_secret_like_values
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports.display_labels import find_internal_display_tokens
from app.services.trade_review.context import (
    CashContext,
    OptionPositionContext,
    PortfolioReviewContext,
    StockPositionContext,
)
from app.services.trade_review.exposure_adapter import (
    build_exposure_evidence_sections,
    proposed_equity_trade_from_intent,
    reviewed_exposure_snapshot_from_context,
)
from app.services.trade_review.exposure_engine import (
    ClassificationExecutionContext,
    CompanyClassificationUnavailable,
)
from app.services.trade_review.models import (
    OptionLeg,
    OptionStrategyIntent,
    StockTradeIntent,
    TradeIntentFreshnessSnapshot,
)

pytestmark = [pytest.mark.unit]


class _FakeProfileClient:
    def __init__(self, rows: dict[str, dict[str, str]]) -> None:
        self.rows = rows
        self.calls: list[str] = []

    def fetch_company_profile(self, *, symbol: str):
        self.calls.append(symbol)
        row = self.rows.get(symbol)
        if row is None:
            raise CompanyClassificationUnavailable("missing")
        return row


def test_adapter_builds_display_only_exposure_sections_from_reviewed_context() -> None:
    context = _portfolio_context(
        cash=Decimal("12000"),
        stock_positions=(
            _stock("SMH", "etf", Decimal("35000")),
            _stock("VTI", "etf", Decimal("40000")),
            _stock("AAPL", "stock", Decimal("13000")),
        ),
    )
    intent = _stock_intent(symbol="NVDA", quantity=Decimal("40"), price=Decimal("175"))
    classification_context = ClassificationExecutionContext(
        client=_FakeProfileClient(
            {
                "AAPL": {"sector": "Technology", "industry": "Consumer Electronics"},
                "NVDA": {"sector": "Technology", "industry": "Semiconductors"},
            }
        ),
        live_enabled=True,
    )

    before_after, concentration = build_exposure_evidence_sections(
        portfolio_context=context,
        intent=intent,
        classification_context=classification_context,
    )

    assert before_after.section_key == "before_after_portfolio_impact"
    assert before_after.availability == "available"
    assert before_after.trade_impact_narrative_groups is not None
    assert before_after.trade_impact_narrative_groups.proceed_statements
    assert before_after.trade_impact_narrative_groups.not_reviewed_statement is not None
    assert before_after.trade_impact_narrative_groups.verify_statement is not None
    assert concentration.section_key == "concentration_risk_drift"
    assert concentration.availability == "available"
    rendered = "\n".join(
        (
            before_after.summary_label or "",
            *before_after.detail_labels,
            concentration.summary_label or "",
            *concentration.detail_labels,
        )
    )
    assert "This purchase ($7,000 at the reviewed price basis)" in rendered
    assert "NVDA | $0 | 0.0% | +$7,000 | $7,000 | 7.0%." in rendered
    assert "provider_account" not in rendered.lower()
    assert _safe_section_payload(before_after)
    assert _safe_section_payload(concentration)


def test_adapter_caveats_missing_market_values_and_buckets_options_without_raw_rows() -> None:
    context = _portfolio_context(
        cash=Decimal("25000"),
        stock_positions=(
            _stock("SOXX", "etf", Decimal("30000")),
            _stock("MSFT", "stock", None),
        ),
        option_positions=(
            _option(Decimal("1250")),
            _option(None),
        ),
    )
    snapshot, caveats = reviewed_exposure_snapshot_from_context(context)

    assert snapshot.cash_value == Decimal("25000")
    assert tuple(position.symbol for position in snapshot.positions) == ("SOXX", "OPTIONS")
    assert "position_market_value_unavailable" in caveats
    assert "options_exposure_bucketed" in caveats

    before_after, concentration = build_exposure_evidence_sections(
        portfolio_context=context,
        intent=_stock_intent(symbol="AMD", quantity=Decimal("50"), price=Decimal("100")),
        classification_context=ClassificationExecutionContext(
            client=_FakeProfileClient({"AMD": {"sector": "Technology", "industry": "Semiconductors"}}),
            live_enabled=True,
        ),
    )

    assert before_after.availability == "limited"
    assert concentration.availability == "limited"
    assert "position_market_value_unavailable" in before_after.caveat_codes
    assert "options_exposure_bucketed" in before_after.caveat_codes
    prose = " ".join((*before_after.detail_labels, *concentration.detail_labels))
    assert "Options positions were treated as one options asset-class bucket" in prose
    assert "option_contract_id" not in repr((before_after.model_dump(mode="python"), concentration.model_dump(mode="python")))
    assert _safe_section_payload(before_after)
    assert _safe_section_payload(concentration)


def test_adapter_reclassifies_core_money_market_position_before_freezing_display_sections() -> None:
    before_after, concentration = build_exposure_evidence_sections(
        portfolio_context=_portfolio_context(
            cash=Decimal("100"),
            stock_positions=(
                _stock("SPAXX", "etf", Decimal("100")),
                _stock("SOXX", "etf", Decimal("900")),
            ),
        ),
        intent=_stock_intent(symbol="NVDA", quantity=Decimal("1"), price=Decimal("10")),
        classification_context=ClassificationExecutionContext(
            client=_FakeProfileClient({"NVDA": {"sector": "Technology", "industry": "Semiconductors"}}),
            live_enabled=True,
        ),
    )

    rendered = "\n".join((*before_after.detail_labels, *concentration.detail_labels))
    assert "money_market_core_treated_as_cash" in before_after.caveat_codes
    assert "money_market_core_treated_as_cash" in concentration.caveat_codes
    assert "Cash includes the money market core position (SPAXX)." in rendered
    assert "SPAXX |" not in rendered
    assert _safe_section_payload(before_after)
    assert _safe_section_payload(concentration)


def test_adapter_degrades_option_trade_intent_without_engine_failure() -> None:
    before_after, concentration = build_exposure_evidence_sections(
        portfolio_context=_portfolio_context(cash=Decimal("50000")),
        intent=_option_intent(),
    )

    assert before_after.availability == "not_available"
    assert concentration.availability == "not_available"
    assert before_after.caveat_codes == ("trade_impact_not_available",)
    assert concentration.caveat_codes == ("trade_impact_not_available",)
    assert _safe_section_payload(before_after)
    assert _safe_section_payload(concentration)


def test_adapter_rejects_non_buy_equity_trade_for_purchase_impact() -> None:
    intent = _stock_intent(symbol="NVDA", quantity=Decimal("10"), price=Decimal("175"), action="trim")

    with pytest.raises(ValueError):
        proposed_equity_trade_from_intent(intent)


def _safe_section_payload(section) -> bool:
    payload = section.model_dump(mode="python")
    groups = payload.get("trade_impact_narrative_groups") or {}
    prose = " ".join(
        str(value)
        for value in (
            payload.get("section_label"),
            payload.get("summary_label"),
            *(payload.get("detail_labels") or ()),
            *(groups.get("proceed_statements") or ()),
            groups.get("not_reviewed_statement"),
            groups.get("verify_statement"),
        )
        if value
    )
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_secret_like_values(payload)
    assert not find_internal_display_tokens(prose)
    return True


def _portfolio_context(
    *,
    cash: Decimal | None,
    stock_positions: tuple[StockPositionContext, ...] = (),
    option_positions: tuple[OptionPositionContext, ...] = (),
) -> PortfolioReviewContext:
    generated = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
    return PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=generated,
        latest_snapshot_as_of=generated,
        total_internal_value=Decimal("100000"),
        data_sources=("synthetic_test",),
        data_freshness_statuses=("fresh",),
        cash=(
            None
            if cash is None
            else CashContext(
                total_cash=cash,
                free_cash=cash,
                reserved_collateral_cash=Decimal("0"),
                data_freshness_status="fresh",
                as_of=generated,
                source="synthetic_test",
            )
        ),
        stock_positions=stock_positions,
        option_positions=option_positions,
    )


def _stock(symbol: str, asset_type: str, market_value: Decimal | None) -> StockPositionContext:
    generated = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
    return StockPositionContext(
        symbol=symbol,
        asset_type=asset_type,
        quantity=Decimal("1"),
        market_value=market_value,
        data_freshness_status="fresh",
        as_of=generated,
        source="synthetic_test",
    )


def _option(market_value: Decimal | None) -> OptionPositionContext:
    generated = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
    return OptionPositionContext(
        option_contract_id=uuid4(),
        position_side="long",
        quantity=Decimal("1"),
        market_value=market_value,
        status="open",
        data_freshness_status="fresh",
        as_of=generated,
        source="synthetic_test",
    )


def _stock_intent(
    *,
    symbol: str,
    quantity: Decimal,
    price: Decimal,
    action: str = "buy",
) -> StockTradeIntent:
    generated = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
    return StockTradeIntent(
        intent_id=f"intent-{symbol.lower()}",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="stock",
        intent_type="stock_buy" if action == "buy" else "stock_sell_trim",
        created_at=generated,
        calculation_version="test-v1",
        data_freshness_snapshot=TradeIntentFreshnessSnapshot(
            broker_portfolio_status="fresh",
            market_quote_status="fresh",
        ),
        symbol=symbol,
        action=action,
        quantity=quantity,
        price_assumption=price,
    )


def _option_intent() -> OptionStrategyIntent:
    generated = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
    return OptionStrategyIntent(
        intent_id="intent-csp",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="option",
        intent_type="option_strategy",
        created_at=generated,
        calculation_version="test-v1",
        data_freshness_snapshot=TradeIntentFreshnessSnapshot(
            broker_portfolio_status="fresh",
            market_quote_status="fresh",
        ),
        strategy_type="cash_secured_put",
        underlying_symbol="NVDA",
        legs=(
            OptionLeg(
                underlying_symbol="NVDA",
                option_type="put",
                leg_action="sell_to_open",
                expiration_date=date(2026, 9, 18),
                strike=Decimal("150"),
                quantity=Decimal("1"),
                premium=Decimal("2.50"),
            ),
        ),
    )
