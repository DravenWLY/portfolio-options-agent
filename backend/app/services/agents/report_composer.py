"""Deterministic report composer for Phase 16 agent outputs."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from app.schemas.reports import ReportMessageCreate
from app.services.agents.freshness_guardrail import FreshnessGuardrailAgentOutput
from app.services.agents.portfolio_context import PortfolioContextAgentOutput
from app.services.agents.trade_review import TradeReviewAgentOutput
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS


AGENT_NAME = "report_composer_agent"
COMPOSER_VERSION = "report-composer-v1"
FORBIDDEN_REPORT_COMPOSER_KEYS = FORBIDDEN_REPORT_FACT_KEYS | {
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
    "total_cash",
    "free_cash",
    "buying_power",
    "positions",
    "holdings",
}
PROHIBITED_REPORT_PHRASES = ("you should", "i recommend", "recommend buying", "recommend selling", "guaranteed")


@dataclass(frozen=True)
class ReportComposerAgentOutput:
    agent_name: str
    generated_at: datetime
    calculation_version: str
    title: str
    markdown: str
    source_agent_names: tuple[str, ...]
    deterministic_sections: tuple[str, ...]
    llm_generated_sections: tuple[str, ...]
    traceability: dict[str, Any]

    def to_report_message_create(self, *, sequence: int) -> ReportMessageCreate:
        """Return a report-history message payload ready for persistence."""

        self._validate_safe()
        return ReportMessageCreate(
            sender_type="agent",
            message_type="final_report",
            content_markdown=self.markdown,
            content_json={
                "generator": AGENT_NAME,
                "calculation_version": self.calculation_version,
                "source_agent_names": list(self.source_agent_names),
                "deterministic_sections": list(self.deterministic_sections),
                "llm_generated_sections": list(self.llm_generated_sections),
                "traceability": _json_safe(self.traceability),
            },
            sequence=sequence,
        )

    def _validate_safe(self) -> None:
        payload = asdict(self)
        forbidden = _find_forbidden_keys(payload)
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"report composer payload contains forbidden keys: {blocked}")
        rendered = repr(payload).lower()
        for phrase in PROHIBITED_REPORT_PHRASES:
            if phrase in rendered:
                raise ValueError(f"report composer payload contains prohibited phrase: {phrase}")


class ReportComposerAgent:
    """Compose approved deterministic agent outputs into a durable markdown report."""

    def run(
        self,
        *,
        portfolio_context: PortfolioContextAgentOutput,
        trade_review: TradeReviewAgentOutput,
        freshness_guardrail: FreshnessGuardrailAgentOutput,
        generated_at: datetime | None = None,
        title: str = "Portfolio Trade Review",
    ) -> ReportComposerAgentOutput:
        generated = generated_at or datetime.now(UTC)
        markdown = _render_markdown(
            title=title,
            generated_at=generated,
            portfolio_context=portfolio_context,
            trade_review=trade_review,
            freshness_guardrail=freshness_guardrail,
        )
        output = ReportComposerAgentOutput(
            agent_name=AGENT_NAME,
            generated_at=generated,
            calculation_version=COMPOSER_VERSION,
            title=title,
            markdown=markdown,
            source_agent_names=(
                portfolio_context.agent_name,
                trade_review.agent_name,
                freshness_guardrail.agent_name,
            ),
            deterministic_sections=(
                "portfolio_shape",
                "freshness_guardrails",
                "trade_review_explanation",
                "safety_boundary",
            ),
            llm_generated_sections=(),
            traceability={
                "review_actionability_status": freshness_guardrail.review_actionability_status,
                "broker_snapshot_scope": freshness_guardrail.broker_snapshot_scope,
                "market_quote_scope": freshness_guardrail.market_quote_scope,
                "broker_snapshot_status": freshness_guardrail.broker_snapshot_status,
                "market_quote_status": freshness_guardrail.market_quote_status,
                "trade_review_highest_severity": trade_review.highest_severity,
                "trade_review_has_blocker": trade_review.has_blocker,
            },
        )
        output._validate_safe()
        return output


def _render_markdown(
    *,
    title: str,
    generated_at: datetime,
    portfolio_context: PortfolioContextAgentOutput,
    trade_review: TradeReviewAgentOutput,
    freshness_guardrail: FreshnessGuardrailAgentOutput,
) -> str:
    guardrails = "\n".join(
        f"- [{guardrail.severity}] {guardrail.scope}/{guardrail.code}: {guardrail.message} "
        f"Remediation: {guardrail.remediation}"
        for guardrail in freshness_guardrail.guardrails
    )
    if not guardrails:
        guardrails = "- None"
    explanation_sections = []
    for section in trade_review.sections:
        bullets = "\n".join(f"- {bullet}" for bullet in section.bullets)
        explanation_sections.append(f"### {section.title}\n\n{bullets}")
    explanation_markdown = "\n\n".join(explanation_sections) if explanation_sections else "No explanation sections."

    shape = portfolio_context.portfolio_shape
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- Generated at: {generated_at.isoformat()}",
            f"- Source: deterministic backend agent outputs only",
            f"- Review actionability status: {freshness_guardrail.review_actionability_status}",
            f"- Highest deterministic risk severity: {trade_review.highest_severity or 'none'}",
            f"- Has deterministic blocker: {trade_review.has_blocker}",
            "",
            "## Portfolio Shape",
            "",
            f"- Cash context available: {shape.has_cash_context}",
            f"- Stock position count: {shape.stock_position_count}",
            f"- Option position count: {shape.option_position_count}",
            f"- Long option position count: {shape.long_option_position_count}",
            f"- Short option position count: {shape.short_option_position_count}",
            "",
            "## Freshness Guardrails",
            "",
            f"- Broker freshness scope: {freshness_guardrail.broker_snapshot_scope}",
            f"- Broker snapshot status: {freshness_guardrail.broker_snapshot_status}",
            f"- Market freshness scope: {freshness_guardrail.market_quote_scope}",
            f"- Market quote status: {freshness_guardrail.market_quote_status}",
            "",
            guardrails,
            "",
            "## Deterministic Trade Review Explanation",
            "",
            explanation_markdown,
            "",
            "## LLM Boundary",
            "",
            "- No LLM-generated sections are included in this report.",
            "- Future LLM text must explain structured deterministic outputs only.",
            "",
            "## Safety Boundary",
            "",
            "- Review and scenario analysis only.",
            "- This report does not recommend, place, route, or manage trades.",
            "- Broker snapshot freshness and market quote freshness are separate.",
        ]
    )


def _find_forbidden_keys(value: object, *, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.strip().lower() in FORBIDDEN_REPORT_COMPOSER_KEYS:
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


def _json_safe(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
