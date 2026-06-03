"""Reusable, app-owned agent evaluation harness (P25A-T2).

Import-safe, network-free, synthetic-driven. No LLM/provider/tool calls. Exposes
safe findings suitable for ``AgentReviewRunState.eval_flags``.
"""

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
from app.services.agent_eval.harness import evaluate_agent_review_run, evaluate_generated_output
from app.services.agent_eval.results import EvalFinding, EvalReport

__all__ = [
    "EvalFinding",
    "EvalReport",
    "evaluate_agent_review_run",
    "evaluate_generated_output",
    "check_forbidden_wording",
    "check_evidence_faithfulness",
    "check_prompt_privacy_keys",
    "check_prompt_privacy_values",
    "check_generated_output_safety",
    "check_role_boundaries",
    "check_evidence_consistency",
    "classify_failures",
]
