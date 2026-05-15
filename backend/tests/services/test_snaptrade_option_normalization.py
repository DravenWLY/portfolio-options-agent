from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.option_contract import OptionContract
from app.models.user import User
from app.services.broker_import.normalization.options import normalize_option_position, parse_occ_symbol
from app.services.broker_import.providers.models import ProviderOptionPositionSnapshot


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


def test_snaptrade_option_position_normalizes_contract_and_position(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="voo260116p00400000",
        underlying_symbol="voo",
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("210.00"),
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
    assert contract.occ_symbol == "VOO260116P00400000"
    assert contract.underlying_symbol == "VOO"
    assert contract.expiration_date == date(2026, 1, 16)
    assert contract.option_type == "put"
    assert contract.strike == Decimal("400.0000")
    assert position.position_side == "short"
    assert position.quantity == Decimal("1")
    assert position.market_price is None
    assert position.market_value == Decimal("210.00")
    assert position.status == "open"
    assert position.source_ref == "demo-provider-account:VOO260116P00400000"
    assert position.raw_provider_payload == {
        "providerOptionId": "demo-option",
        "userSecret": "[REDACTED]",
    }


def test_snaptrade_option_contract_resolution_is_idempotent(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_option = ProviderOptionPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        occ_symbol="VOO260116P00400000",
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
