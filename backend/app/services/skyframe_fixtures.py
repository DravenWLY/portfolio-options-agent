"""Private-safe synthetic fixture overlay for connected Skyframe smoke tests.

Boundary: this middleware is a stateless, header-gated UI smoke harness. It must
not become canonical demo data, persist rows, call providers, or depend on the
Golden Path DB seed. The route-driven founder demo belongs in
``app.services.golden_path_demo_seed`` and real app storage.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
import hmac
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.access_guard import LOCAL_ACCESS_HEADER
from app.core.config import Settings, get_settings


SKYFRAME_FIXTURE_HEADER = "X-Skyframe-Fixture"
SKYFRAME_FIXTURE_HEADER_VALUE = "private-safe-v1"
SKYFRAME_DASHBOARD_STATE_HEADER = "X-Skyframe-Dashboard-State"
SKYFRAME_DEMO_NOTICE = "demo · skyframe private-safe fixture"
SKYFRAME_DEMO_USER_ID = "11111111-1111-4111-8111-111111111111"
SKYFRAME_DEMO_ACCOUNT_ID = "66666666-6666-4666-8666-666666666666"
SKYFRAME_SOURCE_REPORT_ID = "22222222-2222-4222-8222-222222222222"
SKYFRAME_FULL_REPORT_ID = "33333333-3333-4333-8333-333333333333"
SKYFRAME_DRAFT_REPORT_ID = "77777777-7777-4777-8777-777777777777"
SKYFRAME_UNAVAILABLE_REPORT_ID = "44444444-4444-4444-8444-444444444444"
SKYFRAME_FAILED_REPORT_ID = "55555555-5555-4555-8555-555555555555"
SKYFRAME_GOLDEN_SOURCE_REFERENCE = "trrev_skyframe_demo_review"
SKYFRAME_GOLDEN_ARTIFACT_REFERENCE = "svrev_skyframe_demo_review"

_ALLOWED_APP_ENVS = {"local", "dev", "development", "test", "testing"}
_ALLOWED_DASHBOARD_STATES = {"unavailable", "populated", "empty"}
_NOW = "2026-06-19T15:00:00Z"
_TODAY = "2026-06-19"


class SkyframeFixtureMiddleware(BaseHTTPMiddleware):
    """Serve fixed synthetic payloads for explicitly gated connected smoke runs."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        fixture_response = await skyframe_fixture_response(request, get_settings())
        if fixture_response is not None:
            return fixture_response
        return await call_next(request)


async def skyframe_fixture_response(request: Request, settings: Settings) -> JSONResponse | None:
    """Return a fixture response when the explicit private-safe smoke gates are satisfied."""

    if not _fixture_active(request, settings):
        return None

    path = request.url.path.rstrip("/") or "/"
    dashboard_state = request.headers.get(SKYFRAME_DASHBOARD_STATE_HEADER, "unavailable")
    if dashboard_state not in _ALLOWED_DASHBOARD_STATES:
        if _is_smoke_surface(path):
            return JSONResponse(
                {
                    "detail": "Unsupported Skyframe Dashboard fixture state.",
                    "data_mode": "synthetic_demo",
                    "demo_notice": SKYFRAME_DEMO_NOTICE,
                },
                status_code=400,
            )
        return None

    if request.method != "GET":
        post_response = await _fixture_post_response_for_path(request, path)
        if post_response is not None:
            return post_response
        if _is_smoke_surface(path):
            return JSONResponse(
                {
                    "detail": "This method is not available in the Skyframe private-safe fixture.",
                    "data_mode": "synthetic_demo",
                    "demo_notice": SKYFRAME_DEMO_NOTICE,
                },
                status_code=405,
            )
        return None

    payload = _fixture_payload_for_path(path, dashboard_state)
    if payload is not None:
        return JSONResponse(payload)

    if _is_smoke_surface(path):
        return JSONResponse(
            {
                "detail": "Skyframe fixture data is not available for this smoke path.",
                "data_mode": "synthetic_demo",
                "demo_notice": SKYFRAME_DEMO_NOTICE,
            },
            status_code=404,
        )
    return None


async def _fixture_post_response_for_path(request: Request, path: str) -> JSONResponse | None:
    if path == "/trade-reviews/portfolio-preview":
        body = await _safe_json_body(request)
        payload = _portfolio_preview_fixture(body)
        if payload is None:
            return _fixture_not_found("Skyframe fixture trade review source is not available.")
        return JSONResponse(payload)

    parts = path.strip("/").split("/")
    if len(parts) == 4 and parts[0] == "users" and parts[2:] == ["reports", "from-trade-review"]:
        body = await _safe_json_body(request)
        payload = _saved_review_artifact_fixture(body, include_agent_summary=False)
        if payload is None:
            return _fixture_not_found("Skyframe fixture saved review source is not available.")
        return JSONResponse(payload, status_code=201)

    if (
        len(parts) == 5
        and parts[0] == "users"
        and parts[2] == "reports"
        and parts[4] == "agent-team-report"
    ):
        if parts[3] not in {SKYFRAME_SOURCE_REPORT_ID, SKYFRAME_FULL_REPORT_ID}:
            return _fixture_not_found("Skyframe fixture saved report is not available.")
        return JSONResponse(_saved_review_artifact_fixture({}, include_agent_summary=True), status_code=201)

    return None


async def _safe_json_body(request: Request) -> dict[str, Any] | None:
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _fixture_not_found(detail: str) -> JSONResponse:
    return JSONResponse(
        {
            "detail": detail,
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
        },
        status_code=404,
    )


