"""Legacy P19/P25 Agent Console preview path (quarantined P34A-T11C).

These modules back the ``/agent-team/trade-review-analysis/preview`` route and
the standalone Gemini smoke via ``ReviewRunner`` / ``AgentTeamOrchestrator``.
They are the earlier generation of the Agent Team and are **bug-fix only** —
the canonical product path is the tool-mediated saved-report pipeline
(``tool_mediated_report`` today; ``orchestration/`` after P34A-T11E). Do not
extend this package or route new work through it.

The flat old paths (``agent_team.review_runner``, ``orchestrator``, ``prompts``,
``prompt_inputs``, ``evidence``, ``evidence_projection``, ``state``,
``run_state``, ``frontend_read``) remain as compatibility shims that re-export
from here until the P34A-T11F importer flip.
"""
