import pytest
from pydantic import ValidationError

from app.schemas.account import AccountCreate, AccountNicknameUpdate, AccountUpdate
from app.schemas.user import UserCreate


pytestmark = pytest.mark.unit


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


def test_account_nickname_update_normalizes_safe_text_and_allows_clear() -> None:
    payload = AccountNicknameUpdate(nickname="  Momentum   IRA  ")

    assert payload.nickname == "Momentum IRA"
    assert AccountNicknameUpdate(nickname=None).nickname is None
    assert AccountNicknameUpdate(nickname="   ").nickname is None
    assert AccountNicknameUpdate(nickname=" " * 100).nickname is None


@pytest.mark.parametrize(
    "nickname",
    (
        "Account 123456",
        "provider_account_id secret",
        "buying_power test",
        "buying power test",
        "api_key test",
        "api key test",
        "access_token test",
        "access token test",
        "raw_payload detail",
        "safe to trade account",
        "ready-to-trade account",
        "Guaranteed return",
        "You should buy",
        "Recommend buying",
        "<script>alert(1)</script>",
    ),
)
def test_account_nickname_update_rejects_private_or_unsupported_text(nickname: str) -> None:
    with pytest.raises(ValidationError):
        AccountNicknameUpdate(nickname=nickname)
