from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes import reports as report_routes
from app.api.routes.trade_reviews import _saved_review_safe_caveat_code_tuple
from app.config import Settings
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.report_message import ReportMessage
from app.models.report_thread import ReportThread
from app.models.saved_review_source import SavedReviewSource
from app.schemas.reports import SavedEvidencePackageRead, SavedReviewArtifactCreateRequest, SavedReviewArtifactRead
from app.schemas.trade_review_workspace import validate_trade_review_saved_source_reference
from app.services.agent_team import tool_mediated_report
from app.services.agent_team.llm_clients.contracts import LLMProviderRequest, LLMProviderResponse, LLMProviderStatus
from app.services.agent_team.llm_clients.factory import LLMProviderResolution
from app.services.agent_team.orchestration.models import LIVE_PROMPT_VERSION
from app.services.market_data.eod_history import (
    MarketContextExecutionContext,
    MarketContextPolicy,
    market_context_execution_context_for_client,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports import agent_team_report as agent_team_report_service
from app.services.reports import crud as report_service
from app.services.reports.public_evidence import (
    EdgarCompanyProfileSourcePolicy,
    EdgarRecentFilingsSourcePolicy,
)
from app.services.reports.source_snapshots import (
    FmpFundamentalsSourcePolicy,
    FredMacroSeriesSourcePolicy,
    fmp_fundamentals_execution_context_for_client,
    fred_macro_series_execution_context_for_client,
)
from app.services.trade_review import exposure_adapter as exposure_adapter_service


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_create_list_and_get_report_thread_detail(client: TestClient, db_session: Session) -> None:
    user_response = client.post("/users", json={"display_name": "Demo Report API", "email": "report-api@example.com"})
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Demo Taxable",
            "base_currency": "USD",
        },
    )
    account_id = account_response.json()["id"]

    create_response = client.post(
        f"/users/{user_id}/reports",
        json={
            "account_id": account_id,
            "title": "Synthetic portfolio review",
            "report_type": "portfolio_review",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["user_id"] == user_id
    assert created["account_id"] == account_id
    assert created["title"] == "Synthetic portfolio review"
    assert created["deleted_at"] is None
    assert created["scope_metadata"] is None
    assert created["public_evidence_attribution"] is None

    db_session.add(
        ReportMessage(
            thread_id=created["id"],
            sender_type="system",
            message_type="markdown_report",
            content_markdown="# Synthetic",
            sequence=1,
        )
    )
    db_session.commit()

    list_response = client.get(f"/users/{user_id}/reports")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert [thread["id"] for thread in listed] == [created["id"]]
    assert listed[0]["scope_metadata"] is None
    assert listed[0]["public_evidence_attribution"] is None

    detail_response = client.get(f"/users/{user_id}/reports/{created['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == created["id"]
    assert detail["scope_metadata"] is None
    assert detail["public_evidence_attribution"] is None
    assert detail["messages"][0]["message_type"] == "markdown_report"
    assert detail["messages"][0]["content_markdown"] == "# Synthetic"
    assert not find_forbidden_keys(
        detail["scope_metadata"],
        forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS,
    )


def test_create_saved_review_artifact_persists_generation_time_scope(client: TestClient, db_session: Session) -> None:
    user_response = client.post("/users", json={"display_name": "Saved Review User", "email": "saved@example.com"})
    user_id = user_response.json()["id"]
    generated_at = datetime(2026, 6, 13, 15, 30, tzinfo=UTC).isoformat()
    source_payload = {
        "source_kind": "trade_review_workspace",
        "source_reference": "workspace_savedreview1",
        "title": "Saved covered-call review",
        "report_type": "trade_review",
        "scope_metadata": _scope_metadata_payload("Primary reviewed account"),
        "deterministic_summary": _deterministic_summary_payload(),
        "generated_at": generated_at,
        "limitations": ("Generated from reviewed data available at the time.",),
        "caveat_codes": ("selected_context_scope",),
    }
    source = report_service.record_saved_review_source(
        db_session,
        UUID(user_id),
        SavedReviewArtifactCreateRequest(**source_payload),
    )
    assert source is not None

    response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "title": "Saved covered-call review",
            "report_type": "trade_review",
            "scope_metadata": _scope_metadata_payload("Client supplied scope must be ignored"),
            "deterministic_summary": {
                **_deterministic_summary_payload(),
                "symbol_or_underlying": "MSFT",
            },
        },
    )

    assert response.status_code == 201
    saved = response.json()
    assert saved["status"] == "saved"
    assert saved["artifact_reference"].startswith("svrev_")
    assert saved["scope_metadata"]["scope_summary_label"] == (
        "Review account selected · Context scope: Selected reviewed context."
    )
    assert saved["deterministic_summary"]["review_actionability_status"] == "analysis_only"
    assert saved["deterministic_summary"]["symbol_or_underlying"] == "HOOD"
    assert saved["generated_at"] == generated_at.replace("+00:00", "Z")
    assert not find_forbidden_keys(saved, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)

    list_response = client.get(f"/users/{user_id}/reports")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["scope_metadata"]["scope_summary_label"] == saved["scope_metadata"]["scope_summary_label"]

    # Later mutable account/context state must not reinterpret the saved report scope.
    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Later Broker",
            "account_type": "taxable_individual",
            "display_name": "Later Account",
            "base_currency": "USD",
        },
    )
    assert account_response.status_code == 201

    detail_response = client.get(f"/users/{user_id}/reports/{listed[0]['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["scope_metadata"] == listed[0]["scope_metadata"]
    assert detail["scope_metadata"]["scope_summary_label"] == (
        "Review account selected · Context scope: Selected reviewed context."
    )


def test_generate_agent_team_report_persists_summary_and_projects_on_reports(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_response = client.post("/users", json={"display_name": "Agent Report User", "email": "agent-report@example.com"})
    user_id = user_response.json()["id"]
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="workspace_agentreport1",
        title="Saved covered-call review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Primary reviewed account"),
        deterministic_summary=_deterministic_summary_payload(),
        limitations=("Generated from reviewed data available at the time.",),
        caveat_codes=("selected_context_scope",),
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None
    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_agentreport1",
            "title": "Saved covered-call review",
            "report_type": "trade_review",
        },
    )
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]

    first_generated_at = datetime(2026, 6, 15, 18, 0, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: first_generated_at)
    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    saved = response.json()
    assert saved["agent_summary"]["report_status"] == "full_agent_report"
    assert saved["agent_summary"]["report_generated_at"] == first_generated_at.isoformat().replace("+00:00", "Z")
    assert saved["public_evidence"]["public_evidence_mode"] == "not_reviewed"
    assert saved["public_evidence"]["public_company_profile"]["availability"] == "not_reviewed"
    assert saved["agent_summary"]["final_synthesis_markdown"] is not None
    assert saved["agent_summary"]["evidence_schema_version"] == "p29a_t1_v1"
    assert saved["agent_summary"]["role_summaries"]
    immutable_saved_source = {
        "source_reference": saved["source_reference"],
        "scope_metadata": saved["scope_metadata"],
        "deterministic_summary": saved["deterministic_summary"],
        "generated_at": saved["generated_at"],
    }
    agent_summary_rendered = repr(saved["agent_summary"]).lower()
    assert "primary reviewed account" not in agent_summary_rendered
    assert "acctref_savedreview1" not in agent_summary_rendered
    assert not find_forbidden_keys(saved, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)

    listed = client.get(f"/users/{user_id}/reports").json()
    assert listed[0]["agent_summary"]["report_status"] == "full_agent_report"
    assert listed[0]["public_evidence_attribution"] is None
    detail = client.get(f"/users/{user_id}/reports/{thread_id}").json()
    assert detail["agent_summary"] == listed[0]["agent_summary"]
    assert detail["public_evidence_attribution"] is None

    second_generated_at = datetime(2026, 6, 15, 18, 5, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: second_generated_at)
    regenerated_response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert regenerated_response.status_code == 201
    regenerated = regenerated_response.json()
    assert regenerated["agent_summary"]["report_generated_at"] == second_generated_at.isoformat().replace("+00:00", "Z")
    assert regenerated["agent_summary"]["report_status"] == "full_agent_report"
    assert regenerated["public_evidence"] == saved["public_evidence"]
    assert {
        "source_reference": regenerated["source_reference"],
        "scope_metadata": regenerated["scope_metadata"],
        "deterministic_summary": regenerated["deterministic_summary"],
        "generated_at": regenerated["generated_at"],
    } == immutable_saved_source


