import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.provider_credentials_metadata import ProviderCredentialsMetadataCreate


pytestmark = [pytest.mark.api, pytest.mark.smoke]


def test_openapi_does_not_expose_secret_reference_fields(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    forbidden = {"secret_ref", "encrypted_secret_ref", "secretRef", "encryptedSecretRef", "user_secret", "userSecret"}

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                assert key not in forbidden
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            assert value not in forbidden

    walk(response.json())


def test_broker_sync_foundation_uses_fake_secret_references_only() -> None:
    payload = ProviderCredentialsMetadataCreate(
        provider="snaptrade",
        credential_name="Synthetic SnapTrade User Secret",
        secret_ref="secret://snaptrade/synthetic-user",
        scopes=["read_accounts", "read_holdings"],
    )

    assert payload.secret_ref == "secret://snaptrade/synthetic-user"


def test_broker_sync_foundation_rejects_uuid_shaped_secret_ref() -> None:
    with pytest.raises(ValidationError):
        ProviderCredentialsMetadataCreate(
            provider="snaptrade",
            credential_name="Synthetic SnapTrade User Secret",
            secret_ref="11111111-1111-4111-8111-111111111111",
            scopes=["read_accounts", "read_holdings"],
        )
