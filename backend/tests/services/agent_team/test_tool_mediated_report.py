from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import pytest

from app.services.agent_team.llm_clients.contracts import (
    LLMProviderMessage,
    LLMProviderFinishReason,
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderStatus,
    register_static_system_prompts,
    registered_static_system_prompts,
)
from app.services.agent_team.llm_clients.factory import ChainedLLMProvider, LLMProviderResolution
from app.services.agent_team.auditing.live_report_gates import (
    ASSERTION_CATEGORY_RE,
    _normalize_category_capture,
    validate_live_report_consistency,
)
from app.services.agent_team.auditing.evidence_auditor import _hard_block_flag
from app.services.agent_team import tool_mediated_report as subject
from app.services.agent_team.orchestration import tool_mediated_runner as runner_subject
from app.services.agent_team.tool_mediated_report import (
    MAX_PLANNER_REPASSES,
    MAX_TOOL_CALLS_PER_ROLE,
    MAX_TOOL_CALLS_TOTAL,
    PLAN_DIMENSIONS,
    PLAN_VERSION,
    PROVIDER_MODE,
    RoleFinding,
    RoleFindingSet,
    audit_findings,
    build_evidence_catalog,
    build_planner_plan,
    build_tool_mediated_agent_team_summary_from_provider_resolution,
    build_tool_mediated_agent_team_summary,
    run_tool_mediated_agent_team,
    usable_content_by_role,
)
from app.services.agent_team.tools import ToolResult, default_tool_registry, validate_tool_payload
from app.services.market_data.eod_history import market_context_execution_context_for_client
from app.schemas.reports import SavedAgentTeamSummaryRead, SavedEvidenceSectionRead
from tests.services.agent_team.test_tools import (
    _evidence_package,
    _fred_economic_awareness_section,
    _public_company_profile_section,
    _sec_recent_filings_section,
    _section,
)


pytestmark = [pytest.mark.unit]


EXPECTED_USABLE_CONTENT = {
    "fundamentals_analyst": frozenset({"trade_intent_summary", "public_company_profile"}),
    "news_analyst": frozenset(
        {"trade_intent_summary", "economic_awareness_snapshot", "public_events_calendar"}
    ),
    "technical_analyst": frozenset({"trade_intent_summary", "market_quote_freshness", "public_market_context"}),
    "risk_management_agent": frozenset(
        {
            "trade_intent_summary",
            "scope_state",
            "actionability",
            "freshness",
            "portfolio_impact_summary",
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
            "freshness",
            "portfolio_impact_summary",
            "concentration_risk_drift",
            "liquidity_collateral_caveats",
            "options_exposure_summary",
            "market_quote_freshness",
            "economic_awareness_snapshot",
            "public_events_calendar",
            "public_company_profile",
            "public_market_context",
        }
    ),
}


EXPECTED_PLAN = {
    "fundamentals_analyst": ("trade_intent_summary", "public_company_profile"),
    "news_analyst": ("trade_intent_summary", "economic_awareness_context", "sec_recent_filings_metadata"),
    "technical_analyst": ("trade_intent_summary", "market_quote_freshness", "market_context_snapshot"),
    "risk_management_agent": (
        "trade_intent_summary",
        "portfolio_scope_context",
        "deterministic_review_findings",
        "broker_snapshot_freshness",
        "market_quote_freshness",
        "market_context_snapshot",
        "evidence_gap_inspector",
    ),
    "portfolio_manager_agent": (),
}


def _run_state(evidence=None):
    return run_tool_mediated_agent_team(
        evidence or _evidence_package(),
        registry=default_tool_registry(),
    )


def _role_summary(summary, role_name: str):
    return next(role for role in summary.role_summaries if role.role_name == role_name)


def _valid_live_report(role_name: str, *, row_value: str = "available") -> str:
    if role_name == "technical_analyst":
        return (
            f"Saved market context was {row_value} in the role envelopes. "
            "Freshness and availability categories help frame whether reviewed values may have aged."
        )
    if role_name == "risk_management_agent":
        return (
            "Saved scope caveats remain important context for manual review. "
            "Re-verify the exposure math in the reviewed app before comparing with current broker screens."
        )
    return "Reviewed public context is available as deterministic background."


class _FakeLiveProvider:
    provider_name = "fake_live_provider"
    model = "fake-live-model"

    def __init__(
        self,
        *,
        status_by_role: dict[str, LLMProviderStatus] | None = None,
        content_by_role: dict[str, str] | None = None,
        finish_reason_by_role: dict[str, LLMProviderFinishReason | None] | None = None,
    ) -> None:
        self.status_by_role = dict(status_by_role or {})
        self.content_by_role = dict(content_by_role or {})
        self.finish_reason_by_role = dict(finish_reason_by_role or {})
        self.calls: list[LLMProviderRequest] = []

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        self.calls.append(request)
        status = self.status_by_role.get(request.role_name, "ok")
        if status != "ok":
            return LLMProviderResponse(
                request_id=request.request_id,
                role_name=request.role_name,
                status=status,
                provider=self.provider_name,
                model=self.model,
                prompt_version=request.prompt_version,
                content_markdown=None,
                is_mock=False,
                error_code=status,
                error_message="Provider unavailable; deterministic evidence remains available.",
                metadata={"safe_partial_output": "true"},
            )
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=self.content_by_role.get(
                request.role_name,
                _valid_live_report(request.role_name),
            ),
            is_mock=False,
            finish_reason=self.finish_reason_by_role.get(request.role_name),
            metadata={"safe_partial_output": "false"},
        )


class _UnsafeLiveProvider(_FakeLiveProvider):
    def __init__(self, content: str) -> None:
        super().__init__()
        self.content = content

    def complete(self, request: LLMProviderRequest):  # noqa: ANN201 - deliberately bypasses response dataclass validation.
        self.calls.append(request)
        return SimpleNamespace(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=self.content,
            is_mock=False,
            metadata={},
        )


class _TimeoutLiveProvider(_FakeLiveProvider):
    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        self.calls.append(request)
        raise TimeoutError("synthetic timeout")


def _agent_safe_results_for_public_roles(state) -> list[ToolResult]:
    return [
        result
        for result in state.tool_results
        if result.role_name in {"fundamentals_analyst", "news_analyst", "technical_analyst"}
        and result.evidence_tier == "agent_safe"
    ]


def _result(
    *,
    role_name: str,
    evidence_refs: tuple[str, ...],
    availability: str = "available",
) -> ToolResult:
    return ToolResult(
        tool_name="trade_intent_summary",
        role_name=role_name,
        status="ok",
        evidence_tier="public",
        data_mode="public",
        availability=availability,
        evidence_refs=evidence_refs,
        summary_payload={"summary": "Synthetic reviewed evidence result."},
    )


def _finding_set(role_name: str, finding: RoleFinding) -> RoleFindingSet:
    return RoleFindingSet(
        role_name=role_name,
        role_status="completed",
        findings=(finding,),
        warning_codes=(),
    )


def _findings_by_role(state) -> dict[str, tuple[str, ...]]:
    return {item.role_name: tuple(finding.claim_text for finding in item.findings) for item in state.audited_findings}


def _finding_counts_by_role(state) -> dict[str, int]:
    return {item.role_name: len(item.findings) for item in state.audited_findings}


class _FakeFmpEodClient:
    def __init__(self, rows) -> None:
        self.rows = tuple(rows)
        self.calls: list[str] = []

    def fetch_eod_history(self, *, symbol: str, limit: int = 260):
        self.calls.append(symbol)
        return self.rows


def _linear_eod_rows_for_runner(count: int):
    start = date(2025, 1, 1)
    rows = []
    for index in range(count):
        close = Decimal(index + 1)
        rows.append(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": str(close),
                "high": str(close + Decimal("1")),
                "low": str(close - Decimal("1")),
                "close": str(close),
                "volume": 1001 + index,
            }
        )
    return tuple(reversed(rows))


def _technical_live_report_with_market_values(*, latest_close: str = "260.0", date_label: str = "2025-09-17") -> str:
    return (
        f"FMP end-of-day context was fresh as of {date_label}. "
        f"Latest close {latest_close}, SMA200 160.5, and RSI14 100.0 were supplied as backend-computed context."
    )


def _technical_live_report_with_category_sentence(sentence: str) -> str:
    return f"{sentence} Unavailable context remains not available."


def test_u1_usable_content_by_role_matches_pinned_spec() -> None:
    assert usable_content_by_role() == EXPECTED_USABLE_CONTENT


def test_c1_catalog_exposes_safe_sections_and_rejects_private_tokens() -> None:
    catalog = build_evidence_catalog(_evidence_package(), default_tool_registry())
    section_by_key = {section.section_key: section for section in catalog.sections}

    assert catalog.locked_question == "what_would_be_ignored"
    assert section_by_key["public_company_profile"].evidence_tier == "public"
    assert section_by_key["liquidity_collateral_caveats"].evidence_tier == "agent_safe"
    assert section_by_key["before_after_portfolio_impact"].availability == "not_available"

    with pytest.raises(ValueError, match="raw_payload"):
        subject.EvidenceCatalogSection(
            section_key="raw_payload",
            availability="available",
            evidence_tier="public",
            freshness_category=None,
            caveat_codes=(),
        )