def test_generate_agent_team_report_route_ignores_client_requested_tool_mode(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="client-mode-ignored@example.com",
        source_reference="workspace_clientmode1",
    )

    def _unexpected_provider_resolution() -> LLMProviderResolution:
        raise AssertionError("Provider resolution should not run without backend tool-mediated opt-in")

    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_agent_team_report_provider_resolution",
        _unexpected_provider_resolution,
    )
    response = client.post(
        f"/users/{user_id}/reports/{thread_id}/agent-team-report",
        json={"mode": "tool_mediated", "provider": "fake_live_provider"},
    )

    assert response.status_code == 201
    saved = response.json()
    assert saved["agent_summary"]["provider_mode"] == "deterministic_template"
    assert saved["agent_summary"]["tool_run_artifact"] is None


def test_generate_agent_team_report_route_wires_live_fmp_eod_history_context(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="route-eod-history@example.com",
        source_reference="workspace_routeeod1",
    )
    policy = MarketContextPolicy(mode="live")
    context = MarketContextExecutionContext(policy=policy)
    monkeypatch.setattr(report_routes, "market_context_policy_from_environment", lambda: policy)
    monkeypatch.setattr(report_routes, "default_market_context_execution_context", lambda: context)

    captured: dict[str, object] = {}
    real_generate = agent_team_report_service.generate_agent_team_report_for_thread

    def _capture_generate(*args: object, **kwargs: object):
        captured.update(kwargs)
        return real_generate(*args, **kwargs)

    monkeypatch.setattr(agent_team_report_service, "generate_agent_team_report_for_thread", _capture_generate)

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    assert captured["fmp_eod_history_policy"] is policy
    assert captured["fmp_eod_history_context"] is context


def test_generate_agent_team_report_route_leaves_fmp_eod_history_unconfigured_when_mode_is_off(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="route-eod-history-off@example.com",
        source_reference="workspace_routeeodoff1",
    )
    monkeypatch.setattr(report_routes, "market_context_policy_from_environment", lambda: MarketContextPolicy(mode="off"))

    def _unexpected_context() -> MarketContextExecutionContext:
        raise AssertionError("EOD context resolution must not run when the lane is disabled")

    monkeypatch.setattr(report_routes, "default_market_context_execution_context", _unexpected_context)

    captured: dict[str, object] = {}
    real_generate = agent_team_report_service.generate_agent_team_report_for_thread

    def _capture_generate(*args: object, **kwargs: object):
        captured.update(kwargs)
        return real_generate(*args, **kwargs)

    monkeypatch.setattr(agent_team_report_service, "generate_agent_team_report_for_thread", _capture_generate)

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    assert captured["fmp_eod_history_policy"] is None
    assert captured["fmp_eod_history_context"] is None


def test_generate_agent_team_report_route_freezes_live_fmp_fundamentals_snapshot(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="route-fundamentals@example.com",
        source_reference="workspace_routefundamentals1",
    )
    fundamentals_client = _CountingFmpFundamentalsClient()
    settings = Settings(
        app_env="test",
        fmp_api_key="test-key-not-real",
        fmp_fundamentals_mode="live",
    )
    monkeypatch.setattr(report_routes, "get_settings", lambda: settings)
    monkeypatch.setattr(report_routes, "FmpFundamentalsHttpClient", lambda **_: fundamentals_client)
    monkeypatch.setattr(report_routes, "_resolve_fmp_eod_history_generation_context", lambda: (None, None))
    monkeypatch.setattr(
        report_routes,
        "_resolve_edgar_report_evidence_generation_context",
        lambda: (None, None, None, None),
    )

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    saved = response.json()
    fundamentals = saved["public_evidence"]["public_fundamentals_snapshot"]
    assert fundamentals["availability"] == "available"
    assert fundamentals["source_key"] == "fmp_reported_statement_facts"
    assert fundamentals_client.calls == ("income", "balance", "cash_flow")


@pytest.mark.parametrize(
    ("mode", "api_key", "app_env"),
    (
        ("off", "test-key-not-real", "test"),
        ("", "test-key-not-real", "test"),
        ("live", "", "test"),
        ("live", "test-key-not-real", "production"),
    ),
)
def test_fmp_fundamentals_route_resolution_fails_closed_before_client_construction(
    mode: str,
    api_key: str,
    app_env: str,
) -> None:
    construction_calls = 0

    def _unexpected_factory(**_: object) -> _CountingFmpFundamentalsClient:
        nonlocal construction_calls
        construction_calls += 1
        return _CountingFmpFundamentalsClient()

    policy, context = report_routes._resolve_fmp_fundamentals_generation_context(
        settings=Settings(
            app_env=app_env,
            fmp_api_key=api_key,
            fmp_fundamentals_mode=mode,
        ),
        client_factory=_unexpected_factory,
    )

    assert policy is None
    assert context is None
    assert construction_calls == 0


def test_fmp_fundamentals_route_resolution_fails_closed_on_client_construction_error() -> None:
    def _failing_factory(**_: object) -> _CountingFmpFundamentalsClient:
        raise RuntimeError("synthetic construction failure")

    policy, context = report_routes._resolve_fmp_fundamentals_generation_context(
        settings=Settings(
            app_env="test",
            fmp_api_key="test-key-not-real",
            fmp_fundamentals_mode="live",
        ),
        client_factory=_failing_factory,
    )

    assert policy is None
    assert context is None


def test_generate_agent_team_report_route_threads_backend_p36_live_lane_flags(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="route-p36-lanes@example.com",
        source_reference="workspace_routep36lanes1",
    )
    provider = _RouteFakeLiveProvider()
    monkeypatch.setattr(agent_team_report_service, "resolve_backend_agent_team_report_generation_mode", lambda: "tool_mediated")
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_agent_team_report_provider_resolution",
        lambda: LLMProviderResolution(
            provider=provider,
            status="ok",
            provider_name="mock",
            model=provider.model,
        ),
    )
    monkeypatch.setattr(agent_team_report_service, "resolve_p36_live_lane_flags", lambda: (True, True, True))
    monkeypatch.setattr(report_routes, "_resolve_fmp_eod_history_generation_context", lambda: (None, None))

    captured: dict[str, object] = {}
    real_generate = agent_team_report_service.generate_agent_team_report_for_thread

    def _capture_generate(*args: object, **kwargs: object):
        captured.update(kwargs)
        return real_generate(*args, **kwargs)

    monkeypatch.setattr(agent_team_report_service, "generate_agent_team_report_for_thread", _capture_generate)

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    assert captured["p36_risk_live_enabled"] is True
    assert captured["p36_public_live_enabled"] is True
    assert captured["p36_pm_live_enabled"] is True


def test_generate_agent_team_report_route_wires_and_freezes_both_edgar_report_lanes(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="route-edgar-lanes@example.com",
        source_reference="workspace_routeedgarlanes1",
    )
    profile_client = _CountingEdgarProfileClient()
    filings_client = _CountingEdgarRecentFilingsClient()
    monkeypatch.setattr(
        report_routes,
        "_resolve_edgar_report_evidence_generation_context",
        lambda: (
            EdgarCompanyProfileSourcePolicy(enabled=True),
            profile_client,
            EdgarRecentFilingsSourcePolicy(enabled=True),
            filings_client,
        ),
    )
    monkeypatch.setattr(report_routes, "_resolve_fmp_eod_history_generation_context", lambda: (None, None))

    saved_thread = db_session.get(ReportThread, UUID(thread_id))
    assert saved_thread is not None
    assert isinstance(saved_thread.saved_artifact_json, dict)
    deterministic_baseline = deepcopy(saved_thread.saved_artifact_json["deterministic_summary"])
    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    generated = response.json()
    assert profile_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")
    assert filings_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")
    assert generated["deterministic_summary"] == deterministic_baseline
    profile = generated["public_evidence"]["public_company_profile"]
    filings = generated["public_evidence"]["public_events_calendar"]
    assert profile["availability"] == "available"
    assert filings["availability"] == "available"
    assert {fact["fact_key"] for fact in profile["facts"]}.isdisjoint({"sector", "industry", "subindustry", "peer_group"})
    public_rendered = repr(generated["public_evidence"]).lower()
    for forbidden in ("/archives/", "data.sec.gov", "raw_payload", "account_id", "provider_account_id"):
        assert forbidden not in public_rendered

    listed = client.get(f"/users/{user_id}/reports").json()
    detail = client.get(f"/users/{user_id}/reports/{thread_id}").json()
    assert listed[0]["agent_summary"] == generated["agent_summary"]
    assert detail["agent_summary"] == generated["agent_summary"]

    regenerated = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")
    assert regenerated.status_code == 201
    assert profile_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")
    assert filings_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")


