"""Strategy wrappers around the generic deterministic trade-review pipeline."""

from app.services.strategies.etf_review import ETFReviewEvaluator
from app.services.strategies.interfaces import StrategyEvaluator, StrategyReview
from app.services.strategies.options_single_leg import (
    CashSecuredPutEvaluator,
    CoveredCallEvaluator,
    LongCallReviewEvaluator,
    LongPutReviewEvaluator,
)
from app.services.strategies.stock_review import StockBuyReviewEvaluator, StockSellTrimReviewEvaluator

__all__ = [
    "CashSecuredPutEvaluator",
    "CoveredCallEvaluator",
    "ETFReviewEvaluator",
    "LongCallReviewEvaluator",
    "LongPutReviewEvaluator",
    "StockBuyReviewEvaluator",
    "StockSellTrimReviewEvaluator",
    "StrategyEvaluator",
    "StrategyReview",
]
