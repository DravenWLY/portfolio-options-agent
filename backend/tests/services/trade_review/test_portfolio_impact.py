from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.trade_review.context import CashContext, PortfolioReviewContext
from app.services.trade_review.models import OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntentFreshnessSnapshot
from app.services.trade_review.payoff import PayoffScenarioEngine
from app.services.trade_review.portfolio_impact import PortfolioImpactEngine
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot


pytestmark = [pytest.mark.unit]


def _context(*, free_cash: Decimal = Decimal("10000")) -> PortfolioReviewContext:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    return PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=now,
        latest_snapshot_as_of=now,
        total_internal_value=Decimal("25000"),
        data_sources=("manual",),
        data_freshness_statuses=("fresh",),
        cash=CashContext(
            total_cash=free_cash,
            free_cash=free_cash,
            reserved_collateral_cash=Decimal("0"),
            data_freshness_status="fresh",
            as_of=now,
            source="manual",
        ),
        stock_positions=(),
        option_positions=(),
    )


def _market_snapshot() -> TradeReviewMarketSnapshot:
    return TradeReviewMarketSnapshot(report_market_snapshot=None)


def _freshness() -> TradeIntentFreshnessSnapshot:
    return TradeIntentFreshnessSnapshot(broker_portfolio_status="fresh", market_quote_status="fresh")


def test_stock_buy_impact_reduces_projected_free_cash() -> None:
    intent = StockTradeIntent(
        intent_id="stock-impact",
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
    payoff = PayoffScenarioEngine().evaluate(intent)

    impact = PortfolioImpactEngine().calculate(
        intent=intent,
        portfolio_context=_context(),
        market_snapshot=_market_snapshot(),
        payoff=payoff,
    )

    assert impact.cash_delta == Decimal("-200")
    assert impact.projected_free_cash == Decimal("9800")
    assert impact.concentration_symbol == "XYZ"


def test_short_put_impact_tracks_premium_and_collateral_separately() -> None:
    intent = OptionStrategyIntent(
        intent_id="put-impact",
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
    payoff = PayoffScenarioEngine().evaluate(intent)

    impact = PortfolioImpactEngine().calculate(
        intent=intent,
        portfolio_context=_context(),
        market_snapshot=_market_snapshot(),
        payoff=payoff,
    )

    assert impact.premium_cash_delta == Decimal("200")
    assert impact.collateral_delta == Decimal("5000")
    assert impact.projected_free_cash == Decimal("5200")
    assert impact.assignment_share_delta == Decimal("100")
