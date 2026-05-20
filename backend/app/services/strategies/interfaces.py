"""Strategy evaluator interfaces for read-only trade review."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from app.services.trade_review.context import PortfolioReviewContext
from app.services.trade_review.models import TradeIntent
from app.services.trade_review.payoff import PayoffReview, PayoffScenarioEngine, PriceScenario
from app.services.trade_review.portfolio_impact import PortfolioImpact, PortfolioImpactEngine
from app.services.trade_review.report import TradeReviewReport, build_trade_review_report
from app.services.trade_review.risk import TradeReviewRiskEngine, TradeReviewRiskResult
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidationResult, TradeIntentValidator


@dataclass(frozen=True)
class StrategyReview:
    strategy_name: str
    intent: TradeIntent
    validation: TradeIntentValidationResult
    payoff: PayoffReview
    portfolio_impact: PortfolioImpact
    risk: TradeReviewRiskResult
    report: TradeReviewReport


class StrategyEvaluator(Protocol):
    strategy_name: str

    def evaluate(
        self,
        intent: TradeIntent,
        portfolio_context: PortfolioReviewContext,
        market_snapshot: TradeReviewMarketSnapshot,
        *,
        scenarios: tuple[PriceScenario, ...] | None = None,
        today: date | None = None,
        generated_at: datetime | None = None,
    ) -> StrategyReview:
        """Run the generic deterministic review pipeline for one intent."""


class BaseStrategyEvaluator:
    strategy_name = "generic_trade_review"

    def evaluate(
        self,
        intent: TradeIntent,
        portfolio_context: PortfolioReviewContext,
        market_snapshot: TradeReviewMarketSnapshot,
        *,
        scenarios: tuple[PriceScenario, ...] | None = None,
        today: date | None = None,
        generated_at: datetime | None = None,
    ) -> StrategyReview:
        self._validate_supported_intent(intent)
        validation = TradeIntentValidator().validate(intent, today=today)
        payoff = PayoffScenarioEngine().evaluate(intent, scenarios=scenarios)
        impact = PortfolioImpactEngine().calculate(
            intent=intent,
            portfolio_context=portfolio_context,
            market_snapshot=market_snapshot,
            payoff=payoff,
        )
        risk = TradeReviewRiskEngine().evaluate(
            validation=validation,
            portfolio_impact=impact,
            market_snapshot=market_snapshot,
        )
        report = build_trade_review_report(
            intent=intent,
            generated_at=generated_at or datetime.now(UTC),
            validation=validation,
            payoff=payoff,
            portfolio_impact=impact,
            risk=risk,
            market_snapshot=market_snapshot,
        )
        return StrategyReview(
            strategy_name=self.strategy_name,
            intent=intent,
            validation=validation,
            payoff=payoff,
            portfolio_impact=impact,
            risk=risk,
            report=report,
        )

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        raise NotImplementedError
