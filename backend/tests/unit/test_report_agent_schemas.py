from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.report_thread import ReportThread
from app.models.saved_review_source import SavedReviewSource
from app.schemas.agent_runs import AgentRunCreate, AgentStepCreate
from app.schemas.reports import (
    AgentTeamReportRead,
    AgentTeamReportRoleSectionRead,
    AgentTeamReportSynthesisRead,
    ReportMessageCreate,
    ReportThreadCreate,
    ReportThreadRead,
    ReportPublicEvidenceAttributionRead,
    SavedAgentTeamRoleSummaryRead,
    SavedAgentTeamSummaryRead,
    SavedDeterministicReviewSummaryRead,
    SavedEvidencePackageRead,
    SavedEvidenceSectionRead,
    SavedPublicEvidencePackageRead,
    SavedPublicEvidenceSectionRead,
    SavedPublicRoleEvidenceProjectionRead,
    SavedReviewArtifactCreateRequest,
    SavedReviewArtifactRead,
    SavedReviewReportMetadataRead,
)
from app.schemas.trade_review_workspace import PortfolioScopeRead, ReportScopeMetadataRead, ReviewAccountRead
from app.services.reports.crud import (
    _saved_artifact_json_can_be_committed,
    _saved_review_source_payload_is_valid,
    saved_review_artifact_for_thread,
)
from app.services.reports.agent_team_report import (
    build_agent_team_summary_from_evidence,
    build_validation_failed_summary_for_test,
)
from app.services.reports.public_evidence import (
    EdgarCompanyProfileHttpClient,
    EdgarCompanyProfileSourcePolicy,
    EdgarSourceUnavailableError,
    build_edgar_company_profile_live_smoke_projection,
    build_public_evidence_projection,
    build_public_role_evidence_projection,
)
from app.services.agent_team.report_output_safety import validate_agent_team_report_output


pytestmark = pytest.mark.unit

_PUBLIC_ROLES = frozenset({"fundamentals_analyst", "news_analyst", "technical_analyst"})


def test_report_thread_create_schema() -> None:
    account_id = uuid4()
    payload = ReportThreadCreate(
        account_id=account_id,
        title="Synthetic report",
        report_type="portfolio_review",
        status="draft",
    )

    assert payload.account_id == account_id
    assert payload.title == "Synthetic report"
    assert payload.report_type == "portfolio_review"
    assert payload.status == "draft"


