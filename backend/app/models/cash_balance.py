from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CashBalance(Base):
    __tablename__ = "cash_balances"
    __table_args__ = (
        Index("ix_cash_balances_account_id", "account_id"),
        Index("ix_cash_balances_account_id_as_of", "account_id", "as_of"),
        Index("ix_cash_balances_sync_run_id", "sync_run_id"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    sync_run_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("broker_sync_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    available_cash: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    buying_power: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    reserved_collateral_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    free_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    premium_income_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    dca_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual", server_default="manual")
    source_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_freshness_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
