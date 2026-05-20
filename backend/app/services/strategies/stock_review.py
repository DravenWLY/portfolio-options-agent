"""Stock strategy wrappers for deterministic trade review."""

from app.services.strategies.interfaces import BaseStrategyEvaluator
from app.services.trade_review.models import StockTradeIntent, TradeIntent


class StockBuyReviewEvaluator(BaseStrategyEvaluator):
    strategy_name = "stock_buy_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        if not isinstance(intent, StockTradeIntent) or intent.action != "buy":
            raise ValueError("StockBuyReviewEvaluator requires a stock buy intent")


class StockSellTrimReviewEvaluator(BaseStrategyEvaluator):
    strategy_name = "stock_sell_trim_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        if not isinstance(intent, StockTradeIntent) or intent.action not in {"sell", "trim"}:
            raise ValueError("StockSellTrimReviewEvaluator requires a stock sell or trim intent")
