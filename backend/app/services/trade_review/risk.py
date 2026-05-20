"""Risk-rule integration for deterministic trade review outputs."""

from dataclasses import dataclass
from decimal import Decimal

from app.services.risk.report import determine_highest_severity
from app.services.risk.violations import (
    RiskRuleViolation,
    RiskSeverity,
    evaluate_broker_freshness,
    evaluate_market_actionability,
)
from app.services.trade_review.portfolio_impact import PortfolioImpact
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidationResult


@dataclass(frozen=True)
class TradeReviewRiskResult:
    violations: tuple[RiskRuleViolation, ...]
    highest_severity: RiskSeverity | None
    has_blocker: bool


class TradeReviewRiskEngine:
    """Combine validation, freshness, and impact signals into risk violations."""

    def evaluate(
        self,
        *,
        validation: TradeIntentValidationResult,
        portfolio_impact: PortfolioImpact,
        market_snapshot: TradeReviewMarketSnapshot,
    ) -> TradeReviewRiskResult:
        violations: list[RiskRuleViolation] = []
        violations.extend(_validation_to_violations(validation))
        violations.extend(evaluate_broker_freshness(freshness_status=portfolio_impact.broker_freshness_status))
        violations.extend(_evaluate_market_freshness_status(portfolio_impact.market_freshness_status))
        for reference in market_snapshot.quote_references + market_snapshot.chain_references:
            violations.extend(
                evaluate_market_actionability(
                    actionability_status=reference.actionability_status,
                    source=f"market_quote:{reference.kind}",
                )
            )
        if market_snapshot.manual_review_required and not market_snapshot.quote_references and not market_snapshot.chain_references:
            violations.append(
                RiskRuleViolation(
                    code="market_snapshot_manual_review_required",
                    severity="warning",
                    message="Market snapshot is missing or requires manual review.",
                    source="market_quote",
                )
            )
        if portfolio_impact.projected_free_cash is not None and portfolio_impact.projected_free_cash < 0:
            violations.append(
                RiskRuleViolation(
                    code="projected_free_cash_negative",
                    severity="blocker",
                    message="Projected free cash is negative after this reviewed intent.",
                    source="portfolio_impact",
                    metric="projected_free_cash",
                    actual=portfolio_impact.projected_free_cash,
                    threshold=Decimal("0"),
                )
            )
        if portfolio_impact.collateral_delta > 0 and portfolio_impact.projected_free_cash is None:
            violations.append(
                RiskRuleViolation(
                    code="cash_context_missing_for_collateral",
                    severity="blocker",
                    message="Collateral impact cannot be evaluated without cash context.",
                    source="portfolio_impact",
                )
            )
        highest = determine_highest_severity(tuple(violations))
        return TradeReviewRiskResult(
            violations=tuple(violations),
            highest_severity=highest,
            has_blocker=highest == "blocker",
    )


def _evaluate_market_freshness_status(freshness_status: str) -> tuple[RiskRuleViolation, ...]:
    if freshness_status == "fresh":
        return ()
    if freshness_status in {"manual", "delayed", "eod_only"}:
        return (
            RiskRuleViolation(
                code=f"market_quote_{freshness_status}",
                severity="warning",
                message="Market quote input is not live and should be reviewed as analysis-only.",
                source="market_quote",
                actual=freshness_status,
            ),
        )
    if freshness_status in {"stale", "unknown", "error"}:
        return (
            RiskRuleViolation(
                code=f"market_quote_{freshness_status}",
                severity="blocker",
                message="Market quote freshness is not sufficient for deterministic trade review.",
                source="market_quote",
                actual=freshness_status,
            ),
        )
    return (
        RiskRuleViolation(
            code="market_quote_unknown_freshness_status",
            severity="blocker",
            message="Market quote freshness status is unknown.",
            source="market_quote",
            actual=freshness_status,
        ),
    )


def _validation_to_violations(validation: TradeIntentValidationResult) -> tuple[RiskRuleViolation, ...]:
    severity_map: dict[str, RiskSeverity] = {
        "info": "info",
        "warning": "warning",
        "blocker": "blocker",
    }
    return tuple(
        RiskRuleViolation(
            code=f"validation_{finding.code}",
            severity=severity_map[finding.severity],
            message=finding.message,
            source="trade_intent_validation",
            metric=finding.field,
        )
        for finding in validation.findings
    )
