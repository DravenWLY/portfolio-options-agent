"""P34A-T11F guard: the flat compatibility shims are gone; canonical paths hold.

After the importer flip, the 19 flat single-module shims under ``agent_team/``
were deleted. This test fails loudly if any of them is reintroduced (which would
mean two homes for the same code again) and confirms the canonical packages plus
the two retained package facades still expose the surface consumers rely on.
"""

import importlib

import pytest

_REMOVED_FLAT_MODULES = (
    "llm_provider",
    "provider_config",
    "provider_factory",
    "google_provider",
    "openai_provider",
    "mock_provider",
    "output_safety",
    "report_output_safety",
    "prompt_safety",
    "roles",
    "orchestrator",
    "review_runner",
    "prompts",
    "prompt_inputs",
    "evidence",
    "evidence_projection",
    "state",
    "run_state",
    "frontend_read",
)


@pytest.mark.parametrize("name", _REMOVED_FLAT_MODULES)
def test_flat_shim_module_is_removed(name: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(f"app.services.agent_team.{name}")


def test_canonical_packages_expose_their_surface() -> None:
    llm = importlib.import_module("app.services.agent_team.llm_clients")
    safety = importlib.import_module("app.services.agent_team.safety")
    agents = importlib.import_module("app.services.agent_team.agents")
    assert hasattr(llm, "resolve_llm_provider") and hasattr(llm, "ChainedLLMProvider")
    assert hasattr(safety, "validate_agent_team_report_output")
    assert hasattr(agents, "role_definition")
    # Retained package facades still resolve for consumers.
    tools = importlib.import_module("app.services.agent_team.tools")
    tmr = importlib.import_module("app.services.agent_team.tool_mediated_report")
    assert hasattr(tools, "execute_tool_request")
    assert hasattr(tmr, "build_tool_mediated_agent_team_summary")


def test_package_facade_re_export_identity_holds() -> None:
    # The two retained facades must expose the SAME objects as their submodules.
    tools = importlib.import_module("app.services.agent_team.tools")
    envelopes = importlib.import_module("app.services.agent_team.tools.envelopes")
    tmr = importlib.import_module("app.services.agent_team.tool_mediated_report")
    runner = importlib.import_module("app.services.agent_team.orchestration.tool_mediated_runner")
    assert tools.ToolResult is envelopes.ToolResult
    assert tmr.run_tool_mediated_agent_team is runner.run_tool_mediated_agent_team