def test_report_thread_read_exposes_nullable_saved_scope_metadata() -> None:
    payload = ReportThreadRead(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Legacy report",
        report_type="portfolio_review",
        status="completed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    assert payload.scope_metadata is None


def test_report_thread_read_accepts_reviewed_saved_scope_metadata_shape() -> None:
    scope_metadata = _saved_scope_metadata()

    payload = ReportThreadRead(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Generated report",
        report_type="trade_review",
        status="completed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
        scope_metadata=scope_metadata,
    )

    assert payload.scope_metadata is not None
    assert payload.scope_metadata.scope_summary_label.startswith("Review account:")
    assert payload.scope_metadata.account_level_feasibility_evaluated is True


def test_report_thread_read_projects_scope_from_saved_artifact_json_only() -> None:
    generated = datetime.now(UTC)
    saved_scope = _saved_scope_metadata()
    report_thread = ReportThread(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Saved reviewed report",
        report_type="trade_review",
        status="completed",
        created_at=generated,
        updated_at=generated,
        deleted_at=None,
        saved_artifact_json={
            "artifact_reference": "svrev_savedreview1",
            "scope_metadata": saved_scope.model_dump(mode="json"),
            "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
            "agent_summary": None,
            "generated_at": generated.isoformat(),
            "saved_at": generated.isoformat(),
            "review_pipeline_label": "Portfolio Copilot review pipeline",
            "limitations": ("Generated from reviewed data available at the time.",),
            "caveat_codes": ("selected_context_scope",),
        },
    )

    read = ReportThreadRead.model_validate(report_thread)
    artifact = saved_review_artifact_for_thread(report_thread)

    assert read.scope_metadata is not None
    assert read.scope_metadata.scope_summary_label == saved_scope.scope_summary_label
    assert artifact.scope_metadata is not None
    assert artifact.scope_metadata.scope_summary_label == saved_scope.scope_summary_label
    assert artifact.deterministic_summary is not None
    assert artifact.report.report_reference == "svrev_savedreview1"


def test_saved_review_source_payload_validation_rejects_incomplete_stored_json() -> None:
    source = SavedReviewSource(
        user_id=uuid4(),
        source_kind="trade_review_workspace",
        source_reference="workspace_savedreview1",
        scope_metadata_json={},
        deterministic_summary_json={},
        generated_at=datetime.now(UTC),
        review_pipeline_label="Portfolio Copilot review pipeline",
        limitations_json=[],
        caveat_codes_json=[],
    )

    assert _saved_review_source_payload_is_valid(source) is False


def test_saved_review_source_payload_validation_accepts_complete_stored_json() -> None:
    source = SavedReviewSource(
        user_id=uuid4(),
        source_kind="trade_review_workspace",
        source_reference="workspace_savedreview1",
        scope_metadata_json=_saved_scope_metadata().model_dump(mode="json"),
        deterministic_summary_json=_saved_deterministic_summary().model_dump(mode="json"),
        generated_at=datetime.now(UTC),
        review_pipeline_label="Portfolio Copilot review pipeline",
        limitations_json=[],
        caveat_codes_json=[],
    )

    assert _saved_review_source_payload_is_valid(source) is True


@pytest.mark.parametrize(
    "unsafe_update",
    (
        {"limitations": ("You should buy after reading this snapshot.",)},
        {"caveat_codes": ("raw_payload",)},
        {"review_pipeline_label": "provider_account_id pipeline"},
    ),
)
def test_saved_artifact_precommit_validation_rejects_unsafe_source_metadata(
    unsafe_update: dict[str, object],
) -> None:
    saved_at = datetime.now(UTC)
    saved_artifact_json = {
        "artifact_reference": "svrev_savedreview1",
        "source_kind": "trade_review_workspace",
        "source_reference": "workspace_savedreview1",
        "scope_metadata": _saved_scope_metadata().model_dump(mode="json"),
        "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
        "agent_summary": None,
        "generated_at": saved_at.isoformat(),
        "saved_at": saved_at.isoformat(),
        "review_pipeline_label": "Portfolio Copilot review pipeline",
        "limitations": ("Generated from reviewed data available at the time.",),
        "caveat_codes": ("selected_context_scope",),
    }
    saved_artifact_json.update(unsafe_update)

    assert (
        _saved_artifact_json_can_be_committed(
            saved_artifact_json,
            title="Saved reviewed report",
            report_type="trade_review",
            status="completed",
            created_at=saved_at,
            updated_at=saved_at,
        )
        is False
    )


def test_saved_artifact_precommit_validation_accepts_complete_safe_source_metadata() -> None:
    saved_at = datetime.now(UTC)
    saved_artifact_json = {
        "artifact_reference": "svrev_savedreview1",
        "source_kind": "trade_review_workspace",
        "source_reference": "workspace_savedreview1",
        "scope_metadata": _saved_scope_metadata().model_dump(mode="json"),
        "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
        "agent_summary": None,
        "generated_at": saved_at.isoformat(),
        "saved_at": saved_at.isoformat(),
        "review_pipeline_label": "Portfolio Copilot review pipeline",
        "limitations": ("Generated from reviewed data available at the time.",),
        "caveat_codes": ("selected_context_scope",),
    }

    assert (
        _saved_artifact_json_can_be_committed(
            saved_artifact_json,
            title="Saved reviewed report",
            report_type="trade_review",
            status="completed",
            created_at=saved_at,
            updated_at=saved_at,
        )
        is True
    )


def test_saved_review_artifact_create_request_accepts_opaque_source_reference_only() -> None:
    payload = SavedReviewArtifactCreateRequest(
        source_kind="trade_review_workspace",
        source_reference="trrev_savedreview1",
        title="Saved covered-call review",
    )

    assert payload.source_reference == "trrev_savedreview1"
    assert payload.report_type == "saved_review_artifact"

    with pytest.raises(ValidationError):
        SavedReviewArtifactCreateRequest(
            source_kind="trade_review_workspace",
            source_reference="provider_account_id_123",
            title="Unsafe source",
        )


@pytest.mark.parametrize(
    ("source_kind", "source_reference"),
    (
        ("trade_review_workspace", "trrev_savedreview1"),
        ("trade_review_workspace", "workspace_savedreview1"),
        ("agent_team_run", "agentrun_savedreview1"),
    ),
)
def test_saved_review_artifact_create_request_preserves_valid_source_reference_examples(
    source_kind: str,
    source_reference: str,
) -> None:
    payload = SavedReviewArtifactCreateRequest(
        source_kind=source_kind,
        source_reference=source_reference,
        title="Saved review snapshot",
    )

    assert payload.source_reference == source_reference


@pytest.mark.parametrize(
    "source_reference",
    (
        "trrev_broker123",
        "workspace_provider123",
        "agentrun_account123",
        "trrev_raw_payload1",
        "workspace_prompt123",
    ),
)
def test_saved_review_artifact_create_request_rejects_private_source_reference_hints(
    source_reference: str,
) -> None:
    with pytest.raises(ValidationError):
        SavedReviewArtifactCreateRequest(
            source_kind="trade_review_workspace",
            source_reference=source_reference,
            title="Saved review snapshot",
        )


def test_saved_review_artifact_read_preserves_generation_time_scope_and_summaries() -> None:
    generated = datetime.now(UTC)
    payload = SavedReviewArtifactRead(
        artifact_reference="svrev_savedreview1",
        source_kind="trade_review_workspace",
        source_reference="trrev_savedreview1",
        status="saved",
        report=SavedReviewReportMetadataRead(
            report_reference="svrev_savedreview1",
            title="Saved covered-call review",
            report_type="trade_review",
            status="completed",
            created_at=generated,
            updated_at=generated,
        ),
        scope_metadata=_saved_scope_metadata(),
        deterministic_summary=SavedDeterministicReviewSummaryRead(
            supported_flow="covered_call",
            review_flow_label="Covered call",
            symbol_or_underlying="HOOD",
            review_actionability_status="analysis_only",
            actionability_label="Analysis-only review",
            highest_severity="warning",
            report_status="generated",
            broker_snapshot_freshness_label="Broker snapshot from generated review",
            market_quote_freshness_label="Market quote from generated review",
            caveat_codes=("selected_context_scope", "account_level_feasibility_not_evaluated"),
        ),
        agent_summary=SavedAgentTeamSummaryRead(
            run_status="completed",
            provider_mode="mock",
            role_summaries=(
                SavedAgentTeamRoleSummaryRead(
                    role_name="portfolio_manager_agent",
                    display_name="Portfolio Manager",
                    provider_status="ok",
                    summary_markdown="Analysis-only synthesis from saved review output.",
                    warning_codes=(),
                ),
            ),
            warning_codes=(),
        ),
        generated_at=generated,
        saved_at=generated,
        review_pipeline_label="Portfolio Copilot review pipeline",
        limitations=("Saved review snapshot generated from reviewed data available at the time.",),
        caveat_codes=("selected_context_scope",),
    )

    assert payload.scope_metadata is not None
    assert payload.source_reference == "trrev_savedreview1"
    assert payload.report.report_reference == "svrev_savedreview1"
    assert payload.deterministic_summary is not None
    assert payload.agent_summary is not None


def test_saved_evidence_package_projects_from_saved_artifact_without_account_labels_or_refs() -> None:
    artifact = _saved_review_artifact()

    evidence = SavedEvidencePackageRead.from_saved_review_artifact(artifact)
    rendered = repr(evidence.model_dump(mode="python")).lower()

    assert evidence.evidence_schema_version == "p29a_t1_v1"
    assert evidence.requires_runtime_tools is False
    assert evidence.source_snapshot.artifact_reference == artifact.artifact_reference
    assert evidence.source_snapshot.source_reference == "trrev_savedreview1"
    assert evidence.trade_intent_summary.supported_flow == "covered_call"
    assert evidence.trade_intent_summary.symbol_or_underlying == "HOOD"
    assert evidence.scope_state.review_account_selected is True
    assert evidence.scope_state.portfolio_scope_mode == "selected_context"
    assert evidence.scope_state.account_level_feasibility_evaluated is True
    assert evidence.market_quote_freshness.summary_label == "Market quote from generated review"
    assert evidence.economic_awareness_snapshot.availability == "not_reviewed"
    assert evidence.market_mood_snapshot.availability == "not_reviewed"
    assert evidence.public_evidence is not None
    assert evidence.public_evidence.public_evidence_schema_version == "p29b_public_v1"
    assert evidence.public_evidence.public_company_profile.availability == "not_reviewed"
    assert evidence.public_evidence.public_company_profile.rights_status == "not_reviewed"
    assert "fidelity taxable" not in rendered
    assert "acctref_reportscope1" not in rendered
    assert "ctx_reportscope1" not in rendered


def test_saved_evidence_package_uses_saved_public_evidence_when_present() -> None:
    public_evidence = SavedPublicEvidencePackageRead.not_reviewed("HOOD").model_copy(
        update={
            "public_evidence_mode": "synthetic_demo",
            "public_company_profile": _reviewed_public_section(
                "public_company_profile",
                "Public company profile",
                "Reviewed synthetic company profile attached at generation time.",
            ),
        }
    )
    artifact = _saved_review_artifact().model_copy(update={"public_evidence": public_evidence})

    evidence = SavedEvidencePackageRead.from_saved_review_artifact(artifact)

    assert evidence.public_evidence is not None
    assert evidence.public_evidence.public_evidence_mode == "synthetic_demo"
    assert evidence.public_evidence.public_company_profile.availability == "available"
    assert evidence.public_evidence.public_company_profile.summary_label == (
        "Reviewed synthetic company profile attached at generation time."
    )


def test_saved_review_artifact_for_thread_reads_public_evidence_from_saved_json() -> None:
    generated = datetime.now(UTC)
    public_evidence = SavedPublicEvidencePackageRead.not_reviewed("HOOD").model_copy(
        update={
            "public_evidence_mode": "synthetic_demo",
            "public_company_profile": _reviewed_public_section(
                "public_company_profile",
                "Public company profile",
                "Reviewed synthetic company profile attached at generation time.",
            ),
        }
    )
    report_thread = ReportThread(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Saved reviewed report",
        report_type="trade_review",
        status="completed",
        created_at=generated,
        updated_at=generated,
        deleted_at=None,
        saved_artifact_json={
            "artifact_reference": "svrev_savedreview1",
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "scope_metadata": _saved_scope_metadata().model_dump(mode="json"),
            "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
            "agent_summary": None,
            "public_evidence": public_evidence.model_dump(mode="json"),
            "generated_at": generated.isoformat(),
            "saved_at": generated.isoformat(),
            "review_pipeline_label": "Portfolio Copilot review pipeline",
            "limitations": ("Generated from reviewed data available at the time.",),
            "caveat_codes": ("selected_context_scope",),
        },
    )

    artifact = saved_review_artifact_for_thread(report_thread)
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(artifact)

    assert artifact.public_evidence is not None
    assert evidence.public_evidence is not None
    assert evidence.public_evidence.public_company_profile.availability == "available"


def test_report_thread_read_projects_edgar_public_evidence_attribution_only_from_saved_source_key() -> None:
    generated = datetime.now(UTC)
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(),
    )
    report_thread = ReportThread(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Saved reviewed report",
        report_type="trade_review",
        status="completed",
        created_at=generated,
        updated_at=generated,
        deleted_at=None,
        saved_artifact_json={
            "artifact_reference": "svrev_savedreview1",
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "scope_metadata": _saved_scope_metadata().model_dump(mode="json"),
            "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
            "agent_summary": None,
            "public_evidence": public_evidence.model_dump(mode="json"),
            "generated_at": generated.isoformat(),
            "saved_at": generated.isoformat(),
            "review_pipeline_label": "Portfolio Copilot review pipeline",
            "limitations": ("Generated from reviewed data available at the time.",),
            "caveat_codes": ("selected_context_scope",),
        },
    )

    read = ReportThreadRead.model_validate(report_thread)

    assert read.public_evidence_attribution is not None
    assert read.public_evidence_attribution.model_dump(mode="python") == {
        "section_key": "public_company_profile",
        "source_key": "sec_edgar_submissions",
        "source_label": "SEC EDGAR metadata - company profile only",
        "availability": "available",
        "has_sic_label": True,
    }
    rendered = repr(read.model_dump(mode="python")).lower()
    assert "security brokers" not in rendered
    assert "cik 0000001234" not in rendered
    assert "12/31" not in rendered
    assert "example public test company" not in rendered
    assert "investment advice" not in rendered


def test_report_thread_read_public_evidence_attribution_is_null_without_saved_source_key() -> None:
    generated = datetime.now(UTC)
    public_evidence = SavedPublicEvidencePackageRead.not_reviewed("HOOD").model_copy(
        update={
            "public_evidence_mode": "synthetic_demo",
            "public_company_profile": _reviewed_public_section(
                "public_company_profile",
                "Public company profile",
                "Reviewed synthetic company profile attached at generation time.",
            ),
        }
    )
    report_thread = ReportThread(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Saved reviewed report",
        report_type="trade_review",
        status="completed",
        created_at=generated,
        updated_at=generated,
        deleted_at=None,
        saved_artifact_json={
            "artifact_reference": "svrev_savedreview1",
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "scope_metadata": _saved_scope_metadata().model_dump(mode="json"),
            "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
            "agent_summary": None,
            "public_evidence": public_evidence.model_dump(mode="json"),
            "generated_at": generated.isoformat(),
            "saved_at": generated.isoformat(),
            "review_pipeline_label": "Portfolio Copilot review pipeline",
            "limitations": ("Generated from reviewed data available at the time.",),
            "caveat_codes": ("selected_context_scope",),
        },
    )

    read = ReportThreadRead.model_validate(report_thread)

    assert read.public_evidence_attribution is None


