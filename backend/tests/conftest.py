from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

os.environ.setdefault("LOCAL_DEV_ACCESS_TOKEN", "test-local-dev-access-token")
os.environ.setdefault("SNAPTRADE_SECRET_ENCRYPTION_KEY", "test_snaptrade_secret_encryption_key_32_chars")

from app.db.session import SessionLocal, engine
from app.main import app as fastapi_app
from app.models.account import Account
from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.provider_credentials_metadata import ProviderCredentialsMetadata
from app.models.report_message import ReportMessage
from app.models.report_thread import ReportThread
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
    return TestClient(app, headers={"X-Local-Access-Token": "test-local-dev-access-token"})


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    if not _database_available():
        pytest.skip("Configured database is unavailable")

    db = SessionLocal()
    try:
        db.execute(delete(ProviderCredentialsMetadata))
        db.execute(delete(AgentStep))
        db.execute(delete(AgentRun))
        db.execute(delete(ReportMessage))
        db.execute(delete(ReportThread))
        db.execute(delete(BrokerSyncRun))
        db.execute(delete(BrokerAccount))
        db.execute(delete(BrokerConnection))
        db.execute(delete(OptionPosition))
        db.execute(delete(OptionContract))
        db.execute(delete(StockPosition))
        db.execute(delete(CashBalance))
        db.execute(delete(Account))
        db.execute(delete(User))
        db.commit()
        yield db
    finally:
        db.execute(delete(ProviderCredentialsMetadata))
        db.execute(delete(AgentStep))
        db.execute(delete(AgentRun))
        db.execute(delete(ReportMessage))
        db.execute(delete(ReportThread))
        db.execute(delete(BrokerSyncRun))
        db.execute(delete(BrokerAccount))
        db.execute(delete(BrokerConnection))
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
