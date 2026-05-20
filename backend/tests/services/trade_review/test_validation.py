from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.trade_review import OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntentFreshnessSnapshot, TradeIntentValidator


pytestmark = [pytest.mark.unit]


def _base_kwargs(asset_class: str, intent_type: str) -> dict:
    return {
        "intent_id": "review-1",
        "user_id": uuid4(),
        "account_id": uuid4(),
        "asset_class": asset_class,
        "intent_type": intent_type,
        "created_at": datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        "calculation_version": "trade-review-v1",
        "data_freshness_snapshot": TradeIntentFreshnessSnapshot(
            broker_portfolio_status="cached",
            market_quote_status="manual",
        ),
    }


def test_validator_warns_when_stock_price_assumption_is_missing() -> None:
    intent = StockTradeIntent(
        **_base_kwargs("stock", "stock_buy"),
        symbol="VOO",
        action="buy",
        quantity=Decimal("1"),
    )

    result = TradeIntentValidator().validate(intent)

    assert result.blocked is False
    assert result.manual_review_required is True
    assert result.highest_severity == "warning"
    assert result.is_clean is False
    assert result.can_reach_deterministic_review is True
    assert result.findings[0].code == "price_assumption_missing"
    assert result.findings[0].severity == "warning"


def test_validator_blocks_strategy_shape_mismatch() -> None:
    intent = OptionStrategyIntent(
        **_base_kwargs("option", "option_strategy"),
        strategy_type="long_call",
        underlying_symbol="HOOD",
        legs=(
            OptionLeg(
                underlying_symbol="HOOD",
                option_type="put",
                leg_action="sell_to_open",
                expiration_date=date(2026, 6, 19),
                strike=Decimal("70"),
                quantity=Decimal("1"),
                premium=Decimal("2.00"),
            ),
        ),
    )

    result = TradeIntentValidator().validate(intent, today=date(2026, 5, 18))

    assert result.blocked is True
    assert result.highest_severity == "blocker"
    assert result.is_clean is False
    assert any(finding.code == "strategy_shape_mismatch" for finding in result.findings)


def test_validator_blocks_expired_option_leg() -> None:
    intent = OptionStrategyIntent(
        **_base_kwargs("option", "option_strategy"),
        strategy_type="long_put",
        underlying_symbol="QQQ",
        legs=(
            OptionLeg(
                underlying_symbol="QQQ",
                option_type="put",
                leg_action="buy_to_open",
                expiration_date=date(2026, 5, 18),
                strike=Decimal("500"),
                quantity=Decimal("1"),
                premium=Decimal("3.50"),
            ),
        ),
    )

    result = TradeIntentValidator().validate(intent, today=date(2026, 5, 18))

    assert result.can_reach_deterministic_review is False
    assert any(finding.code == "expiration_not_future" for finding in result.findings)


def test_validator_marks_manual_review_contract_as_warning() -> None:
    intent = OptionStrategyIntent(
        **_base_kwargs("option", "option_strategy"),
        strategy_type="custom_option_strategy",
        underlying_symbol="SPX",
        legs=(
            OptionLeg(
                underlying_symbol="SPX",
                option_type="call",
                leg_action="buy_to_open",
                expiration_date=date(2026, 6, 19),
                strike=Decimal("5000"),
                quantity=Decimal("1"),
                premium=Decimal("10"),
                support_status="manual_review_required",
            ),
        ),
    )

    result = TradeIntentValidator().validate(intent, today=date(2026, 5, 18))

    assert result.blocked is False
    assert result.manual_review_required is True
    assert any(finding.code == "option_contract_manual_review_required" for finding in result.findings)


def test_validator_marks_fully_specified_stock_intent_clean() -> None:
    intent = StockTradeIntent(
        **_base_kwargs("stock", "stock_buy"),
        symbol="VOO",
        action="buy",
        quantity=Decimal("1"),
        price_assumption=Decimal("500"),
    )

    result = TradeIntentValidator().validate(intent)

    assert result.findings == ()
    assert result.highest_severity is None
    assert result.is_clean is True
    assert result.manual_review_required is False
    assert result.can_reach_deterministic_review is True