def test_report_thread_read_projects_limited_edgar_attribution_without_literal_sic() -> None:
    generated = datetime.now(UTC)
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(
            submissions={
                "name": "Example Public Test Company, Inc.",
                "tickers": ["EXMP"],
            }
        ),
    )
    report_thread = ReportThread(
        id=uuid4(),
        user_id=uuid4(),
        account_id=None,
        title="Saved reviewed report",
        report_type="trade_review",
        status="completed",
        created_at=generated,
        updated_at=generated,
        deleted_at=None,
        saved_artifact_json={
            "artifact_reference": "svrev_savedreview1",
            "source_kind": "trade_review_workspace",
            "source_reference": "workspace_savedreview1",
            "scope_metadata": _saved_scope_metadata().model_dump(mode="json"),
            "deterministic_summary": _saved_deterministic_summary().model_dump(mode="json"),
            "agent_summary": None,
            "public_evidence": public_evidence.model_dump(mode="json"),
            "generated_at": generated.isoformat(),
            "saved_at": generated.isoformat(),
            "review_pipeline_label": "Portfolio Copilot review pipeline",
            "limitations": ("Generated from reviewed data available at the time.",),
            "caveat_codes": ("selected_context_scope",),
        },
    )

    read = ReportThreadRead.model_validate(report_thread)

    assert read.public_evidence_attribution is not None
    assert read.public_evidence_attribution.availability == "limited"
    assert read.public_evidence_attribution.has_sic_label is False
    rendered = repr(read.model_dump(mode="python")).lower()
    assert "sic label" not in rendered
    assert "cik 0000001234" not in rendered


def test_saved_public_evidence_package_defaults_to_not_reviewed_sections() -> None:
    public_evidence = SavedPublicEvidencePackageRead.not_reviewed("HOOD")

    sections = (
        public_evidence.public_company_profile,
        public_evidence.public_fundamentals_snapshot,
        public_evidence.public_news_snapshot,
        public_evidence.public_events_calendar,
        public_evidence.public_technical_context,
        public_evidence.public_market_context,
    )

    assert public_evidence.public_evidence_mode == "not_reviewed"
    assert {section.section_key for section in sections} == {
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_news_snapshot",
        "public_events_calendar",
        "public_technical_context",
        "public_market_context",
    }
    assert {section.availability for section in sections} == {"not_reviewed"}
    assert {section.rights_status for section in sections} == {"not_reviewed"}


def test_public_evidence_projection_default_provider_is_not_reviewed_and_offline() -> None:
    public_evidence = build_public_evidence_projection(symbol_or_underlying="HOOD")

    assert public_evidence.public_evidence_mode == "not_reviewed"
    assert public_evidence.symbol_or_underlying == "HOOD"
    assert public_evidence.public_news_snapshot.availability == "not_reviewed"
    assert public_evidence.public_technical_context.source_label == "No reviewed public source attached"


def test_edgar_company_profile_policy_disabled_fails_closed_without_client_call() -> None:
    client = _ReplayEdgarProfileClient(raise_on_call=True)

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=False),
        edgar_client=client,
    )

    assert client.calls == ()
    assert public_evidence.public_company_profile.availability == "not_available"
    assert public_evidence.public_company_profile.caveat_codes == ("edgar_source_disabled",)
    assert public_evidence.public_fundamentals_snapshot.availability == "not_reviewed"


def test_edgar_company_profile_invalid_live_user_agent_policy_fails_closed_without_client_call() -> None:
    client = _ReplayEdgarProfileClient(raise_on_call=True)
    policy = EdgarCompanyProfileSourcePolicy(
        enabled=True,
        external_access_enabled=True,
        runtime_environment="local",
        declared_user_agent=None,
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=policy,
        edgar_client=client,
    )

    assert policy.live_client_ready() is False
    assert client.calls == ()
    assert public_evidence.public_company_profile.availability == "not_available"
    assert public_evidence.public_company_profile.caveat_codes == ("edgar_live_policy_not_ready",)


def test_edgar_company_profile_valid_live_policy_is_readiness_only_for_future_client() -> None:
    policy = EdgarCompanyProfileSourcePolicy(
        enabled=True,
        external_access_enabled=True,
        runtime_environment="local",
        declared_user_agent="Portfolio Copilot local demo contact engineering@example.test",
        request_timeout_seconds=3.0,
        response_size_cap_bytes=100_000,
        request_budget_per_run=2,
    )

    assert policy.live_client_ready() is True


def test_edgar_company_profile_http_client_requires_live_ready_policy() -> None:
    with pytest.raises(EdgarSourceUnavailableError):
        EdgarCompanyProfileHttpClient(
            policy=EdgarCompanyProfileSourcePolicy(enabled=True, external_access_enabled=True),
            transport=_FakeEdgarHttpTransport(),
        )


def test_edgar_company_profile_http_client_uses_injected_transport_without_network() -> None:
    policy = _live_ready_edgar_policy()
    client = EdgarCompanyProfileHttpClient(policy=policy, transport=_FakeEdgarHttpTransport())

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=policy,
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    facts = {fact.fact_key: fact.value_label for fact in profile.facts}
    assert profile.availability == "available"
    assert facts["company_name"] == "Example Public Test Company, Inc."
    assert facts["cik_reference"] == "CIK 0000001234"
    assert client.request_count == 2


def test_edgar_company_profile_http_client_enforces_request_budget() -> None:
    policy = _live_ready_edgar_policy(request_budget_per_run=2)
    client = EdgarCompanyProfileHttpClient(policy=policy, transport=_FakeEdgarHttpTransport())

    client.fetch_company_tickers()
    client.fetch_submissions("CIK 0000001234")

    with pytest.raises(EdgarSourceUnavailableError):
        client.fetch_company_tickers()


def test_edgar_company_profile_live_smoke_helper_uses_explicit_policy_and_fake_transport() -> None:
    public_evidence = build_edgar_company_profile_live_smoke_projection(
        symbol_or_underlying="EXMP",
        declared_user_agent="Portfolio Copilot local demo contact engineering@example.test",
        runtime_environment="local",
        transport=_FakeEdgarHttpTransport(),
    )

    profile = public_evidence.public_company_profile
    facts = {fact.fact_key: fact.value_label for fact in profile.facts}
    assert public_evidence.public_evidence_mode == "provider_reference"
    assert profile.availability == "available"
    assert profile.source_label == "SEC EDGAR metadata - company profile only"
    assert profile.limitations == (
        "SEC EDGAR profile evidence is limited to structured company identity metadata.",
        "Normalized identity facts only; raw EDGAR payloads are not retained.",
        "SEC SIC metadata may be broad, legacy, and may lag company changes; EDGAR metadata does not include financial analysis, filing text, or investment conclusions.",
    )
    assert facts["company_name"] == "Example Public Test Company, Inc."
    assert facts["ticker"] == "EXMP"


def test_edgar_company_profile_replay_success_normalizes_profile_section() -> None:
    client = _ReplayEdgarProfileClient()

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="exmp",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    facts = {fact.fact_key: fact.value_label for fact in profile.facts}
    assert public_evidence.public_evidence_mode == "provider_reference"
    assert profile.availability == "available"
    assert profile.rights_status == "reviewed"
    assert profile.source_key == "sec_edgar_submissions"
    assert profile.source_label == "SEC EDGAR metadata - company profile only"
    assert facts == {
        "company_name": "Example Public Test Company, Inc.",
        "ticker": "EXMP",
        "exchange": "Nasdaq",
        "cik_reference": "CIK 0000001234",
        "sic_label": "Security Brokers, Dealers & Flotation Companies",
        "fiscal_year_end": "12/31",
    }
    assert client.calls == ("fetch_company_tickers", "fetch_submissions:CIK 0000001234")


