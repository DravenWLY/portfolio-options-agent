import json
from uuid import uuid4
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


def _encrypt_snaptrade_credentials(snaptrade_user_id: str, user_secret: str, encryption_key: str) -> str:
    payload = json.dumps(
        {"snaptrade_user_id": snaptrade_user_id, "user_secret": user_secret},
        sort_keys=True,
        separators=(",", ":"),
    )
    return encrypt_secret(payload, encryption_key)


def decrypt_snaptrade_credentials(encrypted_secret_ref: str, encryption_key: str) -> tuple[str, str]:
    payload = json.loads(decrypt_secret(encrypted_secret_ref, encryption_key))
    snaptrade_user_id = str(payload.get("snaptrade_user_id") or "").strip()
    user_secret = str(payload.get("user_secret") or "").strip()
    if not snaptrade_user_id or not user_secret:
        raise SnapTradeUserRegistrationMissingError("SnapTrade credential envelope is incomplete")
    return snaptrade_user_id, user_secret


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

    snaptrade_user_ref = f"poa_{uuid4().hex}"
    response = adapter.register_user(snaptrade_user_ref)
    if credential is None:
        credential = ProviderCredentialsMetadata(
            user_id=user_id,
            provider="snaptrade",
            credential_name=SNAPTRADE_USER_CREDENTIAL_NAME,
        )
        db.add(credential)

    resolved_key = resolve_snaptrade_encryption_key(encryption_key)
    credential.secret_ref = None
    credential.encrypted_secret_ref = _encrypt_snaptrade_credentials(
        response.snaptrade_user_id,
        response.user_secret,
        resolved_key,
    )
    credential.status = "active"
    credential.scopes = ["read_accounts", "read_balances", "read_positions"]
    credential.raw_metadata = {
        "registration_payload": allowlisted_provider_payload(
            response.raw_payload,
            CREDENTIAL_METADATA_ALLOWLIST,
        ),
    }
    db.commit()
    db.refresh(credential)
    return credential


def link_existing_snaptrade_user(
    db: Session,
    user_id: UUID,
    snaptrade_user_id: str,
    user_secret: str,
    encryption_key: str,
) -> ProviderCredentialsMetadata:
    if _get_active_user(db, user_id) is None:
        raise SnapTradeUserNotFoundError("User not found")

    normalized_snaptrade_user_id = snaptrade_user_id.strip()
    normalized_user_secret = user_secret.strip()
    if not normalized_snaptrade_user_id or not normalized_user_secret:
        raise SnapTradeUserRegistrationMissingError("SnapTrade user id and user secret are required")

    credential = _get_snaptrade_credential(db, user_id)
    if credential is None:
        credential = ProviderCredentialsMetadata(
            user_id=user_id,
            provider="snaptrade",
            credential_name=SNAPTRADE_USER_CREDENTIAL_NAME,
        )
        db.add(credential)

    resolved_key = resolve_snaptrade_encryption_key(encryption_key)
    credential.secret_ref = None
    credential.encrypted_secret_ref = _encrypt_snaptrade_credentials(
        normalized_snaptrade_user_id,
        normalized_user_secret,
        resolved_key,
    )
    credential.status = "active"
    credential.scopes = ["read_accounts", "read_balances", "read_positions"]
    credential.raw_metadata = {
        "registration_payload": {},
        "manual_existing_user_link": True,
    }
    db.commit()
    db.refresh(credential)
    return credential


def create_connection_portal_url(
    db: Session,
    user_id: UUID,
    adapter: SnapTradeAdapter,
    encryption_key: str,
    broker: str | None = None,
):
    if _get_active_user(db, user_id) is None:
        raise SnapTradeUserNotFoundError("User not found")

    credential = _get_snaptrade_credential(db, user_id)
    if credential is None or credential.encrypted_secret_ref is None:
        raise SnapTradeUserRegistrationMissingError("SnapTrade user has not been registered")

    snaptrade_user_id, user_secret = decrypt_snaptrade_credentials(
        credential.encrypted_secret_ref,
        resolve_snaptrade_encryption_key(encryption_key),
    )
    return adapter.create_connection_portal_url(snaptrade_user_id, user_secret, broker)
