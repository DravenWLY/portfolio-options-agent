import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import create_db_engine


def test_configured_database_connection() -> None:
    engine = create_db_engine()

    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
    except SQLAlchemyError as exc:
        pytest.skip(f"Configured database is unavailable: {exc}")
