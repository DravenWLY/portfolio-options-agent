from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from app.services.agent_team.llm_clients.contracts import (
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.tool_mediated_report import build_tool_mediated_agent_team_summary
from app.services.reports.display_labels import find_internal_display_tokens
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from tests import agent_team_report_artifacts as artifacts
from tests.services.agent_team.test_tools import _evidence_package


pytestmark = [pytest.mark.unit]


def test_tool_mediated_saved_report_export_writes_selected_clean_readback_fields(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    readback_payload = {
        "id": "thread_should_not_be_exported",
        "title": "Readback title should not be exported",
        "scope_metadata": {"provider_account_id": "provider_account_id_should_not_be_seen"},
        "agent_summary": summary.model_dump(mode="json"),
    }
    monkeypatch.setattr(artifacts, "REPORT_ARTIFACT_DIR", tmp_path)

    markdown_path, json_path = artifacts.write_tool_mediated_saved_report_artifacts(
        readback_payload,
        label="offline-mock-readback",
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    selected_json_text = json_path.read_text(encoding="utf-8")
    selected_payload = json.loads(selected_json_text)
    assert markdown_path.parent == tmp_path
    assert json_path.parent == tmp_path
    for section in (
        "# Tool-Mediated Saved Agent Team Report",
        "## Header",
        "## Provider Runs",
        "## Portfolio Manager Synthesis",
        "## Per-Role Findings",
        "## Warning Codes",
        "## Open Questions",
        "## Evidence Gap Sections",
    ):
        assert section in markdown
    assert set(selected_payload) == {
        "agent_summary",
        "evidence_gap_sections",
        "open_questions",
        "provider_runs",
        "role_findings",
        "warning_codes",
    }
    assert "thread_should_not_be_exported" not in markdown
    assert "thread_should_not_be_exported" not in selected_json_text
    assert "provider_account_id_should_not_be_seen" not in markdown
    assert "provider_account_id_should_not_be_seen" not in selected_json_text

    for payload in (markdown, selected_json_text, selected_payload):
        assert not find_secret_like_values(payload)
        assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
        assert not find_prohibited_llm_phrases(payload)
    assert not find_internal_display_tokens(markdown)


def test_tool_mediated_saved_report_export_raises_before_writing_unsafe_artifacts(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    readback_payload = {"agent_summary": summary.model_dump(mode="json")}
    readback_payload["agent_summary"]["tool_run_artifact"]["audited_findings"][0]["findings"][0][
        "claim_text"
    ] = "You should buy this immediately."
    monkeypatch.setattr(artifacts, "REPORT_ARTIFACT_DIR", tmp_path)

    with pytest.raises(ValueError, match="failed safety sweep"):
        artifacts.write_tool_mediated_saved_report_artifacts(
            readback_payload,
            label="unsafe-readback",
        )

    assert not list(tmp_path.iterdir())
