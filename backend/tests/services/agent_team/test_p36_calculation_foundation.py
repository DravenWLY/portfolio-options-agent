from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path

import pytest

from app.config import ConfigurationError
from app.schemas.reports import SavedEvidenceSectionRead, SavedToolMediatedRunArtifactRead
from app.schemas.reports import SavedPublicEvidenceFactRead, SavedPublicEvidenceSectionRead
from app.services.agent_team.auditing.v3_value_gates import (
    ADVICE_BOUNDARY_FLAG,
    GROUNDING_FLAG,
    IDENTIFIER_AMBIGUOUS_FLAG,
    IDENTIFIER_PRIVACY_FLAG,
    NUMERIC_PROVENANCE_FLAG,
    P36_PM_PROMPT_VERSION,
    STRUCTURE_CONTRACT_FLAG,
    V2_ARTIFACT_SCHEMA_VERSION,
    WHAT_WAS_VERIFIED_FLAG,
    _advice_boundary_flag,
    _pm_advice_boundary_flag,
    frozen_artifact_gate_version,
    validate_p36_public_analysis_section,
    validate_p36_pm_synthesis,
    validate_v3_value_bearing_markdown,
    validate_p36_risk_analysis_section,
)
from app.services.agent_team.auditing.live_report_gates import prompt_fact_labels_for_tool_result
from app.services.agent_team.auditing.p36_constants import P36_F6_VOCABULARY_ONLY_TOKENS
from app.services.agent_team.orchestration.deterministic_standalone import (
    build_deterministic_standalone_summary_check,
    freeze_deterministic_standalone_summary_check,
)
from app.services.agent_team.llm_clients.contracts import AGENT_TEAM_ROLES, LLMProviderResponse
from app.services.agent_team.llm_clients.contracts import registered_static_system_prompts
from app.services.agent_team.orchestration import tool_mediated_runner as runner
from app.services.agent_team.orchestration.p36_public_prompts import (
    P36_PUBLIC_ROLE_BLOCKS,
    P36_PUBLIC_SYSTEM_PROMPTS,
    render_p36_public_system_prompt,
)
from app.services.agent_team.orchestration.p36_pm_prompt import P36_PM_SYSTEM_PROMPT
from app.services.agent_team.orchestration.p36_risk_prompt import (
    P36_ANALYST_GATE_DISCIPLINE,
    P36_RISK_ROLE_BLOCK,
    P36_RISK_SYSTEM_PROMPT,
    render_p36_risk_system_prompt,
)
from app.services.agent_team.orchestration.tool_mediated_runner import (
    build_tool_mediated_agent_team_summary,
    run_tool_mediated_agent_team,
)
from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output
from app.services.agent_team.tools import (
    P36_CALC_TOOL_CONTRACT_VERSION,
    ToolRequest,
    ToolResult,
    default_tool_registry,
    execute_tool_request,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports.agent_team_report import P36_LIVE_LANES_ENV, resolve_p36_live_lane_flags
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


def test_p36_live_lane_resolver_defaults_off_and_rejects_unknown_configuration() -> None:
    assert resolve_p36_live_lane_flags({}) == (False, False, False)
    assert resolve_p36_live_lane_flags({P36_LIVE_LANES_ENV: "   "}) == (False, False, False)
    assert resolve_p36_live_lane_flags({P36_LIVE_LANES_ENV: "risk, public,pm"}) == (True, True, True)

    with pytest.raises(ConfigurationError, match="unsupported lane names"):
        resolve_p36_live_lane_flags({P36_LIVE_LANES_ENV: "risk,unknown"})


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


@pytest.mark.parametrize("topic", tuple(sorted(P36_F6_VOCABULARY_ONLY_TOKENS)))
@pytest.mark.parametrize(
    "role_name",
    ("risk_management_agent", "technical_analyst", "fundamentals_analyst", "news_analyst"),
)
def test_p36_f6_vocabulary_import_does_not_change_numeric_or_identifier_gate_outcomes(
    role_name: str,
    topic: str,
) -> None:
    sentence = f"The {topic} 48213 was reviewed in the saved evidence."
    expected = IDENTIFIER_PRIVACY_FLAG if topic == "account" else NUMERIC_PROVENANCE_FLAG
    if role_name == "risk_management_agent":
        assert validate_p36_risk_analysis_section(
            markdown=f"{_p36_risk_section(include_values=True)}\n\n{sentence}",
            role_results=_p36_risk_gate_results(),
        ) == expected
        return
    assert validate_p36_public_analysis_section(
        role_name=role_name,
        markdown=f"{_p36_public_section(role_name)}\n\n{sentence}",
        role_results=_p36_public_role_results()[role_name],
    ) == expected


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


def _p36_public_section(role_name: str, *, macro_heading: bool = False, macro_sentence: str | None = None) -> str:
    titles = {
        "technical_analyst": "#### Technical analysis — XYZ",
        "fundamentals_analyst": "#### Company context — XYZ",
        "news_analyst": "#### Events and macro context — XYZ",
    }
    body = " ".join(
        (
            "Computed from the saved evidence, this section describes only the dated record available for this review.",
            "The frozen inputs keep the observation tied to the saved package rather than a current source.",
            "The recorded context is descriptive, uncertainty qualified, and limited to the source labels supplied in this run.",
            "Freshness and coverage remain part of reading the saved record without changing any availability category.",
            "The section identifies what was present and what was not reviewed without extending the evidence beyond its frozen scope.",
            "The calculation and source labels below provide the reviewed basis for the narrative.",
        )
    )
    if role_name == "technical_analyst":
        headings = (
            "##### Range and trend context",
            "##### Volatility context",
            "##### Gaps and caveats",
        )
        verified = "Frozen end-of-day range-position calculation and saved price history were cross-checked against 2025-09-17. Current data could not be verified from this saved package."
    elif role_name == "fundamentals_analyst":
        headings = ("##### What was reviewed", "##### Recency and coverage")
        verified = "Saved trade intent summary and the saved company profile were cross-checked against 2026-06-01. Reported statements could not be verified from this saved package."
    else:
        headings = ("##### Filing and release record",)
        if macro_heading:
            headings = (*headings, "##### Macro backdrop")
        headings = (*headings, "##### Recency against this review")
        verified = "Saved trade intent summary and frozen macro-series comparison were cross-checked against 2026-06-01. Unreviewed macro context remains a named gap."
    sections = [titles[role_name]]
    for heading in headings:
        sections.extend((heading, macro_sentence if heading == "##### Macro backdrop" and macro_sentence else body))
    sections.extend(
        (
            "##### What was verified",
            verified,
            "| Context item | Value or finding | Source and as-of | Status/caveat |",
            "| Saved context | Frozen evidence only | Saved package | Reviewed scope |",
        )
    )
    return "\n\n".join(sections)


class _P36PublicLoopProvider:
    provider_name = "p36-public-loop-fake"
    model = "p36-public-loop-model"

    def __init__(self) -> None:
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        role_name = request.role_name
        calls_for_role = sum(item.role_name == role_name for item in self.calls)
        if calls_for_role == 1:
            tool_ids = {
                "technical_analyst": ("C6", "C7", "C8", "C9", "C10", "C15"),
                "fundamentals_analyst": ("C11", "C12", "C15"),
                "news_analyst": ("C13", "C14", "C15"),
            }[role_name]
            content = json.dumps({"tool_requests": [{"tool_id": tool_id, "args": {}} for tool_id in tool_ids]})
        else:
            content = _p36_public_section(role_name)
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=content,
            is_mock=True,
            finish_reason="stop",
        )