def test_edgar_company_profile_keeps_sic_label_source_specific_not_normalized_classification() -> None:
    client = _ReplayEdgarProfileClient(
        submissions={
            "name": "Example Semiconductor Test Company, Inc.",
            "tickers": ["EXMP"],
            "exchanges": ["Nasdaq"],
            "sicDescription": "Semiconductors & Related Devices",
            "fiscalYearEnd": "1231",
            "sector": "Technology",
            "industry": "Semiconductors",
            "subindustry": "Graphics Processors",
            "peer_group": "Chipmakers",
        }
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    facts = {fact.fact_key: fact.value_label for fact in profile.facts}
    assert profile.availability == "available"
    assert facts["sic_label"] == "Semiconductors & Related Devices"
    assert "sector" not in facts
    assert "industry" not in facts
    assert "subindustry" not in facts
    assert "peer_group" not in facts
    assert "Technology" not in repr(public_evidence)
    assert "Graphics Processors" not in repr(public_evidence)
    assert (
        "SEC SIC metadata may be broad, legacy, and may lag company changes; EDGAR metadata does not include financial analysis, filing text, or investment conclusions."
        in profile.limitations
    )


def test_edgar_company_profile_duplicate_ticker_rows_fail_closed_without_guessing_identity() -> None:
    client = _ReplayEdgarProfileClient(
        company_tickers={
            "0": {"cik_str": 1234, "ticker": "EXMP", "title": "Example Public Test Company, Inc."},
            "1": {"cik_str": 5678, "ticker": "EXMP", "title": "Example Duplicate Test Company, Inc."},
        }
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    assert profile.availability == "not_available"
    assert profile.facts == ()
    assert profile.caveat_codes == ("edgar_symbol_unresolved",)
    assert client.calls == ("fetch_company_tickers",)


def test_edgar_company_profile_invalid_cik_fails_closed() -> None:
    client = _ReplayEdgarProfileClient(
        company_tickers={"0": {"cik_str": "not-a-cik", "ticker": "EXMP", "title": "Example Test Company"}}
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    assert profile.availability == "not_available"
    assert profile.facts == ()
    assert profile.caveat_codes == ("edgar_cik_unavailable",)
    assert client.calls == ("fetch_company_tickers",)


def test_edgar_company_profile_overlong_numeric_cik_fails_before_submissions_fetch() -> None:
    client = _ReplayEdgarProfileClient(
        company_tickers={"0": {"cik_str": "12345678901", "ticker": "EXMP", "title": "Example Test Company"}}
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    assert profile.availability == "not_available"
    assert profile.facts == ()
    assert profile.caveat_codes == ("edgar_cik_unavailable",)
    assert client.calls == ("fetch_company_tickers",)


def test_edgar_company_profile_client_exception_fails_closed_without_raw_content() -> None:
    client = _ReplayEdgarProfileClient(
        exception_message="https://data.sec.gov/submissions/CIK0000001234.json raw_payload api_key=secret"
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    rendered = repr(public_evidence.model_dump(mode="python")).lower()
    assert public_evidence.public_company_profile.availability == "not_available"
    assert public_evidence.public_company_profile.caveat_codes == ("edgar_replay_unavailable",)
    assert "data.sec.gov" not in rendered
    assert "raw_payload" not in rendered
    assert "api_key" not in rendered
    assert "secret" not in rendered


def test_edgar_company_profile_replay_unresolved_symbol_does_not_guess_identity() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXM",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(),
    )

    profile = public_evidence.public_company_profile
    assert profile.availability == "not_available"
    assert profile.facts == ()
    assert profile.caveat_codes == ("edgar_symbol_unresolved",)
    assert "Example Public Test Company" not in repr(profile)


def test_edgar_company_profile_missing_optional_fields_is_limited_without_fabrication() -> None:
    client = _ReplayEdgarProfileClient(
        submissions={
            "name": "Example Public Test Company, Inc.",
            "tickers": ["EXMP"],
        }
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    facts = {fact.fact_key: fact.value_label for fact in profile.facts}
    assert profile.availability == "limited"
    assert profile.caveat_codes == ("edgar_profile_partial_metadata",)
    assert facts["company_name"] == "Example Public Test Company, Inc."
    assert facts["ticker"] == "EXMP"
    assert facts["cik_reference"] == "CIK 0000001234"
    assert "exchange" not in facts
    assert "sic_label" not in facts


def test_edgar_company_profile_missing_required_metadata_is_not_available() -> None:
    client = _ReplayEdgarProfileClient(
        company_tickers={"0": {"cik_str": 1234, "ticker": "EXMP"}},
        submissions={"tickers": ["EXMP"]},
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    profile = public_evidence.public_company_profile
    assert profile.availability == "not_available"
    assert profile.facts == ()
    assert profile.caveat_codes == ("edgar_profile_metadata_incomplete",)


def test_edgar_company_profile_discards_raw_payload_fields_and_private_context() -> None:
    client = _ReplayEdgarProfileClient(
        submissions={
            "name": "Example Public Test Company, Inc.",
            "tickers": ["EXMP"],
            "exchanges": ["Nasdaq"],
            "sicDescription": "Security Brokers, Dealers & Flotation Companies",
            "fiscalYearEnd": "1231",
            "source_url": "https://example.test/should-not-appear",
            "raw_payload": {"account_id": "acct_private"},
            "filings": {"recent": {"accessionNumber": ["0000000000-00-000000"]}},
        }
    )

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=client,
    )

    rendered = repr(public_evidence.model_dump(mode="python")).lower()
    assert public_evidence.public_company_profile.availability == "available"
    assert "source_url" not in rendered
    assert "raw_payload" not in rendered
    assert "acct_private" not in rendered
    assert "accession" not in rendered


def test_edgar_company_profile_public_evidence_supports_package_aware_validation() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(),
    )
    evidence = _evidence_with_public_sections(
        {"public_company_profile": public_evidence.public_company_profile}
    )

    projection = build_public_role_evidence_projection(evidence, role_name="fundamentals_analyst")
    payload = {
        "role_summaries": (
            {
                "role_name": "fundamentals_analyst",
                "display_name": "Fundamentals Analyst",
                "role_status": "completed",
                "provider_status": "ok",
                "summary_markdown": "Company identity context is available from reviewed public evidence.",
                "evidence_references": ("trade_intent_summary", "public_company_profile"),
                "warning_codes": (),
            },
        ),
        "evidence_references": ("trade_intent_summary", "public_company_profile"),
    }

    assert projection.citable_section_keys == ("public_company_profile",)
    validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_public_role_evidence_projection_narrows_sections_to_role_boundary() -> None:
    public_evidence = SavedPublicEvidencePackageRead.not_reviewed("HOOD").model_copy(
        update={
            "public_evidence_mode": "synthetic_demo",
            "public_company_profile": _reviewed_public_section(
                "public_company_profile",
                "Public company profile",
                "Reviewed synthetic company profile.",
            ),
            "public_fundamentals_snapshot": _reviewed_public_section(
                "public_fundamentals_snapshot",
                "Public fundamentals snapshot",
                "Reviewed synthetic fundamentals snapshot.",
            ),
            "public_events_calendar": _reviewed_public_section(
                "public_events_calendar",
                "Public events calendar",
                "Reviewed synthetic event calendar.",
            ),
            "public_news_snapshot": _reviewed_public_section(
                "public_news_snapshot",
                "Public news snapshot",
                "Reviewed synthetic news snapshot.",
            ),
        }
    )
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(
        _saved_review_artifact().model_copy(update={"public_evidence": public_evidence})
    )

    projection = build_public_role_evidence_projection(evidence, role_name="fundamentals_analyst")

    assert projection.role_name == "fundamentals_analyst"
    assert projection.instrument_context.symbol_or_underlying == "HOOD"
    assert projection.allowed_section_keys == (
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_events_calendar",
    )
    assert projection.citable_section_keys == projection.allowed_section_keys
    assert {section.section_key for section in projection.sections} == set(projection.allowed_section_keys)
    assert "public_news_snapshot" not in projection.allowed_section_keys
    assert projection.degrade_reason is None


def test_public_role_evidence_projection_defaults_to_no_reviewed_public_evidence() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())

    projection = build_public_role_evidence_projection(evidence, role_name="news_analyst")

    assert projection.citable_section_keys == ()
    assert projection.degrade_reason == "no_reviewed_public_evidence"
    assert {section.availability for section in projection.sections} == {"not_reviewed"}


def test_saved_public_evidence_rejects_raw_source_payloads_urls_and_article_bodies() -> None:
    with pytest.raises(ValidationError):
        SavedPublicEvidenceSectionRead(
            section_key="public_news_snapshot",
            section_label="Public news snapshot",
            availability="available",
            freshness_category="fresh",
            freshness_label="Collected for this saved report",
            source_label="Synthetic public evidence",
            rights_status="internal_demo_only",
            summary_label="https://example.test/full-story",
            limitations=("Internal demo only.",),
        )

    with pytest.raises(ValidationError):
        SavedPublicEvidenceSectionRead(
            section_key="public_news_snapshot",
            section_label="Public news snapshot",
            availability="available",
            freshness_category="fresh",
            freshness_label="Collected for this saved report",
            source_label="Synthetic public evidence",
            rights_status="internal_demo_only",
            limitations=("Internal demo only.",),
            facts=(
                {
                    "fact_key": "article_body",
                    "fact_label": "Article body",
                    "value_label": "Full article body must not enter saved public evidence.",
                },
            ),
        )


def test_saved_public_evidence_available_sections_require_reviewed_or_demo_rights() -> None:
    with pytest.raises(ValidationError):
        SavedPublicEvidenceSectionRead(
            section_key="public_company_profile",
            section_label="Public company profile",
            availability="available",
            freshness_category="fresh",
            freshness_label="Collected for this saved report",
            source_label="Unreviewed public source",
            rights_status="not_reviewed",
            summary_label="Reviewed source rights are required before this can be cited.",
            limitations=("Source rights are not reviewed.",),
        )


def test_saved_evidence_package_requires_immutable_saved_scope_and_summary() -> None:
    artifact = _saved_review_artifact().model_copy(update={"scope_metadata": None})

    with pytest.raises(ValueError):
        SavedEvidencePackageRead.from_saved_review_artifact(artifact)


def test_saved_evidence_package_rejects_private_fields_values_and_advice_wording() -> None:
    with pytest.raises(ValidationError):
        SavedEvidenceSectionRead(
            section_key="liquidity_private",
            section_label="Liquidity caveat",
            availability="limited",
            summary_label="buying_power is available",
        )

    with pytest.raises(ValidationError):
        SavedEvidenceSectionRead(
            section_key="agent_instruction",
            section_label="Unsafe instruction",
            availability="available",
            summary_label="You should buy before close.",
        )

    with pytest.raises(ValidationError):
        SavedEvidenceSectionRead(
            section_key="unsafe_advice",
            section_label="Unsafe advice",
            availability="available",
            summary_label="This is financial advice and a trade recommendation.",
        )

    artifact = _saved_review_artifact()
    safe_evidence = SavedEvidencePackageRead.from_saved_review_artifact(artifact)
    payload = safe_evidence.model_dump(mode="python")
    payload["current_account_selector"] = "acctref_reportscope1"
    with pytest.raises(ValidationError):
        SavedEvidencePackageRead(**payload)


def test_agent_team_report_read_projects_source_snapshot_without_current_state() -> None:
    report_generated_at = datetime(2026, 6, 15, 18, 0, tzinfo=UTC)
    artifact = _saved_review_artifact().model_copy(
        update={
            "agent_summary": SavedAgentTeamSummaryRead(
                run_status="partially_completed",
                provider_mode="deterministic_template",
                report_generated_at=report_generated_at,
                role_summaries=(
                    SavedAgentTeamRoleSummaryRead(
                        role_name="risk_management_agent",
                        display_name="Risk Manager",
                        role_status="completed",
                        provider_status="ok",
                        summary_markdown="Risk review uses saved deterministic evidence only.",
                        evidence_references=("trade_intent_summary", "scope_state", "actionability"),
                        warning_codes=("selected_context_scope",),
                    ),
                ),
                warning_codes=("public_evidence_roles_skipped",),
                report_status="full_agent_report",
                final_synthesis_markdown="Agent Team analysis is generated from the saved evidence package.",
                final_synthesis_authored_by="deterministic_template",
                evidence_schema_version="p29a_t1_v1",
                evidence_references=("trade_intent_summary", "scope_state", "actionability"),
            )
        }
    )

    report = AgentTeamReportRead.from_saved_review_artifact(artifact)
    rendered = repr(report.model_dump(mode="python")).lower()

    assert report.report_status == "full_agent_report"
    assert report.run_completeness == "full"
    assert report.source_snapshot.source_reference == "trrev_savedreview1"
    assert report.generated_at == artifact.generated_at
    assert report.report_generated_at == report_generated_at
    assert report.final_synthesis is not None
    assert "acctref_reportscope1" not in rendered
    assert "ctx_reportscope1" not in rendered


def test_agent_team_report_read_source_snapshot_has_no_report_generated_at() -> None:
    artifact = _saved_review_artifact().model_copy(update={"agent_summary": None})

    report = AgentTeamReportRead.from_saved_review_artifact(artifact)

    assert report.report_status == "source_snapshot"
    assert report.generated_at == artifact.generated_at
    assert report.report_generated_at is None


def test_agent_team_report_read_legacy_agent_summary_without_report_generated_at_is_safe() -> None:
    artifact = _saved_review_artifact().model_copy(
        update={
            "agent_summary": SavedAgentTeamSummaryRead(
                run_status="partially_completed",
                provider_mode="deterministic_template",
                role_summaries=(
                    SavedAgentTeamRoleSummaryRead(
                        role_name="risk_management_agent",
                        display_name="Risk Manager",
                        role_status="completed",
                        provider_status="ok",
                        summary_markdown="Risk review uses saved deterministic evidence only.",
                        evidence_references=("trade_intent_summary", "scope_state", "actionability"),
                        warning_codes=("selected_context_scope",),
                    ),
                ),
                warning_codes=("public_evidence_roles_skipped",),
                report_status="full_agent_report",
                final_synthesis_markdown="Agent Team analysis is generated from the saved evidence package.",
                final_synthesis_authored_by="deterministic_template",
                evidence_schema_version="p29a_t1_v1",
                evidence_references=("trade_intent_summary", "scope_state", "actionability"),
            )
        }
    )

    report = AgentTeamReportRead.from_saved_review_artifact(artifact)

    assert report.report_status == "full_agent_report"
    assert report.report_generated_at is None


def test_agent_team_report_rejects_role_evidence_outside_boundary() -> None:
    with pytest.raises(ValidationError):
        SavedAgentTeamRoleSummaryRead(
            role_name="fundamentals_analyst",
            display_name="Fundamentals Analyst",
            role_status="completed",
            provider_status="ok",
            summary_markdown="Public role summary from saved evidence.",
            evidence_references=("portfolio_impact_summary",),
            warning_codes=(),
        )


def test_agent_team_report_provider_unavailable_summary_is_safe() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    report_generated_at = datetime(2026, 6, 15, 19, 0, tzinfo=UTC)

    summary = build_agent_team_summary_from_evidence(
        evidence,
        mode="provider_unavailable",
        report_generated_at=report_generated_at,
    )

    assert summary.report_status == "agent_unavailable"
    assert summary.report_generated_at == report_generated_at
    assert summary.run_status == "failed"
    assert {role.role_status for role in summary.role_summaries} == {"unavailable"}
    assert summary.final_synthesis_markdown is None


def test_agent_team_report_deterministic_draft_summary_records_generation_time() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact()).model_copy(
        update={
            "actionability": SavedEvidencePackageRead.from_saved_review_artifact(
                _saved_review_artifact().model_copy(
                    update={
                        "deterministic_summary": _saved_deterministic_summary().model_copy(
                            update={"review_actionability_status": "blocked_stale_market_quote"}
                        )
                    }
                )
            ).actionability
        }
    )
    report_generated_at = datetime(2026, 6, 15, 19, 30, tzinfo=UTC)

    summary = build_agent_team_summary_from_evidence(evidence, report_generated_at=report_generated_at)

    assert summary.report_status == "deterministic_draft"
    assert summary.report_generated_at == report_generated_at
    assert {role.role_status for role in summary.role_summaries} == {"gated"}


def test_agent_team_report_validator_accepts_safe_summary_shape_references() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    payload = {
        "run_status": "partially_completed",
        "provider_mode": "deterministic_template",
        "role_summaries": (
            {
                "role_name": "risk_management_agent",
                "display_name": "Risk Manager",
                "role_status": "completed",
                "provider_status": "ok",
                "summary_markdown": "Risk review uses saved deterministic evidence only.",
                "evidence_references": ("trade_intent_summary", "market_quote_freshness"),
                "warning_codes": (),
                "unavailable_reason": None,
            },
        ),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "Agent Team analysis is generated from the saved evidence package.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_t1_v1",
        "evidence_references": ("trade_intent_summary", "market_quote_freshness"),
    }

    validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_agent_team_report_validator_rejects_summary_shape_unavailable_evidence_reference() -> None:
    evidence = _saved_evidence_with_unavailable_market_quote()
    payload = {
        "run_status": "partially_completed",
        "provider_mode": "deterministic_template",
        "role_summaries": (
            {
                "role_name": "risk_management_agent",
                "display_name": "Risk Manager",
                "role_status": "completed",
                "provider_status": "ok",
                "summary_markdown": "Risk review uses saved deterministic evidence only.",
                "evidence_references": ("trade_intent_summary", "market_quote_freshness"),
                "warning_codes": (),
                "unavailable_reason": None,
            },
        ),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "Agent Team analysis is generated from the saved evidence package.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_t1_v1",
        "evidence_references": ("trade_intent_summary", "market_quote_freshness"),
    }

    with pytest.raises(ValueError):
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_public_role_evidence_references_require_available_public_section() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    assert evidence.public_evidence is not None
    payload = {
        "run_status": "partially_completed",
        "provider_mode": "deterministic_template",
        "role_summaries": (
            {
                "role_name": "fundamentals_analyst",
                "display_name": "Fundamentals Analyst",
                "role_status": "completed",
                "provider_status": "ok",
                "summary_markdown": "Fundamentals review uses reviewed public evidence only.",
                "evidence_references": ("public_company_profile",),
                "warning_codes": (),
                "unavailable_reason": None,
            },
        ),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "Agent Team analysis is generated from the saved evidence package.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_t1_v1",
        "evidence_references": ("public_company_profile",),
    }

    with pytest.raises(ValueError):
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_public_role_evidence_references_accept_reviewed_available_public_section() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    assert evidence.public_evidence is not None
    public_evidence = evidence.public_evidence.model_copy(
        update={
            "public_evidence_mode": "synthetic_demo",
            "public_company_profile": _reviewed_public_section(
                "public_company_profile",
                "Public company profile",
                "Reviewed synthetic public profile label for this saved report.",
            ),
        }
    )
    evidence = evidence.model_copy(update={"public_evidence": public_evidence})
    payload = {
        "run_status": "partially_completed",
        "provider_mode": "deterministic_template",
        "role_summaries": (
            {
                "role_name": "fundamentals_analyst",
                "display_name": "Fundamentals Analyst",
                "role_status": "completed",
                "provider_status": "ok",
                "summary_markdown": "Fundamentals review uses reviewed public evidence only.",
                "evidence_references": ("trade_intent_summary", "public_company_profile"),
                "warning_codes": (),
                "unavailable_reason": None,
            },
        ),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "Agent Team analysis is generated from the saved evidence package.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_t1_v1",
        "evidence_references": ("trade_intent_summary", "public_company_profile"),
    }

    validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_agent_team_report_generation_falls_back_when_summary_references_unavailable_evidence() -> None:
    evidence = _saved_evidence_with_unavailable_market_quote()
    report_generated_at = datetime(2026, 6, 15, 20, 0, tzinfo=UTC)

    summary = build_agent_team_summary_from_evidence(evidence, report_generated_at=report_generated_at)
    fallback = build_validation_failed_summary_for_test(
        evidence,
        summary.model_dump(mode="python"),
        report_generated_at=report_generated_at,
    )

    assert fallback.report_status == "validation_failed"
    assert fallback.report_generated_at == report_generated_at
    assert fallback.final_synthesis_markdown is None
    assert fallback.evidence_references == ()


def test_agent_team_report_validation_failure_falls_back_without_persisting_unsafe_text() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    unsafe_payload = {
        "run_status": "completed",
        "provider_mode": "deterministic_template",
        "role_summaries": (),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "This is financial advice and a trade recommendation.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_t1_v1",
        "evidence_references": ("trade_intent_summary",),
    }

    report_generated_at = datetime(2026, 6, 15, 20, 30, tzinfo=UTC)

    summary = build_validation_failed_summary_for_test(
        evidence,
        unsafe_payload,
        report_generated_at=report_generated_at,
    )

    rendered = repr(summary.model_dump(mode="python")).lower()
    assert summary.report_status == "validation_failed"
    assert summary.report_generated_at == report_generated_at
    assert summary.final_synthesis_markdown is None
    assert "financial advice" not in rendered
    assert "trade recommendation" not in rendered


# -- P29B-T3B: public-role generation wiring and validation behavior ----------


def test_public_roles_skip_honestly_for_default_not_reviewed_evidence() -> None:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 15, 23, 0, tzinfo=UTC)
    )

    public = {s.role_name: s for s in summary.role_summaries if s.role_name in _PUBLIC_ROLES}
    assert {s.role_status for s in public.values()} == {"skipped"}
    assert all(s.unavailable_reason == "no_reviewed_public_evidence" for s in public.values())
    assert all(s.summary_markdown is None for s in public.values())
    assert summary.warning_codes == ("public_evidence_roles_skipped",)
    assert summary.run_status == "partially_completed"
    assert summary.report_status == "full_agent_report"
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_fundamentals_uses_available_edgar_profile_as_identity_context_only() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(
            submissions={
                "name": "Support.com Target Company, Inc.",
                "tickers": ["EXMP"],
                "exchanges": ["Nasdaq"],
                "sicDescription": "Semiconductors & Related Devices",
                "fiscalYearEnd": "1231",
            }
        ),
    )
    evidence = _evidence_with_public_sections(
        {"public_company_profile": public_evidence.public_company_profile}
    )

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 16, 16, 0, tzinfo=UTC)
    )

    by_role = {s.role_name: s for s in summary.role_summaries}
    fundamentals = by_role["fundamentals_analyst"]
    news = by_role["news_analyst"]
    technical = by_role["technical_analyst"]
    markdown = fundamentals.summary_markdown or ""
    assert fundamentals.role_status == "completed"
    assert fundamentals.evidence_references == ("trade_intent_summary", "public_company_profile")
    assert "SEC EDGAR metadata - company profile only" in markdown
    assert "company name" in markdown
    assert "ticker" in markdown
    assert "listing exchange" in markdown
    assert "CIK reference" in markdown
    assert "SEC SIC regulatory classification metadata" in markdown
    assert "fiscal year-end metadata" in markdown
    assert "broad, legacy" in markdown
    assert "0000001234" not in markdown
    assert "12/31" not in markdown
    assert "Support.com" not in markdown
    assert "Semiconductors & Related Devices" not in markdown
    assert "sector" not in markdown.lower()
    assert "industry" not in markdown.lower()
    assert news.role_status == "skipped"
    assert "public_company_profile" not in news.evidence_references
    assert technical.role_status == "skipped"
    assert "public_company_profile" not in technical.evidence_references
    assert "company identity and listing context" in (summary.final_synthesis_markdown or "")
    assert "sector" not in (summary.final_synthesis_markdown or "").lower()
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_fundamentals_uses_limited_edgar_profile_without_sic_statement_when_sic_absent() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(
            submissions={
                "name": "Example Public Test Company, Inc.",
                "tickers": ["EXMP"],
            }
        ),
    )
    evidence = _evidence_with_public_sections(
        {"public_company_profile": public_evidence.public_company_profile}
    )

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 16, 16, 30, tzinfo=UTC)
    )

    fundamentals = next(s for s in summary.role_summaries if s.role_name == "fundamentals_analyst")
    markdown = fundamentals.summary_markdown or ""
    assert public_evidence.public_company_profile.availability == "limited"
    assert fundamentals.role_status == "completed"
    assert "public_evidence_limited" in fundamentals.warning_codes
    assert "SEC SIC" not in markdown
    assert "broad, legacy" not in markdown
    assert "limited or stale" in markdown
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_fundamentals_uses_limited_edgar_profile_with_sic_caveat_when_sic_present() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(
            submissions={
                "name": "Example Public Test Company, Inc.",
                "tickers": ["EXMP"],
                "sicDescription": "Semiconductors & Related Devices",
            }
        ),
    )
    evidence = _evidence_with_public_sections(
        {"public_company_profile": public_evidence.public_company_profile}
    )

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 16, 17, 0, tzinfo=UTC)
    )

    fundamentals = next(s for s in summary.role_summaries if s.role_name == "fundamentals_analyst")
    markdown = fundamentals.summary_markdown or ""
    assert public_evidence.public_company_profile.availability == "limited"
    assert fundamentals.role_status == "completed"
    assert "public_evidence_limited" in fundamentals.warning_codes
    assert "SEC SIC regulatory classification metadata" in markdown
    assert "broad, legacy" in markdown
    assert "Semiconductors & Related Devices" not in markdown
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_fundamentals_skips_when_edgar_profile_not_available() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(exception_message="raw_payload data.sec.gov account_id"),
    )
    evidence = _evidence_with_public_sections(
        {"public_company_profile": public_evidence.public_company_profile}
    )

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 16, 17, 30, tzinfo=UTC)
    )

    fundamentals = next(s for s in summary.role_summaries if s.role_name == "fundamentals_analyst")
    assert public_evidence.public_company_profile.availability == "not_available"
    assert fundamentals.role_status == "skipped"
    assert fundamentals.summary_markdown is None
    assert fundamentals.unavailable_reason == "public_evidence_not_available"
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_report_output_rejects_full_edgar_attribution_sentence() -> None:
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="EXMP",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=_ReplayEdgarProfileClient(),
    )
    evidence = _evidence_with_public_sections(
        {"public_company_profile": public_evidence.public_company_profile}
    )
    payload = _single_role_summary_payload(
        "fundamentals_analyst",
        "Fundamentals Analyst",
        ("trade_intent_summary", "public_company_profile"),
        "Source: SEC EDGAR submissions metadata. Company identity and listing metadata only. Not investment advice or a trading signal.",
    )

    with pytest.raises(ValueError):
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_public_roles_complete_from_reviewed_available_public_evidence() -> None:
    evidence = _evidence_with_public_sections(_all_reviewed_public_sections())
    report_generated_at = datetime(2026, 6, 15, 21, 0, tzinfo=UTC)

    summary = build_agent_team_summary_from_evidence(evidence, report_generated_at=report_generated_at)

    public = {s.role_name: s for s in summary.role_summaries if s.role_name in _PUBLIC_ROLES}
    assert {s.role_status for s in public.values()} == {"completed"}
    assert "public_company_profile" in public["fundamentals_analyst"].evidence_references
    assert "public_news_snapshot" in public["news_analyst"].evidence_references
    assert "public_technical_context" in public["technical_analyst"].evidence_references
    assert all("trade_intent_summary" in s.evidence_references for s in public.values())
    assert summary.warning_codes == ("public_evidence_roles_included",)
    assert summary.run_status == "completed"
    # End-to-end: completed public summaries pass package-aware validation and do
    # not fall back to validation_failed.
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )
    revalidated = build_validation_failed_summary_for_test(
        evidence, summary.model_dump(mode="python"), report_generated_at=report_generated_at
    )
    assert revalidated.report_status == "full_agent_report"


