import pytest

from app.services.agent_eval import (
    EvalFinding,
    EvalReport,
    check_evidence_consistency,
    check_evidence_faithfulness,
    check_forbidden_wording,
    check_generated_output_safety,
    check_prompt_privacy_keys,
    check_prompt_privacy_values,
    check_role_boundaries,
    classify_failures,
    evaluate_agent_review_run,
    evaluate_generated_output,
)


pytestmark = [pytest.mark.unit]

_SAFE_ROLE_TEXTS = (
    ("fundamentals_analyst", "Analysis-only commentary over public company evidence."),
    ("risk_management_agent", "Analysis-only commentary over sanitized deterministic evidence."),
)
_SAFE_SYNTHESIS = "Mock portfolio-team synthesis. Deterministic backend services own all calculations."

_SUMMARY = {
    "review_flow_label": "equity_purchase_review",
    "actionability_summary": {"review_actionability_status": "analysis_only", "reason_count": 0},
    "risk_summary": {"has_blocker": False, "risk_rule_count": 0},
    "portfolio_shape": {"context_available": False},
    "caveat_codes": (),
}


# -- forbidden wording -------------------------------------------------------


def test_forbidden_wording_flags_advice() -> None:
    finding = check_forbidden_wording({"text": "you should buy this name now"})
    assert finding.status == "flagged"
    assert finding.detail is not None


def test_forbidden_wording_passes_safe_text() -> None:
    assert check_forbidden_wording({"text": _SAFE_SYNTHESIS}).status == "passed"


# -- faithfulness / ungrounded figures ---------------------------------------


@pytest.mark.parametrize("text", ("Price target $250.00", "about 30% upside", "delta: 5"))
def test_faithfulness_flags_ungrounded_figures(text: str) -> None:
    assert check_evidence_faithfulness({"text": text}).status == "flagged"


def test_faithfulness_passes_clean_commentary() -> None:
    assert check_evidence_faithfulness({"role_texts": list(_SAFE_ROLE_TEXTS)}).status == "passed"


# -- privacy -----------------------------------------------------------------


def test_privacy_keys_flags_forbidden_key() -> None:
    assert check_prompt_privacy_keys({"cash_balance": "1000.00"}).status == "flagged"


def test_privacy_keys_passes_safe_payload() -> None:
    assert check_prompt_privacy_keys({"headline": "synthetic public overview"}).status == "passed"


def test_privacy_values_flags_private_token() -> None:
    assert check_prompt_privacy_values({"text": "the account_id is hidden"}).status == "flagged"


def test_privacy_values_flags_secret_like_value() -> None:
    secret = "AIza" + "B" * 30
    assert check_prompt_privacy_values({"text": f"key {secret}"}).status == "flagged"


def test_privacy_values_passes_safe() -> None:
    assert check_prompt_privacy_values({"text": "synthetic public commentary"}).status == "passed"


# -- composite ---------------------------------------------------------------


def test_generated_output_safety_composite() -> None:
    safe = (
        check_forbidden_wording({}),
        check_evidence_faithfulness({}),
        check_prompt_privacy_keys({}),
        check_prompt_privacy_values({}),
    )
    composite = check_generated_output_safety(
        wording=safe[0], faithfulness=safe[1], privacy_keys=safe[2], privacy_values=safe[3]
    )
    assert composite.status == "passed"

    bad_faithfulness = check_evidence_faithfulness({"text": "$5 target"})
    composite_bad = check_generated_output_safety(
        wording=safe[0], faithfulness=bad_faithfulness, privacy_keys=safe[2], privacy_values=safe[3]
    )
    assert composite_bad.status == "flagged"


# -- role boundary -----------------------------------------------------------


def test_role_boundary_passes_when_public_clean() -> None:
    observations = (
        ("fundamentals_analyst", True, False),
        ("risk_management_agent", False, True),
    )
    assert check_role_boundaries(observations).status == "passed"


def test_role_boundary_flags_public_receiving_agent_safe() -> None:
    observations = (("fundamentals_analyst", True, True),)
    assert check_role_boundaries(observations).status == "flagged"


# -- evidence consistency ----------------------------------------------------


def test_evidence_consistency_passes_when_equal() -> None:
    assert check_evidence_consistency(dict(_SUMMARY), dict(_SUMMARY)).status == "passed"


def test_evidence_consistency_flags_when_diverged() -> None:
    diverged = dict(_SUMMARY)
    diverged["review_flow_label"] = "fund_purchase_review"
    assert check_evidence_consistency(diverged, dict(_SUMMARY)).status == "flagged"


def test_evidence_consistency_deferred_when_missing() -> None:
    assert check_evidence_consistency(None, dict(_SUMMARY)).status == "deferred"


# -- failure classification --------------------------------------------------


def test_classify_failures_clean_and_partial() -> None:
    assert classify_failures(()).status == "passed"
    assert classify_failures(()).detail == "clean_run"
    assert classify_failures(("news_analyst:rate_limited",)).detail == "partial_run"


# -- harness aggregates ------------------------------------------------------


def test_evaluate_generated_output_returns_all_findings() -> None:
    findings = evaluate_generated_output(role_texts=_SAFE_ROLE_TEXTS, final_synthesis=_SAFE_SYNTHESIS)
    checks = {finding.check for finding in findings}
    assert checks == {
        "generated_output_safety",
        "forbidden_wording",
        "evidence_faithfulness",
        "prompt_privacy_keys",
        "prompt_privacy_values",
    }
    assert all(finding.status == "passed" for finding in findings)


def test_evaluate_agent_review_run_full_report_passes() -> None:
    report = evaluate_agent_review_run(
        role_texts=_SAFE_ROLE_TEXTS,
        final_synthesis=_SAFE_SYNTHESIS,
        run_summary=dict(_SUMMARY),
        expected_summary=dict(_SUMMARY),
        role_boundary_observations=(("fundamentals_analyst", True, False),),
        provider_warnings=(),
    )
    assert isinstance(report, EvalReport)
    assert report.passed is True
    flag_dicts = report.to_flag_dicts()
    assert {flag["check"] for flag in flag_dicts} >= {
        "generated_output_safety",
        "evidence_faithfulness",
        "role_boundary",
        "evidence_consistency",
        "failure_classification",
    }


def test_eval_report_flags_unsafe_generated_text() -> None:
    report = evaluate_agent_review_run(
        role_texts=(("fundamentals_analyst", "Price target $300 with guaranteed return"),),
        final_synthesis=None,
    )
    assert report.passed is False
    flagged_checks = {finding.check for finding in report.flagged}
    assert "evidence_faithfulness" in flagged_checks
    assert "generated_output_safety" in flagged_checks


def test_eval_finding_detail_is_safe_constant() -> None:
    finding = EvalFinding(check="forbidden_wording", status="flagged", detail="prohibited advice wording detected")
    assert finding.status == "flagged"
