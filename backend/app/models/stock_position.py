from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StockPosition(Base):
    __tablename__ = "stock_positions"
    __table_args__ = (
        Index("ix_stock_positions_account_id", "account_id"),
        Index("ix_stock_positions_account_id_symbol", "account_id", "symbol"),
        Index("ix_stock_positions_account_id_as_of", "account_id", "as_of"),
        Index("ix_stock_positions_sync_run_id", "sync_run_id"),
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
    symbol: Mapped[str] = mapped_column(String(24), nullable=False)
    instrument_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False, default="stock", server_default="stock")
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    average_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    market_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    open_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual", server_default="manual")
    source_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_freshness_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    raw_provider_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tax_lots: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
