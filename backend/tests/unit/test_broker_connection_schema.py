import pytest
from pydantic import ValidationError

from app.schemas.broker_connection import BrokerConnectionCreate


pytestmark = pytest.mark.unit


def test_broker_connection_create_normalizes_provider_and_strings() -> None:
    payload = BrokerConnectionCreate(
        provider="SNAPTRADE",
        broker_name=" Demo Fidelity ",
        provider_connection_id=" demo-connection-001 ",
        connection_status="connected",
        sync_status="succeeded",
        data_freshness_status="fresh",
        secret_ref="secret://snaptrade/demo-user",
        scopes=["read_accounts", "read_holdings"],
        raw_metadata={"environment": "synthetic"},
    )

    assert payload.provider == "snaptrade"
    assert payload.broker_name == "Demo Fidelity"
    assert payload.provider_connection_id == "demo-connection-001"
    assert payload.secret_ref == "secret://snaptrade/demo-user"
    assert payload.scopes == ["read_accounts", "read_holdings"]
    assert payload.raw_metadata == {"environment": "synthetic"}


def test_broker_connection_create_rejects_plaintext_secret_like_reference() -> None:
    with pytest.raises(ValidationError):
        BrokerConnectionCreate(
            broker_name="Demo Fidelity",
            provider_connection_id="demo-connection-001",
            secret_ref="token=do-not-store-this",
        )


def test_broker_connection_create_rejects_unknown_provider() -> None:
    with pytest.raises(ValidationError):
        BrokerConnectionCreate(
            provider="unsupported_provider",
            broker_name="Demo Fidelity",
            provider_connection_id="demo-connection-001",
        )
