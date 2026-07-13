"""Deterministic mock LLM provider for Phase 19A tests and local previews."""

from datetime import UTC, datetime

from app.services.agent_team.llm_clients.contracts import (
    AGENT_TEAM_ROLES,
    LLMProviderFinishReason,
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderStatus,
)


_ROLE_OUTPUTS = {
    "fundamentals_analyst": (
        "Mock fundamentals analyst output. Analysis-only synthetic commentary "
        "over public company evidence. Deterministic metrics remain owned by backend services."
    ),
    "news_analyst": (
        "Mock news analyst output. Analysis-only synthetic commentary over mocked public news "
        "and macro event evidence. No live news provider was contacted."
    ),
    "technical_analyst": (
        "Mock technical analyst output. Analysis-only synthetic commentary over public or mocked "
        "market context. No live quote provider was contacted."
    ),
    "risk_management_agent": (
        "Mock risk management output. Analysis-only synthetic commentary over sanitized "
        "deterministic risk evidence, caveats, and freshness status."
    ),
    "portfolio_manager_agent": (
        "Mock portfolio manager synthesis. Analysis-only educational summary over prior "
        "role outputs, deterministic evidence, and stated limitations."
    ),
}


class MockLLMProvider:
    """No-network provider that returns deterministic synthetic role output."""

    provider_name = "mock"

    def __init__(
        self,
        *,
        model: str = "mock-agent-team-v1",
        failure_status_by_role: dict[str, LLMProviderStatus] | None = None,
        finish_reason_by_role: dict[str, LLMProviderFinishReason | None] | None = None,
    ) -> None:
        self.model = model
        self.failure_status_by_role = dict(failure_status_by_role or {})
        self.finish_reason_by_role = dict(finish_reason_by_role or {})

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        """Return a deterministic synthetic response or safe simulated failure."""

        if request.role_name not in AGENT_TEAM_ROLES:
            raise ValueError(f"unsupported agent-team role: {request.role_name}")
        failure_status = self.failure_status_by_role.get(request.role_name)
        if failure_status:
            return _failure_response(request, provider=self.provider_name, model=self.model, status=failure_status)
        content = _ROLE_OUTPUTS[request.role_name]
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=content,
            is_mock=True,
            finish_reason=self.finish_reason_by_role.get(request.role_name),
            generated_at=datetime.now(UTC),
            tokens_in=0,
            tokens_out=0,
            estimated_cost="0",
            metadata={
                "output_mode": "mock",
                "data_boundary": "synthetic_analysis_only",
            },
        )


def _failure_response(
    request: LLMProviderRequest,
    *,
    provider: str,
    model: str,
    status: LLMProviderStatus,
) -> LLMProviderResponse:
    if status == "ok":
        raise ValueError("failure status must not be ok")
    return LLMProviderResponse(
        request_id=request.request_id,
        role_name=request.role_name,
        status=status,
        provider=provider,
        model=model,
        prompt_version=request.prompt_version,
        content_markdown=None,
        is_mock=True,
        generated_at=datetime.now(UTC),
        error_code=status,
        error_message=f"Mock provider simulated {status}; partial analysis can continue with deterministic evidence.",
        tokens_in=0,
        tokens_out=0,
        estimated_cost="0",
        metadata={
            "output_mode": "mock_failure",
            "safe_partial_output": "true",
        },
    )
