"""P36 deterministic summary/check surface for saved reports without live roles."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.reports import SavedEvidencePackageRead, SavedToolMediatedRunArtifactRead
from app.services.agent_team.auditing.v3_value_gates import P36_ARTIFACT_SCHEMA_VERSION
from app.services.agent_team.tools import ToolRequest, ToolResult, default_tool_registry, execute_tool_request
from app.services.reports.display_labels import display_label_for_code, display_labels_for_codes, render_display_list


P36_STANDALONE_SUMMARY_CONTRACT_VERSION = "p36_deterministic_standalone_v1"
_CALC_TOOL_NAMES = (
    "calc_exposure_delta",
    "calc_concentration_metrics",
    "calc_cash_impact",
    "calc_option_structure",
    "calc_scenario_exposure",
    "calc_price_range_position",
    "calc_return_windows",
    "calc_drawdown_stats",
    "calc_volatility_stats",
    "calc_ma_relationships",
    "calc_financial_ratios",
    "calc_period_change",
    "calc_macro_series_change",
    "calc_event_window",
)
_CALC_REQUESTING_ROLE = {
    "calc_exposure_delta": "risk_management_agent",
    "calc_concentration_metrics": "risk_management_agent",
    "calc_cash_impact": "risk_management_agent",
    "calc_option_structure": "risk_management_agent",
    "calc_scenario_exposure": "risk_management_agent",
    "calc_price_range_position": "technical_analyst",
    "calc_return_windows": "technical_analyst",
    "calc_drawdown_stats": "technical_analyst",
    "calc_volatility_stats": "technical_analyst",
    "calc_ma_relationships": "technical_analyst",
    "calc_financial_ratios": "fundamentals_analyst",
    "calc_period_change": "fundamentals_analyst",
    "calc_macro_series_change": "news_analyst",
    "calc_event_window": "news_analyst",
}
_FRESHNESS_INVENTORY_ROLES = (
    "technical_analyst",
    "risk_management_agent",
    "fundamentals_analyst",
    "news_analyst",
    "portfolio_manager_agent",
)
_OUTCOME_LABELS = {
    "available": "available from frozen evidence",
    "limited": "limited by frozen evidence caveats",
    "unable_to_verify": "unable to verify from frozen evidence",
    "not_applicable": "not applicable to this saved review",
}
_CALC_DISPLAY_LABELS = {
    "calc_exposure_delta": "Exposure change",
    "calc_concentration_metrics": "Concentration metrics",
    "calc_cash_impact": "Cash impact",
    "calc_option_structure": "Option structure",
    "calc_scenario_exposure": "Option scenario exposure",
    "calc_price_range_position": "Price range and position",
    "calc_return_windows": "Return windows",
    "calc_drawdown_stats": "Drawdown statistics",
    "calc_volatility_stats": "Volatility statistics",
    "calc_ma_relationships": "Moving-average relationships",
    "calc_financial_ratios": "Financial ratios",
    "calc_period_change": "Statement-period change",
    "calc_macro_series_change": "Macro-series change",
    "calc_event_window": "Event-window recency",
    "calc_freshness_inventory": "Freshness inventory",
}


@dataclass(frozen=True)
class DeterministicStandaloneSummaryCheck:
    """A backend-owned report core that needs no live analyst response."""

    contract_version: str
    calculation_results: tuple[ToolResult, ...]
    summary_markdown: str
    verification_items: tuple[str, ...]


def build_deterministic_standalone_summary_check(
    evidence: SavedEvidencePackageRead,
) -> DeterministicStandaloneSummaryCheck:
    """Build a renderable historical summary from frozen evidence and C1-C15.

    This function has no live-provider or source-acquisition seam. It is a
    deterministic historical rendering surface over the package it receives.
    """

    registry = default_tool_registry()
    results = tuple(
        execute_tool_request(
            ToolRequest(tool_name=tool_name, requesting_role=_CALC_REQUESTING_ROLE[tool_name]),
            evidence=evidence,
            registry=registry,
        )
        for tool_name in _CALC_TOOL_NAMES
    ) + tuple(
        execute_tool_request(
            ToolRequest(tool_name="calc_freshness_inventory", requesting_role=role_name),
            evidence=evidence,
            registry=registry,
        )
        for role_name in _FRESHNESS_INVENTORY_ROLES
    )
    lines = [
        "## Saved deterministic review",
        "This summary uses frozen review-time evidence and does not require a live analyst response.",
        "Source: frozen saved evidence.",
    ]
    if evidence.freshness.broker_snapshot_freshness_label:
        lines.append(f"Broker snapshot freshness: {evidence.freshness.broker_snapshot_freshness_label}.")
    if evidence.freshness.market_quote_freshness_label:
        lines.append(f"Market quote freshness: {evidence.freshness.market_quote_freshness_label}.")
    verification_items = [
        "Saved source and review-time scope were used.",
        "Calculation results were derived only from frozen saved evidence.",
    ]
    for result in results:
        payload = result.summary_payload
        outcome = _OUTCOME_LABELS.get(str(payload.get("outcome")), "not available from frozen evidence")
        values = tuple(payload.get("value_labels") or ())
        value_text = _render_values(values)
        method_label = str(payload.get("method_label") or "frozen saved-evidence method")
        as_of_labels = tuple(str(item) for item in payload.get("as_of_labels") or ())
        as_of_text = render_display_list(as_of_labels) if as_of_labels else "saved review time"
        display_name = _CALC_DISPLAY_LABELS[result.tool_name]
        lines.append(
            f"- {display_name}: {outcome}; source: {result.source_label}; "
            f"method: {method_label}; as of {as_of_text}.{value_text}"
        )
        if str(payload.get("outcome")) == "unable_to_verify":
            lines.append(f"  Gap: {display_name.lower()} could not be verified from the frozen saved evidence.")
        caveats = tuple(str(code) for code in payload.get("caveats") or ())
        if caveats:
            labels = display_labels_for_codes(caveats).labels
            verification_items.append(f"Calculation caveats: {render_display_list(labels)}.")
    return DeterministicStandaloneSummaryCheck(
        contract_version=P36_STANDALONE_SUMMARY_CONTRACT_VERSION,
        calculation_results=results,
        summary_markdown="\n".join(lines),
        verification_items=tuple(dict.fromkeys(verification_items)),
    )


def freeze_deterministic_standalone_summary_check(
    check: DeterministicStandaloneSummaryCheck,
    *,
    frozen_at,
) -> SavedToolMediatedRunArtifactRead:
    """Freeze the P36 calculation prefix without a provider or live role run."""

    return SavedToolMediatedRunArtifactRead(
        artifact_schema_version=P36_ARTIFACT_SCHEMA_VERSION,
        provider_mode="tool_mediated_mock",
        plan_version="p36_calculation_plan_v1",
        audit_version="p36_calculation_audit_v1",
        locked_question="saved_deterministic_calculation_check",
        dimensions=("frozen_calculations", "historical_scope"),
        role_plan=tuple(
            {
                "role_name": role_name,
                "tool_requests": tuple(
                    {"tool_name": result.tool_name, "args": {}}
                    for result in check.calculation_results
                    if result.role_name == role_name
                ),
                "rationale_code": "p36_deterministic_calculation_check",
            }
            for role_name in dict.fromkeys(result.role_name for result in check.calculation_results)
        ),
        tool_results=tuple(_frozen_result(result) for result in check.calculation_results),
        audited_findings=(),
        auditor={
            "audit_version": "p36_calculation_audit_v1",
            "role_verdicts": (),
            "contradictions": (),
            "dropped_claims": (),
            "repass_triggered": False,
            "eval_flags": (),
        },
        provider_runs=(),
        open_questions=(),
        synthesis_evidence_references=(),
        warning_codes=(),
        tool_result_count=len(check.calculation_results),
        frozen_at=frozen_at,
    )


def _render_values(value_labels: tuple[object, ...]) -> str:
    parts: list[str] = []
    for row in value_labels:
        if not isinstance(row, dict):
            continue
        value = row.get("value_label")
        unit = row.get("unit_label")
        fact_key = row.get("fact_key")
        if isinstance(value, str) and isinstance(unit, str) and isinstance(fact_key, str):
            # Do not turn an unknown storage key into user-visible prose. The
            # display-label service returns a generic reviewed fallback until a
            # new calculation fact is explicitly approved for rendering.
            label = display_label_for_code(fact_key)
            parts.append(f" {label}: {value} ({unit})")
    return "" if not parts else " Frozen values:" + ";".join(parts) + "."


def _frozen_result(result: ToolResult) -> dict[str, object]:
    return {
        "tool_name": result.tool_name,
        "role_name": result.role_name,
        "status": result.status,
        "evidence_tier": result.evidence_tier,
        "data_mode": result.data_mode,
        "source_key": result.source_key,
        "source_label": result.source_label,
        "availability": result.availability,
        "freshness": result.freshness,
        "as_of": result.as_of,
        "scope": result.scope,
        "caveat_codes": result.caveat_codes,
        "evidence_refs": result.evidence_refs,
        "summary_payload": result.summary_payload,
        "provenance": result.provenance,
        "latency_ms": result.latency_ms,
        "estimated_cost": result.estimated_cost,
        "is_mock": result.is_mock,
        "contract_version": result.contract_version,
    }
