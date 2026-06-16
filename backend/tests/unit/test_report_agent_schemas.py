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
