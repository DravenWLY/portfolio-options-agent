"""Write sanitized Agent Team test report artifacts for manual inspection."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
import json
import re
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT
from app.services.agent_team.llm_clients.contracts import (
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.legacy_console.run_state import AgentReviewRunState
from app.services.reports.display_labels import (
    display_label_for_code,
    display_label_for_section,
    display_labels_for_codes,
    find_internal_display_tokens,
    replace_internal_display_tokens,
    render_display_list,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys

REPORT_ARTIFACT_DIR = PROJECT_ROOT / "reports" / "agent-team-test-results"


def write_agent_review_run_state_artifacts(
    state: AgentReviewRunState,
    *,
    label: str,
) -> tuple[Path, Path]:
    """Write a readable Markdown report plus selected JSON for a safe run state."""

    REPORT_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    file_stem = _artifact_file_stem(label=label, run_reference=state.run_reference)
    markdown_path = REPORT_ARTIFACT_DIR / f"{file_stem}.md"
    json_path = REPORT_ARTIFACT_DIR / f"{file_stem}.json"
    markdown_path.write_text(_run_state_markdown(state), encoding="utf-8")
    json_path.write_text(
        json.dumps(_jsonable(_selected_run_state_payload(state)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return markdown_path, json_path


def write_tool_mediated_saved_report_artifacts(
    readback_payload: dict[str, Any],
    *,
    label: str,
) -> tuple[Path, Path]:
    """Write a readable report from frozen saved-report readback only."""

    selected_payload = _selected_tool_mediated_readback_payload(readback_payload)
    markdown = _tool_mediated_readback_markdown(selected_payload)
    json_text = json.dumps(_jsonable(selected_payload), indent=2, sort_keys=True)
    _assert_artifact_payload_safe(markdown, json_text, selected_payload)

    REPORT_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    summary = selected_payload["agent_summary"]
    run_reference = str(summary.get("report_generated_at") or summary.get("provider_mode") or "tool-mediated")
    file_stem = _artifact_file_stem(label=label, run_reference=run_reference)
    markdown_path = REPORT_ARTIFACT_DIR / f"{file_stem}.md"
    json_path = REPORT_ARTIFACT_DIR / f"{file_stem}.json"
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json_text, encoding="utf-8")
    return markdown_path, json_path


def _artifact_file_stem(*, label: str, run_reference: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{_slug(label)}-{_slug(run_reference)[:24]}"


def _run_state_markdown(state: AgentReviewRunState) -> str:
    lines = [
        "# Agent Team Test Report",
        "",
        f"- Run reference: `{state.run_reference}`",
        f"- Generated at: `{state.generated_at.isoformat()}`",
        f"- Workflow: `{state.workflow_version}`",
        f"- Flow: `{state.review_flow_label}` (`{state.supported_flow}`)",
        f"- Status: `{state.run_status}`",
        f"- Mock output: `{state.is_mock}`",
        f"- Analysis only: `{state.analysis_only}`",
        "",
        "## Final Synthesis",
        "",
        state.final_synthesis or "_No synthesis emitted._",
        "",
        "## Agent Findings",
        "",
    ]
    if not state.role_outputs:
        lines.append("_No role outputs emitted._")
        lines.append("")
    for output in state.role_outputs:
        lines.extend(
            [
                f"### {_humanize(output.role_name)}",
                "",
                f"- Status: `{output.status}`",
                f"- Provider status: `{output.provider_status}`",
                f"- Mock output: `{output.is_mock}`",
            ]
        )
        if output.unavailable_reason:
            lines.append(f"- Unavailable reason: `{output.unavailable_reason}`")
        if output.latency_ms is not None:
            lines.append(f"- Latency: `{output.latency_ms} ms`")
        lines.extend(["", output.content_markdown or "_No role content emitted._", ""])
    lines.extend(["## Evaluation Flags", ""])
    if not state.eval_flags:
        lines.extend(["_No evaluation flags emitted._", ""])
    for flag in state.eval_flags:
        detail = f" — {flag.detail}" if flag.detail else ""
        lines.append(f"- `{flag.check}`: `{flag.status}`{detail}")
    lines.extend(["", "## Provider Warnings", ""])
    if state.provider_warnings:
        lines.extend(f"- `{warning}`" for warning in state.provider_warnings)
    else:
        lines.append("_No provider warnings emitted._")
    lines.extend(["", "## Freshness", ""])
    lines.append(f"- Broker snapshot: `{state.broker_snapshot_freshness}`")
    lines.append(f"- Market quote: `{state.market_quote_freshness}`")
    lines.append("")
    return "\n".join(lines)


def _selected_run_state_payload(state: AgentReviewRunState) -> dict[str, Any]:
    return {
        "run_reference": state.run_reference,
        "workflow_version": state.workflow_version,
        "generated_at": state.generated_at,
        "is_mock": state.is_mock,
        "analysis_only": state.analysis_only,
        "review_reference": state.review_reference,
        "supported_flow": state.supported_flow,
        "review_flow_label": state.review_flow_label,
        "review_actionability_status": state.review_actionability_status,
        "run_status": state.run_status,
        "final_synthesis": state.final_synthesis,
        "role_outputs": state.role_outputs,
        "provider_warnings": state.provider_warnings,
        "eval_flags": state.eval_flags,
        "broker_snapshot_freshness": state.broker_snapshot_freshness,
        "market_quote_freshness": state.market_quote_freshness,
        "deterministic_evidence_summary": state.deterministic_evidence_summary,
        "scope_summary": state.scope_summary,
    }


def _selected_tool_mediated_readback_payload(readback_payload: dict[str, Any]) -> dict[str, Any]:
    summary = _require_mapping(readback_payload.get("agent_summary"), "agent_summary")
    artifact = _require_mapping(summary.get("tool_run_artifact"), "agent_summary.tool_run_artifact")
    provider_runs = tuple(_selected_provider_run(run) for run in _as_tuple(artifact.get("provider_runs")))
    role_findings = tuple(_selected_role_findings(item) for item in _as_tuple(artifact.get("audited_findings")))
    gap_sections = _evidence_gap_sections(artifact)
    return {
        "agent_summary": {
            "report_status": summary.get("report_status"),
            "run_status": summary.get("run_status"),
            "provider_mode": summary.get("provider_mode"),
            "report_generated_at": summary.get("report_generated_at"),
            "warning_codes": tuple(summary.get("warning_codes") or ()),
            "final_synthesis_markdown": summary.get("final_synthesis_markdown"),
        },
        "provider_runs": provider_runs,
        "role_findings": role_findings,
        "warning_codes": tuple(dict.fromkeys((*_as_tuple(summary.get("warning_codes")), *_as_tuple(artifact.get("warning_codes"))))),
        "open_questions": tuple(artifact.get("open_questions") or ()),
        "evidence_gap_sections": gap_sections,
    }


def _selected_provider_run(run: object) -> dict[str, Any]:
    item = _require_mapping(run, "provider_run")
    return {
        "role_name": item.get("role_name"),
        "model": item.get("model"),
        "model_chain_position": item.get("model_chain_position"),
        "attempted_models": tuple(item.get("attempted_models") or ()),
        "status": item.get("status"),
        "prompt_version": item.get("prompt_version"),
        "is_mock": item.get("is_mock"),
    }


def _selected_role_findings(finding_set: object) -> dict[str, Any]:
    item = _require_mapping(finding_set, "audited_finding")
    return {
        "role_name": item.get("role_name"),
        "role_status": item.get("role_status"),
        "warning_codes": tuple(item.get("warning_codes") or ()),
        "live_report_markdown": item.get("live_report_markdown"),
        "findings": tuple(_selected_finding(finding) for finding in _as_tuple(item.get("findings"))),
    }


def _selected_finding(finding: object) -> dict[str, Any]:
    item = _require_mapping(finding, "finding")
    return {
        "finding_type": item.get("finding_type"),
        "claim_text": item.get("claim_text"),
        "evidence_refs": tuple(item.get("evidence_refs") or ()),
        "caveat_codes": tuple(item.get("caveat_codes") or ()),
    }


def _evidence_gap_sections(artifact: dict[str, Any]) -> tuple[str, ...]:
    gaps: list[str] = []
    for result in _as_tuple(artifact.get("tool_results")):
        item = _require_mapping(result, "tool_result")
        if item.get("tool_name") != "evidence_gap_inspector":
            continue
        payload = _require_mapping(item.get("summary_payload"), "tool_result.summary_payload")
        gaps.extend(str(ref) for ref in _as_tuple(payload.get("unavailable_evidence_refs")))
    return tuple(dict.fromkeys(gaps))


def _tool_mediated_readback_markdown(selected: dict[str, Any]) -> str:
    summary = _require_mapping(selected.get("agent_summary"), "selected.agent_summary")
    lines = [
        "# Tool-Mediated Saved Agent Team Report",
        "",
        "## Header",
        "",
        f"- Report status: {display_label_for_code(summary.get('report_status'))}",
        f"- Run status: {display_label_for_code(summary.get('run_status'))}",
        f"- Provider mode: {display_label_for_code(summary.get('provider_mode'))}",
        f"- Generated at: `{summary.get('report_generated_at')}`",
        "",
        "## Provider Runs",
        "",
    ]
    provider_runs = _as_tuple(selected.get("provider_runs"))
    if not provider_runs:
        lines.extend(["_No provider runs were frozen._", ""])
    for run in provider_runs:
        item = _require_mapping(run, "selected.provider_run")
        lines.extend(
            [
                f"### {_humanize(str(item.get('role_name') or 'unknown_role'))}",
                "",
                f"- Model: `{item.get('model')}`",
                f"- Model chain position: `{item.get('model_chain_position')}`",
                f"- Attempted models: `{', '.join(str(model) for model in _as_tuple(item.get('attempted_models'))) or 'none'}`",
                f"- Status: {display_label_for_code(item.get('status'))}",
                f"- Prompt version: `{item.get('prompt_version')}`",
                f"- Mock: `{item.get('is_mock')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Portfolio Manager Synthesis",
            "",
            replace_internal_display_tokens(str(summary.get("final_synthesis_markdown") or "")) or "_No synthesis emitted._",
            "",
            "## Per-Role Findings",
            "",
        ]
    )
    for role in _as_tuple(selected.get("role_findings")):
        item = _require_mapping(role, "selected.role_findings")
        lines.extend([f"### {_humanize(str(item.get('role_name') or 'unknown_role'))}", ""])
        lines.append(f"- Role status: {display_label_for_code(item.get('role_status'))}")
        lines.append(f"- Warnings: {render_display_list(display_labels_for_codes(_as_tuple(item.get('warning_codes'))).labels)}")
        if item.get("live_report_markdown"):
            lines.extend(
                [
                    "",
                    "#### Live Report",
                    "",
                    replace_internal_display_tokens(str(item.get("live_report_markdown"))) or "",
                    "",
                ]
            )
        for finding in _as_tuple(item.get("findings")):
            finding_item = _require_mapping(finding, "selected.finding")
            lines.extend(
                [
                    "",
                    f"- Category: {display_label_for_code(finding_item.get('finding_type'))}",
                    f"- Claim: {replace_internal_display_tokens(str(finding_item.get('claim_text') or '')) or '_No claim text._'}",
                    f"- Evidence: {render_display_list(display_label_for_section(str(ref)) for ref in _as_tuple(finding_item.get('evidence_refs')))}",
                    f"- Caveats: {render_display_list(display_labels_for_codes(_as_tuple(finding_item.get('caveat_codes'))).labels)}",
                ]
            )
        lines.append("")
    lines.extend(["## Warning Codes", ""])
    warnings = _as_tuple(selected.get("warning_codes"))
    lines.extend(f"- {label}" for label in display_labels_for_codes(warnings).labels)
    if not warnings:
        lines.append("_No warning codes emitted._")
    lines.extend(["", "## Open Questions", ""])
    questions = _as_tuple(selected.get("open_questions"))
    lines.extend(f"- {question}" for question in questions)
    if not questions:
        lines.append("_No open questions emitted._")
    lines.extend(["", "## Evidence Gap Sections", ""])
    gaps = _as_tuple(selected.get("evidence_gap_sections"))
    lines.extend(f"- {display_label_for_section(str(gap))}" for gap in gaps)
    if not gaps:
        lines.append("_No evidence gaps emitted._")
    lines.append("")
    return "\n".join(lines)


def _assert_artifact_payload_safe(markdown: str, json_text: str, selected_payload: dict[str, Any]) -> None:
    for label, value in (
        ("markdown artifact", markdown),
        ("json artifact text", json_text),
        ("selected artifact payload", selected_payload),
    ):
        secret_values = find_secret_like_values(value)
        forbidden_keys = find_forbidden_keys(value, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
        prohibited_phrases = find_prohibited_llm_phrases(value)
        if secret_values or forbidden_keys or prohibited_phrases:
            raise ValueError(
                f"{label} failed safety sweep: "
                f"secret_values={sorted(secret_values)}, "
                f"forbidden_keys={sorted(forbidden_keys)}, "
                f"prohibited_phrases={sorted(prohibited_phrases)}"
            )
    display_tokens = find_internal_display_tokens(markdown)
    if display_tokens:
        raise ValueError(f"markdown artifact contains internal display tokens: {sorted(display_tokens)}")


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _as_tuple(value: object) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-").lower()
    return text or "agent-team-report"


def _humanize(value: str) -> str:
    return value.replace("_", " ").title()