def test_generate_agent_team_report_route_tool_mediated_mock_opt_in_persists_frozen_artifact(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="tool-mediated-mock@example.com",
        source_reference="workspace_toolmock1",
    )
    provider = _RouteFakeLiveProvider()
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: datetime(2026, 7, 2, 14, 0, tzinfo=UTC))
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_backend_agent_team_report_generation_mode",
        lambda: "tool_mediated",
    )
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_agent_team_report_provider_resolution",
        lambda: LLMProviderResolution(
            provider=provider,
            status="ok",
            provider_name="mock",
            model=provider.model,
        ),
    )

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    saved = response.json()
    summary = saved["agent_summary"]
    artifact = summary["tool_run_artifact"]
    assert provider.calls == []
    assert summary["provider_mode"] == "tool_mediated_mock"
    assert artifact is not None
    assert artifact["provider_mode"] == "tool_mediated_mock"
    assert artifact["tool_result_count"] > 0
    assert artifact["provider_runs"] == []
    rendered = repr(saved).lower()
    for forbidden in (
        "raw_payload",
        "source_url",
        "https://",
        "prompt:",
        "api_key",
        "access_token",
        "buying_power",
        "safe to trade",
        "ready to trade",
        "i recommend",
        "place order",
        "execute trade",
    ):
        assert forbidden not in rendered

    def _unexpected_tool_execution(*args: object, **kwargs: object) -> object:
        raise AssertionError("Saved report readback should not rerun tool execution")

    monkeypatch.setattr(tool_mediated_report, "execute_tool_request", _unexpected_tool_execution)
    detail_response = client.get(f"/users/{user_id}/reports/{thread_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["agent_summary"] == summary


def test_generate_agent_team_report_route_tool_mediated_live_opt_in_freezes_provider_runs(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="tool-mediated-live@example.com",
        source_reference="workspace_toollive1",
    )
    provider = _RouteFakeLiveProvider(
        content_by_role={
            "fundamentals_analyst": "Live fundamentals context cites reviewed public evidence as background.",
            "technical_analyst": "Live technical context cites saved market freshness as background.",
            "risk_management_agent": "Live risk context cites deterministic caveats as background.",
        }
    )
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: datetime(2026, 7, 2, 15, 0, tzinfo=UTC))
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_backend_agent_team_report_generation_mode",
        lambda: "tool_mediated",
    )
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_agent_team_report_provider_resolution",
        lambda: LLMProviderResolution(
            provider=provider,
            status="ok",
            provider_name=provider.provider_name,
            model=provider.model,
        ),
    )

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    saved = response.json()
    summary = saved["agent_summary"]
    artifact = summary["tool_run_artifact"]
    assert summary["provider_mode"] == "tool_mediated_live"
    assert artifact["provider_mode"] == "tool_mediated_live"
    assert provider.calls
    assert {run["provider"] for run in artifact["provider_runs"]} == {"fake_live_provider"}
    assert {run["model"] for run in artifact["provider_runs"]} == {"fake-live-model"}
    assert {run["prompt_version"] for run in artifact["provider_runs"]} == {LIVE_PROMPT_VERSION}
    assert all(run["status"] == "ok" for run in artifact["provider_runs"])
    assert "live_provider_reasoning_used" in repr(summary).lower()

    provider.calls.clear()
    detail_response = client.get(f"/users/{user_id}/reports/{thread_id}")
    list_response = client.get(f"/users/{user_id}/reports")
    assert detail_response.status_code == 200
    assert list_response.status_code == 200
    assert provider.calls == []
    assert detail_response.json()["agent_summary"] == summary
    assert list_response.json()[0]["agent_summary"] == summary


def test_generate_agent_team_report_route_unsafe_live_provider_output_fails_closed(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, thread_id = _create_saved_agent_report_thread(
        client,
        db_session,
        email="tool-mediated-unsafe@example.com",
        source_reference="workspace_toolunsafe1",
    )
    provider = _RouteFakeLiveProvider(
        content_by_role={"risk_management_agent": "You should submit order at $123."}
    )
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_backend_agent_team_report_generation_mode",
        lambda: "tool_mediated",
    )
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_agent_team_report_provider_resolution",
        lambda: LLMProviderResolution(
            provider=provider,
            status="ok",
            provider_name=provider.provider_name,
            model=provider.model,
        ),
    )

    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    saved = response.json()
    rendered = repr(saved["agent_summary"]).lower()
    assert saved["agent_summary"]["provider_mode"] == "tool_mediated_live"
    assert saved["agent_summary"]["tool_run_artifact"] is not None
    assert "live_provider_safety_fallback" in rendered
    assert "you should" not in rendered
    assert "submit order" not in rendered
    assert "$123" not in rendered


