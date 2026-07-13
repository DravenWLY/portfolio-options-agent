from datetime import UTC, date, datetime, timedelta
import json

import pytest

from app.schemas.reports import SavedEvidenceSectionRead, SavedToolMediatedRunArtifactRead
from app.schemas.reports import SavedPublicEvidenceFactRead, SavedPublicEvidenceSectionRead
from app.services.agent_team.auditing.v3_value_gates import (
    ADVICE_BOUNDARY_FLAG,
    GROUNDING_FLAG,
    IDENTIFIER_AMBIGUOUS_FLAG,
    IDENTIFIER_PRIVACY_FLAG,
    NUMERIC_PROVENANCE_FLAG,
    STRUCTURE_CONTRACT_FLAG,
    V2_ARTIFACT_SCHEMA_VERSION,
    WHAT_WAS_VERIFIED_FLAG,
    _advice_boundary_flag,
    frozen_artifact_gate_version,
    validate_v3_value_bearing_markdown,
    validate_p36_risk_analysis_section,
)
from app.services.agent_team.orchestration.deterministic_standalone import (
    build_deterministic_standalone_summary_check,
    freeze_deterministic_standalone_summary_check,
)
from app.services.agent_team.llm_clients.contracts import LLMProviderResponse
from app.services.agent_team.orchestration import tool_mediated_runner as runner
from app.services.agent_team.orchestration.tool_mediated_runner import (
    build_tool_mediated_agent_team_summary,
    run_tool_mediated_agent_team,
)
from app.services.agent_team.tools import (
    P36_CALC_TOOL_CONTRACT_VERSION,
    ToolRequest,
    ToolResult,
    default_tool_registry,
    execute_tool_request,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports.display_labels import find_internal_display_tokens
from app.services.reports.display_labels import UNKNOWN_DISPLAY_LABEL
from app.services.reports.source_snapshots import (
    FMP_EOD_HISTORY_ATTRIBUTION,
    FMP_EOD_HISTORY_CAVEAT,
    FMP_FUNDAMENTALS_ATTRIBUTION,
    FMP_FUNDAMENTALS_SOURCE_KEY,
    FMP_FUNDAMENTALS_SOURCE_LABEL,
    FRED_MACRO_SERIES_ATTRIBUTION,
    FRED_MACRO_SERIES_SOURCE_KEY,
    FRED_MACRO_SERIES_SOURCE_LABEL,
    FmpEodHistorySnapshotProvider,
)
from app.services.market_data.eod_history import (
    FMP_EOD_SOURCE_KEY,
    FMP_EOD_SOURCE_LABEL,
    MarketContextPolicy,
    market_context_execution_context_for_client,
)
from tests.services.agent_team.test_tools import _evidence_package


pytestmark = [pytest.mark.unit]


def _calculation_evidence(*, supported_flow: str = "stock_buy"):
    evidence = _evidence_package()
    before_after = SavedEvidenceSectionRead(
        section_key="before_after_portfolio_impact",
        section_label="Before/after portfolio impact",
        availability="available",
        summary_label="Synthetic frozen before-and-after exposure evidence.",
        detail_labels=(
            "Single-name/asset view: Row | Before $ | Before % | Trade Delta $ | After $ | After %.",
            "Cash | $100.00 | 50.0% | -$20.00 | $80.00 | 40.0%.",
            "XYZ | $100.00 | 50.0% | +$20.00 | $120.00 | 60.0%.",
            "Industry view: Row | Before $ | Before % | Trade Delta $ | After $ | After %.",
            "Semiconductors | $100.00 | 50.0% | +$20.00 | $120.00 | 60.0%.",
            "Sector view: Row | Before $ | Before % | Trade Delta $ | After $ | After %.",
            "Technology | $100.00 | 50.0% | +$20.00 | $120.00 | 60.0%.",
        ),
    )
    concentration = SavedEvidenceSectionRead(
        section_key="concentration_risk_drift",
        section_label="Concentration and risk drift",
        availability="available",
        summary_label="Synthetic frozen concentration evidence.",
    )
    intent = evidence.trade_intent_summary.model_copy(update={"supported_flow": supported_flow})
    return evidence.model_copy(
        update={
            "trade_intent_summary": intent,
            "before_after_portfolio_impact": before_after,
            "concentration_risk_drift": concentration,
        }
    )


def _fmp_fundamentals_section(*, include_prior: bool = False) -> SavedPublicEvidenceSectionRead:
    as_of = "Fiscal period: FY 2026; report date: 2026-06-01; currency: USD"
    prior_as_of = "Fiscal period: FY 2025; report date: 2025-06-01; currency: USD"
    source_label = FMP_FUNDAMENTALS_SOURCE_LABEL
    return SavedPublicEvidenceSectionRead(
        section_key="public_fundamentals_snapshot",
        section_label="Public fundamentals snapshot",
        availability="available",
        freshness_category="fresh",
        freshness_label="Synthetic normalized statement facts",
        source_key=FMP_FUNDAMENTALS_SOURCE_KEY,
        source_label=source_label,
        rights_status="reviewed",
        as_of=datetime(2026, 6, 1, tzinfo=UTC),
        collected_at=datetime(2026, 6, 1, tzinfo=UTC),
        facts=(
            SavedPublicEvidenceFactRead(
                fact_key="income_statement_revenue",
                fact_label="Income statement: Revenue",
                value_label="200 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
            *(
                (
                    SavedPublicEvidenceFactRead(
                        fact_key="income_statement_revenue",
                        fact_label="Income statement: Revenue",
                        value_label="160 USD",
                        as_of_label=prior_as_of,
                        source_label=source_label,
                    ),
                )
                if include_prior
                else ()
            ),
            SavedPublicEvidenceFactRead(
                fact_key="income_statement_gross_profit",
                fact_label="Income statement: Gross profit",
                value_label="100 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
            SavedPublicEvidenceFactRead(
                fact_key="income_statement_operating_income",
                fact_label="Income statement: Operating income",
                value_label="40 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
            SavedPublicEvidenceFactRead(
                fact_key="income_statement_net_income",
                fact_label="Income statement: Net income",
                value_label="20 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
            SavedPublicEvidenceFactRead(
                fact_key="cash_flow_free_cash_flow",
                fact_label="Cash flow: Free cash flow",
                value_label="30 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
            SavedPublicEvidenceFactRead(
                fact_key="balance_sheet_current_assets",
                fact_label="Balance sheet: Current assets",
                value_label="80 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
            SavedPublicEvidenceFactRead(
                fact_key="balance_sheet_current_liabilities",
                fact_label="Balance sheet: Current liabilities",
                value_label="40 USD",
                as_of_label=as_of,
                source_label=source_label,
            ),
        ),
        limitations=(FMP_FUNDAMENTALS_ATTRIBUTION, "Synthetic normalized snapshot only."),
        caveat_codes=("fmp_reported_statement_facts_only",),
    )


def _fred_macro_series_section(*, include_prior: bool = False) -> SavedPublicEvidenceSectionRead:
    source_label = FRED_MACRO_SERIES_SOURCE_LABEL
    facts = [
        SavedPublicEvidenceFactRead(
            fact_key="fred_consumer_price_index",
            fact_label="Consumer Price Index",
            value_label="3.2 Percent",
            as_of_label="Observation date: 2026-06-01; frequency: Monthly",
            source_label=source_label,
        )
    ]
    if include_prior:
        facts.append(
            SavedPublicEvidenceFactRead(
                fact_key="fred_consumer_price_index",
                fact_label="Consumer Price Index",
                value_label="3.0 Percent",
                as_of_label="Observation date: 2026-05-01; frequency: Monthly",
                source_label=source_label,
            )
        )
    return SavedPublicEvidenceSectionRead(
        section_key="fred_macro_series_snapshot",
        section_label="FRED macro series snapshot",
        availability="available",
        freshness_category="fresh",
        freshness_label="Synthetic normalized macro observations",
        source_key=FRED_MACRO_SERIES_SOURCE_KEY,
        source_label=source_label,
        rights_status="reviewed",
        as_of=datetime(2026, 6, 1, tzinfo=UTC),
        collected_at=datetime(2026, 6, 1, tzinfo=UTC),
        facts=tuple(facts),
        limitations=(FRED_MACRO_SERIES_ATTRIBUTION, "Synthetic normalized snapshot only."),
        caveat_codes=("fred_macro_series_observations_only",),
    )


def _frozen_eod_section(*, row_count: int = 260) -> SavedPublicEvidenceSectionRead:
    start = date(2025, 1, 1)
    facts = tuple(
        SavedPublicEvidenceFactRead(
            fact_key="eod_ohlcv_bar",
            fact_label="End-of-day OHLCV row",
            value_label=f"{(start + timedelta(days=index)).isoformat()}|{index + 1}|{index + 2}|{index}|{index + 1}|{1000 + index}",
            as_of_label=f"Window date: {(start + timedelta(days=index)).isoformat()}; collected: 2026-01-01",
            source_label=FMP_EOD_SOURCE_LABEL,
        )
        for index in range(row_count)
    )
    return SavedPublicEvidenceSectionRead(
        section_key="public_market_context",
        section_label="Public market context",
        availability="available",
        freshness_category="fresh",
        freshness_label="Synthetic frozen end-of-day window",
        source_key=FMP_EOD_SOURCE_KEY,
        source_label=FMP_EOD_SOURCE_LABEL,
        rights_status="reviewed",
        as_of=datetime.combine(start + timedelta(days=row_count - 1), datetime.min.time(), tzinfo=UTC),
        collected_at=datetime(2026, 1, 1, tzinfo=UTC),
        facts=facts,
        limitations=(FMP_EOD_HISTORY_ATTRIBUTION, FMP_EOD_HISTORY_CAVEAT),
        caveat_codes=("eod_not_live_prices",),
    )


class _FrozenOnlyEodClient:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_eod_history(self, *, symbol: str, limit: int = 260):
        self.calls += 1
        start = date(2025, 1, 1)
        return tuple(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": str(index + 1),
                "high": str(index + 2),
                "low": str(index),
                "close": str(index + 1),
                "volume": 1000 + index,
            }
            for index in reversed(range(260))
        )


def _public_calculation_evidence(
    *,
    include_eod: bool = False,
    include_statement_prior: bool = False,
    include_macro_prior: bool = False,
):
    from tests.services.agent_team.test_tools import _sec_recent_filings_section

    evidence = _calculation_evidence()
    assert evidence.public_evidence is not None
    public_evidence = evidence.public_evidence.model_copy(
        update={
            "public_fundamentals_snapshot": _fmp_fundamentals_section(include_prior=include_statement_prior),
            "public_events_calendar": _sec_recent_filings_section(),
            "fred_macro_series_snapshot": _fred_macro_series_section(include_prior=include_macro_prior),
            "public_market_context": _frozen_eod_section() if include_eod else evidence.public_evidence.public_market_context,
        }
    )
    return evidence.model_copy(update={"public_evidence": public_evidence})


def _calc_result(*, value_label: str = "1000000 dollars") -> ToolResult:
    return ToolResult(
        tool_name="calc_cash_impact",
        role_name="risk_management_agent",
        status="ok",
        evidence_tier="agent_safe",
        data_mode="agent_safe",
        source_key="frozen_saved_evidence_calculations",
        source_label="Frozen saved-evidence calculations",
        availability="available",
        evidence_refs=("before_after_portfolio_impact",),
        summary_payload={
            "calc_name": "calc_cash_impact",
            "inputs_used": ("before_after_portfolio_impact",),
            "value_labels": (
                {"fact_key": "cash_before_value", "value_label": value_label, "unit_label": "dollars"},
            ),
            "method_label": "Synthetic frozen cash calculation",
            "as_of_labels": ("2026-07-12",),
            "caveats": (),
            "outcome": "available",
        },
        provenance="frozen_saved_evidence",
        is_mock=False,
        contract_version=P36_CALC_TOOL_CONTRACT_VERSION,
    )


def test_p36_registry_and_c1_to_c3_use_only_frozen_derived_evidence() -> None:
    evidence = _calculation_evidence()
    registry = default_tool_registry()

    for name in ("calc_exposure_delta", "calc_concentration_metrics", "calc_cash_impact"):
        result = execute_tool_request(
            ToolRequest(tool_name=name, requesting_role="risk_management_agent"),
            evidence=evidence,
            registry=registry,
        )
        assert result.contract_version == P36_CALC_TOOL_CONTRACT_VERSION
        assert result.evidence_tier == "agent_safe"
        assert result.data_mode == "agent_safe"
        assert result.provenance == "frozen_saved_evidence"
        assert result.summary_payload["outcome"] == "available"
        assert result.summary_payload["inputs_used"]
        assert all("account" not in row["fact_key"] for row in result.summary_payload["value_labels"])
        assert not find_forbidden_keys(result.summary_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
        assert all("$" not in row["value_label"] and "%" not in row["value_label"] for row in result.summary_payload["value_labels"])

    blocked = execute_tool_request(
        ToolRequest(tool_name="calc_cash_impact", requesting_role="technical_analyst"),
        evidence=evidence,
        registry=registry,
    )
    assert blocked.status == "blocked"
    assert blocked.evidence_tier == "public"


def test_p36_c4_c5_options_fail_closed_when_broker_semantics_are_absent() -> None:
    evidence = _calculation_evidence(supported_flow="covered_call")
    registry = default_tool_registry()

    for name in ("calc_option_structure", "calc_scenario_exposure"):
        result = execute_tool_request(
            ToolRequest(tool_name=name, requesting_role="risk_management_agent"),
            evidence=evidence,
            registry=registry,
        )
        assert result.status == "unavailable"
        assert result.availability == "not_available"
        assert result.summary_payload["outcome"] == "unable_to_verify"
        assert result.summary_payload["value_labels"] == ()
        assert "available_covered_shares_not_reviewed" in result.caveat_codes
        assert "pending_order_awareness_not_reviewed" in result.caveat_codes
        assert "covered" not in " ".join(str(row) for row in result.summary_payload["value_labels"]).lower()


def test_p36_calculation_envelope_retires_only_legacy_contract_count_scanner() -> None:
    result = _calc_result(value_label="40 contracts")

    assert result.summary_payload["value_labels"][0]["value_label"] == "40 contracts"

    with pytest.raises(ValueError, match="generated metric"):
        ToolResult(
            tool_name="deterministic_review_findings",
            role_name="risk_management_agent",
            status="ok",
            evidence_tier="agent_safe",
            data_mode="agent_safe",
            summary_payload={"label": "40 contracts"},
        )

    for forbidden_value in ("10 yield", "price target 100", "$100 dollars"):
        with pytest.raises(ValueError):
            _calc_result(value_label=forbidden_value)


@pytest.mark.parametrize(
    ("markdown", "expected"),
    (
        ("The frozen result lists 1000000 dollars as of 2026-07-12.", None),
        ("The frozen result lists 1,000,000 dollars as of 2026-07-12.", None),
        ("The frozen result lists 1000001 dollars as of 2026-07-12.", NUMERIC_PROVENANCE_FLAG),
        ("The account number: 12345678 was present.", IDENTIFIER_PRIVACY_FLAG),
        ("The provider_id: demo-provider-123456 was present.", IDENTIFIER_PRIVACY_FLAG),
        ("api_key: synthetic-secret-value was present.", IDENTIFIER_PRIVACY_FLAG),
        ("Review /Archives/edgar/data/example.txt.", IDENTIFIER_PRIVACY_FLAG),
        ("The connection 123456 was not reviewed.", IDENTIFIER_AMBIGUOUS_FLAG),
        ("The account has 123 dollars in the frozen result.", NUMERIC_PROVENANCE_FLAG),
        ("The account nickname, snapshot cash, holdings, positions, portfolio, and exposure remain saved context.", None),
    ),
)
def test_p36_f5_f6_canaries(markdown: str, expected: str | None) -> None:
    assert validate_v3_value_bearing_markdown(markdown=markdown, role_results=(_calc_result(),)) == expected


def test_p36_standalone_summary_and_v3_freeze_never_rerun_calculations(monkeypatch) -> None:
    evidence = _calculation_evidence()
    check = build_deterministic_standalone_summary_check(evidence)
    frozen = freeze_deterministic_standalone_summary_check(
        check,
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )

    assert len(check.calculation_results) == 19
    assert "frozen review-time evidence" in check.summary_markdown
    assert "Broker snapshot freshness:" in check.summary_markdown
    assert "Source: frozen saved evidence." in check.summary_markdown
    assert "Gap: option structure could not be verified" not in check.summary_markdown
    assert "cash before value" in check.summary_markdown
    assert not find_internal_display_tokens(check.summary_markdown)
    assert frozen_artifact_gate_version(frozen) == "v3"

    def _must_not_run(*args, **kwargs):
        raise AssertionError("readback must not rerun calculations")

    monkeypatch.setattr(
        "app.services.agent_team.orchestration.deterministic_standalone.execute_tool_request",
        _must_not_run,
    )
    round_tripped = SavedToolMediatedRunArtifactRead.model_validate(frozen.model_dump(mode="json"))
    assert round_tripped.model_dump(mode="json") == frozen.model_dump(mode="json")


def test_p36_c6_to_c15_are_public_frozen_only_with_labeled_comparison_windows(monkeypatch) -> None:
    evidence = _public_calculation_evidence(
        include_eod=True,
        include_statement_prior=True,
        include_macro_prior=True,
    )
    registry = default_tool_registry()
    public_tools = (
        "calc_price_range_position",
        "calc_return_windows",
        "calc_drawdown_stats",
        "calc_volatility_stats",
        "calc_ma_relationships",
        "calc_financial_ratios",
        "calc_period_change",
        "calc_macro_series_change",
        "calc_event_window",
        "calc_freshness_inventory",
    )
    for name in public_tools:
        assert registry[name].evidence_tier == "public"

    for name in (
        "calc_price_range_position",
        "calc_return_windows",
        "calc_drawdown_stats",
        "calc_volatility_stats",
        "calc_ma_relationships",
    ):
        technical = execute_tool_request(
            ToolRequest(tool_name=name, requesting_role="technical_analyst"),
            evidence=evidence,
            registry=registry,
        )
        assert technical.status == "ok"
        assert technical.evidence_tier == "public"
        assert technical.data_mode == "public"
        assert technical.summary_payload["outcome"] == "available"
        assert "public_market_context" in technical.evidence_refs
        assert "Window:" in technical.summary_payload["as_of_labels"][0]
        assert technical.summary_payload["value_labels"]

    ratios = execute_tool_request(
        ToolRequest(tool_name="calc_financial_ratios", requesting_role="fundamentals_analyst"),
        evidence=evidence,
        registry=registry,
    )
    assert ratios.summary_payload["outcome"] == "available"
    assert {row["fact_key"] for row in ratios.summary_payload["value_labels"]} == {
        "gross_margin_percent",
        "operating_margin_percent",
        "net_margin_percent",
        "free_cash_flow_margin_percent",
        "current_ratio",
    }

    period = execute_tool_request(
        ToolRequest(tool_name="calc_period_change", requesting_role="fundamentals_analyst"),
        evidence=evidence,
        registry=registry,
    )
    macro = execute_tool_request(
        ToolRequest(tool_name="calc_macro_series_change", requesting_role="news_analyst"),
        evidence=evidence,
        registry=registry,
    )
    assert period.summary_payload["outcome"] == "available"
    assert {row["fact_key"] for row in period.summary_payload["value_labels"]} >= {
        "statement_absolute_change",
        "statement_percent_change",
        "statement_current_period",
        "statement_prior_period",
    }
    assert macro.summary_payload["outcome"] == "available"
    assert {row["fact_key"] for row in macro.summary_payload["value_labels"]} >= {
        "macro_absolute_change",
        "macro_change_direction",
        "macro_current_observation",
        "macro_prior_observation",
    }

    no_lane_period = execute_tool_request(
        ToolRequest(tool_name="calc_period_change", requesting_role="fundamentals_analyst"),
        evidence=_calculation_evidence(),
        registry=registry,
    )
    assert no_lane_period.summary_payload["outcome"] == "unable_to_verify"
    assert "source_rights_not_approved" in no_lane_period.caveat_codes

    single_period = _public_calculation_evidence(include_eod=True)
    for name, role, caveat in (
        ("calc_period_change", "fundamentals_analyst", "period_comparison_not_available"),
        ("calc_macro_series_change", "news_analyst", "macro_series_history_not_available"),
    ):
        unavailable = execute_tool_request(
            ToolRequest(tool_name=name, requesting_role=role),
            evidence=single_period,
            registry=registry,
        )
        assert unavailable.summary_payload["outcome"] == "unable_to_verify"
        assert caveat in unavailable.caveat_codes

    absent_eod = execute_tool_request(
        ToolRequest(tool_name="calc_return_windows", requesting_role="technical_analyst"),
        evidence=_public_calculation_evidence(),
        registry=registry,
    )
    assert absent_eod.summary_payload["outcome"] == "unable_to_verify"
    assert "frozen_eod_history_not_available" in absent_eod.caveat_codes

    event = execute_tool_request(
        ToolRequest(tool_name="calc_event_window", requesting_role="news_analyst"),
        evidence=evidence,
        registry=registry,
    )
    assert event.summary_payload["outcome"] == "available"
    assert any(row["value_label"] == "3 days old" for row in event.summary_payload["value_labels"])

    from tests.services.agent_team.test_tools import _sec_recent_filings_section

    future_events = _sec_recent_filings_section().model_copy(
        update={
            "facts": (
                SavedPublicEvidenceFactRead(fact_key="form_type", fact_label="Form type", value_label="Form 8-K"),
                SavedPublicEvidenceFactRead(
                    fact_key="filing_date",
                    fact_label="Filing date",
                    value_label="Filed 2026-06-04",
                ),
            )
        }
    )
    assert evidence.public_evidence is not None
    future_evidence = evidence.model_copy(
        update={"public_evidence": evidence.public_evidence.model_copy(update={"public_events_calendar": future_events})}
    )
    future_event = execute_tool_request(
        ToolRequest(tool_name="calc_event_window", requesting_role="news_analyst"),
        evidence=future_evidence,
        registry=registry,
    )
    assert "event_after_saved_snapshot" in future_event.caveat_codes
    assert {
        row["fact_key"]: row["value_label"] for row in future_event.summary_payload["value_labels"]
    }["event_timing_label"] == "3 days after the saved snapshot"

    freshness = execute_tool_request(
        ToolRequest(tool_name="calc_freshness_inventory", requesting_role="news_analyst"),
        evidence=evidence,
        registry=registry,
    )
    assert freshness.evidence_tier == "public"
    assert all(not ref.startswith("before_after_") for ref in freshness.evidence_refs)
    assert all("scope_state" not in ref for ref in freshness.evidence_refs)

    def _must_not_prompt_or_fetch(*args, **kwargs):
        raise AssertionError("deterministic floors must not invoke a provider or source client")

    monkeypatch.setattr(
        "app.services.agent_team.orchestration.tool_mediated_runner._live_provider_request",
        _must_not_prompt_or_fetch,
    )
    check = build_deterministic_standalone_summary_check(evidence)
    frozen = freeze_deterministic_standalone_summary_check(check, frozen_at=datetime(2026, 6, 1, tzinfo=UTC))
    assert len(check.calculation_results) == 19
    freshness_results = tuple(result for result in check.calculation_results if result.tool_name == "calc_freshness_inventory")
    assert {result.role_name for result in freshness_results} == {
        "technical_analyst",
        "risk_management_agent",
        "fundamentals_analyst",
        "news_analyst",
        "portfolio_manager_agent",
    }
    for result in freshness_results:
        assert "before_after_portfolio_impact" not in result.evidence_refs
        assert "scope_state" not in result.evidence_refs
    assert frozen.provider_runs == ()
    assert "method: Frozen reported-statement ratio calculation" in check.summary_markdown
    assert "method: Frozen end-of-day range-position calculation" in check.summary_markdown
    assert "method: Frozen reported-statement period comparison" in check.summary_markdown
    assert "method: Frozen macro-series comparison" in check.summary_markdown
    assert "source: Frozen saved-evidence calculations" in check.summary_markdown
    assert not find_internal_display_tokens(check.summary_markdown)
    assert "p36-role-analysis-v1" not in frozen.model_dump_json()
    assert "pm-synthesis" not in frozen.model_dump_json()


def test_p36_eod_window_is_frozen_before_deterministic_composition_and_readback() -> None:
    client = _FrozenOnlyEodClient()
    context = market_context_execution_context_for_client(
        client,
        collected_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    section = FmpEodHistorySnapshotProvider(
        policy=MarketContextPolicy(mode="live"),
        context=context,
    ).section("XYZ")
    assert client.calls == 1

    evidence = _public_calculation_evidence(include_statement_prior=True, include_macro_prior=True)
    assert evidence.public_evidence is not None
    frozen_evidence = evidence.model_copy(
        update={"public_evidence": evidence.public_evidence.model_copy(update={"public_market_context": section})}
    )
    check = build_deterministic_standalone_summary_check(frozen_evidence)
    frozen = freeze_deterministic_standalone_summary_check(
        check,
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )

    assert client.calls == 1
    assert frozen.provider_runs == ()
    assert all(result.summary_payload["outcome"] == "available" for result in check.calculation_results[5:10])
    restored = SavedToolMediatedRunArtifactRead.model_validate(frozen.model_dump(mode="json"))
    assert restored.model_dump(mode="json") == frozen.model_dump(mode="json")
    assert client.calls == 1


def test_p36_calculation_display_labels_render_approved_labels_or_a_safe_fallback() -> None:
    from app.services.agent_team.orchestration.deterministic_standalone import _render_values

    rendered = _render_values(
        (
            {"fact_key": "gross_margin_percent", "value_label": "50.0 percent", "unit_label": "percent"},
            {"fact_key": "unapproved_storage_key", "value_label": "synthetic", "unit_label": "label"},
        )
    )
    assert "gross margin" in rendered
    assert "unapproved_storage_key" not in rendered
    assert UNKNOWN_DISPLAY_LABEL in rendered


def test_p36_freeze_cannot_mix_v2_and_v3_contracts() -> None:
    evidence = _calculation_evidence()
    frozen = freeze_deterministic_standalone_summary_check(
        build_deterministic_standalone_summary_check(evidence),
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    mixed = frozen.model_dump(mode="python")
    mixed["artifact_schema_version"] = V2_ARTIFACT_SCHEMA_VERSION

    with pytest.raises(ValueError, match="v3 gate contract"):
        SavedToolMediatedRunArtifactRead.model_validate(mixed)

    legacy_summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    assert legacy_summary.tool_run_artifact is not None
    assert frozen_artifact_gate_version(legacy_summary.tool_run_artifact) == "v2"


def test_p36_readback_revalidates_the_frozen_calculation_envelope_shape() -> None:
    frozen = freeze_deterministic_standalone_summary_check(
        build_deterministic_standalone_summary_check(_calculation_evidence()),
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    poisoned = frozen.model_dump(mode="python")
    first_result = dict(poisoned["tool_results"][0])
    malformed_payload = dict(first_result["summary_payload"])
    malformed_payload["unreviewed_input"] = "synthetic"
    first_result["summary_payload"] = malformed_payload
    poisoned["tool_results"] = (first_result, *poisoned["tool_results"][1:])

    with pytest.raises(ValueError, match="approved envelope keys"):
        SavedToolMediatedRunArtifactRead.model_validate(poisoned)


def test_p36_v3_freeze_drops_an_entire_live_section_for_unmatched_numeric_prose() -> None:
    frozen = freeze_deterministic_standalone_summary_check(
        build_deterministic_standalone_summary_check(_calculation_evidence()),
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    poisoned = frozen.model_dump(mode="python")
    poisoned["audited_findings"] = (
        {
            "role_name": "risk_management_agent",
            "role_status": "completed",
            "findings": (),
            "warning_codes": (),
            "live_report_markdown": "The frozen calculation lists 1000001 dollars.",
        },
    )

    with pytest.raises(ValueError, match="numeric_provenance_blocked"):
        SavedToolMediatedRunArtifactRead.model_validate(poisoned)


def test_p36_v3_provenance_does_not_borrow_a_value_from_another_role() -> None:
    frozen = freeze_deterministic_standalone_summary_check(
        build_deterministic_standalone_summary_check(_calculation_evidence()),
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    poisoned = frozen.model_dump(mode="python")
    tool_results = [dict(item) for item in poisoned["tool_results"]]
    cash_result = next(item for item in tool_results if item["tool_name"] == "calc_cash_impact")
    cash_result["role_name"] = "portfolio_manager_agent"
    payload = dict(cash_result["summary_payload"])
    labels = [dict(label) for label in payload["value_labels"]]
    labels[0]["value_label"] = "1000001 dollars"
    payload["value_labels"] = tuple(labels)
    cash_result["summary_payload"] = payload
    poisoned["tool_results"] = tuple(tool_results)
    poisoned["audited_findings"] = (
        {
            "role_name": "risk_management_agent",
            "role_status": "completed",
            "findings": (),
            "warning_codes": (),
            "live_report_markdown": "The frozen calculation lists 1000001 dollars.",
        },
    )

    with pytest.raises(ValueError, match="numeric_provenance_blocked"):
        SavedToolMediatedRunArtifactRead.model_validate(poisoned)


def test_p36_v3_frozen_role_text_allows_topic_vocabulary_but_blocks_compound_private_tokens() -> None:
    frozen = freeze_deterministic_standalone_summary_check(
        build_deterministic_standalone_summary_check(_calculation_evidence()),
        frozen_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    vocabulary_only = frozen.model_dump(mode="python")
    vocabulary_only["audited_findings"] = (
        {
            "role_name": "risk_management_agent",
            "role_status": "completed",
            "findings": (),
            "warning_codes": (),
            "live_report_markdown": (
                "The saved portfolio cash, holdings, positions, and exposure remain review context."
            ),
        },
    )
    SavedToolMediatedRunArtifactRead.model_validate(vocabulary_only)

    compound_token = frozen.model_dump(mode="python")
    compound_token["audited_findings"] = (
        {
            "role_name": "risk_management_agent",
            "role_status": "completed",
            "findings": (),
            "warning_codes": (),
            "live_report_markdown": "The cash_balance field was present in saved context.",
        },
    )
    with pytest.raises(ValueError, match="identifier_privacy_blocked"):
        SavedToolMediatedRunArtifactRead.model_validate(compound_token)


class _P36RiskLoopProvider:
    provider_name = "p36-risk-loop-fake"
    model = "p36-risk-loop-model"

    def __init__(
        self,
        *,
        invalid_requests: bool = False,
        include_values: bool = False,
        request_forever: bool = False,
        truncate: bool = False,
        mutated_numeric: bool = False,
        malformed: bool = False,
        excessive_requests: bool = False,
        execution_phrase: bool = False,
    ) -> None:
        self.calls = []
        self.invalid_requests = invalid_requests
        self.include_values = include_values
        self.request_forever = request_forever
        self.truncate = truncate
        self.mutated_numeric = mutated_numeric
        self.malformed = malformed
        self.excessive_requests = excessive_requests
        self.execution_phrase = execution_phrase

    def complete(self, request):
        self.calls.append(request)
        if self.truncate:
            content = _p36_risk_section()
        elif self.execution_phrase:
            content = "Please place an order."
        elif self.malformed:
            content = "not a structured request or final section"
        elif self.invalid_requests:
            content = '{"tool_requests": [{"tool_id": "C3", "args": {"scope_category": "12"}}]}'
        elif self.excessive_requests:
            content = json.dumps(
                {
                    "tool_requests": [
                        {"tool_id": "C3", "args": {}}
                        for _ in range(runner.P36_RISK_MAX_TOOL_REQUESTS + 1)
                    ]
                }
            )
        elif self.request_forever or len(self.calls) == 1:
            content = (
                '{"tool_requests": ['
                '{"tool_id": "C1", "args": {"scope_category": "industry"}}, '
                '{"tool_id": "C2", "args": {}}, '
                '{"tool_id": "C3", "args": {}}, '
                '{"tool_id": "C15", "args": {}}'
                ']}'
            )
        else:
            content = _p36_risk_section(include_values=self.include_values)
            if self.mutated_numeric:
                content = content.replace("60.0%", "60.1%")
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=content,
            is_mock=True,
            finish_reason="length" if self.truncate else "stop",
        )


def _p36_risk_section(*, include_values: bool = False) -> str:
    body = " ".join(
        (
            "Per this run's exposure calculation, the saved exposure figures describe the affected industry before and after the proposed trade.",
            "Computed from the saved snapshot, the cash calculation describes the reviewed cash impact without asserting current feasibility.",
            "Per this run's concentration calculation, concentration is a description of the frozen portfolio structure rather than a verdict about it.",
            "The calculation results remain limited to the reviewed package and do not establish current broker state.",
            "The freshness inventory identifies which saved context had a dated record and which context remained unavailable.",
            "These relationships describe saved evidence and leave any decision about the trade outside this section.",
            "The scope may omit changes after the saved snapshot, so the displayed figures are historical review context.",
            "No replacement estimate is used when a calculation result is unavailable for this run.",
        )
    )
    return "\n\n".join(
        (
            "#### Risk and exposure analysis",
            "##### What this trade changes",
            body,
            "##### Concentration and reference points",
            (
                "Per this run's exposure calculation, the affected industry moved from 50.0% to 60.0%, "
                "and computed from the saved snapshot, the cash calculation recorded $100.00 before and $80.00 after."
                if include_values
                else "Per this run's concentration calculation, the reference-point context remains descriptive and uses only the frozen calculation results."
            ),
            "##### Input trust and freshness",
            "The saved freshness inventory identifies dated context and makes unavailable context explicit without filling a gap from elsewhere.",
            "##### What was verified",
            "Frozen role-visible freshness inventory and Frozen saved-evidence calculations were cross-checked against 2025-09-17. Current broker state could not be verified from this saved package.",
            "| Context item | Value or finding | Source and as-of | Status/caveat |",
            "| Exposure context | Frozen calculation results | Frozen saved-evidence calculations, 2025-09-17 | Reviewed package only |",
        )
    )


def test_p36_risk_loop_is_bounded_mediated_and_freezes_the_accepted_section() -> None:
    provider = _P36RiskLoopProvider()
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
    assert risk.live_report_markdown == _p36_risk_section()
    assert len(provider.calls) == 2


def test_p36_risk_loop_accepts_only_frozen_calculation_values_in_live_prose() -> None:
    provider = _P36RiskLoopProvider(include_values=True)
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
    assert risk.live_report_markdown == _p36_risk_section(include_values=True)
    assert "50.0% to 60.0%" in risk.live_report_markdown
    assert "$100.00" in risk.live_report_markdown
    assert {request.role_name for request in provider.calls} == {"risk_management_agent"}
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.artifact_schema_version == "p36_tool_run_freeze_v1"
    assert any(item.tool_name == "calc_cash_impact" for item in summary.tool_run_artifact.tool_results)
    frozen = SavedToolMediatedRunArtifactRead.model_validate(summary.tool_run_artifact.model_dump(mode="json"))
    assert frozen.model_dump(mode="json") == summary.tool_run_artifact.model_dump(mode="json")
    assert len(provider.calls) == 2


def test_p36_risk_loop_stops_after_two_refused_requests_and_keeps_floor() -> None:
    provider = _P36RiskLoopProvider(invalid_requests=True)
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
    assert risk.live_report_markdown is None
    assert len(provider.calls) == 2
    assert "live_provider_safety_fallback" in risk.warning_codes
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.artifact_schema_version == "p36_tool_run_freeze_v1"


def test_p36_risk_loop_stops_after_two_malformed_responses_and_keeps_floor() -> None:
    provider = _P36RiskLoopProvider(malformed=True)
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
    assert risk.live_report_markdown is None
    assert len(provider.calls) == 2
    assert "live_provider_validation_failed" in risk.warning_codes


def test_p36_risk_loop_enforces_tier_one_tool_token_and_wall_clock_budgets(monkeypatch) -> None:
    evidence = _public_calculation_evidence(include_eod=True)

    request_budget_provider = _P36RiskLoopProvider(excessive_requests=True)
    request_budget_summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=request_budget_provider,
        p36_risk_live_enabled=True,
    )
    request_budget_risk = next(item for item in request_budget_summary.role_summaries if item.role_name == "risk_management_agent")
    assert request_budget_risk.live_report_markdown is None
    assert len(request_budget_provider.calls) == 1

    monkeypatch.setattr(runner, "P36_RISK_TOKEN_CEILING", 1)
    token_budget_provider = _P36RiskLoopProvider()
    token_budget_summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=token_budget_provider,
        p36_risk_live_enabled=True,
    )
    token_budget_risk = next(item for item in token_budget_summary.role_summaries if item.role_name == "risk_management_agent")
    assert token_budget_risk.live_report_markdown is None
    assert token_budget_provider.calls == []

    monkeypatch.setattr(
        runner,
        "P36_RISK_TOKEN_CEILING",
        runner.P36_RISK_MAX_PROVIDER_CALLS * runner.P36_ANALYST_MAX_TOKENS_PER_ITERATION,
    )
    monkeypatch.setattr(runner, "P36_RISK_WALL_CLOCK_SECONDS", -1)
    wall_clock_provider = _P36RiskLoopProvider()
    wall_clock_summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=wall_clock_provider,
        p36_risk_live_enabled=True,
    )
    wall_clock_risk = next(item for item in wall_clock_summary.role_summaries if item.role_name == "risk_management_agent")
    assert wall_clock_risk.live_report_markdown is None
    assert wall_clock_provider.calls == []


def test_p36_risk_loop_forces_the_floor_when_iteration_three_requests_again() -> None:
    provider = _P36RiskLoopProvider(request_forever=True)
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
    assert risk.live_report_markdown is None
    assert len(provider.calls) == 3
    assert "live_provider_safety_fallback" in risk.warning_codes


def test_p36_risk_loop_drops_truncated_or_unproven_numeric_provider_output() -> None:
    for provider in (
        _P36RiskLoopProvider(truncate=True),
        _P36RiskLoopProvider(include_values=True, mutated_numeric=True),
    ):
        summary = build_tool_mediated_agent_team_summary(
            _public_calculation_evidence(include_eod=True),
            report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
            llm_provider=provider,
            p36_risk_live_enabled=True,
        )
        risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
        assert risk.live_report_markdown is None
        assert risk.summary_markdown


def test_p36_execution_phrase_uses_one_whole_section_fallback_path() -> None:
    provider = _P36RiskLoopProvider(execution_phrase=True)
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    risk = next(item for item in summary.role_summaries if item.role_name == "risk_management_agent")
    assert risk.live_report_markdown is None
    assert "live_provider_safety_fallback" in risk.warning_codes
    assert "live_advice_boundary_dropped" not in risk.warning_codes


def test_p36_risk_dynamic_prompt_uses_opaque_calculation_ids_only() -> None:
    provider = _P36RiskLoopProvider()
    build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
    )

    assert len(provider.calls) == 2
    assert all("risk and exposure analyst" in request.messages[0].content for request in provider.calls)
    dynamic_messages = tuple(request.messages[1].content.lower() for request in provider.calls)
    assert all("calc_cash_impact" not in message for message in dynamic_messages)
    assert all("cash" not in message for message in dynamic_messages)
    assert all("'tool_id'" in message for message in dynamic_messages)
    assert all("c1" in message and "c15" in message for message in dynamic_messages)


def _p36_risk_gate_results() -> tuple[ToolResult, ...]:
    evidence = _public_calculation_evidence(include_eod=True)
    registry = default_tool_registry()
    names = (
        "trade_intent_summary",
        "portfolio_scope_context",
        "deterministic_review_findings",
        "broker_snapshot_freshness",
        "market_quote_freshness",
        "evidence_gap_inspector",
        "calc_exposure_delta",
        "calc_concentration_metrics",
        "calc_cash_impact",
        "calc_freshness_inventory",
    )
    return tuple(
        execute_tool_request(
            ToolRequest(tool_name=name, requesting_role="risk_management_agent"),
            evidence=evidence,
            registry=registry,
        )
        for name in names
    )


def test_p36_risk_gate_blocks_suitability_but_allows_descriptive_concentration() -> None:
    results = _p36_risk_gate_results()
    valid = _p36_risk_section(include_values=True)
    assert validate_p36_risk_analysis_section(markdown=valid, role_results=results) is None
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace(
            "The calculation results remain limited to the reviewed package and do not establish current broker state.",
            "the saved calculation concentrates the portfolio further.",
        ),
        role_results=results,
    ) is None
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("a description of the frozen portfolio structure", "too concentrated"),
        role_results=results,
    ) == ADVICE_BOUNDARY_FLAG
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("rather than a verdict about it", "consider trimming"),
        role_results=results,
    ) == ADVICE_BOUNDARY_FLAG
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace(
            "The calculation results remain limited to the reviewed package and do not establish current broker state.",
            "the saved market context is below both saved long-term averages.",
        ),
        role_results=results,
    ) is None
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("rather than a verdict about it", "suitable for a long-term hold"),
        role_results=results,
    ) == ADVICE_BOUNDARY_FLAG


def test_p36_risk_gate_drops_whole_sections_for_provenance_privacy_structure_and_grounding() -> None:
    results = _p36_risk_gate_results()
    valid = _p36_risk_section(include_values=True)
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("60.0%", "60.1%"),
        role_results=results,
    ) == NUMERIC_PROVENANCE_FLAG
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("historical review context", "cash_balance was present"),
        role_results=results,
    ) == IDENTIFIER_PRIVACY_FLAG
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("##### Input trust and freshness\n", ""),
        role_results=results,
    ) == STRUCTURE_CONTRACT_FLAG
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("2025-09-17", "this run"),
        role_results=results,
    ) == WHAT_WAS_VERIFIED_FLAG
    assert validate_p36_risk_analysis_section(
        markdown=valid.replace("historical review context", "filing says the context changed"),
        role_results=results,
    ) == GROUNDING_FLAG


def test_p36_f6_ambiguous_identifier_residual_defers_to_f5_provenance() -> None:
    allowed = (_calc_result(value_label="136559 dollars"),)

    assert validate_v3_value_bearing_markdown(
        markdown="The saved account context records 136559 dollars.",
        role_results=allowed,
    ) is None
    assert validate_v3_value_bearing_markdown(
        markdown="The saved account context records 136560 dollars.",
        role_results=allowed,
    ) == IDENTIFIER_AMBIGUOUS_FLAG
    assert validate_v3_value_bearing_markdown(
        markdown="The account number: 136559 was present.",
        role_results=allowed,
    ) == IDENTIFIER_PRIVACY_FLAG


def test_p36_f4_attribution_does_not_treat_headings_as_interpretation() -> None:
    assert _advice_boundary_flag("#### Concentration and reference points") is None
