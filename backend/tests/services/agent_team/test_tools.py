from datetime import UTC, datetime

import pytest

from app.schemas.reports import (
    SavedEvidenceActionabilityRead,
    SavedEvidenceFreshnessRead,
    SavedEvidencePackageRead,
    SavedEvidenceScopeStateRead,
    SavedEvidenceSectionRead,
    SavedEvidenceSourceSnapshotRead,
    SavedEvidenceTradeIntentSummaryRead,
    SavedPublicEvidenceFactRead,
    SavedPublicEvidencePackageRead,
    SavedPublicEvidenceSectionRead,
)
from app.services.agent_team.tools import (
    ToolAuditRecord,
    ToolRequest,
    ToolRegistryEntry,
    ToolResult,
    assert_tool_tier_allowed,
    blocked_tool_result,
    budget_exceeded_tool_result,
    build_tool_registry,
    default_tool_registry,
    execute_tool_request,
    is_tool_allowed_for_role,
    timeout_tool_result,
    tool_audit_record_field_names,
    tool_result_for_disallowed_role,
    unavailable_tool_result,
)


pytestmark = [pytest.mark.unit]


def _public_entry(**overrides) -> ToolRegistryEntry:
    payload = dict(
        tool_name="public_company_overview",
        display_name="Public Company Overview",
        evidence_tier="public",
        role_allowlist=("fundamentals_analyst", "news_analyst"),
    )
    payload.update(overrides)
    return ToolRegistryEntry(**payload)


def _section(
    section_key: str,
    *,
    availability: str = "available",
    summary_label: str = "Saved evidence section available.",
    caveat_codes: tuple[str, ...] = (),
) -> SavedEvidenceSectionRead:
    return SavedEvidenceSectionRead(
        section_key=section_key,
        section_label=section_key.replace("_", " ").title(),
        availability=availability,
        summary_label=summary_label,
        caveat_codes=caveat_codes,
    )


def _not_reviewed_public_section(section_key: str) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key=section_key,
        section_label=section_key.replace("_", " ").title(),
        availability="not_reviewed",
        freshness_category="not_reviewed",
        freshness_label="Not reviewed",
        source_label="No reviewed public source attached",
        rights_status="not_reviewed",
        summary_label="No reviewed public evidence attached.",
        limitations=("Public source was not reviewed for this saved evidence package.",),
    )


def _public_company_profile_section(
    *,
    availability: str = "available",
) -> SavedPublicEvidenceSectionRead:
    is_citable = availability in {"available", "limited"}
    return SavedPublicEvidenceSectionRead(
        section_key="public_company_profile",
        section_label="Public Company Profile",
        availability=availability,
        freshness_category="fresh" if is_citable else "not_available",
        freshness_label=(
            "Saved source metadata timestamp available"
            if is_citable
            else "Saved source metadata was not available"
        ),
        source_label="SEC EDGAR metadata - company profile only",
        source_key="sec_edgar_submissions" if is_citable else None,
        rights_status="internal_demo_only" if is_citable else "not_reviewed",
        as_of=datetime(2026, 6, 1, tzinfo=UTC) if is_citable else None,
        collected_at=datetime(2026, 6, 1, 12, tzinfo=UTC) if is_citable else None,
        summary_label=(
            "Company identity metadata is available."
            if is_citable
            else "Public company profile is not available."
        ),
        facts=(
            SavedPublicEvidenceFactRead(fact_key="company_name", fact_label="Company name", value_label="Example Co"),
            SavedPublicEvidenceFactRead(fact_key="ticker", fact_label="Ticker", value_label="XYZ"),
            SavedPublicEvidenceFactRead(
                fact_key="sic_label",
                fact_label="SEC SIC label",
                value_label="Source-specific regulatory classification",
            ),
        )
        if is_citable
        else (),
        limitations=("SEC classification metadata may be broad, legacy, or lag company changes.",),
        caveat_codes=("sec_sic_source_specific",) if is_citable else (),
    )


