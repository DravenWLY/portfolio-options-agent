from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provider_credentials_metadata import ProviderCredentialsMetadata
from app.models.user import User
from app.services.broker_import.normalization.sanitization import (
    CREDENTIAL_METADATA_ALLOWLIST,
    allowlisted_provider_payload,
)
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter
from app.services.broker_import.secrets import decrypt_secret, encrypt_secret, resolve_snaptrade_encryption_key

SNAPTRADE_USER_CREDENTIAL_NAME = "snaptrade_user"


class SnapTradeConnectionFlowError(RuntimeError):
    """Base error for backend-only SnapTrade connection flow failures."""


class SnapTradeUserNotFoundError(SnapTradeConnectionFlowError):
    """Raised when a local user is missing."""


class SnapTradeUserRegistrationMissingError(SnapTradeConnectionFlowError):
    """Raised when a portal URL is requested before registration."""


def _get_active_user(db: Session, user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))


def _get_snaptrade_credential(db: Session, user_id: UUID) -> ProviderCredentialsMetadata | None:
    return db.scalar(
        select(ProviderCredentialsMetadata).where(
            ProviderCredentialsMetadata.user_id == user_id,
            ProviderCredentialsMetadata.provider == "snaptrade",
            ProviderCredentialsMetadata.credential_name == SNAPTRADE_USER_CREDENTIAL_NAME,
            ProviderCredentialsMetadata.deleted_at.is_(None),
        )
    )


def register_snaptrade_user(
    db: Session,
    user_id: UUID,
    adapter: SnapTradeAdapter,
    encryption_key: str,
) -> ProviderCredentialsMetadata:
    if _get_active_user(db, user_id) is None:
        raise SnapTradeUserNotFoundError("User not found")

    credential = _get_snaptrade_credential(db, user_id)
    if credential is not None and credential.status == "active" and credential.encrypted_secret_ref:
        return credential

    response = adapter.register_user(str(user_id))
    if credential is None:
        credential = ProviderCredentialsMetadata(
            user_id=user_id,
            provider="snaptrade",
            credential_name=SNAPTRADE_USER_CREDENTIAL_NAME,
        )
        db.add(credential)

    resolved_key = resolve_snaptrade_encryption_key(encryption_key)
    credential.secret_ref = None
    credential.encrypted_secret_ref = encrypt_secret(response.user_secret, resolved_key)
    credential.status = "active"
    credential.scopes = ["read_accounts", "read_balances", "read_positions"]
    credential.raw_metadata = {
        "snaptrade_user_id": response.snaptrade_user_id,
        "registration_payload": allowlisted_provider_payload(
            response.raw_payload,
            CREDENTIAL_METADATA_ALLOWLIST,
        ),
    }
    db.commit()
    db.refresh(credential)
    return credential


def create_connection_portal_url(
    db: Session,
    user_id: UUID,
    adapter: SnapTradeAdapter,
    encryption_key: str,
):
    if _get_active_user(db, user_id) is None:
        raise SnapTradeUserNotFoundError("User not found")

    credential = _get_snaptrade_credential(db, user_id)
    if credential is None or credential.encrypted_secret_ref is None:
        raise SnapTradeUserRegistrationMissingError("SnapTrade user has not been registered")

    snaptrade_user_id = (credential.raw_metadata or {}).get("snaptrade_user_id")
    if not snaptrade_user_id:
        raise SnapTradeUserRegistrationMissingError("SnapTrade user metadata is incomplete")

    user_secret = decrypt_secret(
        credential.encrypted_secret_ref,
        resolve_snaptrade_encryption_key(encryption_key),
    )
    return adapter.create_connection_portal_url(snaptrade_user_id, user_secret)
