from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_sync_run import BrokerSyncRun
from app.services.broker_import.accounts import get_user_broker_account
from app.services.broker_import.normalization.cash import normalize_cash_balance
from app.services.broker_import.normalization.options import normalize_option_positions_safely
from app.services.broker_import.normalization.sanitization import sanitized_sync_error, sanitized_sync_summary
from app.services.broker_import.normalization.stocks import normalize_stock_positions
from app.services.broker_import.providers.exceptions import BrokerProviderError
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter
from app.services.broker_import.sync_runs import get_active_sync_run


class BrokerSyncAccountNotFoundError(RuntimeError):
    """Raised when a broker account cannot be synced because it is missing."""


class ActiveBrokerSyncRunError(RuntimeError):
    def __init__(self, sync_run: BrokerSyncRun) -> None:
        self.sync_run = sync_run
        super().__init__("Broker account already has an active sync run")


def sync_broker_account(
    db: Session,
    user_id: UUID,
    broker_account_id: UUID,
    adapter: SnapTradeAdapter,
    trigger: str = "manual",
) -> BrokerSyncRun:
    broker_account = get_user_broker_account(db, user_id, broker_account_id)
    if broker_account is None:
        raise BrokerSyncAccountNotFoundError("Broker account not found")
    if broker_account.account_id is None:
        raise BrokerSyncAccountNotFoundError("Broker account is not mapped to an internal account")

    active_run = get_active_sync_run(db, broker_account_id)
    if active_run is not None:
        raise ActiveBrokerSyncRunError(active_run)

    try:
        refresh = adapter.refresh_account(broker_account.provider_account_id)
        balance = adapter.get_balances(broker_account.provider_account_id)
        positions = adapter.get_positions(broker_account.provider_account_id)
        option_positions = adapter.get_option_positions(broker_account.provider_account_id)
    except BrokerProviderError as exc:
        started_at = datetime.now(UTC)
        sync_run = BrokerSyncRun(
            broker_connection_id=broker_account.broker_connection_id,
            broker_account_id=broker_account.id,
            trigger=trigger,
            status="failed",
            started_at=started_at,
            completed_at=datetime.now(UTC),
            error=sanitized_sync_error(exc.__class__.__name__, "Broker provider request failed"),
        )
        broker_account.sync_status = "failed"
        db.add(sync_run)
        db.commit()
        db.refresh(sync_run)
        return sync_run

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

    completed_at = refresh.completed_at or datetime.now(UTC)
    normalize_cash_balance(db, broker_account.account_id, balance, sync_run_id=sync_run.id)
    normalized_stock_positions = normalize_stock_positions(db, broker_account.account_id, positions, sync_run_id=sync_run.id)
    option_result = normalize_option_positions_safely(
        db,
        broker_account.account_id,
        option_positions,
        sync_run_id=sync_run.id,
    )
    partial_failures = option_result.partial_failures

    status = refresh.status
    if partial_failures and status == "succeeded":
        status = "partially_succeeded"
    if status not in {"succeeded", "partially_succeeded"}:
        status = "failed"

    sync_run.status = status
    sync_run.completed_at = completed_at
    sync_run.provider_request_id = refresh.provider_request_id
    sync_run.accounts_count = refresh.accounts_count
    sync_run.positions_count = len(normalized_stock_positions) + len(option_result.positions)
    sync_run.transactions_count = refresh.transactions_count
    sync_run.summary = sanitized_sync_summary(
        provider_request_id=refresh.provider_request_id,
        balance_currency=balance.currency,
        stock_positions_count=len(normalized_stock_positions),
        option_positions_count=len(option_result.positions),
        partial_failures=partial_failures,
        warnings=list(refresh.warnings),
    )

    broker_account.sync_status = status
    broker_account.data_freshness_status = balance.data_freshness_status
    if status in {"succeeded", "partially_succeeded"}:
        broker_account.last_successful_sync_at = completed_at

    db.commit()
    db.refresh(sync_run)
    return sync_run
