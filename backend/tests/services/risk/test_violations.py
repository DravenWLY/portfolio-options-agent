from decimal import Decimal

import pytest

from app.services.risk.violations import (
    RiskRuleViolation,
    RiskThresholdRule,
    evaluate_broker_freshness,
    evaluate_market_actionability,
    evaluate_threshold_rules,
)


pytestmark = [pytest.mark.unit]


def test_threshold_rules_emit_structured_severity_tagged_violations() -> None:
    violations = evaluate_threshold_rules(
        metrics={
            "collateral_utilization": Decimal("0.82"),
            "largest_position_weight": Decimal("0.38"),
        },
        rules=(
            RiskThresholdRule(
                code="high_collateral_utilization",
                severity="violation",
                metric="collateral_utilization",
                operator=">",
                threshold=Decimal("0.75"),
                message="Collateral utilization is above the synthetic threshold.",
            ),
            RiskThresholdRule(
                code="large_position",
                severity="warning",
                metric="largest_position_weight",
                operator=">",
                threshold=Decimal("0.40"),
                message="Largest position exceeds target concentration.",
            ),
        ),
    )

    assert len(violations) == 1
    assert violations[0].code == "high_collateral_utilization"
    assert violations[0].severity == "violation"
    assert violations[0].actual == Decimal("0.82")
    assert violations[0].threshold == Decimal("0.75")


def test_missing_metric_is_a_blocker() -> None:
    violations = evaluate_threshold_rules(
        metrics={},
        rules=(
            RiskThresholdRule(
                code="missing_test",
                severity="warning",
                metric="required_metric",
                operator=">",
                threshold=Decimal("0"),
                message="Synthetic rule",
            ),
        ),
    )

    assert violations[0].code == "missing_test_missing_metric"
    assert violations[0].severity == "blocker"


@pytest.mark.parametrize(
    ("status", "expected_severity", "expected_count"),
    [
        ("actionable_snapshot", None, 0),
        ("analysis_only", "warning", 1),
        ("manual_review_required", "warning", 1),
        ("blocked_stale_quote", "blocker", 1),
        ("unexpected", "blocker", 1),
    ],
)
def test_market_actionability_maps_to_violations(status, expected_severity, expected_count) -> None:
    violations = evaluate_market_actionability(actionability_status=status)

    assert len(violations) == expected_count
    if expected_count:
        assert violations[0].severity == expected_severity
        assert violations[0].source == "market_quote"


@pytest.mark.parametrize(
    ("status", "expected_severity", "expected_count"),
    [
        ("fresh", None, 0),
        ("cached", "warning", 1),
        ("delayed", "warning", 1),
        ("stale", "warning", 1),
        ("unknown", "warning", 1),
        ("error", "blocker", 1),
        ("reauth_required", "blocker", 1),
        ("weird", "blocker", 1),
    ],
)
def test_broker_freshness_maps_to_violations(status, expected_severity, expected_count) -> None:
    violations = evaluate_broker_freshness(freshness_status=status)

    assert len(violations) == expected_count
    if expected_count:
        assert violations[0].severity == expected_severity
        assert violations[0].source == "broker_portfolio"


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: RiskRuleViolation("", "warning", "message", "source"),
            "code",
        ),
        (
            lambda: RiskRuleViolation("code", "bad", "message", "source"),
            "severity",
        ),
        (
            lambda: RiskRuleViolation("code", "warning", "", "source"),
            "message",
        ),
        (
            lambda: RiskRuleViolation("code", "warning", "message", ""),
            "source",
        ),
        (
            lambda: RiskThresholdRule("code", "warning", "", ">", Decimal("1"), "message"),
            "metric",
        ),
        (
            lambda: RiskThresholdRule("code", "warning", "metric", "bad", Decimal("1"), "message"),
            "operator",
        ),
    ],
)
def test_violation_inputs_are_validated(factory, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        factory()
