"""Google/Gemini provider adapter boundary with lazy SDK construction.

Default tests use injected fake clients. The Google SDK is imported only if a
live Google provider is explicitly configured and no client was injected.
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Protocol

from app.services.agent_team.llm_provider import LLMProviderRequest, LLMProviderResponse, LLMProviderStatus


class GoogleGeminiClient(Protocol):
    def generate(self, request: LLMProviderRequest) -> str:
        """Return generated text for a provider request."""


@dataclass(frozen=True)
class GoogleGeminiProviderError(Exception):
    status: LLMProviderStatus
    safe_message: str = "Google provider request failed safely."


class GoogleGeminiLLMProvider:
    """Google/Gemini implementation behind the app-owned provider protocol."""

    provider_name = "google"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        client: GoogleGeminiClient | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 0,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._client = client
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        """Call an injected or lazy Google client and map output into a safe response."""

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
                metadata={"provider_mode": "live_google"},
            )
        except GoogleGeminiProviderError as exc:
            return self._failure_response(request, status=_safe_status(exc.status), safe_message=exc.safe_message)
        except TimeoutError:
            return self._failure_response(request, status="provider_timeout")
        except ValueError:
            return self._failure_response(request, status="safety_validation_failed")
        except Exception:
            return self._failure_response(request, status="provider_unavailable")

    def _build_default_client(self) -> GoogleGeminiClient:
        if not self._api_key:
            raise GoogleGeminiProviderError(status="provider_auth_error")
        try:
            genai = import_module("google.genai")
        except Exception as exc:
            raise GoogleGeminiProviderError(status="provider_unavailable") from exc
        return _GoogleGenAIClient(genai=genai, api_key=self._api_key, model=self.model)

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


class _GoogleGenAIClient:
    """Lazy google-genai client; constructed only for live Gemini use."""

    def __init__(self, *, genai, api_key: str, model: str) -> None:  # noqa: ANN001
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, request: LLMProviderRequest) -> str:
        prompt = "\n\n".join(message.content for message in request.messages)
        response = self._client.models.generate_content(model=self._model, contents=prompt)
        text = getattr(response, "text", None)
        if not isinstance(text, str):
            raise GoogleGeminiProviderError(status="invalid_response")
        return text


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
        "rate_limited": "Google provider rate limit reached; deterministic evidence remains available.",
        "quota_exceeded": "Google provider quota exceeded; deterministic evidence remains available.",
        "provider_timeout": "Google provider timed out; deterministic evidence remains available.",
        "provider_auth_error": "Google provider is not authorized; deterministic evidence remains available.",
        "provider_unavailable": "Google provider is unavailable; deterministic evidence remains available.",
        "invalid_response": "Google provider returned an invalid response; deterministic evidence remains available.",
        "safety_validation_failed": "Google provider output failed safety validation; deterministic evidence remains available.",
    }
    return messages.get(status, "Google provider request failed; deterministic evidence remains available.")
