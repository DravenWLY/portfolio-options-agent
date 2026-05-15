from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.main import app as fastapi_app
from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.models.user import User


def _database_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    if not _database_available():
        pytest.skip("Configured database is unavailable")

    db = SessionLocal()
    try:
        db.execute(delete(OptionPosition))
        db.execute(delete(OptionContract))
        db.execute(delete(StockPosition))
        db.execute(delete(CashBalance))
        db.execute(delete(Account))
        db.execute(delete(User))
        db.commit()
        yield db
    finally:
        db.execute(delete(OptionPosition))
        db.execute(delete(OptionContract))
        db.execute(delete(StockPosition))
        db.execute(delete(CashBalance))
        db.execute(delete(Account))
        db.execute(delete(User))
        db.commit()
        db.close()


@pytest.fixture
def synthetic_user_data() -> dict[str, str]:
    return {
        "display_name": "Demo User",
        "email": "demo@example.com",
    }


@pytest.fixture
def synthetic_account_data() -> dict[str, str]:
    return {
        "broker_name": "Demo Broker",
        "account_type": "taxable_individual",
        "display_name": "Demo Taxable Account",
        "base_currency": "USD",
    }


@pytest.fixture
def fake_api_key() -> str:
    return "test_fake_api_key_do_not_use"