def _fixture_active(request: Request, settings: Settings) -> bool:
    if not settings.skyframe_fixtures_enabled:
        return False
    if settings.app_env.strip().lower() not in _ALLOWED_APP_ENVS:
        return False
    if request.headers.get(SKYFRAME_FIXTURE_HEADER) != SKYFRAME_FIXTURE_HEADER_VALUE:
        return False
    expected_token = settings.local_dev_access_token
    supplied_token = request.headers.get(LOCAL_ACCESS_HEADER)
    if not expected_token or supplied_token is None:
        return False
    return hmac.compare_digest(supplied_token, expected_token)


def _fixture_payload_for_path(path: str, dashboard_state: str) -> Any | None:
    if path == "/users":
        return [_user()]
    if path == "/market-context/market-mood":
        return _market_mood(dashboard_state)
    if path == "/market-context/market-mood/detail":
        return _market_mood_detail()
    if path == "/economic-calendar/events":
        return _economic_calendar_events(dashboard_state)

    users_parts = path.strip("/").split("/")
    if len(users_parts) >= 2 and users_parts[0] == "users":
        tail = users_parts[2:]
        if tail == ["accounts"]:
            return [_account()]
        if tail == ["reports"]:
            return _reports_list()
        if len(tail) == 2 and tail[0] == "reports":
            return _report_detail(tail[1])
        if tail == ["trade-reviews"]:
            return _trade_reviews(dashboard_state)
        if tail == ["risk-alerts"]:
            return _risk_alerts(dashboard_state)
        if tail == ["readiness"]:
            return _readiness(dashboard_state)
        if tail == ["dashboard-account-summary"]:
            return _dashboard_account_summary(dashboard_state)
        if tail == ["portfolio-contexts"]:
            return _portfolio_contexts(dashboard_state)
    return None


def _is_smoke_surface(path: str) -> bool:
    return (
        path == "/users"
        or path.startswith("/users/")
        or path.startswith("/market-context/")
        or path.startswith("/economic-calendar/")
        or path.startswith("/trade-reviews")
    )


def _user() -> dict[str, Any]:
    return {
        "id": SKYFRAME_DEMO_USER_ID,
        "display_name": "Skyframe Demo User",
        "email": "skyframe-demo@example.com",
        "auth_provider": "skyframe_fixture",
        "is_active": True,
        "created_at": _NOW,
        "updated_at": _NOW,
        "deleted_at": None,
    }


def _account() -> dict[str, Any]:
    return {
        "id": SKYFRAME_DEMO_ACCOUNT_ID,
        "user_id": SKYFRAME_DEMO_USER_ID,
        "broker_name": "Skyframe Demo Broker",
        "account_type": "taxable_individual",
        "display_name": "Synthetic demo account",
        "base_currency": "USD",
        "is_manual": True,
        "created_at": _NOW,
        "updated_at": _NOW,
        "deleted_at": None,
    }


def _portfolio_preview_fixture(body: dict[str, Any] | None) -> dict[str, Any] | None:
    if body is None:
        return None
    supported_flow = body.get("supported_flow")
    if supported_flow in {"stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"}:
        if not body.get("symbol") or body.get("quantity") is None or body.get("price_assumption") is None:
            return None
        return _trade_review_workspace("stock_buy")
    if supported_flow in {"cash_secured_put", "covered_call"} and isinstance(body.get("option_leg"), dict):
        return _trade_review_workspace("cash_secured_put")
    return None


def _trade_review_workspace(flow: str) -> dict[str, Any]:
    is_option = flow == "cash_secured_put"
    trade_intent = (
        {
            "intent_id": "intent_skyframe_option",
            "supported_flow": "cash_secured_put",
            "asset_class": "option",
            "intent_type": "cash_secured_put",
            "status": "analysis_only",
            "symbol": None,
            "action": None,
            "quantity": None,
            "price_assumption": None,
            "strategy_type": "cash_secured_put",
            "underlying_symbol": "SPY",
            "legs": [
                {
                    "underlying_symbol": "SPY",
                    "option_type": "put",
                    "leg_action": "sell_to_open",
                    "expiration_date": "2026-09-18",
                    "strike": "400",
                    "quantity": "1",
                    "premium": "1",
                    "multiplier": "100",
                    "occ_symbol": None,
                    "support_status": "manual_review_required",
                    "unsupported_reason": None,
                }
            ],
        }
        if is_option
        else {
            "intent_id": "intent_skyframe_equity",
            "supported_flow": "stock_buy",
            "asset_class": "stock",
            "intent_type": "stock_buy",
            "status": "analysis_only",
            "symbol": "SPY",
            "action": "buy_to_review",
            "quantity": "1",
            "price_assumption": "100",
            "strategy_type": None,
            "underlying_symbol": None,
            "legs": [],
        }
    )
    return {
        "review_reference": "trv_skyframe_demo_review",
        "saved_review_source_reference": SKYFRAME_GOLDEN_SOURCE_REFERENCE,
        "generated_at": _NOW,
        "calculation_version": "skyframe-fixture-v1",
        "supported_flow": trade_intent["supported_flow"],
        "trade_intent_summary": trade_intent,
        "portfolio_context": _portfolio_context_summary(),
        "scope_metadata": _scope_metadata(),
        "actionability": _actionability_decision(),
        "deterministic_review": _deterministic_review(is_option=is_option),
        "agent_orchestration": {
            "run_reference": "agentrun_skyframe_demo",
            "workflow_version": "skyframe-fixture-v1",
            "review_actionability_status": "manual_confirmation_required",
            "stage_order": ["deterministic_review", "agent_team_report"],
            "stage_statuses": {
                "deterministic_review": "completed",
                "agent_team_report": "manual_generation_pending",
            },
            "unavailable_stages": {},
            "source_agent_names": ["deterministic_template"],
            "report_composed": False,
        },
        "report_output": {
            "title": "Skyframe synthetic review snapshot",
            "content_markdown": "Synthetic fixture review snapshot for private-safe smoke.",
            "deterministic_sections": ["scope", "freshness", "caveats"],
            "llm_generated_sections": [],
            "source_agent_names": ["deterministic_template"],
        },
        "caveats": _workspace_caveats(is_option=is_option),
    }


