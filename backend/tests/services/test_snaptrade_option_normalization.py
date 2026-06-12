from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.option_contract import OptionContract
from app.models.user import User
from app.services.broker_import.providers.snaptrade_models import SnapTradeOptionPositionResponse
from app.services.broker_import.providers.snaptrade_sdk_client import SnapTradeSDKClient
from app.services.broker_import.normalization.options import (
    normalize_option_position,
    option_position_status,
    parse_occ_symbol,
)
from app.services.broker_import.providers.models import ProviderOptionPositionSnapshot, ProviderTaxLotSnapshot


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _create_account(db_session: Session) -> Account:
    user = User(display_name="Option Normalization User")
    db_session.add(user)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Demo Account",
    )
    db_session.add(account)
    db_session.commit()
    return account


def test_parse_occ_symbol_supports_synthetic_snaptrade_option_symbol() -> None:
    parsed = parse_occ_symbol("voo260116p00400000")

    assert parsed.occ_symbol == "VOO260116P00400000"
    assert parsed.underlying_symbol == "VOO"
    assert parsed.expiration_date == date(2026, 1, 16)
    assert parsed.option_type == "put"
    assert parsed.strike == Decimal("400")


def test_option_position_status_marks_future_positive_quantity_as_open() -> None:
    parsed = parse_occ_symbol("VOO270116P00400000")
    provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="VOO270116P00400000",
        underlying_symbol="VOO",
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("210.00"),
        currency="USD",
        sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        received_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    assert option_position_status(parsed, provider_option, current_date=date(2026, 6, 6)) == "open"


def test_option_position_status_marks_expired_or_zero_quantity_as_non_current() -> None:
    expired = parse_occ_symbol("VOO260116P00400000")
    future = parse_occ_symbol("VOO270116P00400000")
    expired_provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="VOO260116P00400000",
        underlying_symbol="VOO",
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("210.00"),
        currency="USD",
        sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        received_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        sync_status="succeeded",
        data_freshness_status="fresh",
    )
    zero_quantity_provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="VOO270116P00400000",
        underlying_symbol="VOO",
        position_side="short",
        quantity=Decimal("0"),
        market_value=Decimal("0.00"),
        currency="USD",
        sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        received_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    assert option_position_status(expired, expired_provider_option, current_date=date(2026, 6, 6)) == "expired"
    assert option_position_status(future, zero_quantity_provider_option, current_date=date(2026, 6, 6)) == "closed"


def test_snaptrade_option_position_normalizes_contract_and_position(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="voo270116p00400000",
        underlying_symbol="voo",
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("-210.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
        raw_payload={"providerOptionId": "demo-option", "userSecret": "test_secret"},
    )

    position = normalize_option_position(db_session, account.id, provider_option)
    db_session.commit()
    contract = db_session.get(OptionContract, position.option_contract_id)

    assert contract is not None
    assert contract.occ_symbol == "VOO270116P00400000"
    assert contract.underlying_symbol == "VOO"
    assert contract.expiration_date == date(2027, 1, 16)
    assert contract.option_type == "put"
    assert contract.strike == Decimal("400.0000")
    assert position.position_side == "short"
    assert position.quantity == Decimal("1")
    assert position.market_price is None
    assert position.market_value == Decimal("-210.00")
    assert position.status == "open"
    assert position.source_ref == "demo-provider-account:VOO270116P00400000"
    assert position.raw_provider_payload == {
        "providerOptionId": "demo-option",
        "userSecret": "[REDACTED]",
    }


def test_snaptrade_sdk_option_mapping_uses_signed_total_contract_market_value(db_session: Session) -> None:
    client = SnapTradeSDKClient(snaptrade=object(), db=db_session, encryption_key="test-key")
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)

    mapped = client._map_option_position(
        {
            "units": "-1",
            "price": "3.47",
            "currency": {"code": "USD"},
            "symbol": {
                "option_symbol": {
                    "ticker": "XYZ260619C00050000",
                    "underlying_symbol": {"symbol": "XYZ"},
                    "option_type": "CALL",
                    "expiration_date": "2026-06-19",
                    "strike_price": "50",
                }
            },
        },
        provider_account_id="demo-provider-account",
        now=timestamp,
    )
    snapshot = SnapTradeOptionPositionResponse(**mapped).to_provider_snapshot()

    assert snapshot.position_side == "short"
    assert snapshot.quantity == Decimal("1")
    assert snapshot.market_value == Decimal("-347.00")
    assert snapshot.market_price == Decimal("3.47")
    assert snapshot.multiplier == Decimal("100")


