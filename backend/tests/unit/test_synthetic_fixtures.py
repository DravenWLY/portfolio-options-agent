import pytest


pytestmark = [pytest.mark.unit, pytest.mark.smoke]


def test_synthetic_user_fixture_uses_demo_identity(synthetic_user_data: dict[str, str]) -> None:
    assert synthetic_user_data["display_name"] == "Demo User"
    assert synthetic_user_data["email"] == "demo@example.com"


def test_synthetic_account_fixture_uses_demo_account(synthetic_account_data: dict[str, str]) -> None:
    assert synthetic_account_data == {
        "broker_name": "Demo Broker",
        "account_type": "taxable_individual",
        "display_name": "Demo Taxable Account",
        "base_currency": "USD",
    }


def test_fake_api_key_is_obviously_not_real(fake_api_key: str) -> None:
    assert fake_api_key.startswith("test_")
    assert not fake_api_key.startswith(("sk-", "xoxb-", "ghp_", "AIza"))
