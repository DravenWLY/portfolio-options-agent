"""App-owned agent review run-state model for Phase 25A (P25A-T1).

This module defines an immutable, validated, persistence-READY-but-NOT-persisted
run-state for the portfolio-aware trade-review agent workflow. It generalizes
``AgentTeamAnalysisState`` (and intentionally does **not** replace it yet) by
adding per-stage timing, budget, and evaluation scaffolding.

Backend-only. No persistence, no API schema, no live calls. Every structure
validates on construction against the existing privacy / wording /
generated-metric boundary (see ADR 0008 safety boundaries).
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal

from app.schemas.actionability import ReviewActionabilityStatus
from app.services.agent_team.llm_provider import AgentTeamRole
from app.services.agent_team.output_safety import validate_llm_provider_output
from app.services.agent_team.prompt_safety import validate_agent_team_text


AGENT_REVIEW_RUN_STATE_VERSION = "agent-review-run-state-v1"

AgentReviewRunStatus = Literal["completed", "partially_completed", "failed_safe"]
AgentReviewStageOutcome = Literal[
    "planned",
    "completed",
    "skipped",
    "unavailable",
    "gated",
    "blocked",
]
AgentReviewRoleStatus = Literal["completed", "unavailable", "skipped"]
AgentReviewEvalStatus = Literal["passed", "flagged", "deferred"]

AGENT_REVIEW_RUN_STATUSES: tuple[str, ...] = ("completed", "partially_completed", "failed_safe")
AGENT_REVIEW_STAGE_OUTCOMES: tuple[str, ...] = (
    "planned",
    "completed",
    "skipped",
    "unavailable",
    "gated",
    "blocked",
)
AGENT_REVIEW_ROLE_STATUSES: tuple[str, ...] = ("completed", "unavailable", "skipped")
AGENT_REVIEW_EVAL_STATUSES: tuple[str, ...] = ("passed", "flagged", "deferred")


@dataclass(frozen=True)
class AgentReviewStageStatus:
    """One stage outcome with optional timing/budget scaffolding."""

    stage: str
    status: str
    role_name: AgentTeamRole | None = None
    provider_status: str | None = None
    unavailable_reason: str | None = None
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    estimated_cost: str | None = None

    def __post_init__(self) -> None:
        if self.status not in AGENT_REVIEW_STAGE_OUTCOMES:
            raise ValueError(f"unsupported stage outcome: {self.status}")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        validate_agent_team_text(asdict(self), label="agent-review stage status")


@dataclass(frozen=True)
class AgentReviewRoleOutput:
    """One role's safe commentary output (validated text only)."""

    role_name: AgentTeamRole
    status: str
    content_markdown: str | None
    provider_status: str
    is_mock: bool
    unavailable_reason: str | None = None
    latency_ms: int | None = None

    def __post_init__(self) -> None:
        if self.status not in AGENT_REVIEW_ROLE_STATUSES:
            raise ValueError(f"unsupported role status: {self.status}")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        validate_llm_provider_output(asdict(self), label="agent-review role output")


@dataclass(frozen=True)
class AgentReviewEvalFlag:
    """One process-level evaluation result (faithfulness harness lands in T2)."""

    check: str
    status: str
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in AGENT_REVIEW_EVAL_STATUSES:
            raise ValueError(f"unsupported eval status: {self.status}")
        validate_agent_team_text(asdict(self), label="agent-review eval flag")


@dataclass(frozen=True)
class AgentReviewBudgetSummary:
    """Token/cost scaffolding. P25A-T1 records usage but enforces no ceiling."""

    tokens_in: int = 0
    tokens_out: int = 0
    estimated_cost: str = "0"
    token_budget: int | None = None
    budget_exceeded: bool = False

    def __post_init__(self) -> None:
        if self.tokens_in < 0 or self.tokens_out < 0:
            raise ValueError("token counts must not be negative")
        if self.token_budget is not None and self.token_budget < 0:
            raise ValueError("token_budget must not be negative")
        validate_agent_team_text(asdict(self), label="agent-review budget summary")


@dataclass(frozen=True)
class AgentReviewTimingSummary:
    """Coarse run timing. ``dispatch_mode`` is sequential in P25A-T1."""

    total_latency_ms: int = 0
    role_dispatch_latency_ms: int = 0
    dispatch_mode: str = "sequential"

    def __post_init__(self) -> None:
        if self.total_latency_ms < 0 or self.role_dispatch_latency_ms < 0:
            raise ValueError("latency values must not be negative")
        validate_agent_team_text(asdict(self), label="agent-review timing summary")


@dataclass(frozen=True)
class AgentReviewRunState:
    """Immutable, validated agent review run-state (not persisted in P25A-T1)."""

    run_reference: str
    workflow_version: str
    generated_at: datetime
    is_mock: bool
    analysis_only: bool
    review_reference: str
    supported_flow: str
    review_flow_label: str
    review_actionability_status: ReviewActionabilityStatus
    broker_snapshot_freshness: dict[str, object]
    market_quote_freshness: dict[str, object]
    deterministic_evidence_summary: dict[str, object]
    run_status: str
    budget_summary: AgentReviewBudgetSummary
    timing_summary: AgentReviewTimingSummary
    # Lossy, sanitized scope categories/booleans/codes for the analyzed scope
    # (which review account / broader portfolio context the run was scoped to).
    # Never carries account refs, labels, kinds, balances, or other private values.
    scope_summary: dict[str, object] = field(default_factory=dict)
    stage_statuses: tuple[AgentReviewStageStatus, ...] = ()
    role_outputs: tuple[AgentReviewRoleOutput, ...] = ()
    provider_warnings: tuple[str, ...] = ()
    safety_flags: tuple[str, ...] = field(default_factory=tuple)
    eval_flags: tuple[AgentReviewEvalFlag, ...] = ()
    final_synthesis: str | None = None

    def __post_init__(self) -> None:
        if self.run_status not in AGENT_REVIEW_RUN_STATUSES:
            raise ValueError(f"unsupported run status: {self.run_status}")
        if not self.run_reference.strip():
            raise ValueError("run_reference must not be empty")
        validate_llm_provider_output(asdict(self), label="agent-review run state")
