"""Template-based deterministic risk report composition."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from app.services.market_data.snapshots import ReportMarketDataSnapshot
from app.services.risk.allocation import AllocationImpact
from app.services.risk.assignment import AssignmentProjection
from app.services.risk.collateral import CollateralSummary
from app.services.risk.violations import RISK_SEVERITIES, RiskRuleViolation, RiskSeverity
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS


RiskFactValue = Decimal | str | int | None


@dataclass(frozen=True)
class RiskReportSection:
    title: str
    facts: Mapping[str, RiskFactValue]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        forbidden = set(self.facts) & FORBIDDEN_REPORT_FACT_KEYS
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"risk report facts contain forbidden broker/private keys: {blocked}")


@dataclass(frozen=True)
class DeterministicRiskReport:
    account_id: str
    generated_at: datetime
    calculation_version: str
    sections: tuple[RiskReportSection, ...]
    risk_rule_violations: tuple[RiskRuleViolation, ...]
    highest_severity: RiskSeverity | None
    has_blocker: bool
    input_snapshot: ReportMarketDataSnapshot | None = None
    markdown: str = ""


def build_deterministic_risk_report(
    *,
    account_id: str,
    generated_at: datetime,
    calculation_version: str,
    option_metrics: Mapping[str, RiskFactValue],
    collateral: CollateralSummary,
    assignments: tuple[AssignmentProjection, ...],
    allocation: AllocationImpact,
    risk_rule_violations: tuple[RiskRuleViolation, ...],
    input_snapshot: ReportMarketDataSnapshot | None = None,
) -> DeterministicRiskReport:
    """Compose deterministic report sections and markdown from structured inputs."""

    if not account_id.strip():
        raise ValueError("account_id must not be empty")
    if not calculation_version.strip():
        raise ValueError("calculation_version must not be empty")

    sections = (
        RiskReportSection("Option Metrics", dict(option_metrics)),
        RiskReportSection(
            "Collateral",
            {
                "cash_available_for_collateral": collateral.total_cash,
                "collateral_reserved": collateral.total_reserved_cash,
                "free_cash_after_collateral": collateral.free_cash,
                "collateral_utilization": collateral.collateral_utilization,
            },
        ),
        RiskReportSection(
            "Assignment / Exercise Scenarios",
            {
                "scenario_count": len(assignments),
                "largest_projected_position_weight_including_cash": max(
                    (item.largest_position_weight for item in assignments),
                    default=Decimal("0"),
                ),
            },
        ),
        RiskReportSection(
            "Allocation Impact",
            {
                "total_value": allocation.total_value,
                "largest_position_symbol": allocation.largest_position_symbol,
                "largest_position_weight_excluding_cash": allocation.largest_position_weight,
            },
        ),
    )
    highest_severity = determine_highest_severity(risk_rule_violations)
    report_without_markdown = DeterministicRiskReport(
        account_id=account_id,
        generated_at=generated_at,
        calculation_version=calculation_version,
        sections=sections,
        risk_rule_violations=risk_rule_violations,
        highest_severity=highest_severity,
        has_blocker=highest_severity == "blocker",
        input_snapshot=input_snapshot,
    )
    markdown = render_risk_report_markdown(report_without_markdown)
    return DeterministicRiskReport(
        account_id=account_id,
        generated_at=generated_at,
        calculation_version=calculation_version,
        sections=sections,
        risk_rule_violations=risk_rule_violations,
        highest_severity=highest_severity,
        has_blocker=highest_severity == "blocker",
        input_snapshot=input_snapshot,
        markdown=markdown,
    )


def determine_highest_severity(violations: tuple[RiskRuleViolation, ...]) -> RiskSeverity | None:
    """Return highest deterministic violation severity, or None when clean."""

    if not violations:
        return None
    severity_rank = {severity: index for index, severity in enumerate(RISK_SEVERITIES)}
    return max((violation.severity for violation in violations), key=lambda severity: severity_rank[severity])


def render_risk_report_markdown(report: DeterministicRiskReport) -> str:
    """Render a conservative markdown report without LLM-generated claims."""

    lines = [
        "# Deterministic Risk Report",
        "",
        f"- Generated at: {report.generated_at.isoformat()}",
        f"- Calculation version: {report.calculation_version}",
        "- Source: deterministic Python services only",
        f"- Highest severity: {report.highest_severity or 'none'}",
        f"- Has blocker: {report.has_blocker}",
        "",
    ]
    for section in report.sections:
        lines.extend((f"## {section.title}", ""))
        for key, value in section.facts.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.extend(("## Risk Rule Violations", ""))
    if report.risk_rule_violations:
        for violation in report.risk_rule_violations:
            metric_text = f" ({violation.metric})" if violation.metric else ""
            lines.append(f"- [{violation.severity}] {violation.code}{metric_text}: {violation.message}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("> Manual decision support only. No trades or orders are placed by this report.")
    return "\n".join(lines)
