from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.provider_credentials_metadata import (
    ProviderCredentialsMetadataCreate,
    ProviderCredentialsMetadataInternalRead,
    ProviderCredentialsMetadataRead,
)


pytestmark = pytest.mark.unit


def test_provider_credentials_metadata_create_normalizes_provider_and_name() -> None:
    payload = ProviderCredentialsMetadataCreate(
        user_id=uuid4(),
        provider="SNAPTRADE",
        credential_name=" Demo SnapTrade User Secret ",
        secret_ref="secret://snaptrade/demo-user",
        scopes=["read_accounts", "read_holdings"],
        status="active",
        raw_metadata={"environment": "synthetic"},
    )

    assert payload.provider == "snaptrade"
    assert payload.credential_name == "Demo SnapTrade User Secret"
    assert payload.secret_ref == "secret://snaptrade/demo-user"
    assert payload.encrypted_secret_ref is None
    assert payload.scopes == ["read_accounts", "read_holdings"]


def test_provider_credentials_metadata_create_accepts_encrypted_reference() -> None:
    payload = ProviderCredentialsMetadataCreate(
        provider="other",
        credential_name="Demo Encrypted Ref",
        encrypted_secret_ref="encrypted://local/demo-reference",
    )

    assert payload.secret_ref is None
    assert payload.encrypted_secret_ref == "encrypted://local/demo-reference"


def test_provider_credentials_metadata_create_rejects_missing_reference() -> None:
    with pytest.raises(ValidationError):
        ProviderCredentialsMetadataCreate(
            provider="snaptrade",
            credential_name="Demo Missing Reference",
        )


def test_provider_credentials_metadata_create_rejects_multiple_references() -> None:
    with pytest.raises(ValidationError):
        ProviderCredentialsMetadataCreate(
            provider="snaptrade",
            credential_name="Demo Multiple References",
            secret_ref="secret://snaptrade/demo-user",
            encrypted_secret_ref="encrypted://local/demo-reference",
        )


def test_provider_credentials_metadata_create_rejects_plaintext_secret_material() -> None:
    with pytest.raises(ValidationError):
        ProviderCredentialsMetadataCreate(
            provider="snaptrade",
            credential_name="Demo Plaintext Secret",
            secret_ref="secret=do-not-store-this",
        )


def test_provider_credentials_metadata_public_read_does_not_expose_secret_refs() -> None:
    assert "secret_ref" not in ProviderCredentialsMetadataRead.model_fields
    assert "encrypted_secret_ref" not in ProviderCredentialsMetadataRead.model_fields
    assert "secret_ref" in ProviderCredentialsMetadataInternalRead.model_fields
    assert "encrypted_secret_ref" in ProviderCredentialsMetadataInternalRead.model_fields