def test_p1_to_p5_planner_matches_pinned_plan_and_limits() -> None:
    plan = build_planner_plan(build_evidence_catalog(_evidence_package(), default_tool_registry()))

    assert plan.plan_version == PLAN_VERSION
    assert plan.dimensions == PLAN_DIMENSIONS
    actual = {item.role_name: tuple(request.tool_name for request in item.tool_requests) for item in plan.role_plan}
    assert actual == EXPECTED_PLAN
    assert sum(len(item.tool_requests) for item in plan.role_plan) == 15
    assert sum(len(item.tool_requests) for item in plan.role_plan) <= MAX_TOOL_CALLS_TOTAL
    assert all(len(item.tool_requests) <= MAX_TOOL_CALLS_PER_ROLE for item in plan.role_plan)
    assert MAX_PLANNER_REPASSES == 1
    assert [role for role, tools in actual.items() if "evidence_gap_inspector" in tools] == ["risk_management_agent"]


def test_r1_to_r4_role_results_keep_public_roles_public_and_news_degraded() -> None:
    state = _run_state()
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    assert _agent_safe_results_for_public_roles(state) == []
    assert summary.report_status == "full_agent_report"
    assert summary.provider_mode == PROVIDER_MODE
    assert summary.run_status == "completed"
    assert _role_summary(summary, "fundamentals_analyst").role_status == "completed"
    assert _role_summary(summary, "fundamentals_analyst").evidence_references == (
        "trade_intent_summary",
        "public_company_profile",
    )
    news = _role_summary(summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary",)
    assert news.warning_codes == (
        "fred_economic_awareness_not_available",
        "sec_edgar_recent_filings_not_available",
    )
    assert "public_company_profile" not in _role_summary(summary, "news_analyst").evidence_references
    assert "public_company_profile" not in _role_summary(summary, "technical_analyst").evidence_references
    assert "public_news_snapshot" not in summary.evidence_references


def test_fred_economic_awareness_context_can_complete_news_role_without_cnn_or_fmp() -> None:
    evidence = _evidence_package(economic_awareness_snapshot=_fred_economic_awareness_section())

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    news = _role_summary(summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary", "economic_awareness_snapshot")
    assert "fred_economic_awareness_context_only" in news.warning_codes
    assert "Consumer Price Index release (2026-07-15)" in (news.summary_markdown or "")
    assert "Federal Open Market Committee calendar (2026-07-29)" in (news.summary_markdown or "")
    assert "economic_awareness_snapshot" in summary.evidence_references
    assert "market_mood_snapshot" not in summary.evidence_references
    assert "public_news_snapshot" not in summary.evidence_references
    pm = _role_summary(summary, "portfolio_manager_agent")
    assert "FRED macro calendar metadata was included as background only." in (pm.summary_markdown or "")
    assert "FRED macro calendar metadata was included as economic context only." in (
        summary.final_synthesis_markdown or ""
    )
    assert summary.tool_run_artifact is not None
    fred_results = tuple(
        result
        for result in summary.tool_run_artifact.tool_results
        if result.tool_name == "economic_awareness_context"
    )
    assert fred_results
    assert all(result.source_key == "fred_macro_calendar_metadata" for result in fred_results)
    rendered = repr(summary.model_dump(mode="json")).lower()
    assert "cnn-derived" not in rendered
    assert "fmp economic calendar" not in rendered
    assert "raw_payload" not in rendered


def test_fred_economic_awareness_without_safe_rows_uses_availability_sentence() -> None:
    section = _fred_economic_awareness_section().model_copy(
        update={"detail_labels": ("actual_label: 3.0", "forecast_label: 2.9")}
    )
    evidence = _evidence_package(economic_awareness_snapshot=section)

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    news = _role_summary(summary, "news_analyst")
    assert "FRED macro calendar metadata was checked and is available as economic context only." in (
        news.summary_markdown or ""
    )
    rendered = repr(summary.model_dump(mode="json")).lower()
    assert "actual_label" not in rendered
    assert "forecast_label" not in rendered


def test_fred_economic_awareness_unavailable_degrades_to_named_gap() -> None:
    evidence = _evidence_package(economic_awareness_snapshot=_fred_economic_awareness_section(availability="not_available"))

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    news = _role_summary(summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary",)
    assert "fred_economic_awareness_not_available" in news.warning_codes
    assert "FRED macro calendar metadata was not available or not reviewed" in (news.summary_markdown or "")
    assert "economic_awareness_snapshot" not in summary.evidence_references


def test_sec_recent_filings_metadata_can_complete_news_role_without_public_news_provider() -> None:
    evidence = _evidence_package(public_events_calendar=_sec_recent_filings_section())

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    news = _role_summary(summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary", "public_events_calendar")
    assert "sec_edgar_recent_filings_metadata_only" in news.warning_codes
    assert "Form 8-K (Filed 2026-05-29)" in (news.summary_markdown or "")
    assert "filref_recent_event_001" not in (news.summary_markdown or "")
    assert "public_events_calendar" in summary.evidence_references
    assert "public_news_snapshot" not in summary.evidence_references
    pm = _role_summary(summary, "portfolio_manager_agent")
    assert "Company-event metadata was included as background only." in (pm.summary_markdown or "")
    assert "Company-event metadata was included as background only." in (summary.final_synthesis_markdown or "")
    assert summary.tool_run_artifact is not None
    edgar_results = tuple(
        result
        for result in summary.tool_run_artifact.tool_results
        if result.tool_name == "sec_recent_filings_metadata"
    )
    assert edgar_results
    assert all(result.source_key == "sec_edgar_recent_filings" for result in edgar_results)
    rendered = repr(summary.model_dump(mode="json")).lower()
    assert "newsapi" not in rendered
    assert "source_url" not in rendered
    assert "filing_text" not in rendered
    assert "raw_payload" not in rendered


def test_sec_recent_filings_unavailable_degrades_to_trade_intent_gap_only() -> None:
    evidence = _evidence_package(public_events_calendar=_sec_recent_filings_section(availability="not_available"))

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    news = _role_summary(summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary",)
    assert "sec_edgar_recent_filings_not_available" in news.warning_codes
    assert "not available or not reviewed" in (news.summary_markdown or "")
    assert "public_events_calendar" not in summary.evidence_references


def test_r5_missing_public_evidence_degrades_public_roles_without_agent_safe_leak() -> None:
    evidence = _evidence_package().model_copy(update={"public_evidence": None})
    summary = build_tool_mediated_agent_team_summary(evidence, report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert _role_summary(summary, "fundamentals_analyst").role_status == "skipped"
    assert _role_summary(summary, "fundamentals_analyst").evidence_references == ("trade_intent_summary",)
    assert _role_summary(summary, "news_analyst").role_status == "completed"
    assert _role_summary(summary, "news_analyst").evidence_references == ("trade_intent_summary",)
    assert _role_summary(summary, "technical_analyst").role_status == "completed"


def test_limited_public_company_profile_completes_with_limited_caveat() -> None:
    evidence = _evidence_package(public_company_profile=_public_company_profile_section(availability="limited"))
    summary = build_tool_mediated_agent_team_summary(evidence, report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))
    fundamentals = _role_summary(summary, "fundamentals_analyst")

    assert fundamentals.role_status == "completed"
    assert fundamentals.evidence_references == ("trade_intent_summary", "public_company_profile")
    assert "public_evidence_limited" in fundamentals.warning_codes


def test_a1_a3_a8_auditor_filters_unsupported_boundary_and_unavailable_refs() -> None:
    finding_sets = (
        _finding_set(
            "fundamentals_analyst",
            RoleFinding(
                finding_type="missing_context",
                claim_text="This unsupported claim should be removed.",
                evidence_refs=("scope_state", "public_company_profile", "market_quote_freshness"),
            ),
        ),
    )
    results_by_role = {
        "fundamentals_analyst": (
            _result(role_name="fundamentals_analyst", evidence_refs=("scope_state",)),
            _result(role_name="fundamentals_analyst", evidence_refs=("public_company_profile",), availability="not_available"),
            _result(role_name="fundamentals_analyst", evidence_refs=("market_quote_freshness",), availability="available"),
        )
    }
    auditor, audited = audit_findings(
        finding_sets,
        results_by_role,
        {"fundamentals_analyst": frozenset({"scope_state", "public_company_profile", "market_quote_freshness"})},
    )

    assert audited[0].findings == ()
    assert auditor.repass_triggered is True
    assert set(auditor.dropped_claims) == {"citable_boundary_filtered", "unavailable_ref_filtered"}


@pytest.mark.parametrize(
    ("claim_text", "expected_flag"),
    (
        ("This includes provider_account_id_secret.", "private_leak_blocked"),
        ("You should buy this immediately.", "advice_wording_blocked"),
        ("This invents a $100 target.", "invented_metric_blocked"),
        ("The 8-K signals a bullish catalyst.", "sec_interpretation_blocked"),
        ("The filing states revenue rose.", "sec_interpretation_blocked"),
        ("Raw SEC file aapl-20260601.pdf leaked.", "source_leak_blocked"),
        ("The CPI release suggests a bullish macro signal.", "fred_interpretation_blocked"),
        ("A likely rate cut makes this an urgent market move.", "fred_interpretation_blocked"),
    ),
)
def test_a4_to_a6_auditor_drops_private_advice_and_invented_number_findings(
    claim_text: str,
    expected_flag: str,
) -> None:
    finding_sets = (
        _finding_set(
            "risk_management_agent",
            RoleFinding(
                finding_type="ignored_risk",
                claim_text=claim_text,
                evidence_refs=("trade_intent_summary",),
            ),
        ),
    )

    auditor, audited = audit_findings(
        finding_sets,
        {"risk_management_agent": (_result(role_name="risk_management_agent", evidence_refs=("trade_intent_summary",)),)},
        {"risk_management_agent": frozenset({"trade_intent_summary"})},
    )

    assert audited[0].findings == ()
    assert auditor.repass_triggered is False
    assert expected_flag in auditor.eval_flags


def test_sec_recent_filings_role_boundary_filters_non_news_role_refs() -> None:
    finding_sets = (
        _finding_set(
            "fundamentals_analyst",
            RoleFinding(
                finding_type="missing_context",
                claim_text="SEC event metadata was incorrectly routed to fundamentals.",
                evidence_refs=("public_events_calendar",),
            ),
        ),
    )
    results_by_role = {
        "fundamentals_analyst": (
            _result(role_name="fundamentals_analyst", evidence_refs=("public_events_calendar",)),
        )
    }

    auditor, audited = audit_findings(
        finding_sets,
        results_by_role,
        {"fundamentals_analyst": frozenset({"public_events_calendar"})},
    )

    assert audited[0].findings == ()
    assert "citable_boundary_filtered" in auditor.dropped_claims


def test_sec_interpretation_guard_does_not_block_non_sec_freshness_wording() -> None:
    finding_sets = (
        _finding_set(
            "technical_analyst",
            RoleFinding(
                finding_type="missing_context",
                claim_text="Market quote freshness is time-sensitive context for manual review.",
                evidence_refs=("market_quote_freshness",),
            ),
        ),
        _finding_set(
            "risk_management_agent",
            RoleFinding(
                finding_type="missing_context",
                claim_text="Market freshness should be reviewed before earnings as part of manual context checks.",
                evidence_refs=("market_quote_freshness",),
            ),
        ),
    )
    results_by_role = {
        "technical_analyst": (_result(role_name="technical_analyst", evidence_refs=("market_quote_freshness",)),),
        "risk_management_agent": (_result(role_name="risk_management_agent", evidence_refs=("market_quote_freshness",)),),
    }

    auditor, audited = audit_findings(
        finding_sets,
        results_by_role,
        {
            "technical_analyst": frozenset({"market_quote_freshness"}),
            "risk_management_agent": frozenset({"market_quote_freshness"}),
        },
    )

    assert all(item.findings for item in audited)
    assert "sec_interpretation_blocked" not in auditor.eval_flags
    assert "fred_interpretation_blocked" not in auditor.eval_flags


def test_a7_contradiction_becomes_open_question_and_one_repass() -> None:
    finding_sets = (
        _finding_set(
            "technical_analyst",
            RoleFinding(
                finding_type="missing_context",
                claim_text="Market quote freshness has a structured positive freshness signal.",
                evidence_refs=("market_quote_freshness",),
                caveat_codes=("fresh",),
            ),
        ),
        _finding_set(
            "risk_management_agent",
            RoleFinding(
                finding_type="missing_context",
                claim_text="Market quote freshness has a structured negative freshness signal.",
                evidence_refs=("market_quote_freshness",),
                caveat_codes=("stale",),
            ),
        ),
    )
    results_by_role = {
        "technical_analyst": (_result(role_name="technical_analyst", evidence_refs=("market_quote_freshness",)),),
        "risk_management_agent": (_result(role_name="risk_management_agent", evidence_refs=("market_quote_freshness",)),),
    }

    auditor, _audited = audit_findings(
        finding_sets,
        results_by_role,
        {
            "technical_analyst": frozenset({"market_quote_freshness"}),
            "risk_management_agent": frozenset({"market_quote_freshness"}),
        },
    )

    assert auditor.repass_triggered is True
    assert auditor.contradictions
    assert "contradiction_open_question" in auditor.eval_flags


def test_repass_is_capped_at_one_and_can_repair_citation_failure() -> None:
    calls: list[str] = []

    def override(role_name: str, finding_set: RoleFindingSet) -> RoleFindingSet:
        if role_name != "fundamentals_analyst":
            return finding_set
        calls.append(role_name)
        ref = "never_received" if len(calls) == 1 else "public_company_profile"
        return RoleFindingSet(
            role_name=role_name,
            role_status="completed",
            findings=(
                RoleFinding(
                    finding_type="missing_context",
                    claim_text="Reviewed public company profile context is background.",
                    evidence_refs=(ref,),
                ),
            ),
            warning_codes=(),
        )

    state = run_tool_mediated_agent_team(
        _evidence_package(),
        registry=default_tool_registry(),
        role_finding_override=override,
    )

    assert calls == ["fundamentals_analyst", "fundamentals_analyst"]
    assert state.auditor.repass_triggered is True
    assert "unsupported_claim" in state.auditor.dropped_claims
    fundamentals = next(item for item in state.audited_findings if item.role_name == "fundamentals_analyst")
    assert fundamentals.findings[0].evidence_refs == ("public_company_profile",)


def test_s1_to_s3_end_to_end_summary_is_valid_byte_stable_and_no_gaps_cited() -> None:
    generated_at = datetime(2026, 6, 1, tzinfo=UTC)
    first = build_tool_mediated_agent_team_summary(_evidence_package(), report_generated_at=generated_at)
    second = build_tool_mediated_agent_team_summary(_evidence_package(), report_generated_at=generated_at)

    assert first == second
    assert first.report_status == "full_agent_report"
    assert first.final_synthesis_authored_by == "deterministic_template"
    assert "What you would be ignoring" in (first.final_synthesis_markdown or "")
    assert "buy" not in repr(first.model_dump(mode="json")).lower()
    assert "safe to trade" not in repr(first.model_dump(mode="json")).lower()
    assert "before_after_portfolio_impact" not in first.evidence_references
    assert "public_news_snapshot" not in first.evidence_references


def test_p34a_t9_deterministic_specificity_names_freshness_scope_gaps_and_inventory() -> None:
    evidence = _evidence_package().model_copy(
        update={
            "freshness": _evidence_package().freshness.model_copy(
                update={
                    "broker_snapshot_freshness_label": "Broker snapshot is stale",
                    "market_quote_freshness_label": "Market quotes are stale",
                }
            ),
            "market_quote_freshness": _section(
                "market_quote_freshness",
                summary_label="Market quote freshness is unknown",
            ),
        }
    )

    summary = build_tool_mediated_agent_team_summary(evidence, report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    risk = _role_summary(summary, "risk_management_agent")
    technical = _role_summary(summary, "technical_analyst")
    assert "Saved broker snapshot freshness is categorized as stale." in (risk.summary_markdown or "")
    assert "Market quote freshness is categorized as unknown." in (risk.summary_markdown or "")
    assert "account-level feasibility was not evaluated" in (risk.summary_markdown or "")
    assert "scope is limited to the selected portfolio context" in (risk.summary_markdown or "")
    assert "before/after portfolio impact" in (risk.summary_markdown or "")
    assert "public fundamentals snapshot" in (risk.summary_markdown or "")
    assert "Market quote freshness is categorized as unknown" in (technical.summary_markdown or "")
    assert "saved quotes are not live prices" in (technical.summary_markdown or "")
    assert "## Risk and scope notes" in (summary.final_synthesis_markdown or "")
    assert "Unavailable or not-reviewed context:" in (summary.final_synthesis_markdown or "")
    assert "before/after portfolio impact" in (summary.final_synthesis_markdown or "")


def test_t4_tool_run_artifact_freezes_plan_results_auditor_and_citation_graph() -> None:
    generated_at = datetime(2026, 6, 1, tzinfo=UTC)
    summary = build_tool_mediated_agent_team_summary(_evidence_package(), report_generated_at=generated_at)
    artifact = summary.tool_run_artifact

    assert artifact is not None
    assert artifact.artifact_schema_version == "p33a_tool_run_freeze_v1"
    assert artifact.provider_mode == PROVIDER_MODE
    assert artifact.plan_version == PLAN_VERSION
    assert artifact.audit_version == subject.AUDIT_VERSION
    assert artifact.locked_question == "what_would_be_ignored"
    assert artifact.tool_result_count == 15
    assert len(artifact.tool_results) == 15
    assert artifact.frozen_at == generated_at
    assert artifact.synthesis_evidence_references == summary.evidence_references
    assert artifact.warning_codes == summary.warning_codes
    assert {role.role_name for role in artifact.role_plan} == {
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "risk_management_agent",
        "portfolio_manager_agent",
    }
    assert artifact.auditor.dropped_claims == ()
    assert artifact.auditor.repass_triggered is False
    gap_result = next(result for result in artifact.tool_results if result.tool_name == "evidence_gap_inspector")
    assert gap_result.evidence_refs == ("trade_intent_summary", "scope_state")
    assert "before_after_portfolio_impact" in gap_result.summary_payload["unavailable_evidence_refs"]
    assert "payload" not in gap_result.model_dump(mode="python")


def test_t4_tool_run_artifact_round_trips_through_saved_summary_json() -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    round_tripped = SavedAgentTeamSummaryRead.model_validate(summary.model_dump(mode="json"))

    assert round_tripped.model_dump(mode="json") == summary.model_dump(mode="json")
    assert round_tripped.tool_run_artifact is not None
    assert round_tripped.tool_run_artifact.tool_result_count == 15


def test_fmp_eod_market_context_freezes_values_and_round_trips_without_refetch() -> None:
    client = _FakeFmpEodClient(_linear_eod_rows_for_runner(260))
    context = market_context_execution_context_for_client(
        client,
        collected_at=datetime(2025, 9, 18, tzinfo=UTC),
    )
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        market_context=context,
    )

    assert client.calls == ["XYZ"]
    assert summary.tool_run_artifact is not None
    market_results = [
        result
        for result in summary.tool_run_artifact.tool_results
        if result.tool_name == "market_context_snapshot" and result.status == "ok"
    ]
    assert len(market_results) == 2
    assert {result.role_name for result in market_results} == {"technical_analyst", "risk_management_agent"}
    for result in market_results:
        assert result.source_key == "fmp_eod_history"
        assert result.evidence_refs == ("public_market_context",)
        assert result.summary_payload["values"]["latest_close"] == 260.0
        assert result.summary_payload["indicators"]["sma200"] == 160.5
        assert "eod_not_live_prices" in result.caveat_codes
    assert "public_market_context" in summary.evidence_references
    assert "FMP end-of-day market context was included" in (summary.final_synthesis_markdown or "")

    round_tripped = SavedAgentTeamSummaryRead.model_validate(summary.model_dump(mode="json"))

    assert round_tripped.model_dump(mode="json") == summary.model_dump(mode="json")
    assert client.calls == ["XYZ"]


def test_t4_legacy_summary_without_tool_run_artifact_remains_valid() -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    payload = summary.model_dump(mode="json")
    payload.pop("tool_run_artifact")

    legacy = SavedAgentTeamSummaryRead.model_validate(payload)

    assert legacy.tool_run_artifact is None
    assert legacy.report_status == "full_agent_report"


@pytest.mark.parametrize(
    ("summary_payload", "expected"),
    (
        ({"nested": "provider_account_id_secret"}, "provider_account_id"),
        ({"summary": "You should buy this."}, "you should"),
        ({"summary": "Invented target $100.00"}, "generated metric"),
        ({"source_url": "reviewed source label only"}, "source_url"),
        ({"url": "reviewed source label only"}, "url"),
        ({"nested": {"urls": ("reviewed source label only",)}}, "urls"),
    ),
)
def test_t4_tool_run_artifact_rejects_unsafe_frozen_tool_payloads(
    summary_payload: dict[str, str],
    expected: str,
) -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    payload = summary.model_dump(mode="python")
    assert payload["tool_run_artifact"] is not None
    payload["tool_run_artifact"]["tool_results"][0]["summary_payload"] = summary_payload

    with pytest.raises(ValueError, match=expected):
        SavedAgentTeamSummaryRead.model_validate(payload)


def test_e2_blocked_actionability_uses_existing_deterministic_draft() -> None:
    evidence = _evidence_package().model_copy(
        update={
            "actionability": _evidence_package().actionability.model_copy(
                update={"review_actionability_status": "blocked_unstable_position_truth"}
            )
        }
    )

    summary = build_tool_mediated_agent_team_summary(evidence, report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert summary.report_status == "deterministic_draft"
    assert summary.provider_mode == "deterministic_template"
    assert summary.tool_run_artifact is None


def test_e5_unavailable_refs_and_gap_refs_are_not_cited() -> None:
    summary = build_tool_mediated_agent_team_summary(_evidence_package(), report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert "before_after_portfolio_impact" not in summary.evidence_references
    assert "economic_awareness_snapshot" not in summary.evidence_references
    assert "market_mood_snapshot" not in summary.evidence_references
    assert "public_news_snapshot" not in summary.evidence_references
    assert any(code.endswith("_unavailable") for code in _role_summary(summary, "risk_management_agent").warning_codes)


def test_unavailable_deterministic_section_is_filtered_without_validation_fallback() -> None:
    evidence = _evidence_package().model_copy(
        update={
            "portfolio_impact_summary": _section(
                "portfolio_impact_summary",
                availability="not_available",
                summary_label="Portfolio impact was not available in saved evidence.",
            )
        }
    )

    summary = build_tool_mediated_agent_team_summary(evidence, report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert summary.report_status == "full_agent_report"
    assert summary.run_status == "completed"
    assert "portfolio_impact_summary" not in summary.evidence_references
    assert "portfolio_impact_summary" not in _role_summary(summary, "risk_management_agent").evidence_references


def test_e6_validation_backstop_falls_back_to_validation_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    # _synthesis_markdown lives in (and is called from) the relocated runner
    # module after P34A-T11E; patch it there so the injected unsafe synthesis
    # actually reaches the validation backstop.
    from app.services.agent_team.orchestration import tool_mediated_runner

    monkeypatch.setattr(
        tool_mediated_runner,
        "_synthesis_markdown",
        lambda *_args, **_kwargs: "You should buy because this is safe to trade.",
    )

    summary = build_tool_mediated_agent_team_summary(_evidence_package(), report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert summary.report_status == "validation_failed"
    assert summary.run_status == "failed"
    assert "you should" not in repr(summary.model_dump(mode="json")).lower()


def test_p34a_live_provider_gate_is_disabled_by_default_even_with_provider() -> None:
    provider = _FakeLiveProvider()
    generated_at = datetime(2026, 6, 1, tzinfo=UTC)
    deterministic = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=generated_at,
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=generated_at,
        llm_provider=provider,
    )

    assert provider.calls == []
    assert summary.provider_mode == "tool_mediated_mock"
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.provider_mode == "tool_mediated_mock"
    assert summary.model_dump(mode="json") == deterministic.model_dump(mode="json")


def test_p34a_provider_factory_resolution_controls_live_gate() -> None:
    provider = _FakeLiveProvider()
    live_resolution = LLMProviderResolution(
        provider=provider,
        status="ok",
        provider_name=provider.provider_name,
        model=provider.model,
    )

    live_summary = build_tool_mediated_agent_team_summary_from_provider_resolution(
        _evidence_package(),
        provider_resolution=live_resolution,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    assert provider.calls
    assert live_summary.provider_mode == "tool_mediated_live"

    mock_provider = _FakeLiveProvider()
    mock_resolution = LLMProviderResolution(
        provider=mock_provider,
        status="ok",
        provider_name="mock",
        model=mock_provider.model,
    )

    mock_summary = build_tool_mediated_agent_team_summary_from_provider_resolution(
        _evidence_package(),
        provider_resolution=mock_resolution,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    assert mock_provider.calls == []
    assert mock_summary.provider_mode == "tool_mediated_mock"


def test_p34a_live_provider_success_uses_sanitized_tool_result_envelopes_only() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _valid_live_report("technical_analyst"),
            "risk_management_agent": _valid_live_report("risk_management_agent"),
        }
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    assert summary.provider_mode == "tool_mediated_live"
    assert summary.report_status == "full_agent_report"
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.provider_mode == "tool_mediated_live"
    assert summary.tool_run_artifact.tool_result_count == 15
    assert summary.tool_run_artifact.provider_runs
    assert {request.role_name for request in provider.calls} == {
        "technical_analyst",
        "risk_management_agent",
    }
    assert {run.role_name for run in summary.tool_run_artifact.provider_runs} == {
        "technical_analyst",
        "risk_management_agent",
    }
    assert all(run.provider == "fake_live_provider" for run in summary.tool_run_artifact.provider_runs)
    assert all(run.model == "fake-live-model" for run in summary.tool_run_artifact.provider_runs)
    assert all(run.prompt_version == "p35-role-note-v2" for run in summary.tool_run_artifact.provider_runs)
    assert all(run.status == "ok" for run in summary.tool_run_artifact.provider_runs)
    fundamentals = _role_summary(summary, "fundamentals_analyst")
    fundamentals_summary = fundamentals.summary_markdown or ""
    assert "Reviewed public company profile context is background that could be overlooked." in fundamentals_summary
    assert fundamentals.live_report_markdown is None
    assert fundamentals.evidence_references == (
        "trade_intent_summary",
        "public_company_profile",
    )
    technical = _role_summary(summary, "technical_analyst")
    risk = _role_summary(summary, "risk_management_agent")
    assert technical.live_report_markdown == _valid_live_report("technical_analyst")
    assert risk.live_report_markdown == _valid_live_report("risk_management_agent")
    assert "live_provider_reasoning_used" in technical.warning_codes
    assert "live_provider_reasoning_used" in risk.warning_codes
    rendered_requests = repr(tuple(request.messages for request in provider.calls)).lower()
    assert "summary_payload" not in rendered_requests
    assert "scope':" not in rendered_requests
    assert "cash_secured_put" not in rendered_requests
    assert "buying_power" not in rendered_requests
    assert "raw_payload" not in rendered_requests
    assert "account_id" not in rendered_requests
    for request in provider.calls:
        assert request.request_id.startswith("p35_")
        assert request.messages[0].content in runner_subject.LIVE_ROLE_SYSTEM_PROMPTS
        validate_tool_payload({"content": request.messages[1].content}, label="captured live prompt user envelope")


def test_manual_confirmation_actionability_still_reaches_fake_live_role_path() -> None:
    evidence = _evidence_package()
    evidence = evidence.model_copy(
        update={
            "actionability": evidence.actionability.model_copy(
                update={
                    "review_actionability_status": "manual_confirmation_required",
                    "actionability_label": "Manual confirmation required",
                }
            )
        }
    )
    provider = _FakeLiveProvider()

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    assert summary.report_status == "full_agent_report"
    assert {request.role_name for request in provider.calls} == {
        "technical_analyst",
        "risk_management_agent",
    }


def test_p35_t7c_v2_system_prompts_are_registered_verbatim_and_current_live_roles_use_them() -> None:
    provider = _FakeLiveProvider()
    state = run_tool_mediated_agent_team(_evidence_package(), registry=default_tool_registry())
    role_results = {
        role_name: tuple(result for result in state.tool_results if result.role_name == role_name)
        for role_name in runner_subject.LIVE_ROLE_PROMPT_BLOCKS
    }
    finding_sets = {finding.role_name: finding for finding in state.audited_findings}
    shared_constraint_phrases = (
        "what would a manual reviewer\nacting right now overlook in the saved evidence?",
        "exactly one note of two to four plain-language sentences.",
        "Plain prose only — no headings, no tables, no lists, no bullets, no field",
        "envelope value, or write no number at all. Never compute, convert,",
        "only exactly as the envelopes categorize each item.",
        'say "not reviewed" or "not available" in plain words; caveat codes',
        "not in digits, not in words, not by comparison.",
        "no advice, no action instructions other than",
    )
    role_markers = {
        "technical_analyst": '"Market context" heading',
        "risk_management_agent": '"Risk and scope notes" heading',
        "fundamentals_analyst": '"Company context" heading',
        "news_analyst": '"Events and filings context" heading',
    }

    assert runner_subject.LIVE_ROLE_SYSTEM_PROMPTS.issubset(registered_static_system_prompts())
    for role_name, block in runner_subject.LIVE_ROLE_PROMPT_BLOCKS.items():
        finding_set = finding_sets[role_name]
        evidence_refs = runner_subject._ordered_refs(runner_subject._union_refs(finding_set.findings))
        request = runner_subject._live_provider_request(
            role_name,
            role_results[role_name],
            evidence_refs=evidence_refs,
            provider=provider,
        )

        assert request.request_id == f"p35_{role_name}_tool_mediated"
        assert request.prompt_version == "p35-role-note-v2"
        assert request.messages[0].content == runner_subject._render_live_role_system_prompt(role_name)
        assert block in request.messages[0].content
        assert role_markers[role_name] in request.messages[0].content
        assert all(phrase in request.messages[0].content for phrase in shared_constraint_phrases)
        assert request.messages[1].content == repr(
            {
                "allowed_evidence_refs": evidence_refs,
                "tool_result_envelopes": tuple(
                    runner_subject._prompt_tool_result_envelope(result) for result in role_results[role_name]
                ),
                "output_rule": "one connective note only; two to four sentences; no heading, table, list, symbol, or portfolio magnitude",
            }
        )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )
    assert {request.role_name for request in provider.calls} == {
        "technical_analyst",
        "risk_management_agent",
    }
    assert _role_summary(summary, "fundamentals_analyst").live_report_markdown is None
    assert _role_summary(summary, "news_analyst").live_report_markdown is None


def test_p35_t7c_static_prompt_registry_pins_all_four_exact_rendered_prompts() -> None:
    prompt_digests = {
        role_name: sha256(runner_subject._render_live_role_system_prompt(role_name).encode()).hexdigest()
        for role_name in runner_subject.LIVE_ROLE_PROMPT_BLOCKS
    }

    # These digests pin Claude E's approved verbatim text. Changing a prompt
    # requires an intentional design/review update, not an implicit registry drift.
    assert prompt_digests == {
        "technical_analyst": "f0d9f5f9cc9f0f7f06e8b1b7ea1060fc49a15d78881068c05fcbb441cf1d63d6",
        "risk_management_agent": "9fd8d3d2d359809de6bbde64db61a8c1f99319340d0eaec672d1295d001b2790",
        "fundamentals_analyst": "c28c06d69e10e65199ffc6c53ce295a7fbf14ea8ba68866b42bc31dfd173510a",
        "news_analyst": "6fb59bafaa2506a50cd917f16d618df52bedb98d849b669ff3a27e56f31f6db6",
    }
    assert frozenset(
        runner_subject._render_live_role_system_prompt(role_name) for role_name in runner_subject.LIVE_ROLE_PROMPT_BLOCKS
    ).issubset(registered_static_system_prompts())


def test_p35_t7c_unmapped_live_role_fails_closed() -> None:
    with pytest.raises(ValueError, match="unmapped live role prompt block: portfolio_manager_agent"):
        runner_subject._live_role_prompt_block("portfolio_manager_agent")


def test_p35_t7c_static_registry_does_not_bypass_dynamic_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    for forbidden_token in ("cash", "holdings", "account_id"):
        with pytest.raises(ValueError, match="forbidden private value"):
            LLMProviderMessage(role="user", content=f"Synthetic {forbidden_token} context.")
    with pytest.raises(ValueError, match="forbidden private value"):
        LLMProviderMessage(role="system", content="Synthetic non-registry holdings context.")

    monkeypatch.setattr(
        runner_subject,
        "_prompt_tool_result_envelope",
        lambda _result: {"availability": "available", "caveat_codes": ("cash",)},
    )
    with pytest.raises(ValueError, match="forbidden private value"):
        runner_subject._live_provider_request(
            "technical_analyst",
            (object(),),
            evidence_refs=("trade_intent_summary",),
            provider=_FakeLiveProvider(),
        )


def test_p35_t7c_static_prompt_registration_rejects_poisoned_entries() -> None:
    with pytest.raises(ValueError, match="secret-like"):
        register_static_system_prompts(("Static instruction api_key=abc12345",))
    with pytest.raises(ValueError, match="prohibited advice"):
        register_static_system_prompts(("Static instruction says you should buy.",))


def test_p35_t7c_length_truncated_live_note_keeps_deterministic_floor() -> None:
    deterministic = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": "Saved market context was available in the role envelopes. This trailing",
        },
        finish_reason_by_role={"technical_analyst": "length"},
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    technical = _role_summary(summary, "technical_analyst")
    deterministic_technical = _role_summary(deterministic, "technical_analyst")
    assert technical.live_report_markdown is None
    assert technical.summary_markdown == deterministic_technical.summary_markdown
    assert "live_note_truncated_dropped" in technical.warning_codes
    assert "live_provider_unavailable" in technical.warning_codes
    assert "This trailing" not in (summary.final_synthesis_markdown or "")
    assert "finish_reason" not in repr(summary.model_dump(mode="json"))


@pytest.mark.parametrize("finish_reason", (None, "unknown"))
def test_p35_t7c_absent_or_unknown_finish_reason_evaluates_live_note(finish_reason: str | None) -> None:
    provider = _FakeLiveProvider(finish_reason_by_role={"technical_analyst": finish_reason})

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert technical.live_report_markdown == _valid_live_report("technical_analyst")
    assert "live_note_truncated_dropped" not in technical.warning_codes


def test_p34a_t9b_live_overlay_preserves_all_deterministic_findings_and_adds_at_most_one() -> None:
    evidence = _evidence_package()
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _valid_live_report("technical_analyst"),
            "risk_management_agent": _valid_live_report("risk_management_agent"),
        }
    )

    deterministic_state = run_tool_mediated_agent_team(evidence, registry=default_tool_registry())
    live_state = run_tool_mediated_agent_team(
        evidence,
        registry=default_tool_registry(),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    deterministic_claims = _findings_by_role(deterministic_state)
    live_claims = _findings_by_role(live_state)
    deterministic_counts = _finding_counts_by_role(deterministic_state)
    live_counts = _finding_counts_by_role(live_state)
    provider_roles = {request.role_name for request in provider.calls}
    for role_name, claims in deterministic_claims.items():
        for claim in claims:
            assert claim in live_claims[role_name]
        assert live_counts[role_name] == deterministic_counts[role_name]
        if role_name in provider_roles:
            role_set = next(item for item in live_state.audited_findings if item.role_name == role_name)
            assert role_set.live_report_markdown is not None
        else:
            role_set = next(item for item in live_state.audited_findings if item.role_name == role_name)
            assert role_set.live_report_markdown is None


def test_p36_t7_composer_keeps_risk_live_note_out_of_synthesis() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _valid_live_report("technical_analyst"),
            "risk_management_agent": _valid_live_report("risk_management_agent"),
        }
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    synthesis = summary.final_synthesis_markdown or ""
    assert "## Market context" in synthesis
    assert "## Risk and scope notes" in synthesis
    assert _valid_live_report("technical_analyst") in synthesis
    assert _valid_live_report("risk_management_agent") not in synthesis
    assert _role_summary(summary, "risk_management_agent").live_report_markdown == _valid_live_report(
        "risk_management_agent"
    )
    assert "Audited live role sections:" not in synthesis
    assert "###" not in synthesis
    assert synthesis.index("Saved end-of-day market context was not available") < synthesis.index(
        _valid_live_report("technical_analyst")
    )


def test_p34a_t17_live_report_numeric_gate_allows_frozen_market_values() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _technical_live_report_with_market_values(),
        }
    )
    context = market_context_execution_context_for_client(
        _FakeFmpEodClient(_linear_eod_rows_for_runner(260)),
        collected_at=datetime(2025, 9, 18, tzinfo=UTC),
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
        market_context=context,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert "Latest close 260.0" in (technical.live_report_markdown or "")
    assert "SMA200 160.5" in (technical.live_report_markdown or "")
    assert "numeric_consistency_blocked" not in technical.warning_codes
    assert summary.tool_run_artifact is not None
    technical_set = next(item for item in summary.tool_run_artifact.audited_findings if item.role_name == "technical_analyst")
    assert technical_set.live_report_markdown == technical.live_report_markdown


def test_p34a_t17_live_report_numeric_gate_drops_wrong_market_value() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _technical_live_report_with_market_values(latest_close="999.0"),
        }
    )
    context = market_context_execution_context_for_client(
        _FakeFmpEodClient(_linear_eod_rows_for_runner(260)),
        collected_at=datetime(2025, 9, 18, tzinfo=UTC),
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
        market_context=context,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert technical.live_report_markdown is None
    assert "live_numeric_mismatch_dropped" in technical.warning_codes
    assert summary.tool_run_artifact is not None
    assert "numeric_consistency_blocked" in summary.tool_run_artifact.auditor.eval_flags
    assert "999.0" not in repr(summary.model_dump(mode="json"))


def test_p34a_t17_live_report_category_gate_drops_t13_manual_freshness_sentence() -> None:
    sentence = "The market quote freshness was designated as manual despite available evidence."
    match = ASSERTION_CATEGORY_RE.search(sentence)
    assert match is not None
    assert _normalize_category_capture(match.group(2)) == "manual"
    bad_report = _technical_live_report_with_category_sentence(sentence)
    provider = _FakeLiveProvider(content_by_role={"technical_analyst": bad_report})

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert technical.live_report_markdown is None
    assert "live_category_mismatch_dropped" in technical.warning_codes
    assert summary.tool_run_artifact is not None
    assert "category_consistency_blocked" in summary.tool_run_artifact.auditor.eval_flags


def test_p34a_t17_live_report_category_gate_allows_natural_freshness_assertion() -> None:
    report = _technical_live_report_with_category_sentence(
        "Market quote freshness is categorized as fresh in the saved evidence."
    )
    provider = _FakeLiveProvider(content_by_role={"technical_analyst": report})
    evidence = _evidence_package().model_copy(
        update={
            "market_quote_freshness": _section(
                "market_quote_freshness",
                summary_label="fresh",
            )
        }
    )

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert technical.live_report_markdown == report
    assert "category_consistency_blocked" not in technical.warning_codes


def test_p34a_t17_live_report_category_gate_handles_limited_availability_assertion() -> None:
    limited_result = ToolResult(
        tool_name="public_company_profile",
        role_name="fundamentals_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        availability="limited",
        evidence_refs=("public_company_profile",),
        summary_payload={"summary": "Synthetic limited public profile."},
    )
    available_result = ToolResult(
        tool_name="public_company_profile",
        role_name="fundamentals_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        availability="available",
        evidence_refs=("public_company_profile",),
        summary_payload={"summary": "Synthetic available public profile."},
    )
    markdown = "availability was limited for the snapshot"

    assert validate_live_report_consistency(markdown=markdown, role_results=(limited_result,)) is None
    assert (
        validate_live_report_consistency(markdown=markdown, role_results=(available_result,))
        == "category_consistency_blocked"
    )


def _fresh_market_quote_freshness_result() -> ToolResult:
    return ToolResult(
        tool_name="market_quote_freshness",
        role_name="technical_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        availability="available",
        freshness="fresh",
        evidence_refs=("market_quote_freshness",),
        summary_payload={"summary": "Synthetic fresh market quote freshness."},
    )


def test_p34a_t17a_f2_category_gate_drops_colon_form_wrong_category() -> None:
    # T18 field finding verbatim shape: a live summary-table cell relabeled
    # the envelope data_mode as a freshness category via colon phrasing.
    markdown = "| Saved market quote freshness | Market quote freshness: manual | None |"

    assert (
        validate_live_report_consistency(
            markdown=markdown,
            role_results=(_fresh_market_quote_freshness_result(),),
        )
        == "category_consistency_blocked"
    )


def test_p34a_t17a_f2_category_gate_allows_colon_form_matching_category() -> None:
    assert (
        validate_live_report_consistency(
            markdown="Market quote freshness: fresh",
            role_results=(_fresh_market_quote_freshness_result(),),
        )
        is None
    )


def test_p34a_t17a_f2_category_gate_allows_colon_form_honest_gap() -> None:
    markdown = "FMP end-of-day availability: not available for this report run."

    assert (
        validate_live_report_consistency(
            markdown=markdown,
            role_results=(_fresh_market_quote_freshness_result(),),
        )
        is None
    )


def test_p34a_t17_live_report_category_gate_allows_honest_not_reviewed_gap() -> None:
    report = (
        "Saved market context remains not reviewed in the role envelopes. "
        "Unavailable context remains not available."
    )
    assert "not reviewed" in report
    provider = _FakeLiveProvider(content_by_role={"technical_analyst": report})

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert technical.live_report_markdown == report
    assert "category_consistency_blocked" not in technical.warning_codes


def test_p34a_t17_live_report_structure_gate_keeps_news_sec_metadata_deterministic() -> None:
    result = ToolResult(
        tool_name="sec_recent_filings_metadata",
        role_name="news_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        source_key="sec_edgar_recent_filings",
        source_label="SEC EDGAR recent filing metadata - company events only",
        availability="available",
        evidence_refs=("public_events_calendar",),
        summary_payload={
            "reviewed_filing_metadata": (
                {"fact_key": "form_type", "fact_label": "Form Type", "value_label": "10-K"},
                {"fact_key": "filing_date", "fact_label": "Filing Date", "value_label": "2026-07-01"},
            )
        },
    )
    base_finding = RoleFinding(
        finding_type="missing_context",
        claim_text="Reviewed SEC filing metadata is background.",
        evidence_refs=("public_events_calendar",),
    )
    good_report = "\n".join(
        (
            "### Reviewed context",
            "SEC form 10-K filed 2026-07-01 was present as metadata only.",
            "### Not reviewed",
            "Filing contents were not reviewed.",
            "### Summary table",
            "| Context item | Frozen value or category | Status / caveat |",
            "| SEC filing metadata | 10-K | metadata only |",
        )
    )
    bad_report = good_report.replace("10-K", "13-F")

    good_auditor, good = audit_findings(
        (
            RoleFindingSet(
                role_name="news_analyst",
                role_status="completed",
                findings=(base_finding,),
                warning_codes=(),
                live_report_markdown=good_report,
            ),
        ),
        {"news_analyst": (result,)},
        {"news_analyst": frozenset({"public_events_calendar"})},
    )

    assert good[0].live_report_markdown is None
    assert "structure_contract_blocked" in good_auditor.eval_flags
    assert "numeric_consistency_blocked" not in good_auditor.eval_flags
    assert "13-F" in bad_report


def test_sec_recent_filings_news_finding_stays_deterministic_in_live_mode() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _valid_live_report("technical_analyst"),
            "risk_management_agent": _valid_live_report("risk_management_agent"),
            "news_analyst": "The filing signals a bullish catalyst.",
        }
    )
    evidence = _evidence_package(public_events_calendar=_sec_recent_filings_section())
    mock_summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    news = _role_summary(summary, "news_analyst")
    mock_news = _role_summary(mock_summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary", "public_events_calendar")
    assert news.summary_markdown == mock_news.summary_markdown
    assert "Form 8-K (Filed 2026-05-29)" in (news.summary_markdown or "")
    assert "bullish catalyst" not in (news.summary_markdown or "")
    assert {request.role_name for request in provider.calls} == {
        "technical_analyst",
        "risk_management_agent",
    }
    rendered_requests = repr(tuple(request.messages for request in provider.calls)).lower()
    assert "summary_payload" not in rendered_requests
    assert "reviewed_filing_metadata" not in rendered_requests
    assert "form 8-k" not in rendered_requests
    assert "filed 2026-05-29" not in rendered_requests


def test_fred_economic_awareness_news_finding_stays_deterministic_in_live_mode() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "technical_analyst": _valid_live_report("technical_analyst"),
            "risk_management_agent": _valid_live_report("risk_management_agent"),
            "news_analyst": "The CPI release suggests a bullish macro signal.",
        }
    )
    evidence = _evidence_package(economic_awareness_snapshot=_fred_economic_awareness_section())
    mock_summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    news = _role_summary(summary, "news_analyst")
    mock_news = _role_summary(mock_summary, "news_analyst")
    assert news.role_status == "completed"
    assert news.evidence_references == ("trade_intent_summary", "economic_awareness_snapshot")
    assert news.summary_markdown == mock_news.summary_markdown
    assert "Consumer Price Index release (2026-07-15)" in (news.summary_markdown or "")
    assert "bullish macro signal" not in (news.summary_markdown or "")
    assert {request.role_name for request in provider.calls} == {
        "technical_analyst",
        "risk_management_agent",
    }
    rendered_requests = repr(tuple(request.messages for request in provider.calls)).lower()
    assert "summary_payload" not in rendered_requests
    assert "consumer price index" not in rendered_requests
    assert "2026-07-15" not in rendered_requests