@pytest.mark.parametrize(
    ("preview_payload", "expected_flow", "expected_symbol", "expected_preview_caveat"),
    (
        (
            {
                "supported_flow": "stock_buy",
                "symbol": "XYZ",
                "quantity": "3",
                "price_assumption": "50",
            },
            "stock_buy",
            "XYZ",
            None,
        ),
        (
            {
                "supported_flow": "cash_secured_put",
                "option_leg": {
                    "underlying_symbol": "XYZ",
                    "option_type": "put",
                    "leg_action": "sell_to_open",
                    "expiration_date": "2026-06-19",
                    "strike": "50",
                    "quantity": "1",
                    "premium": "2",
                },
            },
            "cash_secured_put",
            "XYZ",
            "cash_secured_put_collateral_generic",
        ),
    ),
    ids=("stock-buy", "cash-secured-put"),
)
def test_db_backed_golden_path_preview_save_generate_readback_and_regenerate(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    preview_payload: dict,
    expected_flow: str,
    expected_symbol: str,
    expected_preview_caveat: str,
) -> None:
    user_id, account_reference = _create_connected_broker_account_reference(client, db_session)
    preview_response = client.post(
        "/trade-reviews/portfolio-preview",
        headers={"X-User-Id": user_id},
        json={
            **preview_payload,
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": account_reference,
            },
        },
    )

    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["supported_flow"] == expected_flow
    intent_symbol = preview["trade_intent_summary"].get("symbol") or preview["trade_intent_summary"].get(
        "underlying_symbol"
    )
    assert intent_symbol == expected_symbol
    assert "account_level_feasibility_not_evaluated" in preview["scope_metadata"]["scope_caveat_codes"]
    if expected_preview_caveat is not None:
        assert expected_preview_caveat in {caveat["code"] for caveat in preview["caveats"]}
    source_reference = preview["saved_review_source_reference"]
    assert source_reference is not None
    assert validate_trade_review_saved_source_reference(source_reference) == source_reference
    saved_source = db_session.scalar(
        select(SavedReviewSource).where(
            SavedReviewSource.user_id == UUID(user_id),
            SavedReviewSource.source_reference == source_reference,
            SavedReviewSource.deleted_at.is_(None),
        )
    )
    assert saved_source is not None
    assert saved_source.scope_metadata_json["scope_summary_label"] == preview["scope_metadata"]["scope_summary_label"]
    assert saved_source.deterministic_summary_json["supported_flow"] == expected_flow
    assert saved_source.deterministic_summary_json["symbol_or_underlying"] == expected_symbol
    derived_sections = saved_source.deterministic_summary_json.get("derived_exposure_sections") or []
    assert [section["section_key"] for section in derived_sections] == [
        "before_after_portfolio_impact",
        "concentration_risk_drift",
    ]

    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": source_reference,
            "title": f"Saved {expected_flow} golden-path review",
            "report_type": "trade_review",
            "scope_metadata": _scope_metadata_payload("Client supplied scope must be ignored"),
            "deterministic_summary": {
                **_deterministic_summary_payload(),
                "supported_flow": "covered_call",
                "symbol_or_underlying": "MSFT",
            },
        },
    )

    assert save_response.status_code == 201
    saved = save_response.json()
    assert saved["source_reference"] == source_reference
    _assert_saved_scope_preserves_review_selection_with_safe_caveats(
        saved["scope_metadata"],
        preview["scope_metadata"],
    )
    assert saved["deterministic_summary"]["supported_flow"] == expected_flow
    assert saved["deterministic_summary"]["symbol_or_underlying"] == expected_symbol
    assert saved["public_evidence"] is None
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(SavedReviewArtifactRead.model_validate(saved))
    assert evidence.source_snapshot.source_reference == source_reference
    assert evidence.trade_intent_summary.supported_flow == expected_flow
    assert evidence.trade_intent_summary.symbol_or_underlying == expected_symbol
    assert evidence.scope_state.account_level_feasibility_evaluated is False
    assert evidence.before_after_portfolio_impact.availability == "not_available"
    assert evidence.concentration_risk_drift.availability == "not_available"
    assert "account_snapshot_unavailable" in evidence.before_after_portfolio_impact.caveat_codes
    assert "account_snapshot_unavailable" in evidence.concentration_risk_drift.caveat_codes
    monkeypatch.setattr(
        exposure_adapter_service,
        "build_trade_exposure_impact",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("readback must not recompute exposure impact")),
    )
    reread_evidence = SavedEvidencePackageRead.from_saved_review_artifact(SavedReviewArtifactRead.model_validate(saved))
    assert reread_evidence.before_after_portfolio_impact == evidence.before_after_portfolio_impact
    assert reread_evidence.concentration_risk_drift == evidence.concentration_risk_drift
    assert saved["scope_metadata"]["review_account"]["display_label"] == "Swing account"
    assert evidence.scope_state.review_account_display_label == "Swing account"
    assert repr(saved["scope_metadata"]).lower().count("swing account") == 1
    assert repr(evidence.model_dump(mode="python")).lower().count("swing account") == 1

    saved_scope_without_nickname = deepcopy(saved["scope_metadata"])
    saved_scope_without_nickname["review_account"].pop("display_label")
    assert "swing account" not in repr(saved_scope_without_nickname).lower()

    evidence_without_nickname = evidence.model_dump(mode="python")
    evidence_without_nickname["scope_state"].pop("review_account_display_label")
    evidence_rendered = repr(evidence_without_nickname).lower()
    for forbidden in (
        account_reference.lower(),
        "provider_account_id_secret",
        "provider_connection_id_secret",
        "taxable account ending",
        "buying_power",
    ):
        assert forbidden not in evidence_rendered

    listed = client.get(f"/users/{user_id}/reports").json()
    assert len(listed) == 1
    thread_id = listed[0]["id"]
    assert listed[0]["scope_metadata"] == saved["scope_metadata"]

    first_generated_at = datetime(2026, 6, 22, 14, 0, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: first_generated_at)
    generated_response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")
    assert generated_response.status_code == 201
    generated = generated_response.json()
    assert generated["agent_summary"]["report_generated_at"] == first_generated_at.isoformat().replace("+00:00", "Z")
    assert generated["agent_summary"]["provider_mode"] == "deterministic_template"
    assert generated["agent_summary"]["tool_run_artifact"] is None
    assert generated["source_reference"] == saved["source_reference"]
    assert generated["scope_metadata"] == saved["scope_metadata"]
    assert repr(generated["scope_metadata"]).lower().count("swing account") == 1
    assert generated["deterministic_summary"] == saved["deterministic_summary"]
    assert generated["generated_at"] == saved["generated_at"]
    assert generated["public_evidence"]["public_evidence_mode"] == "not_reviewed"
    generated_summary_rendered = repr(generated["agent_summary"]).lower()
    for forbidden in (
        account_reference.lower(),
        "provider_account_id_secret",
        "provider_connection_id_secret",
        "taxable account ending",
        "buying_power",
    ):
        assert forbidden not in generated_summary_rendered
    assert generated["agent_summary"]["tool_run_artifact"] is None
    assert "swing account" not in repr(generated["agent_summary"]).lower()
    assert "swing account" not in repr(generated["public_evidence"]).lower()

    # Later mutable account state must not reinterpret the saved report scope or source snapshot.
    later_account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Later Broker",
            "account_type": "taxable_individual",
            "display_name": "Later Mutable Account",
            "base_currency": "USD",
        },
    )
    assert later_account_response.status_code == 201
    detail_after_mutation = client.get(f"/users/{user_id}/reports/{thread_id}").json()
    assert detail_after_mutation["scope_metadata"] == saved["scope_metadata"]
    assert detail_after_mutation["agent_summary"] == generated["agent_summary"]

    immutable_saved_source = {
        "source_reference": generated["source_reference"],
        "scope_metadata": generated["scope_metadata"],
        "deterministic_summary": generated["deterministic_summary"],
        "generated_at": generated["generated_at"],
        "public_evidence": generated["public_evidence"],
    }
    second_generated_at = datetime(2026, 6, 22, 14, 5, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: second_generated_at)
    regenerated_response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")
    assert regenerated_response.status_code == 201
    regenerated = regenerated_response.json()
    assert regenerated["agent_summary"]["report_generated_at"] == second_generated_at.isoformat().replace("+00:00", "Z")
    assert {
        "source_reference": regenerated["source_reference"],
        "scope_metadata": regenerated["scope_metadata"],
        "deterministic_summary": regenerated["deterministic_summary"],
        "generated_at": regenerated["generated_at"],
        "public_evidence": regenerated["public_evidence"],
    } == immutable_saved_source
    assert repr(regenerated["scope_metadata"]).lower().count("swing account") == 1
    regenerated_summary_rendered = repr(regenerated["agent_summary"]).lower()
    for forbidden in (
        account_reference.lower(),
        "provider_account_id_secret",
        "provider_connection_id_secret",
        "taxable account ending",
        "buying_power",
    ):
        assert forbidden not in regenerated_summary_rendered
    assert regenerated["agent_summary"]["tool_run_artifact"] is None
    assert "swing account" not in repr(regenerated["agent_summary"]).lower()
    assert "swing account" not in repr(regenerated["public_evidence"]).lower()

    saved_rendered = repr(
        {
            "saved": saved,
            "generated": generated,
            "regenerated": regenerated,
            "detail": detail_after_mutation,
        }
    ).lower()
    assert generated["scope_metadata"]["review_account"]["account_reference"] == account_reference
    assert regenerated["scope_metadata"]["review_account"]["account_reference"] == account_reference
    for forbidden in (
        "provider_account_id_secret",
        "provider_connection_id_secret",
        "taxable account ending",
        "raw_payload",
        "buying_power",
        "safe to trade",
        "ready to trade",
        "guaranteed return",
        "place order",
        "submit order",
        "execute trade",
        "i recommend",
    ):
        assert forbidden not in saved_rendered
    assert not find_forbidden_keys(saved, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(generated, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(regenerated, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_generate_agent_team_report_with_injected_edgar_profile_persists_and_reuses_saved_public_evidence(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_response = client.post(
        "/users", json={"display_name": "EDGAR Report User", "email": "edgar-report@example.com"}
    )
    user_id = user_response.json()["id"]
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="workspace_edgarprofile1",
        title="Saved EDGAR-backed review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Primary reviewed account"),
        deterministic_summary=_deterministic_summary_payload(),
        limitations=("Generated from reviewed data available at the time.",),
        caveat_codes=("selected_context_scope",),
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None
    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_edgarprofile1",
            "title": "Saved EDGAR-backed review",
            "report_type": "trade_review",
        },
    )
    assert save_response.status_code == 201
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]
    edgar_client = _CountingEdgarProfileClient()

    report_generated_at = datetime(2026, 6, 16, 14, 0, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: report_generated_at)
    summary = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(thread_id),
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=edgar_client,
    )

    assert summary is not None
    assert edgar_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")
    report_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(thread_id))
    assert report_thread is not None
    artifact = report_service.saved_review_artifact_for_thread(report_thread)
    public_evidence = artifact.public_evidence
    assert public_evidence is not None
    profile = public_evidence.public_company_profile
    facts = {fact.fact_key: fact.value_label for fact in profile.facts}
    assert public_evidence.public_evidence_mode == "provider_reference"
    assert profile.availability == "available"
    assert facts == {
        "company_name": "Hood Example Markets, Inc.",
        "ticker": "HOOD",
        "exchange": "Nasdaq",
        "cik_reference": "CIK 0000123456",
        "sic_label": "Security Brokers, Dealers & Flotation Companies",
        "fiscal_year_end": "12/31",
    }
    assert "sector" not in facts
    assert "industry" not in facts
    assert "subindustry" not in facts
    assert "peer_group" not in facts
    assert artifact.agent_summary is not None
    fundamentals = next(
        role for role in artifact.agent_summary.role_summaries if role.role_name == "fundamentals_analyst"
    )
    assert fundamentals.role_status == "completed"
    assert fundamentals.evidence_references == ("trade_intent_summary", "public_company_profile")
    assert "SEC EDGAR metadata - company profile only" in (fundamentals.summary_markdown or "")
    assert "0000123456" not in (fundamentals.summary_markdown or "")
    assert "12/31" not in (fundamentals.summary_markdown or "")

    detail_response = client.get(f"/users/{user_id}/reports/{thread_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert "public_evidence" not in detail
    assert detail["public_evidence_attribution"] == {
        "section_key": "public_company_profile",
        "source_key": "sec_edgar_submissions",
        "source_label": "SEC EDGAR metadata - company profile only",
        "availability": "available",
        "has_sic_label": True,
    }
    rendered_detail = repr(detail).lower()
    assert "security brokers" not in rendered_detail
    assert "cik 0000123456" not in rendered_detail
    assert "12/31" not in rendered_detail
    assert "hood example markets" not in rendered_detail
    assert "investment advice" not in rendered_detail
    assert edgar_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")

    raising_client = _CountingEdgarProfileClient(raise_on_call=True)
    second_generated_at = datetime(2026, 6, 16, 14, 5, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: second_generated_at)
    regenerated = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(thread_id),
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=raising_client,
    )

    assert regenerated is not None
    assert raising_client.calls == ()
    refreshed_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(thread_id))
    assert refreshed_thread is not None
    refreshed_artifact = report_service.saved_review_artifact_for_thread(refreshed_thread)
    assert refreshed_artifact.public_evidence == artifact.public_evidence
    assert refreshed_artifact.agent_summary is not None
    assert refreshed_artifact.agent_summary.report_generated_at == second_generated_at


