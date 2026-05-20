"""Agent-team orchestration contract for portfolio-aware trade review."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, TypeAlias
from uuid import UUID

from app.schemas.agent_runs import AgentRunCreate, AgentRunStatus, AgentStepCreate, AgentStepStatus
from app.schemas.actionability import PortfolioActionabilityDecision, ReviewActionabilityStatus
from app.schemas.reports import ReportMessageCreate
from app.services.agents.context_envelopes import ContextEnvelope, ContextEnvelopeType, make_context_envelope
from app.services.agents.freshness_guardrail import FreshnessGuardrailAgent, FreshnessGuardrailAgentOutput
from app.services.agents.portfolio_context import PortfolioContextAgent, PortfolioContextAgentOutput, ReportHistoryReference
from app.services.agents.report_composer import ReportComposerAgent, ReportComposerAgentOutput
from app.services.agents.roles import (
    ALL_AGENT_ROLES,
    MVP_AGENT_ROLES,
    OPTIONAL_FUTURE_AGENT_ROLES,
    P1_AGENT_ROLES,
    AgentRoleDefinition,
    AgentRoleName,
    role_registry,
)
from app.services.agents.trade_review import TradeReviewAgent, TradeReviewAgentOutput
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys
from app.services.trade_review.context import PortfolioReviewContext
from app.services.trade_review.report import TradeReviewAgentProjection


WORKFLOW_VERSION = "portfolio-agent-team-v1"

AgentWorkflowStage: TypeAlias = Literal[
    "validate_trade_intent",
    "build_portfolio_context",
    "resolve_market_snapshot",
    "run_deterministic_review",
    "evaluate_actionability",
    "retrieve_public_research_evidence",
    "run_optional_interpretation",
    "run_freshness_guardrail",
    "compose_report",
    "persist_run_steps",
]
StageStatus: TypeAlias = Literal["planned", "completed", "skipped", "unavailable", "gated", "blocked"]
StageExecutionMode: TypeAlias = Literal[
    "deterministic",
    "actionability_gate",
    "optional_public_research",
    "optional_llm",
    "persistence",
]

DEFAULT_AGENT_WORKFLOW_STAGES: tuple[str, ...] = (
    "validate_trade_intent",
    "build_portfolio_context",
    "resolve_market_snapshot",
    "run_deterministic_review",
    "evaluate_actionability",
    "retrieve_public_research_evidence",
    "run_optional_interpretation",
    "run_freshness_guardrail",
    "compose_report",
    "persist_run_steps",
)
OPTIONAL_STAGE_UNAVAILABLE_REASONS = {
    "resolve_market_snapshot": "real_market_provider_not_configured_use_manual_or_mock_snapshot",
    "retrieve_public_research_evidence": "public_research_evidence_not_configured",
    "run_optional_interpretation": "llm_interpretation_not_configured",
}


@dataclass(frozen=True)
class OrchestratorStageContract:
    stage: AgentWorkflowStage
    status: StageStatus
    role_name: AgentRoleName
    execution_mode: StageExecutionMode
    input_envelope_type: ContextEnvelopeType | None
    output_envelope_type: ContextEnvelopeType | None
    actionability_status: ReviewActionabilityStatus | None = None
    unavailable_reason: str | None = None
    source_component: str | None = None
    source_version: str | None = None


@dataclass(frozen=True)
class AgentTeamOrchestrationContract:
    run_reference: str
    workflow_version: str
    stages: tuple[OrchestratorStageContract, ...]
    actionability_status: ReviewActionabilityStatus | None = None

    def to_agent_step_plan(self) -> tuple[dict, ...]:
        """Return a safe stage plan shape for future agent_steps mapping."""

        payload = tuple(asdict(stage) for stage in self.stages)
        forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"orchestration contract contains forbidden private fields: {blocked}")
        return payload


@dataclass(frozen=True)
class AgentTeamStageOutput:
    stage: AgentWorkflowStage
    status: StageStatus
    role_name: AgentRoleName
    execution_mode: StageExecutionMode
    input_envelope_type: ContextEnvelopeType | None
    output_envelope_type: ContextEnvelopeType | None
    actionability_status: ReviewActionabilityStatus | None = None
    unavailable_reason: str | None = None
    output_envelope: ContextEnvelope | None = None

    def to_agent_step_create(self, *, agent_run_id: UUID, step_order: int) -> AgentStepCreate:
        """Map the stage to an existing agent-step create schema without persisting."""

        return AgentStepCreate(
            agent_run_id=agent_run_id,
            step_order=step_order,
            step_key=self.stage,
            step_type=self.execution_mode,
            status=_agent_step_status(self.status),
            input_snapshot_json={
                "stage": self.stage,
                "role_name": self.role_name,
                "input_envelope_type": self.input_envelope_type,
                "actionability_status": self.actionability_status,
            },
            output_snapshot_json=self._output_snapshot(),
            calculation_version=WORKFLOW_VERSION,
            data_freshness_snapshot=_stage_freshness_snapshot(self),
        )

    def _output_snapshot(self) -> dict[str, Any]:
        if self.output_envelope is not None:
            return self.output_envelope.to_payload()
        return {
            "stage": self.stage,
            "status": self.status,
            "role_name": self.role_name,
            "unavailable_reason": self.unavailable_reason,
            "output_envelope_type": self.output_envelope_type,
        }


@dataclass(frozen=True)
class AgentTeamOrchestrationResult:
    run_reference: str
    generated_at: datetime
    contract: AgentTeamOrchestrationContract
    stage_outputs: tuple[AgentTeamStageOutput, ...]
    portfolio_context_output: PortfolioContextAgentOutput
    trade_review_output: TradeReviewAgentOutput
    freshness_guardrail_output: FreshnessGuardrailAgentOutput
    report_output: ReportComposerAgentOutput | None

    def to_agent_run_create(
        self,
        *,
        account_id: UUID | None = None,
        report_thread_id: UUID | None = None,
    ) -> AgentRunCreate:
        """Map the orchestration result to an existing agent-run create schema."""

        return AgentRunCreate(
            account_id=account_id,
            report_thread_id=report_thread_id,
            run_type="portfolio_agent_team",
            status=_agent_run_status(self),
            provider="deterministic_backend",
            model=None,
            token_budget=0,
            cost_budget=Decimal("0"),
            input_snapshot_json={
                "run_reference": self.run_reference,
                "workflow_version": self.contract.workflow_version,
                "stage_order": list(DEFAULT_AGENT_WORKFLOW_STAGES),
            },
            output_snapshot_json=self.summary_snapshot(),
            calculation_version=WORKFLOW_VERSION,
            data_freshness_snapshot=self.data_freshness_snapshot(),
            started_at=self.generated_at,
            completed_at=self.generated_at,
        )

    def to_agent_step_creates(self, *, agent_run_id: UUID) -> tuple[AgentStepCreate, ...]:
        """Map all stage outputs to existing agent-step create schemas."""

        return tuple(
            stage.to_agent_step_create(agent_run_id=agent_run_id, step_order=index)
            for index, stage in enumerate(self.stage_outputs, start=1)
        )

    def to_report_message_create(self, *, sequence: int) -> ReportMessageCreate | None:
        """Return the final report-history message payload when composition is allowed."""

        if self.report_output is None:
            return None
        return self.report_output.to_report_message_create(sequence=sequence)

    def summary_snapshot(self) -> dict[str, Any]:
        payload = {
            "run_reference": self.run_reference,
            "workflow_version": self.contract.workflow_version,
            "review_actionability_status": self.contract.actionability_status,
            "stage_statuses": {stage.stage: stage.status for stage in self.stage_outputs},
            "source_agent_names": [
                self.portfolio_context_output.agent_name,
                self.trade_review_output.agent_name,
                self.freshness_guardrail_output.agent_name,
                *([self.report_output.agent_name] if self.report_output is not None else []),
            ],
            "report_composed": self.report_output is not None,
        }
        _raise_if_forbidden(payload, label="agent team summary")
        return payload

    def data_freshness_snapshot(self) -> dict[str, Any]:
        actionability = self.contract.actionability_status
        payload = {
            "review_actionability_status": actionability,
            "broker_snapshot": {
                "freshness_scope": self.freshness_guardrail_output.broker_snapshot_scope,
                "freshness_status": self.freshness_guardrail_output.broker_snapshot_status,
            },
            "market_quotes": {
                "freshness_scope": self.freshness_guardrail_output.market_quote_scope,
                "freshness_status": self.freshness_guardrail_output.market_quote_status,
            },
        }
        _raise_if_forbidden(payload, label="agent team freshness")
        return payload


class PortfolioAgentTeamOrchestrator:
    """Run the deterministic Phase 16A components in the approved stage order."""

    def run(
        self,
        *,
        run_reference: str,
        portfolio_context: PortfolioReviewContext,
        trade_review_projection: TradeReviewAgentProjection,
        actionability: PortfolioActionabilityDecision,
        report_history_references: tuple[ReportHistoryReference, ...] = (),
        generated_at: datetime | None = None,
    ) -> AgentTeamOrchestrationResult:
        generated = generated_at or datetime.now(UTC)
        contract = build_orchestration_contract(run_reference=run_reference, actionability=actionability)
        portfolio_output = PortfolioContextAgent().run(
            portfolio_context=portfolio_context,
            actionability=actionability,
            report_history_references=report_history_references,
            generated_at=generated,
        )
        trade_output = TradeReviewAgent().run(
            projection=trade_review_projection,
            actionability=actionability,
            generated_at=generated,
        )
        guardrail_output = FreshnessGuardrailAgent().run(
            actionability=actionability,
            generated_at=generated,
        )
        report_output = (
            ReportComposerAgent().run(
                portfolio_context=portfolio_output,
                trade_review=trade_output,
                freshness_guardrail=guardrail_output,
                generated_at=generated,
            )
            if actionability.can_run_agent_explanation
            else None
        )
        stage_outputs = tuple(
            _build_stage_output(
                stage_contract=stage,
                trade_review_projection=trade_review_projection,
                portfolio_output=portfolio_output,
                trade_output=trade_output,
                guardrail_output=guardrail_output,
                report_output=report_output,
            )
            for stage in contract.stages
        )
        result = AgentTeamOrchestrationResult(
            run_reference=run_reference,
            generated_at=generated,
            contract=contract,
            stage_outputs=stage_outputs,
            portfolio_context_output=portfolio_output,
            trade_review_output=trade_output,
            freshness_guardrail_output=guardrail_output,
            report_output=report_output,
        )
        _raise_if_forbidden(result.summary_snapshot(), label="agent team orchestration result")
        return result


def build_orchestration_contract(
    *,
    run_reference: str,
    actionability: PortfolioActionabilityDecision | None = None,
) -> AgentTeamOrchestrationContract:
    """Build a planned/executed stage contract without running external providers."""

    actionability_status = actionability.review_actionability_status if actionability else None
    return AgentTeamOrchestrationContract(
        run_reference=run_reference,
        workflow_version=WORKFLOW_VERSION,
        actionability_status=actionability_status,
        stages=tuple(
            _stage_contract(stage, actionability_status=actionability_status)
            for stage in DEFAULT_AGENT_WORKFLOW_STAGES
        ),
    )


def _build_stage_output(
    *,
    stage_contract: OrchestratorStageContract,
    trade_review_projection: TradeReviewAgentProjection,
    portfolio_output: PortfolioContextAgentOutput,
    trade_output: TradeReviewAgentOutput,
    guardrail_output: FreshnessGuardrailAgentOutput,
    report_output: ReportComposerAgentOutput | None,
) -> AgentTeamStageOutput:
    status = _executed_stage_status(stage_contract, report_output=report_output)
    envelope = _stage_output_envelope(
        stage_contract,
        trade_review_projection=trade_review_projection,
        portfolio_output=portfolio_output,
        trade_output=trade_output,
        guardrail_output=guardrail_output,
        report_output=report_output,
        status=status,
    )
    return AgentTeamStageOutput(
        stage=stage_contract.stage,
        status=status,
        role_name=stage_contract.role_name,
        execution_mode=stage_contract.execution_mode,
        input_envelope_type=stage_contract.input_envelope_type,
        output_envelope_type=stage_contract.output_envelope_type,
        actionability_status=stage_contract.actionability_status,
        unavailable_reason=stage_contract.unavailable_reason,
        output_envelope=envelope,
    )


def _executed_stage_status(
    stage_contract: OrchestratorStageContract,
    *,
    report_output: ReportComposerAgentOutput | None,
) -> StageStatus:
    if stage_contract.stage in {
        "validate_trade_intent",
        "build_portfolio_context",
        "run_deterministic_review",
        "evaluate_actionability",
        "run_freshness_guardrail",
        "persist_run_steps",
    }:
        return "completed"
    if stage_contract.stage == "compose_report":
        return "completed" if report_output is not None else stage_contract.status
    return stage_contract.status


def _stage_output_envelope(
    stage_contract: OrchestratorStageContract,
    *,
    trade_review_projection: TradeReviewAgentProjection,
    portfolio_output: PortfolioContextAgentOutput,
    trade_output: TradeReviewAgentOutput,
    guardrail_output: FreshnessGuardrailAgentOutput,
    report_output: ReportComposerAgentOutput | None,
    status: StageStatus,
) -> ContextEnvelope | None:
    if status != "completed":
        return None
    if stage_contract.stage == "validate_trade_intent":
        payload = _validation_output_payload(trade_review_projection.validation)
    elif stage_contract.stage == "build_portfolio_context":
        payload = _portfolio_output_payload(portfolio_output)
    elif stage_contract.stage == "run_deterministic_review":
        payload = _deterministic_review_payload(trade_review_projection, trade_output)
    elif stage_contract.stage == "evaluate_actionability":
        payload = {
            "review_actionability_status": guardrail_output.review_actionability_status,
            "broker_snapshot": {
                "freshness_scope": guardrail_output.broker_snapshot_scope,
                "freshness_status": guardrail_output.broker_snapshot_status,
            },
            "market_quotes": {
                "freshness_scope": guardrail_output.market_quote_scope,
                "freshness_status": guardrail_output.market_quote_status,
            },
        }
    elif stage_contract.stage == "run_freshness_guardrail":
        payload = guardrail_output.to_agent_step_output()
    elif stage_contract.stage == "compose_report" and report_output is not None:
        payload = {
            "agent_name": report_output.agent_name,
            "calculation_version": report_output.calculation_version,
            "source_agent_names": report_output.source_agent_names,
            "deterministic_sections": report_output.deterministic_sections,
            "llm_generated_sections": report_output.llm_generated_sections,
            "traceability": report_output.traceability,
        }
    elif stage_contract.stage == "persist_run_steps":
        payload = {
            "persistence_mapping_available": True,
            "target_contracts": ("AgentRunCreate", "AgentStepCreate", "ReportMessageCreate"),
        }
    else:
        return None
    _raise_if_forbidden(payload, label=stage_contract.stage)
    return make_context_envelope(
        envelope_type=stage_contract.output_envelope_type or "report_composition_context",
        payload=payload,
        allowed_role_names=(stage_contract.role_name,),
        source_component=stage_contract.source_component or stage_contract.role_name,
        source_version=stage_contract.source_version,
    )


def _portfolio_output_payload(output: PortfolioContextAgentOutput) -> dict[str, Any]:
    return {
        "agent_name": output.agent_name,
        "portfolio_shape": {
            "has_cash_context": output.portfolio_shape.has_cash_context,
            "stock_position_count": output.portfolio_shape.stock_position_count,
            "option_position_count": output.portfolio_shape.option_position_count,
            "long_option_position_count": output.portfolio_shape.long_option_position_count,
            "short_option_position_count": output.portfolio_shape.short_option_position_count,
        },
        "freshness": {
            "broker_snapshot_status": output.freshness.broker_snapshot_status,
            "market_quote_status": output.freshness.market_quote_status,
            "review_actionability_status": output.freshness.review_actionability_status,
            "language_tier": output.freshness.language_tier,
        },
        "notes": output.notes,
    }


def _validation_output_payload(validation) -> dict[str, Any]:
    return {
        "intent_id": validation.intent_id,
        "manual_review_required": validation.manual_review_required,
        "blocked": validation.blocked,
        "highest_severity": validation.highest_severity,
        "is_clean": validation.is_clean,
        "finding_count": len(validation.findings),
        "finding_codes": tuple(finding.code for finding in validation.findings),
    }


def _deterministic_review_payload(
    projection: TradeReviewAgentProjection,
    output: TradeReviewAgentOutput,
) -> dict[str, Any]:
    return {
        "agent_name": output.agent_name,
        "intent_id": output.intent_id,
        "review_actionability_status": output.review_actionability_status,
        "can_run_agent_explanation": output.can_run_agent_explanation,
        "highest_severity": output.highest_severity,
        "has_blocker": output.has_blocker,
        "payoff": {
            "scenario_point_count": len(projection.payoff.points),
            "max_loss_available": projection.payoff.max_loss is not None,
            "max_gain_available": projection.payoff.max_gain is not None,
            "calculation_note_count": len(projection.payoff.calculation_notes),
        },
        "portfolio_impact": {
            "broker_freshness_status": projection.portfolio_impact.broker_freshness_status,
            "market_freshness_status": projection.portfolio_impact.market_freshness_status,
            "market_manual_review_required": projection.portfolio_impact.market_manual_review_required,
            "concentration_symbol": projection.portfolio_impact.concentration_symbol,
        },
        "risk": {
            "violation_count": len(projection.risk_rule_violations),
            "highest_severity": projection.highest_severity,
            "has_blocker": projection.has_blocker,
        },
        "deterministic_fields_used": output.deterministic_fields_used,
        "notes": output.notes,
    }


def _stage_contract(
    stage: str,
    *,
    actionability_status: ReviewActionabilityStatus | None,
) -> OrchestratorStageContract:
    role_name, execution_mode, input_type, output_type, source_component = _stage_metadata(stage)
    status, reason = _stage_status(stage, actionability_status=actionability_status)
    return OrchestratorStageContract(
        stage=stage,  # type: ignore[arg-type]
        status=status,
        role_name=role_name,
        execution_mode=execution_mode,
        input_envelope_type=input_type,
        output_envelope_type=output_type,
        actionability_status=actionability_status if stage in {"evaluate_actionability", "run_freshness_guardrail", "compose_report"} else None,
        unavailable_reason=reason,
        source_component=source_component,
        source_version=WORKFLOW_VERSION,
    )


def _stage_metadata(
    stage: str,
) -> tuple[AgentRoleName, StageExecutionMode, ContextEnvelopeType | None, ContextEnvelopeType | None, str]:
    metadata: dict[str, tuple[AgentRoleName, StageExecutionMode, ContextEnvelopeType | None, ContextEnvelopeType | None, str]] = {
        "validate_trade_intent": (
            "trade_review_agent",
            "deterministic",
            "deterministic_review_context",
            "deterministic_review_context",
            "trade_intent_validator",
        ),
        "build_portfolio_context": (
            "portfolio_context_agent",
            "deterministic",
            "private_portfolio_safe_context",
            "private_portfolio_safe_context",
            "portfolio_context_agent",
        ),
        "resolve_market_snapshot": (
            "market_data_agent",
            "deterministic",
            "deterministic_review_context",
            "deterministic_review_context",
            "market_snapshot_resolver",
        ),
        "run_deterministic_review": (
            "trade_review_agent",
            "deterministic",
            "deterministic_review_context",
            "deterministic_review_context",
            "trade_review_engine",
        ),
        "evaluate_actionability": (
            "freshness_guardrail_agent",
            "actionability_gate",
            "actionability_context",
            "actionability_context",
            "portfolio_actionability_policy",
        ),
        "retrieve_public_research_evidence": (
            "news_research_evidence_agent",
            "optional_public_research",
            "public_evidence_context",
            "public_evidence_context",
            "public_research_evidence",
        ),
        "run_optional_interpretation": (
            "bull_case_agent",
            "optional_llm",
            "llm_explanation_context",
            "llm_explanation_context",
            "optional_llm_interpretation",
        ),
        "run_freshness_guardrail": (
            "freshness_guardrail_agent",
            "deterministic",
            "actionability_context",
            "report_composition_context",
            "freshness_guardrail_agent",
        ),
        "compose_report": (
            "report_composer_agent",
            "deterministic",
            "report_composition_context",
            "report_composition_context",
            "report_composer_agent",
        ),
        "persist_run_steps": (
            "report_composer_agent",
            "persistence",
            "report_composition_context",
            "report_composition_context",
            "agent_run_step_persistence_mapping",
        ),
    }
    return metadata[stage]


def _stage_status(
    stage: str,
    *,
    actionability_status: ReviewActionabilityStatus | None,
) -> tuple[StageStatus, str | None]:
    if stage in OPTIONAL_STAGE_UNAVAILABLE_REASONS:
        if stage == "run_optional_interpretation" and actionability_status in {
            "manual_confirmation_required",
            "blocked_stale_broker_snapshot",
            "blocked_stale_market_quote",
            "blocked_unknown_freshness",
            "blocked_provider_error",
        }:
            return "gated", "actionability_policy_blocks_optional_interpretation"
        return "unavailable", OPTIONAL_STAGE_UNAVAILABLE_REASONS[stage]
    if stage == "evaluate_actionability" and actionability_status is not None:
        return "completed", None
    if stage == "compose_report":
        if actionability_status in {
            "blocked_stale_broker_snapshot",
            "blocked_stale_market_quote",
            "blocked_unknown_freshness",
            "blocked_provider_error",
        }:
            return "blocked", "actionability_policy_blocks_polished_report"
        if actionability_status == "manual_confirmation_required":
            return "gated", "manual_confirmation_required_before_report_composition"
    return "planned", None


def _agent_step_status(stage_status: StageStatus) -> AgentStepStatus:
    if stage_status == "completed":
        return "completed"
    if stage_status == "planned":
        return "queued"
    return "skipped"


def _agent_run_status(result: AgentTeamOrchestrationResult) -> AgentRunStatus:
    if result.report_output is not None:
        return "completed"
    return "partially_completed"


def _stage_freshness_snapshot(stage_output: AgentTeamStageOutput) -> dict[str, Any]:
    payload = {
        "stage": stage_output.stage,
        "review_actionability_status": stage_output.actionability_status,
        "output_envelope_type": stage_output.output_envelope_type,
    }
    _raise_if_forbidden(payload, label=f"{stage_output.stage} freshness snapshot")
    return payload


def _raise_if_forbidden(payload: object, *, label: str) -> None:
    forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{label} contains forbidden private fields: {blocked}")
