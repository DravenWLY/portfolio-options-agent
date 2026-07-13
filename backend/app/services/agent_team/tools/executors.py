"""Tool execution + per-tool saved-evidence projections (P34A-T11D split).

Executes reviewed offline tools over the frozen ``SavedEvidencePackageRead``
and builds sanitized ``ToolResult`` envelopes. The privacy-tier boundary,
envelope contracts, and validators live in ``envelopes``; registry building
lives in ``registry``. No behavior change from the pre-split module.
"""

from datetime import datetime  # noqa: F401  (used by per-tool projections)

from app.schemas.reports import (
    SavedEvidencePackageRead,
    SavedEvidenceSectionRead,
    SavedPublicEvidenceSectionRead,
)
from app.services.agent_team.tools.envelopes import *  # noqa: F401,F403
from app.services.agent_team.tools.calculations import execute_calculation_tool
from app.services.agent_team.tools.registry import default_tool_registry
from app.services.market_data.eod_history import (
    FMP_EOD_CAVEAT_CODE,
    FMP_EOD_SOURCE_KEY,
    FMP_EOD_SOURCE_LABEL,
    FMP_EOD_UNAVAILABLE_CAVEAT_CODE,
    FmpEodHistoryError,
    MarketContextExecutionContext,
    get_market_context_snapshot,
)

__all__ = [
    "execute_tool_request",
    "blocked_tool_result",
    "unavailable_tool_result",
    "timeout_tool_result",
    "budget_exceeded_tool_result",
    "tool_result_for_disallowed_role",
]


def execute_tool_request(
    request: ToolRequest,
    *,
    evidence: SavedEvidencePackageRead,
    registry: dict[str, ToolRegistryEntry] | None = None,
    market_context: MarketContextExecutionContext | None = None,
) -> ToolResult:
    """Execute one reviewed offline tool over the provided frozen saved evidence package."""

    active_registry = registry or default_tool_registry()
    entry = active_registry.get(request.tool_name)
    if entry is None:
        return _request_blocked_result(
            tool_name=request.tool_name,
            role_name=request.requesting_role,
            reason="Requested tool is not in the reviewed allowlist.",
        )
    if not entry.allows_role(request.requesting_role):
        return _request_blocked_result(
            tool_name=entry.tool_name,
            role_name=request.requesting_role,
            reason="Requesting role is not allowed to receive this tool tier.",
        )
    if entry.evidence_tier == "agent_safe" and request.requesting_role in PUBLIC_ANALYST_ROLES:
        return _request_blocked_result(
            tool_name=entry.tool_name,
            role_name=request.requesting_role,
            reason="Public roles cannot receive portfolio-aware evidence.",
        )
    if entry.tool_name in P36_CALC_TOOL_NAMES:
        return execute_calculation_tool(request=request, evidence=evidence, entry=entry)

    builders = {
        "trade_intent_summary": _tool_trade_intent_summary,
        "portfolio_scope_context": _tool_portfolio_scope_context,
        "deterministic_review_findings": _tool_deterministic_review_findings,
        "broker_snapshot_freshness": _tool_broker_snapshot_freshness,
        "market_quote_freshness": _tool_market_quote_freshness,
        "market_context_snapshot": _tool_market_context_snapshot,
        "public_company_profile": _tool_public_company_profile,
        "economic_awareness_context": _tool_economic_awareness_context,
        "sec_recent_filings_metadata": _tool_sec_recent_filings_metadata,
        "evidence_gap_inspector": _tool_evidence_gap_inspector,
    }
    if entry.tool_name == "market_context_snapshot":
        return _tool_market_context_snapshot(
            request=request,
            evidence=evidence,
            entry=entry,
            market_context=market_context,
        )
    return builders[entry.tool_name](request=request, evidence=evidence, entry=entry)