@pytest.mark.parametrize("status", ("provider_auth_error", "provider_timeout", "rate_limited"))
def test_p34a_live_provider_failures_degrade_to_skipped_roles(status: LLMProviderStatus) -> None:
    provider = _FakeLiveProvider(status_by_role={"risk_management_agent": status})

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )
    risk = _role_summary(summary, "risk_management_agent")

    assert summary.provider_mode == "tool_mediated_live"
    assert risk.role_status == "completed"
    assert risk.unavailable_reason is None
    assert f"live_provider_{status}" in risk.warning_codes
    assert risk.summary_markdown is not None
    assert "Live" not in risk.summary_markdown
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.tool_results
    assert any(run.role_name == "risk_management_agent" and run.status == status for run in summary.tool_run_artifact.provider_runs)


def test_p34a_live_provider_timeout_exception_degrades_to_deterministic_fallback() -> None:
    provider = _TimeoutLiveProvider()

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )
    risk = _role_summary(summary, "risk_management_agent")

    assert summary.provider_mode == "tool_mediated_live"
    assert risk.role_status == "completed"
    assert "live_provider_provider_timeout" in risk.warning_codes
    assert summary.tool_run_artifact is not None
    assert any(run.role_name == "risk_management_agent" and run.status == "provider_timeout" for run in summary.tool_run_artifact.provider_runs)


