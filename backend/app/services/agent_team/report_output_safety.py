"""Safety validation for saved Agent Team report output."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.reports import SavedEvidencePackageRead, validate_saved_review_artifact_payload
from app.services.agent_team.output_safety import validate_llm_provider_output


PUBLIC_EVIDENCE_KEYS = frozenset(
    {
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_news_snapshot",
        "public_events_calendar",
        "public_technical_context",
        "public_market_context",
    }
)
CANONICAL_EVIDENCE_KEYS = frozenset(
    {
        "trade_intent_summary",
        "scope_state",
        "freshness",
        "actionability",
        "account_readiness",
        "portfolio_impact_summary",
        "before_after_portfolio_impact",
        "concentration_risk_drift",
        "liquidity_collateral_caveats",
        "options_exposure_summary",
        "market_quote_freshness",
        "economic_awareness_snapshot",
        "market_mood_snapshot",
    }
).union(PUBLIC_EVIDENCE_KEYS)
ALWAYS_CITABLE_EVIDENCE_KEYS = frozenset({"trade_intent_summary", "scope_state", "freshness", "actionability"})
ROLE_ALLOWED_EVIDENCE_KEYS: dict[str, frozenset[str]] = {
    "fundamentals_analyst": frozenset(
        {
            "trade_intent_summary",
            "public_company_profile",
            "public_fundamentals_snapshot",
            "public_events_calendar",
        }
    ),
    "news_analyst": frozenset(
        {
            "trade_intent_summary",
            "public_news_snapshot",
            "public_events_calendar",
            "public_market_context",
            "economic_awareness_snapshot",
            "market_mood_snapshot",
        }
    ),
    "technical_analyst": frozenset(
        {
            "trade_intent_summary",
            "public_technical_context",
            "public_market_context",
            "market_quote_freshness",
        }
    ),
    "risk_management_agent": frozenset(
        {
            "trade_intent_summary",
            "scope_state",
            "actionability",
            "account_readiness",
            "freshness",
            "portfolio_impact_summary",
            "before_after_portfolio_impact",
            "concentration_risk_drift",
            "liquidity_collateral_caveats",
            "options_exposure_summary",
            "market_quote_freshness",
        }
    ),
    "portfolio_manager_agent": frozenset(
        {
            "trade_intent_summary",
            "scope_state",
            "actionability",
            "account_readiness",
            "freshness",
            "portfolio_impact_summary",
            "before_after_portfolio_impact",
            "concentration_risk_drift",
            "liquidity_collateral_caveats",
            "options_exposure_summary",
            "market_quote_freshness",
            "economic_awareness_snapshot",
            "market_mood_snapshot",
            *PUBLIC_EVIDENCE_KEYS,
        }
    ),
}
PORTFOLIO_MANAGER_SYNTHESIS_EVIDENCE_KEYS = ROLE_ALLOWED_EVIDENCE_KEYS["portfolio_manager_agent"]
REPORT_PROHIBITED_PHRASES = frozenset(
    {
        "financial advice",
        "investment advice",
        "trading advice",
        "trade advice",
        "trade recommendation",
        "investment recommendation",
        "buy recommendation",
        "sell recommendation",
        "our recommendation",
        "we recommend",
        "i recommend",
        "recommendation to buy",
        "recommendation to sell",
        "recommend buying",
        "recommend selling",
        "you should buy",
        "you should sell",
        "should buy",
        "should sell",
        "i would buy",
        "i would sell",
        "buy now",
        "sell now",
        "enter the trade",
        "exit the trade",
        "take the trade",
        "make the trade",
        "open a position",
        "close the position",
        "place order",
        "place an order",
        "submit order",
        "submit an order",
        "execute trade",
        "execute the trade",
        "order instruction",
        "safe to trade",
        "ready to trade",
        "safe-to-trade",
        "ready-to-trade",
        "guaranteed",
        "guaranteed return",
        "guaranteed returns",
    }
)
REPORT_ALLOWED_NEGATED_DISCLOSURES = (
    (
        "source: fred, federal reserve bank of st. louis. economic release/calendar metadata only. "
        "not investment advice or a trading signal."
    ),
    (
        "fred aggregates data from multiple sources; releases may lag, revise, or be subject to "
        "source-specific rights. portfolio copilot does not use this as a trade recommendation."
    ),
)
# Bare-number invented technical levels / price targets. Public and technical
# role narrative is qualitative and carries no numbers, so any level keyword
# adjacent to a digit is LLM-invented and rejected (deterministic metrics are
# backend-owned and never appear in narrative). Input is repr().lower().
INVENTED_LEVEL_PATTERNS = (
    re.compile(r"\b(?:support|resistance|pivot|breakout|breakdown)\b[^.\n]{0,16}?\d"),
    re.compile(r"\d[^.\n]{0,8}?\b(?:support|resistance|pivot)\b"),
    re.compile(r"\b(?:price\s+)?target\b[^.\n]{0,8}?\d"),
    re.compile(r"\blevels?\b[^.\n]{0,8}?\d"),
)
# Source leakage: report output must carry sanitized labels only, never source
# URLs, links, or raw source references (article bodies are already stripped at
# the public-evidence layer; this guards generated narrative).
SOURCE_LEAK_PATTERNS = (
    re.compile(r"https?://"),
    re.compile(r"\bwww\.[a-z0-9.-]+"),
)


def validate_agent_team_report_output(
    payload: object,
    *,
    label: str,
    evidence_package: SavedEvidencePackageRead | None = None,
) -> None:
    """Reject unsafe Agent Team report output before persistence or projection."""

    validate_saved_review_artifact_payload(payload)
    validate_llm_provider_output(payload, label=label)
    _reject_report_phrases(payload, label=label)
    _reject_source_leaks(payload, label=label)
    _reject_invented_levels(payload, label=label)
    _validate_evidence_references(payload, evidence_package=evidence_package)


def _reject_report_phrases(value: object, *, label: str) -> None:
    rendered = repr(value).lower()
    for disclosure in REPORT_ALLOWED_NEGATED_DISCLOSURES:
        rendered = rendered.replace(disclosure, "")
    if any(phrase in rendered for phrase in REPORT_PROHIBITED_PHRASES):
        raise ValueError(f"{label} contains prohibited advice or execution wording")


def _reject_source_leaks(value: object, *, label: str) -> None:
    rendered = repr(value).lower()
    if any(pattern.search(rendered) for pattern in SOURCE_LEAK_PATTERNS):
        raise ValueError(f"{label} contains a source URL or raw source reference")


def _reject_invented_levels(value: object, *, label: str) -> None:
    rendered = repr(value).lower()
    if any(pattern.search(rendered) for pattern in INVENTED_LEVEL_PATTERNS):
        raise ValueError(f"{label} contains an invented technical level or price target")


def _validate_evidence_references(
    payload: object,
    *,
    evidence_package: SavedEvidencePackageRead | None,
) -> None:
    if not isinstance(payload, dict):
        return
    section_availability = _section_availability(evidence_package)
    for section in payload.get("role_sections") or ():
        _validate_role_reference_section(section, section_availability=section_availability)
    for section in payload.get("role_summaries") or ():
        _validate_role_reference_section(section, section_availability=section_availability)
    synthesis = payload.get("final_synthesis")
    if isinstance(synthesis, dict):
        _validate_reference_set(
            synthesis.get("evidence_references") or (),
            allowed=PORTFOLIO_MANAGER_SYNTHESIS_EVIDENCE_KEYS,
            section_availability=section_availability,
        )
    if "evidence_references" in payload:
        _validate_reference_set(
            payload.get("evidence_references") or (),
            allowed=PORTFOLIO_MANAGER_SYNTHESIS_EVIDENCE_KEYS,
            section_availability=section_availability,
        )


def _validate_role_reference_section(
    section: object,
    *,
    section_availability: dict[str, str],
) -> None:
    if not isinstance(section, dict):
        return
    role_name = str(section.get("role_name") or "")
    allowed = ROLE_ALLOWED_EVIDENCE_KEYS.get(role_name)
    if allowed is None:
        raise ValueError("agent-team report contains unknown role")
    _validate_reference_set(
        section.get("evidence_references") or (),
        allowed=allowed,
        section_availability=section_availability,
    )


def _validate_reference_set(
    references: Any,
    *,
    allowed: frozenset[str],
    section_availability: dict[str, str],
) -> None:
    for reference in references:
        ref = str(reference)
        if ref not in CANONICAL_EVIDENCE_KEYS or ref not in allowed:
            raise ValueError("agent-team report cites evidence outside the role boundary")
        availability = section_availability.get(ref)
        if availability is not None and availability not in {"available", "limited"}:
            raise ValueError("agent-team report cites unavailable evidence")


def _section_availability(evidence_package: SavedEvidencePackageRead | None) -> dict[str, str]:
    if evidence_package is None:
        return {}
    availability: dict[str, str] = {}
    _collect_section_availability(evidence_package.model_dump(mode="python"), availability)
    return availability


def _collect_section_availability(value: object, availability: dict[str, str]) -> None:
    if isinstance(value, dict):
        section_key = value.get("section_key")
        section_availability = value.get("availability")
        if isinstance(section_key, str) and isinstance(section_availability, str):
            availability[section_key] = section_availability
        for child in value.values():
            _collect_section_availability(child, availability)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _collect_section_availability(child, availability)
