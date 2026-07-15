"""On-demand Agent Team report generation from saved review evidence."""

from __future__ import annotations

from datetime import UTC, datetime
import os
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ConfigurationError
from app.models.report_thread import ReportThread
from app.schemas.reports import (
    SavedAgentTeamRoleSummaryRead,
    SavedAgentTeamSummaryRead,
    SavedEvidencePackageRead,
)
from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output
from app.services.agent_team.agents.roles import role_registry
from app.services.reports.crud import saved_review_artifact_for_thread
from app.services.reports.public_evidence import (
    EdgarCompanyProfileClient,
    EdgarCompanyProfileSourcePolicy,
    build_public_evidence_projection,
    build_public_role_evidence_projection,
)
from app.services.reports.source_snapshots import (
    FmpFundamentalsExecutionContext,
    FmpFundamentalsSourcePolicy,
    FredMacroSeriesExecutionContext,
    FredMacroSeriesSourcePolicy,
)
from app.services.market_data.eod_history import MarketContextExecutionContext, MarketContextPolicy

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.agent_team.llm_clients.factory import LLMProviderResolution

AgentTeamReportGenerationMode = Literal["deterministic_template", "provider_unavailable", "tool_mediated"]
BackendAgentTeamReportGenerationMode = Literal["deterministic_template", "tool_mediated"]

P36_LIVE_LANES_ENV = "POA_P36_LIVE_LANES"
_P36_LIVE_LANE_NAMES = frozenset({"risk", "public", "pm"})

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
        "Fundamentals analyst briefing for {symbol}: public company context you "
        "might overlook. It summarizes reviewed public company and fundamentals "
        "evidence only ({sections}), states what is missing as qualitative context, "
        "and leaves all calculations to deterministic backend services."
    ),
    "news_analyst": (
        "News analyst briefing for {symbol}: public event context you might "
        "overlook. It summarizes reviewed public news and event evidence only "
        "({sections}) and notes unavailable context without price-movement "
        "predictions or event-timing directives."
    ),
    "technical_analyst": (
        "Technical analyst briefing for {symbol}: reviewed public market context "
        "you might overlook. It summarizes reviewed public technical evidence only "
        "({sections}) using non-directional qualitative framing, without invented "
        "indicator values or directional calls."
    ),
}
_PUBLIC_ROLE_LIMITED_CAVEAT = (
    "One or more cited public sections are limited or stale; treat that context as "
    "partial and verify it manually."
)


def _now_utc() -> datetime:
    return datetime.now(UTC)


def resolve_backend_agent_team_report_generation_mode(
    env: "Mapping[str, str] | None" = None,
) -> BackendAgentTeamReportGenerationMode:
    """Resolve the backend-only report generation mode without client input."""

    values = env if env is not None else os.environ
    raw = values.get("POA_AGENT_TEAM_REPORT_GENERATION_MODE", "").strip().lower()
    if raw in {"tool_mediated", "tool-mediated", "tool_mediated_mock", "tool_mediated_live"}:
        return "tool_mediated"
    return "deterministic_template"


def resolve_agent_team_report_provider_resolution(env: "Mapping[str, str] | None" = None) -> "LLMProviderResolution":
    """Resolve the backend-owned provider only after tool-mediated mode is enabled."""

    from app.services.agent_team.llm_clients.factory import resolve_llm_provider_from_env

    return resolve_llm_provider_from_env(env)


def resolve_p36_live_lane_flags(env: "Mapping[str, str] | None" = None) -> tuple[bool, bool, bool]:
    """Resolve the backend-only P36 live-lane subset without client input."""

    values = env if env is not None else os.environ
    raw = values.get(P36_LIVE_LANES_ENV, "")
    if not raw.strip():
        return False, False, False
    lanes = frozenset(part.strip().lower() for part in raw.split(","))
    unknown = lanes - _P36_LIVE_LANE_NAMES
    if unknown:
        raise ConfigurationError(f"{P36_LIVE_LANES_ENV} contains unsupported lane names")
    return "risk" in lanes, "public" in lanes, "pm" in lanes