@pytest.mark.parametrize(
    "unsafe_content",
    (
        "This references provider_account_id_secret.",
        "You should buy this.",
        "This invents a $100 target.",
        "This connective sentence mentions 2026 context.",
        "The filing signals a bullish catalyst.",
        "The CPI release suggests a bullish macro signal.",
        "Review https://example.com for more context.",
    ),
)
def test_p34a_live_provider_unsafe_output_is_rejected_before_persistence(unsafe_content: str) -> None:
    provider = _UnsafeLiveProvider(unsafe_content)

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    assert summary.provider_mode == "tool_mediated_live"
    rendered = repr(summary.model_dump(mode="json")).lower()
    assert unsafe_content.lower() not in rendered
    assert "provider_account_id_secret" not in rendered
    assert "you should buy" not in rendered
    assert "$100" not in rendered
    assert "2026 context" not in rendered
    assert "bullish catalyst" not in rendered
    assert "bullish macro signal" not in rendered
    assert "https://example.com" not in rendered
    assert summary.tool_run_artifact is not None
    assert all(
        role.role_status == "completed"
        for role in summary.role_summaries
        if role.role_name in {"technical_analyst", "risk_management_agent"}
    )
    assert all(
        any(
            code
            in {
                "live_provider_safety_fallback",
                "live_structure_contract_dropped",
                "live_numeric_mismatch_dropped",
                "live_category_mismatch_dropped",
                "live_display_token_dropped",
                "live_portfolio_claim_dropped",
            }
            for code in role.warning_codes
        )
        for role in summary.role_summaries
        if role.role_name in {"technical_analyst", "risk_management_agent"}
    )
    assert summary.tool_run_artifact.auditor.repass_triggered is False
    assert any(
        flag in summary.tool_run_artifact.auditor.eval_flags
        for flag in {
            "private_leak_blocked",
            "advice_wording_blocked",
            "invented_metric_blocked",
            "sec_interpretation_blocked",
            "fred_interpretation_blocked",
            "source_leak_blocked",
            "live_provider_validation_failed",
            "structure_contract_blocked",
            "numeric_consistency_blocked",
            "category_consistency_blocked",
            "display_token_blocked",
            "portfolio_claim_blocked",
        }
    )
    deterministic_state = run_tool_mediated_agent_team(_evidence_package(), registry=default_tool_registry())
    deterministic_claims = _findings_by_role(deterministic_state)
    live_claims = {
        item.role_name: tuple(finding.claim_text for finding in item.findings)
        for item in summary.tool_run_artifact.audited_findings
    }
    for role_name in {"technical_analyst", "risk_management_agent"}:
        for claim in deterministic_claims[role_name]:
            assert claim in live_claims[role_name]


