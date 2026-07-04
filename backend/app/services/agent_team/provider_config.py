"""Backend-owned provider configuration for the LLM provider gate.

Normal tests should pass explicit mappings/secrets and never depend on process
environment, ``.env`` files, or real API keys. Live tests remain opt-in and
external.
"""

from dataclasses import asdict, dataclass, field
from typing import Literal, Mapping

from app.services.agent_team.llm_provider import validate_llm_provider_payload


LLMMode = Literal["mock", "live"]
LLMProviderName = Literal["mock", "google", "openai"]
LLMRateLimitFallback = Literal["partial_report"]

DEFAULT_MOCK_MODEL = "mock-agent-team-v1"
DEFAULT_LIVE_MODEL = "gemini-1.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class LLMProviderConfigurationError(ValueError):
    """Safe provider configuration error that never carries secret values."""


@dataclass(frozen=True)
class LLMProviderConfig:
    """Sanitized provider config safe to pass around backend services."""

    mode: LLMMode = "mock"
    provider: LLMProviderName = "mock"
    model: str = DEFAULT_MOCK_MODEL
    timeout_seconds: int = 30
    max_retries: int = 0
    token_budget_per_run: int = 4000
    rate_limit_fallback: LLMRateLimitFallback = "partial_report"
    live_tests_enabled: bool = False
    google_credential_available: bool = False
    openai_credential_available: bool = False

    def __post_init__(self) -> None:
        if self.mode not in {"mock", "live"}:
            raise LLMProviderConfigurationError("POA_LLM_MODE must be mock or live")
        if self.provider not in {"mock", "google", "openai"}:
            raise LLMProviderConfigurationError("POA_LLM_PROVIDER must be mock, google, or openai")
        if not self.model.strip():
            raise LLMProviderConfigurationError("POA_LLM_MODEL must not be empty")
        if self.timeout_seconds <= 0:
            raise LLMProviderConfigurationError("POA_LLM_TIMEOUT_SECONDS must be positive")
        if self.max_retries < 0:
            raise LLMProviderConfigurationError("POA_LLM_MAX_RETRIES must be non-negative")
        if self.token_budget_per_run <= 0:
            raise LLMProviderConfigurationError("POA_LLM_TOKEN_BUDGET_PER_RUN must be positive")
        if self.rate_limit_fallback != "partial_report":
            raise LLMProviderConfigurationError("POA_LLM_RATE_LIMIT_FALLBACK must be partial_report")
        if self.mode == "mock" and self.provider != "mock":
            raise LLMProviderConfigurationError("mock mode requires mock provider")
        if self.mode == "live" and self.provider not in {"google", "openai"}:
            raise LLMProviderConfigurationError("live mode supports google or openai provider only")
        if self.mode == "live" and self.provider == "google" and not self.google_credential_available:
            raise LLMProviderConfigurationError("live google mode requires backend Google API key")
        if self.mode == "live" and self.provider == "openai" and not self.openai_credential_available:
            raise LLMProviderConfigurationError("live openai mode requires backend OpenAI API key")
        validate_llm_provider_payload(asdict(self), label="LLM provider config")

    def public_snapshot(self) -> dict[str, object]:
        """Return non-secret config metadata safe for diagnostics/tests."""

        return {
            "mode": self.mode,
            "provider": self.provider,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "token_budget_per_run": self.token_budget_per_run,
            "rate_limit_fallback": self.rate_limit_fallback,
            "live_tests_enabled": self.live_tests_enabled,
            "google_credential_configured": self.google_credential_available,
            "openai_credential_configured": self.openai_credential_available,
        }


@dataclass(frozen=True)
class LLMProviderSecrets:
    """Secret provider values kept out of repr/public snapshots.

    Tests may construct this with fake values such as ``"test-key-not-real"``.
    The object is intentionally separate from ``LLMProviderConfig`` so safe
    diagnostics/config snapshots never contain credential values.
    """

    google_api_key: str | None = field(default=None, repr=False)
    openai_api_key: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "google_api_key", _optional_secret(self.google_api_key))
        object.__setattr__(self, "openai_api_key", _optional_secret(self.openai_api_key))

    @property
    def google_credential_available(self) -> bool:
        return self.google_api_key is not None

    @property
    def openai_credential_available(self) -> bool:
        return self.openai_api_key is not None

    def public_snapshot(self) -> dict[str, bool]:
        return {
            "google_credential_configured": self.google_credential_available,
            "openai_credential_configured": self.openai_credential_available,
        }


def load_llm_provider_config(env: Mapping[str, str] | None = None) -> LLMProviderConfig:
    """Build provider config from an explicit environment mapping.

    The returned object stores only key availability, never the key value.
    """

    values = env or {}
    mode = _text(values.get("POA_LLM_MODE"), default="mock").lower()
    provider = _text(values.get("POA_LLM_PROVIDER"), default="mock" if mode == "mock" else "google").lower()
    if mode == "mock":
        default_model = DEFAULT_MOCK_MODEL
    elif provider == "openai":
        default_model = DEFAULT_OPENAI_MODEL
    else:
        default_model = DEFAULT_LIVE_MODEL
    model = _text(values.get("POA_LLM_MODEL"), default=default_model)
    return LLMProviderConfig(
        mode=mode,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        model=model,
        timeout_seconds=_int(values.get("POA_LLM_TIMEOUT_SECONDS"), default=30),
        max_retries=_int(values.get("POA_LLM_MAX_RETRIES"), default=0),
        token_budget_per_run=_int(values.get("POA_LLM_TOKEN_BUDGET_PER_RUN"), default=4000),
        rate_limit_fallback=_text(values.get("POA_LLM_RATE_LIMIT_FALLBACK"), default="partial_report"),  # type: ignore[arg-type]
        live_tests_enabled=live_llm_tests_enabled(values),
        google_credential_available=bool(_text(values.get("GOOGLE_API_KEY"), default="")),
        openai_credential_available=bool(_text(values.get("OPENAI_API_KEY"), default="")),
    )


def load_llm_provider_secrets(env: Mapping[str, str] | None = None) -> LLMProviderSecrets:
    """Load provider secrets from an explicit mapping.

    Passing ``None`` returns an empty secret set. Process environment access is
    centralized in provider_factory's ``*_from_env`` boundary.
    """

    values = env or {}
    return LLMProviderSecrets(
        google_api_key=values.get("GOOGLE_API_KEY"),
        openai_api_key=values.get("OPENAI_API_KEY"),
    )


def live_llm_tests_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Return whether live LLM tests are explicitly enabled.

    ``RUN_LIVE_LLM_TESTS`` is the generic test flag; ``POA_LLM_LIVE_TESTS`` is
    kept as the existing project-specific alias.
    """

    values = env or {}
    return _bool(values.get("RUN_LIVE_LLM_TESTS"), default=False) or _bool(
        values.get("POA_LLM_LIVE_TESTS"), default=False
    )


def _text(value: str | None, *, default: str) -> str:
    if value is None:
        return default
    text = value.strip()
    return text or default


def _int(value: str | None, *, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise LLMProviderConfigurationError("LLM provider numeric config must be an integer") from exc


def _bool(value: str | None, *, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _optional_secret(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None
