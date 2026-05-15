import pytest

from app.services.broker_import.providers.snaptrade import SnapTradeAdapter
from app.services.broker_import.refresh_connections import refresh_snaptrade_connections
from app.services.broker_import.sync import sync_broker_account


pytestmark = [pytest.mark.smoke]


def test_snaptrade_primary_sync_modules_import_without_real_provider_calls() -> None:
    adapter = SnapTradeAdapter()

    assert adapter is not None
    assert callable(refresh_snaptrade_connections)
    assert callable(sync_broker_account)
