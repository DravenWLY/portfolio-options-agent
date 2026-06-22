import pytest
from fastapi.testclient import TestClient

from app.api.routes import accounts as accounts_route
from app.api.routes import economic_calendar as economic_calendar_route
from app.api.routes import market_context as market_context_route
from app.api.routes import reports as reports_route
from app.api.routes import trade_reviews as trade_reviews_route
from app.api.routes import users as users_route
from app.schemas.account import AccountRead
from app.schemas.economic_calendar import EconomicCalendarEventListRead
from app.schemas.market_mood import MarketMoodDetailRead, MarketMoodRead
from app.schemas.reports import ReportThreadDetailRead, ReportThreadRead, SavedReviewArtifactRead
from app.schemas.trade_review_workspace import (
    DashboardAccountSummaryRead,
    PortfolioContextListRead,
    ReviewReadinessRead,
    RiskAlertListRead,
    TradeReviewWorkspaceRead,
    TradeReviewListRead,
)
from app.schemas.user import UserRead
from app.services.skyframe_fixtures import (
    SKYFRAME_DEMO_ACCOUNT_ID,
    SKYFRAME_DEMO_USER_ID,
    SKYFRAME_DASHBOARD_STATE_HEADER,
    SKYFRAME_DRAFT_REPORT_ID,
    SKYFRAME_FAILED_REPORT_ID,
    SKYFRAME_FIXTURE_HEADER,
    SKYFRAME_FIXTURE_HEADER_VALUE,
    SKYFRAME_FULL_REPORT_ID,
    SKYFRAME_GOLDEN_SOURCE_REFERENCE,
    SKYFRAME_SOURCE_REPORT_ID,
    SKYFRAME_UNAVAILABLE_REPORT_ID,
)


pytestmark = pytest.mark.api

_TOKEN = "test-local-dev-access-token"


def _fixture_headers(*, dashboard_state: str | None = None) -> dict[str, str]:
    headers = {
        "X-Local-Access-Token": _TOKEN,
        SKYFRAME_FIXTURE_HEADER: SKYFRAME_FIXTURE_HEADER_VALUE,
    }
    if dashboard_state is not None:
        headers[SKYFRAME_DASHBOARD_STATE_HEADER] = dashboard_state
    return headers


def _enable_fixtures(monkeypatch: pytest.MonkeyPatch, *, app_env: str = "local") -> None:
    monkeypatch.setenv("LOCAL_DEV_ACCESS_TOKEN", _TOKEN)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("POA_SKYFRAME_FIXTURES", "1")


def test_skyframe_fixture_requires_env_flag(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_DEV_ACCESS_TOKEN", _TOKEN)
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("POA_SKYFRAME_FIXTURES", "0")
    monkeypatch.setattr(users_route.user_service, "list_users", lambda db: [])

    response = client.get("/users", headers=_fixture_headers())

    assert response.status_code == 200
    assert response.json() == []


def test_skyframe_fixture_requires_header(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    monkeypatch.setattr(users_route.user_service, "list_users", lambda db: [])

    response = client.get("/users", headers={"X-Local-Access-Token": _TOKEN})

    assert response.status_code == 200
    assert response.json() == []


def test_skyframe_fixture_requires_valid_local_access_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)

    response = client.get(
        "/users",
        headers={
            "X-Local-Access-Token": "wrong-token",
            SKYFRAME_FIXTURE_HEADER: SKYFRAME_FIXTURE_HEADER_VALUE,
        },
    )

    assert response.status_code == 401


def test_skyframe_fixture_is_blocked_in_production_like_env(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch, app_env="production")
    monkeypatch.setattr(users_route.user_service, "list_users", lambda db: [])

    response = client.get("/users", headers=_fixture_headers())

    assert response.status_code == 200
    assert response.json() == []


def test_skyframe_fixture_supported_path_bypasses_real_user_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)

    def fail_if_called(db):  # type: ignore[no-untyped-def]
        raise AssertionError("real user service must not be called for skyframe fixtures")

    monkeypatch.setattr(users_route.user_service, "list_users", fail_if_called)

    response = client.get("/users", headers=_fixture_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {
            "id": SKYFRAME_DEMO_USER_ID,
            "display_name": "Skyframe Demo User",
            "email": "skyframe-demo@example.com",
            "auth_provider": "skyframe_fixture",
            "is_active": True,
            "created_at": "2026-06-19T15:00:00Z",
            "updated_at": "2026-06-19T15:00:00Z",
            "deleted_at": None,
        }
    ]


