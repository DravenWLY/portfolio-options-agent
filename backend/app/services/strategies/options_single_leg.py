"""Single-leg option strategy wrappers over the generic trade-review pipeline."""

from app.services.strategies.interfaces import BaseStrategyEvaluator
from app.services.trade_review.models import OptionStrategyIntent, TradeIntent


class LongCallReviewEvaluator(BaseStrategyEvaluator):
    strategy_name = "long_call_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        _require_option_strategy(intent, "long_call")


class LongPutReviewEvaluator(BaseStrategyEvaluator):
    strategy_name = "long_put_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        _require_option_strategy(intent, "long_put")


class CashSecuredPutEvaluator(BaseStrategyEvaluator):
    strategy_name = "cash_secured_put_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        _require_option_strategy(intent, "cash_secured_put")


class CoveredCallEvaluator(BaseStrategyEvaluator):
    strategy_name = "covered_call_review"

    def _validate_supported_intent(self, intent: TradeIntent) -> None:
        _require_option_strategy(intent, "covered_call")


def _require_option_strategy(intent: TradeIntent, strategy_type: str) -> None:
    if not isinstance(intent, OptionStrategyIntent) or intent.strategy_type != strategy_type:
        raise ValueError(f"expected {strategy_type} option strategy intent")