def generate_agent_team_report_for_thread(
    db: Session,
    user_id: UUID,
    thread_id: UUID,
    *,
    mode: AgentTeamReportGenerationMode = "deterministic_template",
    edgar_policy: EdgarCompanyProfileSourcePolicy | None = None,
    edgar_client: EdgarCompanyProfileClient | None = None,
    fmp_fundamentals_policy: FmpFundamentalsSourcePolicy | None = None,
    fmp_fundamentals_context: FmpFundamentalsExecutionContext | None = None,
    fmp_eod_history_policy: MarketContextPolicy | None = None,
    fmp_eod_history_context: MarketContextExecutionContext | None = None,
    fred_macro_series_policy: FredMacroSeriesSourcePolicy | None = None,
    fred_macro_series_context: FredMacroSeriesExecutionContext | None = None,
    provider_resolution: "LLMProviderResolution | None" = None,
    p36_risk_live_enabled: bool = False,
    p36_public_live_enabled: bool = False,
    p36_pm_live_enabled: bool = False,
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
                        symbol_or_underlying=evidence.trade_intent_summary.symbol_or_underlying,
                        edgar_policy=edgar_policy,
                        edgar_client=edgar_client,
                        fmp_fundamentals_policy=fmp_fundamentals_policy,
                        fmp_fundamentals_context=fmp_fundamentals_context,
                        fmp_eod_history_policy=fmp_eod_history_policy,
                        fmp_eod_history_context=fmp_eod_history_context,
                        fred_macro_series_policy=fred_macro_series_policy,
                        fred_macro_series_context=fred_macro_series_context,
                    )
                }
            )
    except (TypeError, ValidationError, ValueError):
        return None

    report_generated_at = _now_utc()
    if mode == "tool_mediated":
        summary = _build_tool_mediated_summary(
            evidence,
            provider_resolution=provider_resolution,
            report_generated_at=report_generated_at,
            p36_risk_live_enabled=p36_risk_live_enabled,
            p36_public_live_enabled=p36_public_live_enabled,
            p36_pm_live_enabled=p36_pm_live_enabled,
        )
    else:
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


def _build_tool_mediated_summary(
    evidence: SavedEvidencePackageRead,
    *,
    provider_resolution: "LLMProviderResolution | None",
    report_generated_at: datetime,
    p36_risk_live_enabled: bool = False,
    p36_public_live_enabled: bool = False,
    p36_pm_live_enabled: bool = False,
) -> SavedAgentTeamSummaryRead:
    from app.services.agent_team.llm_clients.factory import resolve_llm_provider
    from app.services.agent_team.tool_mediated_report import (
        build_tool_mediated_agent_team_summary_from_provider_resolution,
    )

    resolution = provider_resolution or resolve_llm_provider()
    return build_tool_mediated_agent_team_summary_from_provider_resolution(
        evidence,
        provider_resolution=resolution,
        report_generated_at=report_generated_at,
        p36_risk_live_enabled=p36_risk_live_enabled,
        p36_public_live_enabled=p36_public_live_enabled,
        p36_pm_live_enabled=p36_pm_live_enabled,
    )


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

    evidence_references = _portfolio_role_evidence_references(evidence)
    synthesis = _portfolio_manager_synthesis_markdown(evidence, public_summaries, public_completed)
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
        evidence_references=evidence_references,
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
    if role_name == "fundamentals_analyst" and "public_company_profile" in citable:
        return _fundamentals_company_profile_markdown(projection, limited=limited)

    sections_phrase = ", ".join(
        section.section_label for section in projection.sections if section.section_key in citable
    )
    symbol = projection.instrument_context.symbol_or_underlying or "the reviewed instrument"
    markdown = _PUBLIC_ROLE_TEMPLATES[role_name].format(symbol=symbol, sections=sections_phrase)
    if limited:
        markdown = f"{markdown} {_PUBLIC_ROLE_LIMITED_CAVEAT}"
    return markdown