def test_fresh_report_thread_acquires_all_approved_public_evidence_once_and_preserves_historical_thread(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post(
        "/users",
        json={"display_name": "Fresh Frozen Source User", "email": "fresh-frozen-source@example.com"},
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    source_reference = "workspace_freshfrozen1"
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference=source_reference,
        title="Saved frozen-source review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Synthetic review account"),
        deterministic_summary=_deterministic_summary_payload(),
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None

    historical_save = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": source_reference,
            "title": "Historical saved review",
            "report_type": "trade_review",
        },
    )
    assert historical_save.status_code == 201
    assert historical_save.json()["public_evidence"] is None
    historical_thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]
    historical_thread = db_session.get(ReportThread, UUID(historical_thread_id))
    assert historical_thread is not None
    historical_artifact_json = deepcopy(historical_thread.saved_artifact_json)

    fresh_save = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": source_reference,
            "title": "Fresh saved review",
            "report_type": "trade_review",
        },
    )
    assert fresh_save.status_code == 201
    assert fresh_save.json()["public_evidence"] is None
    report_threads = client.get(f"/users/{user_id}/reports").json()
    fresh_thread_id = report_threads[0]["id"]
    assert fresh_thread_id != historical_thread_id
    fresh_thread = db_session.get(ReportThread, UUID(fresh_thread_id))
    assert fresh_thread is not None
    assert fresh_thread.saved_artifact_json["public_evidence"] is None

    profile_client = _CountingEdgarProfileClient()
    filings_client = _CountingEdgarRecentFilingsClient()
    fundamentals_client = _CountingFmpFundamentalsClient()
    eod_client = _CountingFmpEodClient()
    generated = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(fresh_thread_id),
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=profile_client,
        edgar_recent_filings_policy=EdgarRecentFilingsSourcePolicy(enabled=True),
        edgar_recent_filings_client=filings_client,
        fmp_fundamentals_policy=FmpFundamentalsSourcePolicy(enabled=True),
        fmp_fundamentals_context=fmp_fundamentals_execution_context_for_client(
            fundamentals_client,
            collected_at=datetime(2026, 7, 16, 12, tzinfo=UTC),
        ),
        fmp_eod_history_policy=MarketContextPolicy(mode="live"),
        fmp_eod_history_context=market_context_execution_context_for_client(
            eod_client,
            collected_at=datetime(2026, 7, 16, 12, tzinfo=UTC),
        ),
    )

    assert generated is not None
    assert profile_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")
    assert filings_client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000123456")
    assert fundamentals_client.calls == ("income", "balance", "cash_flow")
    assert eod_client.calls == (("HOOD", 260),)
    generated_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(fresh_thread_id))
    assert generated_thread is not None
    generated_artifact = report_service.saved_review_artifact_for_thread(generated_thread)
    assert generated_artifact.public_evidence is not None
    public_evidence = generated_artifact.public_evidence
    assert public_evidence.public_company_profile.availability == "available"
    assert public_evidence.public_events_calendar.availability == "available"
    assert public_evidence.public_fundamentals_snapshot.availability == "available"
    assert public_evidence.public_market_context.availability == "available"
    assert public_evidence.fred_macro_series_snapshot is not None
    assert public_evidence.fred_macro_series_snapshot.availability == "not_reviewed"
    frozen_public_evidence_bytes = json.dumps(
        public_evidence.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    raising_profile_client = _CountingEdgarProfileClient(raise_on_call=True)
    raising_filings_client = _CountingEdgarRecentFilingsClient(raise_on_call=True)
    raising_fundamentals_client = _CountingFmpFundamentalsClient(raise_on_call=True)
    raising_eod_client = _CountingFmpEodClient(raise_on_call=True)
    regenerated = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(fresh_thread_id),
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=raising_profile_client,
        edgar_recent_filings_policy=EdgarRecentFilingsSourcePolicy(enabled=True),
        edgar_recent_filings_client=raising_filings_client,
        fmp_fundamentals_policy=FmpFundamentalsSourcePolicy(enabled=True),
        fmp_fundamentals_context=fmp_fundamentals_execution_context_for_client(raising_fundamentals_client),
        fmp_eod_history_policy=MarketContextPolicy(mode="live"),
        fmp_eod_history_context=market_context_execution_context_for_client(raising_eod_client),
    )

    assert regenerated is not None
    assert raising_profile_client.calls == ()
    assert raising_filings_client.calls == ()
    assert raising_fundamentals_client.calls == ()
    assert raising_eod_client.calls == ()
    regenerated_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(fresh_thread_id))
    assert regenerated_thread is not None
    regenerated_artifact = report_service.saved_review_artifact_for_thread(regenerated_thread)
    assert regenerated_artifact.public_evidence is not None
    assert json.dumps(
        regenerated_artifact.public_evidence.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") == frozen_public_evidence_bytes

    db_session.expire_all()
    unchanged_historical_thread = db_session.get(ReportThread, UUID(historical_thread_id))
    assert unchanged_historical_thread is not None
    assert unchanged_historical_thread.saved_artifact_json == historical_artifact_json


def test_generate_agent_team_report_freezes_fmp_and_fred_snapshots_without_regeneration_refetch(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_response = client.post(
        "/users", json={"display_name": "Source Snapshot User", "email": "source-snapshot@example.com"}
    )
    user_id = user_response.json()["id"]
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="workspace_sourcesnapshot1",
        title="Saved normalized-source review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Synthetic review account"),
        deterministic_summary=_deterministic_summary_payload(),
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None
    saved = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_sourcesnapshot1",
            "title": "Saved normalized-source review",
            "report_type": "trade_review",
        },
    )
    assert saved.status_code == 201
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]
    fmp_client = _CountingFmpFundamentalsClient()
    fred_client = _CountingFredMacroSeriesClient()
    fmp_context = fmp_fundamentals_execution_context_for_client(
        fmp_client,
        collected_at=datetime(2026, 7, 12, 12, tzinfo=UTC),
    )
    fred_context = fred_macro_series_execution_context_for_client(
        fred_client,
        collected_at=datetime(2026, 7, 12, 12, tzinfo=UTC),
    )

    summary = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(thread_id),
        fmp_fundamentals_policy=FmpFundamentalsSourcePolicy(enabled=True),
        fmp_fundamentals_context=fmp_context,
        fred_macro_series_policy=FredMacroSeriesSourcePolicy(enabled=True),
        fred_macro_series_context=fred_context,
    )

    assert summary is not None
    assert fmp_client.calls == ("income", "balance", "cash_flow")
    assert fred_client.calls == 6
    report_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(thread_id))
    assert report_thread is not None
    artifact = report_service.saved_review_artifact_for_thread(report_thread)
    assert artifact.public_evidence is not None
    assert artifact.public_evidence.public_fundamentals_snapshot.availability == "available"
    assert artifact.public_evidence.fred_macro_series_snapshot is not None
    assert artifact.public_evidence.fred_macro_series_snapshot.availability == "available"
    frozen_payload = artifact.public_evidence.model_dump(mode="python")
    assert not find_forbidden_keys(frozen_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    for forbidden in ("raw_payload", "https://", "api_key", "prompt", "trace", "provider_account_id"):
        assert forbidden not in repr(frozen_payload).lower()

    regenerated = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(thread_id),
        fmp_fundamentals_policy=FmpFundamentalsSourcePolicy(enabled=True),
        fmp_fundamentals_context=fmp_fundamentals_execution_context_for_client(
            _CountingFmpFundamentalsClient(raise_on_call=True)
        ),
        fred_macro_series_policy=FredMacroSeriesSourcePolicy(enabled=True),
        fred_macro_series_context=fred_macro_series_execution_context_for_client(
            _CountingFredMacroSeriesClient(raise_on_call=True)
        ),
    )

    assert regenerated is not None
    refreshed_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(thread_id))
    assert refreshed_thread is not None
    refreshed_artifact = report_service.saved_review_artifact_for_thread(refreshed_thread)
    assert refreshed_artifact.public_evidence == artifact.public_evidence


