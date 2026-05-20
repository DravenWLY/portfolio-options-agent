"""ETF strategy wrappers for deterministic trade review."""

from app.services.strategies.interfaces import BaseStrategyEvaluator
from app.services.trade_review.models import ETFTradeIntent, TradeIntent


class ETFReviewEvaluator(BaseStrategyEvaluator):
    strategy_name = "etf_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        if not isinstance(intent, ETFTradeIntent):
            raise ValueError("ETFReviewEvaluator requires an ETF intent")