def test_public_role_limited_evidence_completes_with_explicit_caveat() -> None:
    sections = _all_reviewed_public_sections()
    sections["public_news_snapshot"] = _limited_public_section(
        "public_news_snapshot", "Public news snapshot", "Limited/stale synthetic news snapshot."
    )
    evidence = _evidence_with_public_sections(sections)

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 15, 21, 30, tzinfo=UTC)
    )

    news = next(s for s in summary.role_summaries if s.role_name == "news_analyst")
    assert news.role_status == "completed"
    assert "public_evidence_limited" in news.warning_codes
    assert "limited or stale" in (news.summary_markdown or "")
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_public_roles_partial_coverage_when_only_some_evidence_reviewed() -> None:
    # Only the fundamentals-unique sections are reviewed; the events calendar is
    # shared with news, so it stays not_reviewed to keep news/technical skipped.
    sections = {
        "public_company_profile": _reviewed_public_section(
            "public_company_profile", "Public company profile", "Reviewed synthetic company profile."
        ),
        "public_fundamentals_snapshot": _reviewed_public_section(
            "public_fundamentals_snapshot", "Public fundamentals snapshot", "Reviewed synthetic fundamentals."
        ),
    }
    evidence = _evidence_with_public_sections(sections)

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 15, 22, 0, tzinfo=UTC)
    )

    by_role = {s.role_name: s for s in summary.role_summaries}
    assert by_role["fundamentals_analyst"].role_status == "completed"
    assert by_role["news_analyst"].role_status == "skipped"
    assert by_role["news_analyst"].unavailable_reason == "no_reviewed_public_evidence"
    assert by_role["technical_analyst"].role_status == "skipped"
    assert summary.warning_codes == ("public_evidence_partial_coverage",)
    assert summary.run_status == "partially_completed"
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_public_role_assembly_failure_degrades_to_unavailable(monkeypatch) -> None:
    import app.services.reports.agent_team_report as agent_team_report_module

    def _raise_assembly_failure(*args, **kwargs):
        raise ValueError("synthetic public-evidence projection assembly failure")

    monkeypatch.setattr(
        agent_team_report_module, "build_public_role_evidence_projection", _raise_assembly_failure
    )
    evidence = _evidence_with_public_sections(_all_reviewed_public_sections())

    summary = build_agent_team_summary_from_evidence(
        evidence, report_generated_at=datetime(2026, 6, 15, 22, 30, tzinfo=UTC)
    )

    public = {s.role_name: s for s in summary.role_summaries if s.role_name in _PUBLIC_ROLES}
    assert {s.role_status for s in public.values()} == {"unavailable"}
    assert all(s.unavailable_reason == "public_evidence_provider_unavailable" for s in public.values())
    assert all(s.summary_markdown is None for s in public.values())
    assert summary.warning_codes == ("public_evidence_roles_skipped",)
    validate_agent_team_report_output(
        summary.model_dump(mode="python"), label="agent-team saved report", evidence_package=evidence
    )


