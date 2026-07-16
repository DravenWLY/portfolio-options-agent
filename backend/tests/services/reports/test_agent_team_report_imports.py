"""Cold-import coverage for the saved Agent Team report service."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_report_generation_mode_resolver_cold_imports_without_app_main() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; "
            "assert 'app.main' not in sys.modules; "
            "from app.services.reports.agent_team_report import "
            "resolve_backend_agent_team_report_generation_mode; "
            "assert 'app.main' not in sys.modules; "
            "assert resolve_backend_agent_team_report_generation_mode({}) == 'deterministic_template'",
        ],
        cwd=BACKEND_ROOT,
        env={"POA_DOTENV_DISABLED": "1", "PYTHONPATH": str(BACKEND_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_safety_package_keeps_report_validator_reexport() -> None:
    from app.services.agent_team.safety import validate_agent_team_report_output
    from app.services.agent_team.safety.report_output_safety import (
        validate_agent_team_report_output as direct_validator,
    )

    assert validate_agent_team_report_output is direct_validator
