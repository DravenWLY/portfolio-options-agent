"""Private-safe synthetic fixture overlay for connected Skyframe smoke tests."""

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
SKYFRAME_UNAVAILABLE_REPORT_ID = "44444444-4444-4444-8444-444444444444"
SKYFRAME_FAILED_REPORT_ID = "55555555-5555-4555-8555-555555555555"

_ALLOWED_APP_ENVS = {"local", "dev", "development", "test", "testing"}
_ALLOWED_DASHBOARD_STATES = {"unavailable", "populated", "empty"}
_NOW = "2026-06-19T15:00:00Z"
_TODAY = "2026-06-19"


class SkyframeFixtureMiddleware(BaseHTTPMiddleware):
    """Serve fixed synthetic payloads for explicitly gated connected smoke runs."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        fixture_response = skyframe_fixture_response(request, get_settings())
        if fixture_response is not None:
            return fixture_response
        return await call_next(request)


def skyframe_fixture_response(request: Request, settings: Settings) -> JSONResponse | None:
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
    return path == "/users" or path.startswith("/users/") or path.startswith("/market-context/") or path.startswith(
        "/economic-calendar/"
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


def _reports_list() -> list[dict[str, Any]]:
    return [
        _report_thread(SKYFRAME_SOURCE_REPORT_ID, "Saved source snapshot", None),
        _report_thread(SKYFRAME_FULL_REPORT_ID, "Agent Team report", _agent_summary("full_agent_report")),
        _report_thread(SKYFRAME_UNAVAILABLE_REPORT_ID, "Agent unavailable report", _agent_summary("agent_unavailable")),
        _report_thread(SKYFRAME_FAILED_REPORT_ID, "Validation failed report", _agent_summary("validation_failed")),
    ]


def _report_detail(thread_id: str) -> dict[str, Any] | None:
    reports = {item["id"]: item for item in _reports_list()}
    report = reports.get(thread_id)
    if report is None:
        return None
    return {**report, "messages": []}


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


def _agent_summary(report_status: str) -> dict[str, Any]:
    if report_status == "full_agent_report":
        run_status = "completed"
        role_status = "completed"
        summary = "Synthetic smoke synthesis rendered from fixed fixture evidence."
        final = "Synthetic smoke synthesis. Broad context only; not a trading signal."
        evidence_refs: tuple[str, ...] = ("trade_intent_summary", "scope_state", "actionability")
    elif report_status == "validation_failed":
        run_status = "failed"
        role_status = "validation_failed"
        summary = None
        final = None
        evidence_refs = ()
    else:
        run_status = "failed"
        role_status = "unavailable"
        summary = None
        final = None
        evidence_refs = ()
    return {
        "run_status": run_status,
        "provider_mode": "synthetic_fixture",
        "report_generated_at": _NOW,
        "role_summaries": [
            {
                "role_name": "portfolio_manager_agent",
                "display_name": "Portfolio Manager",
                "role_status": role_status,
                "provider_status": "synthetic_fixture",
                "summary_markdown": summary,
                "evidence_references": list(evidence_refs),
                "warning_codes": [] if summary else ["fixture_degraded_state"],
                "unavailable_reason": None if summary else "fixture_degraded_state",
            }
        ],
        "warning_codes": [] if report_status == "full_agent_report" else ["fixture_degraded_state"],
        "report_status": report_status,
        "final_synthesis_markdown": final,
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_saved_evidence_v1",
        "evidence_references": list(evidence_refs),
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
