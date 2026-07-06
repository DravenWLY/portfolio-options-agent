"""Public backend configuration facade.

Application code should import settings from ``app.config`` (or receive a
``Settings`` instance through dependency injection). The implementation lives in
``app.core.config`` so older imports remain compatible while new code has a
short, stable module path.
"""

from __future__ import annotations

from app.core.config import (
    DEFAULT_APP_ENV,
    DEFAULT_APP_NAME,
    DEFAULT_DATABASE_URL,
    DEFAULT_DOTENV_PATH,
    DEFAULT_JBLANKED_CALENDAR_BASE_URL,
    DEFAULT_JBLANKED_CALENDAR_SOURCE,
    DEFAULT_POSTGRES_DB,
    DEFAULT_POSTGRES_PASSWORD,
    DEFAULT_POSTGRES_PORT,
    DEFAULT_POSTGRES_USER,
    DEFAULT_SNAPTRADE_ENVIRONMENT,
    PROJECT_ROOT,
    ConfigurationError,
    Settings,
    build_settings,
    get_settings,
    load_dotenv_values,
)

__all__ = [
    "DEFAULT_APP_ENV",
    "DEFAULT_APP_NAME",
    "DEFAULT_DATABASE_URL",
    "DEFAULT_DOTENV_PATH",
    "DEFAULT_JBLANKED_CALENDAR_BASE_URL",
    "DEFAULT_JBLANKED_CALENDAR_SOURCE",
    "DEFAULT_POSTGRES_DB",
    "DEFAULT_POSTGRES_PASSWORD",
    "DEFAULT_POSTGRES_PORT",
    "DEFAULT_POSTGRES_USER",
    "DEFAULT_SNAPTRADE_ENVIRONMENT",
    "PROJECT_ROOT",
    "ConfigurationError",
    "Settings",
    "build_settings",
    "get_settings",
    "load_dotenv_values",
]
