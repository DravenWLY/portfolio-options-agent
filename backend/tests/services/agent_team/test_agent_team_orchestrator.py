from dataclasses import asdict
from datetime import date
import sys

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.llm_clients.contracts import (
    AGENT_TEAM_ROLES,
    LLMProviderRequest,
    LLMProviderResponse,
    find_forbidden_string_values,
)
from app.services.agent_team.llm_clients.mock import MockLLMProvider
from app.services.agent_team.legacy_console.orchestrator import AgentTeamOrchestrator, default_agent_team_stage_order
from app.services.agent_team.llm_clients.factory import LLMProviderResolution, UnavailableLLMProvider
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.unit]


def test_orchestrator_runs_exact_stage_order_with_mock_provider() -> None:
    workspace = _workspace()
    state = AgentTeamOrchestrator().run(workspace=workspace)

    assert tuple(stage.stage for stage in state.stage_statuses) == default_agent_team_stage_order()
    assert tuple(output.role_name for output in state.role_outputs) == AGENT_TEAM_ROLES
    assert state.run_status == "completed"
    assert state.workflow_version == "agent-team-analysis-v1"
    assert state.review_actionability_status == workspace.actionability.review_actionability_status
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"
    assert find_forbidden_keys(state.__dict__, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()


def test_orchestrator_degrades_provider_failures_to_partial_output() -> None:
    workspace = _workspace()
    provider = MockLLMProvider(failure_status_by_role={"news_analyst": "rate_limited"})
    state = AgentTeamOrchestrator(provider=provider).run(workspace=workspace)

    news = next(output for output in state.role_outputs if output.role_name == "news_analyst")
    assert state.run_status == "partially_completed"
    assert news.status == "unavailable"
    assert news.provider_status == "rate_limited"
    assert "news_analyst:rate_limited" in state.provider_warnings
    assert next(stage for stage in state.stage_statuses if stage.stage == "news_analyst").status == "unavailable"


def test_orchestrator_keeps_deterministic_review_as_input_fast_path() -> None:
    workspace = _workspace()
    state = AgentTeamOrchestrator().run(workspace=workspace)

    assert state.deterministic_evidence_summary["risk_summary"]["has_blocker"] == (
        workspace.deterministic_review.has_blocker
    )
    assert state.deterministic_evidence_summary["portfolio_shape"]["stock_position_count"] == 2
    assert "provider:mock" in state.safety_flags


def test_orchestrator_does_not_import_tradingagents() -> None:
    AgentTeamOrchestrator().run(workspace=_workspace())

    assert "tradingagents" not in sys.modules


def test_orchestrator_preserves_deterministic_evidence_when_provider_unavailable() -> None:
    workspace = _workspace()
    resolution = LLMProviderResolution(
        provider=UnavailableLLMProvider(
            provider_name="google",
            model="gemini-synthetic",
            status="provider_auth_error",
            error_message="Google provider credential is unavailable; deterministic evidence remains available.",
        ),
        status="provider_auth_error",
        provider_name="google",
        model="gemini-synthetic",
    )

    state = AgentTeamOrchestrator(provider_resolution=resolution).run(workspace=workspace)

    assert state.run_status == "partially_completed"
    assert all(output.status == "unavailable" for output in state.role_outputs)
    assert state.deterministic_evidence_summary["risk_summary"]["has_blocker"] == workspace.deterministic_review.has_blocker
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"


def test_orchestrator_allows_live_provider_domain_words_in_generated_output() -> None:
    workspace = _workspace()
    state = AgentTeamOrchestrator(provider=_DomainWordProvider()).run(workspace=workspace)

    assert state.run_status == "completed"
    assert len(state.role_outputs) == 5
    assert all(output.provider_status == "ok" for output in state.role_outputs)
    assert state.role_outputs[0].content_markdown is not None
    assert "cash flow" in state.role_outputs[0].content_markdown


def test_orchestrator_emits_p19c_prompt_inputs_to_provider_requests() -> None:
    provider = _CapturingProvider()
    AgentTeamOrchestrator(provider=provider).run(workspace=_workspace())

    assert tuple(request.role_name for request in provider.requests) == AGENT_TEAM_ROLES
    for request in provider.requests:
        request_payload = asdict(request)
        assert find_forbidden_keys(request_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
        assert find_forbidden_string_values(request_payload) == set()
        rendered = "\n".join(message.content for message in request.messages)
        if request.role_name in PUBLIC_ANALYST_ROLES:
            assert "agent_safe_deterministic_projection" not in rendered
            assert "portfolio_shape_summary" not in rendered
            assert "deterministic_risk_summary" not in rendered
            assert "actionability_summary" not in rendered
            assert "broker_snapshot_freshness" not in rendered
            assert "market_quote_freshness" not in rendered
        else:
            assert "'evidence_mode': 'agent_safe_deterministic_projection'" in rendered
            assert "'deterministic_metric_source': 'backend_owned_not_llm_generated'" in rendered
            assert "'broker_snapshot_freshness': {'freshness_scope': 'broker_snapshot'" in rendered
            assert "'market_quote_freshness': {'freshness_scope': 'market_quote'" in rendered


def _workspace():
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy",
            symbol="XYZ",
            quantity="3",
            price_assumption="50",
            portfolio_context_selection={"mode": "latest_available"},
        )
    )


class _DomainWordProvider:
    provider_name = "google"
    model = "gemini-synthetic"

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=(
                "Generic educational text mentioning cash flow, holdings narratives, "
                "and position sizing without any numbers or identifiers."
            ),
            is_mock=False,
        )


class _CapturingProvider:
    provider_name = "mock"
    model = "mock-agent-team-v1"

    def __init__(self) -> None:
        self.requests: list[LLMProviderRequest] = []

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        self.requests.append(request)
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown="Synthetic analysis-only role output.",
            is_mock=True,
        )