def test_p36_public_prompts_are_exact_reviewed_static_entries() -> None:
    registered = registered_static_system_prompts()
    assert set(P36_PUBLIC_SYSTEM_PROMPTS) == {"technical_analyst", "fundamentals_analyst", "news_analyst"}
    assert all(prompt in registered for prompt in P36_PUBLIC_SYSTEM_PROMPTS.values())
    assert "Your section describes saved history and nothing past it." in P36_PUBLIC_SYSTEM_PROMPTS["technical_analyst"]
    assert "Your section stops at the reported past and its recency." in P36_PUBLIC_SYSTEM_PROMPTS["fundamentals_analyst"]
    assert "Your section stops at the dated record and its recency." in P36_PUBLIC_SYSTEM_PROMPTS["news_analyst"]


def _k2a_r2_verbatim_block(heading: str) -> str:
    design_path = (
        Path(__file__).resolve().parents[4]
        / "docs"
        / "claude-e-agentic"
        / "PHASE_36_T7_ANALYST_GATE_SURVIVAL_TUNING_DESIGN.md"
    )
    design = design_path.read_text(encoding="utf-8")
    section = design.split(heading, 1)[1]
    return section.split("```text\n", 1)[1].split("\n```", 1)[0]


def test_p36_k2b_analyst_prompt_constants_match_the_reviewed_k2a_r2_document() -> None:
    risk_delta = _k2a_r2_verbatim_block("### 3.4 Risk (all three families)")
    fundamentals_delta = _k2a_r2_verbatim_block("Fundamentals:\n")
    news_delta = _k2a_r2_verbatim_block("News:\n")
    technical_delta = _k2a_r2_verbatim_block("### 3.3 Technical (F-4.6 survivor)")

    assert P36_ANALYST_GATE_DISCIPLINE == _k2a_r2_verbatim_block(
        "### 3.1 New shared constant — `P36_ANALYST_GATE_DISCIPLINE` (analysts only)"
    )
    assert risk_delta in P36_RISK_ROLE_BLOCK
    assert fundamentals_delta in P36_PUBLIC_ROLE_BLOCKS["fundamentals_analyst"]
    assert news_delta in P36_PUBLIC_ROLE_BLOCKS["news_analyst"]
    assert technical_delta in P36_PUBLIC_ROLE_BLOCKS["technical_analyst"]
    assert render_p36_risk_system_prompt().endswith(P36_ANALYST_GATE_DISCIPLINE)
    assert all(
        render_p36_public_system_prompt(role_name).endswith(P36_ANALYST_GATE_DISCIPLINE)
        for role_name in P36_PUBLIC_SYSTEM_PROMPTS
    )


def test_p36_k2b_registration_is_exact_and_leaves_the_pm_prompt_byte_identical() -> None:
    expected_pm_digest = "7869fb9216b1722160406bab0bbe4f55188011606a498bcc0ea777e91962b4a7"
    analyst_prompts = frozenset((P36_RISK_SYSTEM_PROMPT, *P36_PUBLIC_SYSTEM_PROMPTS.values()))
    superseded_prompts = frozenset(
        prompt.removesuffix(f"\n\n{P36_ANALYST_GATE_DISCIPLINE}") for prompt in analyst_prompts
    )

    assert sha256(P36_PM_SYSTEM_PROMPT.encode()).hexdigest() == expected_pm_digest
    assert P36_ANALYST_GATE_DISCIPLINE not in P36_PM_SYSTEM_PROMPT
    assert P36_RISK_SYSTEM_PROMPT == render_p36_risk_system_prompt()
    assert analyst_prompts.issubset(registered_static_system_prompts())
    assert not superseded_prompts & registered_static_system_prompts()


def test_p36_k2b_precision_canary_allows_decimal_equality_but_not_added_precision() -> None:
    result = _calc_result(value_label="49.9")

    assert validate_v3_value_bearing_markdown(
        markdown="Per this run's calculation, the frozen result is 49.90.",
        role_results=(result,),
    ) is None
    assert validate_v3_value_bearing_markdown(
        markdown="Per this run's calculation, the frozen result is 49.958.",
        role_results=(result,),
    ) == NUMERIC_PROVENANCE_FLAG