def _evidence_package(
    *,
    public_company_profile: SavedPublicEvidenceSectionRead | None = None,
    public_events_calendar: SavedPublicEvidenceSectionRead | None = None,
    economic_awareness_snapshot: SavedEvidenceSectionRead | None = None,
) -> SavedEvidencePackageRead:
    caveat_codes = ("selected_context_scope", "account_level_feasibility_not_evaluated")
    public_section = public_company_profile or _public_company_profile_section()
    return SavedEvidencePackageRead(
        source_snapshot=SavedEvidenceSourceSnapshotRead(
            source_kind="trade_review_workspace",
            source_reference="trrev_tooldemo1",
            artifact_reference="svrev_tooldemo1",
            generated_at=datetime(2026, 6, 1, 10, tzinfo=UTC),
            saved_at=datetime(2026, 6, 1, 10, 5, tzinfo=UTC),
        ),
        trade_intent_summary=SavedEvidenceTradeIntentSummaryRead(
            supported_flow="cash_secured_put",
            review_flow_label="Cash-secured put",
            symbol_or_underlying="XYZ",
        ),
        scope_state=SavedEvidenceScopeStateRead(
            review_account_selected=True,
            review_account_included_in_portfolio_scope=True,
            review_account_is_feasibility_source=False,
            account_level_feasibility_evaluated=False,
            portfolio_scope_mode="selected_context",
            portfolio_selection_mode="latest_available",
            scope_caveat_codes=caveat_codes,
        ),
        account_readiness=_section(
            "account_readiness",
            summary_label="Account-level feasibility was not evaluated in the saved review scope.",
            caveat_codes=caveat_codes,
        ),
        freshness=SavedEvidenceFreshnessRead(
            broker_snapshot_freshness_label="Broker snapshot freshness label saved",
            market_quote_freshness_label="Market quote freshness label saved",
        ),
        actionability=SavedEvidenceActionabilityRead(
            review_actionability_status="analysis_only",
            actionability_label="Analysis-only review",
            highest_severity="warning",
            report_status="generated",
        ),
        portfolio_impact_summary=_section(
            "portfolio_impact_summary",
            availability="limited",
            summary_label="Saved deterministic portfolio-impact caveats are available.",
            caveat_codes=caveat_codes,
        ),
        before_after_portfolio_impact=_section(
            "before_after_portfolio_impact",
            availability="not_available",
            summary_label="Before/after details were not included in this saved source.",
        ),
        concentration_risk_drift=_section(
            "concentration_risk_drift",
            availability="limited",
            summary_label="Highest deterministic severity is warning.",
            caveat_codes=caveat_codes,
        ),
        cash_collateral_caveats=_section(
            "liquidity_collateral_caveats",
            availability="limited",
            summary_label="Liquidity and collateral model caveats are available without raw private amounts.",
            caveat_codes=caveat_codes,
        ),
        options_exposure_summary=_section(
            "options_exposure_summary",
            availability="limited",
            summary_label="Options feasibility caveats are available as reviewed saved-source labels.",
            caveat_codes=caveat_codes,
        ),
        market_quote_freshness=_section(
            "market_quote_freshness",
            availability="available",
            summary_label="Market quote freshness label saved",
        ),
        economic_awareness_snapshot=economic_awareness_snapshot
        or _section(
            "economic_awareness_snapshot",
            availability="not_reviewed",
            summary_label="Economic awareness was not included in this saved source.",
        ),
        market_mood_snapshot=_section(
            "market_mood_snapshot",
            availability="not_reviewed",
            summary_label="Market Mood was not included in this saved source.",
        ),
        public_evidence=SavedPublicEvidencePackageRead(
            public_evidence_mode="provider_reference",
            symbol_or_underlying="XYZ",
            public_company_profile=public_section,
            public_fundamentals_snapshot=_not_reviewed_public_section("public_fundamentals_snapshot"),
            public_news_snapshot=_not_reviewed_public_section("public_news_snapshot"),
            public_events_calendar=public_events_calendar or _not_reviewed_public_section("public_events_calendar"),
            public_technical_context=_not_reviewed_public_section("public_technical_context"),
            public_market_context=_not_reviewed_public_section("public_market_context"),
            limitations=("Only reviewed normalized public evidence sections are attached.",),
        ),
        caveat_codes=caveat_codes,
        limitations=("Saved evidence generated from reviewed deterministic data.",),
    )


def _fred_economic_awareness_section(*, availability: str = "available") -> SavedEvidenceSectionRead:
    return _section(
        "economic_awareness_snapshot",
        availability=availability,
        summary_label="FRED macro release calendar metadata is available as economic context only.",
        caveat_codes=("fred_macro_calendar_metadata",),
    ).model_copy(
        update={
            "detail_labels": (
                "release_name: Consumer Price Index release",
                "release_date: 2026-07-15",
                "event_name: Federal Open Market Committee calendar",
                "event_date: 2026-07-29",
            )
        }
    )


def _sec_recent_filings_section(*, availability: str = "available") -> SavedPublicEvidenceSectionRead:
    is_citable = availability in {"available", "limited"}
    return SavedPublicEvidenceSectionRead(
        section_key="public_events_calendar",
        section_label="Public events calendar",
        availability=availability,
        freshness_category="fresh" if is_citable else "not_available",
        freshness_label="Recent filing metadata collection timestamp available" if is_citable else "Not available",
        source_label="SEC EDGAR recent filing metadata - company events only",
        source_key="sec_edgar_recent_filings" if is_citable else None,
        rights_status="internal_demo_only" if is_citable else "not_reviewed",
        as_of=datetime(2026, 6, 1, tzinfo=UTC) if is_citable else None,
        collected_at=datetime(2026, 6, 1, 12, tzinfo=UTC) if is_citable else None,
        summary_label=(
            "SEC EDGAR recent filing metadata is available as company-event context only."
            if is_citable
            else "SEC EDGAR recent filing metadata was not available."
        ),
        facts=(
            SavedPublicEvidenceFactRead(fact_key="form_type", fact_label="Form type", value_label="Form 8-K"),
            SavedPublicEvidenceFactRead(
                fact_key="filing_date",
                fact_label="Filing date",
                value_label="Filed 2026-05-29",
            ),
            SavedPublicEvidenceFactRead(
                fact_key="filing_reference",
                fact_label="Normalized filing reference",
                value_label="filref_recent_event_001",
            ),
        )
        if is_citable
        else (),
        limitations=(
            "Recent filing metadata is company-event context only; filing contents are not interpreted.",
        ),
        caveat_codes=("sec_edgar_recent_filings_metadata",) if is_citable else (),
    )


