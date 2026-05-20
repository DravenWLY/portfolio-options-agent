from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.strategies import (
    CashSecuredPutEvaluator,
    CoveredCallEvaluator,
    ETFReviewEvaluator,
    LongCallReviewEvaluator,
    LongPutReviewEvaluator,
    StockBuyReviewEvaluator,
    StockSellTrimReviewEvaluator,
)
from app.services.trade_review.context import CashContext, PortfolioReviewContext
from app.services.trade_review.models import ETFTradeIntent, OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntentFreshnessSnapshot
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot


pytestmark = [pytest.mark.unit]


def _context() -> PortfolioReviewContext:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    return PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=now,
        latest_snapshot_as_of=now,
        total_internal_value=Decimal("10000"),
        data_sources=("manual",),
        data_freshness_statuses=("fresh",),
        cash=CashContext(
            total_cash=Decimal("10000"),
            free_cash=Decimal("10000"),
            reserved_collateral_cash=Decimal("0"),
            data_freshness_status="fresh",
            as_of=now,
            source="manual",
        ),
        stock_positions=(),
        option_positions=(),
    )


def _freshness() -> TradeIntentFreshnessSnapshot:
    return TradeIntentFreshnessSnapshot(broker_portfolio_status="fresh", market_quote_status="fresh")


def _stock(action: str = "buy") -> StockTradeIntent:
    return StockTradeIntent(
        intent_id=f"stock-{action}",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="stock",
        intent_type=f"stock_{action}",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=_freshness(),
        symbol="XYZ",
        action=action,  # type: ignore[arg-type]
        quantity=Decimal("1"),
        price_assumption=Decimal("20"),
    )


def _etf() -> ETFTradeIntent:
    return ETFTradeIntent(
        intent_id="etf-buy",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="etf",
        intent_type="etf_buy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=_freshness(),
        symbol="VOO",
        action="buy",
        quantity=Decimal("1"),
        price_assumption=Decimal("500"),
    )


def _option(strategy_type: str, leg_action: str, option_type: str) -> OptionStrategyIntent:
    return OptionStrategyIntent(
        intent_id=f"option-{strategy_type}",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="option",
        intent_type="option_strategy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=_freshness(),
        strategy_type=strategy_type,  # type: ignore[arg-type]
        underlying_symbol="XYZ",
        legs=(
            OptionLeg(
                underlying_symbol="XYZ",
                option_type=option_type,  # type: ignore[arg-type]
                leg_action=leg_action,  # type: ignore[arg-type]
                expiration_date=date(2026, 6, 19),
                strike=Decimal("50"),
                quantity=Decimal("1"),
                premium=Decimal("2"),
            ),
        ),
    )


@pytest.mark.parametrize(
    ("evaluator", "intent"),
    (
        (StockBuyReviewEvaluator(), _stock("buy")),
        (StockSellTrimReviewEvaluator(), _stock("trim")),
        (ETFReviewEvaluator(), _etf()),
        (LongCallReviewEvaluator(), _option("long_call", "buy_to_open", "call")),
        (LongPutReviewEvaluator(), _option("long_put", "buy_to_open", "put")),
        (CashSecuredPutEvaluator(), _option("cash_secured_put", "sell_to_open", "put")),
        (CoveredCallEvaluator(), _option("covered_call", "sell_to_open", "call")),
    ),
)
def test_strategy_wrappers_share_generic_trade_review_pipeline(evaluator, intent) -> None:
    review = evaluator.evaluate(
        intent,
        _context(),
        TradeReviewMarketSnapshot(report_market_snapshot=None),
        generated_at=datetime(2026, 5, 18, 15, 5, tzinfo=UTC),
    )

    assert review.intent is intent
    assert review.payoff.points
    assert review.report.markdown.startswith("# Deterministic Trade Review")
    assert "wheel" not in review.report.markdown.lower()


def test_strategy_wrapper_rejects_wrong_intent_shape() -> None:
    with pytest.raises(ValueError, match="stock buy"):
        StockBuyReviewEvaluator().evaluate(
            _stock("trim"),
            _context(),
            TradeReviewMarketSnapshot(report_market_snapshot=None),
        )
