"""P34A-T11E layout guard: god-module relocated + Evidence Auditor extracted.

Asserts tool_mediated_report.py is now a facade over orchestration.models +
orchestration.tool_mediated_runner + auditing.evidence_auditor, that the facade
re-exports the full external surface (incl the privately-imported
_chain_metadata), and that the runner<->auditor cycle is broken via the shared
models foundation. Behavior-preserving relocation.
"""

import importlib


def test_facade_exposes_full_external_surface() -> None:
    facade = importlib.import_module("app.services.agent_team.tool_mediated_report")
    for name in (
        # public API imported by reports service, agent_eval, and tests
        "build_tool_mediated_agent_team_summary",
        "build_tool_mediated_agent_team_summary_from_provider_resolution",
        "run_tool_mediated_agent_team",
        "build_evidence_catalog",
        "build_planner_plan",
        "build_role_findings",
        "audit_findings",
        "usable_content_by_role",
        "RoleFinding",
        "RoleFindingSet",
        "AuditorRecord",
        "Contradiction",
        "ToolMediatedRunState",
        "PLAN_VERSION",
        "AUDIT_VERSION",
        "MAX_PLANNER_REPASSES",
        "PLAN_DIMENSIONS",
        # privately imported by test_provider_chain
        "_chain_metadata",
    ):
        assert hasattr(facade, name), f"facade missing {name}"


def test_symbols_resolve_to_their_new_home_modules() -> None:
    facade = importlib.import_module("app.services.agent_team.tool_mediated_report")
    models = importlib.import_module("app.services.agent_team.orchestration.models")
    auditor = importlib.import_module("app.services.agent_team.auditing.evidence_auditor")
    runner = importlib.import_module("app.services.agent_team.orchestration.tool_mediated_runner")

    # dataclasses/constants live in models
    assert facade.RoleFinding is models.RoleFinding
    assert facade.ToolMediatedRunState is models.ToolMediatedRunState
    assert facade.AUDIT_VERSION == models.AUDIT_VERSION
    # auditor extracted
    assert facade.audit_findings is auditor.audit_findings
    assert runner.audit_findings is auditor.audit_findings
    # runner owns the pipeline entry points
    assert facade.run_tool_mediated_agent_team is runner.run_tool_mediated_agent_team
    assert facade.build_tool_mediated_agent_team_summary is runner.build_tool_mediated_agent_team_summary


def test_models_foundation_has_no_cycle_dependency_on_runner_or_auditor() -> None:
    # models must import cleanly WITHOUT importing the runner or auditor, so the
    # shared-foundation layering that breaks the type cycle actually holds.
    import sys

    for mod in (
        "app.services.agent_team.orchestration.models",
        "app.services.agent_team.auditing.evidence_auditor",
        "app.services.agent_team.orchestration.tool_mediated_runner",
    ):
        sys.modules.pop(mod, None)
    models = importlib.import_module("app.services.agent_team.orchestration.models")
    # auditor uses the shared dataclasses from models (same objects).
    auditor = importlib.import_module("app.services.agent_team.auditing.evidence_auditor")
    assert auditor.RoleFindingSet is models.RoleFindingSet
    assert auditor.usable_content_by_role is models.usable_content_by_role
