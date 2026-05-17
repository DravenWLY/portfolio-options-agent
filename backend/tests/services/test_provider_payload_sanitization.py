import pytest

from app.services.broker_import.normalization.sanitization import (
    CREDENTIAL_METADATA_ALLOWLIST,
    REDACTION_VALUE,
    SYNC_SUMMARY_ALLOWLIST,
    allowlisted_provider_payload,
    sanitize_provider_payload,
)


pytestmark = [pytest.mark.unit]


def test_provider_payload_sanitization_redacts_secret_like_keys() -> None:
    payload = {
        "providerPositionId": "demo-position",
        "accessToken": "test_token",
        "nested": {
            "api_key": "test_api_key",
            "safeField": "safe-value",
        },
        "items": [
            {"authorization": "Bearer test_token"},
            {"symbol": "VOO"},
        ],
    }

    sanitized = sanitize_provider_payload(payload)

    assert sanitized == {
        "providerPositionId": "demo-position",
        "accessToken": REDACTION_VALUE,
        "nested": {
            "api_key": REDACTION_VALUE,
            "safeField": "safe-value",
        },
        "items": [
            {"authorization": REDACTION_VALUE},
            {"symbol": "VOO"},
        ],
    }


def test_provider_payload_sanitization_handles_none_and_scalar_values() -> None:
    assert sanitize_provider_payload(None) is None
    assert sanitize_provider_payload("safe") == "safe"
    assert sanitize_provider_payload(123) == 123


def test_credential_metadata_allowlist_excludes_provider_secret_fields() -> None:
    payload = {
        "synthetic": True,
        "provider_request_id": "demo-request",
        "userSecret": "11111111-1111-4111-8111-111111111111",
        "data": "opaque-provider-data",
        "safe_but_unlisted": "must-not-persist",
    }

    assert allowlisted_provider_payload(payload, CREDENTIAL_METADATA_ALLOWLIST) == {
        "synthetic": True,
        "provider_request_id": "demo-request",
    }


def test_sync_summary_allowlist_excludes_unexpected_provider_fields() -> None:
    payload = {
        "provider_request_id": "demo-request",
        "warnings": ["synthetic warning"],
        "partial_failures": [],
        "authorization": "Bearer test-token",
        "unexpected": "drop-me",
    }

    assert allowlisted_provider_payload(payload, SYNC_SUMMARY_ALLOWLIST) == {
        "provider_request_id": "demo-request",
        "warnings": ["synthetic warning"],
        "partial_failures": [],
    }