def _portfolio_context_summary() -> dict[str, Any]:
    return {
        "context_reference": "ctx_skyframe_demo",
        "context_source": "synthetic_mock",
        "selection_mode": "latest_available",
        "summary_as_of": _NOW,
        "latest_snapshot_as_of": _NOW,
        "broker_snapshot": _broker_snapshot(),
        "stock_position_count": 0,
        "option_position_count": 0,
        "cash_state": "not_exposed",
        "label": "Skyframe synthetic context",
    }


def _broker_snapshot() -> dict[str, Any]:
    return {
        "source": "synthetic_mock",
        "freshness_scope": "broker_snapshot",
        "freshness_status": "fresh",
        "sync_status": "fixture",
        "as_of": _NOW,
        "received_at": _NOW,
        "last_successful_sync_at": _NOW,
        "provider_status": "not_applicable",
        "sanitized_error_code": None,
        "retryable": None,
    }


def _market_quotes() -> dict[str, Any]:
    return {
        "freshness_scope": "market_quote",
        "freshness_status": "fresh",
        "data_mode": "manual",
        "actionability_status": "manual_review_required",
        "as_of_min": _NOW,
        "as_of_max": _NOW,
        "received_at_min": _NOW,
        "received_at_max": _NOW,
        "provider_status": "not_applicable",
        "sanitized_error_code": None,
        "retryable": None,
    }


def _actionability_decision() -> dict[str, Any]:
    return {
        "policy_version": "skyframe-fixture-v1",
        "evaluated_at": _NOW,
        "review_actionability_status": "manual_confirmation_required",
        "can_run_deterministic_review": True,
        "can_run_agent_explanation": True,
        "requires_user_confirmation": True,
        "language_tier": "analysis_only",
        "broker_snapshot": _broker_snapshot(),
        "market_quotes": _market_quotes(),
        "reasons": [
            {
                "code": "synthetic_fixture_manual_review",
                "scope": "review",
                "severity": "info",
                "message": "Synthetic fixture requires manual review.",
            }
        ],
        "user_confirmation": {
            "state": "unconfirmed",
            "confirmed_at": None,
            "expires_at": None,
            "confirmation_scope": "review",
        },
    }


def _deterministic_review(*, is_option: bool) -> dict[str, Any]:
    return {
        "highest_severity": "info",
        "has_blocker": False,
        "portfolio_impact": {
            "broker_freshness_status": "fresh",
            "market_freshness_status": "fresh",
            "market_manual_review_required": True,
            "concentration_symbol": "SPY",
            "notes": ["Synthetic fixture portfolio impact is for smoke review only."],
        },
        "cash_collateral_impact": {
            "estimated_trade_cash_change": None,
            "estimated_premium_cash_change": None,
            "estimated_collateral_requirement_change": None,
            "projected_free_cash_state": "not_exposed",
            "notes": ["Synthetic fixture does not expose liquidity amounts."],
        },
        "concentration_allocation_impact": {
            "concentration_symbol": "SPY",
            "estimated_concentration_value_change": None,
            "allocation_drift_status": "not_modelled_in_phase_18a",
            "notes": ["Synthetic fixture does not model allocation drift."],
        },
        "options_exposure": {
            "underlying_symbol": "SPY" if is_option else None,
            "assignment_share_delta": "not_exposed",
            "exercise_share_delta": "not_exposed",
            "covered_call_coverage_model": "not_applicable",
            "cash_secured_put_collateral_model": "generic_rule_only" if is_option else "not_applicable",
            "notes": ["Synthetic fixture option exposure remains caveated."],
        },
        "risk_rule_violations": [],
        "missing_data_warnings": [
            {
                "code": "synthetic_fixture_manual_review",
                "scope": "review",
                "severity": "info",
                "message": "Synthetic fixture has no private brokerage data.",
            }
        ],
        "scenario_payoff_summary": {
            "points": [],
            "max_loss": None,
            "max_gain": None,
            "calculation_notes": ["Synthetic fixture omits payoff amounts."],
        },
    }


def _workspace_caveats(*, is_option: bool) -> list[dict[str, Any]]:
    caveats = [
        {
            "code": "synthetic_fixture",
            "severity": "info",
            "applies_to": "review",
            "message": "Synthetic fixture payload for private-safe smoke only.",
        },
        {
            "code": "account_level_feasibility_not_evaluated",
            "severity": "info",
            "applies_to": "scope",
            "message": "Account-level feasibility is not evaluated in this fixture.",
        },
    ]
    if is_option:
        caveats.append(
            {
                "code": "csp_collateral_unverified",
                "severity": "info",
                "applies_to": "options",
                "message": "Option collateral remains unverified in this fixture.",
            }
        )
    return caveats