def test_public_role_cross_boundary_citation_fails_closed() -> None:
    evidence = _evidence_with_public_sections(_all_reviewed_public_sections())
    # public_news_snapshot is available but outside the fundamentals boundary.
    payload = _single_role_summary_payload(
        "fundamentals_analyst",
        "Fundamentals Analyst",
        ("trade_intent_summary", "public_news_snapshot"),
        "Fundamentals summary citing a news section.",
    )

    with pytest.raises(ValueError):
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_report_output_rejects_invented_levels_and_price_targets() -> None:
    evidence = _evidence_with_public_sections(_all_reviewed_public_sections())
    for unsafe_markdown in (
        "Technical view for HOOD: watch support at 145 and resistance near 160.",
        "Technical view for HOOD: estimated target of 172 over the next year.",
    ):
        payload = _single_role_summary_payload(
            "technical_analyst",
            "Technical Analyst",
            ("trade_intent_summary", "public_technical_context"),
            unsafe_markdown,
        )
        with pytest.raises(ValueError):
            validate_agent_team_report_output(
                payload, label="agent-team saved report", evidence_package=evidence
            )


def test_report_output_rejects_source_url_leak() -> None:
    evidence = _evidence_with_public_sections(_all_reviewed_public_sections())
    payload = _single_role_summary_payload(
        "news_analyst",
        "News Analyst",
        ("trade_intent_summary", "public_news_snapshot"),
        "News summary. See https://news.example.com/article for the full story.",
    )

    with pytest.raises(ValueError):
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_report_output_rejects_private_data_token_in_public_summary() -> None:
    evidence = _evidence_with_public_sections(_all_reviewed_public_sections())
    payload = _single_role_summary_payload(
        "fundamentals_analyst",
        "Fundamentals Analyst",
        ("trade_intent_summary", "public_company_profile"),
        "Fundamentals summary referencing account_id for the reviewed account.",
    )

    with pytest.raises(ValueError):
        validate_agent_team_report_output(payload, label="agent-team saved report", evidence_package=evidence)


