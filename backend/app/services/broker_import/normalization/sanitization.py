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

CREDENTIAL_METADATA_ALLOWLIST = frozenset({"synthetic", "request_id", "provider_request_id", "warnings"})
BROKER_CONNECTION_METADATA_ALLOWLIST = frozenset({"synthetic", "request_id", "provider_request_id", "warnings"})
BROKER_ACCOUNT_PAYLOAD_ALLOWLIST = frozenset({"synthetic", "request_id", "provider_request_id", "warnings"})
SYNC_SUMMARY_ALLOWLIST = frozenset(
    {
        "balance_currency",
        "stock_positions_count",
        "option_positions_count",
        "partial_failures",
        "warnings",
        "provider_request_id",
    }
)
SYNC_ERROR_ALLOWLIST = frozenset({"type", "message"})


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


def allowlisted_provider_payload(payload: Mapping | None, allowed_keys: frozenset[str]) -> dict:
    if not payload:
        return {}
    return {
        str(key): sanitize_provider_payload(value)
        for key, value in payload.items()
        if str(key) in allowed_keys
    }


def sanitized_sync_error(error_type: str, message: str) -> dict[str, str]:
    return allowlisted_provider_payload(
        {"type": error_type, "message": message},
        SYNC_ERROR_ALLOWLIST,
    )


def sanitized_sync_summary(**values: Any) -> dict:
    return allowlisted_provider_payload(values, SYNC_SUMMARY_ALLOWLIST)