def test_p36_k2b_long_date_bigram_and_spelled_magnitude_fail_numeric_provenance() -> None:
    result = _calc_result(value_label="49.9")

    assert validate_v3_value_bearing_markdown(
        markdown="The 8-K filing arrived per this run's calculation.",
        role_results=(result,),
    ) == NUMERIC_PROVENANCE_FLAG
    assert validate_v3_value_bearing_markdown(
        markdown="Form 10-Q metadata was reviewed per this run's calculation.",
        role_results=(result,),
    ) == NUMERIC_PROVENANCE_FLAG
    assert validate_v3_value_bearing_markdown(
        markdown="The snapshot is two days stale per this run's calculation.",
        role_results=(result,),
    ) == NUMERIC_PROVENANCE_FLAG


@pytest.mark.parametrize("forbidden", ("annualized", "yield", "support"))
def test_p36_k2b_document_scan_rejects_forbidden_prose_inside_an_accepted_section(forbidden: str) -> None:
    with pytest.raises(ValueError):
        validate_agent_team_report_output(
            {
                "final_synthesis_markdown": f"An accepted analyst section used {forbidden} in rendered prose.",
                "evidence_references": (),
            },
            label="p36 K2B document scan",
        )


def test_p36_k2b_active_lane_prompt_labels_stay_safe_for_document_rendering() -> None:
    evidence = _public_calculation_evidence(
        include_eod=True,
        include_statement_prior=True,
        include_macro_prior=True,
    )
    public_state = run_tool_mediated_agent_team(
        evidence,
        registry=default_tool_registry(),
        llm_provider=_P36PublicLoopProvider(),
        p36_public_live_enabled=True,
    )
    risk_state = run_tool_mediated_agent_team(
        evidence,
        registry=default_tool_registry(),
        llm_provider=_P36RiskLoopProvider(),
        p36_risk_live_enabled=True,
    )
    fact_labels = tuple(
        label
        for result in (*public_state.tool_results, *risk_state.tool_results)
        for label in prompt_fact_labels_for_tool_result(result)
    )
    display_labels = tuple(label["display_label"] for label in fact_labels)

    assert display_labels
    validate_agent_team_report_output(
        {
            "final_synthesis_markdown": "Reviewed prompt labels: " + "; ".join(display_labels),
            "evidence_references": (),
        },
        label="p36 K2B active-lane label audit",
    )


def test_p36_k2c_volatility_prompt_projection_uses_the_approved_display_label() -> None:
    result = execute_tool_request(
        ToolRequest(tool_name="calc_volatility_stats", requesting_role="technical_analyst"),
        evidence=_public_calculation_evidence(include_eod=True),
        registry=default_tool_registry(),
    )
    projected = prompt_fact_labels_for_tool_result(result)
    volatility_label = next(item for item in projected if item["fact_key"] == "annualized_volatility_percent")

    assert volatility_label["display_label"] == "Realized volatility (annual basis)"
    assert volatility_label["fact_key"] == "annualized_volatility_percent"


def test_p36_k2b_guidance_compliant_fixtures_survive_all_analyst_gates_and_fake_loops() -> None:
    evidence = _public_calculation_evidence(include_eod=True)
    risk_results = _p36_risk_gate_results()
    public_results = _p36_public_role_results()

    assert validate_p36_risk_analysis_section(
        markdown=_p36_risk_section(include_values=True),
        role_results=risk_results,
    ) is None
    for role_name in P36_PUBLIC_SYSTEM_PROMPTS:
        assert validate_p36_public_analysis_section(
            role_name=role_name,
            markdown=_p36_public_section(role_name),
            role_results=public_results[role_name],
        ) is None

    provider = _P36GateSurvivalLoopProvider()
    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )
    live_sections = {
        role.role_name: role.live_report_markdown
        for role in summary.role_summaries
        if role.role_name != "portfolio_manager_agent"
    }

    assert all(live_sections.values())
    assert summary.final_synthesis_authored_by == "portfolio_manager_agent"
    assert summary.tool_run_artifact is not None


def test_p36_composed_document_does_not_embed_accepted_analyst_sections() -> None:
    from app.schemas.reports import _projected_final_synthesis_markdown, _render_frozen_role_section

    provider = _P36GateSurvivalLoopProvider()
    market_context = market_context_execution_context_for_client(
        _FrozenOnlyEodClient(),
        collected_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
        market_context=market_context,
    )

    synthesis = summary.final_synthesis_markdown or ""
    analyst_sections = tuple(
        role.live_report_markdown
        for role in summary.role_summaries
        if role.role_name != "portfolio_manager_agent"
    )

    assert all(section for section in analyst_sections)
    assert all(section not in synthesis for section in analyst_sections)
    assert "No Technical Analyst note is available in this saved report." not in synthesis
    assert "| Indicator | Frozen value or category |" in synthesis
    assert _projected_final_synthesis_markdown(summary) == synthesis
    for role in summary.role_summaries:
        if role.role_name == "portfolio_manager_agent":
            continue
        projected = _render_frozen_role_section(role)
        analysis, debugging = projected.split("## Frozen debugging details", maxsplit=1)
        assert role.live_report_markdown in analysis
        assert role.live_report_markdown not in debugging


