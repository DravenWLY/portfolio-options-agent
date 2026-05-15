import inspect

import pytest

from app.services.broker_import.providers.base import BrokerPortfolioProvider
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter, SnapTradeAdapterNotConfiguredError


pytestmark = [pytest.mark.adapter, pytest.mark.unit]


READ_ONLY_METHODS = {
    "list_connections",
    "list_accounts",
    "get_balances",
    "get_positions",
    "get_option_positions",
    "get_transactions",
    "refresh_account",
}

FORBIDDEN_TRADING_METHODS = {
    "place_order",
    "submit_order",
    "cancel_order",
    "replace_order",
    "execute_trade",
    "trade",
    "preview_order",
}


def test_snaptrade_adapter_satisfies_broker_portfolio_provider_protocol() -> None:
    adapter = SnapTradeAdapter()

    assert isinstance(adapter, BrokerPortfolioProvider)
    assert adapter.provider_name == "snaptrade"


def test_snaptrade_adapter_exposes_read_only_provider_methods() -> None:
    adapter_methods = {
        name
        for name, value in inspect.getmembers(SnapTradeAdapter, predicate=inspect.isfunction)
        if not name.startswith("_")
    }

    assert READ_ONLY_METHODS.issubset(adapter_methods)
    assert FORBIDDEN_TRADING_METHODS.isdisjoint(adapter_methods)


@pytest.mark.parametrize("method_name", sorted(READ_ONLY_METHODS))
def test_snaptrade_adapter_read_only_methods_raise_not_configured(method_name: str) -> None:
    adapter = SnapTradeAdapter()

    with pytest.raises(SnapTradeAdapterNotConfiguredError, match="read-only skeleton"):
        if method_name == "get_transactions":
            getattr(adapter, method_name)("demo-account", None, None)
        else:
            getattr(adapter, method_name)("demo-reference")


def test_snaptrade_adapter_has_no_trading_or_order_members() -> None:
    adapter_members = set(dir(SnapTradeAdapter))

    assert FORBIDDEN_TRADING_METHODS.isdisjoint(adapter_members)
