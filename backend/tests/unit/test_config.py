import pytest

from app.core.config import DEFAULT_DATABASE_URL, Settings, get_settings


pytestmark = pytest.mark.unit


def test_get_settings_uses_safe_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SNAPTRADE_CLIENT_ID", raising=False)
    monkeypatch.delenv("SNAPTRADE_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("SNAPTRADE_ENVIRONMENT", raising=False)

    settings = get_settings()

    assert settings == Settings(
        app_name="portfolio-options-agent",
        app_env="local",
        database_url=DEFAULT_DATABASE_URL,
        snaptrade_client_id="",
        snaptrade_consumer_key="",
        snaptrade_environment="sandbox",
    )


def test_get_settings_reads_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/test_db")
    monkeypatch.setenv("SNAPTRADE_CLIENT_ID", "test_snaptrade_client_id")
    monkeypatch.setenv("SNAPTRADE_CONSUMER_KEY", "test_snaptrade_consumer_key")
    monkeypatch.setenv("SNAPTRADE_ENVIRONMENT", "sandbox")

    settings = get_settings()

    assert settings.app_name == "test-app"
    assert settings.app_env == "test"
    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/test_db"
    assert settings.snaptrade_client_id == "test_snaptrade_client_id"
    assert settings.snaptrade_consumer_key == "test_snaptrade_consumer_key"
    assert settings.snaptrade_environment == "sandbox"


def test_snaptrade_settings_default_to_no_real_credentials(monkeypatch) -> None:
    monkeypatch.delenv("SNAPTRADE_CLIENT_ID", raising=False)
    monkeypatch.delenv("SNAPTRADE_CONSUMER_KEY", raising=False)

    settings = get_settings()

    assert settings.snaptrade_client_id == ""
    assert settings.snaptrade_consumer_key == ""
    assert not settings.snaptrade_client_id.startswith("sk-")
    assert not settings.snaptrade_consumer_key.startswith("sk-")
