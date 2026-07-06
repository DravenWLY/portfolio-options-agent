# DEPRECATED (P34A-T11C): legacy P19/P25 Agent Console preview path. Bug-fix
# only; superseded by the tool-mediated saved-report pipeline. Do not extend.
"""Safe evidence projections for the Phase 19A mock agent team."""

from dataclasses import asdict, dataclass, field

from app.schemas.trade_review_workspace import TradeReviewWorkspaceRead
from app.services.agent_team.safety.prompt_safety import validate_agent_team_text


FLOW_LABELS = {
    "stock_buy": "equity_purchase_review",
    "stock_sell_trim": "equity_reduction_review",
    "etf_buy": "fund_purchase_review",
    "etf_sell_trim": "fund_reduction_review",
    "covered_call": "covered_call_review",
    "cash_secured_put": "short_put_collateral_review",
}


@dataclass(frozen=True)
class PublicEvidenceBundle:
    ticker: str
    company_name: str | None = None
    fundamentals_context: str = "Mock public fundamentals evidence is unavailable in this phase."
    news_context: str = "Mock public news evidence is unavailable in this phase."
    macro_context: str = "Mock macro event context is synthetic and analysis-only."
    technical_context: str = "Mock technical context is unavailable; no live quote provider was contacted."
    evidence_mode: str = "mock_public_evidence"

    def __post_init__(self) -> None:
        validate_agent_team_text(asdict(self), label="public evidence bundle")


@dataclass(frozen=True)
class DeterministicEvidenceBundle:
    review_flow_label: str
    trade_intent_summary: dict[str, object]
    actionability_summary: dict[str, object]
    broker_snapshot_freshness: dict[str, object]
    market_quote_freshness: dict[str, object]
    risk_summary: dict[str, object]
    portfolio_shape: dict[str, object] = field(default_factory=dict)
    caveat_codes: tuple[str, ...] = ()
    evidence_mode: str = "sanitized_deterministic_evidence"

    def __post_init__(self) -> None:
        validate_agent_team_text(asdict(self), label="deterministic evidence bundle")


def public_evidence_from_workspace(workspace: TradeReviewWorkspaceRead) -> PublicEvidenceBundle:
    ticker = (
        workspace.trade_intent_summary.symbol
        or workspace.trade_intent_summary.underlying_symbol
        or "XYZ"
    )
    return PublicEvidenceBundle(ticker=ticker)


def deterministic_evidence_from_workspace(workspace: TradeReviewWorkspaceRead) -> DeterministicEvidenceBundle:
    summary = workspace.trade_intent_summary
    context = workspace.portfolio_context
    return DeterministicEvidenceBundle(
        review_flow_label=FLOW_LABELS[workspace.supported_flow],
        trade_intent_summary={
            "intent_type": _safe_intent_label(workspace.supported_flow),
            "asset_class": summary.asset_class,
            "symbol": summary.symbol or summary.underlying_symbol,
            "status": summary.status,
            "option_leg_count": len(summary.legs),
        },
        actionability_summary={
            "review_actionability_status": workspace.actionability.review_actionability_status,
            "language_tier": workspace.actionability.language_tier,
            "reason_count": len(workspace.actionability.reasons),
        },
        broker_snapshot_freshness={
            "freshness_scope": workspace.actionability.broker_snapshot.freshness_scope,
            "freshness_status": workspace.actionability.broker_snapshot.freshness_status,
            "source": workspace.actionability.broker_snapshot.source,
        },
        market_quote_freshness={
            "freshness_scope": workspace.actionability.market_quotes.freshness_scope,
            "freshness_status": workspace.actionability.market_quotes.freshness_status,
            "data_mode": workspace.actionability.market_quotes.data_mode,
            "actionability_status": workspace.actionability.market_quotes.actionability_status,
        },
        risk_summary={
            "highest_severity": workspace.deterministic_review.highest_severity,
            "has_blocker": workspace.deterministic_review.has_blocker,
            "risk_rule_count": len(workspace.deterministic_review.risk_rule_violations),
            "missing_data_warning_count": len(workspace.deterministic_review.missing_data_warnings),
        },
        portfolio_shape={
            "context_available": context is not None,
            "stock_position_count": context.stock_position_count if context is not None else 0,
            "option_position_count": context.option_position_count if context is not None else 0,
            "liquidity_state": _liquidity_state(context.cash_state) if context is not None else "not_available",
        },
        caveat_codes=tuple(_safe_caveat_code(caveat.code) for caveat in workspace.caveats),
    )


def _safe_intent_label(supported_flow: str) -> str:
    return FLOW_LABELS[supported_flow]


def _liquidity_state(value: str) -> str:
    if value == "available":
        return "available"
    if value == "not_exposed":
        return "not_exposed"
    return "not_available"


def _safe_caveat_code(code: str) -> str:
    return code.replace("cash_secured_put", "short_put").replace("cash_", "liquidity_")