def _reports_list() -> list[dict[str, Any]]:
    return [
        _report_thread(SKYFRAME_SOURCE_REPORT_ID, "Saved source snapshot", None),
        _report_thread(SKYFRAME_FULL_REPORT_ID, "Agent Team report", _agent_summary("full_agent_report")),
        _report_thread(SKYFRAME_DRAFT_REPORT_ID, "Deterministic draft report", _agent_summary("deterministic_draft")),
        _report_thread(SKYFRAME_UNAVAILABLE_REPORT_ID, "Agent unavailable report", _agent_summary("agent_unavailable")),
        _report_thread(SKYFRAME_FAILED_REPORT_ID, "Validation failed report", _agent_summary("validation_failed")),
    ]


def _report_detail(thread_id: str) -> dict[str, Any] | None:
    reports = {item["id"]: item for item in _reports_list()}
    report = reports.get(thread_id)
    if report is None:
        return None
    return {**report, "messages": []}


def _saved_review_artifact_fixture(
    body: dict[str, Any] | None,
    *,
    include_agent_summary: bool,
) -> dict[str, Any] | None:
    if body is None:
        return None
    if not include_agent_summary and not body:
        return None
    if body:
        allowed_body = {
            "source_kind": "trade_review_workspace",
            "source_reference": SKYFRAME_GOLDEN_SOURCE_REFERENCE,
            "title": body.get("title"),
            "report_type": body.get("report_type", "saved_review_artifact"),
        }
        if body != allowed_body or not isinstance(body.get("title"), str):
            return None
    return {
        "artifact_reference": SKYFRAME_GOLDEN_ARTIFACT_REFERENCE,
        "source_kind": "trade_review_workspace",
        "source_reference": SKYFRAME_GOLDEN_SOURCE_REFERENCE,
        "status": "saved",
        "report": {
            "report_reference": SKYFRAME_GOLDEN_ARTIFACT_REFERENCE,
            "title": "Skyframe synthetic saved review",
            "report_type": "saved_review_artifact",
            "status": "completed",
            "created_at": _NOW,
            "updated_at": _NOW,
        },
        "scope_metadata": _scope_metadata(),
        "deterministic_summary": _deterministic_summary(),
        "agent_summary": _agent_summary("full_agent_report") if include_agent_summary else None,
        "public_evidence": None,
        "generated_at": _NOW,
        "saved_at": _NOW,
        "review_pipeline_label": "Portfolio Copilot review pipeline",
        "limitations": ["Synthetic fixture saved review artifact for private-safe smoke only."],
        "caveat_codes": ["synthetic_fixture", "account_feasibility_not_evaluated"],
    }


def _report_thread(thread_id: str, title: str, agent_summary: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "id": thread_id,
        "user_id": SKYFRAME_DEMO_USER_ID,
        "account_id": None,
        "title": title,
        "report_type": "saved_review_artifact",
        "status": "completed",
        "created_at": _NOW,
        "updated_at": _NOW,
        "deleted_at": None,
        "scope_metadata": _scope_metadata(),
        "agent_summary": agent_summary,
    }


def _deterministic_summary() -> dict[str, Any]:
    return {
        "supported_flow": "cash_secured_put",
        "review_flow_label": "Cash-secured put review",
        "symbol_or_underlying": "SPY",
        "review_actionability_status": "manual_confirmation_required",
        "actionability_label": "Manual confirmation required",
        "highest_severity": "info",
        "report_status": "generated",
        "broker_snapshot_freshness_label": "Synthetic fixture broker snapshot",
        "market_quote_freshness_label": "Synthetic fixture market context",
        "caveat_codes": ["synthetic_fixture", "account_feasibility_not_evaluated"],
    }


def _agent_summary(report_status: str) -> dict[str, Any]:
    if report_status == "full_agent_report":
        run_status = "completed"
        role_summaries = [
            _agent_role_summary(
                "risk_management_agent",
                "Risk Manager",
                "completed",
                "Risk Manager briefing: synthetic deterministic risk flags, freshness categories, scope caveats, and option-exposure caveats are visible for smoke review.",
                ("trade_intent_summary", "scope_state", "actionability", "freshness"),
            ),
            _agent_role_summary(
                "portfolio_manager_agent",
                "Portfolio Manager",
                "completed",
                "Portfolio Manager briefing: synthetic smoke content groups deterministic risk flags, data freshness gaps, scope and feasibility caveats, and context not reviewed.",
                ("trade_intent_summary", "scope_state", "actionability", "freshness"),
            ),
        ]
        final = (
            "What you would be ignoring if you acted manually now: deterministic risk flags from the synthetic saved review; "
            "data freshness and availability gaps; scope and feasibility caveats; and context not reviewed in this private-safe fixture. "
            "Manual verification checklist: review the saved scope, freshness categories, feasibility caveats, option-leg mechanics, "
            "and missing public context before acting on your own. This is read-only fixture context for visual smoke."
        )
        evidence_refs: tuple[str, ...] = ("trade_intent_summary", "scope_state", "actionability")
        warning_codes: list[str] = []
    elif report_status == "deterministic_draft":
        run_status = "failed"
        role_summaries = [
            _agent_role_summary(role_name, display_name, "gated", None, ())
            for role_name, display_name in (
                ("fundamentals_analyst", "Fundamentals Analyst"),
                ("news_analyst", "News Analyst"),
                ("technical_analyst", "Technical Analyst"),
                ("risk_management_agent", "Risk Manager"),
                ("portfolio_manager_agent", "Portfolio Manager"),
            )
        ]
        final = (
            "What you would be ignoring if you acted manually now: the synthetic deterministic review did not complete because the actionability gate stopped the specialist briefing. "
            "Deterministic fixture evidence remains attached for audit. Manual verification checklist: review freshness categories, scope caveats, feasibility caveats, "
            "and option-leg mechanics in the saved fixture evidence before acting on your own. This is read-only fixture context for visual smoke."
        )
        evidence_refs = ("trade_intent_summary", "scope_state", "actionability")
        warning_codes = ["blocked_actionability_llm_roles_skipped"]
    elif report_status == "validation_failed":
        run_status = "failed"
        role_summaries = [_agent_role_summary("portfolio_manager_agent", "Portfolio Manager", "validation_failed", None, ())]
        final = None
        evidence_refs = ()
        warning_codes = ["fixture_degraded_state"]
    else:
        run_status = "failed"
        role_summaries = [_agent_role_summary("portfolio_manager_agent", "Portfolio Manager", "unavailable", None, ())]
        final = None
        evidence_refs = ()
        warning_codes = ["fixture_degraded_state"]
    return {
        "run_status": run_status,
        "provider_mode": "synthetic_fixture",
        "report_generated_at": _NOW,
        "role_summaries": role_summaries,
        "warning_codes": warning_codes,
        "report_status": report_status,
        "final_synthesis_markdown": final,
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_saved_evidence_v1",
        "evidence_references": list(evidence_refs),
    }


