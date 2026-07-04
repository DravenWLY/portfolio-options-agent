"""Write sanitized Agent Team test report artifacts for manual inspection."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
import json
import re
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT
from app.services.agent_team.run_state import AgentReviewRunState

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
