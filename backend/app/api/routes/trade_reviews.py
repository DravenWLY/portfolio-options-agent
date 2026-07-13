from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Depends, Header
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import SavedDeterministicReviewSummaryRead, SavedEvidenceSectionRead, SavedReviewArtifactCreateRequest
from app.schemas.trade_review_workspace import (
    TradeReviewPortfolioPreviewRequest,
    TradeReviewWorkspacePreviewRequest,
    TradeReviewWorkspaceRead,
    ReportScopeMetadataRead,
)
from app.services.reports import crud as report_service
from app.services.trade_review.frontend_read import (
    build_trade_review_workspace_portfolio_preview,
    build_trade_review_workspace_preview,
)

router = APIRouter(prefix="/trade-reviews", tags=["trade-reviews"])

_SAVED_REVIEW_PRIVATE_CAVEAT_CODE_MAP: dict[str, str] = {
    "buying_power_display_only": "liquidity_model_unverified",
    "cash_collateral_policy_not_reviewed": "liquidity_model_unverified",
    "cash_collateral_not_fully_modelled": "liquidity_model_unverified",
    "cash_collateral_not_fully_modeled": "liquidity_model_unverified",
    "csp_collateral_unverified": "account_feasibility_not_evaluated",
    "covered_call_coverage_unverified": "account_feasibility_not_evaluated",
}
_SAVED_REVIEW_PRIVATE_CAVEAT_TOKENS = ("buying_power", "cash", "collateral")


@router.post("/preview", response_model=TradeReviewWorkspaceRead)
def preview_trade_review(payload: TradeReviewWorkspacePreviewRequest) -> TradeReviewWorkspaceRead:
    """Return a deterministic synthetic trade-review workspace preview."""

    return build_trade_review_workspace_preview(payload)


@router.post("/portfolio-preview", response_model=TradeReviewWorkspaceRead)
def preview_portfolio_trade_review(
    payload: TradeReviewPortfolioPreviewRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID | None = Header(default=None, alias="X-User-Id"),
) -> TradeReviewWorkspaceRead:
    """Return a deterministic portfolio-backed trade-review workspace preview."""

    derived_exposure_sections: list[SavedEvidenceSectionRead] = []

    def _capture_derived_exposure_sections(sections: tuple[object, ...]) -> None:
        derived_exposure_sections.clear()
        derived_exposure_sections.extend(
            section for section in sections if isinstance(section, SavedEvidenceSectionRead)
        )

    workspace = build_trade_review_workspace_portfolio_preview(
        payload,
        db=db,
        current_user_id=current_user_id,
        derived_exposure_sections_callback=_capture_derived_exposure_sections,
    )
    return _workspace_with_saved_review_source_reference(
        workspace,
        db=db,
        current_user_id=current_user_id,
        derived_exposure_sections=tuple(derived_exposure_sections),
    )


def _workspace_with_saved_review_source_reference(
    workspace: TradeReviewWorkspaceRead,
    *,
    db: Session,
    current_user_id: UUID | None,
    derived_exposure_sections: tuple[SavedEvidenceSectionRead, ...] = (),
) -> TradeReviewWorkspaceRead:
    if current_user_id is None or workspace.scope_metadata is None:
        return workspace

    source_reference = f"trrev_{uuid4().hex}"
    caveat_codes = _saved_review_safe_caveat_codes(workspace)
    try:
        create_request = SavedReviewArtifactCreateRequest(
            source_kind="trade_review_workspace",
            source_reference=source_reference,
            title=f"{_review_flow_label(workspace.supported_flow)} snapshot",
            report_type="trade_review",
            scope_metadata=_saved_review_safe_scope_metadata(workspace.scope_metadata),
            deterministic_summary=_deterministic_summary_from_workspace(
                workspace,
                caveat_codes=caveat_codes,
                derived_exposure_sections=derived_exposure_sections,
            ),
            generated_at=workspace.generated_at,
            limitations=("Saved review source generated from reviewed backend workspace output.",),
            caveat_codes=caveat_codes,
        )
    except (ValidationError, ValueError):
        return workspace
    source = report_service.record_saved_review_source(
        db,
        current_user_id,
        create_request,
    )
    if source is None:
        return workspace
    return workspace.model_copy(update={"saved_review_source_reference": source.source_reference})


