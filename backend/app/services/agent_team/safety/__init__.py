"""Agent Team safety-validator layer (P34A-T11B).

Groups the app-owned output/report/prompt safety boundaries that were
previously flat modules under ``agent_team/``:

- ``output_safety``        — provider-output boundary (advice/private/metric rejection)
- ``report_output_safety`` — saved Agent Team report boundary + role evidence allowlists
- ``prompt_safety``        — prompt/input payload boundary

The old module paths (``agent_team.output_safety``, ``report_output_safety``,
``prompt_safety``) remain as compatibility shims that re-export from here.
These are validators only — no behavior change was made in the move.
"""

from typing import Any

from app.services.agent_team.safety.output_safety import (
    GENERATED_METRIC_PATTERNS,
    validate_llm_provider_output,
)
from app.services.agent_team.safety.prompt_safety import (
    validate_agent_team_text,
    validate_prompt_input_payload,
)
_REPORT_OUTPUT_SAFETY_EXPORTS = frozenset(
    {
        "INVENTED_LEVEL_PATTERNS",
        "REPORT_PROHIBITED_PHRASES",
        "ROLE_ALLOWED_EVIDENCE_KEYS",
        "SOURCE_LEAK_PATTERNS",
        "validate_agent_team_report_output",
    }
)


def __getattr__(name: str) -> Any:
    """Defer report-schema-dependent exports until they are requested.

    ``report_output_safety`` imports report schemas, while light-weight agent
    safety validators are needed during those schemas' initialization.
    """

    if name in _REPORT_OUTPUT_SAFETY_EXPORTS:
        from app.services.agent_team.safety import report_output_safety

        return getattr(report_output_safety, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "GENERATED_METRIC_PATTERNS",
    "INVENTED_LEVEL_PATTERNS",
    "REPORT_PROHIBITED_PHRASES",
    "ROLE_ALLOWED_EVIDENCE_KEYS",
    "SOURCE_LEAK_PATTERNS",
    "validate_agent_team_report_output",
    "validate_agent_team_text",
    "validate_llm_provider_output",
    "validate_prompt_input_payload",
]
