from pathlib import Path

import pytest

from tests.live_llm_config import load_live_llm_test_config


def test_live_llm_config_loads_allowlisted_values_without_overriding_existing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.local.live-llm.env"
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