def _stock_etf_evidence_package() -> SavedEvidencePackageRead:
    evidence = _evidence_package()
    return evidence.model_copy(
        update={
            "trade_intent_summary": SavedEvidenceTradeIntentSummaryRead(
                supported_flow="stock_or_etf",
                review_flow_label="Stock or ETF review",
                symbol_or_underlying="XYZ",
            ),
            "options_exposure_summary": _section(
                "options_exposure_summary",
                availability="not_available",
                summary_label="Options exposure summary was not part of this saved stock or ETF review.",
            ),
        }
    )


# -- registry entry governance ----------------------------------------------


def test_public_tool_entry_constructs() -> None:
    entry = _public_entry()
    assert entry.evidence_tier == "public"
    assert entry.is_mock is True
    assert entry.allows_role("fundamentals_analyst")
    assert not entry.allows_role("risk_management_agent")


def test_agent_safe_tool_entry_allows_only_portfolio_roles() -> None:
    entry = ToolRegistryEntry(
        tool_name="agent_safe_risk_lookup",
        display_name="Agent-safe Risk Lookup",
        evidence_tier="agent_safe",
        role_allowlist=("risk_management_agent", "portfolio_manager_agent"),
    )
    assert entry.evidence_tier == "agent_safe"


def test_private_tier_tool_is_prohibited() -> None:
    with pytest.raises(ValueError):
        _public_entry(evidence_tier="private_forbidden")


def test_agent_safe_tool_rejects_public_role_in_allowlist() -> None:
    with pytest.raises(ValueError):
        ToolRegistryEntry(
            tool_name="leaky_tool",
            display_name="Leaky",
            evidence_tier="agent_safe",
            role_allowlist=("fundamentals_analyst",),
        )


def test_entry_rejects_unknown_role() -> None:
    with pytest.raises(ValueError):
        _public_entry(role_allowlist=("not_a_role",))


def test_entry_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError):
        _public_entry(mode="async")


def test_entry_rejects_unknown_tier() -> None:
    with pytest.raises(ValueError):
        _public_entry(evidence_tier="totally_unknown")


def test_build_registry_rejects_duplicate_tool_names() -> None:
    with pytest.raises(ValueError):
        build_tool_registry((_public_entry(), _public_entry()))


def test_is_tool_allowed_for_role() -> None:
    entry = _public_entry()
    assert is_tool_allowed_for_role(entry, "fundamentals_analyst") is True
    assert is_tool_allowed_for_role(entry, "portfolio_manager_agent") is False


# -- tool result envelope ----------------------------------------------------


def _result(**overrides) -> ToolResult:
    payload = dict(
        tool_name="public_company_overview",
        role_name="fundamentals_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="synthetic",
        payload={"headline": "Synthetic public company overview."},
        provenance="synthetic",
    )
    payload.update(overrides)
    return ToolResult(**payload)


def test_tool_result_constructs() -> None:
    result = _result()
    assert result.status == "ok"
    assert result.evidence_tier == "public"


def test_tool_result_rejects_private_tier() -> None:
    with pytest.raises(ValueError):
        _result(evidence_tier="private_forbidden")


def test_tool_result_rejects_forbidden_private_key_in_payload() -> None:
    with pytest.raises(ValueError):
        _result(payload={"cash_balance": "1000.00"})


def test_tool_result_rejects_invented_metric_in_payload() -> None:
    with pytest.raises(ValueError):
        _result(payload={"headline": "Price target $250.00 and 30% upside."})


def test_tool_result_rejects_prohibited_wording_in_payload() -> None:
    with pytest.raises(ValueError):
        _result(payload={"headline": "you should buy this name now"})


# -- audit record ------------------------------------------------------------


def test_audit_record_has_no_payload_or_input_fields() -> None:
    names = tool_audit_record_field_names()
    assert "payload" not in names
    assert "inputs" not in names
    assert "outputs" not in names
    assert set(names) == {
        "run_reference",
        "tool_name",
        "role_name",
        "status",
        "evidence_tier",
        "latency_ms",
        "estimated_cost",
        "is_mock",
    }


def test_audit_record_constructs_safe() -> None:
    record = ToolAuditRecord(
        run_reference="agent-review-rev_demo",
        tool_name="public_company_overview",
        role_name="fundamentals_analyst",
        status="ok",
        evidence_tier="public",
        latency_ms=4,
    )
    assert record.status == "ok"


def test_audit_record_rejects_private_value_token() -> None:
    with pytest.raises(ValueError):
        ToolAuditRecord(
            run_reference="account_id_should_not_be_here",
            tool_name="public_company_overview",
            role_name="fundamentals_analyst",
            status="ok",
            evidence_tier="public",
        )


# -- degraded states ---------------------------------------------------------


@pytest.mark.parametrize(
    ("builder", "expected_status"),
    (
        (blocked_tool_result, "blocked"),
        (unavailable_tool_result, "unavailable"),
        (timeout_tool_result, "timeout"),
        (budget_exceeded_tool_result, "budget_exceeded"),
    ),
)
def test_degraded_result_builders(builder, expected_status: str) -> None:
    result = builder(
        tool_name="public_company_overview",
        role_name="news_analyst",
        evidence_tier="public",
    )
    assert result.status == expected_status
    assert result.payload == {}
    assert result.is_mock is True


