from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.trade_review.models import OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntentFreshnessSnapshot
from app.services.trade_review.payoff import PayoffScenarioEngine, PriceScenario


pytestmark = [pytest.mark.unit]


def _freshness() -> TradeIntentFreshnessSnapshot:
    return TradeIntentFreshnessSnapshot(broker_portfolio_status="fresh", market_quote_status="fresh")


def test_stock_buy_payoff_uses_price_assumption_without_recommendation() -> None:
    intent = StockTradeIntent(
        intent_id="stock-buy-1",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="stock",
        intent_type="stock_buy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=_freshness(),
        symbol="XYZ",
        action="buy",
        quantity=Decimal("10"),
        price_assumption=Decimal("20"),
    )

    review = PayoffScenarioEngine().evaluate(
        intent,
        scenarios=(PriceScenario("up", Decimal("22")),),
    )

    assert review.points[0].net_cash_flow == Decimal("-200")
    assert review.points[0].scenario_pnl == Decimal("20")
    assert "recommend" not in " ".join(review.calculation_notes).lower()


def test_short_put_payoff_receives_credit_and_loses_when_underlying_falls() -> None:
    intent = OptionStrategyIntent(
        intent_id="put-1",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="option",
        intent_type="option_strategy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=_freshness(),
        strategy_type="cash_secured_put",
        underlying_symbol="XYZ",
        legs=(
            OptionLeg(
                underlying_symbol="XYZ",
                option_type="put",
                leg_action="sell_to_open",
                expiration_date=date(2026, 6, 19),
                strike=Decimal("50"),
                quantity=Decimal("1"),
                premium=Decimal("2"),
            ),
        ),
    )

    review = PayoffScenarioEngine().evaluate(
        intent,
        scenarios=(PriceScenario("down", Decimal("45")), PriceScenario("up", Decimal("55"))),
    )

    assert review.points[0].net_cash_flow == Decimal("200")
    assert review.points[0].scenario_pnl == Decimal("-300")
    assert review.points[1].scenario_pnl == Decimal("200")
    assert review.max_loss == Decimal("4800")
    assert review.max_gain == Decimal("200")


def test_long_call_payoff_caps_loss_at_debit_for_zero_intrinsic_scenario() -> None:
    intent = OptionStrategyIntent(
        intent_id="call-1",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="option",
        intent_type="option_strategy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=_freshness(),
        strategy_type="long_call",
        underlying_symbol="XYZ",
        legs=(
            OptionLeg(
                underlying_symbol="XYZ",
                option_type="call",
                leg_action="buy_to_open",
                expiration_date=date(2026, 6, 19),
                strike=Decimal("50"),
                quantity=Decimal("1"),
                premium=Decimal("3"),
            ),
        ),
    )

    review = PayoffScenarioEngine().evaluate(intent, scenarios=(PriceScenario("below", Decimal("45")),))

    assert review.points[0].net_cash_flow == Decimal("-300")
    assert review.points[0].scenario_pnl == Decimal("-300")
    assert review.max_loss == Decimal("300")
    assert review.max_gain is None
