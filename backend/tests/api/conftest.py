from collections.abc import Generator

import pytest
from sqlalchemy import delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.models.user import User


def _database_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    if not _database_available():
        pytest.skip("Configured database is unavailable")

    db = SessionLocal()
    try:
        db.execute(delete(CashBalance))
        db.execute(delete(Account))
        db.execute(delete(User))
        db.commit()
        yield db
    finally:
        db.execute(delete(CashBalance))
        db.execute(delete(Account))
        db.execute(delete(User))
        db.commit()
        db.close()
