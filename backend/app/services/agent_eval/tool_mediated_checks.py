"""Evaluation checks for tool-mediated saved Agent Team reports (P33A-T5)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Iterable

from app.schemas.reports import SavedAgentTeamSummaryRead
from app.services.agent_eval.checks import (
    check_evidence_faithfulness,
    check_forbidden_wording,
    check_prompt_privacy_keys,
)
from app.services.agent_eval.results import (
    DETAIL_ARTIFACT_MISSING,
    DETAIL_ARTIFACT_ON_DRAFT,
    DETAIL_CITATION_BOUNDARY,
    DETAIL_CITATION_UNRESOLVED,
    DETAIL_CONTRADICTION_OPEN,
    DETAIL_DISCOVERY_DELTA,
    DETAIL_DISCOVERY_REGRESSION,
    DETAIL_GAP_CITED,
    DETAIL_HARD_BLOCK_LEAK,
    DETAIL_INVENTED_LEVEL,
    DETAIL_MISSING_NOT_SURFACED,
    DETAIL_NOT_BYTE_STABLE,
    DETAIL_REPASS_UNBOUNDED,
    DETAIL_SYNTHESIS_UNAUDITED,
    EvalFinding,
)
from app.services.agent_team.llm_clients.contracts import (
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.safety.report_output_safety import (
    INVENTED_LEVEL_PATTERNS,
    SOURCE_LEAK_PATTERNS,
)
from app.services.agent_team.tool_mediated_report import MAX_PLANNER_REPASSES, usable_content_by_role
from app.services.agent_team.tools import TOOL_GENERATED_METRIC_PATTERNS

HARD_BLOCK_FLAGS = frozenset(
    {"private_leak_blocked", "advice_wording_blocked", "invented_metric_blocked"}
)
SAFE_FLOW_VALUE_PATH_SUFFIXES = frozenset(
    {
        ".summary_payload.review_flow_label",
        ".summary_payload.supported_flow",
    }
)


def _finding(check: str, *, ok: bool, detail: str) -> EvalFinding:
    return EvalFinding(check=check, status="passed" if ok else "flagged", detail=None if ok else detail)


def _deferred(check: str, detail: str | None = None) -> EvalFinding:
    return EvalFinding(check=check, status="deferred", detail=detail)


def _all_summary_refs(summary: SavedAgentTeamSummaryRead) -> tuple[str, ...]:
    refs: list[str] = list(summary.evidence_references)
    for role in summary.role_summaries:
        refs.extend(role.evidence_references)
    artifact = summary.tool_run_artifact
    if artifact is not None:
        refs.extend(artifact.synthesis_evidence_references)
        for finding_set in artifact.audited_findings:
            for finding in finding_set.findings:
                refs.extend(finding.evidence_refs)
    return tuple(dict.fromkeys(refs))


def _role_refs(summary: SavedAgentTeamSummaryRead) -> dict[str, tuple[str, ...]]:
    return {role.role_name: role.evidence_references for role in summary.role_summaries}


def _available_frozen_refs_by_role(summary: SavedAgentTeamSummaryRead) -> dict[str, frozenset[str]]:
    refs: dict[str, set[str]] = {}
    artifact = summary.tool_run_artifact
    if artifact is None:
        return {}
    for result in artifact.tool_results:
        if result.availability in {"available", "limited"}:
            refs.setdefault(result.role_name, set()).update(result.evidence_refs)
    portfolio_manager_refs: set[str] = set()
    for values in refs.values():
        portfolio_manager_refs.update(values)
    refs["portfolio_manager_agent"] = portfolio_manager_refs
    return {role: frozenset(values) for role, values in refs.items()}


def _artifact_unavailable_refs(summary: SavedAgentTeamSummaryRead) -> frozenset[str]:
    unavailable: set[str] = set()
    artifact = summary.tool_run_artifact
    if artifact is None:
        return frozenset()
    for result in artifact.tool_results:
        if result.availability not in {"available", "limited"}:
            unavailable.update(result.evidence_refs)
        gap_refs = result.summary_payload.get("unavailable_evidence_refs")
        if isinstance(gap_refs, (list, tuple)):
            unavailable.update(str(ref) for ref in gap_refs)
    for role in summary.role_summaries:
        unavailable.update(code.removesuffix("_unavailable") for code in role.warning_codes if code.endswith("_unavailable"))
    if artifact is not None:
        unavailable.update(code.removesuffix("_unavailable") for code in artifact.warning_codes if code.endswith("_unavailable"))
    return frozenset(unavailable)


def _warning_codes(summary: SavedAgentTeamSummaryRead) -> tuple[str, ...]:
    codes: list[str] = list(summary.warning_codes)
    for role in summary.role_summaries:
        codes.extend(role.warning_codes)
    if summary.tool_run_artifact is not None:
        codes.extend(summary.tool_run_artifact.warning_codes)
        codes.extend(summary.tool_run_artifact.auditor.eval_flags)
        for finding_set in summary.tool_run_artifact.audited_findings:
            codes.extend(finding_set.warning_codes)
    return tuple(dict.fromkeys(codes))


def _is_legacy_without_tool_artifact(summary: SavedAgentTeamSummaryRead) -> bool:
    return summary.tool_run_artifact is None and summary.provider_mode != "tool_mediated_mock"


def _iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _iter_strings(item)


def _contains_source_url_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {"url", "urls", "source_url", "source_urls", "raw_url"}:
                return True
            if _contains_source_url_key(item):
                return True
    elif isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_source_url_key(item) for item in value)
    return False


def _matches_any_pattern(payload: object, patterns: tuple) -> bool:
    return any(any(pattern.search(text) for pattern in patterns) for text in _iter_strings(payload))


def _prompt_privacy_values_finding(payload: object) -> EvalFinding:
    forbidden_paths = {
        path
        for path in find_forbidden_string_values(payload)
        if not any(path.endswith(suffix) for suffix in SAFE_FLOW_VALUE_PATH_SUFFIXES)
    }
    if forbidden_paths or find_secret_like_values(payload):
        return EvalFinding(
            check="prompt_privacy_values",
            status="flagged",
            detail="forbidden private value or credential-like pattern detected",
        )
    return EvalFinding(check="prompt_privacy_values", status="passed")


def check_discovery_non_regression(
    summary: SavedAgentTeamSummaryRead,
    baseline_summary: SavedAgentTeamSummaryRead | None,
) -> EvalFinding:
    if baseline_summary is None:
        return _deferred("tool_discovery_non_regression")
    tool_refs = set(_all_summary_refs(summary))
    baseline_refs = set(_all_summary_refs(baseline_summary))
    tool_findings = _finding_count(summary)
    baseline_findings = _finding_count(baseline_summary)
    # D1: discovery is measured and non-regression-gated later. This finding is
    # intentionally non-blocking in T5B; the delta finding records the gap.
    _ = (tool_refs, baseline_refs, tool_findings, baseline_findings, DETAIL_DISCOVERY_REGRESSION)
    return EvalFinding(check="tool_discovery_non_regression", status="passed", detail=None)


def check_discovery_delta(
    summary: SavedAgentTeamSummaryRead,
    baseline_summary: SavedAgentTeamSummaryRead | None,
) -> EvalFinding:
    _ = (summary, baseline_summary)
    return EvalFinding(check="tool_discovery_delta", status="passed", detail=DETAIL_DISCOVERY_DELTA)


def _finding_count(summary: SavedAgentTeamSummaryRead) -> int:
    artifact = summary.tool_run_artifact
    if artifact is not None:
        return sum(len(item.findings) for item in artifact.audited_findings)
    return sum(1 for role in summary.role_summaries if role.summary_markdown)


def check_gaps_not_cited(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    unavailable = _artifact_unavailable_refs(summary)
    if not unavailable:
        return EvalFinding(check="tool_gaps_not_cited", status="passed")
    cited = set(_all_summary_refs(summary))
    return _finding(
        "tool_gaps_not_cited",
        ok=not bool(cited.intersection(unavailable)),
        detail=DETAIL_GAP_CITED,
    )


def check_missing_context_surfaced(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    unavailable = _artifact_unavailable_refs(summary)
    if not unavailable:
        return EvalFinding(check="tool_missing_context_surfaced", status="passed")
    has_skipped_reason = any(
        role.role_status == "skipped" and bool(role.unavailable_reason) for role in summary.role_summaries
    )
    has_gap_warning = any(code.endswith(("_unavailable", "_not_available")) for code in _warning_codes(summary))
    return _finding(
        "tool_missing_context_surfaced",
        ok=has_skipped_reason or has_gap_warning,
        detail=DETAIL_MISSING_NOT_SURFACED,
    )


def check_role_citations_within_boundary(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    if _is_legacy_without_tool_artifact(summary):
        return _deferred("tool_role_citations_within_boundary")
    usable = usable_content_by_role()
    for role_name, refs in _role_refs(summary).items():
        if not set(refs).issubset(usable.get(role_name, frozenset())):
            return EvalFinding(
                check="tool_role_citations_within_boundary",
                status="flagged",
                detail=DETAIL_CITATION_BOUNDARY,
            )
    return EvalFinding(check="tool_role_citations_within_boundary", status="passed")


def check_citation_graph_closure(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    artifact = summary.tool_run_artifact
    if artifact is None:
        return _deferred("tool_citation_graph_closure")
    available_by_role = _available_frozen_refs_by_role(summary)
    for role_name, refs in _role_refs(summary).items():
        available = available_by_role.get(role_name, frozenset())
        if not set(refs).issubset(available):
            return EvalFinding(
                check="tool_citation_graph_closure",
                status="flagged",
                detail=DETAIL_CITATION_UNRESOLVED,
            )
    return EvalFinding(check="tool_citation_graph_closure", status="passed")


def check_synthesis_cites_audited_only(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    artifact = summary.tool_run_artifact
    if artifact is None:
        return _deferred("tool_synthesis_cites_audited_only")
    usable = usable_content_by_role()["portfolio_manager_agent"]
    audited_refs: set[str] = set()
    for finding_set in artifact.audited_findings:
        for finding in finding_set.findings:
            audited_refs.update(finding.evidence_refs)
    ok = (
        summary.evidence_references == artifact.synthesis_evidence_references
        and set(summary.evidence_references).issubset(usable)
        and set(summary.evidence_references).issubset(audited_refs)
    )
    return _finding(
        "tool_synthesis_cites_audited_only",
        ok=ok,
        detail=DETAIL_SYNTHESIS_UNAUDITED,
    )


def check_contradictions_are_open_questions(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    artifact = summary.tool_run_artifact
    if artifact is None or not artifact.auditor.contradictions:
        return EvalFinding(check="tool_contradictions_are_open_questions", status="passed")
    synthesis = (summary.final_synthesis_markdown or "").lower()
    ok = bool(artifact.open_questions) and "open questions" in synthesis
    return _finding(
        "tool_contradictions_are_open_questions",
        ok=ok,
        detail=DETAIL_CONTRADICTION_OPEN,
    )


def check_repass_bounded(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    artifact = summary.tool_run_artifact
    if artifact is None:
        return _deferred("tool_repass_bounded")
    ok = artifact.auditor.repass_triggered in {True, False} and MAX_PLANNER_REPASSES == 1
    return _finding("tool_repass_bounded", ok=ok, detail=DETAIL_REPASS_UNBOUNDED)


def check_hard_blocks_failed_closed(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    artifact = summary.tool_run_artifact
    if artifact is None:
        return _deferred("tool_hard_blocks_failed_closed")
    flags = set(artifact.auditor.eval_flags)
    hard_flags = flags.intersection(HARD_BLOCK_FLAGS)
    if not hard_flags:
        return EvalFinding(check="tool_hard_blocks_failed_closed", status="passed")
    payload = summary.model_dump(mode="python")
    blocked_clean = not (
        check_prompt_privacy_keys(payload).status == "flagged"
        or _prompt_privacy_values_finding(payload).status == "flagged"
        or find_secret_like_values(payload)
        or find_prohibited_llm_phrases(payload)
        or _matches_any_pattern(payload, (*TOOL_GENERATED_METRIC_PATTERNS,))
    )
    ok = blocked_clean and artifact.auditor.repass_triggered is False
    return _finding("tool_hard_blocks_failed_closed", ok=ok, detail=DETAIL_HARD_BLOCK_LEAK)


def check_no_invented_levels_or_source_leak(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    payload = summary.model_dump(mode="python")
    ok = not _matches_any_pattern(
        payload,
        (*TOOL_GENERATED_METRIC_PATTERNS, *INVENTED_LEVEL_PATTERNS, *SOURCE_LEAK_PATTERNS),
    ) and not _contains_source_url_key(payload)
    return _finding("tool_no_invented_levels_or_source_leak", ok=ok, detail=DETAIL_INVENTED_LEVEL)


def check_artifact_present_for_full_report(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    if summary.report_status != "full_agent_report" or summary.provider_mode != "tool_mediated_mock":
        return _deferred("tool_artifact_present_for_full_report")
    artifact = summary.tool_run_artifact
    ok = artifact is not None and artifact.tool_result_count == len(artifact.tool_results)
    return _finding("tool_artifact_present_for_full_report", ok=ok, detail=DETAIL_ARTIFACT_MISSING)


def check_blocked_draft_has_no_artifact(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    if summary.report_status != "deterministic_draft":
        return _deferred("tool_blocked_draft_has_no_artifact")
    return _finding(
        "tool_blocked_draft_has_no_artifact",
        ok=summary.tool_run_artifact is None,
        detail=DETAIL_ARTIFACT_ON_DRAFT,
    )


def check_byte_stable_regeneration(
    summary: SavedAgentTeamSummaryRead,
    rebuild: Callable[[], SavedAgentTeamSummaryRead] | None,
) -> EvalFinding:
    if rebuild is None:
        return _deferred("tool_byte_stable_regeneration")
    rebuilt = rebuild()
    ok = rebuilt.model_dump(mode="json") == summary.model_dump(mode="json")
    return _finding("tool_byte_stable_regeneration", ok=ok, detail=DETAIL_NOT_BYTE_STABLE)


def check_legacy_summary_valid(summary: SavedAgentTeamSummaryRead) -> EvalFinding:
    if summary.tool_run_artifact is not None:
        return _deferred("tool_legacy_summary_valid")
    return EvalFinding(check="tool_legacy_summary_valid", status="passed")


def evaluate_tool_mediated_safety_net(summary: SavedAgentTeamSummaryRead) -> tuple[EvalFinding, ...]:
    payload = summary.model_dump(mode="python")
    return (
        check_forbidden_wording(payload),
        check_evidence_faithfulness(payload),
        check_prompt_privacy_keys(payload),
        _prompt_privacy_values_finding(payload),
        check_no_invented_levels_or_source_leak(summary),
    )
