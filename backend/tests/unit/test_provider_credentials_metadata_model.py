import pytest

from app.db.base import Base
from app.models.provider_credentials_metadata import ProviderCredentialsMetadata


pytestmark = pytest.mark.unit


def test_provider_credentials_metadata_model_is_registered_with_base_metadata() -> None:
    assert "provider_credentials_metadata" in Base.metadata.tables


def test_provider_credentials_metadata_model_columns() -> None:
    columns = ProviderCredentialsMetadata.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "user_id",
        "provider",
        "credential_name",
        "secret_ref",
        "encrypted_secret_ref",
        "scopes",
        "status",
        "last_tested_at",
        "raw_metadata",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns["user_id"].nullable is True
    assert columns["provider"].nullable is False
    assert columns["credential_name"].nullable is False
    assert columns["secret_ref"].nullable is True
    assert columns["encrypted_secret_ref"].nullable is True


def test_provider_credentials_metadata_indexes() -> None:
    indexes = {index.name for index in ProviderCredentialsMetadata.__table__.indexes}

    assert "uq_provider_credentials_metadata_active_name" in indexes
    assert "ix_provider_credentials_metadata_user_provider" in indexes
    assert "ix_provider_credentials_metadata_status" in indexes
