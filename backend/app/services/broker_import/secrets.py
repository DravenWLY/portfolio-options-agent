import base64
import hashlib
import json
import re

from cryptography.fernet import Fernet, InvalidToken

SECRET_REF_PREFIXES = (
    "secret://",
    "vault://",
    "aws-secretsmanager://",
    "gcp-secretmanager://",
    "azure-keyvault://",
)
UUID_SHAPED_SECRET = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class SecretConfigurationError(RuntimeError):
    """Raised when local secret encryption is not configured."""


class SecretValidationError(ValueError):
    """Raised when plaintext credential material is used where only references are allowed."""


def validate_secret_reference(value: str) -> str:
    stripped = value.strip()
    lowered = stripped.lower()
    if UUID_SHAPED_SECRET.match(stripped):
        raise SecretValidationError("secret_ref must be an indirection reference, not plaintext secret material")
    if not lowered.startswith(SECRET_REF_PREFIXES):
        raise SecretValidationError("secret_ref must use an approved secret reference prefix")
    return stripped


def _derive_key(encryption_key: str) -> bytes:
    if not encryption_key:
        raise SecretConfigurationError("SNAPTRADE_SECRET_ENCRYPTION_KEY is required")
    digest = hashlib.sha256(encryption_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(secret: str, encryption_key: str, key_id: str = "local-v1") -> str:
    token = Fernet(_derive_key(encryption_key)).encrypt(secret.encode("utf-8")).decode("ascii")
    envelope = {
        "v": 1,
        "alg": "Fernet",
        "key_id": key_id,
        "token": token,
    }
    return json.dumps(envelope, sort_keys=True, separators=(",", ":"))


def decrypt_secret(encrypted_secret: str, encryption_key: str) -> str:
    envelope = json.loads(encrypted_secret)
    if envelope.get("alg") != "Fernet":
        raise SecretValidationError("encrypted secret envelope uses unsupported algorithm")
    try:
        plaintext = Fernet(_derive_key(encryption_key)).decrypt(envelope["token"].encode("ascii"))
    except (InvalidToken, KeyError, TypeError, ValueError) as exc:
        raise SecretValidationError("encrypted secret envelope failed authentication") from exc
    return plaintext.decode("utf-8")


def resolve_snaptrade_encryption_key(encryption_key: str) -> str:
    if not encryption_key:
        raise SecretConfigurationError("SNAPTRADE_SECRET_ENCRYPTION_KEY is required")
    return encryption_key
