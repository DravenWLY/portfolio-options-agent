from collections.abc import Mapping, Sequence
from typing import Any

SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "bearer",
    "credential",
    "password",
    "secret",
    "token",
)

REDACTION_VALUE = "[REDACTED]"


def is_sensitive_key(key: str) -> bool:
    normalized = key.replace("-", "_").lower()
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def sanitize_provider_payload(payload: Any) -> Any:
    if payload is None:
        return None

    if isinstance(payload, Mapping):
        return {
            str(key): REDACTION_VALUE if is_sensitive_key(str(key)) else sanitize_provider_payload(value)
            for key, value in payload.items()
        }

    if isinstance(payload, str | int | float | bool):
        return payload

    if isinstance(payload, Sequence):
        return [sanitize_provider_payload(item) for item in payload]

    return str(payload)
