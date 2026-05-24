import sys

import pytest

from app.services.agent_team.mock_provider import MockLLMProvider
from app.services.agent_team.provider_config import LLMProviderConfig, load_llm_provider_config
from app.services.agent_team.provider_factory import UnavailableLLMProvider, resolve_llm_provider, resolve_llm_provider_from_env


pytestmark = [pytest.mark.unit]


def test_provider_factory_defaults_to_mock_provider_without_google_key() -> None:
    resolution = resolve_llm_provider()

    assert resolution.available is True
    assert resolution.status == "ok"
    assert resolution.provider_name == "mock"
    assert isinstance(resolution.provider, MockLLMProvider)


def test_mock_mode_does_not_import_or_construct_google_provider() -> None:
    before = set(sys.modules)
    resolution = resolve_llm_provider(LLMProviderConfig())
    after = set(sys.modules)

    assert resolution.available is True
    assert "google" not in after - before
    assert "google.generativeai" not in sys.modules


def test_live_google_mode_returns_google_provider_when_backend_key_is_passed() -> None:
    config = load_llm_provider_config(
        {
            "POA_LLM_MODE": "live",
            "POA_LLM_PROVIDER": "google",
            "POA_LLM_MODEL": "gemini-synthetic",
            "GOOGLE_API_KEY": "synthetic-test-key-not-returned",
        }
    )
    resolution = resolve_llm_provider(config, google_api_key="synthetic-test-key-not-returned")

    assert resolution.available is True
    assert resolution.provider is not None
    assert resolution.status == "ok"
    assert resolution.provider_name == "google"
    assert "synthetic-test-key-not-returned" not in repr(resolution)


def test_live_google_mode_without_key_resolves_to_safe_unavailable_provider() -> None:
    config = LLMProviderConfig(
        mode="live",
        provider="google",
        model="gemini-synthetic",
        google_credential_available=True,
    )
    resolution = resolve_llm_provider(config)

    assert resolution.available is False
    assert isinstance(resolution.provider, UnavailableLLMProvider)
    assert resolution.status == "provider_auth_error"
    assert resolution.error_code == "provider_auth_error"


def test_provider_factory_never_accepts_client_supplied_provider_fields() -> None:
    resolution = resolve_llm_provider(load_llm_provider_config({}))

    assert resolution.provider_name == "mock"
    assert resolution.model == "mock-agent-team-v1"


def test_resolve_provider_from_env_invalid_live_config_fails_closed() -> None:
    resolution = resolve_llm_provider_from_env({"POA_LLM_MODE": "live", "POA_LLM_PROVIDER": "google"})

    assert resolution.available is False
    assert isinstance(resolution.provider, UnavailableLLMProvider)
    assert resolution.status == "provider_auth_error"
