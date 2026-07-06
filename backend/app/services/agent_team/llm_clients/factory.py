"""Provider resolver for backend-owned Phase 19B LLM provider selection."""

from dataclasses import dataclass
import os

from app.config import get_settings
from app.services.agent_team.llm_clients.chain import CHAIN_ADVANCE_STATUSES, ChainedLLMProvider
from app.services.agent_team.llm_clients.config import (
    LLMProviderConfig,
    LLMProviderConfigurationError,
    LLMProviderSecrets,
    load_llm_provider_config,
    load_llm_provider_secrets,
)
from app.services.agent_team.llm_clients.contracts import (
    LLMProvider,
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderStatus,
)
from app.services.agent_team.llm_clients.google import GoogleGeminiLLMProvider
from app.services.agent_team.llm_clients.mock import MockLLMProvider
from app.services.agent_team.llm_clients.openai import OpenAILLMProvider

# CHAIN_ADVANCE_STATUSES and ChainedLLMProvider moved to
# app.services.agent_team.llm_clients.chain in P34A-T11A; re-exported here so
# existing `from ...provider_factory import ChainedLLMProvider` paths keep
# resolving to the same objects.
__all__ = [
    "CHAIN_ADVANCE_STATUSES",
    "ChainedLLMProvider",
    "LLMProviderResolution",
    "UnavailableLLMProvider",
    "resolve_llm_provider",
    "resolve_llm_provider_from_env",
]


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
    secrets: LLMProviderSecrets | None = None,
    google_api_key: str | None = None,
    openai_api_key: str | None = None,
) -> LLMProviderResolution:
    """Resolve the configured provider without allowing client-side selection."""

    cfg = config or LLMProviderConfig()
    provider_secrets = secrets or LLMProviderSecrets(
        google_api_key=google_api_key,
        openai_api_key=openai_api_key,
    )
    if cfg.mode == "mock":
        return LLMProviderResolution(
            provider=MockLLMProvider(model=cfg.model),
            status="ok",
            provider_name="mock",
            model=cfg.model,
        )
    if cfg.provider == "google":
        if not provider_secrets.google_api_key:
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
        google_providers = tuple(
            GoogleGeminiLLMProvider(
                model=candidate,
                api_key=provider_secrets.google_api_key,
                timeout_seconds=cfg.timeout_seconds,
                max_retries=cfg.max_retries,
            )
            for candidate in (cfg.model_candidates or (cfg.model,))
        )
        return LLMProviderResolution(
            provider=(
                ChainedLLMProvider(providers=google_providers)
                if len(google_providers) > 1
                else google_providers[0]
            ),
            status="ok",
            provider_name="google",
            model=cfg.model,
        )
    if cfg.provider == "openai":
        if not provider_secrets.openai_api_key:
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
        openai_providers = tuple(
            OpenAILLMProvider(
                model=candidate,
                api_key=provider_secrets.openai_api_key,
                timeout_seconds=cfg.timeout_seconds,
                max_retries=cfg.max_retries,
            )
            for candidate in (cfg.model_candidates or (cfg.model,))
        )
        return LLMProviderResolution(
            provider=(
                ChainedLLMProvider(providers=openai_providers)
                if len(openai_providers) > 1
                else openai_providers[0]
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

    if env is not None:
        values = env
        secrets = load_llm_provider_secrets(values)
    else:
        values = dict(os.environ)
        settings = get_settings()
        if settings.google_api_key and not values.get("GOOGLE_API_KEY"):
            values["GOOGLE_API_KEY"] = settings.google_api_key
        if settings.openai_api_key and not values.get("OPENAI_API_KEY"):
            values["OPENAI_API_KEY"] = settings.openai_api_key
        secrets = LLMProviderSecrets(
            google_api_key=settings.google_api_key or values.get("GOOGLE_API_KEY"),
            openai_api_key=settings.openai_api_key or values.get("OPENAI_API_KEY"),
        )
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
    return resolve_llm_provider(config, secrets=secrets)


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
