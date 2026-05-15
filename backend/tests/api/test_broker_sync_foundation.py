import pytest
from fastapi.testclient import TestClient

from app.schemas.provider_credentials_metadata import ProviderCredentialsMetadataCreate


pytestmark = [pytest.mark.api, pytest.mark.smoke]


def test_openapi_does_not_expose_secret_reference_fields(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_text = response.text
    assert "secret_ref" not in openapi_text
    assert "encrypted_secret_ref" not in openapi_text


def test_broker_sync_foundation_uses_fake_secret_references_only() -> None:
    payload = ProviderCredentialsMetadataCreate(
        provider="snaptrade",
        credential_name="Synthetic SnapTrade User Secret",
        secret_ref="secret://snaptrade/synthetic-user",
        scopes=["read_accounts", "read_holdings"],
    )

    assert payload.secret_ref == "secret://snaptrade/synthetic-user"
    assert "real" not in payload.secret_ref.lower()
    assert "token=" not in payload.secret_ref.lower()
