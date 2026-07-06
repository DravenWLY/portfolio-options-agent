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


AUDITOR_EVAL_WARNING_CODES = frozenset(
    {
        "private_leak_blocked",
        "advice_wording_blocked",
        "invented_metric_blocked",
        "fred_interpretation_blocked",
        "live_provider_validation_failed",
        "sec_interpretation_blocked",
        "source_leak_blocked",
    }
)
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
) -> tuple[AuditorRecord, tuple[RoleFindingSet, ...]]:
    availability_by_role = _availability_by_role(results_by_role)
    usable = usable_content_by_role()
    dropped: list[str] = []
    flags: list[str] = []
    audited: list[RoleFindingSet] = []
    fixable_failure = False
    for finding_set in finding_sets:
        flags.extend(code for code in finding_set.warning_codes if code in AUDITOR_EVAL_WARNING_CODES)
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
                warning_codes=tuple(dict.fromkeys((*finding_set.warning_codes, *flags))),
                unavailable_reason=finding_set.unavailable_reason,
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


def _hard_block_flag(finding: RoleFinding) -> str | None:
    payload = asdict(finding)
    if find_forbidden_keys(payload, forbidden_keys=TOOL_FORBIDDEN_KEYS) or find_forbidden_string_values(payload):
        return "private_leak_blocked"
    rendered = repr(payload).lower()
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