def test_saved_review_report_metadata_validates_report_reference() -> None:
    valid = SavedReviewReportMetadataRead(
        report_reference="svrev_savedreview1",
        title="Saved covered-call review",
        report_type="trade_review",
        status="completed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert valid.report_reference == "svrev_savedreview1"

    for unsafe_ref in ("svrev_broker123", "svrev_provider123", "svrev_account123", "svrev_raw_payload1"):
        with pytest.raises(ValidationError):
            SavedReviewReportMetadataRead(
                report_reference=unsafe_ref,
                title="Unsafe saved review",
                report_type="trade_review",
                status="completed",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )


def test_saved_review_artifact_rejects_forbidden_private_fields_and_execution_wording() -> None:
    with pytest.raises(ValidationError):
        SavedDeterministicReviewSummaryRead(
            supported_flow="cash_secured_put",
            review_flow_label="Cash-secured put",
            symbol_or_underlying="XYZ",
            review_actionability_status="analysis_only",
            actionability_label="Analysis-only review",
            highest_severity=None,
            report_status="generated",
            caveat_codes=("raw_payload",),
        )

    with pytest.raises(ValidationError):
        SavedAgentTeamRoleSummaryRead(
            role_name="portfolio_manager_agent",
            display_name="Portfolio Manager",
            provider_status="ok",
            summary_markdown="You should buy this before close.",
            warning_codes=(),
        )

    with pytest.raises(ValidationError):
        SavedAgentTeamRoleSummaryRead(
            role_name="portfolio_manager_agent",
            display_name="Portfolio Manager",
            provider_status="ok",
            summary_markdown="I recommend buying this before close.",
            warning_codes=(),
        )


def test_report_message_create_schema_supports_markdown_and_json() -> None:
    payload = ReportMessageCreate(
        sender_type="system",
        message_type="markdown_report",
        content_markdown="# Synthetic",
        content_json={"source": "deterministic_template"},
        sequence=1,
    )

    assert payload.visibility == "private"
    assert payload.content_json == {"source": "deterministic_template"}


def test_agent_run_create_schema_exposes_traceability_fields() -> None:
    payload = AgentRunCreate(
        input_snapshot_json={"input": "synthetic"},
        output_snapshot_json={"output": "synthetic"},
        calculation_version="calc-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh"},
    )

    assert payload.run_type == "portfolio_analysis"
    assert payload.status == "queued"
    assert payload.input_snapshot_json == {"input": "synthetic"}
    assert payload.output_snapshot_json == {"output": "synthetic"}
    assert payload.calculation_version == "calc-v1"
    assert payload.data_freshness_snapshot == {"broker_portfolio": "fresh"}


def test_agent_run_create_rejects_invalid_time_order() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValidationError):
        AgentRunCreate(started_at=started_at, completed_at=started_at - timedelta(seconds=1))


def test_agent_step_create_schema_exposes_traceability_and_cost_fields() -> None:
    payload = AgentStepCreate(
        agent_run_id=uuid4(),
        step_order=1,
        step_key="load_context",
        step_type="deterministic_context",
        input_snapshot_json={"input": "synthetic"},
        output_snapshot_json={"output": "synthetic"},
        calculation_version="step-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh"},
        tokens_in=0,
        tokens_out=0,
        estimated_cost="0",
    )

    assert payload.status == "queued"
    assert payload.input_snapshot_json == {"input": "synthetic"}
    assert payload.output_snapshot_json == {"output": "synthetic"}
    assert payload.calculation_version == "step-v1"
    assert payload.tokens_in == 0
    assert payload.tokens_out == 0
    assert payload.estimated_cost == 0


def test_report_and_agent_schemas_do_not_expose_secret_fields() -> None:
    schema_names = [
        ReportThreadCreate,
        ReportThreadRead,
        ReportPublicEvidenceAttributionRead,
        ReportMessageCreate,
        SavedReviewArtifactCreateRequest,
        SavedReviewArtifactRead,
        SavedReviewReportMetadataRead,
        SavedEvidencePackageRead,
        SavedEvidenceSectionRead,
        SavedPublicEvidencePackageRead,
        SavedPublicEvidenceSectionRead,
        SavedPublicRoleEvidenceProjectionRead,
        SavedDeterministicReviewSummaryRead,
        SavedAgentTeamSummaryRead,
        SavedAgentTeamRoleSummaryRead,
        AgentTeamReportRead,
        AgentTeamReportRoleSectionRead,
        AgentTeamReportSynthesisRead,
        AgentRunCreate,
        AgentStepCreate,
    ]

    for schema in schema_names:
        fields = set(schema.model_fields)
        assert "secret_ref" not in fields
        assert "encrypted_secret_ref" not in fields
        assert "api_key" not in fields
        assert "access_token" not in fields


