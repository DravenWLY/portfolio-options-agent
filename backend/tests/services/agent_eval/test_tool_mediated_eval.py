from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.agent_eval.harness import evaluate_tool_mediated_report
from app.services.agent_eval.results import (
    DETAIL_ARTIFACT_MISSING,
    DETAIL_ARTIFACT_ON_DRAFT,
    DETAIL_CITATION_BOUNDARY,
    DETAIL_CITATION_UNRESOLVED,
    DETAIL_DISCOVERY_DELTA,
    DETAIL_GAP_CITED,
    DETAIL_INVENTED_LEVEL,
    DETAIL_NOT_BYTE_STABLE,
    DETAIL_SYNTHESIS_UNAUDITED,
    EvalFinding,
    EvalReport,
)
from app.services.agent_eval.tool_mediated_checks import (
    check_artifact_present_for_full_report,
    check_blocked_draft_has_no_artifact,
    check_byte_stable_regeneration,
    check_citation_graph_closure,
    check_discovery_delta,
    check_discovery_non_regression,
    check_gaps_not_cited,
    check_role_citations_within_boundary,
    check_synthesis_cites_audited_only,
)
from app.services.agent_eval.tool_mediated_scenarios import (
    TOOL_MEDIATED_SCENARIOS,
    ToolMediatedScenario,
    _valid_live_report,
    run_scenario,
)
from app.services.agent_team.auditing.live_report_gates import validate_live_report_consistency
from app.services.agent_team.llm_clients.contracts import LLMProviderRequest, LLMProviderResponse
from app.services.agent_team.tools import ToolResult
from app.services.agent_team.tool_mediated_report import (
    RoleFinding,
    RoleFindingSet,
    build_tool_mediated_agent_team_summary,
    usable_content_by_role,
)
from app.schemas.reports import SavedAgentTeamSummaryRead, SavedEvidenceSectionRead
from tests.services.agent_team.test_tools import _evidence_package


pytestmark = [pytest.mark.unit]


def _scenario(name: str) -> ToolMediatedScenario:
    return next(scenario for scenario in TOOL_MEDIATED_SCENARIOS if scenario.name == name)


def _finding(report: EvalReport, check: str) -> EvalFinding:
    return next(finding for finding in report.findings if finding.check == check)


def _role_summary(summary: SavedAgentTeamSummaryRead, role_name: str):
    return next(role for role in summary.role_summaries if role.role_name == role_name)


def _replace_role_refs(
    summary: SavedAgentTeamSummaryRead,
    role_name: str,
    refs: tuple[str, ...],
) -> SavedAgentTeamSummaryRead:
    return summary.model_copy(
        update={
            "role_summaries": tuple(
                role.model_copy(update={"evidence_references": refs})
                if role.role_name == role_name
                else role
                for role in summary.role_summaries
            )
        }
    )


class _EvalLiveProvider:
    provider_name = "eval_live_provider"
    model = "eval-live-model"

    def __init__(self, content_by_role: dict[str, str]) -> None:
        self.content_by_role = dict(content_by_role)
        self.calls: list[LLMProviderRequest] = []

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        self.calls.append(request)
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=self.content_by_role.get(request.role_name, _valid_live_report(request.role_name)),
            is_mock=False,
        )


def _unsafe_artifact_payload(summary: SavedAgentTeamSummaryRead, payload: dict[str, object]) -> SavedAgentTeamSummaryRead:
    unsafe = summary.model_copy(deep=True)
    assert unsafe.tool_run_artifact is not None
    unsafe.tool_run_artifact.tool_results[0].summary_payload = payload
    return unsafe


def _technical_live_report_with_sentence(sentence: str) -> str:
    return f"{sentence} Unavailable context remains not available."


