"""Agent-safe deterministic evidence projection for Phase 19C.

This module is backend-only. It prepares structured evidence for future
provider prompts without exposing owner-only portfolio values or raw broker
context.
"""

from dataclasses import asdict, dataclass, field

from app.schemas.trade_review_workspace import TradeReviewWorkspaceRead
from app.services.agent_team.evidence import FLOW_LABELS
from app.services.agent_team.llm_provider import find_forbidden_string_values
from app.services.agent_team.prompt_safety import validate_agent_team_text
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


SAFE_FLOW_LABELS = {
    "stock_buy": "equity_purchase_review",
    "stock_sell_trim": "equity_reduction_review",
    "etf_buy": "fund_purchase_review",
    "etf_sell_trim": "fund_reduction_review",
    "covered_call": "covered_call_review",
    "cash_secured_put": "short_put_collateral_review",
}

AGENT_EVIDENCE_FORBIDDEN_KEYS = FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS | frozenset(
    {
        "account_reference",
        "account_label",
        "account_kind_label",
        "display_label",
        "cash_amount_label",
        "available_cash_label",
        "buying_power_label",
    }
)


@dataclass(frozen=True)
class AgentSafeDeterministicEvidenceProjection:
    """Structured deterministic evidence safe for agent prompt assembly."""

    evidence_mode: str
    deterministic_metric_source: str
    supported_flow_label: str
    review_flow_label: str
    trade_intent_summary: dict[str, object]
    actionability_summary: dict[str, object]
    broker_snapshot_freshness: dict[str, object]
    market_quote_freshness: dict[str, object]
    deterministic_risk_summary: dict[str, object]
    portfolio_shape_summary: dict[str, object]
    scope_metadata: dict[str, object]
    caveat_codes: tuple[str, ...] = ()
    missing_stale_data_warnings: tuple[dict[str, object], ...] = ()
    calculation_notes: tuple[str, ...] = field(
        default_factory=lambda: ("Deterministic backend services own all calculations.",)
    )

    def __post_init__(self) -> None:
        validate_agent_safe_evidence(asdict(self), label="agent-safe deterministic evidence")

    def to_prompt_payload(self) -> dict[str, object]:
        """Return a stable dict for prompt-input assembly."""

        return asdict(self)


def build_agent_safe_deterministic_evidence(
    workspace: TradeReviewWorkspaceRead,
) -> AgentSafeDeterministicEvidenceProjection:
    """Build agent-visible evidence from the frontend-safe trade-review contract."""

    summary = workspace.trade_intent_summary
    context = workspace.portfolio_context
    return AgentSafeDeterministicEvidenceProjection(
        evidence_mode="agent_safe_deterministic_projection",
        deterministic_metric_source="backend_owned_not_llm_generated",
        supported_flow_label=SAFE_FLOW_LABELS[workspace.supported_flow],
        review_flow_label=FLOW_LABELS[workspace.supported_flow],
        trade_intent_summary={
            "intent_family": SAFE_FLOW_LABELS[workspace.supported_flow],
            "asset_class": summary.asset_class,
            "primary_symbol": summary.symbol or summary.underlying_symbol,
            "intent_status": summary.status,
            "option_leg_count": len(summary.legs),
            "option_strategy_label": _safe_strategy_label(summary.strategy_type),
        },
        actionability_summary={
            "review_actionability_status": workspace.actionability.review_actionability_status,
            "language_tier": workspace.actionability.language_tier,
            "reason_count": len(workspace.actionability.reasons),
            "reason_codes": tuple(_safe_caveat_code(reason.code) for reason in workspace.actionability.reasons),
        },
        broker_snapshot_freshness={
            "freshness_scope": workspace.actionability.broker_snapshot.freshness_scope,
            "freshness_status": workspace.actionability.broker_snapshot.freshness_status,
            "source": workspace.actionability.broker_snapshot.source,
            "provider_status": workspace.actionability.broker_snapshot.provider_status,
        },
        market_quote_freshness={
            "freshness_scope": workspace.actionability.market_quotes.freshness_scope,
            "freshness_status": workspace.actionability.market_quotes.freshness_status,
            "data_mode": workspace.actionability.market_quotes.data_mode,
            "actionability_status": workspace.actionability.market_quotes.actionability_status,
            "provider_status": workspace.actionability.market_quotes.provider_status,
        },
        deterministic_risk_summary={
            "highest_severity": workspace.deterministic_review.highest_severity,
            "has_blocker": workspace.deterministic_review.has_blocker,
            "risk_rule_count": len(workspace.deterministic_review.risk_rule_violations),
            "risk_rule_codes": tuple(item.code for item in workspace.deterministic_review.risk_rule_violations),
            "missing_data_warning_count": len(workspace.deterministic_review.missing_data_warnings),
        },
        portfolio_shape_summary={
            "context_available": context is not None,
            "equity_position_count": context.stock_position_count if context is not None else 0,
            "option_position_count": context.option_position_count if context is not None else 0,
            "liquidity_state": _liquidity_state(context.cash_state) if context is not None else "not_available",
        },
        scope_metadata=_safe_scope_metadata(workspace),
        caveat_codes=tuple(_safe_caveat_code(caveat.code) for caveat in workspace.caveats),
        missing_stale_data_warnings=tuple(
            {
                "code": _safe_caveat_code(warning.code),
                "scope": warning.scope,
                "severity": warning.severity,
            }
            for warning in workspace.deterministic_review.missing_data_warnings
        ),
    )