def _saved_scope_metadata() -> ReportScopeMetadataRead:
    review_account = ReviewAccountRead(
        account_reference="acctref_reportscope1",
        display_label="Fidelity taxable",
        account_kind_label="Taxable brokerage",
        is_review_account=True,
        is_included_in_portfolio_scope=True,
        is_account_level_feasibility_source=True,
    )
    portfolio_scope = PortfolioScopeRead(
        scope_reference="scope_reportscope1",
        scope_mode="selected_context",
        display_label="Selected portfolio context",
        selection_mode="latest_available",
        context_reference="ctx_reportscope1",
        included_account_labels=("Fidelity taxable",),
        excluded_account_labels=(),
        account_level_feasibility_evaluated=True,
        account_level_feasibility_label="Account-level feasibility evaluated for selected review account",
        caveat_codes=("selected_context_scope",),
    )
    return ReportScopeMetadataRead(
        review_account=review_account,
        portfolio_context_scope=portfolio_scope,
        scope_summary_label="Review account: Fidelity taxable - Context scope: Selected portfolio context.",
        account_level_feasibility_evaluated=True,
        scope_caveat_codes=("selected_context_scope",),
    )


def _saved_deterministic_summary() -> SavedDeterministicReviewSummaryRead:
    return SavedDeterministicReviewSummaryRead(
        supported_flow="covered_call",
        review_flow_label="Covered call",
        symbol_or_underlying="HOOD",
        review_actionability_status="analysis_only",
        actionability_label="Analysis-only review",
        highest_severity="warning",
        report_status="generated",
        broker_snapshot_freshness_label="Broker snapshot from generated review",
        market_quote_freshness_label="Market quote from generated review",
        caveat_codes=("selected_context_scope", "account_level_feasibility_not_evaluated"),
    )


def _saved_review_artifact() -> SavedReviewArtifactRead:
    generated = datetime.now(UTC)
    return SavedReviewArtifactRead(
        artifact_reference="svrev_savedreview1",
        source_kind="trade_review_workspace",
        source_reference="trrev_savedreview1",
        status="saved",
        report=SavedReviewReportMetadataRead(
            report_reference="svrev_savedreview1",
            title="Saved covered-call review",
            report_type="trade_review",
            status="completed",
            created_at=generated,
            updated_at=generated,
        ),
        scope_metadata=_saved_scope_metadata(),
        deterministic_summary=_saved_deterministic_summary(),
        agent_summary=SavedAgentTeamSummaryRead(
            run_status="completed",
            provider_mode="mock",
            role_summaries=(
                SavedAgentTeamRoleSummaryRead(
                    role_name="portfolio_manager_agent",
                    display_name="Portfolio Manager",
                    provider_status="ok",
                    summary_markdown="Analysis-only synthesis from saved review output.",
                    warning_codes=(),
                ),
            ),
            warning_codes=(),
        ),
        generated_at=generated,
        saved_at=generated,
        review_pipeline_label="Portfolio Copilot review pipeline",
        limitations=("Saved review snapshot generated from reviewed data available at the time.",),
        caveat_codes=("selected_context_scope",),
    )


def _reviewed_public_section(
    section_key: str,
    section_label: str,
    summary_label: str,
) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key=section_key,  # type: ignore[arg-type]
        section_label=section_label,
        availability="available",
        freshness_category="fresh",
        freshness_label="Collected for this saved report",
        source_label="Synthetic public evidence",
        rights_status="internal_demo_only",
        summary_label=summary_label,
        facts=(
            {
                "fact_key": "synthetic_profile_label",
                "fact_label": "Synthetic profile label",
                "value_label": "Reviewed synthetic public profile",
                "source_label": "Synthetic public evidence",
            },
        ),
        limitations=("Synthetic public evidence for backend contract tests only.",),
    )


def _limited_public_section(
    section_key: str,
    section_label: str,
    summary_label: str,
) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key=section_key,  # type: ignore[arg-type]
        section_label=section_label,
        availability="limited",
        freshness_category="stale",
        freshness_label="Collected earlier; may be stale for this saved report",
        source_label="Synthetic public evidence",
        rights_status="internal_demo_only",
        summary_label=summary_label,
        limitations=("Synthetic limited/stale public evidence for backend contract tests only.",),
    )


def _all_reviewed_public_sections() -> dict[str, SavedPublicEvidenceSectionRead]:
    labels = {
        "public_company_profile": "Public company profile",
        "public_fundamentals_snapshot": "Public fundamentals snapshot",
        "public_events_calendar": "Public events calendar",
        "public_news_snapshot": "Public news snapshot",
        "public_market_context": "Public market context",
        "public_technical_context": "Public technical context",
    }
    return {
        key: _reviewed_public_section(key, label, f"Reviewed synthetic {label.lower()}.")
        for key, label in labels.items()
    }


def _evidence_with_public_sections(
    sections: dict[str, SavedPublicEvidenceSectionRead],
) -> SavedEvidencePackageRead:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    assert evidence.public_evidence is not None
    public_evidence = evidence.public_evidence.model_copy(
        update={"public_evidence_mode": "synthetic_demo", **sections}
    )
    return evidence.model_copy(update={"public_evidence": public_evidence})


def _single_role_summary_payload(
    role_name: str,
    display_name: str,
    evidence_references: tuple[str, ...],
    summary_markdown: str,
) -> dict:
    return {
        "run_status": "partially_completed",
        "provider_mode": "deterministic_template",
        "role_summaries": (
            {
                "role_name": role_name,
                "display_name": display_name,
                "role_status": "completed",
                "provider_status": "ok",
                "summary_markdown": summary_markdown,
                "evidence_references": evidence_references,
                "warning_codes": (),
                "unavailable_reason": None,
            },
        ),
        "warning_codes": (),
        "report_status": "full_agent_report",
        "final_synthesis_markdown": "Agent Team analysis is generated from the saved evidence package.",
        "final_synthesis_authored_by": "deterministic_template",
        "evidence_schema_version": "p29a_t1_v1",
        "evidence_references": ("trade_intent_summary",),
    }


def _saved_evidence_with_unavailable_market_quote() -> SavedEvidencePackageRead:
    evidence = SavedEvidencePackageRead.from_saved_review_artifact(_saved_review_artifact())
    return evidence.model_copy(
        update={
            "market_quote_freshness": SavedEvidenceSectionRead(
                section_key="market_quote_freshness",
                section_label="Market quote freshness",
                availability="not_available",
                summary_label=None,
            )
        }
    )


class _ReplayEdgarProfileClient:
    def __init__(
        self,
        *,
        company_tickers: dict | None = None,
        submissions: dict | None = None,
        raise_on_call: bool = False,
        exception_message: str | None = None,
    ) -> None:
        self.company_tickers = company_tickers or {
            "0": {"cik_str": 1234, "ticker": "EXMP", "title": "Example Public Test Company, Inc."}
        }
        self.submissions = submissions or {
            "name": "Example Public Test Company, Inc.",
            "tickers": ["EXMP"],
            "exchanges": ["Nasdaq"],
            "sicDescription": "Security Brokers, Dealers & Flotation Companies",
            "fiscalYearEnd": "1231",
        }
        self.raise_on_call = raise_on_call
        self.exception_message = exception_message
        self._calls: list[str] = []

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch_company_tickers(self) -> dict:
        self._calls.append("fetch_company_tickers")
        if self.raise_on_call:
            raise AssertionError("EDGAR replay client should not be called")
        if self.exception_message is not None:
            raise RuntimeError(self.exception_message)
        return self.company_tickers

    def fetch_submissions(self, cik_reference: str) -> dict:
        self._calls.append(f"fetch_submissions:{cik_reference}")
        if self.raise_on_call:
            raise AssertionError("EDGAR replay client should not be called")
        return self.submissions


def _live_ready_edgar_policy(**updates: object) -> EdgarCompanyProfileSourcePolicy:
    defaults = {
        "enabled": True,
        "external_access_enabled": True,
        "runtime_environment": "local",
        "declared_user_agent": "Portfolio Copilot local demo contact engineering@example.test",
        "request_timeout_seconds": 3.0,
        "response_size_cap_bytes": 100_000,
        "request_budget_per_run": 3,
    }
    defaults.update(updates)
    return EdgarCompanyProfileSourcePolicy(**defaults)


class _FakeEdgarHttpTransport:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def fetch_json(
        self,
        endpoint_url: str,
        *,
        user_agent: str,
        timeout_seconds: float,
        response_size_cap_bytes: int,
    ) -> dict:
        self.requests.append(
            {
                "endpoint_url": endpoint_url,
                "user_agent": user_agent,
                "timeout_seconds": timeout_seconds,
                "response_size_cap_bytes": response_size_cap_bytes,
            }
        )
        if "company_tickers" in endpoint_url:
            return {"0": {"cik_str": 1234, "ticker": "EXMP", "title": "Example Public Test Company, Inc."}}
        return {
            "name": "Example Public Test Company, Inc.",
            "tickers": ["EXMP"],
            "exchanges": ["Nasdaq"],
            "sicDescription": "Security Brokers, Dealers & Flotation Companies",
            "fiscalYearEnd": "1231",
        }