def _degraded_result(
    *,
    tool_name: str,
    role_name: AgentTeamRole,
    evidence_tier: str,
    status: str,
    source_key: str = "tool_policy",
    source_label: str = "Tool policy",
    summary_payload: dict[str, object] | None = None,
) -> ToolResult:
    if status not in TOOL_DEGRADED_STATUSES:
        raise ValueError(f"not a degraded status: {status}")
    # Enforce the role <-> tier boundary up front (also enforced by ToolResult),
    # so a public role can never produce an agent-safe/private degraded result.
    assert_role_tier_allowed(evidence_tier, role_name)
    return ToolResult(
        tool_name=tool_name,
        role_name=role_name,
        status=status,
        evidence_tier=evidence_tier,
        data_mode="synthetic",
        source_key=source_key,
        source_label=source_label,
        availability="not_available",
        evidence_refs=(),
        summary_payload=summary_payload or {},
        payload={},
        provenance="degraded_no_data",
        freshness=None,
        latency_ms=0,
        estimated_cost="0",
        is_mock=True,
    )


def _request_blocked_result(*, tool_name: str, role_name: AgentTeamRole, reason: str) -> ToolResult:
    """Return a public/synthetic blocked result for a rejected request.

    This avoids constructing an ``agent_safe`` artifact for public roles while
    still giving the runner an honest ToolResult envelope.
    """

    return ToolResult(
        tool_name=tool_name,
        role_name=role_name,
        status="blocked",
        evidence_tier="public",
        data_mode="synthetic",
        source_key="tool_policy",
        source_label="Tool policy",
        availability="not_available",
        summary_payload={"summary": reason},
        provenance="degraded_no_data",
        is_mock=True,
    )


def _tool_trade_intent_summary(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    summary = evidence.trade_intent_summary
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_trade_intent_summary",
        source_label="Saved trade intent summary",
        availability="available",
        evidence_refs=("trade_intent_summary",),
        summary_payload={
            "supported_flow": summary.supported_flow,
            "review_flow_label": summary.review_flow_label,
            "symbol_or_underlying": summary.symbol_or_underlying,
        },
    )


def _tool_portfolio_scope_context(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    scope = evidence.scope_state
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_scope_state",
        source_label="Saved portfolio scope context",
        availability="available",
        evidence_refs=("scope_state",),
        caveat_codes=scope.scope_caveat_codes,
        scope={
            "portfolio_scope_mode": scope.portfolio_scope_mode,
            "portfolio_selection_mode": scope.portfolio_selection_mode,
        },
        summary_payload={
            "review_account_selected": scope.review_account_selected,
            "review_account_included_in_portfolio_scope": scope.review_account_included_in_portfolio_scope,
            "review_account_is_feasibility_source": scope.review_account_is_feasibility_source,
            "account_level_feasibility_evaluated": scope.account_level_feasibility_evaluated,
        },
    )


def _tool_deterministic_review_findings(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    actionability = evidence.actionability
    citable_refs = ["actionability"]
    for section in (
        evidence.portfolio_impact_summary,
        evidence.before_after_portfolio_impact,
        evidence.concentration_risk_drift,
        evidence.cash_collateral_caveats,
        evidence.options_exposure_summary,
    ):
        if section.availability in {"available", "limited"}:
            citable_refs.append(section.section_key)
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_deterministic_review",
        source_label="Saved deterministic review findings",
        availability="limited",
        evidence_refs=tuple(dict.fromkeys(citable_refs)),
        caveat_codes=evidence.caveat_codes,
        summary_payload={
            "review_actionability_status": actionability.review_actionability_status,
            "actionability_label": actionability.actionability_label,
            "highest_severity": actionability.highest_severity,
            "report_status": actionability.report_status,
            "portfolio_impact_availability": evidence.portfolio_impact_summary.availability,
            "liquidity_collateral_availability": evidence.cash_collateral_caveats.availability,
            "options_exposure_availability": evidence.options_exposure_summary.availability,
        },
    )


