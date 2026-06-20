from dataclasses import dataclass
import os


DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://portfolio_options_agent:"
    "portfolio_options_agent_dev_password@localhost:5432/portfolio_options_agent"
)


@dataclass(frozen=True)
class Settings:
    app_name: str = "portfolio-options-agent"
    app_env: str = "local"
    database_url: str = DEFAULT_DATABASE_URL
    local_dev_access_token: str = ""
    snaptrade_client_id: str = ""
    snaptrade_consumer_key: str = ""
    snaptrade_environment: str = "sandbox"
    snaptrade_secret_encryption_key: str = ""
    skyframe_fixtures_enabled: bool = False


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    settings = Settings(
        app_name=os.environ.get("APP_NAME", Settings.app_name),
        app_env=os.environ.get("APP_ENV", Settings.app_env),
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        local_dev_access_token=os.environ.get("LOCAL_DEV_ACCESS_TOKEN", Settings.local_dev_access_token),
        snaptrade_client_id=os.environ.get("SNAPTRADE_CLIENT_ID", Settings.snaptrade_client_id),
        snaptrade_consumer_key=os.environ.get("SNAPTRADE_CONSUMER_KEY", Settings.snaptrade_consumer_key),
        snaptrade_environment=os.environ.get("SNAPTRADE_ENVIRONMENT", Settings.snaptrade_environment),
        snaptrade_secret_encryption_key=os.environ.get(
            "SNAPTRADE_SECRET_ENCRYPTION_KEY",
            Settings.snaptrade_secret_encryption_key,
        ),
        skyframe_fixtures_enabled=_env_flag("POA_SKYFRAME_FIXTURES", Settings.skyframe_fixtures_enabled),
    )
    if settings.snaptrade_client_id and not settings.snaptrade_secret_encryption_key:
        raise ValueError("SNAPTRADE_SECRET_ENCRYPTION_KEY is required when SnapTrade is configured")
    return settings