def test_generate_agent_team_report_with_unavailable_edgar_degrades_safely(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_response = client.post(
        "/users", json={"display_name": "EDGAR Unavailable User", "email": "edgar-unavailable@example.com"}
    )
    user_id = user_response.json()["id"]
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="workspace_edgarprofile2",
        title="Saved EDGAR unavailable review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Primary reviewed account"),
        deterministic_summary=_deterministic_summary_payload(),
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None
    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_edgarprofile2",
            "title": "Saved EDGAR unavailable review",
            "report_type": "trade_review",
        },
    )
    assert save_response.status_code == 201
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]
    edgar_client = _CountingEdgarProfileClient(
        exception_message="https://data.sec.gov/submissions/raw_payload/account_id"
    )

    report_generated_at = datetime(2026, 6, 16, 15, 0, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: report_generated_at)
    summary = agent_team_report_service.generate_agent_team_report_for_thread(
        db_session,
        UUID(user_id),
        UUID(thread_id),
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=edgar_client,
    )

    assert summary is not None
    report_thread = report_service.get_report_thread(db_session, UUID(user_id), UUID(thread_id))
    assert report_thread is not None
    artifact = report_service.saved_review_artifact_for_thread(report_thread)
    assert artifact.agent_summary is not None
    assert artifact.agent_summary.report_status == "full_agent_report"
    assert artifact.public_evidence is not None
    assert artifact.public_evidence.public_evidence_mode == "not_reviewed"
    assert artifact.public_evidence.public_company_profile.availability == "not_available"
    assert artifact.public_evidence.public_company_profile.caveat_codes == ("edgar_replay_unavailable",)
    detail_response = client.get(f"/users/{user_id}/reports/{thread_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["public_evidence_attribution"] is None
    rendered = repr(artifact.model_dump(mode="python")).lower()
    assert "data.sec.gov" not in rendered
    assert "raw_payload" not in rendered
    assert "account_id" not in rendered


def test_generate_agent_team_report_gates_blocked_actionability(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_response = client.post("/users", json={"display_name": "Gated Report User", "email": "gated-report@example.com"})
    user_id = user_response.json()["id"]
    deterministic = {
        **_deterministic_summary_payload(),
        "review_actionability_status": "blocked_stale_market_quote",
        "actionability_label": "Blocked by stale market quote",
    }
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="workspace_agentreport2",
        title="Saved blocked review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Primary reviewed account"),
        deterministic_summary=deterministic,
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None
    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_agentreport2",
            "title": "Saved blocked review",
            "report_type": "trade_review",
        },
    )
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]

    report_generated_at = datetime(2026, 6, 15, 19, 0, tzinfo=UTC)
    monkeypatch.setattr(agent_team_report_service, "_now_utc", lambda: report_generated_at)
    response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert response.status_code == 201
    saved = response.json()
    assert saved["agent_summary"]["report_status"] == "deterministic_draft"
    assert saved["agent_summary"]["report_generated_at"] == report_generated_at.isoformat().replace("+00:00", "Z")
    assert saved["agent_summary"]["final_synthesis_markdown"] is not None
    assert "What you would be ignoring if you acted manually now" in saved["agent_summary"]["final_synthesis_markdown"]
    assert "Manual verification checklist" in saved["agent_summary"]["final_synthesis_markdown"]
    assert {role["role_status"] for role in saved["agent_summary"]["role_summaries"]} == {"gated"}
    assert "blocked_actionability_llm_roles_skipped" in saved["agent_summary"]["warning_codes"]


def test_saved_review_artifact_requires_resolved_scoped_review_source(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "Missing Source", "email": "missing-source@example.com"})
    user_id = user_response.json()["id"]

    response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "title": "Missing reviewed source",
            "scope_metadata": _scope_metadata_payload("Client supplied scope is not a source"),
            "deterministic_summary": _deterministic_summary_payload(),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved review source not found"


def test_saved_review_artifact_source_resolution_is_user_scoped(
    client: TestClient,
    db_session: Session,
) -> None:
    owner_response = client.post("/users", json={"display_name": "Source Owner", "email": "source-owner@example.com"})
    owner_id = owner_response.json()["id"]
    other_response = client.post("/users", json={"display_name": "Source Other", "email": "source-other@example.com"})
    other_id = other_response.json()["id"]
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="workspace_savedreview2",
        title="Owner saved review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Owner reviewed account"),
        deterministic_summary=_deterministic_summary_payload(),
    )
    assert report_service.record_saved_review_source(db_session, UUID(owner_id), source_payload) is not None

    response = client.post(
        f"/users/{other_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview2",
            "title": "Cross-user save attempt",
            "scope_metadata": _scope_metadata_payload("Other reviewed account"),
            "deterministic_summary": _deterministic_summary_payload(),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved review source not found"


def test_saved_review_artifact_malformed_source_fails_before_report_commit(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "Malformed Source", "email": "malformed@example.com"})
    user_id = user_response.json()["id"]
    db_session.add(
        SavedReviewSource(
            user_id=UUID(user_id),
            source_kind="trade_review_workspace",
            source_reference="workspace_savedreview3",
            scope_metadata_json={},
            deterministic_summary_json={},
            generated_at=datetime.now(UTC),
            review_pipeline_label="Portfolio Copilot review pipeline",
            limitations_json=[],
            caveat_codes_json=[],
        )
    )
    db_session.commit()

    response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview3",
            "title": "Malformed source should not save",
        },
    )
    list_response = client.get(f"/users/{user_id}/reports")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved review source not found"
    assert list_response.status_code == 200
    assert list_response.json() == []


