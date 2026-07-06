import socket
import sys
from dataclasses import asdict

import pytest

from app.services.agent_team.llm_clients.contracts import AGENT_TEAM_ROLES, LLMProviderMessage, LLMProviderRequest
from app.services.agent_team.llm_clients.mock import MockLLMProvider
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("role_name", AGENT_TEAM_ROLES)
def test_mock_provider_returns_deterministic_output_for_each_role(role_name: str) -> None:
    provider = MockLLMProvider()
    request = _request(role_name)

    first = provider.complete(request)
    second = provider.complete(request)

    assert first.status == "ok"
    assert first.provider == "mock"
    assert first.model == "mock-agent-team-v1"
    assert first.is_mock is True
    assert first.content_markdown == second.content_markdown
    assert "Mock" in first.content_markdown
    assert "Analysis-only" in first.content_markdown
    assert find_forbidden_keys(asdict(first), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()


def test_mock_provider_needs_no_api_key_and_makes_no_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    provider = MockLLMProvider()
    response = provider.complete(_request("news_analyst"))

    assert response.status == "ok"
    assert response.estimated_cost == "0"


@pytest.mark.parametrize("status", ("rate_limited", "quota_exceeded"))
def test_mock_provider_simulates_safe_partial_failure_metadata(status: str) -> None:
    provider = MockLLMProvider(failure_status_by_role={"technical_analyst": status})
    response = provider.complete(_request("technical_analyst"))

    assert response.status == status
    assert response.content_markdown is None
    assert response.error_code == status
    assert "partial analysis can continue with deterministic evidence" in response.error_message
    assert response.metadata["safe_partial_output"] == "true"
    assert find_forbidden_keys(asdict(response), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()


def test_mock_provider_rejects_prohibited_request_content() -> None:
    provider = MockLLMProvider()
    with pytest.raises(ValueError, match="prohibited advice"):
        provider.complete(
            LLMProviderRequest(
                request_id="req-bad",
                role_name="portfolio_manager_agent",
                messages=(LLMProviderMessage(role="user", content="Synthetic prompt says safe to trade."),),
            )
        )


def test_mock_provider_does_not_import_tradingagents() -> None:
    provider = MockLLMProvider()
    provider.complete(_request("fundamentals_analyst"))

    assert "tradingagents" not in sys.modules


def _request(role_name: str) -> LLMProviderRequest:
    return LLMProviderRequest(
        request_id=f"req-{role_name}",
        role_name=role_name,
        messages=(
            LLMProviderMessage(role="system", content="Synthetic analysis-only role prompt."),
            LLMProviderMessage(role="user", content="Synthetic public evidence prompt."),
        ),
    )