def _agent_role_summary(
    role_name: str,
    display_name: str,
    role_status: str,
    summary_markdown: str | None,
    evidence_references: tuple[str, ...],
) -> dict[str, Any]:
    degraded = summary_markdown is None
    warning_codes = ["blocked_actionability_llm_roles_skipped"] if role_status == "gated" else []
    if degraded and role_status != "gated":
        warning_codes = ["fixture_degraded_state"]
    return {
        "role_name": role_name,
        "display_name": display_name,
        "role_status": role_status,
        "provider_status": "synthetic_fixture" if role_status == "completed" else "skipped",
        "summary_markdown": summary_markdown,
        "evidence_references": list(evidence_references),
        "warning_codes": warning_codes,
        "unavailable_reason": None if not degraded else warning_codes[0],
    }


def _scope_metadata() -> dict[str, Any]:
    return {
        "review_account": None,
        "portfolio_context_scope": {
            "scope_reference": "scope_skyframe_demo",
            "scope_mode": "unavailable",
            "display_label": "Portfolio scope: Skyframe synthetic fixture",
            "selection_mode": None,
            "context_reference": None,
            "included_account_labels": [],
            "excluded_account_labels": [],
            "account_level_feasibility_evaluated": False,
            "account_level_feasibility_label": "Account-level feasibility not evaluated.",
            "caveat_codes": ["synthetic_fixture"],
        },
        "scope_summary_label": "Skyframe synthetic fixture scope.",
        "account_level_feasibility_evaluated": False,
        "scope_caveat_codes": ["synthetic_fixture"],
    }


