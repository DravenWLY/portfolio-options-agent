"""Trade intent review contracts for read-only portfolio-aware analysis."""

from app.services.trade_review.actionability import POLICY_VERSION, evaluate_portfolio_snapshot_actionability
from app.services.trade_review.context import (
    CashContext,
    OptionPositionContext,
    PortfolioContextBuilder,
    PortfolioReviewContext,
    StockPositionContext,
)
from app.services.trade_review.journal import (
    JournalServiceBoundary,
    TradeReviewReportLink,
    link_trade_review_to_report,
)
from app.services.trade_review.models import (
    AssetClass,
    ETFTradeIntent,
    OptionLeg,
    OptionStrategyIntent,
    StockTradeIntent,
    TradeIntent,
    TradeIntentFreshnessSnapshot,
)
from app.services.trade_review.payoff import PayoffReview, PayoffScenarioEngine, PayoffScenarioPoint, PriceScenario
from app.services.trade_review.portfolio_impact import PortfolioImpact, PortfolioImpactEngine
from app.services.trade_review.report import (
    AgentSafePortfolioImpact,
    TradeReviewAgentProjection,
    TradeReviewReport,
    build_trade_review_report,
    to_agent_safe_projection,
)
from app.services.trade_review.risk import TradeReviewRiskEngine, TradeReviewRiskResult
from app.services.trade_review.snapshots import MarketSnapshotResolver, TradeReviewMarketSnapshot
from app.services.trade_review.validation import TradeIntentValidator, TradeIntentValidationResult

__all__ = [
    "AssetClass",
    "AgentSafePortfolioImpact",
    "CashContext",
    "ETFTradeIntent",
    "JournalServiceBoundary",
    "MarketSnapshotResolver",
    "OptionLeg",
    "OptionPositionContext",
    "OptionStrategyIntent",
    "POLICY_VERSION",
    "PayoffReview",
    "PayoffScenarioEngine",
    "PayoffScenarioPoint",
    "PortfolioImpact",
    "PortfolioImpactEngine",
    "PortfolioContextBuilder",
    "PortfolioReviewContext",
    "PriceScenario",
    "StockPositionContext",
    "StockTradeIntent",
    "TradeIntent",
    "TradeIntentFreshnessSnapshot",
    "TradeIntentValidationResult",
    "TradeIntentValidator",
    "TradeReviewAgentProjection",
    "TradeReviewReport",
    "TradeReviewRiskEngine",
    "TradeReviewRiskResult",
    "TradeReviewMarketSnapshot",
    "TradeReviewReportLink",
    "build_trade_review_report",
    "evaluate_portfolio_snapshot_actionability",
    "link_trade_review_to_report",
    "to_agent_safe_projection",
]
