"""Deterministic trade-review explanation agent."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.schemas.actionability import PortfolioActionabilityDecision
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review.report import TradeReviewAgentProjection


AGENT_NAME = "trade_review_agent"
FORBIDDEN_TRADE_REVIEW_AGENT_KEYS = FORBIDDEN_REPORT_FACT_KEYS | {
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
    "cash_delta",
    "projected_free_cash",
    "total_cash",
    "free_cash",
    "buying_power",
}
PROHIBITED_ADVICE_PHRASES = ("you should", "i recommend", "recommend buying", "recommend selling")


@dataclass(frozen=True)
class TradeReviewExplanationSection:
    title: str
    bullets: tuple[str, ...]


@dataclass(frozen=True)
class TradeReviewAgentOutput:
    agent_name: str
    generated_at: datetime
    intent_id: str
    review_actionability_status: str
    can_run_agent_explanation: bool
    highest_severity: str | None
    has_blocker: bool
    sections: tuple[TradeReviewExplanationSection, ...]
    deterministic_fields_used: tuple[str, ...]
    notes: tuple[str, ...]

    def to_llm_payload(self) -> dict:
        payload = asdict(self)
        forbidden = _find_forbidden_keys(payload)
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"trade review agent payload contains forbidden keys: {blocked}")
        rendered = repr(payload).lower()
        for phrase in PROHIBITED_ADVICE_PHRASES:
            if phrase in rendered:
                raise ValueError(f"trade review agent payload contains prohibited advice phrase: {phrase}")
        return payload


class TradeReviewAgent:
    """Explain already-computed trade-review fields without inventing metrics."""

    def run(
        self,
        *,
        projection: TradeReviewAgentProjection,
        actionability: PortfolioActionabilityDecision,
        generated_at: datetime | None = None,
    ) -> TradeReviewAgentOutput:
        generated = generated_at or datetime.now(UTC)
        if not actionability.can_run_agent_explanation:
            sections = (
                TradeReviewExplanationSection(
                    title="Actionability Gate",
                    bullets=tuple(reason.message for reason in actionability.reasons),
                ),
            )
            fields_used = ("review_actionability_status", "actionability.reasons")
            notes = ("Agent explanation is limited because the actionability policy blocks this review.",)
        else:
            sections = (
                _scenario_section(projection),
                _risk_section(projection),
                _freshness_section(projection, actionability),
            )
            fields_used = (
                "payoff.points",
                "payoff.max_loss",
                "payoff.max_gain",
                "risk_rule_violations",
                "highest_severity",
                "has_blocker",
                "portfolio_impact.broker_freshness_status",
                "portfolio_impact.market_freshness_status",
                "review_actionability_status",
            )
            notes = (
                "Explanation is generated from deterministic Python outputs only.",
                "This is review and scenario analysis, not a recommendation or trade instruction.",
            )

        output = TradeReviewAgentOutput(
            agent_name=AGENT_NAME,
            generated_at=generated,
            intent_id=projection.intent_id,
            review_actionability_status=actionability.review_actionability_status,
            can_run_agent_explanation=actionability.can_run_agent_explanation,
            highest_severity=projection.highest_severity,
            has_blocker=projection.has_blocker,
            sections=sections,
            deterministic_fields_used=fields_used,
            notes=notes,
        )
        output.to_llm_payload()
        return output


def _scenario_section(projection: TradeReviewAgentProjection) -> TradeReviewExplanationSection:
    point_count = len(projection.payoff.points)
    return TradeReviewExplanationSection(
        title="Scenario Shape",
        bullets=(
            f"Deterministic payoff review contains {point_count} scenario point(s).",
            f"Maximum loss field is {'available' if projection.payoff.max_loss is not None else 'not available'} for this review.",
            f"Maximum gain field is {'available' if projection.payoff.max_gain is not None else 'not available'} for this review.",
        ),
    )


def _risk_section(projection: TradeReviewAgentProjection) -> TradeReviewExplanationSection:
    violation_count = len(projection.risk_rule_violations)
    severity = projection.highest_severity or "none"
    blocker_text = "contains blocker-level findings" if projection.has_blocker else "contains no blocker-level findings"
    return TradeReviewExplanationSection(
        title="Risk Findings",
        bullets=(
            f"Deterministic risk engine returned {violation_count} finding(s).",
            f"Highest severity is {severity}.",
            f"The review {blocker_text}.",
        ),
    )


def _freshness_section(
    projection: TradeReviewAgentProjection,
    actionability: PortfolioActionabilityDecision,
) -> TradeReviewExplanationSection:
    return TradeReviewExplanationSection(
        title="Freshness Boundary",
        bullets=(
            f"Broker snapshot freshness is {projection.portfolio_impact.broker_freshness_status}.",
            f"Market quote freshness is {projection.portfolio_impact.market_freshness_status}.",
            f"Review actionability status is {actionability.review_actionability_status}.",
        ),
    )


def _find_forbidden_keys(value: object, *, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.strip().lower() in FORBIDDEN_TRADE_REVIEW_AGENT_KEYS:
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
