from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OptionContract(Base):
    __tablename__ = "option_contracts"
    __table_args__ = (
        UniqueConstraint("occ_symbol", name="uq_option_contracts_occ_symbol"),
        Index(
            "ix_option_contracts_underlying_expiration",
            "underlying_symbol",
            "expiration_date",
        ),
        Index(
            "ix_option_contracts_lookup",
            "underlying_symbol",
            "expiration_date",
            "strike",
            "option_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    occ_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    underlying_symbol: Mapped[str] = mapped_column(String(24), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    strike: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)
    style: Mapped[str] = mapped_column(String(20), nullable=False, default="american", server_default="american")
    multiplier: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=100, server_default="100")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
