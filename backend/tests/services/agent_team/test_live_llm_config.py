from pathlib import Path

import pytest

from tests import live_llm_config
from tests.live_llm_config import load_live_llm_test_config


def test_live_llm_config_loads_allowlisted_values_without_overriding_existing(tmp_path: Path) -> None:
    config_path = tmp_path / "live-llm-test.vars"
    config_path.write_text(
        "\n".join(
            [
                "RUN_LIVE_LLM_TESTS=true",
                "GOOGLE_API_KEY=test-key-not-real",
                "IGNORED_KEY=ignored",
            ]
        ),
        encoding="utf-8",
    )
    env = {
        "POA_LIVE_LLM_TEST_CONFIG": str(config_path),
        "GOOGLE_API_KEY": "already-present",
    }

    loaded_path = load_live_llm_test_config(env)

    assert loaded_path == config_path
    assert env["RUN_LIVE_LLM_TESTS"] == "true"
    assert env["GOOGLE_API_KEY"] == "already-present"
    assert "IGNORED_KEY" not in env


def test_live_llm_config_rejects_generic_env_files(tmp_path: Path) -> None:
    config_path = tmp_path / ".env"
    config_path.write_text("GOOGLE_API_KEY=test-key-not-real", encoding="utf-8")

    with pytest.raises(RuntimeError, match="dedicated live-test config"):
        load_live_llm_test_config({"POA_LIVE_LLM_TEST_CONFIG": str(config_path)})


def test_live_llm_config_does_not_read_project_dotenv_without_live_opt_in(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dotenv = tmp_path / ".env"
    project_dotenv.write_text("GOOGLE_API_KEY=test-key-not-real", encoding="utf-8")
    monkeypatch.setattr(live_llm_config, "_PROJECT_DOTENV_PATH", project_dotenv)

    env: dict[str, str] = {}

    loaded_path = load_live_llm_test_config(env)

    assert loaded_path is None
    assert "GOOGLE_API_KEY" not in env


def test_live_llm_config_reads_only_llm_keys_from_project_dotenv_when_live_opted_in(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dotenv = tmp_path / ".env"
    project_dotenv.write_text(
        "\n".join(
            [
                "GOOGLE_API_KEY=test-google-key-not-real",
                "OPENAI_API_KEY=test-openai-key-not-real",
                "FMP_API_KEY=must-not-load",
                "DATABASE_URL=must-not-load",
                "RUN_LIVE_LLM_TESTS=false",
                "POA_LLM_PROVIDER=must-not-load",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(live_llm_config, "_PROJECT_DOTENV_PATH", project_dotenv)

    env = {"RUN_LIVE_LLM_TESTS": "true"}

    loaded_path = load_live_llm_test_config(env)

    assert loaded_path == project_dotenv
    assert env["GOOGLE_API_KEY"] == "test-google-key-not-real"
    assert env["OPENAI_API_KEY"] == "test-openai-key-not-real"
    assert env["RUN_LIVE_LLM_TESTS"] == "true"
    assert "FMP_API_KEY" not in env
    assert "DATABASE_URL" not in env
    assert "POA_LLM_PROVIDER" not in env


def test_live_llm_config_project_dotenv_does_not_override_existing_live_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dotenv = tmp_path / ".env"
    project_dotenv.write_text("GOOGLE_API_KEY=dotenv-key-not-real", encoding="utf-8")
    monkeypatch.setattr(live_llm_config, "_PROJECT_DOTENV_PATH", project_dotenv)

    env = {"RUN_LIVE_LLM_TESTS": "true", "GOOGLE_API_KEY": "process-key-not-real"}

    loaded_path = load_live_llm_test_config(env)

    assert loaded_path == project_dotenv
    assert env["GOOGLE_API_KEY"] == "process-key-not-real"
