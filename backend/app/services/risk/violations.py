"""Deterministic risk-rule violation evaluation.

Severity rationale:

- Market quote stale/unknown/provider-error states are blockers for actionable
  risk analysis because the deterministic engine cannot safely price option
  metrics from unusable quote inputs.
- Broker portfolio stale/cached/delayed/unknown states are warnings because the
  current account snapshot may still be usable for review when clearly labelled
  stale. Broker `error` and `reauth_required` states are blockers because the
  account snapshot cannot be trusted until the connection is repaired.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Mapping


RiskSeverity = Literal["info", "warning", "violation", "blocker"]
RuleOperator = Literal[">", ">=", "<", "<=", "==", "!="]

RISK_SEVERITIES: tuple[str, ...] = ("info", "warning", "violation", "blocker")
RULE_OPERATORS: tuple[str, ...] = (">", ">=", "<", "<=", "==", "!=")


@dataclass(frozen=True)
class RiskRuleViolation:
    code: str
    severity: RiskSeverity
    message: str
    source: str
    metric: str | None = None
    actual: Decimal | str | None = None
    threshold: Decimal | str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code must not be empty")
        if self.severity not in RISK_SEVERITIES:
            raise ValueError("severity must be one of: info, warning, violation, blocker")
        if not self.message.strip():
            raise ValueError("message must not be empty")
        if not self.source.strip():
            raise ValueError("source must not be empty")


@dataclass(frozen=True)
class RiskThresholdRule:
    code: str
    severity: RiskSeverity
    metric: str
    operator: RuleOperator
    threshold: Decimal
    message: str
    source: str = "risk_rule_engine"

    def __post_init__(self) -> None:
        if not self.metric.strip():
            raise ValueError("metric must not be empty")
        if self.operator not in RULE_OPERATORS:
            raise ValueError("operator must be a supported comparison operator")
        RiskRuleViolation(
            code=self.code,
            severity=self.severity,
            message=self.message,
            source=self.source,
        )


def _matches(actual: Decimal, operator: RuleOperator, threshold: Decimal) -> bool:
    if operator == ">":
        return actual > threshold
    if operator == ">=":
        return actual >= threshold
    if operator == "<":
        return actual < threshold
    if operator == "<=":
        return actual <= threshold
    if operator == "==":
        return actual == threshold
    if operator == "!=":
        return actual != threshold
    raise ValueError("operator must be a supported comparison operator")


def evaluate_threshold_rules(
    *,
    metrics: Mapping[str, Decimal],
    rules: tuple[RiskThresholdRule, ...],
) -> tuple[RiskRuleViolation, ...]:
    """Evaluate deterministic numeric threshold rules."""

    violations: list[RiskRuleViolation] = []
    for rule in rules:
        if rule.metric not in metrics:
            violations.append(
                RiskRuleViolation(
                    code=f"{rule.code}_missing_metric",
                    severity="blocker",
                    message=f"Required metric '{rule.metric}' is missing.",
                    source=rule.source,
                    metric=rule.metric,
                    threshold=rule.threshold,
                )
            )
            continue
        actual = metrics[rule.metric]
        if _matches(actual, rule.operator, rule.threshold):
            violations.append(
                RiskRuleViolation(
                    code=rule.code,
                    severity=rule.severity,
                    message=rule.message,
                    source=rule.source,
                    metric=rule.metric,
                    actual=actual,
                    threshold=rule.threshold,
                )
            )
    return tuple(violations)


def evaluate_market_actionability(
    *,
    actionability_status: str,
    source: str = "market_quote",
) -> tuple[RiskRuleViolation, ...]:
    """Convert market quote actionability into deterministic risk violations."""

    if actionability_status.startswith("blocked_"):
        return (
            RiskRuleViolation(
                code=actionability_status,
                severity="blocker",
                message="Market quote input is blocked for actionable analysis.",
                source=source,
                actual=actionability_status,
            ),
        )
    if actionability_status in {"analysis_only", "manual_review_required"}:
        return (
            RiskRuleViolation(
                code=f"market_quote_{actionability_status}",
                severity="warning",
                message="Market quote input is analysis-only or requires manual review.",
                source=source,
                actual=actionability_status,
            ),
        )
    if actionability_status == "actionable_snapshot":
        return ()
    return (
        RiskRuleViolation(
            code="market_quote_unknown_actionability",
            severity="blocker",
            message="Market quote actionability status is unknown.",
            source=source,
            actual=actionability_status,
        ),
    )


def evaluate_broker_freshness(
    *,
    freshness_status: str,
    source: str = "broker_portfolio",
) -> tuple[RiskRuleViolation, ...]:
    """Convert broker portfolio freshness into deterministic risk violations."""

    if freshness_status == "fresh":
        return ()
    if freshness_status in {"cached", "delayed", "stale", "unknown"}:
        return (
            RiskRuleViolation(
                code=f"broker_data_{freshness_status}",
                severity="warning",
                message="Broker portfolio data is not confirmed fresh.",
                source=source,
                actual=freshness_status,
            ),
        )
    if freshness_status in {"error", "reauth_required"}:
        return (
            RiskRuleViolation(
                code=f"broker_data_{freshness_status}",
                severity="blocker",
                message="Broker portfolio data cannot be trusted until resolved.",
                source=source,
                actual=freshness_status,
            ),
        )
    return (
        RiskRuleViolation(
            code="broker_data_unknown_status",
            severity="blocker",
            message="Broker portfolio freshness status is unknown.",
            source=source,
            actual=freshness_status,
        ),
    )
