import sys

import pytest

from app.services.agent_team.llm_provider import (
    AGENT_TEAM_ROLES,
    LLM_PROVIDER_STATUSES,
    LLMProviderMessage,
    LLMProviderRequest,
    LLMProviderResponse,
    validate_llm_provider_payload,
)


pytestmark = [pytest.mark.unit]


def test_role_and_status_vocabularies_are_stable() -> None:
    assert AGENT_TEAM_ROLES == (
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "risk_management_agent",
        "portfolio_manager_agent",
    )
    assert LLM_PROVIDER_STATUSES == (
        "ok",
        "skipped",
        "failed",
        "rate_limited",
        "quota_exceeded",
        "provider_timeout",
        "provider_auth_error",
        "provider_unavailable",
        "invalid_response",
        "safety_validation_failed",
    )


def test_provider_request_shape_is_safe_and_typed() -> None:
    request = _request("fundamentals_analyst")

    assert request.provider == "mock"
    assert request.model == "mock-agent-team-v1"
    assert request.messages[0].role == "system"
    assert request.contract_version == "llm-provider-contract-v1"


def test_provider_request_rejects_forbidden_private_keys_recursively() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        LLMProviderRequest(
            request_id="req-1",
            role_name="risk_management_agent",
            messages=(LLMProviderMessage(role="user", content="Synthetic prompt."),),
            metadata={"nested": {"provider_account_id": "private"}},
        )


@pytest.mark.parametrize(
    "token",
    (
        "broker_account_id",
        "provider_account_id",
        "account_value",
        "cash",
        "holdings",
        "positions",
        "threshold",
        "raw_payload",
        "api_key",
    ),
)
def test_provider_request_rejects_private_string_values(token: str) -> None:
    with pytest.raises(ValueError, match="forbidden private value"):
        LLMProviderRequest(
            request_id="req-1",
            role_name="news_analyst",
            messages=(LLMProviderMessage(role="user", content=f"Synthetic {token} prompt."),),
        )


@pytest.mark.parametrize(
    "phrase",
    (
        "you should buy",
        "you should sell",
        "safe to trade",
        "ready to trade",
        "guaranteed return",
        "place an order",
        "execute the trade",
    ),
)
def test_provider_request_rejects_prohibited_advice_and_execution_phrases(phrase: str) -> None:
    with pytest.raises(ValueError, match="prohibited advice"):
        LLMProviderMessage(role="user", content=f"Synthetic prompt says {phrase}.")


def test_provider_response_rejects_private_keys_values_and_prohibited_phrases() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        LLMProviderResponse(
            request_id="req-1",
            role_name="portfolio_manager_agent",
            status="ok",
            provider="mock",
            model="mock",
            prompt_version="v1",
            content_markdown="Synthetic output.",
            is_mock=True,
            metadata={"account_id": "private"},
        )
    with pytest.raises(ValueError, match="private identifier"):
        LLMProviderResponse(
            request_id="req-1",
            role_name="portfolio_manager_agent",
            status="ok",
            provider="mock",
            model="mock",
            prompt_version="v1",
            content_markdown="Synthetic output mentions raw_payload.",
            is_mock=True,
        )
    with pytest.raises(ValueError, match="prohibited advice"):
        LLMProviderResponse(
            request_id="req-1",
            role_name="portfolio_manager_agent",
            status="ok",
            provider="mock",
            model="mock",
            prompt_version="v1",
            content_markdown="Synthetic output says ready to trade.",
            is_mock=True,
        )


def test_provider_response_allows_generic_domain_words_without_private_identifiers() -> None:
    response = LLMProviderResponse(
        request_id="req-1",
        role_name="portfolio_manager_agent",
        status="ok",
        provider="mock",
        model="mock",
        prompt_version="v1",
        content_markdown="Generic analysis can mention cash, positions, and thresholds without numeric claims.",
        is_mock=True,
    )

    assert response.status == "ok"


def test_validate_llm_provider_payload_rejects_nested_private_tokens() -> None:
    with pytest.raises(ValueError, match="forbidden private value"):
        validate_llm_provider_payload({"safe": ["public", {"note": "provider_account_id"}]}, label="synthetic")


def test_contract_import_does_not_import_tradingagents() -> None:
    assert "tradingagents" not in sys.modules


def _request(role_name: str) -> LLMProviderRequest:
    return LLMProviderRequest(
        request_id=f"req-{role_name}",
        role_name=role_name,
        messages=(
            LLMProviderMessage(role="system", content="Synthetic analysis-only system prompt."),
            LLMProviderMessage(role="user", content="Synthetic public prompt."),
        ),
    )