def _tool_broker_snapshot_freshness(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    label = evidence.freshness.broker_snapshot_freshness_label
    return _section_result(
        request=request,
        entry=entry,
        section_key="freshness",
        source_key="saved_broker_snapshot_freshness",
        source_label="Saved broker snapshot freshness",
        availability="available" if label else "not_available",
        freshness=label,
        summary_payload={
            "freshness_label": label,
            "summary": (
                "Broker snapshot freshness label is available from saved evidence."
                if label
                else "Broker snapshot freshness label is not available in saved evidence."
            ),
        },
    )


def _tool_market_quote_freshness(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = evidence.market_quote_freshness
    return _section_result(
        request=request,
        entry=entry,
        section_key="market_quote_freshness",
        source_key="saved_market_quote_freshness",
        source_label="Saved market quote freshness",
        availability=section.availability,
        freshness=section.summary_label,
        caveat_codes=section.caveat_codes,
        summary_payload={
            "summary_label": section.summary_label,
            "section_label": section.section_label,
        },
    )


def _tool_market_context_snapshot(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
    market_context: MarketContextExecutionContext | None = None,
) -> ToolResult:
    symbol = _reviewed_symbol_or_underlying(evidence)
    if not symbol:
        return _fmp_eod_unavailable_result(
            request=request,
            entry=entry,
            summary="Reviewed symbol was unavailable in the frozen saved evidence package.",
        )
    try:
        snapshot = get_market_context_snapshot(symbol=symbol, context=market_context)
    except FmpEodHistoryError:
        return _fmp_eod_unavailable_result(
            request=request,
            entry=entry,
            summary="FMP end-of-day market context was unavailable or disabled for this report run.",
        )
    return _ok_result(
        request=request,
        entry=entry,
        source_key=FMP_EOD_SOURCE_KEY,
        source_label=FMP_EOD_SOURCE_LABEL,
        availability="limited" if "insufficient_history" in snapshot.caveat_codes else "available",
        freshness=snapshot.freshness_category,
        as_of=snapshot.as_of_datetime,
        evidence_refs=("public_market_context",),
        caveat_codes=snapshot.caveat_codes,
        summary_payload=snapshot.summary_payload(),
    )


def _tool_public_company_profile(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    if evidence.public_evidence is None:
        return _unavailable_saved_section_result(
            request=request,
            entry=entry,
            source_key="saved_public_company_profile",
            source_label="Saved public company profile",
            evidence_ref="public_company_profile",
            summary="Public company profile was not attached to this saved evidence package.",
        )
    section = evidence.public_evidence.public_company_profile
    if section.availability not in {"available", "limited"}:
        return _public_section_result(
            request=request,
            entry=entry,
            section=section,
            status="unavailable",
        )
    return _public_section_result(request=request, entry=entry, section=section, status="ok")


def _tool_economic_awareness_context(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = evidence.economic_awareness_snapshot
    if not _is_approved_fred_economic_awareness_section(section):
        return _section_result(
            request=request,
            entry=entry,
            section_key="economic_awareness_snapshot",
            source_key=FRED_ECONOMIC_AWARENESS_SOURCE_KEY,
            source_label=FRED_ECONOMIC_AWARENESS_SOURCE_LABEL,
            availability="not_available",
            freshness=None,
            caveat_codes=("fred_economic_awareness_not_available",),
            summary_payload={
                "summary": "Approved FRED economic awareness metadata was not attached to this saved evidence package.",
                "availability": section.availability,
            },
        )
    return _section_result(
        request=request,
        entry=entry,
        section_key="economic_awareness_snapshot",
        source_key=FRED_ECONOMIC_AWARENESS_SOURCE_KEY,
        source_label=FRED_ECONOMIC_AWARENESS_SOURCE_LABEL,
        availability=section.availability,
        freshness=section.summary_label,
        caveat_codes=tuple(dict.fromkeys((*section.caveat_codes, "fred_economic_awareness_context_only"))),
        summary_payload={
            "reviewed_release_event_labels": _safe_fred_release_event_labels(section),
            "reviewed_release_metadata": _safe_fred_release_metadata(section),
            "attribution": FRED_ECONOMIC_AWARENESS_ATTRIBUTION,
            "notice": FRED_ECONOMIC_AWARENESS_NOTICE,
            "caveat": FRED_ECONOMIC_AWARENESS_CAVEAT,
        },
    )


def _tool_sec_recent_filings_metadata(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    if evidence.public_evidence is None:
        return _unavailable_saved_section_result(
            request=request,
            entry=entry,
            source_key=SEC_RECENT_FILINGS_SOURCE_KEY,
            source_label=SEC_RECENT_FILINGS_SOURCE_LABEL,
            evidence_ref="public_events_calendar",
            summary="Approved SEC EDGAR recent filing metadata was not attached to this saved evidence package.",
        )
    section = evidence.public_evidence.public_events_calendar
    if not _is_approved_sec_recent_filings_section(section):
        return _public_events_unavailable_result(request=request, entry=entry, section=section)
    return _ok_result(
        request=request,
        entry=entry,
        source_key=SEC_RECENT_FILINGS_SOURCE_KEY,
        source_label=SEC_RECENT_FILINGS_SOURCE_LABEL,
        availability=section.availability,
        freshness=section.freshness_label,
        as_of=section.as_of,
        evidence_refs=("public_events_calendar",),
        caveat_codes=tuple(dict.fromkeys((*section.caveat_codes, "sec_edgar_recent_filings_metadata_only"))),
        summary_payload={
            "reviewed_filing_metadata": _safe_sec_filing_metadata(section),
            "attribution": SEC_RECENT_FILINGS_ATTRIBUTION,
            "caveat": SEC_RECENT_FILINGS_CAVEAT,
            "non_endorsement": SEC_RECENT_FILINGS_NON_ENDORSEMENT,
            "limitations": section.limitations,
        },
    )


def _tool_evidence_gap_inspector(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    unavailable = _unavailable_evidence_refs(evidence)
    return _ok_result(
        request=request,
        entry=entry,
        source_key="saved_evidence_gap_inspector",
        source_label="Saved evidence gap inspector",
        availability="limited" if unavailable else "available",
        evidence_refs=("trade_intent_summary", "scope_state"),
        caveat_codes=evidence.caveat_codes,
        summary_payload={
            "summary": (
                "Saved evidence has unavailable or unreviewed sections."
                if unavailable
                else "Saved evidence sections available to this tool have no unavailable gaps."
            ),
            "unavailable_evidence_refs": unavailable,
        },
    )


def _is_approved_fred_economic_awareness_section(section: SavedEvidenceSectionRead) -> bool:
    if section.section_key != "economic_awareness_snapshot":
        return False
    if section.availability not in {"available", "limited"}:
        return False
    caveat_tokens = {code.lower() for code in section.caveat_codes}
    return bool(FRED_ECONOMIC_AWARENESS_APPROVAL_CODES.intersection(caveat_tokens))


def _safe_fred_release_event_labels(section: SavedEvidenceSectionRead) -> tuple[str, ...]:
    labels: list[str] = []
    for raw_label in section.detail_labels:
        label = str(raw_label).strip()
        if not label or _fred_label_has_forbidden_fact_key(label):
            continue
        parsed = _parse_fred_fact_label(label)
        if parsed is not None:
            fact_key, value_label = parsed
            if fact_key in {"release_name", "event_name"} and _fred_fact_value_is_safe(fact_key, value_label):
                labels.append(value_label)
            continue
        labels.append(label)
    return tuple(dict.fromkeys(labels))


def _safe_fred_release_metadata(section: SavedEvidenceSectionRead) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for raw_label in section.detail_labels:
        parsed = _parse_fred_fact_label(str(raw_label))
        if parsed is None:
            continue
        fact_key, value_label = parsed
        if fact_key not in FRED_ECONOMIC_AWARENESS_FACT_KEYS:
            continue
        if not _fred_fact_value_is_safe(fact_key, value_label):
            continue
        rows.append(
            {
                "fact_key": fact_key,
                "fact_label": fact_key.replace("_", " ").title(),
                "value_label": value_label,
            }
        )
    return tuple(rows)


def _parse_fred_fact_label(label: str) -> tuple[str, str] | None:
    for separator in (":", "="):
        if separator not in label:
            continue
        key, value = label.split(separator, 1)
        fact_key = key.strip().lower().replace(" ", "_").replace("-", "_")
        value_label = value.strip()
        if not fact_key or not value_label or _fred_fact_key_is_forbidden(fact_key):
            return None
        return fact_key, value_label
    return None


def _fred_label_has_forbidden_fact_key(label: str) -> bool:
    parsed = _parse_fred_fact_label(label)
    if parsed is None:
        lowered = label.lower()
        return any(token in lowered for token in FRED_ECONOMIC_AWARENESS_FORBIDDEN_FACT_KEYS)
    return _fred_fact_key_is_forbidden(parsed[0])


def _fred_fact_key_is_forbidden(fact_key: str) -> bool:
    lowered = fact_key.lower()
    return lowered in FRED_ECONOMIC_AWARENESS_FORBIDDEN_FACT_KEYS or any(
        token in lowered for token in FRED_ECONOMIC_AWARENESS_FORBIDDEN_FACT_KEYS
    )


def _fred_fact_value_is_safe(fact_key: str, value_label: str) -> bool:
    lowered = value_label.lower()
    if any(token in lowered for token in FRED_ECONOMIC_AWARENESS_FORBIDDEN_VALUE_TOKENS):
        return False
    if fact_key in {"release_date", "event_date"}:
        return FRED_ECONOMIC_AWARENESS_DATE_RE.fullmatch(value_label.strip()) is not None
    if fact_key in {"release_name", "event_name"}:
        return FRED_ECONOMIC_AWARENESS_NAME_RE.fullmatch(value_label.strip()) is not None
    return False


def _is_approved_sec_recent_filings_section(section: SavedPublicEvidenceSectionRead) -> bool:
    return (
        section.section_key == "public_events_calendar"
        and section.source_key == SEC_RECENT_FILINGS_SOURCE_KEY
        and section.availability in {"available", "limited"}
    )


def _public_events_unavailable_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section: SavedPublicEvidenceSectionRead,
) -> ToolResult:
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status="unavailable",
        evidence_tier=entry.evidence_tier,
        data_mode="public",
        source_key=SEC_RECENT_FILINGS_SOURCE_KEY,
        source_label=SEC_RECENT_FILINGS_SOURCE_LABEL,
        availability="not_available",
        caveat_codes=("sec_edgar_recent_filings_not_available",),
        evidence_refs=(),
        summary_payload={
            "summary": "Approved SEC EDGAR recent filing metadata was not attached to this saved evidence package.",
            "availability": section.availability,
        },
        provenance="saved_public_evidence",
        is_mock=entry.is_mock,
    )


def _fmp_eod_unavailable_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    summary: str,
) -> ToolResult:
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status="unavailable",
        evidence_tier=entry.evidence_tier,
        data_mode="public",
        source_key=FMP_EOD_SOURCE_KEY,
        source_label=FMP_EOD_SOURCE_LABEL,
        availability="not_available",
        caveat_codes=(FMP_EOD_UNAVAILABLE_CAVEAT_CODE,),
        evidence_refs=(),
        summary_payload={
            "summary": summary,
            "source_key": FMP_EOD_SOURCE_KEY,
            "source_label": FMP_EOD_SOURCE_LABEL,
        },
        provenance="provider_unavailable",
        is_mock=entry.is_mock,
    )


def _safe_sec_filing_metadata(section: SavedPublicEvidenceSectionRead) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for fact in section.facts:
        if fact.fact_key not in SEC_RECENT_FILINGS_FACT_KEYS or not fact.value_label:
            continue
        if _looks_like_raw_sec_path_or_file(fact.value_label):
            continue
        if fact.fact_key == "filing_reference" and not _is_safe_normalized_filing_reference(fact.value_label):
            continue
        rows.append(
            {
                "fact_key": fact.fact_key,
                "fact_label": fact.fact_label,
                "value_label": fact.value_label,
            }
        )
    return tuple(rows)


def _reviewed_symbol_or_underlying(evidence: SavedEvidencePackageRead) -> str | None:
    symbol = (evidence.trade_intent_summary.symbol_or_underlying or "").strip().upper()
    return symbol or None


def _is_safe_normalized_filing_reference(value: str) -> bool:
    return SEC_NORMALIZED_FILING_REFERENCE_RE.fullmatch(value.strip()) is not None


def _looks_like_raw_sec_path_or_file(value: str) -> bool:
    return SEC_RAW_PATH_OR_FILE_RE.search(value.strip()) is not None


def _ok_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    source_key: str,
    source_label: str,
    availability: str,
    evidence_refs: tuple[str, ...],
    summary_payload: dict[str, object],
    caveat_codes: tuple[str, ...] = (),
    freshness: str | None = None,
    as_of: datetime | None = None,
    scope: dict[str, object] | None = None,
) -> ToolResult:
    citable_refs = evidence_refs if availability in {"available", "limited"} else ()
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status="ok" if availability in {"available", "limited"} else "unavailable",
        evidence_tier=entry.evidence_tier,
        data_mode="public" if entry.evidence_tier == "public" else "agent_safe",
        source_key=source_key,
        source_label=source_label,
        availability=availability,
        freshness=freshness,
        as_of=as_of,
        scope=scope or {},
        caveat_codes=caveat_codes,
        evidence_refs=citable_refs,
        summary_payload=summary_payload,
        provenance="saved_evidence_package",
        is_mock=entry.is_mock,
    )


