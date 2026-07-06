"""P34A-T11D layout guard: tools.py split into the tools/ package.

Asserts the facade re-exports the full public surface external code relies on,
that the three submodules hold their intended concerns, and that privacy-tier
governance stays first-class in ``envelopes``. Behavior-preserving split.
"""

import importlib


def test_tools_facade_exposes_full_public_surface() -> None:
    tools = importlib.import_module("app.services.agent_team.tools")
    for name in (
        # envelopes: contracts + governance vocabulary
        "ToolRequest",
        "ToolResult",
        "ToolRegistryEntry",
        "ToolAuditRecord",
        "validate_tool_payload",
        "TOOL_FORBIDDEN_KEYS",
        "TOOL_PROHIBITED_PHRASES",
        "TOOL_GENERATED_METRIC_PATTERNS",
        "SEC_RAW_PATH_OR_FILE_RE",
        "assert_role_tier_allowed",
        # registry
        "build_tool_registry",
        "default_tool_registry",
        "is_tool_allowed_for_role",
        # executors
        "execute_tool_request",
        "blocked_tool_result",
        "unavailable_tool_result",
        "timeout_tool_result",
        "budget_exceeded_tool_result",
        "tool_result_for_disallowed_role",
    ):
        assert hasattr(tools, name), f"tools facade missing {name}"


def test_submodules_own_their_concerns_and_are_identical_via_facade() -> None:
    tools = importlib.import_module("app.services.agent_team.tools")
    envelopes = importlib.import_module("app.services.agent_team.tools.envelopes")
    registry = importlib.import_module("app.services.agent_team.tools.registry")
    executors = importlib.import_module("app.services.agent_team.tools.executors")

    assert tools.ToolResult is envelopes.ToolResult
    assert tools.validate_tool_payload is envelopes.validate_tool_payload
    assert tools.default_tool_registry is registry.default_tool_registry
    assert tools.execute_tool_request is executors.execute_tool_request

    # Layering: executors depends on registry's default; both build on envelopes.
    assert executors.default_tool_registry is registry.default_tool_registry
    assert registry.ToolRegistryEntry is envelopes.ToolRegistryEntry


def test_private_tier_boundary_stays_first_class_in_envelopes() -> None:
    envelopes = importlib.import_module("app.services.agent_team.tools.envelopes")
    assert envelopes.PRIVATE_TIER == "private_forbidden"
    assert "private_forbidden" not in envelopes.ALLOWED_TOOL_EVIDENCE_TIERS
    # A valid agent_safe entry constructs (proves the signature); flipping only
    # the tier to private_forbidden must raise — so the rejection below is the
    # governance guard, not a signature mismatch.
    valid_kwargs = dict(
        tool_name="deterministic_review_findings",
        display_name="Deterministic Review Findings",
        evidence_tier="agent_safe",
        role_allowlist=("risk_management_agent",),
        mode="mock",
    )
    envelopes.ToolRegistryEntry(**valid_kwargs)  # does not raise
    import pytest

    with pytest.raises(ValueError):
        envelopes.ToolRegistryEntry(**{**valid_kwargs, "evidence_tier": "private_forbidden"})


def test_default_registry_executes_end_to_end_through_facade() -> None:
    tools = importlib.import_module("app.services.agent_team.tools")
    registry = tools.default_tool_registry()
    assert "trade_intent_summary" in registry
    assert all(entry.evidence_tier in tools.ALLOWED_TOOL_EVIDENCE_TIERS for entry in registry.values())