def test_tool_result_for_disallowed_role_blocks() -> None:
    entry = _public_entry()
    result = tool_result_for_disallowed_role(entry, "portfolio_manager_agent")
    assert result.status == "blocked"
    assert result.payload == {}


def test_assert_tool_tier_allowed_rejects_private() -> None:
    assert_tool_tier_allowed("public")
    assert_tool_tier_allowed("agent_safe")
    with pytest.raises(ValueError):
        assert_tool_tier_allowed("private_forbidden")


# -- role <-> tier boundary enforcement (Codex B blocker fix) ----------------


def test_tool_result_rejects_agent_safe_for_public_role() -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="agent_safe_risk_lookup",
            role_name="fundamentals_analyst",
            status="ok",
            evidence_tier="agent_safe",
            data_mode="synthetic",
            payload={"summary": "sanitized risk evidence reference"},
        )


def test_tool_result_rejects_agent_safe_data_mode_for_public_role() -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="public_company_overview",
            role_name="news_analyst",
            status="ok",
            evidence_tier="public",
            data_mode="agent_safe",
            payload={},
        )


def test_audit_record_rejects_agent_safe_for_public_role() -> None:
    with pytest.raises(ValueError):
        ToolAuditRecord(
            run_reference="agent-review-rev_demo",
            tool_name="agent_safe_risk_lookup",
            role_name="technical_analyst",
            status="ok",
            evidence_tier="agent_safe",
        )


@pytest.mark.parametrize("builder", (blocked_tool_result, unavailable_tool_result))
def test_degraded_helpers_reject_agent_safe_for_public_role(builder) -> None:
    with pytest.raises(ValueError):
        builder(
            tool_name="agent_safe_risk_lookup",
            role_name="fundamentals_analyst",
            evidence_tier="agent_safe",
        )


def test_agent_safe_result_and_audit_allow_portfolio_roles() -> None:
    result = ToolResult(
        tool_name="agent_safe_risk_lookup",
        role_name="risk_management_agent",
        status="ok",
        evidence_tier="agent_safe",
        data_mode="agent_safe",
        payload={"summary": "sanitized deterministic risk evidence reference"},
    )
    assert result.evidence_tier == "agent_safe"

    record = ToolAuditRecord(
        run_reference="agent-review-rev_demo",
        tool_name="agent_safe_risk_lookup",
        role_name="portfolio_manager_agent",
        status="ok",
        evidence_tier="agent_safe",
    )
    assert record.evidence_tier == "agent_safe"

    degraded = blocked_tool_result(
        tool_name="agent_safe_risk_lookup",
        role_name="risk_management_agent",
        evidence_tier="agent_safe",
    )
    assert degraded.status == "blocked"


@pytest.mark.parametrize("role_name", ("fundamentals_analyst", "portfolio_manager_agent"))
def test_public_tier_allows_public_and_portfolio_roles(role_name: str) -> None:
    result = ToolResult(
        tool_name="public_company_overview",
        role_name=role_name,
        status="ok",
        evidence_tier="public",
        data_mode="synthetic",
        payload={"headline": "synthetic public overview"},
    )
    assert result.evidence_tier == "public"

    record = ToolAuditRecord(
        run_reference="agent-review-rev_demo",
        tool_name="public_company_overview",
        role_name=role_name,
        status="ok",
        evidence_tier="public",
    )
    assert record.evidence_tier == "public"


@pytest.mark.parametrize("role_name", ("fundamentals_analyst", "risk_management_agent"))
def test_private_tier_rejected_for_result_audit_and_degraded(role_name: str) -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="x",
            role_name=role_name,
            status="ok",
            evidence_tier="private_forbidden",
            data_mode="synthetic",
        )
    with pytest.raises(ValueError):
        ToolAuditRecord(
            run_reference="agent-review-rev_demo",
            tool_name="x",
            role_name=role_name,
            status="ok",
            evidence_tier="private_forbidden",
        )
    with pytest.raises(ValueError):
        blocked_tool_result(tool_name="x", role_name=role_name, evidence_tier="private_forbidden")


# -- P33A registry/request/result execution ---------------------------------


def test_default_tool_registry_contains_initial_p33a_allowlist() -> None:
    registry = default_tool_registry()

    assert set(registry) == {
        "trade_intent_summary",
        "portfolio_scope_context",
        "deterministic_review_findings",
        "broker_snapshot_freshness",
        "market_quote_freshness",
        "public_company_profile",
        "economic_awareness_context",
        "sec_recent_filings_metadata",
        "evidence_gap_inspector",
    }
    assert registry["trade_intent_summary"].evidence_tier == "public"
    assert registry["market_quote_freshness"].allows_role("technical_analyst")
    assert registry["economic_awareness_context"].evidence_tier == "public"
    assert registry["economic_awareness_context"].allows_role("news_analyst")
    assert registry["sec_recent_filings_metadata"].evidence_tier == "public"
    assert registry["sec_recent_filings_metadata"].allows_role("news_analyst")
    assert registry["sec_recent_filings_metadata"].allows_role("portfolio_manager_agent")
    assert not registry["sec_recent_filings_metadata"].allows_role("fundamentals_analyst")
    assert registry["portfolio_scope_context"].evidence_tier == "agent_safe"
    assert not registry["portfolio_scope_context"].allows_role("fundamentals_analyst")
    assert all(entry.mode == "sync" for entry in registry.values())
    assert all(entry.is_mock is False for entry in registry.values())


