"""Offline public evidence projection helpers for saved Agent Team reports."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.reports import SavedPublicEvidencePackageRead


@dataclass(frozen=True)
class PublicEvidenceProjectionRequest:
    symbol_or_underlying: str | None = None


class NoReviewedPublicEvidenceProvider:
    """Default provider boundary until public source rights are reviewed."""

    def snapshot(self, request: PublicEvidenceProjectionRequest) -> SavedPublicEvidencePackageRead:
        return SavedPublicEvidencePackageRead.not_reviewed(request.symbol_or_underlying)


def build_public_evidence_projection(
    *,
    symbol_or_underlying: str | None,
) -> SavedPublicEvidencePackageRead:
    """Build the default generation-time public evidence projection."""

    return NoReviewedPublicEvidenceProvider().snapshot(
        PublicEvidenceProjectionRequest(symbol_or_underlying=symbol_or_underlying)
    )
