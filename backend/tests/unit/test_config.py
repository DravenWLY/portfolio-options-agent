import pytest

from app.core.config import DEFAULT_DATABASE_URL, Settings, get_settings


pytestmark = pytest.mark.unit


def test_get_settings_uses_safe_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_DEV_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("SNAPTRADE_CLIENT_ID", raising=False)
    monkeypatch.delenv("SNAPTRADE_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("SNAPTRADE_ENVIRONMENT", raising=False)
    monkeypatch.delenv("SNAPTRADE_SECRET_ENCRYPTION_KEY", raising=False)

    settings = get_settings()

    assert settings == Settings(
        app_name="portfolio-options-agent",
        app_env="local",
        database_url=DEFAULT_DATABASE_URL,
        local_dev_access_token="",
        snaptrade_client_id="",
        snaptrade_consumer_key="",
        snaptrade_environment="sandbox",
        snaptrade_secret_encryption_key="",
    )


def test_get_settings_reads_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/test_db")
    monkeypatch.setenv("LOCAL_DEV_ACCESS_TOKEN", "test-local-access-token")
    monkeypatch.setenv("SNAPTRADE_CLIENT_ID", "test_snaptrade_client_id")
    monkeypatch.setenv("SNAPTRADE_CONSUMER_KEY", "test_snaptrade_consumer_key")
    monkeypatch.setenv("SNAPTRADE_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("SNAPTRADE_SECRET_ENCRYPTION_KEY", "test_snaptrade_secret_encryption_key_32_chars")

    settings = get_settings()

    assert settings.app_name == "test-app"
    assert settings.app_env == "test"
    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/test_db"
    assert settings.local_dev_access_token == "test-local-access-token"
    assert settings.snaptrade_client_id == "test_snaptrade_client_id"
    assert settings.snaptrade_consumer_key == "test_snaptrade_consumer_key"
    assert settings.snaptrade_environment == "sandbox"
    assert settings.snaptrade_secret_encryption_key == "test_snaptrade_secret_encryption_key_32_chars"


def test_snaptrade_settings_default_to_no_real_credentials(monkeypatch) -> None:
    monkeypatch.delenv("SNAPTRADE_CLIENT_ID", raising=False)
    monkeypatch.delenv("SNAPTRADE_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("SNAPTRADE_SECRET_ENCRYPTION_KEY", raising=False)

    settings = get_settings()

    assert settings.snaptrade_client_id == ""
    assert settings.snaptrade_consumer_key == ""
    assert not settings.snaptrade_client_id.startswith("sk-")
    assert not settings.snaptrade_consumer_key.startswith("sk-")


def test_snaptrade_config_requires_encryption_key_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("SNAPTRADE_CLIENT_ID", "test_snaptrade_client_id")
    monkeypatch.delenv("SNAPTRADE_SECRET_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValueError, match="SNAPTRADE_SECRET_ENCRYPTION_KEY"):
        get_settings()