def _saved_review_safe_scope_metadata(scope_metadata: ReportScopeMetadataRead) -> ReportScopeMetadataRead:
    portfolio_scope = scope_metadata.portfolio_context_scope.model_copy(
        update={
            "caveat_codes": _saved_review_safe_caveat_code_tuple(
                scope_metadata.portfolio_context_scope.caveat_codes
            )
        }
    )
    return scope_metadata.model_copy(
        update={
            "portfolio_context_scope": portfolio_scope,
            "scope_caveat_codes": _saved_review_safe_caveat_code_tuple(scope_metadata.scope_caveat_codes),
        }
    )


def _deterministic_summary_from_workspace(
    workspace: TradeReviewWorkspaceRead,
    *,
    caveat_codes: tuple[str, ...],
    derived_exposure_sections: tuple[SavedEvidenceSectionRead, ...] = (),
) -> SavedDeterministicReviewSummaryRead:
    return SavedDeterministicReviewSummaryRead(
        supported_flow=workspace.supported_flow,
        review_flow_label=_review_flow_label(workspace.supported_flow),
        symbol_or_underlying=workspace.trade_intent_summary.symbol or workspace.trade_intent_summary.underlying_symbol,
        review_actionability_status=workspace.actionability.review_actionability_status,
        actionability_label=_actionability_label(workspace.actionability.review_actionability_status),
        highest_severity=workspace.deterministic_review.highest_severity,
        report_status="generated",
        broker_snapshot_freshness_label=_broker_snapshot_freshness_label(workspace),
        market_quote_freshness_label=_market_quote_freshness_label(workspace),
        caveat_codes=caveat_codes,
        derived_exposure_sections=derived_exposure_sections,
    )


def _saved_review_safe_caveat_codes(workspace: TradeReviewWorkspaceRead) -> tuple[str, ...]:
    return _saved_review_safe_caveat_code_tuple(tuple(caveat.code for caveat in workspace.caveats))


def _saved_review_safe_caveat_code_tuple(caveat_codes: tuple[str, ...]) -> tuple[str, ...]:
    codes: list[str] = []
    seen: set[str] = set()
    for caveat_code in caveat_codes:
        safe_code = _saved_review_safe_caveat_code(caveat_code)
        if safe_code in seen:
            continue
        seen.add(safe_code)
        codes.append(safe_code)
    return tuple(codes)


def _saved_review_safe_caveat_code(code: str) -> str:
    lowered = code.strip().lower()
    mapped = _SAVED_REVIEW_PRIVATE_CAVEAT_CODE_MAP.get(lowered)
    if mapped is not None:
        return mapped
    if any(token in lowered for token in _SAVED_REVIEW_PRIVATE_CAVEAT_TOKENS):
        return "liquidity_model_unverified"
    return lowered


def _review_flow_label(flow: str) -> str:
    return {
        "stock_buy": "Stock buy review",
        "stock_sell_trim": "Stock sell/trim review",
        "etf_buy": "ETF buy review",
        "etf_sell_trim": "ETF sell/trim review",
        "covered_call": "Covered call review",
        "cash_secured_put": "Cash-secured put review",
    }.get(flow, "Trade review")


def _actionability_label(status: str) -> str:
    return {
        "normal_review": "Normal review",
        "analysis_only": "Analysis-only review",
        "manual_confirmation_required": "Manual confirmation required",
        "blocked_stale_broker_snapshot": "Blocked by stale broker snapshot",
        "blocked_stale_market_quote": "Blocked by stale market quote",
        "blocked_unknown_freshness": "Blocked by unknown freshness",
        "blocked_provider_error": "Blocked by provider error",
    }.get(status, "Review status unavailable")


def _broker_snapshot_freshness_label(workspace: TradeReviewWorkspaceRead) -> str:
    status = workspace.actionability.broker_snapshot.freshness_status.replace("_", " ")
    return f"Broker snapshot freshness: {status}"


def _market_quote_freshness_label(workspace: TradeReviewWorkspaceRead) -> str:
    status = workspace.actionability.market_quotes.freshness_status.replace("_", " ")
    return f"Market quote freshness: {status}"
