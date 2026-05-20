"""Portfolio impact calculations for deterministic trade review."""

from dataclasses import dataclass
from decimal import Decimal

from app.services.trade_review.context import PortfolioReviewContext
from app.services.trade_review.models import ETFTradeIntent, OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntent
from app.services.trade_review.payoff import PayoffReview
from app.services.trade_review.snapshots import TradeReviewMarketSnapshot


@dataclass(frozen=True)
class PortfolioImpact:
    intent_id: str
    cash_delta: Decimal
    premium_cash_delta: Decimal
    collateral_delta: Decimal
    projected_free_cash: Decimal | None
    assignment_share_delta: Decimal
    exercise_share_delta: Decimal
    concentration_symbol: str | None
    concentration_value_delta: Decimal
    broker_freshness_status: str
    market_freshness_status: str
    market_manual_review_required: bool
    notes: tuple[str, ...]


class PortfolioImpactEngine:
    """Estimate cash, collateral, assignment, and concentration deltas."""

    def calculate(
        self,
        *,
        intent: TradeIntent,
        portfolio_context: PortfolioReviewContext,
        market_snapshot: TradeReviewMarketSnapshot,
        payoff: PayoffReview,
    ) -> PortfolioImpact:
        if isinstance(intent, (StockTradeIntent, ETFTradeIntent)):
            return self._stock_or_etf_impact(intent, portfolio_context, market_snapshot)
        if isinstance(intent, OptionStrategyIntent):
            return self._option_impact(intent, portfolio_context, market_snapshot, payoff)
        raise ValueError("unsupported trade intent type")

    def _stock_or_etf_impact(
        self,
        intent: StockTradeIntent | ETFTradeIntent,
        portfolio_context: PortfolioReviewContext,
        market_snapshot: TradeReviewMarketSnapshot,
    ) -> PortfolioImpact:
        price = _require_price(intent.price_assumption, "price_assumption")
        gross = price * intent.quantity
        cash_delta = -gross if intent.action == "buy" else gross
        projected_free_cash = None if portfolio_context.cash is None else portfolio_context.cash.free_cash + cash_delta
        concentration_delta = gross if intent.action == "buy" else -gross
        return PortfolioImpact(
            intent_id=intent.intent_id,
            cash_delta=cash_delta,
            premium_cash_delta=Decimal("0"),
            collateral_delta=Decimal("0"),
            projected_free_cash=projected_free_cash,
            assignment_share_delta=Decimal("0"),
            exercise_share_delta=Decimal("0"),
            concentration_symbol=intent.symbol,
            concentration_value_delta=concentration_delta,
            broker_freshness_status=intent.data_freshness_snapshot.broker_portfolio_status,
            market_freshness_status=intent.data_freshness_snapshot.market_quote_status,
            market_manual_review_required=market_snapshot.manual_review_required,
            notes=("Stock/ETF impact uses the supplied price assumption and does not model taxes or commissions.",),
        )

    def _option_impact(
        self,
        intent: OptionStrategyIntent,
        portfolio_context: PortfolioReviewContext,
        market_snapshot: TradeReviewMarketSnapshot,
        payoff: PayoffReview,
    ) -> PortfolioImpact:
        premium_cash_delta = sum((_option_premium_cash_delta(leg) for leg in intent.legs), Decimal("0"))
        collateral_delta = sum((_option_collateral_delta(leg) for leg in intent.legs), Decimal("0"))
        assignment_share_delta = sum((_assignment_share_delta(leg) for leg in intent.legs), Decimal("0"))
        exercise_share_delta = sum((_exercise_share_delta(leg) for leg in intent.legs), Decimal("0"))
        projected_free_cash = (
            None
            if portfolio_context.cash is None
            else portfolio_context.cash.free_cash + premium_cash_delta - collateral_delta
        )
        return PortfolioImpact(
            intent_id=intent.intent_id,
            cash_delta=premium_cash_delta,
            premium_cash_delta=premium_cash_delta,
            collateral_delta=collateral_delta,
            projected_free_cash=projected_free_cash,
            assignment_share_delta=assignment_share_delta,
            exercise_share_delta=exercise_share_delta,
            concentration_symbol=intent.underlying_symbol,
            concentration_value_delta=_option_concentration_delta(intent, payoff),
            broker_freshness_status=intent.data_freshness_snapshot.broker_portfolio_status,
            market_freshness_status=intent.data_freshness_snapshot.market_quote_status,
            market_manual_review_required=market_snapshot.manual_review_required,
            notes=(
                "Option impact uses premium assumptions and generic collateral rules.",
                "Short put collateral is strike * multiplier * contracts; short call assignment exposure is share obligation, not margin.",
            ),
        )


def _require_price(value: Decimal | None, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required for portfolio impact")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _contract_size(leg: OptionLeg) -> Decimal:
    return leg.quantity * leg.multiplier


def _option_premium_cash_delta(leg: OptionLeg) -> Decimal:
    premium = _require_price(leg.premium, "premium")
    gross = premium * _contract_size(leg)
    return -gross if leg.leg_action.startswith("buy") else gross


def _option_collateral_delta(leg: OptionLeg) -> Decimal:
    if leg.leg_action == "sell_to_open" and leg.option_type == "put":
        return leg.strike * _contract_size(leg)
    return Decimal("0")


def _assignment_share_delta(leg: OptionLeg) -> Decimal:
    if leg.leg_action != "sell_to_open":
        return Decimal("0")
    shares = _contract_size(leg)
    return shares if leg.option_type == "put" else -shares


def _exercise_share_delta(leg: OptionLeg) -> Decimal:
    if leg.leg_action != "buy_to_open":
        return Decimal("0")
    shares = _contract_size(leg)
    return shares if leg.option_type == "call" else -shares


def _option_concentration_delta(intent: OptionStrategyIntent, payoff: PayoffReview) -> Decimal:
    if not payoff.points:
        return Decimal("0")
    unchanged = next((point for point in payoff.points if point.label == "unchanged"), payoff.points[0])
    return unchanged.scenario_pnl