def test_p35_t7a_assumed_external_frozen_document_reconciles_after_purchase_total() -> None:
    before_after = SavedEvidenceSectionRead(
        section_key="before_after_portfolio_impact",
        section_label="Before/after portfolio impact",
        availability="available",
        summary_label=(
            "Trade impact uses a before-purchase portfolio total of $18,800 and an after-purchase "
            "portfolio total of $29,000 using the synthetic reviewed snapshot."
        ),
        detail_labels=(
            "Single-name/asset view: Row | Before $ | Before % | Trade Delta $ | After $ | After %.",
            "Cash | $10,000 | 53.2% | $0 | $10,000 | 34.5%.",
            "AAPL | $8,800 | 46.8% | $0 | $8,800 | 30.3%.",
            "NVDA | $0 | 0.0% | +$10,200 | $10,200 | 35.2%.",
            "Other | $0 | 0.0% | $0 | $0 | 0.0%.",
            "Trade-impact narrative:",
        ),
        caveat_codes=("funding_shortfall_detected", "outside_funds_assumed"),
        trade_impact_narrative_groups={
            "proceed_statements": (
                "This purchase equals 35.2% of the after-purchase portfolio total of $29,000.",
                "The reviewed cash snapshot is short by $200 for this purchase; external funding was assumed for percentage math.",
            ),
            "not_reviewed_statement": "Not reviewed: fund holdings, taxes, and outside accounts.",
            "verify_statement": "Verify current broker capacity.",
        },
    )
    evidence = _evidence_package().model_copy(update={"before_after_portfolio_impact": before_after})

    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    document = summary.final_synthesis_markdown or ""
    after_percents = (Decimal("34.5"), Decimal("30.3"), Decimal("35.2"), Decimal("0.0"))
    assert sum(after_percents) == Decimal("100.0")
    assert "$18,800" in document
    assert "$29,000" in document
    assert "$19,000" not in document
    assert "short by $200" in document
    assert "funding_shortfall_detected" not in document


def test_ev_u1_usable_content_and_full_scenario_pass() -> None:
    usable = usable_content_by_role()

    assert usable["news_analyst"] == frozenset(
        {"trade_intent_summary", "economic_awareness_snapshot", "public_events_calendar"}
    )
    assert "public_company_profile" in usable["fundamentals_analyst"]
    assert "public_events_calendar" not in usable["fundamentals_analyst"]
    assert "liquidity_collateral_caveats" not in usable["fundamentals_analyst"]
    assert "liquidity_collateral_caveats" in usable["risk_management_agent"]
    assert usable["portfolio_manager_agent"].issuperset(usable["risk_management_agent"])

    summary, baseline, report = run_scenario(_scenario("full_available"))

    assert baseline is not None
    assert summary.tool_run_artifact is not None
    assert report.passed is True


def test_ev1_discovery_is_delta_measured_not_regression_gated() -> None:
    summary, baseline, _report = run_scenario(_scenario("full_available"))

    assert check_discovery_non_regression(summary, baseline).status == "passed"
    delta = check_discovery_delta(summary, baseline)
    assert delta.status == "passed"
    assert delta.detail == DETAIL_DISCOVERY_DELTA
    assert check_discovery_non_regression(summary, None).status == "deferred"


def test_ev2_unavailable_and_gap_refs_are_never_citable() -> None:
    clean, _baseline, clean_report = run_scenario(_scenario("stale_market_quote"))

    assert clean_report.passed is True
    assert "market_quote_freshness" not in _role_summary(clean, "technical_analyst").evidence_references
    assert clean.tool_run_artifact is not None
    unavailable_quote_results = tuple(
        result
        for result in clean.tool_run_artifact.tool_results
        if result.tool_name == "market_quote_freshness" and result.availability == "not_available"
    )
    assert unavailable_quote_results
    assert all("market_quote_freshness" not in result.evidence_refs for result in unavailable_quote_results)

    bad = _replace_role_refs(
        clean,
        "technical_analyst",
        ("trade_intent_summary", "market_quote_freshness"),
    )
    gap = check_gaps_not_cited(bad)

    assert gap.status == "flagged"
    assert gap.detail == DETAIL_GAP_CITED


def test_ev3_role_boundaries_and_pm_synthesis_closure_are_enforced() -> None:
    summary, _baseline, _report = run_scenario(_scenario("full_available"))

    assert check_role_citations_within_boundary(summary).status == "passed"
    assert check_citation_graph_closure(summary).status == "passed"
    assert check_synthesis_cites_audited_only(summary).status == "passed"

    bad_role = _replace_role_refs(
        summary,
        "news_analyst",
        ("trade_intent_summary", "public_company_profile"),
    )
    boundary = check_role_citations_within_boundary(bad_role)
    assert boundary.status == "flagged"
    assert boundary.detail == DETAIL_CITATION_BOUNDARY

    unresolved = _replace_role_refs(
        summary,
        "risk_management_agent",
        (*_role_summary(summary, "risk_management_agent").evidence_references, "before_after_portfolio_impact"),
    )
    closure = check_citation_graph_closure(unresolved)
    assert closure.status == "flagged"
    assert closure.detail == DETAIL_CITATION_UNRESOLVED

    bad_synthesis = summary.model_copy(
        update={
            "evidence_references": (
                *summary.evidence_references,
                "before_after_portfolio_impact",
            )
        }
    )
    synthesis = check_synthesis_cites_audited_only(bad_synthesis)
    assert synthesis.status == "flagged"
    assert synthesis.detail == DETAIL_SYNTHESIS_UNAUDITED


