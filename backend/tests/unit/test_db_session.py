import pytest
from sqlalchemy import text

from app.db.base import Base
from app.db.session import create_db_engine


pytestmark = pytest.mark.unit


def test_base_metadata_is_available() -> None:
    assert Base.metadata is not None


def test_create_db_engine_accepts_explicit_database_url() -> None:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
