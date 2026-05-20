"""Context envelope contracts for portfolio-aware agent-team orchestration."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from app.schemas.actionability import PortfolioActionabilityDecision
from app.services.agents.roles import validate_role_envelope_compatibility
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys


ContextEnvelopeType: TypeAlias = Literal[
    "private_portfolio_safe_context",
    "deterministic_review_context",
    "actionability_context",
    "public_evidence_context",
    "llm_explanation_context",
    "report_composition_context",
]
ContextPrivacyTier: TypeAlias = Literal["app_private_safe", "public_safe", "llm_safe", "report_safe"]

CONTEXT_ENVELOPE_TYPES: tuple[str, ...] = (
    "private_portfolio_safe_context",
    "deterministic_review_context",
    "actionability_context",
    "public_evidence_context",
    "llm_explanation_context",
    "report_composition_context",
)
PUBLIC_OR_LLM_ENVELOPES = frozenset({"public_evidence_context", "llm_explanation_context"})


@dataclass(frozen=True)
class ContextEnvelope:
    envelope_type: ContextEnvelopeType
    privacy_tier: ContextPrivacyTier
    payload: dict[str, Any]
    allowed_role_names: tuple[str, ...]
    source_component: str
    source_version: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Return a defensive copy suitable for future agent-step snapshots."""

        return {
            "envelope_type": self.envelope_type,
            "privacy_tier": self.privacy_tier,
            "payload": deepcopy(self.payload),
            "allowed_role_names": list(self.allowed_role_names),
            "source_component": self.source_component,
            "source_version": self.source_version,
        }


def make_context_envelope(
    *,
    envelope_type: ContextEnvelopeType,
    payload: dict[str, Any],
    allowed_role_names: tuple[str, ...],
    source_component: str,
    source_version: str | None = None,
) -> ContextEnvelope:
    """Build an envelope and reject private broker/account fields by default."""

    validate_role_envelope_compatibility(
        envelope_type=envelope_type,
        allowed_role_names=tuple(allowed_role_names),
    )
    copied_payload = deepcopy(payload)
    _raise_if_forbidden(copied_payload, envelope_type=envelope_type)
    return ContextEnvelope(
        envelope_type=envelope_type,
        privacy_tier=_privacy_tier_for(envelope_type),
        payload=copied_payload,
        allowed_role_names=tuple(allowed_role_names),
        source_component=source_component,
        source_version=source_version,
    )


def make_actionability_context_envelope(
    *,
    decision: PortfolioActionabilityDecision,
    allowed_role_names: tuple[str, ...],
) -> ContextEnvelope:
    """Build an actionability envelope from the existing backend-owned policy decision."""

    return make_context_envelope(
        envelope_type="actionability_context",
        allowed_role_names=allowed_role_names,
        source_component="portfolio_actionability_policy",
        source_version=decision.policy_version,
        payload={
            "policy_version": decision.policy_version,
            "review_actionability_status": decision.review_actionability_status,
            "language_tier": decision.language_tier,
            "can_run_deterministic_review": decision.can_run_deterministic_review,
            "can_run_agent_explanation": decision.can_run_agent_explanation,
            "requires_user_confirmation": decision.requires_user_confirmation,
            "broker_snapshot": {
                "freshness_scope": decision.broker_snapshot.freshness_scope,
                "freshness_status": decision.broker_snapshot.freshness_status,
                "source": decision.broker_snapshot.source,
                "provider_status": decision.broker_snapshot.provider_status,
            },
            "market_quotes": {
                "freshness_scope": decision.market_quotes.freshness_scope,
                "freshness_status": decision.market_quotes.freshness_status,
                "data_mode": decision.market_quotes.data_mode,
                "actionability_status": decision.market_quotes.actionability_status,
                "provider_status": decision.market_quotes.provider_status,
            },
            "reasons": tuple(
                {
                    "code": reason.code,
                    "scope": reason.scope,
                    "severity": reason.severity,
                    "message": reason.message,
                }
                for reason in decision.reasons
            ),
        },
    )


def _privacy_tier_for(envelope_type: ContextEnvelopeType) -> ContextPrivacyTier:
    if envelope_type == "public_evidence_context":
        return "public_safe"
    if envelope_type == "llm_explanation_context":
        return "llm_safe"
    if envelope_type == "report_composition_context":
        return "report_safe"
    return "app_private_safe"


def _raise_if_forbidden(payload: dict[str, Any], *, envelope_type: ContextEnvelopeType) -> None:
    forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{envelope_type} contains forbidden private fields: {blocked}")
