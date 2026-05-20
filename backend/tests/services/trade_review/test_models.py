from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.trade_review import ETFTradeIntent, OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntentFreshnessSnapshot


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


def test_stock_trade_intent_normalizes_symbol_and_serializes_snapshot() -> None:
    intent = StockTradeIntent(
        **_base_kwargs("stock", "stock_buy"),
        symbol=" hood ",
        action="buy",
        quantity=Decimal("100"),
        price_assumption=Decimal("77.14"),
        assumptions={"reason": "synthetic review"},
    )

    snapshot = intent.to_snapshot_dict()

    assert intent.symbol == "HOOD"
    assert snapshot["user_id"] == str(intent.user_id)
    assert snapshot["quantity"] == "100"
    assert snapshot["price_assumption"] == "77.14"
    assert snapshot["created_at"] == "2026-05-18T15:00:00+00:00"


def test_etf_trade_intent_rejects_wrong_asset_class() -> None:
    with pytest.raises(ValueError, match="asset_class must be etf"):
        ETFTradeIntent(
            **_base_kwargs("stock", "etf_trim"),
            symbol="VOO",
            action="trim",
            quantity=Decimal("1"),
        )


def test_option_strategy_intent_supports_long_call_and_csp_without_strategy_specific_core_tables() -> None:
    csp_kwargs = _base_kwargs("option", "option_strategy")
    csp_kwargs["intent_id"] = "review-2"
    long_call = OptionStrategyIntent(
        **_base_kwargs("option", "option_strategy"),
        strategy_type="long_call",
        underlying_symbol="hood",
        legs=(
            OptionLeg(
                underlying_symbol="HOOD",
                option_type="call",
                leg_action="buy_to_open",
                expiration_date=date(2026, 6, 19),
                strike=Decimal("85"),
                quantity=Decimal("1"),
                premium=Decimal("2.90"),
            ),
        ),
    )
    csp = OptionStrategyIntent(
        **csp_kwargs,
        strategy_type="cash_secured_put",
        underlying_symbol="VOO",
        legs=(
            OptionLeg(
                underlying_symbol="VOO",
                option_type="put",
                leg_action="sell_to_open",
                expiration_date=date(2026, 7, 17),
                strike=Decimal("500"),
                quantity=Decimal("1"),
                premium=Decimal("4.20"),
            ),
        ),
    )

    assert long_call.strategy_type == "long_call"
    assert csp.strategy_type == "cash_secured_put"
    assert long_call.legs[0].requires_manual_review is False


def test_option_strategy_intent_rejects_mismatched_leg_underlying() -> None:
    with pytest.raises(ValueError, match="all option legs must match"):
        OptionStrategyIntent(
            **_base_kwargs("option", "option_strategy"),
            strategy_type="custom_option_strategy",
            underlying_symbol="HOOD",
            legs=(
                OptionLeg(
                    underlying_symbol="QQQ",
                    option_type="call",
                    leg_action="buy_to_open",
                    expiration_date=date(2026, 6, 19),
                    strike=Decimal("500"),
                    quantity=Decimal("1"),
                ),
            ),
        )


def test_unsupported_option_leg_requires_reason() -> None:
    with pytest.raises(ValueError, match="unsupported_reason"):
        OptionLeg(
            underlying_symbol="SPX",
            option_type="call",
            leg_action="buy_to_open",
            expiration_date=date(2026, 6, 19),
            strike=Decimal("5000"),
            quantity=Decimal("1"),
            support_status="unsupported",
        )


def test_trade_intent_rejects_forbidden_assumption_keys() -> None:
    with pytest.raises(ValueError, match="provider_account_id"):
        StockTradeIntent(
            **_base_kwargs("stock", "stock_buy"),
            symbol="VOO",
            action="buy",
            quantity=Decimal("1"),
            price_assumption=Decimal("500"),
            assumptions={"provider_account_id": "forbidden"},
        )


def test_trade_intent_freshness_snapshot_rejects_forbidden_nested_keys() -> None:
    with pytest.raises(ValueError, match="raw_payload"):
        TradeIntentFreshnessSnapshot(
            broker_portfolio_status="cached",
            market_quote_status="manual",
            notes={"nested": {"raw_payload": {"secret": "forbidden"}}},
        )


def test_trade_intent_deep_copies_guarded_assumptions() -> None:
    assumptions = {"nested": {"safe_note": "synthetic"}}
    intent = StockTradeIntent(
        **_base_kwargs("stock", "stock_buy"),
        symbol="VOO",
        action="buy",
        quantity=Decimal("1"),
        price_assumption=Decimal("500"),
        assumptions=assumptions,
    )

    assumptions["nested"]["provider_account_id"] = "forbidden-after-construction"
    snapshot = intent.to_snapshot_dict()

    assert intent.assumptions == {"nested": {"safe_note": "synthetic"}}
    assert "provider_account_id" not in snapshot["assumptions"]["nested"]


def test_trade_intent_freshness_snapshot_deep_copies_guarded_notes() -> None:
    notes = {"nested": {"safe_note": "synthetic"}}
    freshness = TradeIntentFreshnessSnapshot(
        broker_portfolio_status="cached",
        market_quote_status="manual",
        notes=notes,
    )

    notes["nested"]["raw_payload"] = "forbidden-after-construction"

    assert freshness.notes == {"nested": {"safe_note": "synthetic"}}


def test_option_leg_requires_positive_strike() -> None:
    with pytest.raises(ValueError, match="strike must be positive"):
        OptionLeg(
            underlying_symbol="VOO",
            option_type="put",
            leg_action="buy_to_open",
            expiration_date=date(2026, 6, 19),
            strike=Decimal("0"),
            quantity=Decimal("1"),
        )