def test_snaptrade_sdk_option_mapping_uses_mini_option_multiplier(db_session: Session) -> None:
    client = SnapTradeSDKClient(snaptrade=object(), db=db_session, encryption_key="test-key")
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)

    mapped = client._map_option_position(
        {
            "units": "2",
            "price": "3.47",
            "average_purchase_price": "250.00",
            "open_pnl": "194.00",
            "currency": {"code": "USD"},
            "symbol": {
                "option_symbol": {
                    "ticker": "XYZ260619C00050000",
                    "underlying_symbol": {"symbol": "XYZ"},
                    "option_type": "CALL",
                    "expiration_date": "2026-06-19",
                    "strike_price": "50",
                    "is_mini_option": True,
                }
            },
        },
        provider_account_id="demo-provider-account",
        now=timestamp,
    )
    snapshot = SnapTradeOptionPositionResponse(**mapped).to_provider_snapshot()

    assert snapshot.position_side == "long"
    assert snapshot.quantity == Decimal("2")
    assert snapshot.market_value == Decimal("69.40")
    assert snapshot.market_price == Decimal("3.47")
    assert snapshot.average_purchase_price == Decimal("250.00")
    assert snapshot.open_pnl == Decimal("194.00")
    assert snapshot.multiplier == Decimal("10")


def test_snaptrade_sdk_option_mapping_normalizes_tax_lots_without_raw_lot_ids() -> None:
    client = SnapTradeSDKClient(snaptrade=object(), db=object(), encryption_key="test-key")
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)

    mapped = client._map_option_position(
        {
            "units": "1",
            "price": "3.47",
            "average_purchase_price": "279.33",
            "open_pnl": "67.67",
            "currency": {"code": "USD"},
            "tax_lots": [
                {
                    "original_purchase_date": "2026-01-15T00:00:00Z",
                    "quantity": "1",
                    "purchased_price": "279.33",
                    "cost_basis": "279.33",
                    "current_value": "347.00",
                    "position_type": "LONG",
                    "lot_id": "raw_provider_option_lot_id_secret",
                }
            ],
            "symbol": {
                "option_symbol": {
                    "ticker": "XYZ260619C00050000",
                    "underlying_symbol": {"symbol": "XYZ"},
                    "option_type": "CALL",
                    "expiration_date": "2026-06-19",
                    "strike_price": "50",
                }
            },
        },
        provider_account_id="demo-provider-account",
        now=timestamp,
    )
    snapshot = SnapTradeOptionPositionResponse(**mapped).to_provider_snapshot()

    assert snapshot.tax_lots[0].acquired_date == date(2026, 1, 15)
    assert snapshot.tax_lots[0].quantity == Decimal("1")
    assert snapshot.tax_lots[0].purchase_price == Decimal("279.33")
    assert snapshot.tax_lots[0].cost_basis == Decimal("279.33")
    assert snapshot.tax_lots[0].current_value == Decimal("347.00")
    assert "raw_provider_option_lot_id_secret" not in repr(mapped)


def test_snaptrade_option_position_preserves_broker_reported_enrichment_fields(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="XYZ270116C00050000",
        underlying_symbol="XYZ",
        position_side="long",
        quantity=Decimal("2"),
        market_value=Decimal("694.00"),
        currency="USD",
        market_price=Decimal("3.47"),
        average_purchase_price=Decimal("250.00"),
        open_pnl=Decimal("194.00"),
        multiplier=Decimal("100"),
        tax_lots=(
            ProviderTaxLotSnapshot(
                acquired_date=date(2026, 1, 15),
                quantity=Decimal("2"),
                purchase_price=Decimal("250.00"),
                cost_basis=Decimal("500.00"),
                current_value=Decimal("694.00"),
                position_type="long",
            ),
        ),
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    position = normalize_option_position(db_session, account.id, provider_option)
    contract = db_session.get(OptionContract, position.option_contract_id)

    assert contract is not None
    assert contract.multiplier == Decimal("100.00")
    assert position.market_price == Decimal("3.47")
    assert position.average_price == Decimal("250.00")
    assert position.open_pnl == Decimal("194.00")
    assert position.currency == "USD"
    assert position.tax_lots == [
        {
            "acquired_date": "2026-01-15",
            "quantity": "2",
            "purchase_price": "250.00",
            "cost_basis": "500.00",
            "current_value": "694.00",
            "position_type": "long",
        }
    ]


def test_snaptrade_option_contract_resolution_is_idempotent(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="VOO270116P00400000",
        underlying_symbol="VOO",
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("210.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    first = normalize_option_position(db_session, account.id, provider_option)
    second = normalize_option_position(db_session, account.id, provider_option)

    assert first.id == second.id
    assert first.option_contract_id == second.option_contract_id
