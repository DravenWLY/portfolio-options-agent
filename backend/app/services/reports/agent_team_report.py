"""On-demand Agent Team report generation from saved review evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report_thread import ReportThread
from app.schemas.reports import (
    SavedAgentTeamRoleSummaryRead,
    SavedAgentTeamSummaryRead,
    SavedEvidencePackageRead,
)
from app.services.agent_team.report_output_safety import validate_agent_team_report_output
from app.services.agent_team.roles import role_registry
from app.services.reports.crud import saved_review_artifact_for_thread

AgentTeamReportGenerationMode = Literal["deterministic_template", "provider_unavailable"]

_PUBLIC_ROLE_WARNING = ("no_reviewed_public_evidence",)
_PORTFOLIO_ROLE_EVIDENCE = (
    "trade_intent_summary",
    "scope_state",
    "actionability",
    "account_readiness",
    "freshness",
    "portfolio_impact_summary",
    "concentration_risk_drift",
    "liquidity_collateral_caveats",
    "options_exposure_summary",
    "market_quote_freshness",
)


def _now_utc() -> datetime:
    return datetime.now(UTC)


def generate_agent_team_report_for_thread(
    db: Session,
    user_id: UUID,
    thread_id: UUID,
    *,
    mode: AgentTeamReportGenerationMode = "deterministic_template",
) -> SavedAgentTeamSummaryRead | None:
    """Persist a sanitized Agent Team report summary for an existing saved artifact."""

    report_thread = db.scalar(
        select(ReportThread).where(
            ReportThread.id == thread_id,
            ReportThread.user_id == user_id,
            ReportThread.deleted_at.is_(None),
        )
    )
    if report_thread is None or not isinstance(report_thread.saved_artifact_json, dict):
        return None

    try:
        artifact = saved_review_artifact_for_thread(report_thread)
        evidence = SavedEvidencePackageRead.from_saved_review_artifact(artifact)
    except (TypeError, ValidationError, ValueError):
        return None

    report_generated_at = _now_utc()
    summary = build_agent_team_summary_from_evidence(
        evidence,
        mode=mode,
        report_generated_at=report_generated_at,
    )
    summary = _validate_or_fallback(
        summary.model_dump(mode="python"),
        evidence,
        report_generated_at=report_generated_at,
    )
    report_thread.saved_artifact_json = {
        **report_thread.saved_artifact_json,
        "agent_summary": summary.model_dump(mode="json"),
    }
    db.add(report_thread)
    db.commit()
    return summary


def build_agent_team_summary_from_evidence(
    evidence: SavedEvidencePackageRead,
    *,
    mode: AgentTeamReportGenerationMode = "deterministic_template",
    report_generated_at: datetime | None = None,
) -> SavedAgentTeamSummaryRead:
    """Build deterministic, provider-safe report content from saved evidence only."""

    generated_at = report_generated_at or _now_utc()
    if mode == "provider_unavailable":
        return _provider_unavailable_summary(evidence, report_generated_at=generated_at)
    if evidence.actionability.review_actionability_status.startswith("blocked_"):
        return _deterministic_draft_summary(evidence, report_generated_at=generated_at)

    role_summaries: list[SavedAgentTeamRoleSummaryRead] = []
    for role in role_registry():
        if role.role_name in {"fundamentals_analyst", "news_analyst", "technical_analyst"}:
            role_summaries.append(
                SavedAgentTeamRoleSummaryRead(
                    role_name=role.role_name,
                    display_name=role.display_name,
                    role_status="skipped",
                    provider_status="skipped",
                    summary_markdown=None,
                    evidence_references=("trade_intent_summary",),
                    warning_codes=_PUBLIC_ROLE_WARNING,
                    unavailable_reason="no_reviewed_public_evidence",
                )
            )
            continue
        role_summaries.append(_portfolio_role_summary(role.role_name, role.display_name, evidence))

    synthesis = (
        "Agent Team analysis is generated from the saved evidence package. "
        "Deterministic backend services own all calculations; scope, freshness, and caveats remain attached for audit."
    )
    return SavedAgentTeamSummaryRead(
        run_status="partially_completed",
        provider_mode="deterministic_template",
        report_generated_at=generated_at,
        role_summaries=tuple(role_summaries),
        warning_codes=("public_evidence_roles_skipped",),
        report_status="full_agent_report",
        final_synthesis_markdown=synthesis,
        final_synthesis_authored_by="deterministic_template",
        evidence_schema_version=evidence.evidence_schema_version,
        evidence_references=_PORTFOLIO_ROLE_EVIDENCE,
    )


def _portfolio_role_summary(
    role_name: str,
    display_name: str,
    evidence: SavedEvidencePackageRead,
) -> SavedAgentTeamRoleSummaryRead:
    if role_name == "risk_management_agent":
        markdown = (
            "Risk review uses the saved deterministic evidence package only. "
            "It highlights the saved actionability mode, freshness labels, and caveats for manual review."
        )
        warning_codes = evidence.caveat_codes
    else:
        markdown = (
            "Portfolio synthesis uses validated role summaries and the saved evidence package only. "
            "Deterministic backend services own all calculations."
        )
        warning_codes = ("public_evidence_roles_skipped",)
    return SavedAgentTeamRoleSummaryRead(
        role_name=role_name,
        display_name=display_name,
        role_status="completed",
        provider_status="ok",
        summary_markdown=markdown,
        evidence_references=_PORTFOLIO_ROLE_EVIDENCE,
        warning_codes=tuple(warning_codes),
    )


def _deterministic_draft_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime,
) -> SavedAgentTeamSummaryRead:
    role_summaries = tuple(
        SavedAgentTeamRoleSummaryRead(
            role_name=role.role_name,
            display_name=role.display_name,
            role_status="gated",
            provider_status="skipped",
            summary_markdown=None,
            evidence_references=(),
            warning_codes=("blocked_actionability_llm_roles_skipped",),
            unavailable_reason="blocked_actionability_llm_roles_skipped",
        )
        for role in role_registry()
    )
    return SavedAgentTeamSummaryRead(
        run_status="failed",
        provider_mode="deterministic_template",
        report_generated_at=report_generated_at,
        role_summaries=role_summaries,
        warning_codes=("blocked_actionability_llm_roles_skipped",),
        report_status="deterministic_draft",
        final_synthesis_markdown=None,
        final_synthesis_authored_by=None,
        evidence_schema_version=evidence.evidence_schema_version,
        evidence_references=(),
    )


def _provider_unavailable_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime,
) -> SavedAgentTeamSummaryRead:
    role_summaries = tuple(
        SavedAgentTeamRoleSummaryRead(
            role_name=role.role_name,
            display_name=role.display_name,
            role_status="unavailable",
            provider_status="provider_unavailable",
            summary_markdown=None,
            evidence_references=(),
            warning_codes=("agent_team_provider_unavailable",),
            unavailable_reason="provider_unavailable",
        )
        for role in role_registry()
    )
    return SavedAgentTeamSummaryRead(
        run_status="failed",
        provider_mode="provider_unavailable",
        report_generated_at=report_generated_at,
        role_summaries=role_summaries,
        warning_codes=("agent_team_provider_unavailable",),
        report_status="agent_unavailable",
        final_synthesis_markdown=None,
        final_synthesis_authored_by=None,
        evidence_schema_version=evidence.evidence_schema_version,
        evidence_references=(),
    )


def _validation_failed_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime,
) -> SavedAgentTeamSummaryRead:
    return SavedAgentTeamSummaryRead(
        run_status="failed",
        provider_mode="deterministic_template",
        report_generated_at=report_generated_at,
        role_summaries=(),
        warning_codes=("agent_output_failed_safety_validation",),
        report_status="validation_failed",
        final_synthesis_markdown=None,
        final_synthesis_authored_by=None,
        evidence_schema_version=evidence.evidence_schema_version,
        evidence_references=(),
    )


def _validate_or_fallback(
    payload: dict,
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime | None = None,
) -> SavedAgentTeamSummaryRead:
    try:
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)
        return SavedAgentTeamSummaryRead.model_validate(payload)
    except (TypeError, ValidationError, ValueError):
        return _validation_failed_summary(evidence, report_generated_at=report_generated_at or _now_utc())


def build_validation_failed_summary_for_test(
    evidence: SavedEvidencePackageRead,
    unsafe_payload: dict,
    *,
    report_generated_at: datetime | None = None,
) -> SavedAgentTeamSummaryRead:
    """Exercise failed-safe validation behavior in focused backend tests."""

    return _validate_or_fallback(unsafe_payload, evidence, report_generated_at=report_generated_at)
