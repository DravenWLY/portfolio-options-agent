"""Prompt and output safety helpers for Phase 19A agent-team contracts."""

from app.services.agent_team.llm_clients.contracts import validate_llm_provider_payload


def validate_agent_team_text(value: object, *, label: str) -> None:
    """Apply the Phase 19A provider safety boundary to prompt/output payloads."""

    validate_llm_provider_payload(value, label=label)


def validate_prompt_input_payload(value: object, *, label: str) -> None:
    """Validate prompt/input payloads before provider calls."""

    validate_llm_provider_payload(value, label=label)