def _trade_reviews(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "empty":
        return {
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "items": [],
        }
    return {
        "data_mode": "synthetic_demo",
        "demo_notice": SKYFRAME_DEMO_NOTICE,
        "items": [
            {
                "review_reference": "trv_skyframe_demo",
                "created_at": _NOW,
                "supported_flow": "cash_secured_put",
                "review_flow_label": "Cash-secured put review",
                "symbol_or_underlying": "SPY",
                "review_actionability_status": "analysis_only",
                "highest_severity": "info",
                "report_status": "preview_only",
                "source_mode": "synthetic_preview",
                "broker_snapshot_freshness_label": "Synthetic fixture snapshot",
                "market_quote_freshness_label": "Synthetic fixture market context",
            }
        ],
    }


def _risk_alerts(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "empty":
        return {
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "items": [],
        }
    return {
        "data_mode": "synthetic_demo",
        "demo_notice": SKYFRAME_DEMO_NOTICE,
        "items": [
            {
                "alert_reference": "risk_skyframe_demo",
                "generated_at": _NOW,
                "severity": "info",
                "category": "missing_data",
                "title": "Synthetic fixture readiness note",
                "summary": "Connected smoke uses private-safe fixture data only.",
                "related_symbol_or_underlying": None,
                "related_review_reference": None,
                "freshness_scope": "review",
                "is_blocking": False,
            }
        ],
    }


def _readiness(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "populated":
        return {
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "generated_at": _NOW,
            "overall_review_mode": "analysis_only",
            "broker_snapshot": {
                "freshness_scope": "broker_snapshot",
                "status": "fresh",
                "as_of_label": "Synthetic fixture as of Jun 19, 2026",
                "reason_codes": ["synthetic_fixture"],
                "display_label": "Synthetic fixture broker snapshot",
                "is_blocking": False,
            },
            "market_quotes": {
                "freshness_scope": "market_quote",
                "status": "fresh",
                "as_of_label": "Synthetic fixture as of Jun 19, 2026",
                "reason_codes": ["synthetic_fixture"],
                "display_label": "Synthetic fixture market context",
                "is_blocking": False,
            },
            "agent_provider": {
                "provider_mode": "mock",
                "provider_status": "mock_default",
                "is_mock_default": True,
                "last_checked_at": _NOW,
                "display_label": "Synthetic fixture agent provider",
                "is_blocking": False,
            },
            "recommended_user_action_label": "Synthetic fixture supports visual review only.",
        }
    if dashboard_state == "empty":
        return {
            **_readiness("unavailable"),
            "recommended_user_action_label": "No synthetic Dashboard data is available in this fixture state.",
        }
    return {
        "data_mode": "synthetic_demo",
        "demo_notice": SKYFRAME_DEMO_NOTICE,
        "generated_at": _NOW,
        "overall_review_mode": "analysis_only",
        "broker_snapshot": {
            "freshness_scope": "broker_snapshot",
            "status": "unavailable",
            "as_of_label": None,
            "reason_codes": ["synthetic_fixture"],
            "display_label": "Synthetic fixture broker snapshot unavailable",
            "is_blocking": False,
        },
        "market_quotes": {
            "freshness_scope": "market_quote",
            "status": "unavailable",
            "as_of_label": None,
            "reason_codes": ["synthetic_fixture"],
            "display_label": "Synthetic fixture market quotes unavailable",
            "is_blocking": False,
        },
        "agent_provider": {
            "provider_mode": "mock",
            "provider_status": "mock_default",
            "is_mock_default": True,
            "last_checked_at": _NOW,
            "display_label": "Synthetic fixture agent provider",
            "is_blocking": False,
        },
        "recommended_user_action_label": "Use fixture data for visual smoke only.",
    }


def _freshness(
    scope: str,
    label: str,
    *,
    status: str = "unavailable",
    as_of_label: str | None = None,
) -> dict[str, Any]:
    return {
        "freshness_scope": scope,
        "status": status,
        "as_of_label": as_of_label,
        "display_label": label,
        "reason_codes": ["synthetic_fixture"],
        "is_blocking": False,
    }


def _portfolio_shape(*, stock_count: int = 0, option_count: int = 0) -> dict[str, int]:
    return {"stock_position_count": stock_count, "option_position_count": option_count}


def _dashboard_account_summary(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "populated":
        return {
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "generated_at": _NOW,
            "summary_reference": "das_skyframe_populated",
            "display_scope": "synthetic_demo",
            "source_label": "Skyframe populated synthetic fixture",
            "valuation_basis": "indicative",
            "broker_snapshot_freshness": _freshness(
                "broker_snapshot",
                "Synthetic fixture broker snapshot",
                status="fresh",
                as_of_label="Synthetic fixture as of Jun 19, 2026",
            ),
            "market_quote_freshness": _freshness(
                "market_quote",
                "Synthetic fixture market context",
                status="fresh",
                as_of_label="Synthetic fixture as of Jun 19, 2026",
            ),
            "market_data_mode": "synthetic",
            "privacy_display_mode": "amounts_hidden",
            "market_data_unavailable": False,
            "portfolio_shape": _portfolio_shape(stock_count=4, option_count=2),
            "cash_state": "available",
            "cash_state_label": "Synthetic cash-state example available",
            "total_value_label": None,
            "cash_label": None,
            "stock_etf_exposure_label": None,
            "options_exposure_label": None,
            "collateral_usage_label": None,
            "portfolio_shape_label": "Synthetic mix: stocks, ETFs, and listed options",
            "position_count_label": "6 synthetic position summaries",
            "stock_exposure_label": None,
            "option_exposure_label": None,
            "caveat_codes": ["synthetic_fixture", "amounts_hidden"],
            "display_sections": [
                {
                    "section_key": "shape",
                    "title": "Synthetic portfolio shape",
                    "display_label": "Four stock or ETF summaries and two option summaries.",
                },
                {
                    "section_key": "caveats",
                    "title": "Fixture boundary",
                    "display_label": "No private financial rows are loaded.",
                },
            ],
        }
    if dashboard_state == "empty":
        return {
            **_dashboard_account_summary("unavailable"),
            "summary_reference": "das_skyframe_empty",
            "source_label": "Skyframe empty synthetic fixture",
            "cash_state": "unavailable",
            "cash_state_label": "No synthetic cash-state summary",
            "total_value_label": None,
            "cash_label": None,
            "stock_etf_exposure_label": None,
            "options_exposure_label": None,
            "collateral_usage_label": None,
            "portfolio_shape_label": "No synthetic portfolio summaries",
            "position_count_label": "0 synthetic position summaries",
            "stock_exposure_label": None,
            "option_exposure_label": None,
            "caveat_codes": ["synthetic_fixture", "empty_fixture_state"],
            "display_sections": [],
        }
    return {
        "data_mode": "synthetic_demo",
        "demo_notice": SKYFRAME_DEMO_NOTICE,
        "generated_at": _NOW,
        "summary_reference": "das_skyframe_demo",
        "display_scope": "synthetic_demo",
        "source_label": "Skyframe synthetic fixture",
        "valuation_basis": "unavailable",
        "broker_snapshot_freshness": _freshness("broker_snapshot", "Synthetic fixture broker snapshot unavailable"),
        "market_quote_freshness": _freshness("market_quote", "Synthetic fixture market quotes unavailable"),
        "market_data_mode": "unavailable",
        "privacy_display_mode": "amounts_hidden",
        "market_data_unavailable": True,
        "portfolio_shape": _portfolio_shape(),
        "cash_state": "not_exposed",
        "cash_state_label": "Cash not exposed in fixture",
        "total_value_label": "Value hidden",
        "cash_label": "Cash hidden",
        "stock_etf_exposure_label": "Stock/ETF exposure not shown",
        "options_exposure_label": "Options exposure not shown",
        "collateral_usage_label": "Collateral model not evaluated",
        "portfolio_shape_label": "No private holdings loaded",
        "position_count_label": "0 fixture positions",
        "stock_exposure_label": "Stock/ETF exposure not shown",
        "option_exposure_label": "Options exposure not shown",
        "caveat_codes": ["synthetic_fixture", "private_data_not_loaded"],
        "display_sections": [
            {
                "section_key": "summary",
                "title": "Fixture summary",
                "display_label": "Private-safe synthetic connected smoke data.",
            }
        ],
    }


def _portfolio_contexts(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "empty":
        return {
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "items": [],
        }
    if dashboard_state == "populated":
        return {
            "data_mode": "synthetic_demo",
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "items": [
                {
                    "context_reference": "ctx_skyframe_populated",
                    "context_label": "Skyframe populated synthetic context",
                    "source_kind": "synthetic_demo",
                    "portfolio_shape": _portfolio_shape(stock_count=4, option_count=2),
                    "cash_state": "available",
                    "cash_state_label": "Synthetic cash-state example available",
                    "broker_snapshot_freshness": _freshness(
                        "broker_snapshot",
                        "Synthetic fixture broker snapshot",
                        status="fresh",
                        as_of_label="Synthetic fixture as of Jun 19, 2026",
                    ),
                    "market_quote_freshness": _freshness(
                        "market_quote",
                        "Synthetic fixture market context",
                        status="fresh",
                        as_of_label="Synthetic fixture as of Jun 19, 2026",
                    ),
                    "market_data_unavailable": False,
                    "actionability_preview": {
                        "review_actionability_status": "analysis_only",
                        "overall_review_mode": "analysis_only",
                        "display_label": "Synthetic fixture analysis-only context",
                        "is_blocking": False,
                    },
                    "available_flows": ["stock_buy", "cash_secured_put", "covered_call"],
                    "caveat_codes": ["synthetic_fixture", "private_values_omitted"],
                }
            ],
        }
    return {
        "data_mode": "synthetic_demo",
        "demo_notice": SKYFRAME_DEMO_NOTICE,
        "items": [
            {
                "context_reference": "ctx_skyframe_demo",
                "context_label": "Skyframe synthetic context",
                "source_kind": "synthetic_demo",
                "portfolio_shape": _portfolio_shape(),
                "cash_state": "not_exposed",
                "cash_state_label": "Cash not exposed in fixture",
                "broker_snapshot_freshness": _freshness("broker_snapshot", "Synthetic fixture broker snapshot unavailable"),
                "market_quote_freshness": _freshness("market_quote", "Synthetic fixture market quotes unavailable"),
                "market_data_unavailable": True,
                "actionability_preview": {
                    "review_actionability_status": "analysis_only",
                    "overall_review_mode": "analysis_only",
                    "display_label": "Fixture analysis-only context",
                    "is_blocking": False,
                },
                "available_flows": ["stock_buy", "cash_secured_put", "covered_call"],
                "caveat_codes": ["synthetic_fixture"],
            }
        ],
    }


def _market_mood_base() -> dict[str, Any]:
    return {
        "data_mode": "unavailable",
        "source_label": "Market Mood unavailable",
        "source_detail_label": "No provider-reference fixture snapshot",
        "source_rights_notice": "Internal smoke fixture only.",
        "generated_at": _NOW,
        "updated_at_utc": None,
        "updated_at_label": None,
        "freshness_status": "unavailable",
        "freshness_label": "Market Mood fixture unavailable",
        "is_trading_signal": False,
        "is_actionability_input": False,
        "is_risk_rule_input": False,
        "score": None,
        "score_label": None,
        "score_min": 0,
        "score_max": 100,
        "rating": "unknown",
        "rating_label": "Unavailable",
        "trend_series": [],
        "comparisons": [
            {"window": "1w", "prior_score": None, "prior_score_label": None, "change_label": None, "is_available": False},
            {"window": "1m", "prior_score": None, "prior_score_label": None, "change_label": None, "is_available": False},
            {"window": "1y", "prior_score": None, "prior_score_label": None, "change_label": None, "is_available": False},
        ],
        "caveat_codes": ["synthetic_fixture"],
        "limitations": ["Broad market sentiment context only. Not a trading signal."],
        "status_message": "Skyframe smoke fixture does not load provider-reference Market Mood data.",
    }


def _market_mood(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "populated":
        return {
            "data_mode": "synthetic",
            "source_label": "Skyframe synthetic Market Mood fixture",
            "source_detail_label": "Fixed synthetic smoke snapshot",
            "source_rights_notice": "Synthetic fixture only; no external source data.",
            "generated_at": _NOW,
            "updated_at_utc": _NOW,
            "updated_at_label": "Synthetic fixture as of Jun 19, 2026",
            "freshness_status": "fresh",
            "freshness_label": "Fresh synthetic fixture snapshot",
            "is_trading_signal": False,
            "is_actionability_input": False,
            "is_risk_rule_input": False,
            "score": 50.0,
            "score_label": "50 · synthetic",
            "score_min": 0,
            "score_max": 100,
            "rating": "neutral",
            "rating_label": "Neutral synthetic example",
            "trend_series": [
                {
                    "date": "2026-06-17",
                    "score": 48.0,
                    "score_label": "48 · synthetic",
                    "rating": "neutral",
                    "rating_label": "Neutral synthetic example",
                },
                {
                    "date": "2026-06-18",
                    "score": 49.0,
                    "score_label": "49 · synthetic",
                    "rating": "neutral",
                    "rating_label": "Neutral synthetic example",
                },
                {
                    "date": _TODAY,
                    "score": 50.0,
                    "score_label": "50 · synthetic",
                    "rating": "neutral",
                    "rating_label": "Neutral synthetic example",
                },
            ],
            "comparisons": [
                {
                    "window": "1w",
                    "prior_score": 48.0,
                    "prior_score_label": "48 · synthetic",
                    "change_label": "+2 synthetic points",
                    "is_available": True,
                },
                {
                    "window": "1m",
                    "prior_score": None,
                    "prior_score_label": None,
                    "change_label": None,
                    "is_available": False,
                },
                {
                    "window": "1y",
                    "prior_score": None,
                    "prior_score_label": None,
                    "change_label": None,
                    "is_available": False,
                },
            ],
            "components": [
                {
                    "component_key": "market_momentum",
                    "display_name": "Synthetic market momentum",
                    "score": 52.0,
                    "score_label": "52 · synthetic",
                    "rating": "neutral",
                    "rating_label": "Neutral synthetic example",
                },
                {
                    "component_key": "market_volatility",
                    "display_name": "Synthetic market volatility",
                    "score": 47.0,
                    "score_label": "47 · synthetic",
                    "rating": "neutral",
                    "rating_label": "Neutral synthetic example",
                },
            ],
            "caveat_codes": ["synthetic_fixture"],
            "limitations": ["Broad market sentiment context only. Not a trading signal."],
            "status_message": "Fixed synthetic Market Mood content for private-safe visual smoke only.",
        }
    if dashboard_state == "empty":
        return {
            **_market_mood_base(),
            "source_detail_label": "Empty synthetic smoke state",
            "status_message": "No Market Mood snapshot is present in the empty fixture state.",
            "components": [],
        }
    return {**_market_mood_base(), "components": []}


def _market_mood_detail() -> dict[str, Any]:
    return {**_market_mood_base(), "indicators": []}


def _economic_calendar_events(dashboard_state: str) -> dict[str, Any]:
    if dashboard_state == "empty":
        return {
            "data_mode": "synthetic",
            "source_label": "Skyframe empty synthetic economic calendar",
            "as_of_label": "Fixture as of 2026-06-19",
            "freshness_label": "Empty synthetic fixture calendar",
            "window_start": _TODAY,
            "window_end": _TODAY,
            "timezone": "America/New_York",
            "importance_source": "app_classified",
            "items": [],
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "is_trading_signal": False,
            "limitations": ["Economic awareness only. Not a trading signal."],
        }
    if dashboard_state == "populated":
        return {
            "data_mode": "synthetic",
            "source_label": "Skyframe populated synthetic economic calendar",
            "as_of_label": "Fixture as of 2026-06-19",
            "freshness_label": "Populated synthetic fixture calendar",
            "window_start": _TODAY,
            "window_end": _TODAY,
            "timezone": "America/New_York",
            "importance_source": "app_classified",
            "items": [
                {
                    "event_reference": "econ_skyframe_demo_open",
                    "event_datetime_utc": "2026-06-19T12:30:00Z",
                    "event_has_occurred": True,
                    "event_date_label": "Fri, Jun 19",
                    "event_time_label": "08:30",
                    "event_title": "Synthetic fixture macro release",
                    "event_type": "economic_release",
                    "importance": "medium",
                    "importance_source": "app_classified",
                    "country": "US",
                    "currency": "USD",
                    "actual_label": "Synthetic value",
                    "forecast_label": "Synthetic value",
                    "previous_label": "Synthetic value",
                    "unit_label": None,
                    "source_label": "Skyframe synthetic fixture",
                    "freshness_label": "Populated synthetic fixture calendar",
                    "is_trading_signal": False,
                    "data_mode": "synthetic",
                },
                {
                    "event_reference": "econ_skyframe_demo_tbd",
                    "event_datetime_utc": None,
                    "event_has_occurred": None,
                    "event_date_label": "Fri, Jun 19",
                    "event_time_label": "Time TBD",
                    "event_title": "Synthetic fixture policy note",
                    "event_type": "central_bank",
                    "importance": "low",
                    "importance_source": "app_classified",
                    "country": "US",
                    "currency": "USD",
                    "actual_label": None,
                    "forecast_label": None,
                    "previous_label": None,
                    "unit_label": None,
                    "source_label": "Skyframe synthetic fixture",
                    "freshness_label": "Populated synthetic fixture calendar",
                    "is_trading_signal": False,
                    "data_mode": "synthetic",
                },
            ],
            "demo_notice": SKYFRAME_DEMO_NOTICE,
            "is_trading_signal": False,
            "limitations": ["Economic awareness only. Not a trading signal."],
        }
    return {
        "data_mode": "synthetic",
        "source_label": "Skyframe synthetic economic calendar",
        "as_of_label": "Fixture as of 2026-06-19",
        "freshness_label": "Synthetic fixture calendar",
        "window_start": _TODAY,
        "window_end": _TODAY,
        "timezone": "America/New_York",
        "importance_source": "app_classified",
        "items": [
            {
                "event_reference": "econ_skyframe_demo",
                "event_datetime_utc": None,
                "event_has_occurred": None,
                "event_date_label": "Fri, Jun 19",
                "event_time_label": "Time TBD",
                "event_title": "Synthetic fixture macro event",
                "event_type": "economic_release",
                "importance": "low",
                "importance_source": "app_classified",
                "country": "US",
                "currency": "USD",
                "actual_label": None,
                "forecast_label": None,
                "previous_label": None,
                "unit_label": None,
                "source_label": "Skyframe synthetic fixture",
                "freshness_label": "Synthetic fixture calendar",
                "is_trading_signal": False,
                "data_mode": "synthetic",
            }
        ],
        "demo_notice": SKYFRAME_DEMO_NOTICE,
        "is_trading_signal": False,
        "limitations": ["Economic awareness only. Not a trading signal."],
    }
