import pytest

from app.core.config import DEFAULT_DATABASE_URL, Settings, get_settings


pytestmark = pytest.mark.unit


def test_get_settings_uses_safe_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = get_settings()

    assert settings == Settings(
        app_name="portfolio-options-agent",
        app_env="local",
        database_url=DEFAULT_DATABASE_URL,
    )


def test_get_settings_reads_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/test_db")

    settings = get_settings()

    assert settings.app_name == "test-app"
    assert settings.app_env == "test"
    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/test_db"
