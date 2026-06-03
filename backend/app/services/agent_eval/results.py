"""Result types for the reusable agent evaluation harness (P25A-T2).

These are plain, app-owned, safe structures. ``EvalFinding`` is shaped so its
fields map directly onto ``AgentReviewRunState.eval_flags`` entries. Detail
strings are fixed, generic, safe constants — they NEVER echo offending content
(no private values, no metric tokens, no prohibited phrasing).
"""

from dataclasses import asdict, dataclass
from typing import Literal

from app.services.agent_team.prompt_safety import validate_agent_team_text


EvalStatus = Literal["passed", "flagged", "deferred"]

EVAL_STATUSES: tuple[str, ...] = ("passed", "flagged", "deferred")

# Fixed, safe detail strings. Never interpolate offending content into these.
DETAIL_FORBIDDEN_WORDING = "prohibited advice or execution wording detected"
DETAIL_UNGROUNDED_FIGURE = "ungrounded numeric figure detected in commentary"
DETAIL_PRIVACY_KEY = "forbidden private key detected"
DETAIL_PRIVACY_VALUE = "forbidden private value or credential-like pattern detected"
DETAIL_OUTPUT_SAFETY = "generated text tripped the output-safety boundary"
DETAIL_ROLE_BOUNDARY = "public role received non-public evidence"
DETAIL_EVIDENCE_DIVERGED = "deterministic evidence summary diverged from projection"
DETAIL_NO_PROJECTION = "no projection summary provided to compare"
DETAIL_CLEAN_RUN = "clean_run"
DETAIL_PARTIAL_RUN = "partial_run"


@dataclass(frozen=True)
class EvalFinding:
    """One evaluation result. Safe to map onto ``AgentReviewEvalFlag``."""

    check: str
    status: str
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in EVAL_STATUSES:
            raise ValueError(f"unsupported eval status: {self.status}")
        if not self.check.strip():
            raise ValueError("check must not be empty")
        validate_agent_team_text(asdict(self), label="agent-eval finding")


@dataclass(frozen=True)
class EvalReport:
    """Ordered collection of findings."""

    findings: tuple[EvalFinding, ...] = ()

    @property
    def passed(self) -> bool:
        return all(finding.status != "flagged" for finding in self.findings)

    @property
    def flagged(self) -> tuple[EvalFinding, ...]:
        return tuple(finding for finding in self.findings if finding.status == "flagged")

    def to_flag_dicts(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {"check": finding.check, "status": finding.status, "detail": finding.detail}
            for finding in self.findings
        )
