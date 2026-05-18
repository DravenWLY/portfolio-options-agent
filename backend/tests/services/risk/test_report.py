from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.market_data.snapshots import MarketDataSnapshotReference, ReportMarketDataSnapshot
from app.services.risk.allocation import AllocationPosition, AllocationTarget, calculate_allocation_impact
from app.services.risk.assignment import AssignmentScenario, PositionHolding, project_assignment_scenario
from app.services.risk.collateral import CollateralRequirement, calculate_collateral_summary
from app.services.risk.report import build_deterministic_risk_report, render_risk_report_markdown
from app.services.risk.violations import RiskRuleViolation


pytestmark = [pytest.mark.unit]


def _input_snapshot() -> ReportMarketDataSnapshot:
    captured_at = datetime(2026, 5, 18, 15, 30, tzinfo=UTC)
    reference = MarketDataSnapshotReference(
        snapshot_id="quote-snapshot-demo",
        kind="option_quote",
        purpose="report_input_snapshot",
        provider="manual",
        stable_key="HOOD260618C00085000",
        captured_at=captured_at,
        quote_time=captured_at,
        freshness_scope="market_quote",
        data_mode="manual",
        freshness_status="manual",
        actionability_status="analysis_only",
    )
    return ReportMarketDataSnapshot(
        report_input_snapshot_id="report-input-demo",
        quote_references=(reference,),
        chain_references=(),
        captured_at=captured_at,
    )


def test_deterministic_risk_report_composes_structured_sections_and_markdown() -> None:
    collateral = calculate_collateral_summary(
        account_id="acct-demo",
        total_cash=Decimal("10000"),
        requirements=(
            CollateralRequirement("put-1", "short_option", Decimal("8000")),
        ),
    )
    assignment = project_assignment_scenario(
        cash=Decimal("10000"),
        holdings=(PositionHolding("VOO", Decimal("10"), Decimal("5000")),),
        scenario=AssignmentScenario(
            action="short_put_assignment",
            underlying_symbol="HOOD",
            contracts=Decimal("1"),
            strike=Decimal("80"),
            projected_underlying_price=Decimal("77"),
        ),
    )
    allocation = calculate_allocation_impact(
        positions=(
            AllocationPosition("VOO", Decimal("5000")),
            AllocationPosition("HOOD", Decimal("7700")),
        ),
        targets=(
            AllocationTarget("VOO", Decimal("0.50")),
            AllocationTarget("HOOD", Decimal("0.50")),
        ),
    )
    violation = RiskRuleViolation(
        code="high_collateral_utilization",
        severity="violation",
        message="Collateral utilization is above the synthetic threshold.",
        source="risk_rule_engine",
        metric="collateral_utilization",
        actual=Decimal("0.8"),
        threshold=Decimal("0.75"),
    )

    report = build_deterministic_risk_report(
        account_id="acct-demo",
        generated_at=datetime(2026, 5, 18, 15, 30, tzinfo=UTC),
        calculation_version="risk-engine-v0",
        option_metrics={"premium_yield": Decimal("0.025")},
        collateral=collateral,
        assignments=(assignment,),
        allocation=allocation,
        risk_rule_violations=(violation,),
        input_snapshot=_input_snapshot(),
    )

    assert report.sections[0].title == "Option Metrics"
    assert report.sections[1].facts["free_cash_after_collateral"] == Decimal("2000")
    assert report.risk_rule_violations == (violation,)
    assert report.highest_severity == "violation"
    assert report.has_blocker is False
    assert report.input_snapshot is not None
    assert report.input_snapshot.report_input_snapshot_id == "report-input-demo"
    assert "[violation] high_collateral_utilization" in report.markdown
    assert "Highest severity: violation" in report.markdown
    assert "Has blocker: False" in report.markdown
    assert "Source: deterministic Python services only" in report.markdown
    assert "No trades or orders are placed" in report.markdown
    assert "acct-demo" not in report.markdown


def test_report_markdown_renders_no_violations_state() -> None:
    markdown = render_risk_report_markdown(
        build_deterministic_risk_report(
            account_id="acct-demo",
            generated_at=datetime(2026, 5, 18, 15, 30, tzinfo=UTC),
            calculation_version="risk-engine-v0",
            option_metrics={},
            collateral=calculate_collateral_summary(
                account_id="acct-demo",
                total_cash=Decimal("0"),
            ),
            assignments=(),
            allocation=calculate_allocation_impact(positions=()),
            risk_rule_violations=(),
            input_snapshot=None,
        )
    )

    assert "## Risk Rule Violations" in markdown
    assert "- None" in markdown
    assert "Highest severity: none" in markdown


def test_report_highest_severity_and_blocker_are_deterministic() -> None:
    report = build_deterministic_risk_report(
        account_id="acct-demo",
        generated_at=datetime(2026, 5, 18, 15, 30, tzinfo=UTC),
        calculation_version="risk-engine-v0",
        option_metrics={},
        collateral=calculate_collateral_summary(account_id="acct-demo", total_cash=Decimal("0")),
        assignments=(),
        allocation=calculate_allocation_impact(positions=()),
        risk_rule_violations=(
            RiskRuleViolation("warn", "warning", "Synthetic warning.", "risk_rule_engine"),
            RiskRuleViolation("block", "blocker", "Synthetic blocker.", "risk_rule_engine"),
            RiskRuleViolation("info", "info", "Synthetic info.", "risk_rule_engine"),
        ),
        input_snapshot=None,
    )

    assert report.highest_severity == "blocker"
    assert report.has_blocker is True


def test_report_rejects_forbidden_private_fact_keys() -> None:
    with pytest.raises(ValueError, match="forbidden broker/private keys"):
        build_deterministic_risk_report(
            account_id="acct-demo",
            generated_at=datetime(2026, 5, 18, 15, 30, tzinfo=UTC),
            calculation_version="risk-engine-v0",
            option_metrics={"raw_payload": "nope"},
            collateral=calculate_collateral_summary(account_id="acct-demo", total_cash=Decimal("0")),
            assignments=(),
            allocation=calculate_allocation_impact(positions=()),
            risk_rule_violations=(),
            input_snapshot=None,
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"account_id": "", "calculation_version": "v"}, "account_id"),
        ({"account_id": "acct", "calculation_version": ""}, "calculation_version"),
    ],
)
def test_report_rejects_invalid_required_fields(kwargs, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build_deterministic_risk_report(
            generated_at=datetime(2026, 5, 18, 15, 30, tzinfo=UTC),
            option_metrics={},
            collateral=calculate_collateral_summary(account_id="acct", total_cash=Decimal("0")),
            assignments=(),
            allocation=calculate_allocation_impact(positions=()),
            risk_rule_violations=(),
            input_snapshot=None,
            **kwargs,
        )
