import pytest
from uuid import UUID

from app.db.base import Base
from app.models.user import User


pytestmark = pytest.mark.unit


def test_user_model_is_registered_with_base_metadata() -> None:
    assert "users" in Base.metadata.tables


def test_user_model_columns() -> None:
    columns = User.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "display_name",
        "email",
        "auth_provider",
        "is_active",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns["display_name"].nullable is False
    assert columns["email"].nullable is True


def test_user_defaults_are_application_safe() -> None:
    user = User(display_name="Demo User")

    assert isinstance(user.id, UUID) or user.id is None
    assert user.display_name == "Demo User"
    assert user.email is None