def test_p36_public_loops_are_sequential_and_freeze_without_pending_source_lanes() -> None:
    provider = _P36PublicLoopProvider()
    evidence = _public_calculation_evidence(include_eod=True, include_statement_prior=True, include_macro_prior=True)
    state = run_tool_mediated_agent_team(
        evidence,
        registry=default_tool_registry(),
        llm_provider=provider,
        p36_public_live_enabled=True,
    )
    assert state.provider_runs
    payload = runner._summary_payload_from_run_state(
        state,
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    validate_agent_team_report_output(payload, label="p36 public loop", evidence_package=evidence)
    provider = _P36PublicLoopProvider()
    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_public_live_enabled=True,
    )
    assert summary.report_status == "full_agent_report", summary

    public_roles = {
        item.role_name: item
        for item in summary.role_summaries
        if item.role_name in {"technical_analyst", "fundamentals_analyst", "news_analyst"}
    }
    assert public_roles["technical_analyst"].live_report_markdown is not None
    assert public_roles["fundamentals_analyst"].live_report_markdown is not None
    assert public_roles["news_analyst"].live_report_markdown is not None
    assert [request.role_name for request in provider.calls] == [
        "fundamentals_analyst",
        "fundamentals_analyst",
        "news_analyst",
        "news_analyst",
        "technical_analyst",
        "technical_analyst",
    ]
    assert summary.tool_run_artifact is not None
    frozen = summary.tool_run_artifact
    dormant = {
        item.tool_name: item
        for item in frozen.tool_results
        if item.tool_name in {"calc_financial_ratios", "calc_period_change", "calc_macro_series_change"}
    }
    assert dormant["calc_financial_ratios"].availability == "not_available"
    assert dormant["calc_period_change"].availability == "not_available"
    assert dormant["calc_macro_series_change"].availability == "not_available"
    assert all("source_rights_not_approved" in item.caveat_codes for item in dormant.values())
    calls_before_readback = len(provider.calls)
    SavedToolMediatedRunArtifactRead.model_validate(frozen.model_dump(mode="json"))
    assert len(provider.calls) == calls_before_readback


def _p36_news_c13_result() -> ToolResult:
    return ToolResult(
        tool_name="calc_macro_series_change",
        role_name="news_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        source_key="frozen_saved_evidence_calculations",
        source_label="Frozen macro-series comparison",
        availability="available",
        evidence_refs=("fred_macro_series_snapshot",),
        summary_payload={
            "calc_name": "calc_macro_series_change",
            "inputs_used": ("fred_macro_series_snapshot",),
            "value_labels": (
                {"fact_key": "macro_series_label", "value_label": "Consumer Price Index", "unit_label": "label"},
                {"fact_key": "macro_current_value", "value_label": "3.2 Percent", "unit_label": "Percent"},
                {"fact_key": "macro_prior_value", "value_label": "3.0 Percent", "unit_label": "Percent"},
                {"fact_key": "macro_absolute_change", "value_label": "0.2 Percent", "unit_label": "Percent"},
                {"fact_key": "macro_change_direction", "value_label": "up", "unit_label": "direction"},
                {"fact_key": "macro_current_observation", "value_label": "2026-06-01", "unit_label": "period"},
                {"fact_key": "macro_prior_observation", "value_label": "2026-05-01", "unit_label": "period"},
            ),
            "method_label": "Frozen macro-series comparison",
            "as_of_labels": ("2026-06-01", "2026-05-01"),
            "caveats": (),
            "outcome": "available",
        },
        provenance="frozen_saved_evidence",
        is_mock=True,
        contract_version=P36_CALC_TOOL_CONTRACT_VERSION,
    )


def _p36_news_gate_results() -> tuple[ToolResult, ...]:
    evidence = _public_calculation_evidence(include_eod=True)
    registry = default_tool_registry()
    return (
        execute_tool_request(
            ToolRequest(tool_name="trade_intent_summary", requesting_role="news_analyst"),
            evidence=evidence,
            registry=registry,
        ),
        _p36_news_c13_result(),
    )


def test_p36_c13_requires_same_sentence_governed_series_label_for_each_numeric_value() -> None:
    results = _p36_news_gate_results()
    correct = _p36_public_section(
        "news_analyst",
        macro_heading=True,
        macro_sentence="Computed from the saved series, Consumer Price Index recorded 3.2 Percent in the frozen comparison.",
    )
    assert validate_p36_public_analysis_section(
        role_name="news_analyst",
        markdown=correct,
        role_results=results,
    ) is None

    swapped = correct.replace("Consumer Price Index recorded 3.2", "Yield-curve spread recorded 3.2")
    assert validate_p36_public_analysis_section(
        role_name="news_analyst",
        markdown=swapped,
        role_results=results,
    ) == GROUNDING_FLAG

    split = correct.replace(
        "Consumer Price Index recorded 3.2 Percent in the frozen comparison.",
        "Consumer Price Index is included in the frozen comparison. The recorded value was 3.2 Percent.",
    )
    assert validate_p36_public_analysis_section(
        role_name="news_analyst",
        markdown=split,
        role_results=results,
    ) == GROUNDING_FLAG


def _p36_public_role_results() -> dict[str, tuple[ToolResult, ...]]:
    state = run_tool_mediated_agent_team(
        _public_calculation_evidence(include_eod=True, include_statement_prior=True, include_macro_prior=True),
        registry=default_tool_registry(),
        llm_provider=_P36PublicLoopProvider(),
        p36_public_live_enabled=True,
    )
    return {
        role_name: tuple(result for result in state.tool_results if result.role_name == role_name)
        for role_name in ("technical_analyst", "fundamentals_analyst", "news_analyst")
    }


def test_p36_public_f8_binds_symbol_and_without_variant_headings() -> None:
    results = _p36_public_role_results()

    technical = _p36_public_section("technical_analyst")
    assert validate_p36_public_analysis_section(
        role_name="technical_analyst",
        markdown=technical,
        role_results=results["technical_analyst"],
    ) is None
    assert validate_p36_public_analysis_section(
        role_name="technical_analyst",
        markdown=technical.replace("Technical analysis — XYZ", "Technical analysis — OTHER"),
        role_results=results["technical_analyst"],
    ) == STRUCTURE_CONTRACT_FLAG

    fundamentals = _p36_public_section("fundamentals_analyst")
    assert validate_p36_public_analysis_section(
        role_name="fundamentals_analyst",
        markdown=fundamentals.replace("##### What was reviewed", "##### Reported record"),
        role_results=results["fundamentals_analyst"],
    ) == STRUCTURE_CONTRACT_FLAG

    news = _p36_public_section("news_analyst", macro_heading=True)
    assert validate_p36_public_analysis_section(
        role_name="news_analyst",
        markdown=news,
        role_results=results["news_analyst"],
    ) == STRUCTURE_CONTRACT_FLAG


