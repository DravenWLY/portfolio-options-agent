import base64
import hashlib
import hmac
import json
import os
import re

SECRET_REF_PREFIXES = (
    "secret://",
    "vault://",
    "aws-secretsmanager://",
    "gcp-secretmanager://",
    "azure-keyvault://",
)
LOCAL_DEV_ENCRYPTION_KEY = "synthetic-local-dev-snaptrade-secret-encryption-key-do-not-use"
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
    return hashlib.sha256(encryption_key.encode("utf-8")).digest()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < length:
        output.extend(hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(output[:length])


def encrypt_secret(secret: str, encryption_key: str, key_id: str = "local-v1") -> str:
    key = _derive_key(encryption_key)
    nonce = os.urandom(16)
    plaintext = secret.encode("utf-8")
    stream = _keystream(key, nonce, len(plaintext))
    ciphertext = bytes(left ^ right for left, right in zip(plaintext, stream, strict=True))
    tag = hmac.new(key, key_id.encode("utf-8") + nonce + ciphertext, hashlib.sha256).digest()
    envelope = {
        "v": 1,
        "alg": "HMAC-SHA256-XOR",
        "key_id": key_id,
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
        "tag": _b64encode(tag),
    }
    return json.dumps(envelope, sort_keys=True, separators=(",", ":"))


def decrypt_secret(encrypted_secret: str, encryption_key: str) -> str:
    key = _derive_key(encryption_key)
    envelope = json.loads(encrypted_secret)
    key_id = envelope["key_id"]
    nonce = _b64decode(envelope["nonce"])
    ciphertext = _b64decode(envelope["ciphertext"])
    expected_tag = hmac.new(key, key_id.encode("utf-8") + nonce + ciphertext, hashlib.sha256).digest()
    actual_tag = _b64decode(envelope["tag"])
    if not hmac.compare_digest(expected_tag, actual_tag):
        raise SecretValidationError("encrypted secret envelope failed authentication")
    stream = _keystream(key, nonce, len(ciphertext))
    plaintext = bytes(left ^ right for left, right in zip(ciphertext, stream, strict=True))
    return plaintext.decode("utf-8")


def resolve_snaptrade_encryption_key(encryption_key: str) -> str:
    return encryption_key or LOCAL_DEV_ENCRYPTION_KEY
