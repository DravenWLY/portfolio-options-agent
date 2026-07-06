# DEPRECATED (P34A-T11C): legacy P19/P25 Agent Console preview path. Bug-fix
# only; superseded by the tool-mediated saved-report pipeline. Do not extend.
"""Thin app-owned mock workflow runner for Phase 25A (P25A-T1).

``ReviewRunner`` wraps the existing agent-team foundations (evidence projection,
role-specific prompt inputs, provider boundary, output safety) to produce an
``AgentReviewRunState``. It is additive: it does NOT modify the existing
``AgentTeamOrchestrator`` or the stateless preview route, and it introduces no
persistence, no API schema, and no live calls.

Design points (ADR 0008):
- Mock provider is the default; live calls are out of scope here.
- Deterministic evidence is preserved regardless of role outcomes.
- A blocked/unknown actionability status short-circuits all LLM role calls and
  returns a safe deterministic-only run state.
- Role dispatch goes through an **async-ready seam** that runs **sequentially**
  in P25A-T1. There is no asyncio fan-out, no concurrency, and no semaphore.
  Public-evidence roles are grouped (they are mutually independent and consume
  no prior summaries) to mark the future fan-out point; portfolio-aware roles
  stay ordered and gated. Results aggregate by stable role key.
- Role names are unchanged (Phase 19 names; rename is a separate slice).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

from app.services.agent_team.legacy_console.evidence import public_evidence_from_workspace
from app.services.agent_team.legacy_console.evidence_projection import (
    AgentSafeDeterministicEvidenceProjection,
    build_agent_safe_deterministic_evidence,
)
from app.services.agent_team.llm_clients.contracts import (
    AGENT_TEAM_ROLES,
    AgentTeamRole,
    LLMProvider,
    LLMProviderRequest,
    LLMProviderResponse,
    find_forbidden_string_values,
    find_secret_like_values,
)
from app.services.agent_team.legacy_console.prompt_inputs import build_agent_team_prompt_input
from app.services.agent_team.safety.prompt_safety import validate_agent_team_text
from app.services.agent_team.legacy_console.prompts import render_prompt_input_messages
from app.services.agent_team.llm_clients.factory import resolve_llm_provider_from_env
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES
from app.services.agent_team.legacy_console.run_state import (
    AgentReviewBudgetSummary,
    AgentReviewEvalFlag,
    AgentReviewRoleOutput,
    AgentReviewRunState,
    AgentReviewStageStatus,
    AgentReviewTimingSummary,
)
from app.schemas.trade_review_workspace import TradeReviewWorkspaceRead


AGENT_REVIEW_WORKFLOW_VERSION = "agent-review-workflow-v1"
AGENT_REVIEW_PROMPT_VERSION = "agent-team-prompt-v1"

_DETERMINISTIC_PRESTAGES: tuple[str, ...] = (
    "validate_trade_intent",
    "build_deterministic_evidence_bundle",
    "classify_actionability",
    "prepare_public_evidence_context",
)


@dataclass(frozen=True)
class RoleDispatchUnit:
    """Pure data describing one provider call. No side effects."""

    role_name: AgentTeamRole
    request: LLMProviderRequest


@dataclass(frozen=True)
class RoleDispatchResult:
    role_name: AgentTeamRole
    response: LLMProviderResponse
    latency_ms: int


# A dispatcher receives an ordered batch of units and returns ordered results.
# In P25A-T1 the only implementation is sequential. A future slice may replace
# it with a bounded-parallel implementation for public-evidence roles.
RoleDispatcher = Callable[[LLMProvider, Sequence[RoleDispatchUnit]], list[RoleDispatchResult]]


def dispatch_roles_sequentially(
    provider: LLMProvider,
    units: Sequence[RoleDispatchUnit],
) -> list[RoleDispatchResult]:
    """Async-READY dispatch seam — executes SEQUENTIALLY in P25A-T1.

    Takes an ordered batch of role dispatch units and returns results in the same
    order. No asyncio, no threads, no concurrency. A future slice may swap this
    for a bounded-parallel implementation that fans out independent public roles
    and aggregates by stable role key; that change is contained to this seam.
    """

    results: list[RoleDispatchResult] = []
    for unit in units:
        start = perf_counter()
        response = provider.complete(unit.request)
        latency_ms = max(0, round((perf_counter() - start) * 1000))
        results.append(
            RoleDispatchResult(role_name=unit.role_name, response=response, latency_ms=latency_ms)
        )
    return results


class ReviewRunner:
    """App-owned mock-first runner producing an ``AgentReviewRunState``."""

    #: Inert in P25A-T1. Dispatch is sequential regardless; retained as a config
    #: seam for a future bounded-parallel public-role implementation.
    max_parallelism: int = 1

    def __init__(
        self,
        provider: LLMProvider | None = None,
        *,
        provider_resolution=None,
        role_dispatcher: RoleDispatcher | None = None,
    ) -> None:
        resolution = provider_resolution or (
            None if provider is not None else resolve_llm_provider_from_env()
        )
        self.provider = provider or (resolution.provider if resolution else None)
        if self.provider is None:
            raise ValueError("ReviewRunner requires an LLM provider")
        self._dispatch: RoleDispatcher = role_dispatcher or dispatch_roles_sequentially

    # -- public entry point ------------------------------------------------

    def run(
        self,
        *,
        workspace: TradeReviewWorkspaceRead,
        generated_at: datetime | None = None,
    ) -> AgentReviewRunState:
        generated = generated_at or datetime.now(UTC)
        run_started = perf_counter()
        evidence = build_agent_safe_deterministic_evidence(workspace)
        actionability = workspace.actionability.review_actionability_status

        if _is_blocked_actionability(actionability):
            return self._deterministic_only_state(
                workspace=workspace,
                evidence=evidence,
                generated=generated,
                run_started=run_started,
            )
        return self._commentary_state(
            workspace=workspace,
            evidence=evidence,
            generated=generated,
            run_started=run_started,
        )

    # -- blocked / unknown actionability: deterministic-only safe run ------

    def _deterministic_only_state(
        self,
        *,
        workspace: TradeReviewWorkspaceRead,
        evidence: AgentSafeDeterministicEvidenceProjection,
        generated: datetime,
        run_started: float,
    ) -> AgentReviewRunState:
        stage_statuses: list[AgentReviewStageStatus] = [
            AgentReviewStageStatus(stage=stage, status="completed")
            for stage in _DETERMINISTIC_PRESTAGES
        ]
        for role_name in AGENT_TEAM_ROLES:
            stage_statuses.append(
                AgentReviewStageStatus(
                    stage=role_name,
                    status="gated",
                    role_name=role_name,
                    unavailable_reason="blocked_actionability_llm_roles_skipped",
                )
            )
        stage_statuses.append(AgentReviewStageStatus(stage="compose_review_narrative", status="completed"))
        stage_statuses.append(AgentReviewStageStatus(stage="evaluate_run", status="completed"))
        stage_statuses.append(
            AgentReviewStageStatus(
                stage="persist_run_steps",
                status="skipped",
                unavailable_reason="persistence_not_enabled_p25a_t1",
            )
        )

        final_synthesis = (
            "Deterministic-only review. Agent role commentary was skipped because the portfolio "
            f"snapshot actionability status is '{workspace.actionability.review_actionability_status}'. "
            "Deterministic backend services own all calculations."
        )
        eval_flags = _evaluate_run(
            role_outputs=(),
            final_synthesis=final_synthesis,
            deterministic_summary=_deterministic_evidence_summary(evidence),
            role_boundary_observations=(),
            provider_warnings=(),
        )
        timing = AgentReviewTimingSummary(
            total_latency_ms=_elapsed_ms(run_started),
            role_dispatch_latency_ms=0,
            dispatch_mode="sequential",
        )
        return self._build_state(
            workspace=workspace,
            evidence=evidence,
            generated=generated,
            run_status="completed",
            stage_statuses=tuple(stage_statuses),
            role_outputs=(),
            provider_warnings=(),
            final_synthesis=final_synthesis,
            eval_flags=eval_flags,
            budget=AgentReviewBudgetSummary(),
            timing=timing,
            extra_safety_flags=("deterministic_only_blocked_actionability",),
        )

    # -- normal path: optional mock commentary -----------------------------

    def _commentary_state(
        self,
        *,
        workspace: TradeReviewWorkspaceRead,
        evidence: AgentSafeDeterministicEvidenceProjection,
        generated: datetime,
        run_started: float,
    ) -> AgentReviewRunState:
        public_evidence = public_evidence_from_workspace(workspace)
        public_roles = tuple(r for r in AGENT_TEAM_ROLES if r in PUBLIC_ANALYST_ROLES)
        portfolio_roles = tuple(r for r in AGENT_TEAM_ROLES if r not in PUBLIC_ANALYST_ROLES)

        results_by_role: dict[str, RoleDispatchResult] = {}

        # Public-evidence roles are mutually independent and consume no prior
        # summaries; dispatch them as one batch (sequential now, fan-out later).
        public_units = [
            self._role_unit(workspace, role_name, public_evidence, evidence, prior_summaries=())
            for role_name in public_roles
        ]
        for result in self._dispatch(self.provider, public_units):
            results_by_role[result.role_name] = result

        # Portfolio-aware roles consume accumulated prior summaries and stay
        # ordered; dispatch one at a time through the same seam.
        prior_summaries: list[str] = []
        for role_name in AGENT_TEAM_ROLES:
            result = results_by_role.get(role_name)
            if result is not None:  # already dispatched (public role)
                if result.response.content_markdown:
                    prior_summaries.append(_prompt_safe_prior_summary(result.response.content_markdown))
                continue
            unit = self._role_unit(
                workspace, role_name, public_evidence, evidence, prior_summaries=tuple(prior_summaries)
            )
            (result,) = self._dispatch(self.provider, [unit])
            results_by_role[role_name] = result
            if result.response.content_markdown:
                prior_summaries.append(_prompt_safe_prior_summary(result.response.content_markdown))

        # Aggregate strictly by stable role key (AGENT_TEAM_ROLES order).
        stage_statuses: list[AgentReviewStageStatus] = [
            AgentReviewStageStatus(stage=stage, status="completed")
            for stage in _DETERMINISTIC_PRESTAGES
        ]
        role_outputs: list[AgentReviewRoleOutput] = []
        provider_warnings: list[str] = []
        tokens_in = tokens_out = 0
        dispatch_latency = 0
        for role_name in AGENT_TEAM_ROLES:
            result = results_by_role[role_name]
            response = result.response
            tokens_in += response.tokens_in or 0
            tokens_out += response.tokens_out or 0
            dispatch_latency += result.latency_ms
            # Content-level token guard: live prose that mentions private-value
            # tokens (holdings/positions/cash/…) or secret-like strings is
            # withheld and the role degrades safely. Content-only scan — legit
            # section keys elsewhere in the state are unaffected. Never retried
            # on another model: this is a safety rejection, not availability.
            content_unsafe = bool(response.content_markdown) and bool(
                find_forbidden_string_values(response.content_markdown)
                | find_secret_like_values(response.content_markdown)
            )
            role_status = "completed" if response.status == "ok" and not content_unsafe else "unavailable"
            provider_status = "safety_validation_failed" if content_unsafe else response.status
            unavailable_reason = (
                "live content withheld by private-value token safety guard"
                if content_unsafe
                else response.error_message
            )
            role_outputs.append(
                AgentReviewRoleOutput(
                    role_name=role_name,
                    status=role_status,
                    content_markdown=None if content_unsafe else response.content_markdown,
                    provider_status=provider_status,
                    is_mock=response.is_mock,
                    unavailable_reason=unavailable_reason,
                    latency_ms=result.latency_ms,
                )
            )
            stage_statuses.append(
                AgentReviewStageStatus(
                    stage=role_name,
                    status=role_status,
                    role_name=role_name,
                    provider_status=provider_status,
                    unavailable_reason=unavailable_reason,
                    latency_ms=result.latency_ms,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    estimated_cost=response.estimated_cost,
                )
            )
            if provider_status != "ok":
                provider_warnings.append(f"{role_name}:{provider_status}")

        final_synthesis = _compose_final_synthesis(role_outputs)
        stage_statuses.append(AgentReviewStageStatus(stage="compose_review_narrative", status="completed"))
        stage_statuses.append(AgentReviewStageStatus(stage="evaluate_run", status="completed"))
        stage_statuses.append(
            AgentReviewStageStatus(
                stage="persist_run_steps",
                status="skipped",
                unavailable_reason="persistence_not_enabled_p25a_t1",
            )
        )

        role_boundary_observations = tuple(
            (role_name, role_name in PUBLIC_ANALYST_ROLES, role_name not in PUBLIC_ANALYST_ROLES)
            for role_name in AGENT_TEAM_ROLES
        )
        eval_flags = _evaluate_run(
            role_outputs=tuple(role_outputs),
            final_synthesis=final_synthesis,
            deterministic_summary=_deterministic_evidence_summary(evidence),
            role_boundary_observations=role_boundary_observations,
            provider_warnings=tuple(provider_warnings),
        )
        run_status = "partially_completed" if provider_warnings else "completed"
        budget = AgentReviewBudgetSummary(tokens_in=tokens_in, tokens_out=tokens_out, estimated_cost="0")
        timing = AgentReviewTimingSummary(
            total_latency_ms=_elapsed_ms(run_started),
            role_dispatch_latency_ms=dispatch_latency,
            dispatch_mode="sequential",
        )
        return self._build_state(
            workspace=workspace,
            evidence=evidence,
            generated=generated,
            run_status=run_status,
            stage_statuses=tuple(stage_statuses),
            role_outputs=tuple(role_outputs),
            provider_warnings=tuple(provider_warnings),
            final_synthesis=final_synthesis,
            eval_flags=eval_flags,
            budget=budget,
            timing=timing,
        )

    # -- helpers -----------------------------------------------------------

    def _role_unit(
        self,
        workspace: TradeReviewWorkspaceRead,
        role_name: AgentTeamRole,
        public_evidence,
        evidence: AgentSafeDeterministicEvidenceProjection,
        *,
        prior_summaries: tuple[str, ...],
    ) -> RoleDispatchUnit:
        prompt_input = build_agent_team_prompt_input(
            role_name=role_name,
            public_evidence=public_evidence,
            deterministic_evidence=None if role_name in PUBLIC_ANALYST_ROLES else evidence,
            prior_role_summaries=prior_summaries,
        )
        messages = render_prompt_input_messages(prompt_input)
        request = LLMProviderRequest(
            request_id=f"{workspace.review_reference}:{role_name}",
            role_name=role_name,
            messages=tuple(messages),
            provider=self.provider.provider_name,
            model=self.provider.model,
            prompt_version=AGENT_REVIEW_PROMPT_VERSION,
            metadata={
                "workflow_version": AGENT_REVIEW_WORKFLOW_VERSION,
                "review_reference": workspace.review_reference,
            },
        )
        return RoleDispatchUnit(role_name=role_name, request=request)

    def _build_state(
        self,
        *,
        workspace: TradeReviewWorkspaceRead,
        evidence: AgentSafeDeterministicEvidenceProjection,
        generated: datetime,
        run_status: str,
        stage_statuses: tuple[AgentReviewStageStatus, ...],
        role_outputs: tuple[AgentReviewRoleOutput, ...],
        provider_warnings: tuple[str, ...],
        final_synthesis: str | None,
        eval_flags: tuple[AgentReviewEvalFlag, ...],
        budget: AgentReviewBudgetSummary,
        timing: AgentReviewTimingSummary,
        extra_safety_flags: tuple[str, ...] = (),
    ) -> AgentReviewRunState:
        safety_flags = (
            f"provider:{self.provider.provider_name}",
            "analysis_only",
            "deterministic_metrics_owned_by_backend",
            *extra_safety_flags,
        )
        return AgentReviewRunState(
            run_reference=f"agent-review-{workspace.review_reference}",
            workflow_version=AGENT_REVIEW_WORKFLOW_VERSION,
            generated_at=generated,
            is_mock=getattr(self.provider, "provider_name", "") == "mock",
            analysis_only=True,
            review_reference=workspace.review_reference,
            supported_flow=workspace.supported_flow,
            review_flow_label=evidence.review_flow_label,
            review_actionability_status=workspace.actionability.review_actionability_status,
            broker_snapshot_freshness=dict(evidence.broker_snapshot_freshness),
            market_quote_freshness=dict(evidence.market_quote_freshness),
            deterministic_evidence_summary=_deterministic_evidence_summary(evidence),
            scope_summary=dict(evidence.scope_metadata),
            run_status=run_status,
            budget_summary=budget,
            timing_summary=timing,
            stage_statuses=stage_statuses,
            role_outputs=role_outputs,
            provider_warnings=provider_warnings,
            safety_flags=safety_flags,
            eval_flags=eval_flags,
            final_synthesis=final_synthesis,
        )


def _is_blocked_actionability(status: str) -> bool:
    """Gate LLM roles for blocked/unknown freshness statuses (``blocked_*``)."""

    return status.startswith("blocked_")


def _deterministic_evidence_summary(
    evidence: AgentSafeDeterministicEvidenceProjection,
) -> dict[str, object]:
    return {
        "review_flow_label": evidence.review_flow_label,
        "actionability_summary": dict(evidence.actionability_summary),
        "risk_summary": dict(evidence.deterministic_risk_summary),
        "portfolio_shape": {
            "context_available": evidence.portfolio_shape_summary["context_available"],
            "equity_position_count": evidence.portfolio_shape_summary["equity_position_count"],
            "option_position_count": evidence.portfolio_shape_summary["option_position_count"],
            "liquidity_state": evidence.portfolio_shape_summary["liquidity_state"],
        },
        "caveat_codes": tuple(evidence.caveat_codes),
    }


def _compose_final_synthesis(role_outputs: list[AgentReviewRoleOutput]) -> str:
    completed = [output.role_name for output in role_outputs if output.provider_status == "ok"]
    unavailable = [output.role_name for output in role_outputs if output.provider_status != "ok"]
    text = (
        "Portfolio-team synthesis. Analysis-only educational summary based on "
        f"{len(completed)} completed role output(s). Deterministic backend services own all calculations."
    )
    if unavailable:
        text += f" Some role output was unavailable: {', '.join(unavailable)}."
    return text


def _prompt_safe_prior_summary(content_markdown: str) -> str:
    try:
        validate_agent_team_text(content_markdown, label="prior role summary prompt reuse")
    except ValueError:
        return "Prior role output passed output safety but was withheld from strict prompt reuse."
    return content_markdown


def _evaluate_run(
    *,
    role_outputs: tuple[AgentReviewRoleOutput, ...],
    final_synthesis: str | None,
    deterministic_summary: dict[str, object],
    role_boundary_observations: tuple[tuple[str, bool, bool], ...],
    provider_warnings: tuple[str, ...],
) -> tuple[AgentReviewEvalFlag, ...]:
    """Run the reusable ``agent_eval`` harness and map findings to safe flags."""

    # Imported lazily to avoid an import-time cycle: agent_eval imports
    # agent_team safety submodules, and agent_team/__init__ imports this runner.
    from app.services.agent_eval import evaluate_agent_review_run

    report = evaluate_agent_review_run(
        role_texts=tuple((output.role_name, output.content_markdown) for output in role_outputs),
        final_synthesis=final_synthesis,
        run_summary=deterministic_summary,
        expected_summary=deterministic_summary,
        role_boundary_observations=role_boundary_observations,
        provider_warnings=provider_warnings,
    )
    return tuple(
        AgentReviewEvalFlag(check=finding.check, status=finding.status, detail=finding.detail)
        for finding in report.findings
    )


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))