@pytest.mark.parametrize(
    ("role_name", "replacement"),
    (
        ("technical_analyst", "The saved history will continue beyond the frozen window."),
        ("fundamentals_analyst", "The reported record makes the company attractive."),
        ("news_analyst", "The dated record is already priced in."),
    ),
)
def test_p36_public_role_specific_advice_boundary_canaries_drop_sections(
    role_name: str,
    replacement: str,
) -> None:
    results = _p36_public_role_results()
    markdown = _p36_public_section(role_name).replace(
        "The frozen inputs keep the observation tied to the saved package rather than a current source.",
        replacement,
    )

    assert validate_p36_public_analysis_section(
        role_name=role_name,
        markdown=markdown,
        role_results=results[role_name],
    ) == ADVICE_BOUNDARY_FLAG


@pytest.mark.parametrize(
    "news_verdict",
    (
        "The impact is material.",
        "The news is material.",
        "The 8-K is material.",
        "The guidance update is material.",
        "It is material.",
        "This is material.",
        "The catalyst is material.",
        "The print was material.",
        "The filing is not material.",
        "The filing is highly material.",
        "The disclosure is quite material.",
        "The materiality here is high.",
    ),
)
def test_p36_news_bare_materiality_rule_matches_aa146a2(news_verdict: str) -> None:
    assert _advice_boundary_flag(news_verdict, role_name="news_analyst") == ADVICE_BOUNDARY_FLAG


@pytest.mark.parametrize(
    "news_verdict",
    (
        "The data is immaterial.",
        "The filing is immaterial.",
        "The charge was immaterial.",
        "The immateriality of the item was noted.",
    ),
)
def test_p36_news_immateriality_tightening_is_ratified_by_ruling_t5b_3(news_verdict: str) -> None:
    # RULING-T5B-3 ratified this fail-closed tightening over aa146a2.
    assert _advice_boundary_flag(news_verdict, role_name="news_analyst") == ADVICE_BOUNDARY_FLAG


def test_p36_public_f9_and_f11_drop_unanchored_or_filing_content_prose() -> None:
    results = _p36_public_role_results()
    technical = _p36_public_section("technical_analyst")
    boilerplate = technical.replace(
        "Frozen end-of-day range-position calculation and saved price history were cross-checked against 2025-09-17. Current data could not be verified from this saved package.",
        "The saved evidence was reviewed for this report.",
    )
    assert validate_p36_public_analysis_section(
        role_name="technical_analyst",
        markdown=boilerplate,
        role_results=results["technical_analyst"],
    ) == WHAT_WAS_VERIFIED_FLAG

    news = _p36_public_section("news_analyst").replace(
        "The frozen inputs keep the observation tied to the saved package rather than a current source.",
        "The filing states that its contents changed the reviewed record.",
    )
    assert validate_p36_public_analysis_section(
        role_name="news_analyst",
        markdown=news,
        role_results=results["news_analyst"],
    ) == GROUNDING_FLAG


def _p36_pm_synthesis_payload() -> dict[str, object]:
    return {
        "evidence_weighting": (
            "The company section carries the most weight because it is the reviewed profile record. "
            "The events section supplies dated record context without filing contents. "
            "The deterministic findings retain the documented scope and freshness limits."
        ),
        "evidence_tensions": (
            "The company section and the events section cover different dated records, and the tension remains unresolved. Re-syncing the saved inputs would resolve it.",
        ),
        "verification_priorities": (
            "Verify the latest saved snapshot date before relying on this report.",
            "Review the public-record coverage against the saved scope.",
        ),
        "trust_assessment": (
            "The deterministic findings and accepted sections provide frozen context for this report. "
            "The saved evidence can bear only the weight allowed by its freshness and coverage caveats."
        ),
    }


def _validate_pm_payload(
    payload: dict[str, object],
    *,
    accepted: frozenset[str] | None = None,
    surfaced_markdown: tuple[str, ...] = (),
) -> str | None:
    return validate_p36_pm_synthesis(
        evidence_weighting=str(payload["evidence_weighting"]),
        evidence_tensions=tuple(payload["evidence_tensions"]),  # type: ignore[arg-type]
        verification_priorities=tuple(payload["verification_priorities"]),  # type: ignore[arg-type]
        trust_assessment=str(payload["trust_assessment"]),
        role_results=(),
        accepted_role_names=accepted
        or frozenset({"technical_analyst", "fundamentals_analyst", "news_analyst"}),
        surfaced_markdown=surfaced_markdown,
    )


def test_p36_pm_prompt_is_reviewed_static_and_typed_gate_accepts_safe_synthesis() -> None:
    assert P36_PM_SYSTEM_PROMPT in registered_static_system_prompts()
    assert "Return one strict JSON object and nothing else" in P36_PM_SYSTEM_PROMPT
    assert _validate_pm_payload(_p36_pm_synthesis_payload()) is None


@pytest.mark.parametrize(
    "verdict",
    (
        "The trade is attractive.",
        "The trade holds up well.",
        "The setup looks solid.",
        "The evidence points the right way.",
        "The idea makes sense.",
        "On balance the position stands up.",
    ),
)
def test_p36_pm_soft_and_hard_verdicts_drop_from_freeform_fields(verdict: str) -> None:
    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = verdict + " The technical section is a saved input. The company section is a saved input."
    assert _validate_pm_payload(payload) == ADVICE_BOUNDARY_FLAG
    payload = _p36_pm_synthesis_payload()
    payload["trust_assessment"] = verdict + " The saved evidence remains limited by its frozen scope."
    assert _validate_pm_payload(payload) == ADVICE_BOUNDARY_FLAG