def _fundamentals_company_profile_markdown(projection, *, limited: bool) -> str:
    citable = set(projection.citable_section_keys)
    profile = next(
        section for section in projection.sections if section.section_key == "public_company_profile"
    )
    fact_keys = {fact.fact_key for fact in profile.facts if fact.value_label}
    present_facts = [
        label
        for key, label in (
            ("company_name", "company name"),
            ("ticker", "ticker"),
            ("exchange", "listing exchange"),
            ("cik_reference", "CIK reference"),
            ("sic_label", "SEC SIC regulatory classification metadata"),
            ("fiscal_year_end", "fiscal year-end metadata"),
        )
        if key in fact_keys
    ]
    fact_phrase = ", ".join(present_facts) if present_facts else "company identity metadata"
    unavailable_sections = tuple(
        section.section_label
        for section in projection.sections
        if section.section_key in {"public_fundamentals_snapshot", "public_events_calendar"}
        and section.section_key not in citable
    )
    unavailable_sentence = (
        f" {', '.join(unavailable_sections)} remains not reviewed in this saved evidence package."
        if unavailable_sections
        else ""
    )
    sic_sentence = (
        " SEC SIC metadata is source-specific regulatory metadata and may be broad, legacy, "
        "and may lag company changes."
        if "sic_label" in fact_keys
        else ""
    )
    limited_sentence = f" {_PUBLIC_ROLE_LIMITED_CAVEAT}" if limited else ""
    return (
        "Fundamentals analyst briefing. Reviewed SEC EDGAR metadata - company profile only "
        f"is available as company identity and listing context you might overlook. Present structured facts include {fact_phrase}."
        f"{sic_sentence}{unavailable_sentence}{limited_sentence} This context is background only; "
        "deterministic backend services own all calculations."
    )


def _public_synthesis_clause(
    evidence: SavedEvidencePackageRead,
    public_completed: tuple[SavedAgentTeamRoleSummaryRead, ...],
) -> str:
    if not public_completed:
        return ""
    profile = evidence.public_evidence.public_company_profile if evidence.public_evidence is not None else None
    if profile is not None and profile.availability in {"available", "limited"}:
        return (
            " Saved company identity and listing context is included as analysis-only "
            "background where reviewed profile evidence was available."
        )
    return (
        " Validated public analyst context is included as analysis-only background "
        "where reviewed public evidence was available."
    )


def _portfolio_role_summary(
    role_name: str,
    display_name: str,
    evidence: SavedEvidencePackageRead,
    *,
    coverage_code: str,
) -> SavedAgentTeamRoleSummaryRead:
    evidence_references = _portfolio_role_evidence_references(evidence)
    if role_name == "risk_management_agent":
        markdown = _risk_manager_markdown(evidence)
        warning_codes: tuple[str, ...] = tuple(evidence.caveat_codes)
    else:
        markdown = _portfolio_manager_role_markdown(evidence, coverage_code=coverage_code)
        warning_codes = (coverage_code,)
    return SavedAgentTeamRoleSummaryRead(
        role_name=role_name,
        display_name=display_name,
        role_status="completed",
        provider_status="ok",
        summary_markdown=markdown,
        evidence_references=evidence_references,
        warning_codes=warning_codes,
    )


def _portfolio_role_evidence_references(evidence: SavedEvidencePackageRead) -> tuple[str, ...]:
    references: list[str] = []
    for reference in _PORTFOLIO_ROLE_EVIDENCE:
        if reference == "market_quote_freshness" and evidence.market_quote_freshness.availability == "not_available":
            continue
        references.append(reference)
    return tuple(references)


def _risk_manager_markdown(evidence: SavedEvidencePackageRead) -> str:
    return (
        "Risk Manager briefing: what could be overlooked if acting from memory. "
        "It uses saved deterministic risk flags, freshness categories, scope caveats, "
        "liquidity and collateral caveats, and option-exposure caveats only."
        f"{_account_feasibility_sentence(evidence)}"
        f"{_market_quote_gap_sentence(evidence)} "
        "Deterministic backend services own all calculations."
    )


def _portfolio_manager_role_markdown(
    evidence: SavedEvidencePackageRead,
    *,
    coverage_code: str,
) -> str:
    return (
        "Portfolio Manager briefing: synthesis of what the saved package does and does not cover. "
        "It groups deterministic risk flags, data freshness gaps, scope and feasibility caveats, "
        "and public context gaps as background for manual review."
        f"{_account_feasibility_sentence(evidence)} "
        f"{_public_context_gap_sentence(coverage_code)} Scope, freshness, and caveats remain attached for audit."
    )


