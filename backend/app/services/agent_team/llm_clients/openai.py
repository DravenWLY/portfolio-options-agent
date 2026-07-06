"""OpenAI provider adapter behind the app-owned ``LLMProvider`` protocol.

Backend-only. This is **not** the OpenAI Agents SDK — it uses the plain OpenAI
chat-completions client, imported lazily only when a live OpenAI provider is
explicitly configured and no client was injected. Default tests inject a fake
client; the default suite makes no live call. Errors map to existing safe
provider statuses and never leak raw exception bodies, raw provider payloads,
URLs with keys, or API keys.
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Protocol

from app.services.agent_team.llm_clients.contracts import (
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderStatus,
)


class OpenAIChatClient(Protocol):
    def generate(self, request: LLMProviderRequest) -> str:
        """Return generated text for a provider request."""


@dataclass(frozen=True)
class OpenAIProviderError(Exception):
    status: LLMProviderStatus
    safe_message: str = "OpenAI provider request failed safely."


class OpenAILLMProvider:
    """OpenAI implementation behind the app-owned provider protocol."""

    provider_name = "openai"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        client: OpenAIChatClient | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 0,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._client = client
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        """Call an injected or lazy OpenAI client and map output into a safe response."""

        try:
            client = self._client or self._build_default_client()
            content = client.generate(request)
            if not isinstance(content, str) or not content.strip():
                return self._failure_response(request, status="invalid_response")
            return LLMProviderResponse(
                request_id=request.request_id,
                role_name=request.role_name,
                status="ok",
                provider=self.provider_name,
                model=self.model,
                prompt_version=request.prompt_version,
                content_markdown=content,
                is_mock=False,
                tokens_in=None,
                tokens_out=None,
                estimated_cost=None,
                metadata={"provider_mode": "live_openai"},
            )
        except OpenAIProviderError as exc:
            return self._failure_response(request, status=_safe_status(exc.status), safe_message=exc.safe_message)
        except TimeoutError:
            return self._failure_response(request, status="provider_timeout")
        except ValueError:
            return self._failure_response(request, status="safety_validation_failed")
        except Exception:
            return self._failure_response(request, status="provider_unavailable")

    def _build_default_client(self) -> OpenAIChatClient:
        if not self._api_key:
            raise OpenAIProviderError(status="provider_auth_error")
        try:
            openai = import_module("openai")
        except Exception as exc:
            raise OpenAIProviderError(status="provider_unavailable") from exc
        return _OpenAIChatCompletionsClient(
            openai=openai, api_key=self._api_key, model=self.model, timeout_seconds=self.timeout_seconds
        )

    def _failure_response(
        self,
        request: LLMProviderRequest,
        *,
        status: LLMProviderStatus,
        safe_message: str | None = None,
    ) -> LLMProviderResponse:
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status=status,
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=None,
            is_mock=False,
            error_code=status,
            error_message=safe_message or _safe_error_message(status),
            tokens_in=None,
            tokens_out=None,
            estimated_cost=None,
            metadata={"safe_partial_output": "true"},
        )


class _OpenAIChatCompletionsClient:
    """Lazy plain-SDK chat client. Constructed only for live OpenAI use."""

    def __init__(self, *, openai, api_key: str, model: str, timeout_seconds: int) -> None:  # noqa: ANN001
        self._client = openai.OpenAI(api_key=api_key, timeout=timeout_seconds)
        self._model = model

    def generate(self, request: LLMProviderRequest) -> str:
        messages = [{"role": message.role, "content": message.content} for message in request.messages]
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except Exception as exc:  # map without leaking the raw exception/body
            raise OpenAIProviderError(status=_map_openai_exception(exc)) from None
        text = response.choices[0].message.content if getattr(response, "choices", None) else None
        if not isinstance(text, str):
            raise OpenAIProviderError(status="invalid_response")
        return text


def _map_openai_exception(exc: Exception) -> LLMProviderStatus:
    """Map an SDK exception to a safe status by class name only (no body)."""

    name = type(exc).__name__.lower()
    if "ratelimit" in name:
        return "rate_limited"
    if "timeout" in name:
        return "provider_timeout"
    if "authentication" in name or "permission" in name:
        return "provider_auth_error"
    return "provider_unavailable"


def _safe_status(status: str) -> LLMProviderStatus:
    allowed: set[str] = {
        "rate_limited",
        "quota_exceeded",
        "provider_timeout",
        "provider_auth_error",
        "provider_unavailable",
        "invalid_response",
        "safety_validation_failed",
        "failed",
    }
    return status if status in allowed else "failed"  # type: ignore[return-value]


def _safe_error_message(status: str) -> str:
    messages = {
        "rate_limited": "OpenAI provider rate limit reached; deterministic evidence remains available.",
        "quota_exceeded": "OpenAI provider quota exceeded; deterministic evidence remains available.",
        "provider_timeout": "OpenAI provider timed out; deterministic evidence remains available.",
        "provider_auth_error": "OpenAI provider is not authorized; deterministic evidence remains available.",
        "provider_unavailable": "OpenAI provider is unavailable; deterministic evidence remains available.",
        "invalid_response": "OpenAI provider returned an invalid response; deterministic evidence remains available.",
        "safety_validation_failed": "OpenAI provider output failed safety validation; deterministic evidence remains available.",
    }
    return messages.get(status, "OpenAI provider request failed; deterministic evidence remains available.")
