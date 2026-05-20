from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from app.services.trade_review.models import (
    ETFTradeIntent,
    OptionLeg,
    OptionStrategyIntent,
    StockTradeIntent,
    TradeIntent,
)


ValidationSeverity = Literal["info", "warning", "blocker"]
VALIDATION_SEVERITIES: tuple[str, ...] = ("info", "warning", "blocker")


"""Validation severity is a pre-review readiness signal.

It is intentionally distinct from Phase 13 risk-rule severity, which includes
`violation` for deterministic portfolio/risk outcomes. Validation findings say
whether a proposed intent is clean, needs manual review, or is blocked before
the deterministic trade-review engine runs.
"""


@dataclass(frozen=True)
class TradeIntentValidationFinding:
    code: str
    severity: ValidationSeverity
    message: str
    field: str | None = None


@dataclass(frozen=True)
class TradeIntentValidationResult:
    intent_id: str
    findings: tuple[TradeIntentValidationFinding, ...]
    manual_review_required: bool
    blocked: bool
    highest_severity: ValidationSeverity | None
    is_clean: bool

    @property
    def can_reach_deterministic_review(self) -> bool:
        """True means not blocked; callers must still inspect `is_clean`."""

        return not self.blocked


class TradeIntentValidator:
    """Structured validation before deterministic trade review."""

    def validate(self, intent: TradeIntent, *, today: date | None = None) -> TradeIntentValidationResult:
        findings: list[TradeIntentValidationFinding] = []
        if intent.status == "blocked":
            findings.append(
                TradeIntentValidationFinding(
                    code="intent_status_blocked",
                    severity="blocker",
                    message="Trade intent is blocked before deterministic review.",
                    field="status",
                )
            )
        if intent.status == "manual_review_required":
            findings.append(
                TradeIntentValidationFinding(
                    code="intent_manual_review_required",
                    severity="warning",
                    message="Trade intent is marked for manual review.",
                    field="status",
                )
            )

        if isinstance(intent, (StockTradeIntent, ETFTradeIntent)):
            self._validate_stock_or_etf(intent, findings)
        elif isinstance(intent, OptionStrategyIntent):
            self._validate_option_strategy(intent, findings, today=today)
        else:
            findings.append(
                TradeIntentValidationFinding(
                    code="unsupported_intent_type",
                    severity="blocker",
                    message="Unsupported trade intent type.",
                    field="intent_type",
                )
            )

        highest_severity = _determine_highest_severity(tuple(findings))
        blocked = highest_severity == "blocker"
        manual_review_required = blocked or any(finding.severity == "warning" for finding in findings)
        return TradeIntentValidationResult(
            intent_id=intent.intent_id,
            findings=tuple(findings),
            manual_review_required=manual_review_required,
            blocked=blocked,
            highest_severity=highest_severity,
            is_clean=not findings,
        )

    def _validate_stock_or_etf(
        self,
        intent: StockTradeIntent | ETFTradeIntent,
        findings: list[TradeIntentValidationFinding],
    ) -> None:
        if intent.price_assumption is None:
            findings.append(
                TradeIntentValidationFinding(
                    code="price_assumption_missing",
                    severity="warning",
                    message="No price assumption was supplied; review requires a quote or manual price.",
                    field="price_assumption",
                )
            )

    def _validate_option_strategy(
        self,
        intent: OptionStrategyIntent,
        findings: list[TradeIntentValidationFinding],
        *,
        today: date | None,
    ) -> None:
        for index, leg in enumerate(intent.legs):
            self._validate_option_leg(leg, findings, field_prefix=f"legs[{index}]", today=today)

        if intent.strategy_type == "long_call" and not self._matches_single_leg(intent, "buy_to_open", "call"):
            findings.append(self._strategy_shape_blocker("long_call"))
        if intent.strategy_type == "long_put" and not self._matches_single_leg(intent, "buy_to_open", "put"):
            findings.append(self._strategy_shape_blocker("long_put"))
        if intent.strategy_type == "cash_secured_put" and not self._matches_single_leg(intent, "sell_to_open", "put"):
            findings.append(self._strategy_shape_blocker("cash_secured_put"))
        if intent.strategy_type == "covered_call" and not self._matches_single_leg(intent, "sell_to_open", "call"):
            findings.append(self._strategy_shape_blocker("covered_call"))

    def _validate_option_leg(
        self,
        leg: OptionLeg,
        findings: list[TradeIntentValidationFinding],
        *,
        field_prefix: str,
        today: date | None,
    ) -> None:
        if leg.premium is None:
            findings.append(
                TradeIntentValidationFinding(
                    code="premium_assumption_missing",
                    severity="warning",
                    message="Option leg has no premium assumption.",
                    field=f"{field_prefix}.premium",
                )
            )
        if leg.strike <= Decimal("0"):
            findings.append(
                TradeIntentValidationFinding(
                    code="invalid_strike",
                    severity="blocker",
                    message="Option strike must be positive.",
                    field=f"{field_prefix}.strike",
                )
            )
        if today is not None and leg.expiration_date <= today:
            findings.append(
                TradeIntentValidationFinding(
                    code="expiration_not_future",
                    severity="blocker",
                    message="Option expiration must be in the future for review.",
                    field=f"{field_prefix}.expiration_date",
                )
            )
        if leg.requires_manual_review:
            findings.append(
                TradeIntentValidationFinding(
                    code="option_contract_manual_review_required",
                    severity="warning" if leg.support_status == "manual_review_required" else "blocker",
                    message="Option contract support status requires manual review.",
                    field=field_prefix,
                )
            )

    def _matches_single_leg(self, intent: OptionStrategyIntent, leg_action: str, option_type: str) -> bool:
        return len(intent.legs) == 1 and intent.legs[0].leg_action == leg_action and intent.legs[0].option_type == option_type

    def _strategy_shape_blocker(self, strategy_type: str) -> TradeIntentValidationFinding:
        return TradeIntentValidationFinding(
            code="strategy_shape_mismatch",
            severity="blocker",
            message=f"{strategy_type} requires the expected single option leg shape.",
            field="strategy_type",
        )


def _determine_highest_severity(findings: tuple[TradeIntentValidationFinding, ...]) -> ValidationSeverity | None:
    if not findings:
        return None
    severity_rank = {severity: index for index, severity in enumerate(VALIDATION_SEVERITIES)}
    return max((finding.severity for finding in findings), key=lambda severity: severity_rank[severity])
