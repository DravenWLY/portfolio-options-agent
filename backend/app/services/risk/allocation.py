"""Deterministic allocation and concentration impact calculations."""

from dataclasses import dataclass
from decimal import Decimal


def _normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    return symbol


def _require_non_negative(value: Decimal, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True)
class AllocationPosition:
    symbol: str
    market_value: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        _require_non_negative(self.market_value, "market_value")


@dataclass(frozen=True)
class AllocationTarget:
    symbol: str
    target_weight: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        if self.target_weight < 0 or self.target_weight > 1:
            raise ValueError("target_weight must be between 0 and 1")


@dataclass(frozen=True)
class AllocationImpactItem:
    symbol: str
    market_value: Decimal
    actual_weight: Decimal
    target_weight: Decimal | None
    drift: Decimal | None
    absolute_drift: Decimal | None


@dataclass(frozen=True)
class AllocationImpact:
    total_value: Decimal
    largest_position_symbol: str | None
    # Weight denominator excludes cash unless cash is explicitly supplied as a
    # position. AssignmentProjection uses an account-total denominator that
    # includes projected cash.
    largest_position_weight: Decimal
    items: tuple[AllocationImpactItem, ...]


def calculate_allocation_impact(
    *,
    positions: tuple[AllocationPosition, ...],
    targets: tuple[AllocationTarget, ...] = (),
) -> AllocationImpact:
    """Calculate actual allocation, target drift, and concentration.

    Targets without a matching position are emitted as zero-value drift items so
    under-allocation is visible to downstream risk reports.
    """

    total_value = sum((position.market_value for position in positions), Decimal("0"))
    position_by_symbol = {position.symbol: position for position in positions}
    target_by_symbol = {target.symbol: target.target_weight for target in targets}
    symbols = tuple(sorted(set(position_by_symbol) | set(target_by_symbol)))
    if total_value == 0:
        items = tuple(
            AllocationImpactItem(
                symbol=symbol,
                market_value=(
                    position_by_symbol[symbol].market_value
                    if symbol in position_by_symbol
                    else Decimal("0")
                ),
                actual_weight=Decimal("0"),
                target_weight=target_by_symbol.get(symbol),
                drift=None if symbol not in target_by_symbol else -target_by_symbol[symbol],
                absolute_drift=None if symbol not in target_by_symbol else abs(target_by_symbol[symbol]),
            )
            for symbol in symbols
        )
        return AllocationImpact(
            total_value=Decimal("0"),
            largest_position_symbol=None,
            largest_position_weight=Decimal("0"),
            items=items,
        )

    items = []
    for symbol in symbols:
        position = position_by_symbol.get(symbol)
        market_value = position.market_value if position is not None else Decimal("0")
        actual_weight = market_value / total_value
        target_weight = target_by_symbol.get(symbol)
        drift = None if target_weight is None else actual_weight - target_weight
        items.append(
            AllocationImpactItem(
                symbol=symbol,
                market_value=market_value,
                actual_weight=actual_weight,
                target_weight=target_weight,
                drift=drift,
                absolute_drift=None if drift is None else abs(drift),
            )
        )
    largest = max(items, key=lambda item: item.actual_weight, default=None)
    return AllocationImpact(
        total_value=total_value,
        largest_position_symbol=largest.symbol if largest else None,
        largest_position_weight=largest.actual_weight if largest else Decimal("0"),
        items=tuple(items),
    )
