from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_sync_run import BrokerSyncRun
from app.services.broker_import.accounts import get_broker_account
from app.services.broker_import.providers.exceptions import BrokerProviderError
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter


class BrokerSyncAccountNotFoundError(RuntimeError):
    """Raised when a broker account cannot be synced because it is missing."""


def sync_broker_account(
    db: Session,
    broker_account_id: UUID,
    adapter: SnapTradeAdapter,
    trigger: str = "manual",
) -> BrokerSyncRun:
    broker_account = get_broker_account(db, broker_account_id)
    if broker_account is None:
        raise BrokerSyncAccountNotFoundError("Broker account not found")

    started_at = datetime.now(UTC)
    sync_run = BrokerSyncRun(
        broker_connection_id=broker_account.broker_connection_id,
        broker_account_id=broker_account.id,
        trigger=trigger,
        status="running",
        started_at=started_at,
    )
    db.add(sync_run)
    db.flush()

    try:
        refresh = adapter.refresh_account(broker_account.provider_account_id)
        balance = adapter.get_balances(broker_account.provider_account_id)
        positions = adapter.get_positions(broker_account.provider_account_id)
        option_positions = adapter.get_option_positions(broker_account.provider_account_id)
    except BrokerProviderError as exc:
        completed_at = datetime.now(UTC)
        sync_run.status = "failed"
        sync_run.completed_at = completed_at
        sync_run.error = {"type": exc.__class__.__name__, "message": str(exc)}
        broker_account.sync_status = "failed"
        db.commit()
        db.refresh(sync_run)
        return sync_run

    completed_at = refresh.completed_at or datetime.now(UTC)
    sync_run.status = refresh.status
    sync_run.completed_at = completed_at
    sync_run.provider_request_id = refresh.provider_request_id
    sync_run.accounts_count = refresh.accounts_count
    sync_run.positions_count = len(positions) + len(option_positions)
    sync_run.transactions_count = refresh.transactions_count
    sync_run.summary = {
        "balance_currency": balance.currency,
        "stock_positions_count": len(positions),
        "option_positions_count": len(option_positions),
    }

    broker_account.sync_status = refresh.status
    broker_account.data_freshness_status = balance.data_freshness_status
    if refresh.status in {"succeeded", "partially_succeeded"}:
        broker_account.last_successful_sync_at = completed_at

    db.commit()
    db.refresh(sync_run)
    return sync_run
