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
from app.services.reports.public_evidence import (
    build_public_evidence_projection,
    build_public_role_evidence_projection,
)

AgentTeamReportGenerationMode = Literal["deterministic_template", "provider_unavailable"]

_PUBLIC_ROLE_NAMES: frozenset[str] = frozenset(
    {"fundamentals_analyst", "news_analyst", "technical_analyst"}
)
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

# Deterministic, provider-safe public-role narrative. Digit-free and
# non-directional by construction so the invented-level/metric guards and the
# advice-phrase guard cannot trip on generated output.
_PUBLIC_ROLE_TEMPLATES: dict[str, str] = {
    "fundamentals_analyst": (
        "Fundamentals analyst summary for {symbol}. Summarizes reviewed public "
        "company and fundamentals evidence only ({sections}). States what is "
        "available and what is unknown as qualitative, analysis-only context, with "
        "no invented valuations or directional conclusions. Deterministic backend "
        "services own all calculations."
    ),
    "news_analyst": (
        "News analyst summary for {symbol}. Summarizes reviewed public news and "
        "event context only ({sections}). Notes what is known, unknown, stale, or "
        "unavailable as analysis-only context for manual verification, with no "
        "price-movement predictions or event-timing directives. Deterministic "
        "backend services own all calculations."
    ),
    "technical_analyst": (
        "Technical analyst summary for {symbol}. Summarizes reviewed public market "
        "and technical context only ({sections}). Provides non-directional, "
        "qualitative framing and freshness notes, with no invented indicator "
        "values, support or resistance levels, or directional calls. Deterministic "
        "backend services own all calculations."
    ),
}
_PUBLIC_ROLE_LIMITED_CAVEAT = (
    "One or more cited public sections are limited or stale; treat that context as "
    "partial and verify it manually."
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
        if artifact.public_evidence is None:
            evidence = evidence.model_copy(
                update={
                    "public_evidence": build_public_evidence_projection(
                        symbol_or_underlying=evidence.trade_intent_summary.symbol_or_underlying
                    )
                }
            )
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
        "public_evidence": evidence.public_evidence.model_dump(mode="json") if evidence.public_evidence else None,
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

    summaries_by_role: dict[str, SavedAgentTeamRoleSummaryRead] = {}
    for role in role_registry():
        if role.role_name in _PUBLIC_ROLE_NAMES:
            summaries_by_role[role.role_name] = _public_role_summary(
                role.role_name, role.display_name, evidence
            )
    public_summaries = tuple(summaries_by_role.values())
    public_completed = tuple(s for s in public_summaries if s.role_status == "completed")
    coverage_code = _public_coverage_code(public_summaries, public_completed)

    for role in role_registry():
        if role.role_name not in _PUBLIC_ROLE_NAMES:
            summaries_by_role[role.role_name] = _portfolio_role_summary(
                role.role_name, role.display_name, evidence, coverage_code=coverage_code
            )
    role_summaries = tuple(summaries_by_role[role.role_name] for role in role_registry())
    run_status = (
        "completed"
        if all(summary.role_status == "completed" for summary in role_summaries)
        else "partially_completed"
    )

    public_clause = (
        " Validated public analyst context is included as analysis-only background "
        "where reviewed public evidence was available."
        if public_completed
        else ""
    )
    synthesis = (
        "Agent Team analysis is generated from the saved evidence package." + public_clause + " "
        "Deterministic backend services own all calculations; scope, freshness, and caveats remain attached for audit."
    )
    return SavedAgentTeamSummaryRead(
        run_status=run_status,
        provider_mode="deterministic_template",
        report_generated_at=generated_at,
        role_summaries=role_summaries,
        warning_codes=(coverage_code,),
        report_status="full_agent_report",
        final_synthesis_markdown=synthesis,
        final_synthesis_authored_by="deterministic_template",
        evidence_schema_version=evidence.evidence_schema_version,
        evidence_references=_PORTFOLIO_ROLE_EVIDENCE,
    )


def _public_coverage_code(
    public_summaries: tuple[SavedAgentTeamRoleSummaryRead, ...],
    public_completed: tuple[SavedAgentTeamRoleSummaryRead, ...],
) -> str:
    if not public_completed:
        return "public_evidence_roles_skipped"
    if len(public_completed) < len(public_summaries):
        return "public_evidence_partial_coverage"
    return "public_evidence_roles_included"


def _public_role_summary(
    role_name: str,
    display_name: str,
    evidence: SavedEvidencePackageRead,
) -> SavedAgentTeamRoleSummaryRead:
    """Wire one public role to its role-scoped projection with honest degradation."""

    try:
        projection = build_public_role_evidence_projection(
            evidence, role_name=role_name  # type: ignore[arg-type]
        )
    except (TypeError, ValidationError, ValueError):
        return SavedAgentTeamRoleSummaryRead(
            role_name=role_name,
            display_name=display_name,
            role_status="unavailable",
            provider_status="provider_unavailable",
            summary_markdown=None,
            evidence_references=(),
            warning_codes=("public_evidence_provider_unavailable",),
            unavailable_reason="public_evidence_provider_unavailable",
        )

    if not projection.citable_section_keys:
        reason = projection.degrade_reason or "public_evidence_unavailable"
        return SavedAgentTeamRoleSummaryRead(
            role_name=role_name,
            display_name=display_name,
            role_status="skipped",
            provider_status="skipped",
            summary_markdown=None,
            evidence_references=("trade_intent_summary",),
            warning_codes=(reason,),
            unavailable_reason=reason,
        )

    citable = set(projection.citable_section_keys)
    limited = any(
        section.availability == "limited" for section in projection.sections if section.section_key in citable
    )
    return SavedAgentTeamRoleSummaryRead(
        role_name=role_name,
        display_name=display_name,
        role_status="completed",
        provider_status="ok",
        summary_markdown=_public_role_markdown(role_name, projection, limited=limited),
        evidence_references=("trade_intent_summary", *projection.citable_section_keys),
        warning_codes=("public_evidence_limited",) if limited else (),
    )


def _public_role_markdown(role_name: str, projection, *, limited: bool) -> str:
    citable = set(projection.citable_section_keys)
    sections_phrase = ", ".join(
        section.section_label for section in projection.sections if section.section_key in citable
    )
    symbol = projection.instrument_context.symbol_or_underlying or "the reviewed instrument"
    markdown = _PUBLIC_ROLE_TEMPLATES[role_name].format(symbol=symbol, sections=sections_phrase)
    if limited:
        markdown = f"{markdown} {_PUBLIC_ROLE_LIMITED_CAVEAT}"
    return markdown


def _portfolio_role_summary(
    role_name: str,
    display_name: str,
    evidence: SavedEvidencePackageRead,
    *,
    coverage_code: str,
) -> SavedAgentTeamRoleSummaryRead:
    if role_name == "risk_management_agent":
        markdown = (
            "Risk review uses the saved deterministic evidence package only. "
            "It highlights the saved actionability mode, freshness labels, and caveats for manual review."
        )
        warning_codes: tuple[str, ...] = tuple(evidence.caveat_codes)
    else:
        markdown = (
            "Portfolio synthesis uses validated role summaries and the saved evidence package only, "
            "treating any public analyst context as analysis-only background. "
            "Deterministic backend services own all calculations."
        )
        warning_codes = (coverage_code,)
    return SavedAgentTeamRoleSummaryRead(
        role_name=role_name,
        display_name=display_name,
        role_status="completed",
        provider_status="ok",
        summary_markdown=markdown,
        evidence_references=_PORTFOLIO_ROLE_EVIDENCE,
        warning_codes=warning_codes,
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
