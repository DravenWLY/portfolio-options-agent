from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.services.broker_import.interfaces import BrokerSyncService
from app.services.broker_import.models import (
    BrokerAccountSnapshot,
    BrokerBalanceSnapshot,
    BrokerConnectionSnapshot,
    BrokerOptionPositionSnapshot,
    BrokerPositionSnapshot,
    BrokerSyncRequest,
    BrokerSyncResult,
)


pytestmark = [pytest.mark.unit]


class FakeBrokerSyncService:
    def __init__(self) -> None:
        self.connection_id = uuid4()
        self.account_id = uuid4()
        self.synced_at = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)

    def list_connections(self, user_id: UUID) -> list[BrokerConnectionSnapshot]:
        return [
            BrokerConnectionSnapshot(
                provider="snaptrade",
                broker_name="Demo Fidelity",
                provider_connection_id="demo-connection",
                connection_status="connected",
                sync_status="succeeded",
                data_freshness_status="fresh",
                synced_at=self.synced_at,
                received_at=self.synced_at,
            )
        ]

    def list_accounts(self, broker_connection_id: UUID) -> list[BrokerAccountSnapshot]:
        return [
            BrokerAccountSnapshot(
                provider_account_id="demo-provider-account",
                display_name="Demo Taxable Account",
                account_type="taxable_individual",
                base_currency="USD",
                sync_status="succeeded",
                data_freshness_status="fresh",
                synced_at=self.synced_at,
                received_at=self.synced_at,
            )
        ]

    def get_balance_snapshot(self, broker_account_id: UUID) -> BrokerBalanceSnapshot:
        return BrokerBalanceSnapshot(
            provider_account_id="demo-provider-account",
            total_cash=Decimal("10000.00"),
            available_cash=Decimal("7500.00"),
            buying_power=Decimal("10000.00"),
            currency="USD",
            synced_at=self.synced_at,
            data_freshness_status="fresh",
        )

    def get_position_snapshots(self, broker_account_id: UUID) -> list[BrokerPositionSnapshot]:
        return [
            BrokerPositionSnapshot(
                provider_account_id="demo-provider-account",
                symbol="VOO",
                quantity=Decimal("10"),
                asset_type="etf",
                market_value=Decimal("4500.00"),
                currency="USD",
                synced_at=self.synced_at,
                data_freshness_status="fresh",
            )
        ]

    def get_option_position_snapshots(self, broker_account_id: UUID) -> list[BrokerOptionPositionSnapshot]:
        return [
            BrokerOptionPositionSnapshot(
                provider_account_id="demo-provider-account",
                occ_symbol="VOO260116P00400000",
                underlying_symbol="VOO",
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("210.00"),
                currency="USD",
                synced_at=self.synced_at,
                data_freshness_status="fresh",
            )
        ]

    def request_sync(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        return BrokerSyncResult(
            broker_connection_id=request.broker_connection_id,
            broker_account_id=request.broker_account_id,
            status="succeeded",
            started_at=self.synced_at,
            completed_at=self.synced_at,
            accounts_count=1,
            positions_count=2,
            transactions_count=0,
            metadata={"provider": "snaptrade", "mode": "synthetic"},
        )


def test_fake_broker_sync_service_satisfies_protocol() -> None:
    service = FakeBrokerSyncService()

    assert isinstance(service, BrokerSyncService)


def test_broker_sync_service_interface_returns_sanitized_snapshots() -> None:
    service = FakeBrokerSyncService()
    user_id = uuid4()

    connections = service.list_connections(user_id)
    accounts = service.list_accounts(service.connection_id)
    balance = service.get_balance_snapshot(service.account_id)
    positions = service.get_position_snapshots(service.account_id)
    options = service.get_option_position_snapshots(service.account_id)

    assert connections[0].provider == "snaptrade"
    assert accounts[0].provider_account_id == "demo-provider-account"
    assert balance.total_cash == Decimal("10000.00")
    assert positions[0].symbol == "VOO"
    assert options[0].position_side == "short"


def test_broker_sync_request_and_result_validate_statuses() -> None:
    service = FakeBrokerSyncService()
    request = BrokerSyncRequest(
        broker_connection_id=service.connection_id,
        broker_account_id=service.account_id,
        trigger="manual",
        force_refresh=True,
    )

    result = service.request_sync(request)

    assert result.status == "succeeded"
    assert result.accounts_count == 1
    assert result.positions_count == 2
    assert result.transactions_count == 0


def test_broker_sync_models_reject_invalid_values() -> None:
    with pytest.raises(ValueError):
        BrokerSyncRequest(broker_connection_id=uuid4(), trigger="browser_scrape")

    with pytest.raises(ValueError):
        BrokerConnectionSnapshot(
            provider="snaptrade",
            broker_name="Demo Fidelity",
            provider_connection_id="demo-connection",
            connection_status="mystery",
            sync_status="succeeded",
            data_freshness_status="fresh",
        )

    with pytest.raises(ValueError):
        BrokerSyncResult(
            broker_connection_id=uuid4(),
            broker_account_id=None,
            status="idle",
            started_at=None,
            completed_at=None,
        )