@pytest.mark.parametrize(
    "verdict",
    (
        "Buy this trade.",
        "Reduce the position.",
        "This is a good entry.",
    ),
)
@pytest.mark.parametrize("field_name", ("evidence_weighting", "trust_assessment"))
def test_p36_pm_hard_verdict_canaries_drop_from_every_freeform_field(
    verdict: str,
    field_name: str,
) -> None:
    payload = _p36_pm_synthesis_payload()
    if field_name == "evidence_weighting":
        payload[field_name] = (
            f"{verdict} The company section is a saved input. The events section is a saved input."
        )
    else:
        payload[field_name] = f"{verdict} The saved evidence remains limited by its frozen scope."
    assert _validate_pm_payload(payload) == ADVICE_BOUNDARY_FLAG


@pytest.mark.parametrize(
    "news_verdict",
    (
        "The filing is not material.",
        "The release is already priced in.",
        "The tone was hawkish.",
        "The rate cut is dovish.",
        "It is material.",
        "The 8-K is material.",
        "The filing is highly material.",
        "The event is not material.",
        "The materiality of the filing is high.",
        "The impact was immaterial.",
    ),
)
@pytest.mark.parametrize("field_name", ("evidence_weighting", "trust_assessment"))
def test_p36_pm_inherits_news_interpretation_bans_in_every_freeform_field(
    news_verdict: str,
    field_name: str,
) -> None:
    payload = _p36_pm_synthesis_payload()
    if field_name == "evidence_weighting":
        payload[field_name] = (
            f"{news_verdict} The company section is a saved input. The events section is a saved input."
        )
    else:
        payload[field_name] = f"{news_verdict} The saved evidence remains limited by its frozen scope."
    surfaced_markdown = ("The accepted events section listed Form 8-K.",) if "8-K" in news_verdict else ()
    flag = _validate_pm_payload(payload, surfaced_markdown=surfaced_markdown)
    assert flag is not None
    if news_verdict == "The 8-K is material.":
        # "The 8" is treated as an invalid long-date form by F-5 and therefore
        # fails first. The direct probe below still locks the PM F-4 decision.
        assert flag == NUMERIC_PROVENANCE_FLAG
    else:
        assert flag == ADVICE_BOUNDARY_FLAG


def test_p36_pm_materiality_gate_blocks_unlisted_record_subject_independent_of_f5() -> None:
    assert _pm_advice_boundary_flag(
        "The 8-K is material.",
        freeform_markdown="The 8-K is material.",
    ) == ADVICE_BOUNDARY_FLAG


@pytest.mark.parametrize(
    "evidence_phrase",
    (
        "The company section is not material to this reading.",
        "The saved sections are the material inputs.",
        "The source material was reviewed.",
        "A material portion of the weighting comes from the profile.",
        "The evidence is material to the synthesis.",
        "The findings differ materially across sections.",
    ),
)
def test_p36_pm_allows_material_language_when_it_weights_evidence(evidence_phrase: str) -> None:
    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        f"{evidence_phrase} The company section is a saved input. The events section is a saved input."
    )
    surfaced_markdown = ("The accepted events section listed Form 8-K.",) if "8-K" in evidence_phrase else ()
    assert _validate_pm_payload(payload, surfaced_markdown=surfaced_markdown) is None


@pytest.mark.parametrize(
    "residual_phrase",
    (
        "The section shows the filing is material.",
        "The evidence confirms the 8-K is material.",
        "The company section and the events section disagree on dates, and the filing is highly material.",
    ),
)
def test_p36_pm_known_residual_same_sentence_colocation_is_documented(residual_phrase: str) -> None:
    # Tolerated co-location gap, not approved output. A future targeted gate
    # may tighten this behavior without changing the accepted-output contract.
    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        f"{residual_phrase} The company section is a saved input. The events section is a saved input."
    )
    surfaced_markdown = ("The accepted events section listed Form 8-K.",) if "8-K" in residual_phrase else ()
    assert _validate_pm_payload(payload, surfaced_markdown=surfaced_markdown) is None


def test_p36_pm_known_residual_predicate_severing_wrap_is_documented() -> None:
    # Tolerated predicate-severing wrap gap introduced by the F-B2 splitter,
    # not approved output. A future normalize-per-field pass may tighten this
    # behavior without changing the accepted-output contract.
    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        "The filing is\nmaterial. The company section is a saved input. The events section is a saved input."
    )
    assert _validate_pm_payload(payload) is None


def test_p36_pm_wrapped_nominal_materiality_still_drops() -> None:
    # The nominal materiality ban survives a newline and bounds the wrap residual.
    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        "The materiality\nof the filing is high. The company section is a saved input. The events section is a saved input."
    )
    assert _validate_pm_payload(payload) == ADVICE_BOUNDARY_FLAG


def test_p36_pm_materiality_does_not_merge_unpunctuated_priorities_into_trust() -> None:
    control = _p36_pm_synthesis_payload()
    control["verification_priorities"] = (
        "Verify the latest saved snapshot date before relying on this report.",
        "Review the saved coverage before relying on this report.",
    )
    control["trust_assessment"] = (
        "The materiality of the filing is high. "
        "The saved evidence can bear only the weight allowed by its freshness and coverage caveats."
    )
    assert _validate_pm_payload(control) == ADVICE_BOUNDARY_FLAG

    probe = _p36_pm_synthesis_payload()
    probe["verification_priorities"] = (
        "Verify the latest saved snapshot date before relying on this report.",
        "Review the saved snapshot inputs before relying on this report",
    )
    probe["trust_assessment"] = control["trust_assessment"]
    assert _validate_pm_payload(probe) == ADVICE_BOUNDARY_FLAG


def test_p36_pm_materiality_does_not_merge_unpunctuated_weighting_into_tension() -> None:
    control = _p36_pm_synthesis_payload()
    control["evidence_weighting"] = (
        "The company section carries the most weight because it is the reviewed profile record. "
        "The events section supplies dated record context without filing contents. "
        "The saved inputs stand."
    )
    control["evidence_tensions"] = (
        "The filing is highly material. The tension remains unresolved.",
    )
    assert _validate_pm_payload(control) == ADVICE_BOUNDARY_FLAG

    probe = _p36_pm_synthesis_payload()
    probe["evidence_weighting"] = control["evidence_weighting"].removesuffix(".")
    probe["evidence_tensions"] = control["evidence_tensions"]
    assert _validate_pm_payload(probe) == ADVICE_BOUNDARY_FLAG


