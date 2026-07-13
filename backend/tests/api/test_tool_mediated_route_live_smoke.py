"""Opt-in route-backed live LLM smoke for saved Agent Team reports.

WARNING: real external LLM call. Do not run without explicit founder approval.

This test is excluded from the default suite by the ``external``/``slow``
markers. It also skips unless all opt-in gates are present:

    RUN_LIVE_LLM_TESTS=true
    POA_AGENT_TEAM_ROUTE_LIVE=1
    POA_AGENT_TEAM_REPORT_GENERATION_MODE=tool_mediated
    POA_LLM_MODE=live
    POA_LLM_PROVIDER=google
    GOOGLE_API_KEY=<already exported in the shell>

Optional: POA_LLM_MODEL_CANDIDATES=<id1,id2,...> (max 4) activates the ordered
same-provider model chain in the backend provider resolution; the frozen
provider_runs then include model_chain_position and attempted_models.

When ``RUN_LIVE_LLM_TESTS=true`` is already set, the test helper may retrieve
only the named ``GOOGLE_API_KEY`` variable from the project ``.env``; it does not
load broad app config from that file.

Run from ``backend`` against a disposable ``*_test`` database. Do not pass the
key inline and do not run against real brokerage data.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, build_settings
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.services.agent_team.llm_clients import google as google_provider
from app.services.agent_team import tool_mediated_report
from app.services.agent_team.llm_clients.contracts import (
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.llm_clients.config import live_llm_tests_enabled
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports import agent_team_report as agent_team_report_service
from tests.agent_team_report_artifacts import write_tool_mediated_saved_report_artifacts
from tests.live_llm_config import load_live_llm_test_config


pytestmark = [pytest.mark.api, pytest.mark.db, pytest.mark.external, pytest.mark.slow]


def _route_live_opt_in() -> bool:
    load_live_llm_test_config()
    live_tests = live_llm_tests_enabled(os.environ)
    route_ack = os.environ.get("POA_AGENT_TEAM_ROUTE_LIVE", "").strip().lower() in {"1", "true", "yes", "on"}
    tool_mode = os.environ.get("POA_AGENT_TEAM_REPORT_GENERATION_MODE", "").strip().lower() in {
        "tool_mediated",
        "tool-mediated",
        "tool_mediated_live",
    }
    llm_mode = os.environ.get("POA_LLM_MODE", "").strip().lower() == "live"
    provider = os.environ.get("POA_LLM_PROVIDER", "").strip().lower() == "google"
    has_key = bool(_live_settings().google_api_key)
    return live_tests and route_ack and tool_mode and llm_mode and provider and has_key


def _live_settings() -> Settings:
    return build_settings(env=os.environ, load_dotenv=False)


@pytest.mark.skipif(
    not _route_live_opt_in(),
    reason=(
        "opt-in route-backed Gemini live smoke disabled; requires RUN_LIVE_LLM_TESTS=true, "
        "POA_AGENT_TEAM_ROUTE_LIVE=1, POA_AGENT_TEAM_REPORT_GENERATION_MODE=tool_mediated, "
        "POA_LLM_MODE=live, POA_LLM_PROVIDER=google, and GOOGLE_API_KEY"
    ),
)
def test_route_backed_tool_mediated_live_report_freezes_and_reads_back_without_rerun(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get("POA_AGENT_TEAM_ROUTE_LIVE_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
        original_generate = google_provider._GoogleGenAIClient.generate

        def _debug_generate(self: object, request: object) -> str:
            role_name = str(getattr(request, "role_name", "unknown"))
            model = str(getattr(request, "model", "unknown"))
            messages = tuple(getattr(request, "messages", ()))
            prompt_len = sum(len(str(getattr(message, "content", ""))) for message in messages)
            print("debug_live_route_request", role_name, model, "chars", prompt_len, "messages", len(messages))
            try:
                return original_generate(self, request)  # type: ignore[arg-type]
            except Exception as exc:
                print(
                    "debug_live_route_exception",
                    role_name,
                    type(exc).__name__,
                    "status",
                    getattr(exc, "status", None),
                    "code",
                    getattr(exc, "code", None),
                )
                raise

        monkeypatch.setattr(google_provider._GoogleGenAIClient, "generate", _debug_generate)

    user_id, account_reference = _create_synthetic_review_account(client, db_session)
    preview_response = client.post(
        "/trade-reviews/portfolio-preview",
        headers={"X-User-Id": user_id},
        json={
            "supported_flow": "stock_buy",
            "symbol": os.environ.get("POA_ROUTE_SMOKE_SYMBOL", "XYZ").strip().upper() or "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": account_reference,
            },
        },
    )

    assert preview_response.status_code == 200
    preview = preview_response.json()
    source_reference = preview["saved_review_source_reference"]
    assert isinstance(source_reference, str) and source_reference.startswith("trrev_")

    save_response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": source_reference,
            "title": "Live tool-mediated route smoke",
            "report_type": "trade_review",
        },
    )
    assert save_response.status_code == 201
    thread_id = client.get(f"/users/{user_id}/reports").json()[0]["id"]

    generated_response = client.post(f"/users/{user_id}/reports/{thread_id}/agent-team-report")

    assert generated_response.status_code == 201
    generated = generated_response.json()
    summary = generated["agent_summary"]
    artifact = summary["tool_run_artifact"]
    assert summary["provider_mode"] == "tool_mediated_live"
    assert artifact is not None
    assert artifact["provider_mode"] == "tool_mediated_live"
    assert artifact["provider_runs"], "expected at least one live provider run"
    assert {run["provider"] for run in artifact["provider_runs"]} == {"google"}
    provider_statuses = sorted({str(run["status"]) for run in artifact["provider_runs"]})
    assert any(run["status"] == "ok" for run in artifact["provider_runs"]), provider_statuses
    assert "live_provider_reasoning_used" in repr(summary).lower()
    assert summary["report_status"] == "full_agent_report"

    # P34A-T10A: when a model chain is configured, the frozen provider runs
    # must carry the additive chain metadata (model ids and positions only).
    candidates_env = os.environ.get("POA_LLM_MODEL_CANDIDATES", "").strip()
    if candidates_env:
        candidate_ids = [item.strip() for item in candidates_env.split(",") if item.strip()]
        for run in artifact["provider_runs"]:
            assert run.get("model") in candidate_ids
            position = run.get("model_chain_position")
            assert position is not None and 0 <= int(position) < len(candidate_ids)
            attempted = list(run.get("attempted_models") or ())
            assert attempted, "attempted_models must be frozen for chained runs"
            assert attempted[-1] == run["model"]
            assert all(item in candidate_ids for item in attempted)
        print(
            "chain_freeze_check",
            sorted(
                {
                    (run["model"], int(run["model_chain_position"]), ",".join(run["attempted_models"]))
                    for run in artifact["provider_runs"]
                }
            ),
        )

    _assert_live_saved_summary_safe(summary)

    def _unexpected_tool_execution(*args: object, **kwargs: object) -> object:
        raise AssertionError("Saved report readback must not rerun tool execution")

    def _unexpected_provider_resolution() -> object:
        raise AssertionError("Saved report readback must not resolve a live provider")

    monkeypatch.setattr(tool_mediated_report, "execute_tool_request", _unexpected_tool_execution)
    monkeypatch.setattr(
        agent_team_report_service,
        "resolve_agent_team_report_provider_resolution",
        _unexpected_provider_resolution,
    )
    detail_response = client.get(f"/users/{user_id}/reports/{thread_id}")
    list_response = client.get(f"/users/{user_id}/reports")
    assert detail_response.status_code == 200
    assert list_response.status_code == 200
    assert detail_response.json()["agent_summary"] == summary
    assert list_response.json()[0]["agent_summary"] == summary
    write_tool_mediated_saved_report_artifacts(
        detail_response.json(),
        label="route-backed-tool-mediated-live-smoke",
    )


def _create_synthetic_review_account(client: TestClient, db_session: Session) -> tuple[str, str]:
    user_response = client.post(
        "/users",
        json={"display_name": "Live Route Smoke User", "email": "live-route-smoke@example.com"},
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    connection = BrokerConnection(
        user_id=UUID(user_id),
        provider="snaptrade",
        broker_name="Synthetic broker raw name should not render",
        provider_connection_id="provider_connection_id_secret_live_route",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(connection)
    db_session.flush()
    db_session.add(
        BrokerAccount(
            broker_connection_id=connection.id,
            provider_account_id="provider_account_id_secret_live_route",
            display_name="Synthetic account ending 4321 should not render",
            user_nickname="Live smoke review account",
            account_type="taxable_individual",
            sync_status="idle",
            data_freshness_status="fresh",
        )
    )
    db_session.commit()

    account_details_response = client.get(f"/users/{user_id}/account-details")
    assert account_details_response.status_code == 200
    account_details = account_details_response.json()
    account = account_details["accounts"][0]
    assert account["account_reference"].startswith("acctref_")
    rendered = repr(account_details).lower()
    for forbidden in (
        "provider_account_id_secret_live_route",
        "provider_connection_id_secret_live_route",
        "synthetic account ending",
        "raw_payload",
    ):
        assert forbidden not in rendered
    assert not find_forbidden_keys(account_details, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    return user_id, account["account_reference"]


def _assert_live_saved_summary_safe(summary: dict) -> None:
    rendered = repr(summary).lower()
    for forbidden in (
        "provider_account_id_secret_live_route",
        "provider_connection_id_secret_live_route",
        "synthetic account ending",
        "live smoke review account",
        "raw_payload",
        "source_url",
        "https://",
        "http://",
        "prompt:",
        "api_key",
        "access_token",
        "buying_power",
        "safe to trade",
        "ready to trade",
        "guaranteed return",
        "place order",
        "submit order",
        "execute trade",
        "i recommend",
    ):
        assert forbidden not in rendered
    assert not find_forbidden_keys(summary, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_string_values(summary)
    assert not find_secret_like_values(summary)
    assert not find_prohibited_llm_phrases(summary)