def test_p35_t5_live_portfolio_claim_gate_blocks_comparative_magnitude() -> None:
    provider = _FakeLiveProvider(
        content_by_role={"risk_management_agent": "This would roughly double your chip exposure."}
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    risk = _role_summary(summary, "risk_management_agent")
    assert risk.live_report_markdown is None
    assert "live_portfolio_claim_dropped" in risk.warning_codes
    assert summary.tool_run_artifact is not None
    assert "portfolio_claim_blocked" in summary.tool_run_artifact.auditor.eval_flags
    assert "double your chip exposure" not in repr(summary.model_dump(mode="json")).lower()


def test_p35_t5_live_display_token_gate_blocks_internal_token() -> None:
    provider = _FakeLiveProvider(
        content_by_role={"technical_analyst": "Saved context includes eod_not_live_prices."}
    )

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    technical = _role_summary(summary, "technical_analyst")
    assert technical.live_report_markdown is None
    assert "live_display_token_dropped" in technical.warning_codes
    assert summary.tool_run_artifact is not None
    assert "display_token_blocked" in summary.tool_run_artifact.auditor.eval_flags
    assert "eod_not_live_prices" not in repr(summary.model_dump(mode="json"))


def test_p35_t5_document_uses_frozen_trade_impact_groups_without_parsing_flat_labels() -> None:
    before_after = SavedEvidenceSectionRead(
        section_key="before_after_portfolio_impact",
        section_label="Before/after portfolio impact",
        availability="available",
        summary_label="Frozen before/after impact is available.",
        detail_labels=(
            "Asset class: Row | Before $ | Before % | Trade Delta $ | After $ | After %.",
            "Equity | $93,000 | 93.0% | +$7,000 | $100,000 | 100.0%.",
            "Trade-impact narrative:",
            "Do not parse this flat label into the document.",
        ),
        trade_impact_narrative_groups={
            "proceed_statements": (
                "Proceeding would create a new $7,000 XYZ position from frozen evidence.",
                "Sector exposure would move from 35.0% to 42.0% in the saved calculation.",
            ),
            "not_reviewed_statement": "Not reviewed: fund holdings, taxes, and outside accounts.",
            "verify_statement": "Verify the frozen exposure math against current app screens.",
        },
    )
    evidence = _evidence_package().model_copy(update={"before_after_portfolio_impact": before_after})

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    synthesis = summary.final_synthesis_markdown or ""
    assert "Proceeding would create a new $7,000 XYZ position" in synthesis
    assert "Sector exposure would move from 35.0% to 42.0%" in synthesis
    assert "Not reviewed: fund holdings, taxes, and outside accounts." in synthesis
    assert "Verify the frozen exposure math against current app screens." in synthesis
    assert "Do not parse this flat label into the document." not in synthesis
    assert "## If you proceed" in synthesis
    assert "## What was not reviewed" in synthesis
    assert "- Market Mood snapshot" in synthesis
    assert "- public fundamentals snapshot" in synthesis
    assert "## Verify before acting" in synthesis


def test_p35_t5_pre_t5_package_renders_honest_unavailable_path_without_parse_fallback() -> None:
    before_after = SavedEvidenceSectionRead(
        section_key="before_after_portfolio_impact",
        section_label="Before/after portfolio impact",
        availability="available",
        summary_label="Frozen before/after impact is available.",
        detail_labels=(
            "Trade-impact narrative:",
            "Legacy flat narrative should not be parsed into the v4 report.",
        ),
    )
    evidence = _evidence_package().model_copy(update={"before_after_portfolio_impact": before_after})

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    synthesis = summary.final_synthesis_markdown or ""
    assert "Trade-impact narrative statements were not frozen with this saved package" in synthesis
    assert "Legacy flat narrative should not be parsed into the v4 report." not in synthesis


def test_p36_t7_a2g_document_does_not_project_reviewed_account_nickname() -> None:
    generated_at = datetime(2026, 6, 1, tzinfo=UTC)
    named_evidence = _evidence_package().model_copy(
        update={
            "scope_state": _evidence_package().scope_state.model_copy(
                update={"review_account_display_label": "Growth Demo Account"}
            )
        }
    )

    named_summary = build_tool_mediated_agent_team_summary(named_evidence, report_generated_at=generated_at)
    fallback_summary = build_tool_mediated_agent_team_summary(
        _evidence_package(), report_generated_at=generated_at
    )

    named_document = named_summary.final_synthesis_markdown or ""
    fallback_document = fallback_summary.final_synthesis_markdown or ""
    assert "Growth Demo Account" not in named_document
    assert "- reviewed account - June 1, 2026" in named_document
    assert "for reviewed account using frozen evidence only." in named_document
    assert "- reviewed account - June 1, 2026" in fallback_document
    assert "for reviewed account using frozen evidence only." in fallback_document


def test_p36_t7_composer_title_uses_frozen_review_snapshot_date() -> None:
    base_evidence = _evidence_package()
    evidence = base_evidence.model_copy(
        update={
            "source_snapshot": base_evidence.source_snapshot.model_copy(
                update={"generated_at": datetime(2026, 7, 14, 22, 3, tzinfo=UTC)}
            )
        }
    )

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 7, 15, 0, 30, tzinfo=UTC),
    )

    document = summary.final_synthesis_markdown or ""
    assert "- reviewed account - July 14, 2026" in document
    assert "- reviewed account - July 15, 2026" not in document


