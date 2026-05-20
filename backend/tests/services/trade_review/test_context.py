from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.cash_balance import CashBalanceRead
from app.schemas.option_position import OptionPositionRead
from app.schemas.portfolio import PortfolioSummaryRead
from app.schemas.stock_position import StockPositionRead
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review import CashContext, OptionPositionContext, PortfolioContextBuilder, PortfolioReviewContext, StockPositionContext


pytestmark = [pytest.mark.unit]


def test_portfolio_context_builder_omits_provider_raw_payloads_and_account_numbers() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    user_id = uuid4()
    account_id = uuid4()
    summary = PortfolioSummaryRead(
        account_id=account_id,
        as_of=now,
        cash_as_of=now,
        stock_positions_as_of=now,
        option_positions_as_of=now,
        latest_snapshot_as_of=now,
        total_cash=Decimal("10000"),
        stock_position_count=1,
        stock_market_value=Decimal("4500"),
        option_position_count=1,
        long_option_position_count=0,
        short_option_position_count=1,
        option_market_value=Decimal("-210"),
        total_internal_value=Decimal("14290"),
        data_sources=["snaptrade"],
        data_freshness_statuses=["cached"],
        broker_data_warnings=[],
    )
    cash = CashBalanceRead(
        id=uuid4(),
        account_id=account_id,
        total_cash=Decimal("10000"),
        reserved_collateral_cash=Decimal("0"),
        free_cash=Decimal("10000"),
        premium_income_cash=Decimal("0"),
        dca_cash=Decimal("0"),
        source="snaptrade",
        source_ref="internal-source-ref",
        data_freshness_status="cached",
        as_of=now,
        created_at=now,
    )
    stock = StockPositionRead(
        id=uuid4(),
        account_id=account_id,
        symbol="VOO",
        asset_type="etf",
        quantity=Decimal("10"),
        cost_basis=None,
        market_price=None,
        market_value=Decimal("4500"),
        source="snaptrade",
        source_ref="provider-ref-not-forwarded",
        data_freshness_status="cached",
        raw_provider_payload={"provider_account_id": "should-not-forward"},
        as_of=now,
        created_at=now,
        updated_at=now,
    )
    option = OptionPositionRead(
        id=uuid4(),
        account_id=account_id,
        option_contract_id=uuid4(),
        position_side="short",
        quantity=Decimal("1"),
        average_price=Decimal("2.10"),
        market_price=None,
        market_value=Decimal("210"),
        status="open",
        source="snaptrade",
        source_ref="provider-ref-not-forwarded",
        data_freshness_status="cached",
        raw_provider_payload={"raw_payload": "should-not-forward"},
        as_of=now,
        opened_at=None,
        closed_at=None,
        created_at=now,
        updated_at=now,
    )

    context = PortfolioContextBuilder().build(
        user_id=user_id,
        summary=summary,
        cash_balance=cash,
        stock_positions=(stock,),
        option_positions=(option,),
    )

    assert context.user_id == user_id
    assert context.account_id == account_id
    assert context.cash is not None
    assert context.stock_positions[0].symbol == "VOO"
    assert context.option_positions[0].position_side == "short"
    rendered = repr(context)
    assert "provider_account_id" not in rendered
    assert "raw_payload" not in rendered
    assert "source_ref" not in rendered


def test_portfolio_context_dataclasses_are_structurally_disjoint_from_forbidden_private_fields() -> None:
    forbidden = (FORBIDDEN_REPORT_FACT_KEYS - {"account_id", "total_cash", "available_cash"}) | {
        "account_number",
        "broker_account_number",
        "source_ref",
        "raw_provider_payload",
    }

    for context_type in (CashContext, StockPositionContext, OptionPositionContext, PortfolioReviewContext):
        field_names = {field.name for field in fields(context_type)}
        assert field_names.isdisjoint(forbidden), context_type.__name__
