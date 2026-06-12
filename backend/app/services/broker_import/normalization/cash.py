from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.cash_balance import CashBalance
from app.services.broker_import import reconciliation
from app.services.broker_import.providers.models import ProviderBalanceSnapshot


def normalize_cash_balance(
    db: Session,
    account_id: UUID,
    balance: ProviderBalanceSnapshot,
    sync_run_id: UUID | None = None,
) -> CashBalance:
    ref = reconciliation.source_ref(balance.provider_account_id)
    free_cash = balance.available_cash if balance.available_cash is not None else balance.total_cash
    existing = reconciliation.find_cash_snapshot(db, account_id, balance.provider, ref, balance.sync_timestamp)

    if existing is None:
        existing = CashBalance(
            account_id=account_id,
            source=balance.provider,
            source_ref=ref,
            as_of=balance.sync_timestamp,
        )
        db.add(existing)

    existing.total_cash = balance.total_cash
    existing.available_cash = balance.available_cash
    existing.buying_power = balance.buying_power
    existing.currency = balance.currency.strip().upper()
    existing.sync_run_id = sync_run_id
    existing.reserved_collateral_cash = Decimal("0.00")
    existing.free_cash = free_cash
    existing.premium_income_cash = Decimal("0.00")
    existing.dca_cash = Decimal("0.00")
    existing.data_freshness_status = balance.data_freshness_status
    db.flush()
    return existing
