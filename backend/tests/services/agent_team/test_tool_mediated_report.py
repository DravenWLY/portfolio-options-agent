from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.services.agent_team.llm_provider import LLMProviderRequest, LLMProviderResponse, LLMProviderStatus
from app.services.agent_team.provider_factory import LLMProviderResolution
from app.services.agent_team import tool_mediated_report as subject
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
from app.schemas.reports import SavedAgentTeamSummaryRead
from tests.services.agent_team.test_tools import (
    _evidence_package,
    _fred_economic_awareness_section,
    _public_company_profile_section,
    _section,
)


pytestmark = [pytest.mark.unit]


EXPECTED_USABLE_CONTENT = {
    "fundamentals_analyst": frozenset({"trade_intent_summary", "public_company_profile"}),
    "news_analyst": frozenset({"trade_intent_summary", "economic_awareness_snapshot"}),
    "technical_analyst": frozenset({"trade_intent_summary", "market_quote_freshness"}),
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
            "public_company_profile",
        }
    ),
}


EXPECTED_PLAN = {
    "fundamentals_analyst": ("trade_intent_summary", "public_company_profile"),
    "news_analyst": ("trade_intent_summary", "economic_awareness_context"),
    "technical_analyst": ("trade_intent_summary", "market_quote_freshness"),
    "risk_management_agent": (
        "trade_intent_summary",
        "portfolio_scope_context",
        "deterministic_review_findings",
        "broker_snapshot_freshness",
        "market_quote_freshness",
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


class _FakeLiveProvider:
    provider_name = "fake_live_provider"
    model = "fake-live-model"

    def __init__(
        self,
        *,
        status_by_role: dict[str, LLMProviderStatus] | None = None,
        content_by_role: dict[str, str] | None = None,
    ) -> None:
        self.status_by_role = dict(status_by_role or {})
        self.content_by_role = dict(content_by_role or {})
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
                "Live role context cites supplied evidence as background for manual review.",
            ),
            is_mock=False,
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
    assert sum(len(item.tool_requests) for item in plan.role_plan) == 12
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
    assert news.role_status == "skipped"
    assert news.evidence_references == ("trade_intent_summary",)
    assert news.warning_codes == ("public_news_context_unavailable",)
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
    assert "economic_awareness_snapshot" in summary.evidence_references
    assert "market_mood_snapshot" not in summary.evidence_references
    assert "public_news_snapshot" not in summary.evidence_references
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


def test_r5_missing_public_evidence_degrades_public_roles_without_agent_safe_leak() -> None:
    evidence = _evidence_package().model_copy(update={"public_evidence": None})
    summary = build_tool_mediated_agent_team_summary(evidence, report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert _role_summary(summary, "fundamentals_analyst").role_status == "skipped"
    assert _role_summary(summary, "fundamentals_analyst").evidence_references == ("trade_intent_summary",)
    assert _role_summary(summary, "news_analyst").role_status == "skipped"
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
    assert artifact.tool_result_count == 12
    assert len(artifact.tool_results) == 12
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
    assert round_tripped.tool_run_artifact.tool_result_count == 12


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
    monkeypatch.setattr(
        subject,
        "_synthesis_markdown",
        lambda *_args, **_kwargs: "You should buy because this is safe to trade.",
    )

    summary = build_tool_mediated_agent_team_summary(_evidence_package(), report_generated_at=datetime(2026, 6, 1, tzinfo=UTC))

    assert summary.report_status == "validation_failed"
    assert summary.run_status == "failed"
    assert "you should" not in repr(summary.model_dump(mode="json")).lower()


def test_p34a_live_provider_gate_is_disabled_by_default_even_with_provider() -> None:
    provider = _FakeLiveProvider()

    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
    )

    assert provider.calls == []
    assert summary.provider_mode == "tool_mediated_mock"
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.provider_mode == "tool_mediated_mock"


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
            "fundamentals_analyst": "Live fundamentals context cites reviewed public identity evidence as background.",
            "technical_analyst": "Live technical context cites saved market freshness as background.",
            "risk_management_agent": "Live risk context cites deterministic caveats as background.",
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
    assert summary.tool_run_artifact.tool_result_count == 12
    assert summary.tool_run_artifact.provider_runs
    assert {request.role_name for request in provider.calls} == {
        "fundamentals_analyst",
        "technical_analyst",
        "risk_management_agent",
    }
    assert {run.role_name for run in summary.tool_run_artifact.provider_runs} == {
        "fundamentals_analyst",
        "technical_analyst",
        "risk_management_agent",
    }
    assert all(run.provider == "fake_live_provider" for run in summary.tool_run_artifact.provider_runs)
    assert all(run.model == "fake-live-model" for run in summary.tool_run_artifact.provider_runs)
    assert all(run.prompt_version == "p34a-tool-mediated-role-v1" for run in summary.tool_run_artifact.provider_runs)
    assert all(run.status == "ok" for run in summary.tool_run_artifact.provider_runs)
    assert _role_summary(summary, "fundamentals_analyst").summary_markdown == (
        "Live fundamentals context cites reviewed public identity evidence as background."
    )
    assert _role_summary(summary, "fundamentals_analyst").evidence_references == (
        "trade_intent_summary",
        "public_company_profile",
    )
    assert "live_provider_reasoning_used" in _role_summary(summary, "fundamentals_analyst").warning_codes
    rendered_requests = repr(tuple(request.messages for request in provider.calls)).lower()
    assert "summary_payload" not in rendered_requests
    assert "scope':" not in rendered_requests
    assert "as_of" not in rendered_requests
    assert "cash_secured_put" not in rendered_requests
    assert "buying_power" not in rendered_requests
    assert "raw_payload" not in rendered_requests
    assert "account_id" not in rendered_requests
    for request in provider.calls:
        for message in request.messages:
            validate_tool_payload({"content": message.content}, label="captured live prompt message")


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
    assert summary.tool_run_artifact is not None
    assert all(
        role.role_status == "completed"
        for role in summary.role_summaries
        if role.role_name in {"fundamentals_analyst", "technical_analyst", "risk_management_agent"}
    )
    assert all(
        "live_provider_safety_fallback" in role.warning_codes
        for role in summary.role_summaries
        if role.role_name in {"fundamentals_analyst", "technical_analyst", "risk_management_agent"}
    )
    assert summary.tool_run_artifact.auditor.repass_triggered is False
    assert any(
        flag in summary.tool_run_artifact.auditor.eval_flags
        for flag in {"private_leak_blocked", "advice_wording_blocked", "invented_metric_blocked"}
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