def test_p36_pm_tension_resolution_and_section_attribution_marker_are_gated() -> None:
    payload = _p36_pm_synthesis_payload()
    payload["evidence_tensions"] = (
        "The technical section identifies a downtrend, and the tension favors that record. The company section is a saved input.",
    )
    assert _validate_pm_payload(payload) == ADVICE_BOUNDARY_FLAG

    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        "The company section describes elevated concentration in the saved record. "
        "The events section is a saved input. The deterministic findings retain the documented scope."
    )
    assert _validate_pm_payload(payload) is None


def test_p36_pm_numeric_provenance_allows_only_surfaced_values() -> None:
    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        "The company section records 48213 as a new figure. "
        "The events section is a saved input. The deterministic findings retain the documented scope."
    )
    assert _validate_pm_payload(payload) == NUMERIC_PROVENANCE_FLAG


def test_p36_pm_typed_f1_f2_f3_attribution_and_grounding_gates_fail_closed() -> None:
    payload = _p36_pm_synthesis_payload()
    payload["verification_priorities"] = ("Reduce the position by half.", "Review the frozen inputs.")
    assert _validate_pm_payload(payload) == STRUCTURE_CONTRACT_FLAG

    payload = _p36_pm_synthesis_payload()
    payload["evidence_tensions"] = ("- The technical section has a gap.",)
    assert _validate_pm_payload(payload) == STRUCTURE_CONTRACT_FLAG

    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        "Concentration is elevated in the record. The company section is a saved input. The events section is a saved input."
    )
    assert _validate_pm_payload(payload) == "attribution_required_blocked"

    payload = _p36_pm_synthesis_payload()
    payload["evidence_weighting"] = (
        "The risk section carries the most weight because it is the freshest saved input. The company section is a saved input. The events section is a saved input."
    )
    assert _validate_pm_payload(payload, accepted=frozenset({"technical_analyst", "fundamentals_analyst"})) == GROUNDING_FLAG


class _P36PmLoopProvider:
    provider_name = "p36-pm-loop-fake"
    model = "p36-pm-loop-model"

    def __init__(self, *, unsafe_pm: bool = False, unavailable_pm: bool = False) -> None:
        self.calls = []
        self.unsafe_pm = unsafe_pm
        self.unavailable_pm = unavailable_pm

    def complete(self, request):
        self.calls.append(request)
        if request.role_name in {"technical_analyst", "fundamentals_analyst", "news_analyst"}:
            content = _p36_public_section(request.role_name)
            return LLMProviderResponse(
                request_id=request.request_id,
                role_name=request.role_name,
                status="ok",
                provider=self.provider_name,
                model=self.model,
                prompt_version=request.prompt_version,
                content_markdown=content,
                is_mock=True,
                finish_reason="stop",
            )
        if self.unavailable_pm:
            return LLMProviderResponse(
                request_id=request.request_id,
                role_name=request.role_name,
                status="provider_unavailable",
                provider=self.provider_name,
                model=self.model,
                prompt_version=request.prompt_version,
                content_markdown=None,
                is_mock=True,
                finish_reason="stop",
            )
        payload = _p36_pm_synthesis_payload()
        if self.unsafe_pm:
            payload["evidence_weighting"] = (
                "The trade holds up well. The technical section is a saved input. The company section is a saved input."
            )
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=json.dumps(payload),
            is_mock=True,
            finish_reason="stop",
        )


class _P36PmWithRiskProvider:
    provider_name = "p36-pm-with-risk-fake"
    model = "p36-pm-with-risk-model"

    def __init__(self) -> None:
        self.calls = []
        self.risk_call_count = 0

    def complete(self, request):
        self.calls.append(request)
        if request.role_name == "risk_management_agent":
            self.risk_call_count += 1
            content = (
                '{"tool_requests": ['
                '{"tool_id": "C1", "args": {"scope_category": "industry"}}, '
                '{"tool_id": "C2", "args": {}}, '
                '{"tool_id": "C3", "args": {}}, '
                '{"tool_id": "C15", "args": {}}'
                ']}'
                if self.risk_call_count == 1
                else _p36_risk_section()
            )
        elif request.role_name in {"technical_analyst", "fundamentals_analyst", "news_analyst"}:
            content = _p36_public_section(request.role_name)
        else:
            content = json.dumps(_p36_pm_synthesis_payload())
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=content,
            is_mock=True,
            finish_reason="stop",
        )


class _P36GateSurvivalLoopProvider:
    provider_name = "p36-gate-survival-fake"
    model = "p36-gate-survival-model"

    def __init__(self) -> None:
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        role_name = request.role_name
        call_count = sum(item.role_name == role_name for item in self.calls)
        if role_name == "portfolio_manager_agent":
            content = json.dumps(_p36_pm_synthesis_payload())
        elif call_count == 1:
            tool_ids = {
                "risk_management_agent": ("C1", "C2", "C3", "C15"),
                "technical_analyst": ("C6", "C7", "C8", "C9", "C10", "C15"),
                "fundamentals_analyst": ("C11", "C12", "C15"),
                "news_analyst": ("C13", "C14", "C15"),
            }[role_name]
            content = json.dumps({"tool_requests": [{"tool_id": tool_id, "args": {}} for tool_id in tool_ids]})
        elif role_name == "risk_management_agent":
            content = _p36_risk_section(include_values=True)
        else:
            content = _p36_public_section(role_name)
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=content,
            is_mock=True,
            finish_reason="stop",
        )


