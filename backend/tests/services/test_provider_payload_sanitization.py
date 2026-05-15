import pytest

from app.services.broker_import.normalization.sanitization import REDACTION_VALUE, sanitize_provider_payload


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