def test_tool_request_validates_safe_shape_and_refs() -> None:
    request = ToolRequest(
        tool_name="trade_intent_summary",
        requesting_role="fundamentals_analyst",
        saved_source_reference="trrev_tooldemo1",
        saved_artifact_reference="svrev_tooldemo1",
        args={"symbol_or_underlying": "XYZ", "section_key": "trade_intent_summary"},
        reason_code="role_context",
    )

    assert request.tool_name == "trade_intent_summary"


@pytest.mark.parametrize(
    "bad_args",
    (
        {"provider_account_id": "provider_account_id_secret"},
        {"section_key": "buying_power"},
        {"scope_category": "raw_payload"},
    ),
)
def test_tool_request_rejects_forbidden_args(bad_args: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        ToolRequest(
            tool_name="trade_intent_summary",
            requesting_role="fundamentals_analyst",
            args=bad_args,
        )


@pytest.mark.parametrize(
    ("tool_name", "role_name", "expected_tier", "expected_refs"),
    (
        ("trade_intent_summary", "fundamentals_analyst", "public", ("trade_intent_summary",)),
        ("portfolio_scope_context", "risk_management_agent", "agent_safe", ("scope_state",)),
        (
            "deterministic_review_findings",
            "portfolio_manager_agent",
            "agent_safe",
            ("actionability", "portfolio_impact_summary"),
        ),
        ("broker_snapshot_freshness", "risk_management_agent", "agent_safe", ("freshness",)),
        ("market_quote_freshness", "technical_analyst", "public", ("market_quote_freshness",)),
        ("public_company_profile", "fundamentals_analyst", "public", ("public_company_profile",)),
        ("economic_awareness_context", "news_analyst", "public", ()),
        ("sec_recent_filings_metadata", "news_analyst", "public", ()),
        ("evidence_gap_inspector", "portfolio_manager_agent", "agent_safe", ("trade_intent_summary",)),
    ),
)
def test_initial_tools_return_valid_tool_result_envelopes(
    tool_name: str,
    role_name: str,
    expected_tier: str,
    expected_refs: tuple[str, ...],
) -> None:
    result = execute_tool_request(
        ToolRequest(tool_name=tool_name, requesting_role=role_name),
        evidence=_evidence_package(),
    )

    assert result.tool_name == tool_name
    assert result.role_name == role_name
    assert result.status in {"ok", "unavailable"}
    assert result.evidence_tier == expected_tier
    assert result.contract_version == "p33a_tool_result_v1"
    assert result.is_mock is False
    assert result.provenance in {"saved_evidence_package", "saved_public_evidence"}
    assert result.source_key
    assert result.source_label
    assert result.availability in {"available", "limited", "not_available", "not_reviewed", "not_applicable"}
    assert result.summary_payload
    for ref in expected_refs:
        assert ref in result.evidence_refs
    if result.availability not in {"available", "limited"}:
        assert result.evidence_refs == ()

    rendered = repr(result).lower()
    for forbidden in (
        "provider_account_id",
        "broker_account_id",
        "account_number",
        "buying_power",
        "raw_payload",
        "holdings",
        "positions",
        "tax_lot",
        "prompt",
        "trace",
        "safe to trade",
        "ready to trade",
    ):
        assert forbidden not in rendered


def test_deterministic_review_findings_cites_only_available_or_limited_sections() -> None:
    evidence = _evidence_package().model_copy(
        update={
            "portfolio_impact_summary": _section(
                "portfolio_impact_summary",
                availability="not_available",
                summary_label="Portfolio impact was not available in saved evidence.",
            )
        }
    )

    result = execute_tool_request(
        ToolRequest(tool_name="deterministic_review_findings", requesting_role="risk_management_agent"),
        evidence=evidence,
    )

    assert result.availability == "limited"
    assert "actionability" in result.evidence_refs
    assert "portfolio_impact_summary" not in result.evidence_refs
    assert result.summary_payload["portfolio_impact_availability"] == "not_available"


def test_evidence_gap_inspector_keeps_gap_refs_out_of_citable_evidence_refs() -> None:
    result = execute_tool_request(
        ToolRequest(tool_name="evidence_gap_inspector", requesting_role="risk_management_agent"),
        evidence=_evidence_package(),
    )

    gap_refs = tuple(result.summary_payload["unavailable_evidence_refs"])
    assert "before_after_portfolio_impact" in gap_refs
    assert result.evidence_refs == ("trade_intent_summary", "scope_state")
    assert not set(gap_refs).intersection(result.evidence_refs)


@pytest.mark.parametrize("evidence", (_evidence_package(), _stock_etf_evidence_package()))
def test_m1_tools_read_only_the_frozen_saved_evidence_package(
    evidence: SavedEvidencePackageRead,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_current_state_is_consulted(*args, **kwargs):
        raise AssertionError("M1 tools must not consult current state or external services")

    monkeypatch.setattr("socket.create_connection", fail_if_current_state_is_consulted)

    trade_result = execute_tool_request(
        ToolRequest(tool_name="trade_intent_summary", requesting_role="fundamentals_analyst"),
        evidence=evidence,
    )
    deterministic_result = execute_tool_request(
        ToolRequest(tool_name="deterministic_review_findings", requesting_role="risk_management_agent"),
        evidence=evidence,
    )
    gap_result = execute_tool_request(
        ToolRequest(tool_name="evidence_gap_inspector", requesting_role="portfolio_manager_agent"),
        evidence=evidence,
    )

    assert trade_result.summary_payload["supported_flow"] == evidence.trade_intent_summary.supported_flow
    assert trade_result.summary_payload["review_flow_label"] == evidence.trade_intent_summary.review_flow_label
    assert trade_result.summary_payload["symbol_or_underlying"] == evidence.trade_intent_summary.symbol_or_underlying
    assert deterministic_result.summary_payload["options_exposure_availability"] == (
        evidence.options_exposure_summary.availability
    )
    assert tuple(gap_result.summary_payload["unavailable_evidence_refs"]) == tuple(
        ref
        for ref in gap_result.summary_payload["unavailable_evidence_refs"]
        if ref not in gap_result.evidence_refs
    )
    assert all(result.is_mock is False for result in (trade_result, deterministic_result, gap_result))


def test_public_role_request_for_agent_safe_tool_returns_safe_blocked_result() -> None:
    result = execute_tool_request(
        ToolRequest(tool_name="portfolio_scope_context", requesting_role="fundamentals_analyst"),
        evidence=_evidence_package(),
    )

    assert result.status == "blocked"
    assert result.evidence_tier == "public"
    assert result.data_mode == "synthetic"
    assert result.availability == "not_available"
    assert result.summary_payload["summary"] == "Requesting role is not allowed to receive this tool tier."


def test_unknown_tool_returns_safe_blocked_result_without_execution() -> None:
    result = execute_tool_request(
        ToolRequest(tool_name="unreviewed_tool", requesting_role="portfolio_manager_agent"),
        evidence=_evidence_package(),
    )

    assert result.status == "blocked"
    assert result.source_key == "tool_policy"
    assert result.evidence_refs == ()


def test_public_company_profile_unavailable_degrades_honestly() -> None:
    evidence = _evidence_package(public_company_profile=_public_company_profile_section(availability="not_available"))

    result = execute_tool_request(
        ToolRequest(tool_name="public_company_profile", requesting_role="fundamentals_analyst"),
        evidence=evidence,
    )

    assert result.status == "unavailable"
    assert result.availability == "not_available"
    assert result.evidence_refs == ()
    assert result.summary_payload["fact_keys_present"] == ()


def test_fred_economic_awareness_context_returns_safe_saved_metadata() -> None:
    evidence = _evidence_package(economic_awareness_snapshot=_fred_economic_awareness_section())

    result = execute_tool_request(
        ToolRequest(tool_name="economic_awareness_context", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "ok"
    assert result.evidence_tier == "public"
    assert result.data_mode == "public"
    assert result.source_key == "fred_macro_calendar_metadata"
    assert result.source_label == "FRED macro calendar metadata · economic context only"
    assert result.evidence_refs == ("economic_awareness_snapshot",)
    assert set(result.summary_payload) == {
        "reviewed_release_event_labels",
        "reviewed_release_metadata",
        "attribution",
        "notice",
        "caveat",
    }
    assert result.summary_payload["reviewed_release_event_labels"] == (
        "Consumer Price Index release",
        "Federal Open Market Committee calendar",
    )
    assert result.summary_payload["reviewed_release_metadata"] == (
        {"fact_key": "release_name", "fact_label": "Release Name", "value_label": "Consumer Price Index release"},
        {"fact_key": "release_date", "fact_label": "Release Date", "value_label": "2026-07-15"},
        {
            "fact_key": "event_name",
            "fact_label": "Event Name",
            "value_label": "Federal Open Market Committee calendar",
        },
        {"fact_key": "event_date", "fact_label": "Event Date", "value_label": "2026-07-29"},
    )
    assert (
        result.summary_payload["attribution"]
        == "Source: FRED, Federal Reserve Bank of St. Louis. Economic release/calendar metadata only. "
        "Not investment advice or a trading signal."
    )
    assert (
        result.summary_payload["notice"]
        == "This product uses the FRED API but is not endorsed or certified by the Federal Reserve Bank of St. Louis."
    )
    assert "trade recommendation" in result.summary_payload["caveat"]
    rendered = repr(result).lower()
    for forbidden in ("actual_label", "forecast_label", "previous_label", "raw_payload", "api_key", "http://", "https://"):
        assert forbidden not in rendered


def test_fred_approval_marker_must_be_in_caveat_codes_not_release_labels() -> None:
    section = _section(
        "economic_awareness_snapshot",
        availability="available",
        summary_label="Macro release metadata is available.",
    ).model_copy(update={"detail_labels": ("fred_macro_calendar_metadata",)})
    evidence = _evidence_package(economic_awareness_snapshot=section)

    result = execute_tool_request(
        ToolRequest(tool_name="economic_awareness_context", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "unavailable"
    assert result.evidence_refs == ()


def test_fred_economic_awareness_filters_unapproved_value_fields() -> None:
    section = _fred_economic_awareness_section().model_copy(
        update={
            "detail_labels": (
                "release_name: Consumer Price Index release",
                "release_date: 2026-07-15",
                "release_date: actual 3.0",
                "actual_label: 3.0",
                "event_date: forecast 2.9",
                "forecast_label: 2.9",
                "previous_label: 2.8",
                "observation_value: raw observation",
            )
        }
    )
    evidence = _evidence_package(economic_awareness_snapshot=section)

    result = execute_tool_request(
        ToolRequest(tool_name="economic_awareness_context", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "ok"
    assert result.summary_payload["reviewed_release_metadata"] == (
        {"fact_key": "release_name", "fact_label": "Release Name", "value_label": "Consumer Price Index release"},
        {"fact_key": "release_date", "fact_label": "Release Date", "value_label": "2026-07-15"},
    )
    rendered = repr(result.model_dump(mode="python")).lower() if hasattr(result, "model_dump") else repr(result).lower()
    for forbidden in (
        "actual_label",
        "forecast_label",
        "previous_label",
        "observation_value",
        "raw observation",
        "actual 3.0",
        "forecast 2.9",
    ):
        assert forbidden not in rendered


def test_sec_recent_filings_metadata_returns_safe_saved_event_metadata() -> None:
    evidence = _evidence_package(public_events_calendar=_sec_recent_filings_section())

    result = execute_tool_request(
        ToolRequest(tool_name="sec_recent_filings_metadata", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "ok"
    assert result.evidence_tier == "public"
    assert result.data_mode == "public"
    assert result.source_key == "sec_edgar_recent_filings"
    assert result.source_label == "SEC EDGAR recent filing metadata - company events only"
    assert result.evidence_refs == ("public_events_calendar",)
    assert set(result.summary_payload) == {
        "reviewed_filing_metadata",
        "attribution",
        "caveat",
        "non_endorsement",
        "limitations",
    }
    assert result.summary_payload["reviewed_filing_metadata"] == (
        {"fact_key": "form_type", "fact_label": "Form type", "value_label": "Form 8-K"},
        {"fact_key": "filing_date", "fact_label": "Filing date", "value_label": "Filed 2026-05-29"},
        {
            "fact_key": "filing_reference",
            "fact_label": "Normalized filing reference",
            "value_label": "filref_recent_event_001",
        },
    )
    assert (
        result.summary_payload["attribution"]
        == "Source: SEC EDGAR submissions/index metadata. Recent filing metadata only. "
        "Not investment advice or a trading signal."
    )
    assert "does not interpret filing contents" in result.summary_payload["caveat"]
    assert (
        result.summary_payload["non_endorsement"]
        == "Use of SEC EDGAR data does not imply endorsement by the U.S. Securities and Exchange Commission."
    )
    rendered = repr(result).lower()
    for forbidden in (
        "raw_payload",
        "source_url",
        "http://",
        "https://",
        "filing_text",
        "article_body",
        "api_key",
        "newsapi",
        "fmp economic calendar",
    ):
        assert forbidden not in rendered


def test_sec_recent_filings_tool_rejects_non_edgar_event_source() -> None:
    generic_event_section = _sec_recent_filings_section().model_copy(
        update={
            "source_key": "sec_edgar_submissions",
            "source_label": "SEC EDGAR metadata - company profile only",
            "caveat_codes": ("sec_edgar_recent_filings_metadata",),
        }
    )
    evidence = _evidence_package(public_events_calendar=generic_event_section)

    result = execute_tool_request(
        ToolRequest(tool_name="sec_recent_filings_metadata", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "unavailable"
    assert result.evidence_refs == ()


@pytest.mark.parametrize(
    "section",
    (
        _section(
            "economic_awareness_snapshot",
            availability="available",
            summary_label="FMP calendar metadata was attached.",
            caveat_codes=("fmp_calendar_metadata",),
        ),
        _section(
            "market_mood_snapshot",
            availability="available",
            summary_label="CNN-derived Market Mood was attached.",
            caveat_codes=("cnn_market_mood",),
        ),
    ),
)
def test_non_fred_market_macro_sources_are_not_available_to_agent_tools(section: SavedEvidenceSectionRead) -> None:
    evidence = _evidence_package(economic_awareness_snapshot=section)

    result = execute_tool_request(
        ToolRequest(tool_name="economic_awareness_context", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "unavailable"
    assert result.evidence_refs == ()


def test_sec_recent_filings_tool_drops_raw_sec_file_paths_from_filing_reference() -> None:
    section = _sec_recent_filings_section().model_copy(
        update={
            "facts": (
                SavedPublicEvidenceFactRead(fact_key="form_type", fact_label="Form type", value_label="Form 8-K"),
                SavedPublicEvidenceFactRead(
                    fact_key="filing_date",
                    fact_label="Filing date",
                    value_label="Filed 2026-05-29",
                ),
                SavedPublicEvidenceFactRead(
                    fact_key="filing_reference",
                    fact_label="Normalized filing reference",
                    value_label="/Archives/edgar/data/0000320193/0000320193-26-000001/aapl-20260601.htm",
                ),
            )
        }
    )
    evidence = _evidence_package(public_events_calendar=section)

    result = execute_tool_request(
        ToolRequest(tool_name="sec_recent_filings_metadata", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "ok"
    assert result.evidence_refs == ("public_events_calendar",)
    assert result.summary_payload["reviewed_filing_metadata"] == (
        {"fact_key": "form_type", "fact_label": "Form type", "value_label": "Form 8-K"},
        {"fact_key": "filing_date", "fact_label": "Filing date", "value_label": "Filed 2026-05-29"},
    )
    rendered = repr(result).lower()
    assert "/archives/" not in rendered
    assert "aapl-20260601.htm" not in rendered


def test_sec_recent_filings_tool_drops_raw_sec_file_paths_from_any_metadata_value() -> None:
    section = _sec_recent_filings_section().model_copy(
        update={
            "facts": (
                SavedPublicEvidenceFactRead(
                    fact_key="form_type",
                    fact_label="Form type",
                    value_label="/Archives/edgar/data/0000320193/0000320193-26-000001/aapl-20260601.htm",
                ),
                SavedPublicEvidenceFactRead(
                    fact_key="filing_date",
                    fact_label="Filing date",
                    value_label="edgar/data/0000320193/0000320193-26-000001.txt",
                ),
                SavedPublicEvidenceFactRead(
                    fact_key="form_type",
                    fact_label="Form type",
                    value_label="aapl-20260601.pdf",
                ),
                SavedPublicEvidenceFactRead(
                    fact_key="filing_reference",
                    fact_label="Normalized filing reference",
                    value_label="filref_recent_event_001",
                ),
            )
        }
    )
    evidence = _evidence_package(public_events_calendar=section)

    result = execute_tool_request(
        ToolRequest(tool_name="sec_recent_filings_metadata", requesting_role="news_analyst"),
        evidence=evidence,
    )

    assert result.status == "ok"
    assert result.summary_payload["reviewed_filing_metadata"] == (
        {
            "fact_key": "filing_reference",
            "fact_label": "Normalized filing reference",
            "value_label": "filref_recent_event_001",
        },
    )
    rendered = repr(result).lower()
    assert "/archives/" not in rendered
    assert "edgar/data" not in rendered
    assert "aapl-20260601.htm" not in rendered
    assert "aapl-20260601.pdf" not in rendered


@pytest.mark.parametrize(
    "payload",
    (
        {"source_url": "https://www.sec.gov/raw/disallowed"},
        {"filing_text": "Filing text is outside the approved metadata lane."},
        {"article_body": "News article text is outside the approved metadata lane."},
        {"summary_payload": {"raw_payload": "not allowed"}},
    ),
)
def test_sec_recent_filings_tool_result_rejects_raw_source_shapes(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="sec_recent_filings_metadata",
            role_name="news_analyst",
            status="ok",
            evidence_tier="public",
            data_mode="public",
            source_key="sec_edgar_recent_filings",
            source_label="SEC EDGAR recent filing metadata - company events only",
            availability="available",
            evidence_refs=("public_events_calendar",),
            summary_payload=payload,
        )


def test_unavailable_market_quote_freshness_is_not_cited_as_evidence() -> None:
    evidence = _evidence_package().model_copy(
        update={
            "market_quote_freshness": _section(
                "market_quote_freshness",
                availability="not_available",
                summary_label="Market quote freshness was not available in saved evidence.",
            )
        }
    )

    result = execute_tool_request(
        ToolRequest(tool_name="market_quote_freshness", requesting_role="technical_analyst"),
        evidence=evidence,
    )

    assert result.status == "unavailable"
    assert result.evidence_refs == ()


def test_tool_result_rejects_forbidden_private_values_recursively() -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="trade_intent_summary",
            role_name="portfolio_manager_agent",
            status="ok",
            evidence_tier="agent_safe",
            data_mode="agent_safe",
            summary_payload={"nested": {"value": "provider_account_id_secret"}},
        )


def test_tool_result_rejects_generated_metric_text() -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="trade_intent_summary",
            role_name="fundamentals_analyst",
            status="ok",
            evidence_tier="public",
            data_mode="public",
            summary_payload={"summary": "Generated target $120.00"},
        )


@pytest.mark.parametrize(
    "summary_payload",
    (
        {"source_url": "reviewed source label only, no URLs"},
        {"summary": "Raw source is https://example.test/disallowed"},
        {"nested": {"urls": ("not allowed",)}},
    ),
)
def test_tool_result_rejects_raw_url_keys_and_values(summary_payload: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="public_company_profile",
            role_name="fundamentals_analyst",
            status="ok",
            evidence_tier="public",
            data_mode="public",
            summary_payload=summary_payload,
        )


def test_tool_request_rejects_raw_url_values() -> None:
    with pytest.raises(ValueError):
        ToolRequest(
            tool_name="public_company_profile",
            requesting_role="fundamentals_analyst",
            args={"section_key": "https://example.test/disallowed"},
        )


def test_registry_stays_offline_and_in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("network/provider calls are not allowed")

    monkeypatch.setattr("socket.create_connection", fail_if_called)
    result = execute_tool_request(
        ToolRequest(tool_name="trade_intent_summary", requesting_role="fundamentals_analyst"),
        evidence=_evidence_package(),
    )

    assert result.status == "ok"
    assert result.provenance == "saved_evidence_package"