def test_p35_t7a_document_uses_freshness_labels_without_duplicate_prefixes() -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(), report_generated_at=datetime(2026, 6, 1, tzinfo=UTC)
    )

    document = summary.final_synthesis_markdown or ""
    assert "Broker snapshot freshness: Broker snapshot freshness label saved" not in document
    assert "Market quote freshness: Market quote freshness label saved" not in document
    assert "Broker snapshot freshness label saved." in document
    assert "Market quote freshness label saved." in document


def test_p35_t9_market_context_display_rows_use_reviewed_labels_and_dedupe_metadata() -> None:
    result = ToolResult(
        tool_name="market_context_snapshot",
        role_name="technical_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        source_key="fmp_eod_history",
        source_label="FMP end-of-day history",
        availability="available",
        freshness="Market quote freshness: manual",
        as_of=datetime(2026, 7, 10, tzinfo=UTC),
        evidence_refs=("public_market_context",),
        summary_payload={
            "as_of_date": "2026-07-10",
            "freshness_category": "manual",
            "indicators": {"atr14": 2.5, "unmapped_signal": 1.0},
        },
    )

    fact_labels = runner_subject.prompt_fact_labels_for_tool_result(result)
    rows = runner_subject._market_context_display_rows(result)
    rendered = "\n".join(rows)

    assert "Market quote freshness: manual" not in {fact["value_label"] for fact in fact_labels}
    assert "manual" in {fact["value_label"] for fact in fact_labels}
    assert validate_live_report_consistency(
        markdown="Market quote freshness is categorized as manual in the saved evidence.",
        role_results=(result,),
    ) is None
    assert rendered.count("| as-of date |") == 1
    assert rendered.count("| freshness category |") == 1
    assert "| ATR fourteen | 2.5 |" in rendered
    assert "unmapped_signal" not in rendered
    assert "atr14_usd" not in rendered
    assert "| Omitted indicator |" in rendered


