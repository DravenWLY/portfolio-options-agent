from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.services.agent_team.safety.report_output_safety import CANONICAL_EVIDENCE_KEYS
from app.services.agent_team.tool_mediated_report import build_tool_mediated_agent_team_summary
from app.services.agent_team.tools.envelopes import TOOL_AVAILABILITIES, TOOL_DATA_MODES, TOOL_STATUSES
from app.services.reports.agent_team_report import build_validation_failed_summary_for_test
from app.services.reports.display_labels import (
    FRESHNESS_DISPLAY_LABELS,
    display_label_for_code,
    find_internal_display_tokens,
    missing_display_labels_for_tokens,
    reviewed_display_tokens,
)
from tests.services.agent_team.test_tools import _evidence_package


pytestmark = [pytest.mark.unit]


def test_display_label_map_covers_current_report_vocabularies() -> None:
    tokens = frozenset((*CANONICAL_EVIDENCE_KEYS, *TOOL_AVAILABILITIES, *TOOL_STATUSES, *TOOL_DATA_MODES))

    assert not missing_display_labels_for_tokens(tokens)
    assert "selected_context_scope" in reviewed_display_tokens()
    assert display_label_for_code("selected_context_scope") == "scope is limited to the selected portfolio context"
    assert display_label_for_code("funding_shortfall_detected") == (
        "reviewed cash snapshot did not cover the proposed purchase"
    )
    assert display_label_for_code("position_market_value_unavailable") == (
        "some reviewed position values were unavailable"
    )
    assert display_label_for_code("account_snapshot_unavailable") == (
        "the selected account's synced snapshot was unavailable, so exposure impact was not computed"
    )
    assert display_label_for_code("instrument_type_reconciled") == (
        "the submitted instrument type was reconciled with the reviewed symbol directory"
    )
    assert display_label_for_code("money_market_core_treated_as_cash") == (
        "a money market core position was treated as cash"
    )
    assert display_label_for_code("atr14_usd") == "ATR fourteen"
    assert display_label_for_code("unknown_future_code") == "Unlabeled review detail."


def test_freshness_display_labels_cover_manual_and_market_context_statuses() -> None:
    expected = {"cached", "delayed", "eod_only", "error", "fresh", "manual", "stale", "unavailable", "unknown"}

    assert expected.issubset(FRESHNESS_DISPLAY_LABELS)
    assert display_label_for_code("manual") == "manually entered"


def test_tool_mediated_mock_summary_visible_prose_has_no_internal_display_tokens() -> None:
    summary = build_tool_mediated_agent_team_summary(
        _evidence_package(),
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    prose_values: list[str] = [summary.final_synthesis_markdown or ""]
    for role in summary.role_summaries:
        prose_values.append(role.summary_markdown or "")
        prose_values.append(role.live_report_markdown or "")
    assert not find_internal_display_tokens(" ".join(prose_values))

    assert summary.tool_run_artifact is not None
    frozen_claims = tuple(
        finding.claim_text
        for finding_set in summary.tool_run_artifact.audited_findings
        for finding in finding_set.findings
    )
    assert not find_internal_display_tokens(" ".join(frozen_claims))


def test_display_token_validator_fails_closed_with_eval_flag() -> None:
    evidence = _evidence_package()
    unsafe_payload = {
        "run_status": "completed",
        "provider_mode": "tool_mediated_mock",
        "report_generated_at": datetime(2026, 6, 1, tzinfo=UTC),
        "role_summaries": (),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "selected_context_scope leaked into visible prose.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": evidence.evidence_schema_version,
        "evidence_references": (),
    }

    summary = build_validation_failed_summary_for_test(
        evidence,
        unsafe_payload,
        report_generated_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    assert summary.report_status == "validation_failed"
    assert "display_token_blocked" in summary.warning_codes
