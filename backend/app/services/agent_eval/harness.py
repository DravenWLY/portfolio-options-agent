"""Reusable agent evaluation harness (P25A-T2).

Aggregates the individual checks into an ``EvalReport``. Used both by tests and
by ``ReviewRunner`` at runtime to populate ``AgentReviewRunState.eval_flags``.

Import-safe, network-free, no LLM/provider calls. Inputs are primitives
(role-name/text pairs, plain dict summaries, boolean observations), so the
harness has no dependency on the agent-team run-state types.
"""

from collections.abc import Mapping, Sequence

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
