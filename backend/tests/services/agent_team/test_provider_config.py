import pytest

from app.services.agent_team.provider_config import (
    DEFAULT_MOCK_MODEL,
    DEFAULT_OPENAI_MODEL,
    LLMProviderConfig,
    LLMProviderConfigurationError,
    load_llm_provider_config,
)


pytestmark = [pytest.mark.unit]


def test_provider_config_defaults_to_mock_without_google_key() -> None:
    config = load_llm_provider_config({})

    assert config.mode == "mock"
    assert config.provider == "mock"
    assert config.model == DEFAULT_MOCK_MODEL
    assert config.google_credential_available is False
    snapshot = config.public_snapshot()
    assert snapshot["google_credential_configured"] is False
    assert "GOOGLE_API_KEY" not in repr(snapshot)
    assert "secret" not in repr(snapshot).lower()


def test_provider_config_parses_app_owned_names() -> None:
    config = load_llm_provider_config(
        {
            "POA_LLM_MODE": "mock",
            "POA_LLM_PROVIDER": "mock",
            "POA_LLM_MODEL": "mock-custom",
            "POA_LLM_TIMEOUT_SECONDS": "12",
            "POA_LLM_MAX_RETRIES": "2",
            "POA_LLM_TOKEN_BUDGET_PER_RUN": "321",
            "POA_LLM_RATE_LIMIT_FALLBACK": "partial_report",
            "POA_LLM_LIVE_TESTS": "1",
        }
    )

    assert config.model == "mock-custom"
    assert config.timeout_seconds == 12
    assert config.max_retries == 2
    assert config.token_budget_per_run == 321
    assert config.live_tests_enabled is True


@pytest.mark.parametrize(
    "env",
    (
        {"POA_LLM_MODE": "invalid"},
        {"POA_LLM_MODE": "mock", "POA_LLM_PROVIDER": "google"},
        {"POA_LLM_MODE": "mock", "POA_LLM_TIMEOUT_SECONDS": "0"},
        {"POA_LLM_MODE": "mock", "POA_LLM_MAX_RETRIES": "-1"},
        {"POA_LLM_MODE": "mock", "POA_LLM_RATE_LIMIT_FALLBACK": "raise"},
    ),
)
def test_provider_config_invalid_values_fail_closed(env: dict[str, str]) -> None:
    with pytest.raises(LLMProviderConfigurationError):
        load_llm_provider_config(env)


def test_live_google_requires_backend_key_presence_without_exposing_value() -> None:
    with pytest.raises(LLMProviderConfigurationError, match="requires backend Google API key"):
        load_llm_provider_config({"POA_LLM_MODE": "live", "POA_LLM_PROVIDER": "google"})

    config = load_llm_provider_config(
        {
            "POA_LLM_MODE": "live",
            "POA_LLM_PROVIDER": "google",
            "POA_LLM_MODEL": "gemini-synthetic",
            "GOOGLE_API_KEY": "synthetic-test-key-not-returned",
        }
    )
    snapshot = config.public_snapshot()

    assert config.mode == "live"
    assert config.provider == "google"
    assert config.google_credential_available is True
    assert snapshot["google_credential_configured"] is True
    assert "synthetic-test-key-not-returned" not in repr(config)
    assert "synthetic-test-key-not-returned" not in repr(snapshot)


def test_config_direct_construction_uses_safe_public_fields_only() -> None:
    config = LLMProviderConfig()

    assert config.public_snapshot()["provider"] == "mock"


def test_live_openai_requires_backend_key_presence_without_exposing_value() -> None:
    with pytest.raises(LLMProviderConfigurationError, match="requires backend OpenAI API key"):
        load_llm_provider_config({"POA_LLM_MODE": "live", "POA_LLM_PROVIDER": "openai"})

    config = load_llm_provider_config(
        {
            "POA_LLM_MODE": "live",
            "POA_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "synthetic-openai-key-not-returned",
        }
    )
    snapshot = config.public_snapshot()

    assert config.mode == "live"
    assert config.provider == "openai"
    assert config.model == DEFAULT_OPENAI_MODEL
    assert config.openai_credential_available is True
    assert snapshot["openai_credential_configured"] is True
    assert "synthetic-openai-key-not-returned" not in repr(config)
    assert "synthetic-openai-key-not-returned" not in repr(snapshot)


def test_mock_mode_rejects_openai_provider() -> None:
    with pytest.raises(LLMProviderConfigurationError):
        load_llm_provider_config({"POA_LLM_MODE": "mock", "POA_LLM_PROVIDER": "openai"})


def test_openai_credential_not_required_in_default_mock_mode() -> None:
    config = load_llm_provider_config({})

    assert config.openai_credential_available is False
    assert config.public_snapshot()["openai_credential_configured"] is False
