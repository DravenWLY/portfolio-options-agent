"""Deterministic portfolio-context agent output for Phase 16 workflows."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.schemas.actionability import PortfolioActionabilityDecision
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review.context import PortfolioReviewContext


AGENT_NAME = "portfolio_context_agent"
FORBIDDEN_AGENT_CONTEXT_KEYS = FORBIDDEN_REPORT_FACT_KEYS | {
    "account_number",
    "broker_account_number",
    "provider_account_id",
    "provider_connection_id",
    "raw_payload",
    "raw_metadata",
    "raw_provider_payload",
    "source_ref",
    "user_secret",
    "consumer_key",
    "access_token",
    "api_key",
    "portal_url",
    "total_internal_value",
    "total_cash",
    "free_cash",
    "reserved_collateral_cash",
    "market_value",
    "quantity",
}


@dataclass(frozen=True)
class HoldingsShapeSummary:
    has_cash_context: bool
    stock_position_count: int
    option_position_count: int
    long_option_position_count: int
    short_option_position_count: int


@dataclass(frozen=True)
class PortfolioFreshnessSummary:
    data_sources: tuple[str, ...]
    data_freshness_statuses: tuple[str, ...]
    latest_snapshot_as_of: datetime | None
    broker_snapshot_status: str
    market_quote_status: str
    review_actionability_status: str
    language_tier: str


@dataclass(frozen=True)
class ReportHistoryReference:
    reference_id: str
    report_type: str
    status: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class PortfolioContextAgentOutput:
    agent_name: str
    generated_at: datetime
    portfolio_shape: HoldingsShapeSummary
    freshness: PortfolioFreshnessSummary
    actionability: PortfolioActionabilityDecision
    report_history_references: tuple[ReportHistoryReference, ...]
    notes: tuple[str, ...]

    def to_llm_payload(self) -> dict:
        """Return the default LLM-bound payload with private broker values omitted."""

        payload = asdict(self)
        forbidden = _find_forbidden_keys(payload)
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"portfolio context agent payload contains forbidden keys: {blocked}")
        return payload


class PortfolioContextAgent:
    """Build a sanitized, deterministic portfolio context for downstream agents."""

    def run(
        self,
        *,
        portfolio_context: PortfolioReviewContext,
        actionability: PortfolioActionabilityDecision,
        report_history_references: tuple[ReportHistoryReference, ...] = (),
        generated_at: datetime | None = None,
    ) -> PortfolioContextAgentOutput:
        generated = generated_at or datetime.now(UTC)
        portfolio_shape = HoldingsShapeSummary(
            has_cash_context=portfolio_context.cash is not None,
            stock_position_count=len(portfolio_context.stock_positions),
            option_position_count=len(portfolio_context.option_positions),
            long_option_position_count=sum(1 for position in portfolio_context.option_positions if position.position_side == "long"),
            short_option_position_count=sum(
                1 for position in portfolio_context.option_positions if position.position_side == "short"
            ),
        )
        freshness = PortfolioFreshnessSummary(
            data_sources=tuple(portfolio_context.data_sources),
            data_freshness_statuses=tuple(portfolio_context.data_freshness_statuses),
            latest_snapshot_as_of=portfolio_context.latest_snapshot_as_of,
            broker_snapshot_status=actionability.broker_snapshot.freshness_status,
            market_quote_status=actionability.market_quotes.freshness_status,
            review_actionability_status=actionability.review_actionability_status,
            language_tier=actionability.language_tier,
        )
        notes = _notes_for_actionability(actionability)
        output = PortfolioContextAgentOutput(
            agent_name=AGENT_NAME,
            generated_at=generated,
            portfolio_shape=portfolio_shape,
            freshness=freshness,
            actionability=actionability,
            report_history_references=tuple(report_history_references),
            notes=notes,
        )
        output.to_llm_payload()
        return output


def _notes_for_actionability(actionability: PortfolioActionabilityDecision) -> tuple[str, ...]:
    if actionability.review_actionability_status == "normal_review":
        return ("Broker snapshot and market quote metadata satisfy the current actionability policy.",)
    if actionability.review_actionability_status == "analysis_only":
        return ("Context is available for analysis-only explanation; do not frame it as immediately actionable.",)
    if actionability.requires_user_confirmation:
        return ("Manual confirmation is required before deterministic review or agent explanation proceeds.",)
    return ("Context is blocked by the portfolio snapshot actionability policy.",)


def _find_forbidden_keys(value: object, *, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.strip().lower() in FORBIDDEN_AGENT_CONTEXT_KEYS:
                found.add(key_path)
            found.update(_find_forbidden_keys(item, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(_find_forbidden_keys(item, prefix=item_path))
        return found
    return set()
