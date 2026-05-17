from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.option_position import OptionPosition
from app.schemas.option_position import OptionPositionCreate
from app.services.portfolio.option_contracts import get_or_create_option_contract


def account_exists(db: Session, account_id: UUID) -> bool:
    return db.scalar(select(Account.id).where(Account.id == account_id, Account.deleted_at.is_(None))) is not None


def create_option_position(db: Session, account_id: UUID, payload: OptionPositionCreate) -> OptionPosition | None:
    if not account_exists(db, account_id):
        return None

    option_contract = get_or_create_option_contract(db, payload.contract)
    option_position = OptionPosition(
        account_id=account_id,
        option_contract_id=option_contract.id,
        position_side=payload.position_side,
        quantity=payload.quantity,
        average_price=payload.average_price,
        market_price=payload.market_price,
        market_value=payload.market_value,
        status=payload.status,
        source=payload.source,
        source_ref=payload.source_ref,
        data_freshness_status=payload.data_freshness_status,
        raw_provider_payload=payload.raw_provider_payload,
        as_of=payload.as_of,
        opened_at=payload.opened_at,
        closed_at=payload.closed_at,
    )
    db.add(option_position)
    db.commit()
    db.refresh(option_position)
    return option_position


def list_option_positions(db: Session, account_id: UUID) -> list[OptionPosition] | None:
    if not account_exists(db, account_id):
        return None

    rows = db.scalars(
        select(OptionPosition)
        .where(OptionPosition.account_id == account_id, OptionPosition.status == "open")
        .order_by(
            OptionPosition.option_contract_id.asc(),
            OptionPosition.as_of.desc(),
            OptionPosition.created_at.desc(),
            OptionPosition.id.desc(),
        )
    )
    latest_by_contract: dict[UUID, OptionPosition] = {}
    for position in rows:
        latest_by_contract.setdefault(position.option_contract_id, position)
    return list(latest_by_contract.values())
