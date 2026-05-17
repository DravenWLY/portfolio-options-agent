import pytest

from app.core.config import get_settings
from app.services.broker_import.secrets import decrypt_secret, encrypt_secret, validate_secret_reference


pytestmark = [pytest.mark.unit]


def test_secret_encryption_round_trips_without_plaintext() -> None:
    secret = "11111111-1111-4111-8111-111111111111"
    key = "test_snaptrade_secret_encryption_key_32_chars"

    encrypted = encrypt_secret(secret, key)

    assert secret not in encrypted
    assert '"alg":"Fernet"' in encrypted
    assert '"key_id":"local-v1"' in encrypted
    assert decrypt_secret(encrypted, key) == secret


def test_secret_ref_rejects_uuid_shaped_plaintext_secret() -> None:
    with pytest.raises(ValueError):
        validate_secret_reference("11111111-1111-4111-8111-111111111111")


def test_settings_refuse_snaptrade_without_encryption_key(monkeypatch) -> None:
    monkeypatch.setenv("SNAPTRADE_CLIENT_ID", "test_snaptrade_client_id")
    monkeypatch.delenv("SNAPTRADE_SECRET_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValueError, match="SNAPTRADE_SECRET_ENCRYPTION_KEY"):
        get_settings()