def test_p36_t7_composer_keeps_risk_live_note_in_role_section_only() -> None:
    provider = _FakeLiveProvider()
    base_evidence = _evidence_package()
    evidence = base_evidence.model_copy(
        update={
            "trade_intent_summary": base_evidence.trade_intent_summary.model_copy(
                update={"review_flow_label": "Stock buy review", "supported_flow": "stock_buy"}
            )
        }
    )

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    document = summary.final_synthesis_markdown or ""
    assert "reviews stock buy review" not in document
    assert "covers the saved stock buy" in document
    assert "**Technical Analyst**" in document
    assert "**Risk Manager**" not in document
    assert _role_summary(summary, "risk_management_agent").live_report_markdown is not None


def test_p35_t9_composer_names_missing_live_note_when_live_mode_ran() -> None:
    provider = _FakeLiveProvider(finish_reason_by_role={"technical_analyst": "length"})

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    document = summary.final_synthesis_markdown or ""
    assert "No Technical Analyst note is available in this saved report." in document
    assert "**Risk Manager**" not in document


def test_p35_t9_risk_note_plain_topic_vocabulary_survives_but_disclosures_stay_blocked() -> None:
    provider = _FakeLiveProvider(
        content_by_role={
            "risk_management_agent": (
                "Cash, holdings, and positions remain saved-review topics. "
                "Re-verify the exposure math in the reviewed app before comparing current broker screens."
            )
        }
    )
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )

    risk = _role_summary(summary, "risk_management_agent")
    assert risk.live_report_markdown is not None
    assert "Cash, holdings, and positions" in risk.live_report_markdown
    assert "Cash, holdings, and positions" not in (summary.final_synthesis_markdown or "")

    for unsafe_note in (
        "cash_balance is present in this report. Re-verify the saved evidence.",
        "cash: private value. Re-verify the saved evidence.",
        "api_key: synthetic-secret-value. Re-verify the saved evidence.",
    ):
        auditor, audited = audit_findings(
            (
                RoleFindingSet(
                    role_name="risk_management_agent",
                    role_status="completed",
                    findings=(
                        RoleFinding(
                            finding_type="ignored_risk",
                            claim_text="Saved deterministic risk context remains available.",
                            evidence_refs=("trade_intent_summary",),
                        ),
                    ),
                    warning_codes=(),
                    live_report_markdown=unsafe_note,
                ),
            ),
            {"risk_management_agent": (_result(role_name="risk_management_agent", evidence_refs=("trade_intent_summary",)),)},
            {"risk_management_agent": frozenset({"trade_intent_summary"})},
        )
        assert audited[0].live_report_markdown is None
        assert "private_leak_blocked" in auditor.eval_flags

    # The exception is prose-only: metadata still receives the regular strict scan.
    assert (
        _hard_block_flag(
            RoleFinding(
                finding_type="missing_context",
                claim_text="Cash remains a saved-review topic.",
                evidence_refs=("trade_intent_summary",),
                caveat_codes=("cash",),
            ),
            allow_role_note_topic_vocabulary=True,
        )
        == "private_leak_blocked"
    )