def _section_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section_key: str,
    source_key: str,
    source_label: str,
    availability: str,
    summary_payload: dict[str, object],
    freshness: str | None = None,
    caveat_codes: tuple[str, ...] = (),
) -> ToolResult:
    return _ok_result(
        request=request,
        entry=entry,
        source_key=source_key,
        source_label=source_label,
        availability=availability,
        freshness=freshness,
        evidence_refs=(section_key,),
        caveat_codes=caveat_codes,
        summary_payload=summary_payload,
    )


def _public_section_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section: SavedPublicEvidenceSectionRead,
    status: str,
) -> ToolResult:
    citable_refs = (section.section_key,) if section.availability in {"available", "limited"} else ()
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status=status,
        evidence_tier=entry.evidence_tier,
        data_mode="public",
        source_key=section.source_key or "saved_public_evidence",
        source_label=section.source_label,
        availability=section.availability,
        freshness=section.freshness_label,
        as_of=section.as_of,
        caveat_codes=section.caveat_codes,
        evidence_refs=citable_refs,
        summary_payload={
            "section_key": section.section_key,
            "section_label": section.section_label,
            "summary_label": section.summary_label,
            "fact_keys_present": tuple(fact.fact_key for fact in section.facts),
            "rights_status": section.rights_status,
        },
        provenance="saved_public_evidence",
        is_mock=entry.is_mock,
    )


