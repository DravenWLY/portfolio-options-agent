"""Backend-only application configuration.

The application reads process environment plus an optional local dotenv file
through this module. Unit tests should pass explicit env mappings or disable
dotenv loading so they never depend on a developer's real ``.env`` file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DOTENV_PATH = PROJECT_ROOT / ".env"

DEFAULT_APP_NAME = "portfolio-options-agent"
DEFAULT_APP_ENV = "local"
DEFAULT_POSTGRES_DB = "portfolio_options_agent"
DEFAULT_POSTGRES_USER = "portfolio_options_agent"
DEFAULT_POSTGRES_PASSWORD = "portfolio_options_agent_dev_password"
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://portfolio_options_agent:"
    "portfolio_options_agent_dev_password@localhost:5432/portfolio_options_agent"
)
DEFAULT_SNAPTRADE_ENVIRONMENT = "sandbox"
DEFAULT_JBLANKED_CALENDAR_BASE_URL = "https://www.jblanked.com/news/api"
DEFAULT_JBLANKED_CALENDAR_SOURCE = "forexfactory"

_TRUE_VALUES = {"1", "true", "yes", "on"}
_SECRET_NAMES = {
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "LOCAL_DEV_ACCESS_TOKEN",
    "SNAPTRADE_CLIENT_ID",
    "SNAPTRADE_CONSUMER_KEY",
    "SNAPTRADE_SECRET_ENCRYPTION_KEY",
    "FMP_API_KEY",
    "FRED_API_KEY",
    "JBLANKED_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
}


class ConfigurationError(ValueError):
    """Raised for missing required live/production configuration."""


@dataclass(frozen=True)
class Settings:
    app_name: str = DEFAULT_APP_NAME
    app_env: str = DEFAULT_APP_ENV
    local_dev_access_token: str = field(default="", repr=False)

    skyframe_fixture_header: str = "private-safe-v1"
    skyframe_dashboard_state: str = "unavailable"
    skyframe_fixtures_enabled: bool = False

    postgres_db: str = DEFAULT_POSTGRES_DB
    postgres_user: str = DEFAULT_POSTGRES_USER
    postgres_password: str = field(default=DEFAULT_POSTGRES_PASSWORD, repr=False)
    postgres_port: int = DEFAULT_POSTGRES_PORT
    database_url: str = field(default=DEFAULT_DATABASE_URL, repr=False)

    snaptrade_client_id: str = field(default="", repr=False)
    snaptrade_consumer_key: str = field(default="", repr=False)
    snaptrade_environment: str = DEFAULT_SNAPTRADE_ENVIRONMENT
    snaptrade_secret_encryption_key: str = field(default="", repr=False)

    fmp_api_key: str = field(default="", repr=False)
    fred_api_key: str = field(default="", repr=False)
    jblanked_api_key: str = field(default="", repr=False)
    jblanked_calendar_base_url: str = DEFAULT_JBLANKED_CALENDAR_BASE_URL
    jblanked_calendar_source: str = DEFAULT_JBLANKED_CALENDAR_SOURCE
    market_context_mode: str = "off"
    fmp_fundamentals_mode: str = "off"
    fred_macro_series_mode: str = "off"
    edgar_report_evidence_mode: str = "off"
    sec_edgar_user_agent: str = field(default="", repr=False)
    p36_fmp_fundamentals_daily_request_budget: int = 10
    p36_fred_series_daily_request_budget: int = 18
    p36_edgar_daily_request_budget: int = 60
    p36_edgar_max_requests_per_second: int = 1

    google_api_key: str = field(default="", repr=False)
    openai_api_key: str = field(default="", repr=False)

    @property
    def is_production_like(self) -> bool:
        return self.app_env.strip().lower() in {"prod", "production", "staging"}

    def public_snapshot(self) -> dict[str, object]:
        """Return non-secret metadata safe for tests/diagnostics."""

        return {
            "app_name": self.app_name,
            "app_env": self.app_env,
            "skyframe_fixtures_enabled": self.skyframe_fixtures_enabled,
            "postgres_db": self.postgres_db,
            "postgres_user": self.postgres_user,
            "postgres_port": self.postgres_port,
            "snaptrade_environment": self.snaptrade_environment,
            "jblanked_calendar_base_url": self.jblanked_calendar_base_url,
            "jblanked_calendar_source": self.jblanked_calendar_source,
            "local_dev_access_token_configured": bool(self.local_dev_access_token),
            "database_url_configured": bool(self.database_url),
            "snaptrade_client_configured": bool(self.snaptrade_client_id and self.snaptrade_consumer_key),
            "snaptrade_secret_encryption_key_configured": bool(self.snaptrade_secret_encryption_key),
            "fmp_api_key_configured": bool(self.fmp_api_key),
            "fred_api_key_configured": bool(self.fred_api_key),
            "jblanked_api_key_configured": bool(self.jblanked_api_key),
            "market_context_mode": self.market_context_mode,
            "fmp_fundamentals_mode": self.fmp_fundamentals_mode,
            "fred_macro_series_mode": self.fred_macro_series_mode,
            "edgar_report_evidence_mode": self.edgar_report_evidence_mode,
            "p36_fmp_fundamentals_daily_request_budget": self.p36_fmp_fundamentals_daily_request_budget,
            "p36_fred_series_daily_request_budget": self.p36_fred_series_daily_request_budget,
            "p36_edgar_daily_request_budget": self.p36_edgar_daily_request_budget,
            "p36_edgar_max_requests_per_second": self.p36_edgar_max_requests_per_second,
            "google_api_key_configured": bool(self.google_api_key),
            "openai_api_key_configured": bool(self.openai_api_key),
        }

    def require_google_api_key(self) -> str:
        if not self.google_api_key:
            raise ConfigurationError("GOOGLE_API_KEY is required for live Google LLM mode")
        return self.google_api_key

    def require_openai_api_key(self) -> str:
        if not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for live OpenAI LLM mode")
        return self.openai_api_key

    def require_fmp_api_key(self) -> str:
        if not self.fmp_api_key:
            raise ConfigurationError("FMP_API_KEY is required for live FMP economic calendar refresh")
        return self.fmp_api_key

    def require_fred_api_key(self) -> str:
        if not self.fred_api_key:
            raise ConfigurationError("FRED_API_KEY is required for live FRED economic calendar refresh")
        return self.fred_api_key


def get_settings() -> Settings:
    """FastAPI-safe dependency wrapper with no request-parsed parameters."""

    return build_settings()


def build_settings(
    env: Mapping[str, str] | None = None,
    *,
    dotenv_path: str | Path | None = None,
    load_dotenv: bool = True,
) -> Settings:
    """Build backend settings from dotenv defaults plus process environment.

    Precedence, lowest to highest:
    defaults -> selected dotenv file -> explicit/process env.

    ``env`` and ``dotenv_path`` are injection seams for tests. Passing
    ``load_dotenv=False`` guarantees no local dotenv file is read.
    """

    env_values = dict(os.environ if env is None else env)
    dotenv_values = _dotenv_values(env_values, dotenv_path=dotenv_path, load_dotenv=load_dotenv)
    values = {**dotenv_values, **env_values}
    settings = Settings(
        app_name=_text(values.get("APP_NAME"), default=DEFAULT_APP_NAME),
        app_env=_text(values.get("APP_ENV"), default=DEFAULT_APP_ENV),
        local_dev_access_token=_secret(values.get("LOCAL_DEV_ACCESS_TOKEN")),
        skyframe_fixture_header=_text(values.get("SKYFRAME_FIXTURE_HEADER"), default="private-safe-v1"),
        skyframe_dashboard_state=_text(values.get("SKYFRAME_DASHBOARD_STATE"), default="unavailable"),
        skyframe_fixtures_enabled=_flag(values.get("POA_SKYFRAME_FIXTURES"), default=False),
        postgres_db=_text(values.get("POSTGRES_DB"), default=DEFAULT_POSTGRES_DB),
        postgres_user=_text(values.get("POSTGRES_USER"), default=DEFAULT_POSTGRES_USER),
        postgres_password=_secret(values.get("POSTGRES_PASSWORD"), default=DEFAULT_POSTGRES_PASSWORD),
        postgres_port=_int(values.get("POSTGRES_PORT"), default=DEFAULT_POSTGRES_PORT),
        database_url=_secret(values.get("DATABASE_URL"), default=DEFAULT_DATABASE_URL),
        snaptrade_client_id=_secret(values.get("SNAPTRADE_CLIENT_ID")),
        snaptrade_consumer_key=_secret(values.get("SNAPTRADE_CONSUMER_KEY")),
        snaptrade_environment=_text(values.get("SNAPTRADE_ENVIRONMENT"), default=DEFAULT_SNAPTRADE_ENVIRONMENT),
        snaptrade_secret_encryption_key=_secret(values.get("SNAPTRADE_SECRET_ENCRYPTION_KEY")),
        fmp_api_key=_secret(values.get("FMP_API_KEY")),
        fred_api_key=_secret(values.get("FRED_API_KEY")),
        jblanked_api_key=_secret(values.get("JBLANKED_API_KEY")),
        jblanked_calendar_base_url=_text(
            values.get("JBLANKED_CALENDAR_BASE_URL"),
            default=DEFAULT_JBLANKED_CALENDAR_BASE_URL,
        ),
        jblanked_calendar_source=_text(
            values.get("JBLANKED_CALENDAR_SOURCE"),
            default=DEFAULT_JBLANKED_CALENDAR_SOURCE,
        ),
        market_context_mode=_text(values.get("POA_MARKET_CONTEXT_MODE"), default="off"),
        fmp_fundamentals_mode=_text(values.get("POA_FMP_FUNDAMENTALS_MODE"), default="off"),
        fred_macro_series_mode=_text(values.get("POA_FRED_MACRO_SERIES_MODE"), default="off"),
        edgar_report_evidence_mode=_text(values.get("POA_EDGAR_REPORT_EVIDENCE_MODE"), default="off"),
        sec_edgar_user_agent=_text(values.get("SEC_EDGAR_USER_AGENT"), default=""),
        p36_fmp_fundamentals_daily_request_budget=_int(
            values.get("P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET"), default=10
        ),
        p36_fred_series_daily_request_budget=_int(
            values.get("P36_FRED_SERIES_DAILY_REQUEST_BUDGET"), default=18
        ),
        p36_edgar_daily_request_budget=_int(values.get("P36_EDGAR_DAILY_REQUEST_BUDGET"), default=60),
        p36_edgar_max_requests_per_second=_int(values.get("P36_EDGAR_MAX_REQUESTS_PER_SECOND"), default=1),
        google_api_key=_secret(values.get("GOOGLE_API_KEY")),
        openai_api_key=_secret(values.get("OPENAI_API_KEY")),
    )
    _validate_settings(settings)
    return settings


def load_dotenv_values(path: str | Path) -> dict[str, str]:
    """Parse a small dotenv file without mutating ``os.environ``."""

    file_path = Path(path).expanduser()
    if not file_path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _strip_inline_comment(_strip_quotes(value.strip()))
    return values


def _dotenv_values(
    env_values: Mapping[str, str],
    *,
    dotenv_path: str | Path | None,
    load_dotenv: bool,
) -> dict[str, str]:
    if not load_dotenv or _flag(env_values.get("POA_DOTENV_DISABLED"), default=False):
        return {}
    selected_path = dotenv_path
    if selected_path is None:
        selected_path = env_values.get("POA_DOTENV_PATH") or DEFAULT_DOTENV_PATH
    return load_dotenv_values(selected_path)


def _validate_settings(settings: Settings) -> None:
    if settings.snaptrade_client_id and not settings.snaptrade_secret_encryption_key:
        raise ConfigurationError("SNAPTRADE_SECRET_ENCRYPTION_KEY is required when SnapTrade is configured")
    if settings.is_production_like:
        missing = []
        if not settings.local_dev_access_token:
            missing.append("LOCAL_DEV_ACCESS_TOKEN")
        if not settings.database_url:
            missing.append("DATABASE_URL")
        if settings.snaptrade_client_id and not settings.snaptrade_consumer_key:
            missing.append("SNAPTRADE_CONSUMER_KEY")
        if missing:
            raise ConfigurationError(f"Missing required production-like settings: {', '.join(missing)}")
    if not 1 <= settings.p36_fmp_fundamentals_daily_request_budget <= 10:
        raise ConfigurationError("P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET must be between 1 and 10")
    if not 1 <= settings.p36_fred_series_daily_request_budget <= 18:
        raise ConfigurationError("P36_FRED_SERIES_DAILY_REQUEST_BUDGET must be between 1 and 18")
    if not 1 <= settings.p36_edgar_daily_request_budget <= 60:
        raise ConfigurationError("P36_EDGAR_DAILY_REQUEST_BUDGET must be between 1 and 60")
    if settings.p36_edgar_max_requests_per_second != 1:
        raise ConfigurationError("P36_EDGAR_MAX_REQUESTS_PER_SECOND must be 1")


def _text(value: str | None, *, default: str) -> str:
    if value is None:
        return default
    text = value.strip()
    return text or default


def _secret(value: str | None, *, default: str = "") -> str:
    if value is None:
        return default
    return value.strip()


def _int(value: str | None, *, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ConfigurationError("Configuration integer value is invalid") from exc


def _flag(value: str | None, *, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in _TRUE_VALUES


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _strip_inline_comment(value: str) -> str:
    # Keep URLs and secrets intact; only strip comments after whitespace.
    marker = " #"
    if marker in value:
        return value.split(marker, 1)[0].rstrip()
    return value
