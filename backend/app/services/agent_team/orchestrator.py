"""Synchronous mock agent-team orchestrator for Phase 19A."""

from datetime import UTC, datetime

from app.schemas.trade_review_workspace import TradeReviewWorkspaceRead
from app.services.agent_team.evidence import public_evidence_from_workspace
from app.services.agent_team.evidence_projection import build_agent_safe_deterministic_evidence
from app.services.agent_team.llm_provider import AGENT_TEAM_ROLES, AgentTeamRole, LLMProvider
from app.services.agent_team.prompt_inputs import build_agent_team_prompt_input
from app.services.agent_team.prompt_safety import validate_agent_team_text
from app.services.agent_team.prompts import render_prompt_input_messages
from app.services.agent_team.provider_factory import LLMProviderResolution, resolve_llm_provider_from_env
from app.services.agent_team.roles import PUBLIC_ANALYST_ROLES
from app.services.agent_team.state import (
    AGENT_TEAM_WORKFLOW_VERSION,
    DEFAULT_AGENT_TEAM_STAGE_ORDER,
    AgentTeamAnalysisState,
    AgentTeamRoleOutput,
    AgentTeamStageStatus,
)


class AgentTeamOrchestrator:
    """App-owned workflow runner using the mock LLM provider by default."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_resolution: LLMProviderResolution | None = None,
    ) -> None:
        resolution = provider_resolution or (None if provider is not None else resolve_llm_provider_from_env())
        self.provider = provider or (resolution.provider if resolution else None)
        if self.provider is None:
            raise ValueError("AgentTeamOrchestrator requires an LLM provider")

    def run(self, *, workspace: TradeReviewWorkspaceRead, generated_at: datetime | None = None) -> AgentTeamAnalysisState:
        generated = generated_at or datetime.now(UTC)
        public_evidence = public_evidence_from_workspace(workspace)
        deterministic_evidence = build_agent_safe_deterministic_evidence(workspace)
        role_outputs: list[AgentTeamRoleOutput] = []
        stage_statuses: list[AgentTeamStageStatus] = [
            AgentTeamStageStatus(stage="validate_trade_intent", status="completed"),
            AgentTeamStageStatus(stage="build_deterministic_evidence_bundle", status="completed"),
            AgentTeamStageStatus(stage="classify_actionability", status="completed"),
            AgentTeamStageStatus(stage="prepare_public_evidence_context", status="completed"),
        ]
        prior_summaries: list[str] = []
        provider_warnings: list[str] = []

        for role_name in AGENT_TEAM_ROLES:
            prompt_input = build_agent_team_prompt_input(
                role_name=role_name,
                public_evidence=public_evidence,
                deterministic_evidence=deterministic_evidence
                if role_name not in PUBLIC_ANALYST_ROLES
                else None,
                prior_role_summaries=tuple(prior_summaries),
            )
            messages = render_prompt_input_messages(prompt_input)
            response = self.provider.complete(
                request=_provider_request(
                    workspace=workspace,
                    role_name=role_name,
                    messages=messages,
                    provider_name=self.provider.provider_name,
                    model=self.provider.model,
                )
            )
            role_output = AgentTeamRoleOutput.from_provider_response(response)
            role_outputs.append(role_output)
            stage_statuses.append(
                AgentTeamStageStatus(
                    stage=role_name,
                    status="completed" if response.status == "ok" else "unavailable",
                    role_name=role_name,
                    provider_status=response.status,
                    unavailable_reason=response.error_message,
                )
            )
            if response.content_markdown:
                prior_summaries.append(_prompt_safe_prior_summary(response.content_markdown))
            if response.status != "ok":
                provider_warnings.append(f"{role_name}:{response.status}")

        final_synthesis = _compose_final_synthesis(role_outputs)
        stage_statuses.append(AgentTeamStageStatus(stage="compose_analysis_console_output", status="completed"))
        stage_statuses.append(
            AgentTeamStageStatus(
                stage="persist_run_steps",
                status="skipped",
                unavailable_reason="stateless_mock_preview_no_persistence",
            )
        )
        run_status = "partially_completed" if provider_warnings else "completed"

        return AgentTeamAnalysisState(
            run_reference=f"agent-team-{workspace.review_reference}",
            workflow_version=AGENT_TEAM_WORKFLOW_VERSION,
            generated_at=generated,
            review_flow_label=deterministic_evidence.review_flow_label,
            review_actionability_status=workspace.actionability.review_actionability_status,
            broker_snapshot_freshness=deterministic_evidence.broker_snapshot_freshness,
            market_quote_freshness=deterministic_evidence.market_quote_freshness,
            deterministic_evidence_summary={
                "review_flow_label": deterministic_evidence.review_flow_label,
                "actionability_summary": deterministic_evidence.actionability_summary,
                "risk_summary": deterministic_evidence.deterministic_risk_summary,
                "portfolio_shape": _legacy_portfolio_shape_summary(deterministic_evidence.portfolio_shape_summary),
                "caveat_codes": deterministic_evidence.caveat_codes,
            },
            role_outputs=tuple(role_outputs),
            stage_statuses=tuple(stage_statuses),
            provider_warnings=tuple(provider_warnings),
            final_synthesis=final_synthesis,
            run_status=run_status,
            safety_flags=(
                f"provider:{self.provider.provider_name}",
                "analysis_only",
                "deterministic_metrics_owned_by_backend",
            ),
        )


def _provider_request(
    *,
    workspace: TradeReviewWorkspaceRead,
    role_name: AgentTeamRole,
    messages,
    provider_name: str,
    model: str,
):
    from app.services.agent_team.llm_provider import LLMProviderRequest

    return LLMProviderRequest(
        request_id=f"{workspace.review_reference}:{role_name}",
        role_name=role_name,
        messages=tuple(messages),
        provider=provider_name,
        model=model,
        prompt_version="agent-team-prompt-v1",
        metadata={
            "workflow_version": AGENT_TEAM_WORKFLOW_VERSION,
            "review_reference": workspace.review_reference,
        },
    )


def _compose_final_synthesis(role_outputs: list[AgentTeamRoleOutput]) -> str:
    completed = [output.role_name for output in role_outputs if output.provider_status == "ok"]
    unavailable = [output.role_name for output in role_outputs if output.provider_status != "ok"]
    text = (
        "Mock portfolio-team synthesis. Analysis-only educational summary based on "
        f"{len(completed)} completed role output(s). Deterministic backend services own all calculations."
    )
    if unavailable:
        text += f" Some mock role output was unavailable: {', '.join(unavailable)}."
    return text


def _legacy_portfolio_shape_summary(summary: dict[str, object]) -> dict[str, object]:
    return {
        "context_available": summary["context_available"],
        "stock_position_count": summary["equity_position_count"],
        "option_position_count": summary["option_position_count"],
        "liquidity_state": summary["liquidity_state"],
    }


def _prompt_safe_prior_summary(content_markdown: str) -> str:
    try:
        validate_agent_team_text(content_markdown, label="prior role summary prompt reuse")
    except ValueError:
        return "Prior role output passed output safety but was withheld from strict prompt reuse."
    return content_markdown


def default_agent_team_stage_order() -> tuple[str, ...]:
    return DEFAULT_AGENT_TEAM_STAGE_ORDER
