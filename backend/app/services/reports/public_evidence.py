"""Offline public evidence projection helpers for saved Agent Team reports."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.reports import (
    AgentTeamPublicRoleName,
    SavedEvidencePackageRead,
    SavedPublicEvidencePackageRead,
    SavedPublicRoleEvidenceProjectionRead,
    SavedPublicRoleInstrumentContextRead,
)
from app.services.agent_team.report_output_safety import ROLE_ALLOWED_EVIDENCE_KEYS


@dataclass(frozen=True)
class PublicEvidenceProjectionRequest:
    symbol_or_underlying: str | None = None


class NoReviewedPublicEvidenceProvider:
    """Default provider boundary until public source rights are reviewed."""

    def snapshot(self, request: PublicEvidenceProjectionRequest) -> SavedPublicEvidencePackageRead:
        return SavedPublicEvidencePackageRead.not_reviewed(request.symbol_or_underlying)


def build_public_evidence_projection(
    *,
    symbol_or_underlying: str | None,
) -> SavedPublicEvidencePackageRead:
    """Build the default generation-time public evidence projection."""

    return NoReviewedPublicEvidenceProvider().snapshot(
        PublicEvidenceProjectionRequest(symbol_or_underlying=symbol_or_underlying)
    )


_PUBLIC_ROLE_SECTION_KEYS: dict[AgentTeamPublicRoleName, tuple[str, ...]] = {
    "fundamentals_analyst": (
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_events_calendar",
    ),
    "news_analyst": (
        "public_news_snapshot",
        "public_events_calendar",
        "public_market_context",
    ),
    "technical_analyst": (
        "public_technical_context",
        "public_market_context",
    ),
}


def build_public_role_evidence_projection(
    evidence: SavedEvidencePackageRead,
    *,
    role_name: AgentTeamPublicRoleName,
) -> SavedPublicRoleEvidenceProjectionRead:
    """Narrow generation-time public evidence to a single public role boundary."""

    public_evidence = evidence.public_evidence or build_public_evidence_projection(
        symbol_or_underlying=evidence.trade_intent_summary.symbol_or_underlying
    )
    allowed_section_keys = tuple(
        section_key
        for section_key in _PUBLIC_ROLE_SECTION_KEYS[role_name]
        if section_key in ROLE_ALLOWED_EVIDENCE_KEYS[role_name]
    )
    sections = tuple(getattr(public_evidence, section_key) for section_key in allowed_section_keys)
    citable_section_keys = tuple(
        section.section_key for section in sections if section.availability in {"available", "limited"}
    )
    return SavedPublicRoleEvidenceProjectionRead(
        role_name=role_name,
        instrument_context=SavedPublicRoleInstrumentContextRead(
            symbol_or_underlying=evidence.trade_intent_summary.symbol_or_underlying,
            review_flow_label=evidence.trade_intent_summary.review_flow_label,
        ),
        allowed_section_keys=allowed_section_keys,
        sections=sections,
        citable_section_keys=citable_section_keys,
        degrade_reason=_public_projection_degrade_reason(sections, citable_section_keys),
    )


def _public_projection_degrade_reason(sections: tuple[object, ...], citable_section_keys: tuple[str, ...]) -> str | None:
    if citable_section_keys:
        return None
    availability = {getattr(section, "availability", None) for section in sections}
    if availability == {"not_reviewed"}:
        return "no_reviewed_public_evidence"
    if availability == {"not_available"}:
        return "public_evidence_not_available"
    if availability == {"not_applicable"}:
        return "public_evidence_not_applicable"
    return "public_evidence_unavailable"
