import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.option_position import OptionPosition
from app.schemas.option_contract import OptionContractCreate
from app.services.broker_import import reconciliation
from app.services.broker_import.normalization.sanitization import sanitize_provider_payload
from app.services.broker_import.providers.models import ProviderOptionPositionSnapshot
from app.services.portfolio.option_contracts import get_or_create_option_contract

OCC_SYMBOL_PATTERN = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")


@dataclass(frozen=True)
class ParsedOccSymbol:
    occ_symbol: str
    underlying_symbol: str
    expiration_date: date
    option_type: str
    strike: Decimal


@dataclass(frozen=True)
class OptionNormalizationResult:
    positions: list[OptionPosition]
    partial_failures: list[dict[str, str]]


def parse_occ_symbol(occ_symbol: str) -> ParsedOccSymbol:
    normalized = occ_symbol.strip().upper().replace(" ", "")
    match = OCC_SYMBOL_PATTERN.match(normalized)
    if match is None:
        raise ValueError("Unsupported OCC option symbol format")

    underlying, expiration, option_type_code, strike_digits = match.groups()
    expiration_date = date(
        year=2000 + int(expiration[0:2]),
        month=int(expiration[2:4]),
        day=int(expiration[4:6]),
    )
    option_type = "call" if option_type_code == "C" else "put"
    strike = Decimal(str(int(strike_digits))) / Decimal("1000")
    return ParsedOccSymbol(
        occ_symbol=normalized,
        underlying_symbol=underlying,
        expiration_date=expiration_date,
        option_type=option_type,
        strike=strike,
    )


def normalize_option_position(
    db: Session,
    account_id: UUID,
    position: ProviderOptionPositionSnapshot,
    sync_run_id: UUID | None = None,
) -> OptionPosition:
    parsed = parse_occ_symbol(position.occ_symbol)
    contract = get_or_create_option_contract(
        db,
        OptionContractCreate(
            occ_symbol=parsed.occ_symbol,
            underlying_symbol=position.underlying_symbol or parsed.underlying_symbol,
            expiration_date=parsed.expiration_date,
            strike=parsed.strike,
            option_type=parsed.option_type,
            multiplier=position.multiplier,
        ),
    )
    ref = reconciliation.source_ref(position.provider_account_id, parsed.occ_symbol)
    existing = reconciliation.find_option_snapshot(
        db,
        account_id,
        contract.id,
        position.provider,
        ref,
        position.sync_timestamp,
    )

    if existing is None:
        existing = OptionPosition(
            account_id=account_id,
            option_contract_id=contract.id,
            source=position.provider,
            source_ref=ref,
            as_of=position.sync_timestamp,
        )
        db.add(existing)

    existing.position_side = position.position_side
    existing.sync_run_id = sync_run_id
    existing.quantity = position.quantity
    existing.average_price = position.average_purchase_price
    existing.market_price = position.market_price
    existing.market_value = position.market_value
    existing.open_pnl = position.open_pnl
    existing.currency = position.currency.strip().upper()
    existing.status = option_position_status(parsed, position)
    existing.tax_lots = _serialized_option_tax_lots(position.tax_lots)
    existing.data_freshness_status = position.data_freshness_status
    existing.raw_provider_payload = sanitize_provider_payload(position.raw_payload)
    db.flush()
    return existing


def normalize_option_positions(
    db: Session,
    account_id: UUID,
    positions: list[ProviderOptionPositionSnapshot],
    sync_run_id: UUID | None = None,
) -> list[OptionPosition]:
    return [normalize_option_position(db, account_id, position, sync_run_id=sync_run_id) for position in positions]


def normalize_option_positions_safely(
    db: Session,
    account_id: UUID,
    positions: list[ProviderOptionPositionSnapshot],
    sync_run_id: UUID | None = None,
) -> OptionNormalizationResult:
    normalized: list[OptionPosition] = []
    failures: list[dict[str, str]] = []
    for position in positions:
        try:
            parsed = parse_occ_symbol(position.occ_symbol)
            if position.underlying_symbol and position.underlying_symbol.strip().upper() != parsed.underlying_symbol:
                failures.append(
                    {
                        "occ_symbol": position.occ_symbol,
                        "reason": "underlying_mismatch",
                    }
                )
            normalized.append(normalize_option_position(db, account_id, position, sync_run_id=sync_run_id))
        except ValueError:
            failures.append(
                {
                    "occ_symbol": position.occ_symbol,
                    "reason": "unsupported_occ_symbol",
                }
            )
    return OptionNormalizationResult(positions=normalized, partial_failures=failures)


def option_position_status(
    parsed: ParsedOccSymbol,
    position: ProviderOptionPositionSnapshot,
    *,
    current_date: date | None = None,
) -> str:
    today = current_date or date.today()
    if parsed.expiration_date < today:
        return "expired"
    if position.quantity <= 0:
        return "closed"
    return "open"


def _serialized_option_tax_lots(tax_lots) -> list[dict] | None:
    serialized = []
    for lot in tax_lots:
        serialized.append(
            {
                "acquired_date": lot.acquired_date.isoformat() if lot.acquired_date else None,
                "quantity": str(lot.quantity) if lot.quantity is not None else None,
                "purchase_price": str(lot.purchase_price) if lot.purchase_price is not None else None,
                "cost_basis": str(lot.cost_basis) if lot.cost_basis is not None else None,
                "current_value": str(lot.current_value) if lot.current_value is not None else None,
                "position_type": lot.position_type,
            }
        )
    return serialized or None
