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
_DEFAULT_CONFIG_PATHS: tuple[Path, ...] = (
    _BACKEND_ROOT / "config.local.live-llm.env",
    _BACKEND_ROOT / "secrets" / "live-llm.env",
)
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

    Supported default files, relative to ``backend``:

    - ``config.local.live-llm.env``
    - ``secrets/live-llm.env``

    ``POA_LIVE_LLM_TEST_CONFIG`` may point to another narrowly-scoped local
    config file. Generic ``.env`` files are intentionally rejected.
    """

    env = environ if environ is not None else os.environ
    explicit_path = (env.get("POA_LIVE_LLM_TEST_CONFIG") or "").strip()
    paths = (Path(explicit_path).expanduser(),) if explicit_path else _DEFAULT_CONFIG_PATHS
    for path in paths:
        if not path.exists():
            continue
        _reject_generic_env_path(path)
        values = _parse_config(path)
        for key, value in values.items():
            if key in _ALLOWED_KEYS and key not in env:
                env[key] = value
        return path
    return None


def _reject_generic_env_path(path: Path) -> None:
    if path.name in {".env", ".env.local"} or path.name.startswith(".env."):
        raise RuntimeError("live LLM tests must use a dedicated live-test config file, not a generic .env file")


def _parse_config(path: Path) -> dict[str, str]:
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
        if key not in _ALLOWED_KEYS:
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
