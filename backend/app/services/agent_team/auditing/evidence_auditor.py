"""Evidence Auditor for the tool-mediated Agent Team (P34A-T11E).

Extracted from the god-module: audited-finding filtering, fail-closed hard
blocks (advice / private leak / invented metric / SEC+FRED interpretation /
source leak), and structured contradiction detection. No behavior change.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re
from typing import Callable, Literal

from app.schemas.reports import (
    SavedAgentTeamRoleSummaryRead,
    SavedAgentTeamSummaryRead,
    SavedEvidencePackageRead,
    SavedToolMediatedRunArtifactRead,
    validate_saved_tool_freeze_payload,
)
from app.services.agent_team.llm_clients.contracts import (
    AGENT_TEAM_ROLES,
    AgentTeamRole,
    LLMProvider,
    LLMProviderMessage,
    LLMProviderRequest,
    LLMProviderResponse,
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.safety.output_safety import validate_llm_provider_output
from app.services.agent_team.llm_clients.factory import LLMProviderResolution
from app.services.agent_team.safety.report_output_safety import (
    INVENTED_LEVEL_PATTERNS,
    REPORT_PROHIBITED_PHRASES,
    ROLE_ALLOWED_EVIDENCE_KEYS,
    SOURCE_LEAK_PATTERNS,
)
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES, role_definition
from app.services.agent_team.tools import (
    TOOL_FORBIDDEN_KEYS,
    TOOL_GENERATED_METRIC_PATTERNS,
    TOOL_PROHIBITED_PHRASES,
    SEC_RAW_PATH_OR_FILE_RE,
)
from app.services.agent_team.tools import (
    ToolRegistryEntry,
    ToolRequest,
    ToolResult,
    default_tool_registry,
    execute_tool_request,
    validate_tool_payload,
)
from app.services.privacy import find_forbidden_keys
from app.services.reports.agent_team_report import _deterministic_draft_summary, _validate_or_fallback
from app.services.reports.public_evidence import build_public_role_evidence_projection



from app.services.agent_team.orchestration.models import *  # noqa: F401,F403
from app.services.agent_team.auditing.live_report_gates import (
    LIVE_GATE_WARNING_BY_FLAG,
    validate_live_report_consistency,
    validate_live_report_structure,
)
from app.services.agent_team.auditing.v3_value_gates import (
    ADVICE_BOUNDARY_FLAG,
    ATTRIBUTION_REQUIRED_FLAG,
    GROUNDING_FLAG,
    IDENTIFIER_AMBIGUOUS_FLAG,
    IDENTIFIER_PRIVACY_FLAG,
    NUMERIC_PROVENANCE_FLAG,
    STRUCTURE_CONTRACT_FLAG,
    WHAT_WAS_VERIFIED_FLAG,
    P36_PUBLIC_ANALYST_ROLES,
    validate_p36_public_analysis_section,
    validate_p36_risk_analysis_section,
)


AUDITOR_EVAL_WARNING_CODES = frozenset(
    {
        "private_leak_blocked",
        "advice_wording_blocked",
        "invented_metric_blocked",
        "fred_interpretation_blocked",
        "numeric_consistency_blocked",
        "category_consistency_blocked",
        "structure_contract_blocked",
        "live_provider_validation_failed",
        "portfolio_claim_blocked",
        "sec_interpretation_blocked",
        "source_leak_blocked",
        "display_token_blocked",
        ADVICE_BOUNDARY_FLAG,
        ATTRIBUTION_REQUIRED_FLAG,
        GROUNDING_FLAG,
        WHAT_WAS_VERIFIED_FLAG,
        NUMERIC_PROVENANCE_FLAG,
        IDENTIFIER_PRIVACY_FLAG,
        IDENTIFIER_AMBIGUOUS_FLAG,
    }
)
P36_LIVE_GATE_WARNING_BY_FLAG = {
    ADVICE_BOUNDARY_FLAG: "live_advice_boundary_dropped",
    ATTRIBUTION_REQUIRED_FLAG: "live_attribution_required_dropped",
    WHAT_WAS_VERIFIED_FLAG: "live_what_was_verified_dropped",
    GROUNDING_FLAG: "live_grounding_dropped",
}

# The Risk Manager's reviewed static prompt requires plain-language discussion
# of these topics.  They describe a topic, not a private value.  This narrow
# exception applies only while auditing generated role-note prose; compound
# private tokens, structural disclosures, secrets, and all input/envelope
# validation remain fail-closed.
_ROLE_NOTE_TOPIC_TOKENS = frozenset({"cash", "holdings", "positions"})
_ROLE_NOTE_KEY_VALUE_DISCLOSURE_RE = re.compile(r"\b(?:cash|holdings|positions)\s*[:=]", re.IGNORECASE)
STRUCTURED_NEGATIVE_SIGNAL_TOKENS = (
    "stale",
    "unavailable",
    "not_available",
    "not_reviewed",
    "unknown",
    "not_evaluated",
    "caveated",
    "unverified",
    "limited",
)
STRUCTURED_POSITIVE_SIGNAL_TOKENS = (
    "fresh",
    "verified",
    "available_ok",
    "reviewed_ok",
)
SEC_INTERPRETATION_PATTERNS = (
    re.compile(
        r"\b(?:sec edgar|filings?|8-k|10-k|10-q)\b[^.\n]{0,80}"
        r"\b(signals?|bullish|bearish|materiality|material event|significant|catalyst|implies|suggests|priced in|reaction|beat|miss|guidance)\b"
    ),
    re.compile(
        r"\b(signals?|bullish|bearish|materiality|material event|significant|catalyst|implies|suggests|priced in|reaction|beat|miss|guidance)\b"
        r"[^.\n]{0,80}\b(?:sec edgar|filings?|8-k|10-k|10-q)\b"
    ),
    re.compile(
        r"\b(?:sec edgar|filings?|8-k|10-k|10-q)\b[^.\n]{0,80}"
        r"\b(urgent|act now|time-sensitive|before earnings)\b"
    ),
    re.compile(
        r"\b(urgent|act now|time-sensitive|before earnings)\b"
        r"[^.\n]{0,80}\b(?:sec edgar|filings?|8-k|10-k|10-q)\b"
    ),
    re.compile(r"\bfilings?\s+(says?|states?|discloses?|reveals?|reports?)\b"),
    re.compile(r"\baccording to the filing\b"),
    re.compile(r"\b(sec endorsement|endorsed by the sec|approved by the sec)\b"),
)
FRED_INTERPRETATION_PATTERNS = (
    re.compile(
        r"\b(?:fred|macro|cpi|inflation|fomc|rate|rates|employment situation|economic release)\b[^.\n]{0,90}"
        r"\b(signals?|suggests?|implies|bullish|bearish|forecast|predicts?|market signal|market move|urgent|dovish|hawkish|rate cut|rate hike)\b"
    ),
    re.compile(
        r"\b(signals?|suggests?|implies|bullish|bearish|forecast|predicts?|market signal|market move|urgent|dovish|hawkish|rate cut|rate hike)\b"
        r"[^.\n]{0,90}\b(?:fred|macro|cpi|inflation|fomc|rate|rates|employment situation|economic release)\b"
    ),
    re.compile(r"\bbefore (?:the )?(?:fred|macro|cpi|fomc|economic )?release\b"),
)


def audit_findings(
    finding_sets: tuple[RoleFindingSet, ...],
    results_by_role: dict[str, tuple[ToolResult, ...]],
    received_refs_by_role: dict[str, frozenset[str]],
    *,
    repass: bool = False,
    p36_risk_mode: bool = False,
    p36_public_mode: bool = False,
) -> tuple[AuditorRecord, tuple[RoleFindingSet, ...]]:
    availability_by_role = _availability_by_role(results_by_role)
    usable = usable_content_by_role()
    dropped: list[str] = []
    flags: list[str] = []
    audited: list[RoleFindingSet] = []
    fixable_failure = False
    for finding_set in finding_sets:
        flags.extend(code for code in finding_set.warning_codes if code in AUDITOR_EVAL_WARNING_CODES)
        live_report_markdown = finding_set.live_report_markdown
        live_warning_codes: tuple[str, ...] = ()
        if live_report_markdown:
            if p36_risk_mode and finding_set.role_name == "risk_management_agent":
                live_drop_flag = validate_p36_risk_analysis_section(
                    markdown=live_report_markdown,
                    role_results=results_by_role.get(finding_set.role_name, ()),
                )
            elif p36_public_mode and finding_set.role_name in P36_PUBLIC_ANALYST_ROLES:
                live_drop_flag = validate_p36_public_analysis_section(
                    role_name=finding_set.role_name,
                    markdown=live_report_markdown,
                    role_results=results_by_role.get(finding_set.role_name, ()),
                )
            else:
                live_drop_flag = validate_live_report_structure(
                    role_name=finding_set.role_name,
                    markdown=live_report_markdown,
                )
                if live_drop_flag is None:
                    live_drop_flag = _hard_block_flag(
                        RoleFinding(
                            finding_type="missing_context",
                            claim_text=live_report_markdown,
                            evidence_refs=tuple(received_refs_by_role.get(finding_set.role_name, frozenset())),
                        ),
                        allow_role_note_topic_vocabulary=True,
                    )
                if live_drop_flag is None:
                    live_drop_flag = validate_live_report_consistency(
                        markdown=live_report_markdown,
                        role_results=results_by_role.get(finding_set.role_name, ()),
                    )
            if live_drop_flag is not None:
                dropped.append(live_drop_flag)
                flags.append(live_drop_flag)
                warning = LIVE_GATE_WARNING_BY_FLAG.get(
                    live_drop_flag,
                    P36_LIVE_GATE_WARNING_BY_FLAG.get(live_drop_flag, "live_provider_safety_fallback"),
                )
                live_warning_codes = (warning,)
                live_report_markdown = None
        findings: list[RoleFinding] = []
        for finding in finding_set.findings:
            blocked_flag = _hard_block_flag(finding)
            if blocked_flag is not None:
                dropped.append(blocked_flag)
                flags.append(blocked_flag)
                continue
            refs = tuple(ref for ref in finding.evidence_refs if ref in received_refs_by_role.get(finding_set.role_name, frozenset()))
            if not refs:
                dropped.append("unsupported_claim")
                fixable_failure = True
                continue
            filtered = tuple(ref for ref in refs if ref in usable[finding_set.role_name])
            if len(filtered) != len(refs):
                dropped.append("citable_boundary_filtered")
                fixable_failure = True
            available = tuple(
                ref
                for ref in filtered
                if availability_by_role.get(finding_set.role_name, {}).get(ref) in {"available", "limited"}
            )
            if len(available) != len(filtered):
                dropped.append("unavailable_ref_filtered")
                fixable_failure = True
            if not available:
                continue
            findings.append(
                RoleFinding(
                    finding_type=finding.finding_type,
                    claim_text=finding.claim_text,
                    evidence_refs=available,
                    caveat_codes=finding.caveat_codes,
                )
            )
        audited.append(
            RoleFindingSet(
                role_name=finding_set.role_name,
                role_status=finding_set.role_status,
                findings=tuple(findings),
                warning_codes=tuple(dict.fromkeys((*finding_set.warning_codes, *live_warning_codes, *flags))),
                unavailable_reason=finding_set.unavailable_reason,
                live_report_markdown=live_report_markdown,
                analysis_status=finding_set.analysis_status,
            )
        )
    contradictions = _detect_contradictions(tuple(audited))
    if contradictions:
        flags.append("contradiction_open_question")
    verdicts = tuple((item.role_name, bool(item.findings) or item.role_status == "skipped") for item in audited)
    return (
        AuditorRecord(
            audit_version=AUDIT_VERSION,
            role_verdicts=verdicts,
            contradictions=contradictions,
            dropped_claims=tuple(dict.fromkeys(dropped)),
            repass_triggered=(fixable_failure or bool(contradictions)) and not repass,
            eval_flags=tuple(dict.fromkeys(flags)),
        ),
        tuple(audited),
    )


def _hard_block_flag(
    finding: RoleFinding,
    *,
    allow_role_note_topic_vocabulary: bool = False,
) -> str | None:
    payload = asdict(finding)
    if find_forbidden_keys(payload, forbidden_keys=TOOL_FORBIDDEN_KEYS):
        return "private_leak_blocked"
    if allow_role_note_topic_vocabulary:
        # Keep refs, caveat metadata, and every non-prose field under the full
        # scan. Only this generated role-note sentence may use the three
        # reviewed topic words in ordinary language.
        non_prose_payload = {**payload, "claim_text": ""}
        if find_forbidden_string_values(non_prose_payload) or find_forbidden_string_values(
            finding.claim_text,
            ignored_plain_tokens=_ROLE_NOTE_TOPIC_TOKENS,
        ):
            return "private_leak_blocked"
    elif find_forbidden_string_values(payload):
        return "private_leak_blocked"
    rendered = repr(payload).lower()
    if allow_role_note_topic_vocabulary and _ROLE_NOTE_KEY_VALUE_DISCLOSURE_RE.search(finding.claim_text):
        return "private_leak_blocked"
    if any(phrase in rendered for phrase in (*REPORT_PROHIBITED_PHRASES, *TOOL_PROHIBITED_PHRASES)):
        return "advice_wording_blocked"
    if find_prohibited_llm_phrases(payload):
        return "advice_wording_blocked"
    if find_secret_like_values(payload):
        return "private_leak_blocked"
    if any(pattern.search(rendered) for pattern in SEC_INTERPRETATION_PATTERNS):
        return "sec_interpretation_blocked"
    if any(pattern.search(rendered) for pattern in FRED_INTERPRETATION_PATTERNS):
        return "fred_interpretation_blocked"
    if SEC_RAW_PATH_OR_FILE_RE.search(rendered):
        return "source_leak_blocked"
    if any(code == "live_connective_context" for code in finding.caveat_codes) and LIVE_CONNECTIVE_DIGIT_RE.search(
        finding.claim_text
    ):
        return "invented_metric_blocked"
    if any(pattern.search(rendered) for pattern in (*TOOL_GENERATED_METRIC_PATTERNS, *INVENTED_LEVEL_PATTERNS, *SOURCE_LEAK_PATTERNS)):
        return "invented_metric_blocked"
    return None


def _detect_contradictions(finding_sets: tuple[RoleFindingSet, ...]) -> tuple[Contradiction, ...]:
    by_ref: dict[str, list[tuple[str, RoleFinding]]] = {}
    for finding_set in finding_sets:
        for finding in finding_set.findings:
            for ref in finding.evidence_refs:
                by_ref.setdefault(ref, []).append((finding_set.role_name, finding))
    contradictions: list[Contradiction] = []
    for ref, findings in by_ref.items():
        for index, (role_a, finding_a) in enumerate(findings):
            for role_b, finding_b in findings[index + 1 :]:
                if _opposing_structured_signal(finding_a, finding_b):
                    contradictions.append(
                        Contradiction(
                            evidence_ref=ref,
                            role_a=role_a,
                            role_b=role_b,
                            description="Roles surfaced conflicting freshness or availability stance.",
                        )
                    )
    return tuple(contradictions)


def _opposing_structured_signal(a: RoleFinding, b: RoleFinding) -> bool:
    a_signal = _structured_signal(a.caveat_codes)
    b_signal = _structured_signal(b.caveat_codes)
    return {a_signal, b_signal} == {"positive", "negative"}


def _structured_signal(caveat_codes: tuple[str, ...]) -> str | None:
    rendered = repr(caveat_codes).lower()
    negative = any(token in rendered for token in STRUCTURED_NEGATIVE_SIGNAL_TOKENS)
    positive = any(token in rendered for token in STRUCTURED_POSITIVE_SIGNAL_TOKENS)
    if negative and not positive:
        return "negative"
    if positive and not negative:
        return "positive"
    return None


def _availability_by_role(results_by_role: dict[str, tuple[ToolResult, ...]]) -> dict[str, dict[str, str]]:
    availability: dict[str, dict[str, str]] = {}
    for role, results in results_by_role.items():
        availability[role] = {}
        for result in results:
            for ref in result.evidence_refs:
                availability[role][ref] = result.availability
    return availability