def test_p34a_live_provider_freeze_is_reproducible_with_fixed_inputs() -> None:
    generated_at = datetime(2026, 6, 1, tzinfo=UTC)
    first_provider = _FakeLiveProvider()
    second_provider = _FakeLiveProvider()

    first = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=generated_at,
        llm_provider=first_provider,
        live_provider_enabled=True,
    )
    second = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=generated_at,
        llm_provider=second_provider,
        live_provider_enabled=True,
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    first_call_count = len(first_provider.calls)
    round_tripped = SavedAgentTeamSummaryRead.model_validate(first.model_dump(mode="json"))
    assert round_tripped.model_dump(mode="json") == first.model_dump(mode="json")
    assert len(first_provider.calls) == first_call_count


class _ChainScriptedModelProvider(_FakeLiveProvider):
    """Per-model fake whose first-model calls always fail with quota_exceeded."""

    def __init__(self, *, model: str, always_status: LLMProviderStatus | None = None) -> None:
        super().__init__()
        self.model = model
        self._always_status = always_status

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        if self._always_status is not None:
            self.status_by_role = {request.role_name: self._always_status}
        return super().complete(request)


def test_p34a_t10_chain_metadata_freezes_into_provider_runs_and_readback() -> None:
    exhausted = _ChainScriptedModelProvider(model="chain-model-a", always_status="quota_exceeded")
    serving = _ChainScriptedModelProvider(model="chain-model-b")
    chain = ChainedLLMProvider(providers=(exhausted, serving))
    resolution = LLMProviderResolution(
        provider=chain,
        status="ok",
        provider_name="fake_live_provider",
        model="chain-model-a",
    )

    summary = build_tool_mediated_agent_team_summary_from_provider_resolution(
        _evidence_package(),
        provider_resolution=resolution,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    assert summary.provider_mode == "tool_mediated_live"
    assert summary.tool_run_artifact is not None
    runs = summary.tool_run_artifact.provider_runs
    assert runs, "expected frozen provider runs for the chained live path"
    assert all(run.status == "ok" for run in runs)
    assert all(run.model == "chain-model-b" for run in runs)
    assert all(run.model_chain_position == 1 for run in runs)
    # The first role walks the chain; the sticky index means later roles go
    # straight to the serving model.
    attempted = [tuple(run.attempted_models) for run in runs]
    assert attempted[0] == ("chain-model-a", "chain-model-b")
    assert all(item == ("chain-model-b",) for item in attempted[1:])
    assert len(exhausted.calls) == 1

    round_tripped = SavedAgentTeamSummaryRead.model_validate(summary.model_dump(mode="json"))
    frozen_runs = round_tripped.tool_run_artifact.provider_runs
    assert [run.model_chain_position for run in frozen_runs] == [1] * len(frozen_runs)
    assert [tuple(run.attempted_models) for run in frozen_runs] == attempted
    rendered = repr(round_tripped.model_dump(mode="python")).lower()
    assert "api_key" not in rendered and "prompt:" not in rendered


def test_p34a_t18_category_gate_allows_mandated_scope_caveat_restatement() -> None:
    # The deterministic scope caveats contain "limited" and "unknown" as plain
    # English; a compliant risk-role restatement must not trip the bare check.
    markdown = (
        "Scope is limited to the selected portfolio context; "
        "review account scope membership unknown."
    )

    assert (
        validate_live_report_consistency(
            markdown=markdown,
            role_results=(_fresh_market_quote_freshness_result(),),
        )
        is None
    )


def test_p34a_t18_category_gate_allows_freshness_item_availability_statement() -> None:
    # "X freshness: available" describes the freshness item's availability
    # (a truthful envelope fact), not a freshness category; membership is
    # checked against the token's own vocabulary class.
    markdown = "Saved market quote freshness: available."

    assert (
        validate_live_report_consistency(
            markdown=markdown,
            role_results=(_fresh_market_quote_freshness_result(),),
        )
        is None
    )


def test_p34a_t18_category_gate_admits_label_derived_freshness_category() -> None:
    # Envelope freshness fields carry display labels ("Manual quote entry");
    # the allowed set derives the category token the same way the
    # deterministic floor does, so truthful "freshness: manual" passes.
    result = ToolResult(
        tool_name="market_quote_freshness",
        role_name="technical_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        availability="available",
        freshness="Manual quote entry",
        evidence_refs=("market_quote_freshness",),
        summary_payload={"summary": "Synthetic manual quote freshness."},
    )

    assert (
        validate_live_report_consistency(
            markdown="Market quote freshness: manual",
            role_results=(result,),
        )
        is None
    )


def test_p34a_t18_category_gate_skips_colon_form_item_label_text() -> None:
    # Table cells like "... freshness | Market quote ..." produce colon-form
    # captures that are item labels, not category assertions; they are skipped
    # while vocabulary-word misuse in the same cell still flags.
    markdown = "| Saved market quote freshness | Market quote freshness: stale | None |"

    assert (
        validate_live_report_consistency(
            markdown=markdown,
            role_results=(_fresh_market_quote_freshness_result(),),
        )
        == "category_consistency_blocked"
    )
