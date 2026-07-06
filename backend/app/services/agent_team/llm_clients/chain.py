"""Ordered same-provider model-candidate chain (P34A-T10A).

Split out of the provider factory in P34A-T11A. Pure move: the chain
advance/abort semantics, sticky forward-only index, and additive chain
metadata are unchanged. The LLM never selects its own model; the candidate
order is backend configuration.
"""

from dataclasses import replace

from app.services.agent_team.llm_clients.config import LLMProviderConfigurationError
from app.services.agent_team.llm_clients.contracts import (
    LLMProvider,
    LLMProviderRequest,
    LLMProviderResponse,
)


# Availability-shaped statuses that advance the model chain to the next
# candidate (P34A-T10A binding decision). Auth errors abort the whole chain
# (same key for every candidate) and safety failures are never retried on
# another model — model-shopping past unsafe output is prohibited.
CHAIN_ADVANCE_STATUSES = frozenset(
    {
        "quota_exceeded",
        "rate_limited",
        "provider_unavailable",
        "provider_timeout",
        "invalid_response",
    }
)


class ChainedLLMProvider:
    """Ordered same-provider model chain behind the LLMProvider protocol.

    The configured candidate list IS the chain: no silent additions and no
    cross-provider fallback. The candidate index is sticky and forward-only
    for the lifetime of the resolved provider (one Agent Team run), so later
    roles skip models that already exhausted quota instead of re-failing on
    them. The LLM never selects its own model; the chain is backend config.
    """

    def __init__(self, *, providers: tuple[LLMProvider, ...]) -> None:
        if not providers:
            raise LLMProviderConfigurationError("model chain requires at least one provider")
        names = {getattr(provider, "provider_name", "") for provider in providers}
        if len(names) != 1:
            raise LLMProviderConfigurationError("model chain must use a single provider")
        self._providers = providers
        self._index = 0
        self.provider_name = providers[0].provider_name

    @property
    def model(self) -> str:
        return self._providers[self._index].model

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        attempted: list[str] = []
        response: LLMProviderResponse | None = None
        position = self._index
        while position < len(self._providers):
            provider = self._providers[position]
            response = provider.complete(request)
            attempted.append(provider.model)
            if response.status not in CHAIN_ADVANCE_STATUSES:
                break
            position += 1
        if position >= len(self._providers):
            position = len(self._providers) - 1
        self._index = max(self._index, position)
        if response is None:  # unreachable: the loop always runs at least once
            raise LLMProviderConfigurationError("model chain produced no provider response")
        return self._with_chain_metadata(response, position=position, attempted=tuple(attempted))

    def _with_chain_metadata(
        self,
        response: LLMProviderResponse,
        *,
        position: int,
        attempted: tuple[str, ...],
    ) -> LLMProviderResponse:
        metadata = {
            **response.metadata,
            "model_chain_position": str(position),
            "attempted_models": ",".join(attempted),
        }
        return replace(response, metadata=metadata)
