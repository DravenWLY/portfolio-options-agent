"""Backend-owned provider configuration for the Phase 19B LLM provider gate."""

from dataclasses import asdict, dataclass
from typing import Literal, Mapping

from app.services.agent_team.llm_provider import validate_llm_provider_payload


LLMMode = Literal["mock", "live"]
LLMProviderName = Literal["mock", "google"]
LLMRateLimitFallback = Literal["partial_report"]

DEFAULT_MOCK_MODEL = "mock-agent-team-v1"
DEFAULT_LIVE_MODEL = "gemini-1.5-flash"


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

    def __post_init__(self) -> None:
        if self.mode not in {"mock", "live"}:
            raise LLMProviderConfigurationError("POA_LLM_MODE must be mock or live")
        if self.provider not in {"mock", "google"}:
            raise LLMProviderConfigurationError("POA_LLM_PROVIDER must be mock or google")
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
        if self.mode == "live" and self.provider != "google":
            raise LLMProviderConfigurationError("live mode currently supports google provider only")
        if self.mode == "live" and not self.google_credential_available:
            raise LLMProviderConfigurationError("live google mode requires backend Google API key")
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
        }


def load_llm_provider_config(env: Mapping[str, str] | None = None) -> LLMProviderConfig:
    """Build provider config from an explicit environment mapping.

    The returned object stores only key availability, never the key value.
    """

    values = env or {}
    mode = _text(values.get("POA_LLM_MODE"), default="mock").lower()
    provider = _text(values.get("POA_LLM_PROVIDER"), default="mock" if mode == "mock" else "google").lower()
    model = _text(
        values.get("POA_LLM_MODEL"),
        default=DEFAULT_MOCK_MODEL if mode == "mock" else DEFAULT_LIVE_MODEL,
    )
    return LLMProviderConfig(
        mode=mode,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        model=model,
        timeout_seconds=_int(values.get("POA_LLM_TIMEOUT_SECONDS"), default=30),
        max_retries=_int(values.get("POA_LLM_MAX_RETRIES"), default=0),
        token_budget_per_run=_int(values.get("POA_LLM_TOKEN_BUDGET_PER_RUN"), default=4000),
        rate_limit_fallback=_text(values.get("POA_LLM_RATE_LIMIT_FALLBACK"), default="partial_report"),  # type: ignore[arg-type]
        live_tests_enabled=_bool(values.get("POA_LLM_LIVE_TESTS"), default=False),
        google_credential_available=bool(_text(values.get("GOOGLE_API_KEY"), default="")),
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
