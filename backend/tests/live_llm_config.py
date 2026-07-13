"""Live LLM smoke-test config loader.

This helper is intentionally test-only. It gives Codex/CI/dev shells a narrow
way to provide live-test credentials without making the normal test suite depend
on process environment, broad ``.env`` loading, or import-time application
settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_DOTENV_PATH = _BACKEND_ROOT.parent / ".env"
_LIVE_FLAG_KEYS: frozenset[str] = frozenset({"RUN_LIVE_LLM_TESTS", "POA_LLM_LIVE_TESTS"})
_PROJECT_DOTENV_KEY_ALLOWLIST: frozenset[str] = frozenset({"GOOGLE_API_KEY", "OPENAI_API_KEY"})
_ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "POA_AGENT_TEAM_REPORT_GENERATION_MODE",
        "POA_AGENT_TEAM_ROUTE_LIVE",
        "POA_LLM_LIVE_TESTS",
        "POA_LLM_MODE",
        "POA_LLM_MODEL",
        "POA_LLM_OPENAI_LIVE",
        "POA_LLM_PROVIDER",
        "RUN_LIVE_LLM_TESTS",
    }
)


def load_live_llm_test_config(environ: MutableMapping[str, str] | None = None) -> Path | None:
    """Load an optional gitignored live-test config into missing env keys only.

    ``POA_LIVE_LLM_TEST_CONFIG`` may point to another narrowly-scoped local
    config file. Generic ``.env`` files are intentionally rejected for explicit
    config paths.

    For founder-approved live smoke runs, setting ``RUN_LIVE_LLM_TESTS=true``
    (or legacy ``POA_LLM_LIVE_TESTS=1``) allows this helper to retrieve only the
    named LLM API key variables from the project ``.env`` file. It does not load
    flags, provider config, database settings, broker credentials, or unrelated
    secrets from the project dotenv.
    """

    env = environ if environ is not None else os.environ
    explicit_path = (env.get("POA_LIVE_LLM_TEST_CONFIG") or "").strip()
    if explicit_path:
        path = Path(explicit_path).expanduser()
        if not path.exists():
            return None
        _reject_generic_env_path(path)
        values = _parse_config(path)
        for key, value in values.items():
            if key in _ALLOWED_KEYS and key not in env:
                env[key] = value
        return path
    if _live_tests_explicitly_enabled(env):
        return _load_project_dotenv_llm_keys(env)
    return None


def _reject_generic_env_path(path: Path) -> None:
    if path.name in {".env", ".env.local"} or path.name.startswith(".env."):
        raise RuntimeError("live LLM tests must use a dedicated live-test config file, not a generic .env file")


def _parse_config(path: Path, *, allowed_keys: frozenset[str] = _ALLOWED_KEYS) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in allowed_keys:
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def _load_project_dotenv_llm_keys(env: MutableMapping[str, str]) -> Path | None:
    if not _PROJECT_DOTENV_PATH.exists():
        return None
    values = _parse_config(_PROJECT_DOTENV_PATH, allowed_keys=_PROJECT_DOTENV_KEY_ALLOWLIST)
    for key, value in values.items():
        if key not in env:
            env[key] = value
    return _PROJECT_DOTENV_PATH if values else None


def _live_tests_explicitly_enabled(env: MutableMapping[str, str]) -> bool:
    return any((env.get(key) or "").strip().lower() in {"1", "true", "yes", "on"} for key in _LIVE_FLAG_KEYS)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
