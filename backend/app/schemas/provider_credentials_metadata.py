from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from app.services.broker_import.secrets import validate_secret_reference

ProviderName = Literal["snaptrade", "akoya", "plaid", "tradier", "alpaca", "polygon", "openai", "anthropic", "gemini", "other"]
CredentialStatus = Literal["active", "inactive", "testing_failed", "unknown", "revoked"]


def _looks_like_plaintext_secret(value: str) -> bool:
    lowered = value.lower()
    forbidden_fragments = (
        "password",
        "token=",
        "apikey",
        "api_key",
        "secret=",
        "sk-",
        "xoxb-",
    )
    return any(fragment in lowered for fragment in forbidden_fragments)


class ProviderCredentialsMetadataCreate(BaseModel):
    user_id: UUID | None = None
    provider: ProviderName
    credential_name: str = Field(min_length=1, max_length=120)
    secret_ref: str | None = Field(default=None, max_length=255)
    encrypted_secret_ref: str | None = Field(default=None, max_length=255)
    scopes: list[str] | None = None
    status: CredentialStatus = "unknown"
    last_tested_at: datetime | None = None
    raw_metadata: dict | None = None

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("credential_name")
    @classmethod
    def strip_credential_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("secret_ref", "encrypted_secret_ref")
    @classmethod
    def validate_secret_reference(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if _looks_like_plaintext_secret(stripped):
            raise ValueError("credential metadata must store a reference, not plaintext credential material")
        if info.field_name == "secret_ref":
            return validate_secret_reference(stripped)
        return stripped

    @model_validator(mode="after")
    def require_one_secret_reference(self) -> "ProviderCredentialsMetadataCreate":
        if bool(self.secret_ref) == bool(self.encrypted_secret_ref):
            raise ValueError("provide exactly one of secret_ref or encrypted_secret_ref")
        return self


class ProviderCredentialsMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    provider: str
    credential_name: str
    scopes: list[str] | None
    status: str
    last_tested_at: datetime | None
    raw_metadata: dict | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ProviderCredentialsMetadataInternalRead(ProviderCredentialsMetadataRead):
    secret_ref: str | None
    encrypted_secret_ref: str | None
