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
    snaptrade_client_id: str = ""
    snaptrade_consumer_key: str = ""
    snaptrade_environment: str = "sandbox"
    snaptrade_secret_encryption_key: str = ""


def get_settings() -> Settings:
    settings = Settings(
        app_name=os.environ.get("APP_NAME", Settings.app_name),
        app_env=os.environ.get("APP_ENV", Settings.app_env),
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        snaptrade_client_id=os.environ.get("SNAPTRADE_CLIENT_ID", Settings.snaptrade_client_id),
        snaptrade_consumer_key=os.environ.get("SNAPTRADE_CONSUMER_KEY", Settings.snaptrade_consumer_key),
        snaptrade_environment=os.environ.get("SNAPTRADE_ENVIRONMENT", Settings.snaptrade_environment),
        snaptrade_secret_encryption_key=os.environ.get(
            "SNAPTRADE_SECRET_ENCRYPTION_KEY",
            Settings.snaptrade_secret_encryption_key,
        ),
    )
    if settings.snaptrade_client_id and not settings.snaptrade_secret_encryption_key:
        raise ValueError("SNAPTRADE_SECRET_ENCRYPTION_KEY is required when SnapTrade is configured")
    return settings
