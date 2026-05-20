"""Strategy-neutral payoff and scenario calculations for trade review."""

from dataclasses import dataclass
from decimal import Decimal

from app.services.trade_review.models import ETFTradeIntent, OptionLeg, OptionStrategyIntent, StockTradeIntent, TradeIntent


@dataclass(frozen=True)
class PriceScenario:
    label: str
    underlying_price: Decimal

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("label must not be empty")
        if self.underlying_price < 0:
            raise ValueError("underlying_price must be non-negative")


@dataclass(frozen=True)
class PayoffScenarioPoint:
    label: str
    underlying_price: Decimal
    net_cash_flow: Decimal
    scenario_value: Decimal
    scenario_pnl: Decimal
    description: str


@dataclass(frozen=True)
class PayoffReview:
    intent_id: str
    asset_class: str
    points: tuple[PayoffScenarioPoint, ...]
    max_loss: Decimal | None
    max_gain: Decimal | None
    calculation_notes: tuple[str, ...]


class PayoffScenarioEngine:
    """Compute deterministic scenario outcomes without recommendations."""

    def evaluate(
        self,
        intent: TradeIntent,
        *,
        scenarios: tuple[PriceScenario, ...] | None = None,
    ) -> PayoffReview:
        if isinstance(intent, (StockTradeIntent, ETFTradeIntent)):
            return self._evaluate_stock_or_etf(intent, scenarios=scenarios)
        if isinstance(intent, OptionStrategyIntent):
            return self._evaluate_option_strategy(intent, scenarios=scenarios)
        raise ValueError("unsupported trade intent type")

    def _evaluate_stock_or_etf(
        self,
        intent: StockTradeIntent | ETFTradeIntent,
        *,
        scenarios: tuple[PriceScenario, ...] | None,
    ) -> PayoffReview:
        reference_price = _require_price(intent.price_assumption, "price_assumption")
        scenario_points = scenarios or _default_scenarios(reference_price)
        direction = Decimal("1") if intent.action == "buy" else Decimal("-1")
        net_cash_flow = -reference_price * intent.quantity if intent.action == "buy" else reference_price * intent.quantity
        points = tuple(
            PayoffScenarioPoint(
                label=scenario.label,
                underlying_price=scenario.underlying_price,
                net_cash_flow=net_cash_flow,
                scenario_value=scenario.underlying_price * intent.quantity,
                scenario_pnl=(scenario.underlying_price - reference_price) * intent.quantity * direction,
                description=f"{intent.asset_class} {intent.action} scenario versus price assumption",
            )
            for scenario in scenario_points
        )
        return PayoffReview(
            intent_id=intent.intent_id,
            asset_class=intent.asset_class,
            points=points,
            max_loss=None,
            max_gain=None,
            calculation_notes=(
                "Stock and ETF scenarios compare future price points against the supplied price assumption.",
                "Sell/trim scenarios show avoided downside as positive scenario P/L when prices fall after sale.",
            ),
        )

    def _evaluate_option_strategy(
        self,
        intent: OptionStrategyIntent,
        *,
        scenarios: tuple[PriceScenario, ...] | None,
    ) -> PayoffReview:
        reference_price = intent.legs[0].strike
        scenario_points = scenarios or _default_scenarios(reference_price)
        points = []
        for scenario in scenario_points:
            net_cash_flow = sum((_leg_initial_cash_flow(leg) for leg in intent.legs), Decimal("0"))
            scenario_value = sum((_leg_intrinsic_value(leg, scenario.underlying_price) for leg in intent.legs), Decimal("0"))
            scenario_pnl = sum((_leg_scenario_pnl(leg, scenario.underlying_price) for leg in intent.legs), Decimal("0"))
            points.append(
                PayoffScenarioPoint(
                    label=scenario.label,
                    underlying_price=scenario.underlying_price,
                    net_cash_flow=net_cash_flow,
                    scenario_value=scenario_value,
                    scenario_pnl=scenario_pnl,
                    description=f"{intent.strategy_type} scenario from option intrinsic value and premium assumptions",
                )
            )
        return PayoffReview(
            intent_id=intent.intent_id,
            asset_class=intent.asset_class,
            points=tuple(points),
            max_loss=_estimate_option_max_loss(intent),
            max_gain=_estimate_option_max_gain(intent),
            calculation_notes=(
                "Option payoff uses intrinsic value at scenario price minus debit or plus credit from premium assumptions.",
                "Multi-leg scenarios are summed leg-by-leg; this is not an optimizer.",
            ),
        )


def _require_price(value: Decimal | None, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required for payoff scenarios")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _default_scenarios(reference_price: Decimal) -> tuple[PriceScenario, ...]:
    return (
        PriceScenario("down_10pct", reference_price * Decimal("0.90")),
        PriceScenario("unchanged", reference_price),
        PriceScenario("up_10pct", reference_price * Decimal("1.10")),
    )


def _contract_size(leg: OptionLeg) -> Decimal:
    return leg.quantity * leg.multiplier


def _leg_intrinsic_value(leg: OptionLeg, underlying_price: Decimal) -> Decimal:
    if leg.option_type == "call":
        intrinsic = max(underlying_price - leg.strike, Decimal("0"))
    else:
        intrinsic = max(leg.strike - underlying_price, Decimal("0"))
    return intrinsic * _contract_size(leg)


def _leg_initial_cash_flow(leg: OptionLeg) -> Decimal:
    premium = _require_price(leg.premium, "premium")
    gross = premium * _contract_size(leg)
    return -gross if leg.leg_action.startswith("buy") else gross


def _leg_scenario_pnl(leg: OptionLeg, underlying_price: Decimal) -> Decimal:
    intrinsic_value = _leg_intrinsic_value(leg, underlying_price)
    initial_cash_flow = _leg_initial_cash_flow(leg)
    if leg.leg_action.startswith("buy"):
        return intrinsic_value + initial_cash_flow
    return initial_cash_flow - intrinsic_value


def _estimate_option_max_loss(intent: OptionStrategyIntent) -> Decimal | None:
    if len(intent.legs) != 1:
        return None
    leg = intent.legs[0]
    premium = _require_price(leg.premium, "premium")
    if leg.leg_action.startswith("buy"):
        return premium * _contract_size(leg)
    if leg.option_type == "put":
        return (leg.strike - premium) * _contract_size(leg)
    return None


def _estimate_option_max_gain(intent: OptionStrategyIntent) -> Decimal | None:
    if len(intent.legs) != 1:
        return None
    leg = intent.legs[0]
    premium = _require_price(leg.premium, "premium")
    if leg.leg_action.startswith("sell"):
        return premium * _contract_size(leg)
    if leg.option_type == "put":
        return (leg.strike - premium) * _contract_size(leg)
    return None