def test_skyframe_fixture_reports_use_fixed_synthetic_identifiers(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    response = client.get(f"/users/{incoming_user_id}/reports", headers=_fixture_headers())

    assert response.status_code == 200
    payload = response.json()
    assert {item["user_id"] for item in payload} == {SKYFRAME_DEMO_USER_ID}
    assert incoming_user_id not in repr(payload)
    assert {item["agent_summary"]["report_status"] for item in payload if item["agent_summary"]} == {
        "deterministic_draft",
        "full_agent_report",
        "agent_unavailable",
        "validation_failed",
    }
    by_status = {item["agent_summary"]["report_status"]: item["agent_summary"] for item in payload if item["agent_summary"]}
    full_synthesis = by_status["full_agent_report"]["final_synthesis_markdown"]
    draft_synthesis = by_status["deterministic_draft"]["final_synthesis_markdown"]
    assert "What you would be ignoring if you acted manually now" in full_synthesis
    assert "deterministic risk flags" in full_synthesis
    assert "data freshness and availability gaps" in full_synthesis
    assert "scope and feasibility caveats" in full_synthesis
    assert "context not reviewed" in full_synthesis
    assert "Manual verification checklist" in full_synthesis
    assert "What you would be ignoring if you acted manually now" in draft_synthesis
    assert "blocked_actionability_llm_roles_skipped" in by_status["deterministic_draft"]["warning_codes"]


def test_skyframe_fixture_accounts_use_canonical_fixed_synthetic_identifiers(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real account service must not be called for skyframe fixtures")

    monkeypatch.setattr(accounts_route.account_service, "list_user_accounts", fail_if_called)

    response = client.get(f"/users/{incoming_user_id}/accounts", headers=_fixture_headers())

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    account = AccountRead.model_validate(payload[0])
    assert str(account.id) == SKYFRAME_DEMO_ACCOUNT_ID
    assert str(account.user_id) == SKYFRAME_DEMO_USER_ID
    assert account.display_name == "Synthetic demo account"
    assert incoming_user_id not in repr(payload)


@pytest.mark.parametrize(
    ("include_fixture_header", "app_env"),
    ((False, "local"), (True, "production")),
)
def test_skyframe_fixture_accounts_require_all_gates_and_nonproduction_env(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    include_fixture_header: bool,
    app_env: str,
) -> None:
    _enable_fixtures(monkeypatch, app_env=app_env)
    monkeypatch.setattr(accounts_route.account_service, "list_user_accounts", lambda db, user_id: [])
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    headers = _fixture_headers() if include_fixture_header else {"X-Local-Access-Token": _TOKEN}

    response = client.get(f"/users/{incoming_user_id}/accounts", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_skyframe_fixture_supported_dashboard_children_are_synthetic(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    account_response = client.get(f"/users/{user_id}/dashboard-account-summary", headers=_fixture_headers())
    mood_response = client.get("/market-context/market-mood", headers=_fixture_headers())
    calendar_response = client.get("/economic-calendar/events", headers=_fixture_headers())

    assert account_response.status_code == 200
    assert account_response.json()["data_mode"] == "synthetic_demo"
    assert account_response.json()["demo_notice"] == "demo · skyframe private-safe fixture"
    assert mood_response.status_code == 200
    assert mood_response.json()["data_mode"] == "unavailable"
    assert calendar_response.status_code == 200
    assert calendar_response.json()["data_mode"] == "synthetic"


def test_skyframe_fixture_smoke_owned_unsupported_path_does_not_fall_through(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    response = client.get(f"/users/{incoming_user_id}/account-details", headers=_fixture_headers())

    assert response.status_code == 404
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert incoming_user_id not in repr(payload)


def test_skyframe_fixture_report_generation_posts_fail_closed_before_real_handlers(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    incoming_report_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real report service must not be called for skyframe fixtures")

    monkeypatch.setattr(reports_route.report_service, "create_saved_review_artifact", fail_if_called)
    monkeypatch.setattr(reports_route, "generate_agent_team_report_for_thread", fail_if_called)

    responses = (
        client.post(
            f"/users/{incoming_user_id}/reports/from-trade-review",
            headers=_fixture_headers(),
            json={},
        ),
        client.post(
            f"/users/{incoming_user_id}/reports/{incoming_report_id}/agent-team-report",
            headers=_fixture_headers(),
        ),
    )

    for response in responses:
        assert response.status_code == 404
        payload = response.json()
        assert payload["data_mode"] == "synthetic_demo"
        assert incoming_user_id not in repr(payload)
        assert incoming_report_id not in repr(payload)


def test_skyframe_fixture_portfolio_preview_posts_return_canonical_workspace_without_real_handler(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real trade review builder must not be called for skyframe fixtures")

    monkeypatch.setattr(trade_reviews_route, "build_trade_review_workspace_portfolio_preview", fail_if_called)
    incoming_context_ref = "ctx_incoming_private_context"
    incoming_account_ref = "acctref_incoming_private_ref"
    stock_response = client.post(
        "/trade-reviews/portfolio-preview",
        headers=_fixture_headers(),
        json={
            "supported_flow": "stock_buy",
            "symbol": "ABC",
            "quantity": "9",
            "price_assumption": "11",
            "portfolio_context_selection": {"mode": "selected_context", "context_reference": incoming_context_ref},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": incoming_account_ref,
            },
        },
    )
    option_response = client.post(
        "/trade-reviews/portfolio-preview",
        headers=_fixture_headers(),
        json={
            "supported_flow": "cash_secured_put",
            "option_leg": {
                "underlying_symbol": "XYZ",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": "2026-09-18",
                "strike": "42",
                "quantity": "1",
                "premium": "1",
            },
            "portfolio_context_selection": {"mode": "selected_context", "context_reference": incoming_context_ref},
        },
    )

    for response, expected_flow in ((stock_response, "stock_buy"), (option_response, "cash_secured_put")):
        assert response.status_code == 200
        payload = response.json()
        workspace = TradeReviewWorkspaceRead.model_validate(payload)
        assert workspace.supported_flow == expected_flow
        assert workspace.saved_review_source_reference == SKYFRAME_GOLDEN_SOURCE_REFERENCE
        assert workspace.scope_metadata is not None
        assert workspace.actionability.broker_snapshot.freshness_scope == "broker_snapshot"
        assert workspace.actionability.market_quotes.freshness_scope == "market_quote"
        rendered = repr(payload)
        assert incoming_context_ref not in rendered
        assert incoming_account_ref not in rendered
        assert "ABC" not in rendered
        assert "XYZ" not in rendered


def test_skyframe_fixture_save_and_generate_posts_are_explicit_stateless_and_canonical(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    incoming_title = "Incoming private title"

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real report service must not be called for skyframe fixtures")

    monkeypatch.setattr(reports_route.report_service, "create_saved_review_artifact", fail_if_called)
    monkeypatch.setattr(reports_route, "generate_agent_team_report_for_thread", fail_if_called)
    monkeypatch.setattr(reports_route.report_service, "get_report_thread", fail_if_called)

    save_response = client.post(
        f"/users/{incoming_user_id}/reports/from-trade-review",
        headers=_fixture_headers(),
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": SKYFRAME_GOLDEN_SOURCE_REFERENCE,
            "title": incoming_title,
            "report_type": "saved_review_artifact",
        },
    )
    assert save_response.status_code == 201
    saved = save_response.json()
    saved_artifact = SavedReviewArtifactRead.model_validate(saved)
    assert saved_artifact.agent_summary is None
    assert incoming_user_id not in repr(saved)
    assert incoming_title not in repr(saved)

    generate_response = client.post(
        f"/users/{incoming_user_id}/reports/{SKYFRAME_SOURCE_REPORT_ID}/agent-team-report",
        headers=_fixture_headers(),
        json={},
    )
    assert generate_response.status_code == 201
    generated = generate_response.json()
    generated_artifact = SavedReviewArtifactRead.model_validate(generated)
    assert generated_artifact.agent_summary is not None
    assert generated_artifact.agent_summary.report_status == "full_agent_report"
    assert "What you would be ignoring if you acted manually now" in (
        generated_artifact.agent_summary.final_synthesis_markdown or ""
    )
    assert incoming_user_id not in repr(generated)


def test_skyframe_fixture_save_post_rejects_unknown_source_without_echo(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    incoming_source_ref = "trrev_incoming_private_ref"

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real report service must not be called for skyframe fixtures")

    monkeypatch.setattr(reports_route.report_service, "create_saved_review_artifact", fail_if_called)

    response = client.post(
        f"/users/{incoming_user_id}/reports/from-trade-review",
        headers=_fixture_headers(),
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": incoming_source_ref,
            "title": "Unsupported fixture source",
            "report_type": "saved_review_artifact",
        },
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert incoming_user_id not in repr(payload)
    assert incoming_source_ref not in repr(payload)


def test_skyframe_fixture_refresh_posts_fail_closed_before_real_runners(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)

    def fail_if_called():
        raise AssertionError("real refresh dependency must not be called for skyframe fixtures")

    client.app.dependency_overrides[market_context_route.get_market_mood_refresh_runner] = fail_if_called
    client.app.dependency_overrides[economic_calendar_route.get_economic_calendar_refresh_runner] = fail_if_called
    try:
        responses = (
            client.post("/market-context/market-mood/refresh", headers=_fixture_headers()),
            client.post("/economic-calendar/refresh", headers=_fixture_headers()),
        )
    finally:
        client.app.dependency_overrides.pop(market_context_route.get_market_mood_refresh_runner, None)
        client.app.dependency_overrides.pop(economic_calendar_route.get_economic_calendar_refresh_runner, None)

    for response in responses:
        assert response.status_code == 405
        assert response.json() == {
            "detail": "This method is not available in the Skyframe private-safe fixture.",
            "data_mode": "synthetic_demo",
            "demo_notice": "demo · skyframe private-safe fixture",
        }


def test_skyframe_fixture_supported_payloads_validate_against_canonical_schemas(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    users_payload = client.get("/users", headers=_fixture_headers()).json()
    assert [UserRead.model_validate(item) for item in users_payload]

    accounts_payload = client.get(f"/users/{incoming_user_id}/accounts", headers=_fixture_headers()).json()
    assert [AccountRead.model_validate(item) for item in accounts_payload]
    assert incoming_user_id not in repr(accounts_payload)

    reports_payload = client.get(f"/users/{incoming_user_id}/reports", headers=_fixture_headers()).json()
    validated_reports = [ReportThreadRead.model_validate(item) for item in reports_payload]
    role_names = {
        role.role_name
        for report in validated_reports
        if report.agent_summary is not None
        for role in report.agent_summary.role_summaries
    }
    assert "portfolio_manager_agent" in role_names
    assert "risk_management_agent" in role_names

    for report_id in (
        SKYFRAME_SOURCE_REPORT_ID,
        SKYFRAME_FULL_REPORT_ID,
        SKYFRAME_DRAFT_REPORT_ID,
        SKYFRAME_UNAVAILABLE_REPORT_ID,
        SKYFRAME_FAILED_REPORT_ID,
    ):
        payload = client.get(
            f"/users/{incoming_user_id}/reports/{report_id}",
            headers=_fixture_headers(),
        ).json()
        ReportThreadDetailRead.model_validate(payload)

    canonical_cases = (
        (f"/users/{incoming_user_id}/trade-reviews", TradeReviewListRead),
        (f"/users/{incoming_user_id}/risk-alerts", RiskAlertListRead),
        (f"/users/{incoming_user_id}/readiness", ReviewReadinessRead),
        (f"/users/{incoming_user_id}/dashboard-account-summary", DashboardAccountSummaryRead),
        (f"/users/{incoming_user_id}/portfolio-contexts", PortfolioContextListRead),
        ("/market-context/market-mood", MarketMoodRead),
        ("/market-context/market-mood/detail", MarketMoodDetailRead),
        ("/economic-calendar/events", EconomicCalendarEventListRead),
    )
    for path, response_model in canonical_cases:
        response = client.get(path, headers=_fixture_headers())
        assert response.status_code == 200
        response_model.model_validate(response.json())
        assert incoming_user_id not in repr(response.json())


@pytest.mark.parametrize("dashboard_state", ("unavailable", "populated", "empty"))
def test_skyframe_dashboard_states_validate_across_all_owned_reads(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    dashboard_state: str,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    headers = _fixture_headers(dashboard_state=dashboard_state)
    cases = (
        (f"/users/{incoming_user_id}/trade-reviews", TradeReviewListRead),
        (f"/users/{incoming_user_id}/risk-alerts", RiskAlertListRead),
        (f"/users/{incoming_user_id}/readiness", ReviewReadinessRead),
        (f"/users/{incoming_user_id}/dashboard-account-summary", DashboardAccountSummaryRead),
        (f"/users/{incoming_user_id}/portfolio-contexts", PortfolioContextListRead),
        ("/market-context/market-mood", MarketMoodRead),
        ("/economic-calendar/events", EconomicCalendarEventListRead),
    )

    payloads: dict[str, dict[str, object]] = {}
    for path, response_model in cases:
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        payload = response.json()
        response_model.model_validate(payload)
        assert incoming_user_id not in repr(payload)
        payloads[path] = payload

    accounts_response = client.get(f"/users/{incoming_user_id}/accounts", headers=headers)
    assert accounts_response.status_code == 200
    accounts_payload = accounts_response.json()
    accounts = [AccountRead.model_validate(item) for item in accounts_payload]
    assert [str(account.id) for account in accounts] == [SKYFRAME_DEMO_ACCOUNT_ID]
    assert incoming_user_id not in repr(accounts_payload)

    summary = payloads[f"/users/{incoming_user_id}/dashboard-account-summary"]
    contexts = payloads[f"/users/{incoming_user_id}/portfolio-contexts"]
    reviews = payloads[f"/users/{incoming_user_id}/trade-reviews"]
    alerts = payloads[f"/users/{incoming_user_id}/risk-alerts"]
    mood = payloads["/market-context/market-mood"]
    calendar = payloads["/economic-calendar/events"]
    if dashboard_state == "empty":
        assert reviews["items"] == []
        assert alerts["items"] == []
        assert contexts["items"] == []
        assert calendar["items"] == []
        assert summary["summary_reference"] == "das_skyframe_empty"
        assert mood["data_mode"] == "unavailable"
    elif dashboard_state == "populated":
        assert summary["summary_reference"] == "das_skyframe_populated"
        assert summary["portfolio_shape"] == {"stock_position_count": 4, "option_position_count": 2}
        assert len(contexts["items"]) == 1
        assert mood["data_mode"] == "synthetic"
        assert len(calendar["items"]) == 2
    else:
        assert summary["summary_reference"] == "das_skyframe_demo"
        assert len(contexts["items"]) == 1
        assert mood["data_mode"] == "unavailable"
        assert len(calendar["items"]) == 1


def test_skyframe_dashboard_missing_selector_preserves_unavailable_default(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    paths = (
        f"/users/{incoming_user_id}/trade-reviews",
        f"/users/{incoming_user_id}/risk-alerts",
        f"/users/{incoming_user_id}/readiness",
        f"/users/{incoming_user_id}/dashboard-account-summary",
        f"/users/{incoming_user_id}/portfolio-contexts",
        "/market-context/market-mood",
        "/economic-calendar/events",
        f"/users/{incoming_user_id}/accounts",
    )

    for path in paths:
        default_response = client.get(path, headers=_fixture_headers())
        unavailable_response = client.get(path, headers=_fixture_headers(dashboard_state="unavailable"))
        assert default_response.status_code == 200
        assert default_response.json() == unavailable_response.json()


def test_skyframe_dashboard_active_states_bypass_all_real_services(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real Dashboard service must not be called for skyframe fixtures")

    monkeypatch.setattr(users_route, "list_recent_trade_reviews_for_user", fail_if_called)
    monkeypatch.setattr(users_route, "list_risk_alerts_for_user", fail_if_called)
    monkeypatch.setattr(users_route, "get_review_readiness_for_user", fail_if_called)
    monkeypatch.setattr(users_route, "get_dashboard_account_summary_for_user", fail_if_called)
    monkeypatch.setattr(users_route, "list_portfolio_contexts_for_user", fail_if_called)
    monkeypatch.setattr(accounts_route.account_service, "list_user_accounts", fail_if_called)
    client.app.dependency_overrides[market_context_route.get_market_mood_service] = fail_if_called
    client.app.dependency_overrides[economic_calendar_route.get_economic_calendar_service] = fail_if_called
    try:
        paths = (
            f"/users/{incoming_user_id}/trade-reviews",
            f"/users/{incoming_user_id}/risk-alerts",
            f"/users/{incoming_user_id}/readiness",
            f"/users/{incoming_user_id}/dashboard-account-summary",
            f"/users/{incoming_user_id}/portfolio-contexts",
            "/market-context/market-mood",
            "/economic-calendar/events",
            f"/users/{incoming_user_id}/accounts",
        )
        for path in paths:
            response = client.get(path, headers=_fixture_headers(dashboard_state="populated"))
            assert response.status_code == 200
    finally:
        client.app.dependency_overrides.pop(market_context_route.get_market_mood_service, None)
        client.app.dependency_overrides.pop(economic_calendar_route.get_economic_calendar_service, None)


@pytest.mark.parametrize("invalid_state", ("not-allowed", ""))
def test_skyframe_dashboard_invalid_selector_fails_closed_without_real_services(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    invalid_state: str,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("real Dashboard service must not be called for an invalid fixture state")

    monkeypatch.setattr(users_route, "get_dashboard_account_summary_for_user", fail_if_called)
    monkeypatch.setattr(accounts_route.account_service, "list_user_accounts", fail_if_called)
    client.app.dependency_overrides[market_context_route.get_market_mood_service] = fail_if_called
    client.app.dependency_overrides[economic_calendar_route.get_economic_calendar_service] = fail_if_called
    try:
        paths = (
            f"/users/{incoming_user_id}/dashboard-account-summary",
            f"/users/{incoming_user_id}/accounts",
            "/market-context/market-mood",
            "/economic-calendar/events",
        )
        for path in paths:
            response = client.get(path, headers=_fixture_headers(dashboard_state=invalid_state))
            assert response.status_code == 400
            payload = response.json()
            assert payload["detail"] == "Unsupported Skyframe Dashboard fixture state."
            assert payload["data_mode"] == "synthetic_demo"
            assert incoming_user_id not in repr(payload)
    finally:
        client.app.dependency_overrides.pop(market_context_route.get_market_mood_service, None)
        client.app.dependency_overrides.pop(economic_calendar_route.get_economic_calendar_service, None)


@pytest.mark.parametrize(
    ("gate", "app_env"),
    (("flag", "local"), ("fixture_header", "local"), ("production", "production")),
)
def test_skyframe_dashboard_selector_cannot_bypass_activation_gates(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    gate: str,
    app_env: str,
) -> None:
    _enable_fixtures(monkeypatch, app_env=app_env)
    if gate == "flag":
        monkeypatch.setenv("POA_SKYFRAME_FIXTURES", "0")

    def reached_real_route(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("fixture remained inactive")

    monkeypatch.setattr(users_route, "get_dashboard_account_summary_for_user", reached_real_route)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    headers = _fixture_headers(dashboard_state="populated")
    if gate == "fixture_header":
        headers.pop(SKYFRAME_FIXTURE_HEADER)

    with pytest.raises(AssertionError, match="fixture remained inactive"):
        client.get(f"/users/{incoming_user_id}/dashboard-account-summary", headers=headers)


def test_skyframe_dashboard_selector_requires_valid_local_access_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fixtures(monkeypatch)
    incoming_user_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    headers = _fixture_headers(dashboard_state="populated")
    headers["X-Local-Access-Token"] = "wrong-token"

    response = client.get(f"/users/{incoming_user_id}/dashboard-account-summary", headers=headers)

    assert response.status_code == 401
