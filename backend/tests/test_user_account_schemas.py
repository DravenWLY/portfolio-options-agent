import pytest
from pydantic import ValidationError

from app.schemas.account import AccountCreate, AccountUpdate
from app.schemas.user import UserCreate


def test_user_create_schema_accepts_optional_email() -> None:
    payload = UserCreate(display_name="Demo User")

    assert payload.display_name == "Demo User"
    assert payload.email is None


def test_account_create_normalizes_currency() -> None:
    payload = AccountCreate(
        broker_name="Demo Broker",
        account_type="taxable_individual",
        display_name="Demo Taxable",
        base_currency="usd",
    )

    assert payload.base_currency == "USD"


def test_account_create_rejects_invalid_account_type() -> None:
    with pytest.raises(ValidationError):
        AccountCreate(
            broker_name="Demo Broker",
            account_type="unsupported",
            display_name="Demo Account",
        )


def test_account_update_allows_partial_payload() -> None:
    payload = AccountUpdate(display_name="Updated")

    assert payload.model_dump(exclude_unset=True) == {"display_name": "Updated"}
