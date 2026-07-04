from pathlib import Path

import pytest

from app.core.config import (
    DEFAULT_DATABASE_URL,
    DEFAULT_JBLANKED_CALENDAR_BASE_URL,
    ConfigurationError,
    Settings,
    build_settings,
    load_dotenv_values,
)


pytestmark = pytest.mark.unit


def test_get_settings_uses_safe_defaults_without_dotenv() -> None:
    settings = build_settings(env={}, load_dotenv=False)

    assert settings == Settings()
    assert settings.app_name == "portfolio-options-agent"
    assert settings.app_env == "local"
    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.postgres_port == 5432
    assert settings.snaptrade_environment == "sandbox"
    assert settings.jblanked_calendar_base_url == DEFAULT_JBLANKED_CALENDAR_BASE_URL
    assert settings.jblanked_calendar_source == "forexfactory"
    assert settings.google_api_key == ""
    assert settings.openai_api_key == ""


def test_process_environment_overrides_dotenv_values(tmp_path: Path) -> None:
    dotenv_path = tmp_path / "test.env"
    dotenv_path.write_text(
        "\n".join(
            [
                "APP_NAME=dotenv-app",
                "APP_ENV=dotenv",
                "DATABASE_URL=postgresql+psycopg://dotenv:secret@localhost:5432/dotenv_db",
                "LOCAL_DEV_ACCESS_TOKEN=dotenv-token",
                "FRED_API_KEY=dotenv-fred-key",
            ]
        ),
        encoding="utf-8",
    )

    settings = build_settings(
        env={
            "APP_NAME": "process-app",
            "DATABASE_URL": "postgresql+psycopg://process:secret@localhost:5432/process_db",
            "FRED_API_KEY": "process-fred-key",
        },
        dotenv_path=dotenv_path,
    )

    assert settings.app_name == "process-app"
    assert settings.app_env == "dotenv"
    assert settings.database_url == "postgresql+psycopg://process:secret@localhost:5432/process_db"
    assert settings.local_dev_access_token == "dotenv-token"
    assert settings.fred_api_key == "process-fred-key"


def test_explicit_poa_dotenv_path_loads_temporary_dotenv(tmp_path: Path) -> None:
    dotenv_path = tmp_path / "explicit.env"
    dotenv_path.write_text(
        "\n".join(
            [
                "APP_ENV=test",
                "POSTGRES_DB=poa_test",
                "POSTGRES_USER=poa_user",
                "POSTGRES_PASSWORD='test-password'",
                "POSTGRES_PORT=55432",
                "SNAPTRADE_ENVIRONMENT=production",
                "JBLANKED_CALENDAR_SOURCE=forexfactory-demo",
                "GOOGLE_API_KEY=test-key-not-real",
                "OPENAI_API_KEY=test-openai-key-not-real",
            ]
        ),
        encoding="utf-8",
    )

    settings = build_settings(env={"POA_DOTENV_PATH": str(dotenv_path)})

    assert settings.app_env == "test"
    assert settings.postgres_db == "poa_test"
    assert settings.postgres_user == "poa_user"
    assert settings.postgres_password == "test-password"
    assert settings.postgres_port == 55432
    assert settings.snaptrade_environment == "production"
    assert settings.jblanked_calendar_source == "forexfactory-demo"
    assert settings.google_api_key == "test-key-not-real"
    assert settings.openai_api_key == "test-openai-key-not-real"


def test_missing_dotenv_file_does_not_fail(tmp_path: Path) -> None:
    settings = build_settings(env={"POA_DOTENV_PATH": str(tmp_path / "missing.env")})

    assert settings.app_name == "portfolio-options-agent"


def test_dotenv_loading_can_be_disabled_even_when_path_is_set(tmp_path: Path) -> None:
    dotenv_path = tmp_path / "ignored.env"
    dotenv_path.write_text("APP_NAME=ignored-app", encoding="utf-8")

    settings = build_settings(
        env={
            "POA_DOTENV_PATH": str(dotenv_path),
            "POA_DOTENV_DISABLED": "1",
        }
    )

    assert settings.app_name == "portfolio-options-agent"


def test_secret_values_are_not_in_repr_or_public_snapshot() -> None:
    settings = build_settings(
        env={
            "DATABASE_URL": "postgresql+psycopg://user:secret-password@localhost:5432/test_db",
            "LOCAL_DEV_ACCESS_TOKEN": "test-local-token",
            "SNAPTRADE_CLIENT_ID": "test-client-id",
            "SNAPTRADE_CONSUMER_KEY": "test-consumer-key",
            "SNAPTRADE_SECRET_ENCRYPTION_KEY": "test-encryption-key",
            "FMP_API_KEY": "test-fmp-key",
            "FRED_API_KEY": "test-fred-key",
            "JBLANKED_API_KEY": "test-jblanked-key",
            "GOOGLE_API_KEY": "test-key-not-real",
            "OPENAI_API_KEY": "test-openai-key-not-real",
        },
        load_dotenv=False,
    )

    rendered = repr(settings)
    snapshot = settings.public_snapshot()
    for secret in (
        "secret-password",
        "test-local-token",
        "test-client-id",
        "test-consumer-key",
        "test-encryption-key",
        "test-fmp-key",
        "test-fred-key",
        "test-jblanked-key",
        "test-key-not-real",
        "test-openai-key-not-real",
    ):
        assert secret not in rendered
        assert secret not in repr(snapshot)
    assert snapshot["google_api_key_configured"] is True
    assert snapshot["openai_api_key_configured"] is True


def test_unit_tests_can_use_fake_api_keys() -> None:
    settings = build_settings(
        env={
            "GOOGLE_API_KEY": "test-key-not-real",
            "OPENAI_API_KEY": "test-openai-key-not-real",
        },
        load_dotenv=False,
    )

    assert settings.require_google_api_key() == "test-key-not-real"
    assert settings.require_openai_api_key() == "test-openai-key-not-real"


def test_secret_accessors_raise_without_revealing_values() -> None:
    settings = build_settings(env={}, load_dotenv=False)

    with pytest.raises(ConfigurationError, match="GOOGLE_API_KEY is required"):
        settings.require_google_api_key()
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY is required"):
        settings.require_openai_api_key()


def test_snaptrade_config_requires_encryption_key_when_configured() -> None:
    with pytest.raises(ConfigurationError, match="SNAPTRADE_SECRET_ENCRYPTION_KEY"):
        build_settings(env={"SNAPTRADE_CLIENT_ID": "test_snaptrade_client_id"}, load_dotenv=False)


def test_dotenv_parser_handles_exports_quotes_and_comments(tmp_path: Path) -> None:
    dotenv_path = tmp_path / "parser.env"
    dotenv_path.write_text(
        "\n".join(
            [
                "# comment",
                "export APP_NAME='quoted app'",
                'JBLANKED_CALENDAR_BASE_URL="https://example.test/news/api"',
                "APP_ENV=local # inline comment",
            ]
        ),
        encoding="utf-8",
    )

    values = load_dotenv_values(dotenv_path)

    assert values == {
        "APP_NAME": "quoted app",
        "JBLANKED_CALENDAR_BASE_URL": "https://example.test/news/api",
        "APP_ENV": "local",
    }
