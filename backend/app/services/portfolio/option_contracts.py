from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.option_contract import OptionContract
from app.schemas.option_contract import OptionContractCreate


def get_or_create_option_contract(db: Session, payload: OptionContractCreate) -> OptionContract:
    existing = db.scalar(select(OptionContract).where(OptionContract.occ_symbol == payload.occ_symbol))
    if existing is not None:
        return existing

    option_contract = OptionContract(
        occ_symbol=payload.occ_symbol,
        underlying_symbol=payload.underlying_symbol,
        expiration_date=payload.expiration_date,
        strike=payload.strike,
        option_type=payload.option_type,
        style=payload.style,
        multiplier=payload.multiplier,
    )
    db.add(option_contract)
    db.flush()
    return option_contract
