import pytest

from app.services.agent_team.llm_provider import LLMProviderMessage, LLMProviderRequest
from app.services.agent_team.openai_provider import (
    OpenAILLMProvider,
    OpenAIProviderError,
    _map_openai_exception,
)


pytestmark = [pytest.mark.unit, pytest.mark.adapter]


class FakeOpenAIClient:
    def __init__(self, result: str | Exception) -> None:
        self.result = result
        self.calls = 0

    def generate(self, request: LLMProviderRequest) -> str:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _request() -> LLMProviderRequest:
    return LLMProviderRequest(
        request_id="rev_demo:fundamentals_analyst",
        role_name="fundamentals_analyst",
        messages=(
            LLMProviderMessage(role="system", content="Analysis-only system rules."),
            LLMProviderMessage(role="user", content="Synthetic public evidence payload."),
        ),
        provider="openai",
        model="gpt-synthetic",
    )


def test_openai_provider_mocked_success_maps_to_ok_response() -> None:
    client = FakeOpenAIClient("Mocked OpenAI analysis-only output.")
    provider = OpenAILLMProvider(model="gpt-synthetic", client=client)

    response = provider.complete(_request())

    assert response.status == "ok"
    assert response.provider == "openai"
    assert response.model == "gpt-synthetic"
    assert response.content_markdown == "Mocked OpenAI analysis-only output."
    assert response.is_mock is False
    assert client.calls == 1


@pytest.mark.parametrize(
    "status",
    ("rate_limited", "quota_exceeded", "provider_timeout", "provider_auth_error", "provider_unavailable"),
)
def test_openai_provider_error_maps_to_safe_status(status: str) -> None:
    client = FakeOpenAIClient(OpenAIProviderError(status=status))  # type: ignore[arg-type]
    provider = OpenAILLMProvider(model="gpt-synthetic", client=client)

    response = provider.complete(_request())

    assert response.status == status
    assert response.content_markdown is None
    assert response.is_mock is False
    assert response.error_message and "key" not in response.error_message.lower().split()


def test_openai_provider_unsafe_output_degrades_to_safety_validation_failed() -> None:
    client = FakeOpenAIClient("Price target $250.00 with 30% upside.")
    provider = OpenAILLMProvider(model="gpt-synthetic", client=client)

    response = provider.complete(_request())

    assert response.status == "safety_validation_failed"
    assert response.content_markdown is None


def test_openai_provider_empty_output_maps_to_invalid_response() -> None:
    provider = OpenAILLMProvider(model="gpt-synthetic", client=FakeOpenAIClient("   "))

    assert provider.complete(_request()).status == "invalid_response"


def test_openai_provider_generic_exception_degrades_safely() -> None:
    client = FakeOpenAIClient(RuntimeError("raw provider body should never surface"))
    provider = OpenAILLMProvider(model="gpt-synthetic", client=client)

    response = provider.complete(_request())

    assert response.status == "provider_unavailable"
    assert response.content_markdown is None
    assert "raw provider body" not in (response.error_message or "")


def test_openai_provider_missing_key_without_client_is_auth_error() -> None:
    provider = OpenAILLMProvider(model="gpt-synthetic", api_key=None, client=None)

    response = provider.complete(_request())

    assert response.status == "provider_auth_error"
    assert response.content_markdown is None


@pytest.mark.parametrize(
    ("exc_name", "expected"),
    (
        ("RateLimitError", "rate_limited"),
        ("APITimeoutError", "provider_timeout"),
        ("AuthenticationError", "provider_auth_error"),
        ("PermissionDeniedError", "provider_auth_error"),
        ("SomeOtherError", "provider_unavailable"),
    ),
)
def test_map_openai_exception_by_class_name(exc_name: str, expected: str) -> None:
    exc = type(exc_name, (Exception,), {})()
    assert _map_openai_exception(exc) == expected
