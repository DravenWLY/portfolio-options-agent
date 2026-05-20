from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.market_data.snapshots import MarketDataSnapshotReference
from app.services.trade_review.portfolio_impact import PortfolioImpact
from app.services.trade_review.risk import TradeReviewRiskEngine
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidationFinding, TradeIntentValidationResult


pytestmark = [pytest.mark.unit]


def _impact(*, projected_free_cash: Decimal | None = Decimal("100")) -> PortfolioImpact:
    return PortfolioImpact(
        intent_id="risk-1",
        cash_delta=Decimal("0"),
        premium_cash_delta=Decimal("0"),
        collateral_delta=Decimal("0"),
        projected_free_cash=projected_free_cash,
        assignment_share_delta=Decimal("0"),
        exercise_share_delta=Decimal("0"),
        concentration_symbol=None,
        concentration_value_delta=Decimal("0"),
        broker_freshness_status="fresh",
        market_freshness_status="fresh",
        market_manual_review_required=False,
        notes=(),
    )


def _validation(*findings: TradeIntentValidationFinding) -> TradeIntentValidationResult:
    return TradeIntentValidationResult(
        intent_id="risk-1",
        findings=findings,
        manual_review_required=bool(findings),
        blocked=any(finding.severity == "blocker" for finding in findings),
        highest_severity=None if not findings else "blocker",
        is_clean=not findings,
    )


def test_trade_review_risk_converts_validation_and_negative_cash_to_blockers() -> None:
    result = TradeReviewRiskEngine().evaluate(
        validation=_validation(
            TradeIntentValidationFinding(
                code="price_assumption_missing",
                severity="warning",
                message="No price assumption was supplied.",
                field="price_assumption",
            )
        ),
        portfolio_impact=_impact(projected_free_cash=Decimal("-1")),
        market_snapshot=TradeReviewMarketSnapshot(report_market_snapshot=None),
    )

    codes = {violation.code for violation in result.violations}
    assert "validation_price_assumption_missing" in codes
    assert "projected_free_cash_negative" in codes
    assert result.has_blocker is True


def test_trade_review_risk_treats_blocked_market_quote_as_blocker() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    snapshot = TradeReviewMarketSnapshot(
        report_market_snapshot=None,
        quote_references=(
            MarketDataSnapshotReference(
                snapshot_id="quote-1",
                kind="stock_quote",
                purpose="report_input_snapshot",
                provider="manual",
                stable_key="XYZ",
                captured_at=now,
                quote_time=now,
                freshness_scope="market_quote",
                data_mode="manual",
                freshness_status="stale",
                actionability_status="blocked_stale_quote",
            ),
        ),
    )

    result = TradeReviewRiskEngine().evaluate(
        validation=_validation(),
        portfolio_impact=_impact(),
        market_snapshot=snapshot,
    )

    assert result.highest_severity == "blocker"
    assert any(violation.code == "blocked_stale_quote" for violation in result.violations)


def test_trade_review_risk_treats_unknown_market_freshness_as_blocker() -> None:
    impact = _impact()
    impact = PortfolioImpact(
        intent_id=impact.intent_id,
        cash_delta=impact.cash_delta,
        premium_cash_delta=impact.premium_cash_delta,
        collateral_delta=impact.collateral_delta,
        projected_free_cash=impact.projected_free_cash,
        assignment_share_delta=impact.assignment_share_delta,
        exercise_share_delta=impact.exercise_share_delta,
        concentration_symbol=impact.concentration_symbol,
        concentration_value_delta=impact.concentration_value_delta,
        broker_freshness_status=impact.broker_freshness_status,
        market_freshness_status="unknown",
        market_manual_review_required=impact.market_manual_review_required,
        notes=impact.notes,
    )

    result = TradeReviewRiskEngine().evaluate(
        validation=_validation(),
        portfolio_impact=impact,
        market_snapshot=TradeReviewMarketSnapshot(report_market_snapshot=None),
    )

    assert result.highest_severity == "blocker"
    assert any(violation.code == "market_quote_unknown" for violation in result.violations)