def test_ev4_contradictions_are_open_questions_and_red_team_findings_fail_closed() -> None:
    contradiction, _baseline, contradiction_report = run_scenario(_scenario("contradiction"))
    artifact = contradiction.tool_run_artifact

    assert contradiction_report.passed is True
    assert artifact is not None
    assert artifact.auditor.contradictions
    assert artifact.open_questions
    assert "open questions" in (contradiction.final_synthesis_markdown or "").lower()
    audited_claims = {
        finding.claim_text
        for finding_set in artifact.audited_findings
        for finding in finding_set.findings
    }
    assert "Market quote freshness has a structured positive freshness signal." in audited_claims
    assert "Market quote freshness has a structured negative freshness signal." in audited_claims

    for scenario_name in ("redteam_private_leak", "redteam_advice", "redteam_metric"):
        scenario = _scenario(scenario_name)
        summary, _baseline, report = run_scenario(scenario)
        assert report.passed is True
        assert summary.tool_run_artifact is not None
        assert scenario.expects_hard_block_flag in summary.tool_run_artifact.auditor.eval_flags
        assert summary.tool_run_artifact.auditor.repass_triggered is False
        rendered = repr(summary.model_dump(mode="json")).lower()
        assert "buying_power" not in rendered
        assert "you should" not in rendered
        assert "$1,200" not in rendered


def test_ev4_repass_repair_remains_bounded_and_clean() -> None:
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

    evidence = _scenario("full_available").build_evidence()
    summary = build_tool_mediated_agent_team_summary(
        evidence,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        role_finding_override=override,
    )
    report = evaluate_tool_mediated_report(summary)

    assert calls == ["fundamentals_analyst", "fundamentals_analyst"]
    assert report.passed is True
    assert summary.tool_run_artifact is not None
    assert summary.tool_run_artifact.auditor.repass_triggered is True
    assert "unsupported_claim" in summary.tool_run_artifact.auditor.dropped_claims


