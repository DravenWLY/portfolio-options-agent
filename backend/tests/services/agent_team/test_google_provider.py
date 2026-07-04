import sys

import pytest

from app.services.agent_team.google_provider import GoogleGeminiLLMProvider, GoogleGeminiProviderError
from app.services.agent_team.llm_provider import LLMProviderMessage, LLMProviderRequest


pytestmark = [pytest.mark.unit]


class FakeGoogleClient:
    def __init__(self, result: str | Exception) -> None:
        self.result = result
        self.calls = 0

    def generate(self, request: LLMProviderRequest) -> str:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_google_provider_mocked_success_maps_to_ok_response() -> None:
    client = FakeGoogleClient("Mocked Google analysis-only output.")
    provider = GoogleGeminiLLMProvider(model="gemini-synthetic", client=client)

    response = provider.complete(_request())

    assert response.status == "ok"
    assert response.provider == "google"
    assert response.model == "gemini-synthetic"
    assert response.content_markdown == "Mocked Google analysis-only output."
    assert response.is_mock is False
    assert client.calls == 1


@pytest.mark.parametrize(
    "status",
    (
        "rate_limited",
        "quota_exceeded",
        "provider_auth_error",
        "provider_timeout",
        "provider_unavailable",
        "invalid_response",
    ),
)
def test_google_provider_maps_mocked_provider_failures_to_approved_statuses(status: str) -> None:
    provider = GoogleGeminiLLMProvider(
        model="gemini-synthetic",
        client=FakeGoogleClient(GoogleGeminiProviderError(status=status, safe_message="Synthetic safe failure.")),
    )

    response = provider.complete(_request())

    assert response.status == status
    assert response.content_markdown is None
    assert response.error_code == status
    assert response.error_message == "Synthetic safe failure."


def test_google_provider_maps_timeout_and_invalid_response_safely() -> None:
    timeout_response = GoogleGeminiLLMProvider(
        model="gemini-synthetic",
        client=FakeGoogleClient(TimeoutError("raw timeout body")),
    ).complete(_request())
    invalid_response = GoogleGeminiLLMProvider(model="gemini-synthetic", client=FakeGoogleClient("")).complete(_request())

    assert timeout_response.status == "provider_timeout"
    assert invalid_response.status == "invalid_response"
    assert "raw timeout body" not in repr(timeout_response)


def test_google_provider_maps_google_sdk_quota_error_safely() -> None:
    class GoogleSdkQuotaError(Exception):
        status = "RESOURCE_EXHAUSTED"
        code = 429

    provider = GoogleGeminiLLMProvider(model="gemini-synthetic", client=FakeGoogleClient(GoogleSdkQuotaError()))

    response = provider.complete(_request())

    assert response.status == "quota_exceeded"
    assert response.error_code == "quota_exceeded"
    assert response.content_markdown is None


def test_google_provider_maps_safety_validation_failure_without_raw_output() -> None:
    provider = GoogleGeminiLLMProvider(model="gemini-synthetic", client=FakeGoogleClient("Generated output includes $50."))

    response = provider.complete(_request())

    assert response.status == "safety_validation_failed"
    assert response.content_markdown is None
    assert "$50" not in repr(response)


def test_google_provider_lazy_import_not_used_with_injected_client() -> None:
    before = set(sys.modules)
    provider = GoogleGeminiLLMProvider(model="gemini-synthetic", client=FakeGoogleClient("Mocked output."))
    provider.complete(_request())
    after = set(sys.modules)

    assert "google" not in after - before


def _request() -> LLMProviderRequest:
    return LLMProviderRequest(
        request_id="req-google",
        role_name="news_analyst",
        provider="google",
        model="gemini-synthetic",
        messages=(
            LLMProviderMessage(role="system", content="Synthetic analysis-only system prompt."),
            LLMProviderMessage(role="user", content="Synthetic public prompt."),
        ),
    )
