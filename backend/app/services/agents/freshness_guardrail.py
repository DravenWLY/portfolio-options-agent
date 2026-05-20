"""Freshness guardrail agent for broker snapshot and market quote boundaries."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.schemas.actionability import PortfolioActionabilityDecision
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS


AGENT_NAME = "freshness_guardrail_agent"
FORBIDDEN_GUARDRAIL_KEYS = FORBIDDEN_REPORT_FACT_KEYS | {
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


@dataclass(frozen=True)
class FreshnessGuardrail:
    code: str
    scope: str
    severity: str
    message: str
    remediation: str
    blocks_agent_explanation: bool


@dataclass(frozen=True)
class FreshnessGuardrailAgentOutput:
    agent_name: str
    generated_at: datetime
    review_actionability_status: str
    broker_snapshot_status: str
    market_quote_status: str
    broker_snapshot_scope: str
    market_quote_scope: str
    guardrails: tuple[FreshnessGuardrail, ...]

    def to_agent_step_output(self) -> dict:
        payload = asdict(self)
        forbidden = _find_forbidden_keys(payload)
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"freshness guardrail payload contains forbidden keys: {blocked}")
        return payload


class FreshnessGuardrailAgent:
    """Turn the backend-owned actionability decision into guardrail messages."""

    def run(
        self,
        *,
        actionability: PortfolioActionabilityDecision,
        generated_at: datetime | None = None,
    ) -> FreshnessGuardrailAgentOutput:
        generated = generated_at or datetime.now(UTC)
        guardrails = _guardrails_for(actionability)
        output = FreshnessGuardrailAgentOutput(
            agent_name=AGENT_NAME,
            generated_at=generated,
            review_actionability_status=actionability.review_actionability_status,
            broker_snapshot_status=actionability.broker_snapshot.freshness_status,
            market_quote_status=actionability.market_quotes.freshness_status,
            broker_snapshot_scope=actionability.broker_snapshot.freshness_scope,
            market_quote_scope=actionability.market_quotes.freshness_scope,
            guardrails=guardrails,
        )
        output.to_agent_step_output()
        return output


def _guardrails_for(actionability: PortfolioActionabilityDecision) -> tuple[FreshnessGuardrail, ...]:
    status = actionability.review_actionability_status
    if status == "normal_review":
        return (
            FreshnessGuardrail(
                code="normal_review_allowed",
                scope="review",
                severity="info",
                message="Broker snapshot and market quote metadata satisfy the current actionability policy.",
                remediation="Continue to label output as read-only manual decision support.",
                blocks_agent_explanation=False,
            ),
        )
    if status == "analysis_only":
        return (
            FreshnessGuardrail(
                code="analysis_only",
                scope="review",
                severity="warning",
                message="Review may proceed only as analysis based on the available snapshot.",
                remediation="Keep analysis-only language visible and avoid immediate-action wording.",
                blocks_agent_explanation=False,
            ),
        )
    if status == "manual_confirmation_required":
        return (
            FreshnessGuardrail(
                code="manual_confirmation_required",
                scope="review",
                severity="warning",
                message="Manual, CSV, synthetic/mock, cached, delayed, or EOD input requires explicit confirmation.",
                remediation="Request user confirmation before deterministic review or agent explanation proceeds.",
                blocks_agent_explanation=True,
            ),
        )
    if status == "blocked_stale_broker_snapshot":
        return (
            FreshnessGuardrail(
                code="broker_snapshot_stale",
                scope="broker_snapshot",
                severity="blocker",
                message="Broker portfolio snapshot is stale and cannot be presented as immediately actionable.",
                remediation="Refresh broker holdings or use an approved manual/CSV confirmation workflow before review.",
                blocks_agent_explanation=True,
            ),
        )
    if status == "blocked_stale_market_quote":
        return (
            FreshnessGuardrail(
                code="market_quote_stale",
                scope="market_quote",
                severity="blocker",
                message="Market quote snapshot is stale and cannot support current quote-based review.",
                remediation="Refresh market quote inputs or continue only with clearly labelled stale analysis.",
                blocks_agent_explanation=True,
            ),
        )
    if status == "blocked_unknown_freshness":
        return (
            FreshnessGuardrail(
                code="unknown_freshness",
                scope="review",
                severity="blocker",
                message="Broker or market freshness metadata is unknown.",
                remediation="Provide explicit broker and market freshness metadata before review proceeds.",
                blocks_agent_explanation=True,
            ),
        )
    return (
        FreshnessGuardrail(
            code="provider_error",
            scope="review",
            severity="blocker",
            message="A required broker or market provider is unavailable, in error, or requires reauthorization.",
            remediation="Resolve provider status before account-specific review.",
            blocks_agent_explanation=True,
        ),
    )


def _find_forbidden_keys(value: object, *, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.strip().lower() in FORBIDDEN_GUARDRAIL_KEYS:
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
