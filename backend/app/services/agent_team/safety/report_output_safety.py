"""Safety validation for saved Agent Team report output."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.reports import SavedEvidencePackageRead, validate_saved_review_artifact_payload
from app.services.agent_team.safety.output_safety import validate_llm_provider_output
from app.services.reports.display_labels import DISPLAY_TOKEN_BLOCKED_FLAG, find_internal_display_tokens


PUBLIC_EVIDENCE_KEYS = frozenset(
    {
        "public_company_profile",
        "public_fundamentals_snapshot",
        "fred_macro_series_snapshot",
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
            "fred_macro_series_snapshot",
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
            "public_market_context",
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
    (
        "source: sec edgar submissions/index metadata. recent filing metadata only. "
        "not investment advice or a trading signal."
    ),
    (
        "edgar filing metadata may lag, be corrected, or omit filings that are not available through edgar. "
        "portfolio copilot does not interpret filing contents or treat filing metadata as a trading signal."
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
BACKEND_PROSE_METRIC_RE = re.compile(
    r"(?<![A-Za-z])\$[0-9][0-9,]*(?:\.[0-9]+)?|\b[0-9]+(?:\.[0-9]+)?\s?%",
    re.IGNORECASE,
)
BACKEND_METRIC_PROSE_KEYS = frozenset({"claim_text", "final_synthesis_markdown", "summary_markdown", "section_markdown"})
P35_PROHIBITED_REPORT_PATTERNS = (
    re.compile(r"\b(?:overweight|underweight)\b", re.IGNORECASE),
    re.compile(r"\b(?:comfortable|healthy|prudent|excessive)\b", re.IGNORECASE),
    re.compile(r"\bsafely?\b", re.IGNORECASE),
    re.compile(r"\btoo\s+concentrated\b", re.IGNORECASE),
    re.compile(r"\bwell\s+diversified\b", re.IGNORECASE),
    re.compile(r"\b(?:opportunity|attractive|cheap|expensive)\b", re.IGNORECASE),
    re.compile(r"\breasonable\s+size\b", re.IGNORECASE),
    re.compile(r"\bplenty\s+of\b", re.IGNORECASE),
    re.compile(r"\b(?:is|are|looks|seems)\s+fine\b", re.IGNORECASE),
    re.compile(r"\b(?:likely|unlikely)\b", re.IGNORECASE),
    re.compile(r"\b(?:probability|odds)\b", re.IGNORECASE),
    re.compile(r"\b(?:price\s+)?target\b", re.IGNORECASE),
    re.compile(r"\b(?:support|resistance|entry\s+point)\b", re.IGNORECASE),
    re.compile(r"\b(?:yield|annualized|return\s+on\s+collateral)\b", re.IGNORECASE),
    re.compile(r"\byou\s+should\b", re.IGNORECASE),
    re.compile(r"\bshould\s+(?:add|trim|rebalance|buy|sell|hold|wait|spread)\b", re.IGNORECASE),
    re.compile(r"\bconsider\s+(?:add(?:ing)?|trim(?:ming)?|rebalance|rebalancing|spread(?:ing)?|wait(?:ing)?)\b", re.IGNORECASE),
    re.compile(r"(?<!would\s)\b(?:add|trim|rebalance)\s+(?:this|that|the|your|it)\b", re.IGNORECASE),
    re.compile(r"\b(?:buy|sell|hold)\s+(?:this|that|the|your|it|now)\b", re.IGNORECASE),
)


def validate_agent_team_report_output(
    payload: object,
    *,
    label: str,
    evidence_package: SavedEvidencePackageRead | None = None,
    allow_p36_live_markdown: bool = False,
) -> None:
    """Reject unsafe Agent Team report output before persistence or projection."""

    validate_saved_review_artifact_payload(payload)
    validate_llm_provider_output(
        _payload_for_provider_output_safety(payload),
        label=label,
        allow_value_bearing_markdown=allow_p36_live_markdown or _payload_has_p36_tool_freeze(payload),
    )
    _reject_report_phrases(payload, label=label)
    _reject_source_leaks(payload, label=label)
    _reject_invented_levels(payload, label=label)
    _reject_display_tokens_in_prose(payload, label=label)
    _validate_evidence_references(payload, evidence_package=evidence_package)


def _reject_report_phrases(value: object, *, label: str) -> None:
    rendered = repr(value).lower()
    for disclosure in REPORT_ALLOWED_NEGATED_DISCLOSURES:
        rendered = rendered.replace(disclosure, "")
    if any(phrase in rendered for phrase in REPORT_PROHIBITED_PHRASES):
        raise ValueError(f"{label} contains prohibited advice or execution wording")
    if any(pattern.search(rendered) for pattern in P35_PROHIBITED_REPORT_PATTERNS):
        raise ValueError(f"{label} contains prohibited advice, instruction, or evaluative wording")


def _payload_for_provider_output_safety(value: object, *, key: str | None = None) -> object:
    """Keep live-output metric guards while allowing backend-derived P35 prose metrics."""

    if isinstance(value, dict):
        return {item_key: _payload_for_provider_output_safety(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_payload_for_provider_output_safety(item, key=key) for item in value)
    if isinstance(value, str) and key in BACKEND_METRIC_PROSE_KEYS:
        return BACKEND_PROSE_METRIC_RE.sub("<backend_metric>", value)
    return value


def _payload_has_p36_tool_freeze(value: object) -> bool:
    """Allow P36 numeric prose only when its frozen v3 artifact is present.

    The artifact validator re-applies F-5/F-6 on readback. A bare report
    payload cannot opt out of the legacy generated-metric safety scan.
    """

    if not isinstance(value, dict):
        return False
    artifact = value.get("tool_run_artifact")
    return isinstance(artifact, dict) and artifact.get("artifact_schema_version") == "p36_tool_run_freeze_v1"


def _reject_source_leaks(value: object, *, label: str) -> None:
    rendered = repr(value).lower()
    if any(pattern.search(rendered) for pattern in SOURCE_LEAK_PATTERNS):
        raise ValueError(f"{label} contains a source URL or raw source reference")


def _reject_invented_levels(value: object, *, label: str) -> None:
    rendered = repr(value).lower()
    if any(pattern.search(rendered) for pattern in INVENTED_LEVEL_PATTERNS):
        raise ValueError(f"{label} contains an invented technical level or price target")


USER_VISIBLE_PROSE_KEYS = frozenset(
    {
        "claim_text",
        "final_synthesis_markdown",
        "live_report_markdown",
        "summary_markdown",
    }
)


def _reject_display_tokens_in_prose(value: object, *, label: str) -> None:
    paths = _find_display_token_prose_paths(value)
    if paths:
        raise ValueError(f"{label} {DISPLAY_TOKEN_BLOCKED_FLAG}: {sorted(paths)}")


def _find_display_token_prose_paths(value: object, *, path: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            if key_text in USER_VISIBLE_PROSE_KEYS and isinstance(item, str):
                if find_internal_display_tokens(item):
                    found.add(child_path)
            else:
                found.update(_find_display_token_prose_paths(item, path=child_path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            found.update(_find_display_token_prose_paths(item, path=child_path))
    return found


def _validate_evidence_references(
    payload: object,
    *,
    evidence_package: SavedEvidencePackageRead | None,
) -> None:
    if not isinstance(payload, dict):
        return
    section_availability = _section_availability(evidence_package)
    section_availability.update(_tool_result_section_availability(payload))
    public_events_source_key = _public_events_source_key(evidence_package)
    for section in payload.get("role_sections") or ():
        _validate_role_reference_section(
            section,
            section_availability=section_availability,
            public_events_source_key=public_events_source_key,
        )
    for section in payload.get("role_summaries") or ():
        _validate_role_reference_section(
            section,
            section_availability=section_availability,
            public_events_source_key=public_events_source_key,
        )
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
    public_events_source_key: str | None,
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
        role_name=role_name,
        public_events_source_key=public_events_source_key,
    )


def _validate_reference_set(
    references: Any,
    *,
    allowed: frozenset[str],
    section_availability: dict[str, str],
    role_name: str | None = None,
    public_events_source_key: str | None = None,
) -> None:
    for reference in references:
        ref = str(reference)
        if ref not in CANONICAL_EVIDENCE_KEYS or ref not in allowed:
            raise ValueError("agent-team report cites evidence outside the role boundary")
        if (
            ref == "public_events_calendar"
            and public_events_source_key == "sec_edgar_recent_filings"
            and role_name not in {"news_analyst", "portfolio_manager_agent", None}
        ):
            raise ValueError("SEC recent filing metadata is not citable by this role")
        availability = section_availability.get(ref)
        if availability is not None and availability not in {"available", "limited"}:
            raise ValueError("agent-team report cites unavailable evidence")


def _section_availability(evidence_package: SavedEvidencePackageRead | None) -> dict[str, str]:
    if evidence_package is None:
        return {}
    availability: dict[str, str] = {}
    _collect_section_availability(evidence_package.model_dump(mode="python"), availability)
    return availability


def _tool_result_section_availability(payload: dict[str, Any]) -> dict[str, str]:
    tool_run_artifact = payload.get("tool_run_artifact")
    if not isinstance(tool_run_artifact, dict):
        return {}
    availability: dict[str, str] = {}
    for result in tool_run_artifact.get("tool_results") or ():
        if not isinstance(result, dict):
            continue
        result_availability = result.get("availability")
        if result_availability not in {"available", "limited"}:
            continue
        for ref in result.get("evidence_refs") or ():
            if isinstance(ref, str):
                availability[ref] = result_availability
    return availability


def _public_events_source_key(evidence_package: SavedEvidencePackageRead | None) -> str | None:
    if evidence_package is None or evidence_package.public_evidence is None:
        return None
    return evidence_package.public_evidence.public_events_calendar.source_key


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
