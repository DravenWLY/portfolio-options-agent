from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review.journal import link_trade_review_to_report
from app.services.trade_review.models import StockTradeIntent, TradeIntentFreshnessSnapshot
from app.services.trade_review.payoff import PayoffScenarioEngine
from app.services.trade_review.portfolio_impact import PortfolioImpact
from app.services.trade_review.report import build_trade_review_report, to_agent_safe_projection
from app.services.trade_review.risk import TradeReviewRiskResult
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidator


pytestmark = [pytest.mark.unit]


def test_trade_review_report_renders_review_language_without_execution_or_advice() -> None:
    intent = StockTradeIntent(
        intent_id="report-1",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="stock",
        intent_type="stock_buy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=TradeIntentFreshnessSnapshot(
            broker_portfolio_status="fresh",
            market_quote_status="fresh",
        ),
        symbol="XYZ",
        action="buy",
        quantity=Decimal("1"),
        price_assumption=Decimal("20"),
    )
    payoff = PayoffScenarioEngine().evaluate(intent)
    impact = PortfolioImpact(
        intent_id=intent.intent_id,
        cash_delta=Decimal("-20"),
        premium_cash_delta=Decimal("0"),
        collateral_delta=Decimal("0"),
        projected_free_cash=Decimal("980"),
        assignment_share_delta=Decimal("0"),
        exercise_share_delta=Decimal("0"),
        concentration_symbol="XYZ",
        concentration_value_delta=Decimal("20"),
        broker_freshness_status="fresh",
        market_freshness_status="fresh",
        market_manual_review_required=False,
        notes=(),
    )
    risk = TradeReviewRiskResult(violations=(), highest_severity=None, has_blocker=False)

    report = build_trade_review_report(
        intent=intent,
        generated_at=datetime(2026, 5, 18, 15, 5, tzinfo=UTC),
        validation=TradeIntentValidator().validate(intent),
        payoff=payoff,
        portfolio_impact=impact,
        risk=risk,
        market_snapshot=TradeReviewMarketSnapshot(report_market_snapshot=None),
    )

    assert report.intent_snapshot["symbol"] == "XYZ"
    assert report.data_freshness_snapshot["broker_freshness_scope"] == "broker_portfolio"
    assert "deterministic Python services only" in report.markdown
    assert "does not recommend, place, route, or manage trades" in report.markdown
    assert "you should" not in report.markdown.lower()


def test_trade_review_report_can_carry_report_history_link() -> None:
    intent = StockTradeIntent(
        intent_id="report-link-1",
        user_id=uuid4(),
        account_id=uuid4(),
        asset_class="stock",
        intent_type="stock_buy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=TradeIntentFreshnessSnapshot(
            broker_portfolio_status="fresh",
            market_quote_status="fresh",
        ),
        symbol="XYZ",
        action="buy",
        quantity=Decimal("1"),
        price_assumption=Decimal("20"),
    )
    link = link_trade_review_to_report(
        trade_intent_id=intent.intent_id,
        report_thread_id="thread-1",
        report_message_id="message-1",
        created_at=datetime(2026, 5, 18, 15, 5, tzinfo=UTC),
    )

    report = build_trade_review_report(
        intent=intent,
        generated_at=datetime(2026, 5, 18, 15, 5, tzinfo=UTC),
        validation=TradeIntentValidator().validate(intent),
        payoff=PayoffScenarioEngine().evaluate(intent),
        portfolio_impact=PortfolioImpact(
            intent_id=intent.intent_id,
            cash_delta=Decimal("-20"),
            premium_cash_delta=Decimal("0"),
            collateral_delta=Decimal("0"),
            projected_free_cash=Decimal("980"),
            assignment_share_delta=Decimal("0"),
            exercise_share_delta=Decimal("0"),
            concentration_symbol="XYZ",
            concentration_value_delta=Decimal("20"),
            broker_freshness_status="fresh",
            market_freshness_status="fresh",
            market_manual_review_required=False,
            notes=(),
        ),
        risk=TradeReviewRiskResult(violations=(), highest_severity=None, has_blocker=False),
        market_snapshot=TradeReviewMarketSnapshot(report_market_snapshot=None),
        report_link=link,
    )

    assert report.report_link == link
    assert report.report_link.report_thread_id == "thread-1"


def test_agent_safe_projection_redacts_account_ids_and_absolute_cash_values() -> None:
    user_id = uuid4()
    account_id = uuid4()
    intent = StockTradeIntent(
        intent_id="agent-safe-1",
        user_id=user_id,
        account_id=account_id,
        asset_class="stock",
        intent_type="stock_buy",
        created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        calculation_version="trade-review-v1",
        data_freshness_snapshot=TradeIntentFreshnessSnapshot(
            broker_portfolio_status="fresh",
            market_quote_status="fresh",
        ),
        symbol="XYZ",
        action="buy",
        quantity=Decimal("1"),
        price_assumption=Decimal("20"),
    )
    report = build_trade_review_report(
        intent=intent,
        generated_at=datetime(2026, 5, 18, 15, 5, tzinfo=UTC),
        validation=TradeIntentValidator().validate(intent),
        payoff=PayoffScenarioEngine().evaluate(intent),
        portfolio_impact=PortfolioImpact(
            intent_id=intent.intent_id,
            cash_delta=Decimal("-20"),
            premium_cash_delta=Decimal("0"),
            collateral_delta=Decimal("0"),
            projected_free_cash=Decimal("980"),
            assignment_share_delta=Decimal("0"),
            exercise_share_delta=Decimal("0"),
            concentration_symbol="XYZ",
            concentration_value_delta=Decimal("20"),
            broker_freshness_status="fresh",
            market_freshness_status="fresh",
            market_manual_review_required=False,
            notes=(),
        ),
        risk=TradeReviewRiskResult(violations=(), highest_severity=None, has_blocker=False),
        market_snapshot=TradeReviewMarketSnapshot(report_market_snapshot=None),
    )

    projection = to_agent_safe_projection(report)
    payload = asdict(projection)
    keys = _collect_keys(payload)
    serialized = repr(payload)

    assert "user_id" not in keys
    assert "account_id" not in keys
    assert not (keys & FORBIDDEN_REPORT_FACT_KEYS)
    assert str(user_id) not in serialized
    assert str(account_id) not in serialized
    assert not hasattr(projection.portfolio_impact, "cash_delta")
    assert not hasattr(projection.portfolio_impact, "projected_free_cash")
    assert "980" not in serialized


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {str(key) for key in value}
        for item in value.values():
            found.update(_collect_keys(item))
        return found
    if isinstance(value, (list, tuple)):
        found: set[str] = set()
        for item in value:
            found.update(_collect_keys(item))
        return found
    return set()