def validate_agent_safe_evidence(payload: object, *, label: str) -> None:
    """Reject private fields and prompt-unsafe values in agent evidence."""

    forbidden = find_forbidden_keys(payload, forbidden_keys=AGENT_EVIDENCE_FORBIDDEN_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{label} contains forbidden private field(s): {blocked}")
    private_values = find_forbidden_string_values(payload)
    if private_values:
        blocked = ", ".join(sorted(private_values))
        raise ValueError(f"{label} contains forbidden private value token(s): {blocked}")
    validate_agent_team_text(payload, label=label)


def projection_snapshot(projection: AgentSafeDeterministicEvidenceProjection) -> dict[str, object]:
    """Return a stable synthetic snapshot for tests and future review fixtures."""

    return projection.to_prompt_payload()


def _safe_strategy_label(strategy_type: str | None) -> str | None:
    if strategy_type is None:
        return None
    return SAFE_FLOW_LABELS.get(strategy_type, strategy_type.replace("cash_", "liquidity_"))


def _liquidity_state(value: str) -> str:
    if value == "available":
        return "available"
    if value == "not_exposed":
        return "not_exposed"
    return "not_available"


def _safe_caveat_code(code: str) -> str:
    return (
        code.replace("cash_secured_put", "short_put")
        .replace("buying_power", "broker_capacity")
        .replace("cash_collateral", "liquidity_collateral")
        .replace("cash_", "liquidity_")
    )


def unavailable_agent_scope_summary() -> dict[str, object]:
    """Lossy, sanitized 'scope unavailable' summary (single source of truth).

    Carries only scope categories, booleans, and counts. Never account refs,
    labels, kinds, balances, or any other private value.
    """

    return {
        "scope_present": False,
        "portfolio_scope_mode": "unavailable",
        "portfolio_context_selection_mode": None,
        "selected_context_present": False,
        "included_account_count": 0,
        "excluded_account_count": 0,
        "review_account_present": False,
        "account_level_feasibility_evaluated": False,
        "scope_caveat_codes": (),
    }


def _safe_scope_metadata(workspace: TradeReviewWorkspaceRead) -> dict[str, object]:
    scope_metadata = workspace.scope_metadata
    if scope_metadata is None:
        return unavailable_agent_scope_summary()

    scope = scope_metadata.portfolio_context_scope
    return {
        "scope_present": True,
        "portfolio_scope_mode": scope.scope_mode,
        "portfolio_context_selection_mode": scope.selection_mode,
        "selected_context_present": scope.context_reference is not None,
        "included_account_count": len(scope.included_account_labels),
        "excluded_account_count": len(scope.excluded_account_labels),
        "review_account_present": scope_metadata.review_account is not None,
        "account_level_feasibility_evaluated": scope_metadata.account_level_feasibility_evaluated,
        "scope_caveat_codes": tuple(_safe_caveat_code(code) for code in scope_metadata.scope_caveat_codes),
    }