def _portfolio_manager_synthesis_markdown(
    evidence: SavedEvidencePackageRead,
    public_summaries: tuple[SavedAgentTeamRoleSummaryRead, ...],
    public_completed: tuple[SavedAgentTeamRoleSummaryRead, ...],
) -> str:
    coverage_code = _public_coverage_code(public_summaries, public_completed)
    return (
        "What you would be ignoring if you acted manually now: "
        "deterministic risk flags from the saved review; data freshness and availability gaps; "
        "scope and feasibility caveats; and context not reviewed in the saved package."
        f"{_market_quote_gap_sentence(evidence)}"
        f"{_account_feasibility_sentence(evidence)} "
        f"{_public_context_gap_sentence(coverage_code)}"
        f"{_public_synthesis_clause(evidence, public_completed)} "
        "Manual verification checklist: review the saved scope, freshness categories, feasibility caveats, "
        "option-leg mechanics, and any missing public context before acting on your own. "
        "This is read-only context for manual review, not an instruction or judgment about whether to act. "
        "Deterministic backend services own all calculations."
    )


def _account_feasibility_sentence(evidence: SavedEvidencePackageRead) -> str:
    if evidence.scope_state.account_level_feasibility_evaluated:
        return ""
    return " Account-level feasibility was not evaluated in the saved scope."


def _market_quote_gap_sentence(evidence: SavedEvidencePackageRead) -> str:
    if evidence.market_quote_freshness.availability == "not_available":
        return " Market quote freshness is unavailable in the saved evidence."
    label = (evidence.market_quote_freshness.summary_label or "").lower()
    if "stale" in label or "unavailable" in label or "unknown" in label:
        return " Market quote freshness is flagged for manual review in the saved evidence."
    return ""


def _public_context_gap_sentence(coverage_code: str) -> str:
    if coverage_code == "public_evidence_roles_included":
        return "Reviewed public-role context is attached as secondary background."
    if coverage_code == "public_evidence_partial_coverage":
        return "Some public-role context is attached; missing public checks remain a context gap."
    return "No reviewed fundamentals, news, or technical context was attached to this saved package."


def _deterministic_draft_summary(
    evidence: SavedEvidencePackageRead,
    *,
    report_generated_at: datetime,
) -> SavedAgentTeamSummaryRead:
    evidence_references = _portfolio_role_evidence_references(evidence)
    synthesis = (
        "What you would be ignoring if you acted manually now: the saved deterministic review did not complete "
        "because the actionability gate stopped the specialist briefing. Deterministic evidence remains attached "
        "for audit."
        f"{_market_quote_gap_sentence(evidence)}"
        f"{_account_feasibility_sentence(evidence)} "
        "Manual verification checklist: review freshness categories, scope caveats, feasibility caveats, "
        "and option-leg mechanics in the saved evidence before acting on your own. "
        "This is read-only context for manual review, not an instruction or judgment about whether to act."
    )
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
        final_synthesis_markdown=synthesis,
        final_synthesis_authored_by="deterministic_template",
        evidence_schema_version=evidence.evidence_schema_version,
        evidence_references=evidence_references,
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
    eval_flag: str | None = None,
) -> SavedAgentTeamSummaryRead:
    warning_codes = tuple(
        dict.fromkeys(("agent_output_failed_safety_validation", *((eval_flag,) if eval_flag else ())))
    )
    return SavedAgentTeamSummaryRead(
        run_status="failed",
        provider_mode="deterministic_template",
        report_generated_at=report_generated_at,
        role_summaries=(),
        warning_codes=warning_codes,
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
    except (TypeError, ValidationError, ValueError) as exc:
        eval_flag = "display_token_blocked" if "display_token_blocked" in str(exc) else None
        return _validation_failed_summary(
            evidence,
            report_generated_at=report_generated_at or _now_utc(),
            eval_flag=eval_flag,
        )


def build_validation_failed_summary_for_test(
    evidence: SavedEvidencePackageRead,
    unsafe_payload: dict,
    *,
    report_generated_at: datetime | None = None,
) -> SavedAgentTeamSummaryRead:
    """Exercise failed-safe validation behavior in focused backend tests."""

    return _validate_or_fallback(unsafe_payload, evidence, report_generated_at=report_generated_at)
