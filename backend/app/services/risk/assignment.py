"""Deterministic assignment and exercise scenario projections."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


ScenarioAction = Literal[
    "short_put_assignment",
    "short_call_assignment",
    "long_call_exercise",
    "long_put_exercise",
]

SCENARIO_ACTIONS: tuple[str, ...] = (
    "short_put_assignment",
    "short_call_assignment",
    "long_call_exercise",
    "long_put_exercise",
)


def _normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    return symbol


def _require_non_negative(value: Decimal, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_positive(value: Decimal, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


@dataclass(frozen=True)
class PositionHolding:
    symbol: str
    quantity: Decimal
    market_value: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        _require_non_negative(self.quantity, "quantity")
        _require_non_negative(self.market_value, "market_value")


@dataclass(frozen=True)
class AssignmentScenario:
    action: ScenarioAction
    underlying_symbol: str
    contracts: Decimal
    strike: Decimal
    multiplier: Decimal = Decimal("100")
    projected_underlying_price: Decimal | None = None

    def __post_init__(self) -> None:
        if self.action not in SCENARIO_ACTIONS:
            raise ValueError("action must be a supported assignment/exercise action")
        object.__setattr__(self, "underlying_symbol", _normalize_symbol(self.underlying_symbol))
        _require_positive(self.contracts, "contracts")
        _require_positive(self.strike, "strike")
        _require_positive(self.multiplier, "multiplier")
        if self.projected_underlying_price is not None:
            _require_positive(self.projected_underlying_price, "projected_underlying_price")

    @property
    def share_delta(self) -> Decimal:
        shares = self.contracts * self.multiplier
        if self.action in ("short_put_assignment", "long_call_exercise"):
            return shares
        return -shares

    @property
    def cash_delta(self) -> Decimal:
        shares = self.contracts * self.multiplier
        notional = self.strike * shares
        if self.action in ("short_put_assignment", "long_call_exercise"):
            return -notional
        return notional


@dataclass(frozen=True)
class ProjectedHolding:
    symbol: str
    quantity: Decimal
    market_value: Decimal
    allocation_weight: Decimal


@dataclass(frozen=True)
class AssignmentProjection:
    action: ScenarioAction
    underlying_symbol: str
    share_delta: Decimal
    cash_delta: Decimal
    projected_cash: Decimal
    projected_total_value: Decimal
    largest_position_symbol: str | None
    # Weight denominator includes projected cash. AllocationImpact uses a
    # position-only denominator, so reports should label these separately.
    largest_position_weight: Decimal
    holdings: tuple[ProjectedHolding, ...]


def project_assignment_scenario(
    *,
    cash: Decimal,
    holdings: tuple[PositionHolding, ...],
    scenario: AssignmentScenario,
) -> AssignmentProjection:
    """Project cash, long holdings, and concentration after assignment/exercise.

    Valuation rule: only the scenario underlying is repriced with
    ``projected_underlying_price`` (or strike when omitted). Other holdings keep
    their supplied market values because this service does not model a full
    correlated market shock.

    Scope boundary: this MVP models long-share holdings only. A short call
    assignment that would create a short stock position raises instead of
    projecting margin/short-stock behavior.
    """

    _require_non_negative(cash, "cash")
    projected_cash = cash + scenario.cash_delta
    price = scenario.projected_underlying_price or scenario.strike
    current_by_symbol = {holding.symbol: holding for holding in holdings}
    current = current_by_symbol.get(
        scenario.underlying_symbol,
        PositionHolding(scenario.underlying_symbol, Decimal("0"), Decimal("0")),
    )
    projected_quantity = current.quantity + scenario.share_delta
    if projected_quantity < 0:
        raise ValueError("scenario would create a negative projected holding quantity")

    projected_values: dict[str, tuple[Decimal, Decimal]] = {}
    for holding in holdings:
        projected_values[holding.symbol] = (holding.quantity, holding.market_value)
    projected_values[scenario.underlying_symbol] = (
        projected_quantity,
        projected_quantity * price,
    )

    total_holdings_value = sum((value for _, value in projected_values.values()), Decimal("0"))
    projected_total_value = projected_cash + total_holdings_value
    if projected_total_value <= 0:
        raise ValueError("projected_total_value must be positive")

    projected_holdings = tuple(
        ProjectedHolding(
            symbol=symbol,
            quantity=quantity,
            market_value=value,
            allocation_weight=value / projected_total_value,
        )
        for symbol, (quantity, value) in sorted(projected_values.items())
        if quantity > 0 or value > 0
    )
    largest = max(projected_holdings, key=lambda item: item.allocation_weight, default=None)
    return AssignmentProjection(
        action=scenario.action,
        underlying_symbol=scenario.underlying_symbol,
        share_delta=scenario.share_delta,
        cash_delta=scenario.cash_delta,
        projected_cash=projected_cash,
        projected_total_value=projected_total_value,
        largest_position_symbol=largest.symbol if largest else None,
        largest_position_weight=largest.allocation_weight if largest else Decimal("0"),
        holdings=projected_holdings,
    )