@pytest.mark.parametrize(
    "unsafe_source_fields",
    (
        {"limitations_json": ["You should buy after reading this snapshot."]},
        {"caveat_codes_json": ["raw_payload"]},
        {"review_pipeline_label": "provider_account_id pipeline"},
    ),
)
def test_saved_review_artifact_unsafe_source_metadata_fails_before_report_commit(
    client: TestClient,
    db_session: Session,
    unsafe_source_fields: dict,
) -> None:
    user_response = client.post("/users", json={"display_name": "Unsafe Source", "email": "unsafe-source@example.com"})
    user_id = user_response.json()["id"]
    source_fields = {
        "user_id": UUID(user_id),
        "source_kind": "trade_review_workspace",
        "source_reference": "workspace_savedreview4",
        "scope_metadata_json": _scope_metadata_payload("Primary reviewed account"),
        "deterministic_summary_json": _deterministic_summary_payload(),
        "generated_at": datetime.now(UTC),
        "review_pipeline_label": "Portfolio Copilot review pipeline",
        "limitations_json": ["Generated from reviewed data available at the time."],
        "caveat_codes_json": ["selected_context_scope"],
    }
    source_fields.update(unsafe_source_fields)
    db_session.add(SavedReviewSource(**source_fields))
    db_session.commit()

    response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview4",
            "title": "Unsafe source should not save",
        },
    )
    list_response = client.get(f"/users/{user_id}/reports")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved review source not found"
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_saved_review_artifact_rejects_forbidden_private_fields_and_wording(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "Unsafe Saved", "email": "unsafe-saved@example.com"})
    user_id = user_response.json()["id"]

    unsafe_ref_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_provider123",
            "title": "Unsafe saved source",
            "scope_metadata": _scope_metadata_payload("Primary reviewed account"),
            "deterministic_summary": _deterministic_summary_payload(),
        },
    )
    assert unsafe_ref_response.status_code == 422

    unsafe_wording_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "title": "Unsafe wording",
            "scope_metadata": _scope_metadata_payload("Primary reviewed account"),
            "deterministic_summary": {
                **_deterministic_summary_payload(),
                "actionability_label": "I recommend buying after review.",
            },
        },
    )
    assert unsafe_wording_response.status_code == 422


def test_create_report_for_missing_user_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/users/00000000-0000-0000-0000-000000000001/reports",
        json={"title": "Synthetic report"},
    )

    assert response.status_code == 404


def test_create_report_for_account_owned_by_another_user_returns_404(client: TestClient, db_session: Session) -> None:
    owner_response = client.post("/users", json={"display_name": "Owner", "email": "report-owner@example.com"})
    owner_id = owner_response.json()["id"]
    other_response = client.post("/users", json={"display_name": "Other", "email": "report-other@example.com"})
    other_id = other_response.json()["id"]
    account_response = client.post(
        f"/users/{owner_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Owner Account",
            "base_currency": "USD",
        },
    )

    response = client.post(
        f"/users/{other_id}/reports",
        json={"account_id": account_response.json()["id"], "title": "Synthetic report"},
    )

    assert response.status_code == 404


def test_get_report_thread_for_wrong_user_returns_404(client: TestClient, db_session: Session) -> None:
    owner_response = client.post("/users", json={"display_name": "Owner", "email": "detail-owner@example.com"})
    owner_id = owner_response.json()["id"]
    other_response = client.post("/users", json={"display_name": "Other", "email": "detail-other@example.com"})
    other_id = other_response.json()["id"]
    report_response = client.post(f"/users/{owner_id}/reports", json={"title": "Synthetic report"})

    response = client.get(f"/users/{other_id}/reports/{report_response.json()['id']}")

    assert response.status_code == 404


def _create_saved_agent_report_thread(
    client: TestClient,
    db_session: Session,
    *,
    email: str,
    source_reference: str,
    deterministic_summary: dict | None = None,
) -> tuple[str, str]:
    user_response = client.post("/users", json={"display_name": "Tool-Mediated Report User", "email": email})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    source_payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference=source_reference,
        title="Saved tool-mediated review",
        report_type="trade_review",
        scope_metadata=_scope_metadata_payload("Primary reviewed account"),
        deterministic_summary=deterministic_summary or _deterministic_summary_payload(),
        limitations=("Generated from reviewed data available at the time.",),
        caveat_codes=("selected_context_scope",),
    )
    assert report_service.record_saved_review_source(db_session, UUID(user_id), source_payload) is not None
    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": source_reference,
            "title": "Saved tool-mediated review",
            "report_type": "trade_review",
        },
    )
    assert save_response.status_code == 201
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]
    return user_id, thread_id


class _RouteFakeLiveProvider:
    provider_name = "fake_live_provider"
    model = "fake-live-model"

    def __init__(
        self,
        *,
        status_by_role: dict[str, LLMProviderStatus] | None = None,
        content_by_role: dict[str, str] | None = None,
    ) -> None:
        self.status_by_role = dict(status_by_role or {})
        self.content_by_role = dict(content_by_role or {})
        self.calls: list[LLMProviderRequest] = []

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        self.calls.append(request)
        status = self.status_by_role.get(request.role_name, "ok")
        if status != "ok":
            return LLMProviderResponse(
                request_id=request.request_id,
                role_name=request.role_name,
                status=status,
                provider=self.provider_name,
                model=self.model,
                prompt_version=request.prompt_version,
                content_markdown=None,
                is_mock=False,
                error_code=status,
                error_message="Provider unavailable; deterministic evidence remains available.",
                metadata={"safe_partial_output": "true"},
            )
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status="ok",
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=self.content_by_role.get(
                request.role_name,
                "Live role context cites supplied evidence as background for manual review.",
            ),
            is_mock=False,
            metadata={"safe_partial_output": "false"},
        )


def _scope_metadata_payload(review_account_label: str) -> dict:
    return {
        "review_account": {
            "account_reference": "acctref_savedreview1",
            "display_label": review_account_label,
            "account_kind_label": "Taxable brokerage",
            "is_review_account": True,
            "is_included_in_portfolio_scope": True,
            "is_account_level_feasibility_source": True,
        },
        "portfolio_context_scope": {
            "scope_reference": "scope_savedreview1",
            "scope_mode": "selected_context",
            "display_label": "Selected reviewed context",
            "selection_mode": "latest_available",
            "context_reference": "ctx_savedreview1",
            "included_account_labels": (),
            "excluded_account_labels": (),
            "account_level_feasibility_evaluated": True,
            "account_level_feasibility_label": "Account-level feasibility evaluated for selected review account",
            "caveat_codes": ("selected_context_scope",),
        },
        "scope_summary_label": "Review account selected · Context scope: Selected reviewed context.",
        "account_level_feasibility_evaluated": True,
        "scope_caveat_codes": ("selected_context_scope",),
    }


def _deterministic_summary_payload() -> dict:
    return {
        "supported_flow": "covered_call",
        "review_flow_label": "Covered call",
        "symbol_or_underlying": "HOOD",
        "review_actionability_status": "analysis_only",
        "actionability_label": "Analysis-only review",
        "highest_severity": "warning",
        "report_status": "generated",
        "broker_snapshot_freshness_label": "Broker snapshot from generated review",
        "market_quote_freshness_label": "Market quote from generated review",
        "caveat_codes": ("selected_context_scope", "account_level_feasibility_not_evaluated"),
    }