def test_p36_pm_loop_appends_typed_synthesis_and_freezes_without_rerun() -> None:
    provider = _P36PmLoopProvider()
    evidence = _public_calculation_evidence(include_eod=True)
    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )
    assert summary.final_synthesis_authored_by == "portfolio_manager_agent"
    assert "**Portfolio Manager synthesis**" in (summary.final_synthesis_markdown or "")
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.pm_synthesis is not None
    assert any(run.prompt_version == P36_PM_PROMPT_VERSION for run in summary.tool_run_artifact.provider_runs)
    calls_before_readback = len(provider.calls)
    SavedToolMediatedRunArtifactRead.model_validate(summary.tool_run_artifact.model_dump(mode="json"))
    assert len(provider.calls) == calls_before_readback
    missing_pm_run = summary.tool_run_artifact.model_dump(mode="python")
    missing_pm_run["provider_runs"] = tuple(
        run for run in missing_pm_run["provider_runs"] if run["role_name"] != "portfolio_manager_agent"
    )
    with pytest.raises(ValueError, match="matching PM provider run"):
        SavedToolMediatedRunArtifactRead.model_validate(missing_pm_run)
    assert [request.role_name for request in provider.calls] == [
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "portfolio_manager_agent",
    ]


def test_p36_pm_receives_accepted_risk_section_with_only_vocabulary_relaxed() -> None:
    provider = _P36PmWithRiskProvider()
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )

    assert summary.final_synthesis_authored_by == "portfolio_manager_agent"
    pm_request = provider.calls[-1]
    assert pm_request.role_name == "portfolio_manager_agent"
    assert pm_request.messages[1].content_kind == "p36_pm_accepted_sections"
    assert "cash calculation" in pm_request.messages[1].content
    assert [request.role_name for request in provider.calls] == [
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "risk_management_agent",
        "risk_management_agent",
        "portfolio_manager_agent",
    ]


def test_p36_all_live_lanes_preflight_freezes_every_role_with_v3_prompts() -> None:
    provider = _P36PmWithRiskProvider()
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=provider,
        p36_risk_live_enabled=True,
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )

    assert summary.tool_run_artifact is not None
    provider_runs = summary.tool_run_artifact.provider_runs
    assert {run.role_name for run in provider_runs} == set(AGENT_TEAM_ROLES)
    assert {run.prompt_version for run in provider_runs} <= {
        "p36-role-analysis-v1",
        "p36-pm-synthesis-v1",
    }


class _LegacyP35Provider:
    provider_name = "legacy-p35-fake"
    model = "legacy-p35-model"

    def __init__(self) -> None:
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=(
                "The saved evidence remains limited to the reviewed package. "
                "Current context was not reviewed for this saved report."
            ),
            is_mock=True,
            finish_reason="stop",
        )


def test_p36_and_legacy_runs_keep_numeric_gate_flags_branch_exclusive() -> None:
    p36_summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=_P36PmWithRiskProvider(),
        p36_risk_live_enabled=True,
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )
    legacy_summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=_LegacyP35Provider(),
        live_provider_enabled=True,
    )

    assert "numeric_consistency_blocked" not in repr(p36_summary)
    assert "live_numeric_mismatch_dropped" not in repr(p36_summary)
    assert "numeric_provenance_blocked" not in repr(legacy_summary)
    assert "live_provider_safety_fallback" not in repr(legacy_summary)


class _P36StarvedPackageProvider:
    provider_name = "p36-starved-package-fake"
    model = "p36-starved-package-model"

    def __init__(self) -> None:
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        if request.role_name == "technical_analyst":
            content = _p36_public_section("technical_analyst") + "\n\nThe frozen technical record includes 999."
        elif request.role_name in {"fundamentals_analyst", "news_analyst"}:
            content = _p36_public_section(request.role_name)
        else:
            payload = _p36_pm_synthesis_payload()
            payload["trust_assessment"] = f"{payload['trust_assessment']} The unreviewed value is 999."
            content = json.dumps(payload)
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=content,
            is_mock=True,
            finish_reason="stop",
        )


def test_p36_starved_package_drops_unproven_digits_but_keeps_honest_public_gaps() -> None:
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=False),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=_P36StarvedPackageProvider(),
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )

    roles = {role.role_name: role for role in summary.role_summaries}
    assert roles["technical_analyst"].live_report_markdown is None
    assert "numeric_provenance_blocked" in roles["technical_analyst"].warning_codes
    assert roles["fundamentals_analyst"].live_report_markdown is not None
    assert roles["news_analyst"].live_report_markdown is not None
    assert "could not be verified" in roles["fundamentals_analyst"].live_report_markdown
    assert "not reviewed" in roles["news_analyst"].live_report_markdown
    assert summary.final_synthesis_authored_by == "deterministic_template"
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.pm_synthesis is None
    assert summary.tool_run_artifact.provider_runs[-1].role_name == "portfolio_manager_agent"
    pm_payload = _p36_pm_synthesis_payload()
    pm_payload["trust_assessment"] = f"{pm_payload['trust_assessment']} The unreviewed value is 999."
    assert _validate_pm_payload(pm_payload) == NUMERIC_PROVENANCE_FLAG


@pytest.mark.parametrize(
    ("unsafe_pm", "unavailable_pm", "expected_line"),
    (
        (True, False, "did not pass its safety checks and was omitted"),
        (False, True, "was not available for this run"),
    ),
)
def test_p36_pm_loop_drops_the_whole_block_to_the_deterministic_floor(
    unsafe_pm: bool,
    unavailable_pm: bool,
    expected_line: str,
) -> None:
    summary = build_tool_mediated_agent_team_summary(
        _public_calculation_evidence(include_eod=True),
        report_generated_at=datetime(2026, 7, 12, tzinfo=UTC),
        llm_provider=_P36PmLoopProvider(unsafe_pm=unsafe_pm, unavailable_pm=unavailable_pm),
        p36_public_live_enabled=True,
        p36_pm_live_enabled=True,
    )
    assert summary.final_synthesis_authored_by == "deterministic_template"
    assert expected_line in (summary.final_synthesis_markdown or "")
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.pm_synthesis is None
