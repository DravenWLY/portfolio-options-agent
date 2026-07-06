"""Individual evaluation checks for the reusable agent eval harness (P25A-T2).

Each check is pure, import-safe, network-free, and synthetic-driven. Checks
reuse the existing safety detectors (output safety, provider payload safety,
privacy) rather than reinventing them, so the harness and the runtime
validators stay in agreement. Findings carry only fixed, safe detail strings.
"""

from collections.abc import Iterable, Mapping, Sequence

from app.services.agent_eval.results import (
    DETAIL_CLEAN_RUN,
    DETAIL_EVIDENCE_DIVERGED,
    DETAIL_FORBIDDEN_WORDING,
    DETAIL_NO_PROJECTION,
    DETAIL_OUTPUT_SAFETY,
    DETAIL_PARTIAL_RUN,
    DETAIL_PRIVACY_KEY,
    DETAIL_PRIVACY_VALUE,
    DETAIL_ROLE_BOUNDARY,
    DETAIL_UNGROUNDED_FIGURE,
    EvalFinding,
)
from app.services.agent_team.llm_clients.contracts import (
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.safety.output_safety import GENERATED_METRIC_PATTERNS
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


def _iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _iter_strings(item)


def _matches_any_pattern(payload: object, patterns: Sequence) -> bool:
    return any(any(pattern.search(text) for pattern in patterns) for text in _iter_strings(payload))


def _finding(check: str, *, ok: bool, detail: str) -> EvalFinding:
    return EvalFinding(check=check, status="passed" if ok else "flagged", detail=None if ok else detail)


def check_forbidden_wording(generated: object) -> EvalFinding:
    """Flag advice / execution / guarantee / readiness phrasing in generated text."""

    ok = not find_prohibited_llm_phrases(generated)
    return _finding("forbidden_wording", ok=ok, detail=DETAIL_FORBIDDEN_WORDING)


def check_evidence_faithfulness(generated: object) -> EvalFinding:
    """Flag ungrounded numeric figures (invented metrics) in generated commentary.

    In this product all numbers belong to the deterministic layer and are
    rendered separately; agent commentary must contain no figures. So any metric
    pattern in generated text is an ungrounded/invented figure.
    """

    ok = not _matches_any_pattern(generated, GENERATED_METRIC_PATTERNS)
    return _finding("evidence_faithfulness", ok=ok, detail=DETAIL_UNGROUNDED_FIGURE)


def check_prompt_privacy_keys(payload: object) -> EvalFinding:
    """Flag forbidden private-data keys anywhere in the payload."""

    ok = not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    return _finding("prompt_privacy_keys", ok=ok, detail=DETAIL_PRIVACY_KEY)


def check_prompt_privacy_values(payload: object) -> EvalFinding:
    """Flag forbidden private value tokens or secret-like values in the payload."""

    ok = not (find_forbidden_string_values(payload) or find_secret_like_values(payload))
    return _finding("prompt_privacy_values", ok=ok, detail=DETAIL_PRIVACY_VALUE)


def check_generated_output_safety(
    *,
    wording: EvalFinding,
    faithfulness: EvalFinding,
    privacy_keys: EvalFinding,
    privacy_values: EvalFinding,
) -> EvalFinding:
    """Composite: passes only if all generated-output safety checks pass."""

    ok = all(
        finding.status == "passed"
        for finding in (wording, faithfulness, privacy_keys, privacy_values)
    )
    return _finding("generated_output_safety", ok=ok, detail=DETAIL_OUTPUT_SAFETY)


def check_role_boundaries(
    observations: Iterable[tuple[str, bool, bool]],
) -> EvalFinding:
    """Prove public roles never received non-public (agent-safe) evidence.

    Each observation is ``(role_name, is_public_role, received_agent_safe_evidence)``.
    A public role that received agent-safe evidence is a boundary violation.
    """

    ok = not any(is_public and received for _role, is_public, received in observations)
    return _finding("role_boundary", ok=ok, detail=DETAIL_ROLE_BOUNDARY)


def check_evidence_consistency(
    run_summary: Mapping[str, object] | None,
    expected_summary: Mapping[str, object] | None,
) -> EvalFinding:
    """Confirm the deterministic-evidence summary matches the projection it came from."""

    if run_summary is None or expected_summary is None:
        return EvalFinding(check="evidence_consistency", status="deferred", detail=DETAIL_NO_PROJECTION)
    ok = dict(run_summary) == dict(expected_summary)
    return _finding("evidence_consistency", ok=ok, detail=DETAIL_EVIDENCE_DIVERGED)


def classify_failures(provider_warnings: Sequence[str]) -> EvalFinding:
    """Informational classification of run health for eval_flags."""

    detail = DETAIL_PARTIAL_RUN if provider_warnings else DETAIL_CLEAN_RUN
    return EvalFinding(check="failure_classification", status="passed", detail=detail)