def _unavailable_saved_section_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    source_key: str,
    source_label: str,
    evidence_ref: str,
    summary: str,
) -> ToolResult:
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status="unavailable",
        evidence_tier=entry.evidence_tier,
        data_mode="public" if entry.evidence_tier == "public" else "agent_safe",
        source_key=source_key,
        source_label=source_label,
        availability="not_available",
        evidence_refs=(),
        summary_payload={"summary": summary},
        provenance="saved_evidence_package",
        is_mock=entry.is_mock,
    )


def _unavailable_evidence_refs(evidence: SavedEvidencePackageRead) -> tuple[str, ...]:
    unavailable: list[str] = []
    sections: tuple[SavedEvidenceSectionRead, ...] = (
        evidence.portfolio_impact_summary,
        evidence.before_after_portfolio_impact,
        evidence.concentration_risk_drift,
        evidence.cash_collateral_caveats,
        evidence.options_exposure_summary,
        evidence.market_quote_freshness,
        evidence.economic_awareness_snapshot,
        evidence.market_mood_snapshot,
    )
    for section in sections:
        if section.availability not in {"available", "limited"}:
            unavailable.append(section.section_key)
    if evidence.public_evidence is not None:
        for section in (
            evidence.public_evidence.public_company_profile,
            evidence.public_evidence.public_fundamentals_snapshot,
            evidence.public_evidence.public_news_snapshot,
            evidence.public_evidence.public_events_calendar,
            evidence.public_evidence.public_technical_context,
            evidence.public_evidence.public_market_context,
        ):
            if section.availability not in {"available", "limited"}:
                unavailable.append(section.section_key)
    return tuple(dict.fromkeys(unavailable))


def blocked_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    """Conceptual degrade-to-blocked (e.g. role not allowlisted). No execution."""

    return _degraded_result(tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="blocked")


def unavailable_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    return _degraded_result(tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="unavailable")


def timeout_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    return _degraded_result(tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="timeout")


def budget_exceeded_tool_result(*, tool_name: str, role_name: AgentTeamRole, evidence_tier: str) -> ToolResult:
    return _degraded_result(
        tool_name=tool_name, role_name=role_name, evidence_tier=evidence_tier, status="budget_exceeded"
    )


def tool_result_for_disallowed_role(entry: ToolRegistryEntry, role_name: AgentTeamRole) -> ToolResult:
    """Return a safe ``blocked`` result when a role is not allowlisted. No execution."""

    if entry.allows_role(role_name):
        raise ValueError("role is allowed; no blocked result needed")
    return blocked_tool_result(
        tool_name=entry.tool_name, role_name=role_name, evidence_tier=entry.evidence_tier
    )
