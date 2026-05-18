"""Strategy-neutral cash collateral calculations."""

from dataclasses import dataclass
from decimal import Decimal


def _require_non_negative(value: Decimal, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True)
class CollateralRequirement:
    """A deterministic cash reserve requirement from any risk source."""

    source_id: str
    source_type: str
    required_cash: Decimal
    description: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_type.strip():
            raise ValueError("source_type must not be empty")
        _require_non_negative(self.required_cash, "required_cash")


@dataclass(frozen=True)
class CollateralSummary:
    account_id: str
    total_cash: Decimal
    existing_reserved_cash: Decimal
    option_collateral_required: Decimal
    total_reserved_cash: Decimal
    free_cash: Decimal
    collateral_utilization: Decimal
    requirements: tuple[CollateralRequirement, ...]


def calculate_collateral_summary(
    *,
    account_id: str,
    total_cash: Decimal,
    requirements: tuple[CollateralRequirement, ...] = (),
    existing_reserved_cash: Decimal = Decimal("0"),
) -> CollateralSummary:
    """Calculate account-scoped reserved collateral and free cash.

    Inputs are already-normalized cash amounts. This function does not know
    about a specific option strategy; callers pass structured reserve
    requirements from short options, pending scenarios, or future strategy
    evaluators.

    If ``total_cash`` is zero, ``collateral_utilization`` is reported as zero
    because the percentage denominator is undefined. In that case,
    ``free_cash < 0`` plus ``total_reserved_cash`` are the authoritative
    over-commitment signals.
    """

    if not account_id.strip():
        raise ValueError("account_id must not be empty")
    _require_non_negative(total_cash, "total_cash")
    _require_non_negative(existing_reserved_cash, "existing_reserved_cash")
    option_collateral_required = sum(
        (requirement.required_cash for requirement in requirements),
        Decimal("0"),
    )
    total_reserved_cash = existing_reserved_cash + option_collateral_required
    free_cash = total_cash - total_reserved_cash
    collateral_utilization = (
        total_reserved_cash / total_cash
        if total_cash > 0
        else Decimal("0")
    )
    return CollateralSummary(
        account_id=account_id,
        total_cash=total_cash,
        existing_reserved_cash=existing_reserved_cash,
        option_collateral_required=option_collateral_required,
        total_reserved_cash=total_reserved_cash,
        free_cash=free_cash,
        collateral_utilization=collateral_utilization,
        requirements=requirements,
    )