def _create_connected_broker_account_reference(client: TestClient, db_session: Session) -> tuple[str, str]:
    user_response = client.post(
        "/users",
        json={"display_name": "Golden Path User", "email": "golden-path@example.com"},
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    connection = BrokerConnection(
        user_id=UUID(user_id),
        provider="snaptrade",
        broker_name="Fidelity raw name should not render",
        provider_connection_id="provider_connection_id_secret_golden",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(connection)
    db_session.flush()
    db_session.add(
        BrokerAccount(
            broker_connection_id=connection.id,
            provider_account_id="provider_account_id_secret_golden",
            display_name="Taxable account ending 1234 should not render",
            user_nickname="Swing account",
            account_type="taxable_individual",
            sync_status="idle",
            data_freshness_status="fresh",
        )
    )
    db_session.commit()

    account_details_response = client.get(f"/users/{user_id}/account-details")
    assert account_details_response.status_code == 200
    account_details = account_details_response.json()
    assert account_details["data_mode"] == "private_real_source"
    assert account_details["portfolio_scope"]["account_level_feasibility_evaluated"] is False
    assert account_details["accounts"]
    account = account_details["accounts"][0]
    assert account["account_reference"].startswith("acctref_")
    assert account["display_label"] == "Swing account"
    assert account["source_kind"] == "snaptrade"
    assert account["source_label"] == "SnapTrade"
    assert account["connection_status_label"]
    assert account["account_level_feasibility_evaluated"] is False
    rendered = repr(account_details).lower()
    for forbidden in (
        "provider_account_id_secret",
        "provider_connection_id_secret",
        "taxable account ending",
        "raw_payload",
    ):
        assert forbidden not in rendered
    assert not find_forbidden_keys(account_details, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    return user_id, account["account_reference"]


def _assert_saved_scope_preserves_review_selection_with_safe_caveats(
    saved_scope: dict,
    preview_scope: dict,
) -> None:
    assert saved_scope["review_account"] == preview_scope["review_account"]
    assert saved_scope["scope_summary_label"] == preview_scope["scope_summary_label"]
    assert (
        saved_scope["account_level_feasibility_evaluated"]
        == preview_scope["account_level_feasibility_evaluated"]
    )

    saved_portfolio_scope = dict(saved_scope["portfolio_context_scope"])
    preview_portfolio_scope = dict(preview_scope["portfolio_context_scope"])
    saved_portfolio_caveats = tuple(saved_portfolio_scope.pop("caveat_codes"))
    preview_portfolio_caveats = tuple(preview_portfolio_scope.pop("caveat_codes"))
    assert saved_portfolio_scope == preview_portfolio_scope

    saved_caveats = tuple(saved_scope["scope_caveat_codes"])
    expected_saved_caveats = _saved_review_safe_caveat_code_tuple(tuple(preview_scope["scope_caveat_codes"]))
    expected_saved_portfolio_caveats = _saved_review_safe_caveat_code_tuple(preview_portfolio_caveats)
    assert saved_caveats == expected_saved_caveats
    assert saved_portfolio_caveats == expected_saved_portfolio_caveats

    rendered_saved_caveats = repr((*saved_caveats, *saved_portfolio_caveats)).lower()
    assert "buying_power" not in rendered_saved_caveats
    assert "cash_collateral" not in rendered_saved_caveats
    assert "collateral_unverified" not in rendered_saved_caveats

    rendered_preview_caveats = repr((*preview_scope["scope_caveat_codes"], *preview_portfolio_caveats)).lower()
    if any(token in rendered_preview_caveats for token in ("buying_power", "cash_collateral", "collateral_unverified")):
        assert "liquidity_model_unverified" in saved_caveats or "liquidity_model_unverified" in saved_portfolio_caveats
        assert (
            "account_feasibility_not_evaluated" in saved_caveats
            or "account_feasibility_not_evaluated" in saved_portfolio_caveats
            or "account_level_feasibility_not_evaluated" in saved_caveats
            or "account_level_feasibility_not_evaluated" in saved_portfolio_caveats
        )


class _CountingEdgarProfileClient:
    def __init__(self, *, raise_on_call: bool = False, exception_message: str | None = None) -> None:
        self.raise_on_call = raise_on_call
        self.exception_message = exception_message
        self._calls: list[str] = []

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch_company_tickers(self) -> dict:
        self._calls.append("fetch_company_tickers")
        if self.raise_on_call:
            raise AssertionError("EDGAR client should not be called for saved public evidence")
        if self.exception_message is not None:
            raise RuntimeError(self.exception_message)
        return {"0": {"cik_str": 123456, "ticker": "HOOD", "title": "Hood Example Markets, Inc."}}

    def fetch_submissions(self, cik_reference: str) -> dict:
        self._calls.append(f"fetch_submissions:{cik_reference}")
        if self.raise_on_call:
            raise AssertionError("EDGAR client should not be called for saved public evidence")
        return {
            "name": "Hood Example Markets, Inc.",
            "tickers": ["HOOD"],
            "exchanges": ["Nasdaq"],
            "sicDescription": "Security Brokers, Dealers & Flotation Companies",
            "fiscalYearEnd": "1231",
            "sector": "Financial Services",
            "industry": "Brokerage",
            "subindustry": "Retail Brokerage",
            "peer_group": "Trading Apps",
        }


class _CountingEdgarRecentFilingsClient:
    def __init__(self, *, raise_on_call: bool = False) -> None:
        self.raise_on_call = raise_on_call
        self._calls: list[str] = []

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch_company_tickers(self) -> dict:
        self._calls.append("fetch_company_tickers")
        if self.raise_on_call:
            raise AssertionError("EDGAR recent-filings client should not be called for saved public evidence")
        return {"0": {"cik_str": 123456, "ticker": "HOOD", "title": "Hood Example Markets, Inc."}}

    def fetch_submissions(self, cik_reference: str) -> dict:
        self._calls.append(f"fetch_submissions:{cik_reference}")
        if self.raise_on_call:
            raise AssertionError("EDGAR recent-filings client should not be called for saved public evidence")
        return {
            "filings": {
                "recent": {
                    "form": ["8-K"],
                    "filingDate": ["2026-06-01"],
                    "accessionNumber": ["0000001234-26-000001"],
                }
            }
        }


class _CountingFmpFundamentalsClient:
    def __init__(self, *, raise_on_call: bool = False) -> None:
        self.raise_on_call = raise_on_call
        self._calls: list[str] = []

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch_income_statement(self, *, symbol: str) -> list[dict]:
        self._calls.append("income")
        self._raise_if_needed()
        return [
            {
                "fiscal_period": "Q1 2026",
                "report_date": "2026-05-01",
                "currency": "USD",
                "revenue": "1200",
                "grossProfit": "600",
                "operatingIncome": "210",
                "netIncome": "160",
                "eps": "1.25",
            }
        ]

    def fetch_balance_sheet(self, *, symbol: str) -> list[dict]:
        self._calls.append("balance")
        self._raise_if_needed()
        return [
            {
                "fiscal_period": "Q1 2026",
                "report_date": "2026-05-01",
                "currency": "USD",
                "totalAssets": "5000",
                "totalLiabilities": "1900",
                "totalDebt": "800",
                "totalCurrentAssets": "1800",
                "totalCurrentLiabilities": "900",
            }
        ]

    def fetch_cash_flow(self, *, symbol: str) -> list[dict]:
        self._calls.append("cash_flow")
        self._raise_if_needed()
        return [
            {
                "fiscal_period": "Q1 2026",
                "report_date": "2026-05-01",
                "currency": "USD",
                "operatingCashFlow": "310",
                "capitalExpenditure": "-75",
                "freeCashFlow": "235",
            }
        ]

    def _raise_if_needed(self) -> None:
        if self.raise_on_call:
            raise AssertionError("frozen public evidence must not re-fetch FMP statement facts")


class _CountingFmpEodClient:
    def __init__(self, *, raise_on_call: bool = False) -> None:
        self.raise_on_call = raise_on_call
        self._calls: list[tuple[str, int]] = []

    @property
    def calls(self) -> tuple[tuple[str, int], ...]:
        return tuple(self._calls)

    def fetch_eod_history(self, *, symbol: str, limit: int = 260) -> tuple[dict[str, object], ...]:
        self._calls.append((symbol, limit))
        if self.raise_on_call:
            raise AssertionError("frozen public evidence must not re-fetch FMP EOD history")
        start = date(2025, 1, 1)
        return tuple(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": str(index + 1),
                "high": str(index + 2),
                "low": str(index),
                "close": str(index + 1),
                "volume": 1000 + index,
            }
            for index in reversed(range(limit))
        )


class _CountingFredMacroSeriesClient:
    def __init__(self, *, raise_on_call: bool = False) -> None:
        self.raise_on_call = raise_on_call
        self.calls = 0

    def fetch_series_observation(self, *, series_id: str) -> dict:
        self.calls += 1
        if self.raise_on_call:
            raise AssertionError("frozen public evidence must not re-fetch FRED series")
        return {
            "observation_date": "2026-06-01",
            "value": "3.2",
            "unit": "Percent",
            "frequency": "Monthly",
        }
