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


def get_settings() -> Settings:
    return Settings(
        app_name=os.environ.get("APP_NAME", Settings.app_name),
        app_env=os.environ.get("APP_ENV", Settings.app_env),
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
    )
