from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.report_message import ReportMessage
from app.models.saved_review_source import SavedReviewSource
from app.schemas.reports import SavedReviewArtifactCreateRequest
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports import agent_team_report as agent_team_report_service
from app.services.reports import crud as report_service
from app.services.reports.public_evidence import EdgarCompanyProfileSourcePolicy


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
        "Review account: Primary reviewed account · Context scope: Selected reviewed context."
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
        "Review account: Primary reviewed account · Context scope: Selected reviewed context."
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
    rendered = repr(saved).lower()
    assert "primary reviewed account" not in rendered
    assert "acctref_savedreview1" not in rendered
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
            "included_account_labels": (review_account_label,),
            "excluded_account_labels": (),
            "account_level_feasibility_evaluated": True,
            "account_level_feasibility_label": "Account-level feasibility evaluated for selected review account",
            "caveat_codes": ("selected_context_scope",),
        },
        "scope_summary_label": f"Review account: {review_account_label} · Context scope: Selected reviewed context.",
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
