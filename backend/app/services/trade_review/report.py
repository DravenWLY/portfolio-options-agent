"""Deterministic trade-review report composition."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.risk.violations import RiskRuleViolation, RiskSeverity
from app.services.trade_review.journal import TradeReviewReportLink
from app.services.trade_review.models import TradeIntent
from app.services.trade_review.payoff import PayoffReview
from app.services.trade_review.portfolio_impact import PortfolioImpact
from app.services.trade_review.risk import TradeReviewRiskResult
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidationResult


@dataclass(frozen=True)
class TradeReviewReport:
    intent_id: str
    generated_at: datetime
    calculation_version: str
    intent_snapshot: dict[str, Any]
    validation: TradeIntentValidationResult
    payoff: PayoffReview
    portfolio_impact: PortfolioImpact
    risk_rule_violations: tuple[RiskRuleViolation, ...]
    highest_severity: RiskSeverity | None
    has_blocker: bool
    data_freshness_snapshot: dict[str, Any]
    market_snapshot: TradeReviewMarketSnapshot
    markdown: str
    report_link: TradeReviewReportLink | None = None


@dataclass(frozen=True)
class AgentSafePortfolioImpact:
    """Portfolio-impact view safe for agent prompts by default.

    Absolute cash/account values stay owner-facing only. Agents get freshness,
    review state, exposure shape, and notes without account identifiers or raw
    brokerage payloads.
    """

    broker_freshness_status: str
    market_freshness_status: str
    market_manual_review_required: bool
    assignment_share_delta: Decimal
    exercise_share_delta: Decimal
    concentration_symbol: str | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TradeReviewAgentProjection:
    intent_id: str
    generated_at: datetime
    calculation_version: str
    intent_summary: dict[str, Any]
    validation: TradeIntentValidationResult
    payoff: PayoffReview
    portfolio_impact: AgentSafePortfolioImpact
    risk_rule_violations: tuple[RiskRuleViolation, ...]
    highest_severity: RiskSeverity | None
    has_blocker: bool
    data_freshness_snapshot: dict[str, Any]
    market_snapshot: TradeReviewMarketSnapshot


def build_trade_review_report(
    *,
    intent: TradeIntent,
    generated_at: datetime,
    validation: TradeIntentValidationResult,
    payoff: PayoffReview,
    portfolio_impact: PortfolioImpact,
    risk: TradeReviewRiskResult,
    market_snapshot: TradeReviewMarketSnapshot,
    report_link: TradeReviewReportLink | None = None,
) -> TradeReviewReport:
    """Build a reproducible deterministic report from structured inputs."""

    intent_snapshot = intent.to_snapshot_dict()
    report_without_markdown = TradeReviewReport(
        intent_id=intent.intent_id,
        generated_at=generated_at,
        calculation_version=intent.calculation_version,
        intent_snapshot=intent_snapshot,
        validation=validation,
        payoff=payoff,
        portfolio_impact=portfolio_impact,
        risk_rule_violations=risk.violations,
        highest_severity=risk.highest_severity,
        has_blocker=risk.has_blocker,
        data_freshness_snapshot=intent_snapshot["data_freshness_snapshot"],
        market_snapshot=market_snapshot,
        markdown="",
        report_link=report_link,
    )
    markdown = render_trade_review_markdown(report_without_markdown)
    return TradeReviewReport(
        intent_id=report_without_markdown.intent_id,
        generated_at=report_without_markdown.generated_at,
        calculation_version=report_without_markdown.calculation_version,
        intent_snapshot=report_without_markdown.intent_snapshot,
        validation=validation,
        payoff=payoff,
        portfolio_impact=portfolio_impact,
        risk_rule_violations=risk.violations,
        highest_severity=risk.highest_severity,
        has_blocker=risk.has_blocker,
        data_freshness_snapshot=report_without_markdown.data_freshness_snapshot,
        market_snapshot=market_snapshot,
        markdown=markdown,
        report_link=report_link,
    )


def to_agent_safe_projection(report: TradeReviewReport) -> TradeReviewAgentProjection:
    """Return the default agent-facing view without account ids or cash values."""

    return TradeReviewAgentProjection(
        intent_id=report.intent_id,
        generated_at=report.generated_at,
        calculation_version=report.calculation_version,
        intent_summary=_redact_intent_summary(report.intent_snapshot),
        validation=report.validation,
        payoff=report.payoff,
        portfolio_impact=AgentSafePortfolioImpact(
            broker_freshness_status=report.portfolio_impact.broker_freshness_status,
            market_freshness_status=report.portfolio_impact.market_freshness_status,
            market_manual_review_required=report.portfolio_impact.market_manual_review_required,
            assignment_share_delta=report.portfolio_impact.assignment_share_delta,
            exercise_share_delta=report.portfolio_impact.exercise_share_delta,
            concentration_symbol=report.portfolio_impact.concentration_symbol,
            notes=report.portfolio_impact.notes,
        ),
        risk_rule_violations=report.risk_rule_violations,
        highest_severity=report.highest_severity,
        has_blocker=report.has_blocker,
        data_freshness_snapshot=dict(report.data_freshness_snapshot),
        market_snapshot=report.market_snapshot,
    )


def render_trade_review_markdown(report: TradeReviewReport) -> str:
    """Render conservative markdown without advice, recommendations, or execution language."""

    lines = [
        "# Deterministic Trade Review",
        "",
        f"- Intent id: {report.intent_id}",
        f"- Generated at: {report.generated_at.isoformat()}",
        f"- Calculation version: {report.calculation_version}",
        "- Source: deterministic Python services only",
        f"- Highest severity: {report.highest_severity or 'none'}",
        f"- Has blocker: {report.has_blocker}",
        "",
        "## Intent",
        "",
        f"- Asset class: {report.intent_snapshot['asset_class']}",
        f"- Intent type: {report.intent_snapshot['intent_type']}",
        f"- Status: {report.intent_snapshot['status']}",
        "",
        "## Portfolio Impact",
        "",
        f"- Cash delta: {_format_decimal(report.portfolio_impact.cash_delta)}",
        f"- Premium cash delta: {_format_decimal(report.portfolio_impact.premium_cash_delta)}",
        f"- Collateral delta: {_format_decimal(report.portfolio_impact.collateral_delta)}",
        f"- Projected free cash: {_format_decimal(report.portfolio_impact.projected_free_cash)}",
        "",
        "## Scenario Payoff",
        "",
    ]
    for point in report.payoff.points:
        lines.append(
            f"- {point.label}: underlying {_format_decimal(point.underlying_price)}, "
            f"scenario P/L {_format_decimal(point.scenario_pnl)}"
        )
    lines.extend(("", "## Risk Rule Violations", ""))
    if report.risk_rule_violations:
        for violation in report.risk_rule_violations:
            lines.append(f"- [{violation.severity}] {violation.code}: {violation.message}")
    else:
        lines.append("- None")
    lines.extend(
        (
            "",
            "> Review and scenario analysis only. This report does not recommend, place, route, or manage trades.",
        )
    )
    return "\n".join(lines)


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "unknown"
    return str(value)


def _redact_intent_summary(intent_snapshot: dict[str, Any]) -> dict[str, Any]:
    safe_keys = {
        "intent_id",
        "asset_class",
        "intent_type",
        "created_at",
        "calculation_version",
        "status",
        "symbol",
        "action",
        "quantity",
        "price_assumption",
        "strategy_type",
        "underlying_symbol",
        "legs",
    }
    safe = {key: intent_snapshot[key] for key in safe_keys if key in intent_snapshot}
    if "legs" in safe:
        safe["legs"] = tuple(_redact_option_leg(leg) for leg in safe["legs"])
    return safe


def _redact_option_leg(leg: dict[str, Any]) -> dict[str, Any]:
    safe_keys = {
        "underlying_symbol",
        "option_type",
        "leg_action",
        "expiration_date",
        "strike",
        "quantity",
        "premium",
        "multiplier",
        "occ_symbol",
        "support_status",
        "unsupported_reason",
    }
    return {key: leg[key] for key in safe_keys if key in leg}
