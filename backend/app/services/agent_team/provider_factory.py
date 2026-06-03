"""Provider resolver for backend-owned Phase 19B LLM provider selection."""

from dataclasses import dataclass
import os

from app.services.agent_team.google_provider import GoogleGeminiLLMProvider
from app.services.agent_team.llm_provider import (
    LLMProvider,
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderStatus,
)
from app.services.agent_team.mock_provider import MockLLMProvider
from app.services.agent_team.openai_provider import OpenAILLMProvider
from app.services.agent_team.provider_config import LLMProviderConfig, LLMProviderConfigurationError, load_llm_provider_config


@dataclass(frozen=True)
class LLMProviderResolution:
    provider: LLMProvider | None
    status: str
    provider_name: str
    model: str
    error_code: str | None = None
    error_message: str | None = None

    @property
    def available(self) -> bool:
        return self.provider is not None and self.status == "ok"


def resolve_llm_provider(
    config: LLMProviderConfig | None = None,
    *,
    google_api_key: str | None = None,
    openai_api_key: str | None = None,
) -> LLMProviderResolution:
    """Resolve the configured provider without allowing client-side selection."""

    cfg = config or LLMProviderConfig()
    if cfg.mode == "mock":
        return LLMProviderResolution(
            provider=MockLLMProvider(model=cfg.model),
            status="ok",
            provider_name="mock",
            model=cfg.model,
        )
    if cfg.provider == "google":
        if not google_api_key:
            return LLMProviderResolution(
                provider=UnavailableLLMProvider(
                    provider_name="google",
                    model=cfg.model,
                    status="provider_auth_error",
                    error_message="Google provider credential is unavailable; deterministic evidence remains available.",
                ),
                status="provider_auth_error",
                provider_name="google",
                model=cfg.model,
                error_code="provider_auth_error",
                error_message="Google provider credential is unavailable.",
            )
        return LLMProviderResolution(
            provider=GoogleGeminiLLMProvider(
                model=cfg.model,
                api_key=google_api_key,
                timeout_seconds=cfg.timeout_seconds,
                max_retries=cfg.max_retries,
            ),
            status="ok",
            provider_name="google",
            model=cfg.model,
        )
    if cfg.provider == "openai":
        if not openai_api_key:
            return LLMProviderResolution(
                provider=UnavailableLLMProvider(
                    provider_name="openai",
                    model=cfg.model,
                    status="provider_auth_error",
                    error_message="OpenAI provider credential is unavailable; deterministic evidence remains available.",
                ),
                status="provider_auth_error",
                provider_name="openai",
                model=cfg.model,
                error_code="provider_auth_error",
                error_message="OpenAI provider credential is unavailable.",
            )
        return LLMProviderResolution(
            provider=OpenAILLMProvider(
                model=cfg.model,
                api_key=openai_api_key,
                timeout_seconds=cfg.timeout_seconds,
                max_retries=cfg.max_retries,
            ),
            status="ok",
            provider_name="openai",
            model=cfg.model,
        )
    return LLMProviderResolution(
        provider=None,
        status="provider_unavailable",
        provider_name=cfg.provider,
        model=cfg.model,
        error_code="provider_not_implemented",
        error_message="Configured live provider is unavailable.",
    )


def resolve_llm_provider_from_env(env: dict[str, str] | os._Environ[str] | None = None) -> LLMProviderResolution:
    """Resolve provider from process environment without exposing credential values."""

    values = env if env is not None else os.environ
    try:
        config = load_llm_provider_config(values)
    except LLMProviderConfigurationError:
        return LLMProviderResolution(
            provider=UnavailableLLMProvider(
                provider_name="unavailable",
                model="unavailable",
                status="provider_auth_error",
                error_message="LLM provider configuration is invalid; deterministic evidence remains available.",
            ),
            status="provider_auth_error",
            provider_name="unavailable",
            model="unavailable",
            error_code="provider_config_error",
            error_message="LLM provider configuration is invalid.",
        )
    return resolve_llm_provider(
        config,
        google_api_key=values.get("GOOGLE_API_KEY"),
        openai_api_key=values.get("OPENAI_API_KEY"),
    )


class UnavailableLLMProvider:
    """Provider shim that turns config/provider unavailability into safe role failures."""

    def __init__(
        self,
        *,
        provider_name: str,
        model: str,
        status: LLMProviderStatus,
        error_message: str,
    ) -> None:
        self.provider_name = provider_name
        self.model = model
        self.status = status
        self.error_message = error_message

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status=self.status,
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=None,
            is_mock=False,
            error_code=self.status,
            error_message=self.error_message,
            metadata={"safe_partial_output": "true"},
        )
