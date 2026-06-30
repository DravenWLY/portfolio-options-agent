"""Reusable agent evaluation harness (P25A-T2).

Aggregates the individual checks into an ``EvalReport``. Used both by tests and
by ``ReviewRunner`` at runtime to populate ``AgentReviewRunState.eval_flags``.

Import-safe, network-free, no LLM/provider calls. Inputs are primitives
(role-name/text pairs, plain dict summaries, boolean observations), so the
harness has no dependency on the agent-team run-state types.
"""

from collections.abc import Mapping, Sequence
from collections.abc import Callable

from app.services.agent_eval.checks import (
    check_evidence_consistency,
    check_evidence_faithfulness,
    check_forbidden_wording,
    check_generated_output_safety,
    check_prompt_privacy_keys,
    check_prompt_privacy_values,
    check_role_boundaries,
    classify_failures,
)
from app.services.agent_eval.results import EvalFinding, EvalReport
from app.services.agent_eval.tool_mediated_checks import (
    check_artifact_present_for_full_report,
    check_blocked_draft_has_no_artifact,
    check_byte_stable_regeneration,
    check_citation_graph_closure,
    check_contradictions_are_open_questions,
    check_discovery_delta,
    check_discovery_non_regression,
    check_gaps_not_cited,
    check_hard_blocks_failed_closed,
    check_legacy_summary_valid,
    check_missing_context_surfaced,
    check_repass_bounded,
    check_role_citations_within_boundary,
    check_synthesis_cites_audited_only,
    evaluate_tool_mediated_safety_net,
)
from app.schemas.reports import SavedAgentTeamSummaryRead


def _generated_payload(
    role_texts: Sequence[tuple[str, str | None]],
    final_synthesis: str | None,
) -> dict[str, object]:
    return {
        "role_texts": [
            {"role_name": role_name, "content": content} for role_name, content in role_texts
        ],
        "final_synthesis": final_synthesis,
    }


def evaluate_generated_output(
    *,
    role_texts: Sequence[tuple[str, str | None]] = (),
    final_synthesis: str | None = None,
) -> tuple[EvalFinding, ...]:
    """Run the generated-output safety + faithfulness + privacy checks."""

    payload = _generated_payload(role_texts, final_synthesis)
    wording = check_forbidden_wording(payload)
    faithfulness = check_evidence_faithfulness(payload)
    privacy_keys = check_prompt_privacy_keys(payload)
    privacy_values = check_prompt_privacy_values(payload)
    composite = check_generated_output_safety(
        wording=wording,
        faithfulness=faithfulness,
        privacy_keys=privacy_keys,
        privacy_values=privacy_values,
    )
    return (composite, wording, faithfulness, privacy_keys, privacy_values)


def evaluate_agent_review_run(
    *,
    role_texts: Sequence[tuple[str, str | None]] = (),
    final_synthesis: str | None = None,
    run_summary: Mapping[str, object] | None = None,
    expected_summary: Mapping[str, object] | None = None,
    role_boundary_observations: Sequence[tuple[str, bool, bool]] = (),
    provider_warnings: Sequence[str] = (),
) -> EvalReport:
    """Full run evaluation. Returns an ``EvalReport`` of safe findings."""

    findings: list[EvalFinding] = list(
        evaluate_generated_output(role_texts=role_texts, final_synthesis=final_synthesis)
    )
    findings.append(check_role_boundaries(role_boundary_observations))
    findings.append(check_evidence_consistency(run_summary, expected_summary))
    findings.append(classify_failures(provider_warnings))
    return EvalReport(findings=tuple(findings))


def evaluate_tool_mediated_report(
    summary: SavedAgentTeamSummaryRead,
    *,
    baseline_summary: SavedAgentTeamSummaryRead | None = None,
    rebuild: Callable[[], SavedAgentTeamSummaryRead] | None = None,
) -> EvalReport:
    """Evaluate a frozen tool-mediated saved report without recomputing sources."""

    findings: list[EvalFinding] = [
        check_discovery_non_regression(summary, baseline_summary),
        check_discovery_delta(summary, baseline_summary),
        check_gaps_not_cited(summary),
        check_missing_context_surfaced(summary),
        check_role_citations_within_boundary(summary),
        check_citation_graph_closure(summary),
        check_synthesis_cites_audited_only(summary),
        check_contradictions_are_open_questions(summary),
        check_repass_bounded(summary),
        check_hard_blocks_failed_closed(summary),
        *evaluate_tool_mediated_safety_net(summary),
        check_artifact_present_for_full_report(summary),
        check_blocked_draft_has_no_artifact(summary),
        check_byte_stable_regeneration(summary, rebuild),
        check_legacy_summary_valid(summary),
    ]
    return EvalReport(findings=tuple(findings))
