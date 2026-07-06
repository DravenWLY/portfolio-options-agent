"""LLM client layer for the Agent Team (P34A-T11A).

Groups the app-owned LLM provider concerns that were previously flat modules
under ``agent_team/``:

- ``contracts``  — request/response/protocol dataclasses and payload validators
- ``config``     — sanitized provider configuration + model-candidate parsing
- ``factory``    — backend-owned provider resolution (no client-side selection)
- ``chain``      — ordered same-provider model-candidate fallback
- ``google`` / ``openai`` / ``mock`` — provider adapters behind the protocol

The old module paths (``agent_team.llm_provider``, ``provider_config``,
``provider_factory``, ``google_provider``, ``openai_provider``,
``mock_provider``) remain as compatibility shims that re-export from here.
"""

from app.services.agent_team.llm_clients.chain import (
    CHAIN_ADVANCE_STATUSES,
    ChainedLLMProvider,
)
from app.services.agent_team.llm_clients.config import (
    DEFAULT_LIVE_MODEL,
    DEFAULT_MOCK_MODEL,
    DEFAULT_OPENAI_MODEL,
    MAX_MODEL_CANDIDATES,
    LLMProviderConfig,
    LLMProviderConfigurationError,
    LLMProviderSecrets,
    live_llm_tests_enabled,
    load_llm_provider_config,
    load_llm_provider_secrets,
)
from app.services.agent_team.llm_clients.contracts import (
    AGENT_TEAM_ROLES,
    LLM_PROVIDER_CONTRACT_VERSION,
    LLM_PROVIDER_STATUSES,
    AgentTeamRole,
    LLMProvider,
    LLMProviderMessage,
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderStatus,
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
    validate_llm_provider_payload,
)
from app.services.agent_team.llm_clients.factory import (
    LLMProviderResolution,
    UnavailableLLMProvider,
    resolve_llm_provider,
    resolve_llm_provider_from_env,
)
from app.services.agent_team.llm_clients.google import GoogleGeminiLLMProvider
from app.services.agent_team.llm_clients.mock import MockLLMProvider
from app.services.agent_team.llm_clients.openai import OpenAILLMProvider

__all__ = [
    "AGENT_TEAM_ROLES",
    "AgentTeamRole",
    "CHAIN_ADVANCE_STATUSES",
    "ChainedLLMProvider",
    "DEFAULT_LIVE_MODEL",
    "DEFAULT_MOCK_MODEL",
    "DEFAULT_OPENAI_MODEL",
    "GoogleGeminiLLMProvider",
    "LLM_PROVIDER_CONTRACT_VERSION",
    "LLM_PROVIDER_STATUSES",
    "LLMProvider",
    "LLMProviderConfig",
    "LLMProviderConfigurationError",
    "LLMProviderMessage",
    "LLMProviderRequest",
    "LLMProviderResolution",
    "LLMProviderResponse",
    "LLMProviderSecrets",
    "LLMProviderStatus",
    "MAX_MODEL_CANDIDATES",
    "MockLLMProvider",
    "OpenAILLMProvider",
    "UnavailableLLMProvider",
    "find_forbidden_string_values",
    "find_prohibited_llm_phrases",
    "find_secret_like_values",
    "live_llm_tests_enabled",
    "load_llm_provider_config",
    "load_llm_provider_secrets",
    "resolve_llm_provider",
    "resolve_llm_provider_from_env",
    "validate_llm_provider_payload",
]