@pytest.mark.parametrize(
    ("content_by_role", "expected_flag", "blocked_text"),
        (
            (
                {"technical_analyst": "### Missing required headings\nSaved context remains available."},
                "structure_contract_blocked",
                "missing required headings",
            ),
        (
            {
                "technical_analyst": _technical_live_report_with_sentence(
                    "Saved market context had volume 12000, which was not supplied."
                )
            },
            "numeric_consistency_blocked",
            "12000",
        ),
        (
            {
                "technical_analyst": _technical_live_report_with_sentence(
                    "The market quote freshness is designated as manual despite available evidence."
                )
            },
            "category_consistency_blocked",
            "designated as manual",
        ),
    ),
)
def test_p34a_t17_eval_matrix_live_gate_drops_are_clean(
    content_by_role: dict[str, str],
    expected_flag: str,
    blocked_text: str,
) -> None:
    provider = _EvalLiveProvider(content_by_role)
    summary = build_tool_mediated_agent_team_summary(
        _scenario("full_available").build_evidence(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )
    report = evaluate_tool_mediated_report(summary)

    assert report.passed is True
    assert summary.tool_run_artifact is not None
    assert expected_flag in summary.tool_run_artifact.auditor.eval_flags
    assert blocked_text not in repr(summary.model_dump(mode="json")).lower()


def test_p34a_t17_eval_matrix_honest_gap_live_report_survives() -> None:
    report_markdown = _technical_live_report_with_sentence("Saved market context remains not reviewed.")
    provider = _EvalLiveProvider({"technical_analyst": report_markdown})

    summary = build_tool_mediated_agent_team_summary(
        _scenario("full_available").build_evidence(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
        llm_provider=provider,
        live_provider_enabled=True,
    )
    report = evaluate_tool_mediated_report(summary)
    technical = _role_summary(summary, "technical_analyst")

    assert report.passed is True
    assert technical.live_report_markdown == report_markdown
    assert "category_consistency_blocked" not in technical.warning_codes


def test_p35_t7c_d3_wrong_direction_echo_is_a_known_gate_residual() -> None:
    opposite_direction_envelope = ToolResult(
        tool_name="market_context_snapshot",
        role_name="technical_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="public",
        availability="available",
        freshness="fresh",
        evidence_refs=("public_market_context",),
        summary_payload={
            "relationships": {"close_vs_sma200": "below the 200-day average"},
        },
    )
    mock_note = (
        "Saved market context was above the 200-day average in the reviewed envelopes. "
        "Freshness remains fresh."
    )

    # T7c intentionally adds no relationship-direction gate. This records the
    # residual: 200 is structurally allowed and the category matches, so the
    # wrong-direction echo currently survives for future gate work to catch.
    assert validate_live_report_consistency(
        markdown=mock_note,
        role_results=(opposite_direction_envelope,),
    ) is None


@pytest.mark.parametrize(
    "payload",
    (
        {"nested": "provider_account_id_secret"},
        {"summary": "You should buy this."},
        {"summary": "Invented target $1,200.00"},
        {"source_url": "reviewed source label only"},
    ),
)
def test_ev5_safety_net_runs_over_summary_and_frozen_artifact(payload: dict[str, object]) -> None:
    summary, _baseline, _report = run_scenario(_scenario("full_available"))
    unsafe = _unsafe_artifact_payload(summary, payload)

    report = evaluate_tool_mediated_report(unsafe)

    assert report.passed is False
    assert any(
        finding.status == "flagged"
        and finding.check
        in {
            "forbidden_wording",
            "evidence_faithfulness",
            "prompt_privacy_values",
            "tool_no_invented_levels_or_source_leak",
        }
        for finding in report.findings
    )


def test_ev6_artifact_and_reproducibility_semantics_are_enforced() -> None:
    full, _baseline, _report = run_scenario(_scenario("full_available"))
    blocked, _blocked_baseline, _blocked_report = run_scenario(_scenario("blocked_actionability"))
    legacy, _legacy_baseline, legacy_report = run_scenario(_scenario("legacy_summary"))

    assert check_artifact_present_for_full_report(full).status == "passed"
    assert check_blocked_draft_has_no_artifact(blocked).status == "passed"
    assert check_byte_stable_regeneration(full, lambda: full).status == "passed"
    assert legacy.provider_mode == "deterministic_template"
    assert legacy.tool_run_artifact is None
    assert legacy_report.passed is True

    missing_artifact = full.model_copy(update={"tool_run_artifact": None})
    artifact_finding = check_artifact_present_for_full_report(missing_artifact)
    assert artifact_finding.status == "flagged"
    assert artifact_finding.detail == DETAIL_ARTIFACT_MISSING

    blocked_with_artifact = blocked.model_copy(update={"tool_run_artifact": full.tool_run_artifact})
    draft_finding = check_blocked_draft_has_no_artifact(blocked_with_artifact)
    assert draft_finding.status == "flagged"
    assert draft_finding.detail == DETAIL_ARTIFACT_ON_DRAFT

    changed = full.model_copy(update={"warning_codes": ("changed",)})
    stable = check_byte_stable_regeneration(full, lambda: changed)
    assert stable.status == "flagged"
    assert stable.detail == DETAIL_NOT_BYTE_STABLE


@pytest.mark.parametrize("scenario", TOOL_MEDIATED_SCENARIOS, ids=lambda scenario: scenario.name)
def test_ev_matrix_all_tool_mediated_scenarios_pass(scenario: ToolMediatedScenario) -> None:
    summary, _baseline, report = run_scenario(scenario)

    assert report.passed is True
    if scenario.expects_artifact:
        assert summary.tool_run_artifact is not None
    else:
        assert summary.tool_run_artifact is None
    if scenario.expects_public_skipped:
        assert _role_summary(summary, "fundamentals_analyst").role_status == "skipped"
    if scenario.expects_open_questions:
        assert summary.tool_run_artifact is not None
        assert summary.tool_run_artifact.open_questions
    if scenario.expects_hard_block_flag:
        assert summary.tool_run_artifact is not None
        assert scenario.expects_hard_block_flag in summary.tool_run_artifact.auditor.eval_flags
    if scenario.expects_provider_runs:
        assert summary.tool_run_artifact is not None
        assert summary.tool_run_artifact.provider_runs


def test_ev_regression_builder_summary_remains_valid_under_eval_harness() -> None:
    summary, baseline, report = run_scenario(_scenario("full_available"))

    assert summary.report_status == "full_agent_report"
    assert summary.provider_mode == "tool_mediated_mock"
    assert baseline is not None
    assert all(finding.status != "flagged" for finding in report.findings)
