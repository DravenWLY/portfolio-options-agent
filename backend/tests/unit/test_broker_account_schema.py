from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.broker_account import BrokerAccountCreate


pytestmark = pytest.mark.unit


def test_broker_account_create_normalizes_strings_and_currency() -> None:
    payload = BrokerAccountCreate(
        broker_connection_id=uuid4(),
        account_id=uuid4(),
        provider_account_id=" provider-account-001 ",
        display_name=" Demo Brokerage Account ",
        account_type="taxable_individual",
        base_currency="usd",
        sync_status="succeeded",
        data_freshness_status="fresh",
        raw_payload={"provider": "snaptrade", "sample": True},
    )

    assert payload.provider_account_id == "provider-account-001"
    assert payload.display_name == "Demo Brokerage Account"
    assert payload.base_currency == "USD"
    assert payload.raw_payload == {"provider": "snaptrade", "sample": True}


def test_broker_account_create_allows_unmapped_internal_account() -> None:
    payload = BrokerAccountCreate(
        broker_connection_id=uuid4(),
        provider_account_id="provider-account-001",
        display_name="Demo Brokerage Account",
    )

    assert payload.account_id is None
    assert payload.account_type == "other"
    assert payload.sync_status == "idle"
    assert payload.data_freshness_status == "unknown"


def test_broker_account_create_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        BrokerAccountCreate(
            broker_connection_id=uuid4(),
            provider_account_id="provider-account-001",
            display_name="Demo Brokerage Account",
            data_freshness_status="probably_fresh",
        )
