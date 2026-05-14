from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CashBalance(Base):
    __tablename__ = "cash_balances"
    __table_args__ = (
        Index("ix_cash_balances_account_id", "account_id"),
        Index("ix_cash_balances_account_id_as_of", "account_id", "as_of"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reserved_collateral_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    free_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    premium_income_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    dca_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
