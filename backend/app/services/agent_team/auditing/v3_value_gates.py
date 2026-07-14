"""P36 value-bearing report gates and version-keyed frozen-artifact checks.

This module is intentionally separate from the p35 live-note gates.  A frozen
v2 artifact keeps its legacy gate path; a p36 artifact uses these provenance
and identifier checks only.  No caller may combine the two gate families.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import re
from typing import Iterable, Protocol

from app.services.agent_team.auditing.live_report_gates import (
    DATE_RE,
    NUMBER_RE,
    validate_live_report_consistency,
    prompt_fact_labels_for_tool_result,
)
from app.services.agent_team.auditing.p36_constants import P36_ATTRIBUTION_MARKERS
from app.services.agent_team.llm_clients.contracts import find_secret_like_values
from app.services.agent_team.safety.report_output_safety import SOURCE_LEAK_PATTERNS
from app.services.agent_team.tools import P36_CALC_TOOL_CONTRACT_VERSION, SEC_RAW_PATH_OR_FILE_RE
from app.services.reports.source_snapshots import FRED_MACRO_SERIES


P36_ROLE_PROMPT_VERSION = "p36-role-analysis-v1"
P36_PM_PROMPT_VERSION = "p36-pm-synthesis-v1"
P36_ARTIFACT_SCHEMA_VERSION = "p36_tool_run_freeze_v1"
V2_ARTIFACT_SCHEMA_VERSION = "p33a_tool_run_freeze_v1"

NUMERIC_PROVENANCE_FLAG = "numeric_provenance_blocked"
IDENTIFIER_PRIVACY_FLAG = "identifier_privacy_blocked"
IDENTIFIER_AMBIGUOUS_FLAG = "identifier_ambiguous_dropped"
ADVICE_BOUNDARY_FLAG = "advice_boundary_blocked"
ATTRIBUTION_REQUIRED_FLAG = "attribution_required_blocked"
STRUCTURE_CONTRACT_FLAG = "structure_contract_blocked"
WHAT_WAS_VERIFIED_FLAG = "what_was_verified_blocked"
GROUNDING_FLAG = "grounding_blocked"

P36_RISK_HEADINGS = (
    "#### Risk and exposure analysis",
    "##### What this trade changes",
    "##### Concentration and reference points",
    "##### Input trust and freshness",
    "##### What was verified",
)
P36_RISK_TABLE_HEADER = "| Context item | Value or finding | Source and as-of | Status/caveat |"
P36_PUBLIC_ANALYST_ROLES = frozenset({"technical_analyst", "fundamentals_analyst", "news_analyst"})
P36_PUBLIC_TITLE_PREFIXES = {
    "technical_analyst": "#### Technical analysis — ",
    "fundamentals_analyst": "#### Company context — ",
    "news_analyst": "#### Events and macro context — ",
}
P36_PUBLIC_HEADING_TAILS = {
    "technical_analyst": (
        "##### Range and trend context",
        "##### Volatility context",
        "##### Gaps and caveats",
        "##### What was verified",
    ),
    "fundamentals_analyst": (
        "##### Recency and coverage",
        "##### What was verified",
    ),
    "news_analyst": (
        "##### Filing and release record",
        "##### Recency against this review",
        "##### What was verified",
    ),
}
P36_PUBLIC_WORD_BOUNDS = {
    "technical_analyst": (125, 400),
    "fundamentals_analyst": (90, 400),
    "news_analyst": (90, 400),
}
# The source snapshot defines every governed display label. No free-text alias
# can authorize a macro number in News prose.
FRED_MACRO_SERIES_DISPLAY_ALIASES = frozenset(item.label.lower() for item in FRED_MACRO_SERIES)

_LONG_DATE_RE = re.compile(r"\b([A-Z][a-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?\b")
_SPELLED_MAGNITUDE_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety)\s+"
    r"(?:percent|per\s+cent|dollars?|points?|basis\s+points?|shares?|contracts?|days?)\b",
    re.IGNORECASE,
)
_SPELLED_CARDINALS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_MONTHS = {
    name: index
    for index, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}
_ACCOUNT_NUMBER_RE = re.compile(r"\b(?:account|acct|a/c)\s*(?:number|no\.?|#)?\s*[:#]?\s*\d+\b", re.IGNORECASE)
_MASKED_ACCOUNT_RE = re.compile(r"(?:[*Xx#]{2,}[-–\s]?\d{2,})")
_UUID_RE = re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.IGNORECASE)
_PROVIDER_IDENTIFIER_RE = re.compile(
    r"\b(?:snaptrade|broker|provider)[_-]?(?:id|user|account|connection|secret|token)\s*[:=#-]?\s*[A-Za-z0-9_-]{5,}\b",
    re.IGNORECASE,
)
_COMPOUND_PRIVATE_TOKEN_RE = re.compile(
    r"\b(?:cash_balance|raw_balance|buying_power|raw_holdings|raw_positions|tax_lot|"
    r"account_id|provider_account_id|broker_account_id|provider_connection_id|raw_payload)\b",
    re.IGNORECASE,
)
_IDENTIFIER_CONTEXT_RE = re.compile(r"\b(?:account|acct|a/c|id|number|reference|user|connection|contract)\b", re.IGNORECASE)
_F4_FORECAST_RE = re.compile(r"\b(?:likely|will|expected|forecast|predict|poised to|momentum)\b", re.IGNORECASE)
_F4_RATING_RE = re.compile(r"\b(?:bullish|bearish|buy|sell|hold|overweight|underweight|attractive|cheap|expensive)\b", re.IGNORECASE)
_F4_SUITABILITY_RE = re.compile(
    r"\b(?:too|overly|excessively)\s+concentrated\b|\b(?:acceptable|comfortable|prudent|excessive|healthy|fine|reasonable|appropriate|suitable)\s+"
    r"(?:risk|size|position|concentration)\b|\bwell diversified\b|\bsafe(?:ly)?\b",
    re.IGNORECASE,
)
_F4_ACTION_RE = re.compile(r"\b(?:consider|should|recommend|must|need to)\b", re.IGNORECASE)
_F4_SIZING_HORIZON_RE = re.compile(
    r"\b(?:price\s+target|target\s+price|half|full|smaller|larger)\s+(?:position|size)\b|"
    r"\b(?:long|short|medium)[- ](?:term|horizon)\b(?!\s+(?:averages?|moving|trend))",
    re.IGNORECASE,
)
_F4_NEWS_INTERPRETATION_RE = re.compile(
    r"\b(?:priced in|dovish|hawkish|rate cut|rate hike|material(?:ity)?)\b",
    re.IGNORECASE,
)
_F4_INTERPRETATION_RE = re.compile(
    r"\b(?:downtrend|uptrend|overbought|oversold|compression|easing|elevated|low leverage|high leverage|concentrates?|concentration|drawdown|trend|conventional)\b",
    re.IGNORECASE,
)
_F11_UNGROUNDED_RE = re.compile(r"\b(?:filing\s+(?:says?|states?|discloses?|reveals?|reports?)|according to the filing)\b", re.IGNORECASE)


class _ToolResultLike(Protocol):
    tool_name: str
    contract_version: str
    summary_payload: dict[str, object]
    availability: str
    freshness: str | None
    as_of: datetime | None


def validate_v3_value_bearing_markdown(*, markdown: str, role_results: tuple[_ToolResultLike, ...]) -> str | None:
    """Return the first P36 value-gate failure for one live role or PM block.

    F-5 intentionally runs first but leaves identifier-shaped spans to F-6 so
    an account-number canary receives the stronger privacy disposition.
    """

    allowed = _allowed_numeric_values(role_results)
    provenance_flag = _numeric_provenance_flag(markdown=markdown, allowed=allowed)
    if provenance_flag is not None:
        return provenance_flag
    return _identifier_privacy_flag(markdown, allowed=allowed)


def validate_p36_risk_analysis_section(*, markdown: str, role_results: tuple[_ToolResultLike, ...]) -> str | None:
    """Apply the ordered P36 F-4 through F-11 checks to the Risk surface."""

    value_flag = validate_v3_value_bearing_markdown(markdown=markdown, role_results=role_results)
    if value_flag is not None:
        return value_flag
    advice_flag = _advice_boundary_flag(markdown)
    if advice_flag is not None:
        return advice_flag
    structure_flag = _risk_structure_flag(markdown)
    if structure_flag is not None:
        return structure_flag
    verified_flag = _what_was_verified_flag(markdown=markdown, role_results=role_results)
    if verified_flag is not None:
        return verified_flag
    if _F11_UNGROUNDED_RE.search(markdown):
        return GROUNDING_FLAG
    return None


def validate_p36_public_analysis_section(
    *,
    role_name: str,
    markdown: str,
    role_results: tuple[_ToolResultLike, ...],
) -> str | None:
    """Apply F-4 through F-11 to one P36 public analyst surface."""

    if role_name not in P36_PUBLIC_ANALYST_ROLES:
        return STRUCTURE_CONTRACT_FLAG
    value_flag = validate_v3_value_bearing_markdown(markdown=markdown, role_results=role_results)
    if value_flag is not None:
        return value_flag
    advice_flag = _advice_boundary_flag(markdown, role_name=role_name)
    if advice_flag is not None:
        return advice_flag
    structure_flag = _public_structure_flag(role_name=role_name, markdown=markdown, role_results=role_results)
    if structure_flag is not None:
        return structure_flag
    verified_flag = _what_was_verified_flag(markdown=markdown, role_results=role_results)
    if verified_flag is not None:
        return verified_flag
    if _F11_UNGROUNDED_RE.search(markdown):
        return GROUNDING_FLAG
    if role_name == "news_analyst":
        return _macro_series_grounding_flag(markdown=markdown, role_results=role_results)
    return None


def frozen_artifact_gate_version(artifact: object) -> str:
    """Derive one gate family from frozen prompt/calc versions; never mix them."""

    schema_version = str(getattr(artifact, "artifact_schema_version", ""))
    tool_results = tuple(getattr(artifact, "tool_results", ()) or ())
    provider_runs = tuple(getattr(artifact, "provider_runs", ()) or ())
    has_p36_calc = any(getattr(item, "contract_version", None) == P36_CALC_TOOL_CONTRACT_VERSION for item in tool_results)
    prompt_versions = {str(getattr(item, "prompt_version", "")) for item in provider_runs}
    has_v3_prompt = bool(prompt_versions.intersection({P36_ROLE_PROMPT_VERSION, P36_PM_PROMPT_VERSION}))
    has_v2_prompt = any(version and version not in {P36_ROLE_PROMPT_VERSION, P36_PM_PROMPT_VERSION} for version in prompt_versions)
    if has_p36_calc or has_v3_prompt:
        if schema_version != P36_ARTIFACT_SCHEMA_VERSION or has_v2_prompt:
            raise ValueError("p36 frozen artifact must use only the v3 gate contract")
        return "v3"
    if schema_version != V2_ARTIFACT_SCHEMA_VERSION:
        raise ValueError("legacy frozen artifact must use the v2 gate contract")
    return "v2"


def validate_frozen_artifact_gate_set(artifact: object) -> None:
    """Revalidate frozen additive live text without rerunning a provider or tool."""

    gate_version = frozen_artifact_gate_version(artifact)
    all_tool_results = tuple(getattr(artifact, "tool_results", ()) or ())
    provider_runs = tuple(getattr(artifact, "provider_runs", ()) or ())
    has_p36_risk_live_run = any(
        getattr(item, "role_name", None) == "risk_management_agent"
        and getattr(item, "prompt_version", None) == P36_ROLE_PROMPT_VERSION
        for item in provider_runs
    )
    for finding_set in tuple(getattr(artifact, "audited_findings", ()) or ()):
        markdown = getattr(finding_set, "live_report_markdown", None)
        if not isinstance(markdown, str) or not markdown.strip():
            continue
        if gate_version == "v3":
            # F-5 is role-scoped: a number frozen for another analyst cannot
            # authorize this role's prose. PM results are likewise scoped to
            # the PM's own verified calculation requests when that surface is
            # enabled in a later slice.
            role_results = tuple(
                result
                for result in all_tool_results
                if getattr(result, "role_name", None) == getattr(finding_set, "role_name", None)
            )
            role_name = getattr(finding_set, "role_name", None)
            flag = (
                validate_p36_risk_analysis_section(markdown=markdown, role_results=role_results)
                if has_p36_risk_live_run and role_name == "risk_management_agent"
                else validate_p36_public_analysis_section(
                    role_name=role_name,
                    markdown=markdown,
                    role_results=role_results,
                )
                if role_name in P36_PUBLIC_ANALYST_ROLES
                else validate_v3_value_bearing_markdown(markdown=markdown, role_results=role_results)
            )
        else:
            flag = validate_live_report_consistency(markdown=markdown, role_results=all_tool_results)  # type: ignore[arg-type]
        if flag is not None:
            raise ValueError(f"frozen artifact {gate_version} gate rejected live report: {flag}")


class _AllowedNumbers:
    def __init__(self) -> None:
        self.decimals: set[Decimal] = set()
        self.dates: set[str] = set()
        self.structural_integers: set[str] = set()


def _allowed_numeric_values(role_results: Iterable[_ToolResultLike]) -> _AllowedNumbers:
    allowed = _AllowedNumbers()
    for result in role_results:
        for row in prompt_fact_labels_for_tool_result(result):  # type: ignore[arg-type]
            key = row["fact_key"]
            value = row["value_label"]
            allowed.structural_integers.update(re.findall(r"\d+", key))
            allowed.structural_integers.update(re.findall(r"\d+", value))
            if DATE_RE.fullmatch(value):
                allowed.dates.add(value)
                continue
            for token in NUMBER_RE.findall(value):
                decimal = _decimal(token)
                if decimal is not None:
                    allowed.decimals.add(decimal)
    return allowed


def _numeric_provenance_flag(*, markdown: str, allowed: _AllowedNumbers) -> str | None:
    scrubbed = _scrub_valid_dates(markdown, allowed.dates)
    if scrubbed is None:
        return NUMERIC_PROVENANCE_FLAG
    for match in NUMBER_RE.finditer(scrubbed):
        if _explicit_identifier_context(markdown, match.start(), match.end()):
            continue
        if _ambiguous_identifier_context(markdown, match.start(), match.end(), match.group(0)):
            continue
        if not _numeric_allowed(match.group(0), allowed):
            return NUMERIC_PROVENANCE_FLAG
    for match in _SPELLED_MAGNITUDE_RE.finditer(scrubbed):
        value = _SPELLED_CARDINALS[match.group(1).lower()]
        if Decimal(value) not in allowed.decimals:
            return NUMERIC_PROVENANCE_FLAG
    return None


def _scrub_valid_dates(markdown: str, allowed_dates: set[str]) -> str | None:
    for token in DATE_RE.findall(markdown):
        if token not in allowed_dates:
            return None
    scrubbed = DATE_RE.sub(" ", markdown)
    for match in _LONG_DATE_RE.finditer(markdown):
        month = _MONTHS.get(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else _inferred_year(allowed_dates)
        if month is None or year is None:
            return None
        try:
            normalized = date(year, month, day).isoformat()
        except ValueError:
            return None
        if normalized not in allowed_dates:
            return None
    return _LONG_DATE_RE.sub(" ", scrubbed)


def _inferred_year(allowed_dates: set[str]) -> int | None:
    years = {int(value[:4]) for value in allowed_dates if DATE_RE.fullmatch(value)}
    return next(iter(years)) if len(years) == 1 else None


def _numeric_allowed(token: str, allowed: _AllowedNumbers) -> bool:
    normalized = token.replace(",", "")
    if normalized in allowed.structural_integers:
        return True
    decimal = _decimal(normalized)
    if decimal is None:
        return False
    for candidate in allowed.decimals:
        if decimal == candidate:
            return True
        if decimal != 0 and candidate != 0 and (decimal < 0) != (candidate < 0):
            continue
        places = len(normalized.split(".", 1)[1]) if "." in normalized else 0
        if candidate.quantize(Decimal("1").scaleb(-places), rounding=ROUND_HALF_EVEN) == decimal:
            return True
    return False


def _decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _explicit_identifier_context(markdown: str, start: int, end: int) -> bool:
    window = markdown[max(0, start - 72) : min(len(markdown), end + 72)]
    return bool(
        _ACCOUNT_NUMBER_RE.search(window)
        or _MASKED_ACCOUNT_RE.search(window)
        or _PROVIDER_IDENTIFIER_RE.search(window)
    )


def _ambiguous_identifier_context(markdown: str, start: int, end: int, token: str) -> bool:
    digits = token.replace(",", "").lstrip("+-").replace(".", "")
    if len(digits) < 5:
        return False
    window = markdown[max(0, start - 72) : min(len(markdown), end + 72)]
    return bool(_IDENTIFIER_CONTEXT_RE.search(window))


def _identifier_privacy_flag(markdown: str, *, allowed: _AllowedNumbers) -> str | None:
    if any(pattern.search(markdown) for pattern in SOURCE_LEAK_PATTERNS) or SEC_RAW_PATH_OR_FILE_RE.search(markdown):
        return IDENTIFIER_PRIVACY_FLAG
    if find_secret_like_values(markdown):
        return IDENTIFIER_PRIVACY_FLAG
    if _COMPOUND_PRIVATE_TOKEN_RE.search(markdown) or _UUID_RE.search(markdown) or _PROVIDER_IDENTIFIER_RE.search(markdown):
        return IDENTIFIER_PRIVACY_FLAG
    if _ACCOUNT_NUMBER_RE.search(markdown) or _MASKED_ACCOUNT_RE.search(markdown):
        return IDENTIFIER_PRIVACY_FLAG
    for match in NUMBER_RE.finditer(markdown):
        if (
            _ambiguous_identifier_context(markdown, match.start(), match.end(), match.group(0))
            and not _numeric_allowed(match.group(0), allowed)
        ):
            return IDENTIFIER_AMBIGUOUS_FLAG
    return None


def _advice_boundary_flag(markdown: str, *, role_name: str | None = None) -> str | None:
    # Execution phrases are rejected by the provider output contract before
    # this gate runs. The runner then drops the entire live Risk section to its
    # deterministic floor, so F-4 deliberately does not double-handle them.
    patterns = (_F4_FORECAST_RE, _F4_RATING_RE, _F4_SUITABILITY_RE, _F4_ACTION_RE, _F4_SIZING_HORIZON_RE)
    if role_name == "news_analyst":
        patterns = (*patterns, _F4_NEWS_INTERPRETATION_RE)
    if any(pattern.search(markdown) for pattern in patterns):
        return ADVICE_BOUNDARY_FLAG
    prose_without_headings = "\n".join(
        line for line in markdown.splitlines() if not line.strip().startswith("#")
    )
    for sentence in re.split(r"(?<=[.!?])\s+", prose_without_headings):
        if _F4_INTERPRETATION_RE.search(sentence) and not any(marker in sentence.lower() for marker in P36_ATTRIBUTION_MARKERS):
            return ATTRIBUTION_REQUIRED_FLAG
    return None


def _risk_structure_flag(markdown: str) -> str | None:
    positions = [markdown.find(heading) for heading in P36_RISK_HEADINGS]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        return STRUCTURE_CONTRACT_FLAG
    heading_lines = [line.strip() for line in markdown.splitlines() if line.strip().startswith("#")]
    if heading_lines != list(P36_RISK_HEADINGS):
        return STRUCTURE_CONTRACT_FLAG
    if markdown.count(P36_RISK_TABLE_HEADER) != 1 or markdown.find(P36_RISK_TABLE_HEADER) < positions[-1]:
        return STRUCTURE_CONTRACT_FLAG
    table_rows = [line for line in markdown.splitlines() if line.strip().startswith("|")]
    nonempty_lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if not table_rows or table_rows[0].strip() != P36_RISK_TABLE_HEADER or not nonempty_lines[-1].startswith("|"):
        return STRUCTURE_CONTRACT_FLAG
    prose = " ".join(
        line
        for line in markdown.splitlines()
        if not line.strip().startswith(("#", "|"))
    )
    word_count = len(re.findall(r"\b[\w'-]+\b", prose))
    return None if 125 <= word_count <= 450 else STRUCTURE_CONTRACT_FLAG


def _public_structure_flag(
    *,
    role_name: str,
    markdown: str,
    role_results: tuple[_ToolResultLike, ...],
) -> str | None:
    symbol = _frozen_symbol(role_results)
    title_prefix = P36_PUBLIC_TITLE_PREFIXES[role_name]
    if symbol is None or not markdown.startswith(f"{title_prefix}{symbol}"):
        return STRUCTURE_CONTRACT_FLAG
    title = f"{title_prefix}{symbol}"
    headings = [line.strip() for line in markdown.splitlines() if line.strip().startswith("#")]
    expected = _public_expected_headings(role_name=role_name, role_results=role_results, title=title)
    if headings != list(expected):
        return STRUCTURE_CONTRACT_FLAG
    if markdown.count(P36_RISK_TABLE_HEADER) != 1 or markdown.find(P36_RISK_TABLE_HEADER) < markdown.find("##### What was verified"):
        return STRUCTURE_CONTRACT_FLAG
    table_rows = [line for line in markdown.splitlines() if line.strip().startswith("|")]
    nonempty_lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if not table_rows or table_rows[0].strip() != P36_RISK_TABLE_HEADER or not nonempty_lines[-1].startswith("|"):
        return STRUCTURE_CONTRACT_FLAG
    prose = " ".join(line for line in markdown.splitlines() if not line.strip().startswith(("#", "|")))
    lower, upper = P36_PUBLIC_WORD_BOUNDS[role_name]
    word_count = len(re.findall(r"\b[\w'-]+\b", prose))
    return None if lower <= word_count <= upper else STRUCTURE_CONTRACT_FLAG


def _public_expected_headings(
    *,
    role_name: str,
    role_results: tuple[_ToolResultLike, ...],
    title: str,
) -> tuple[str, ...]:
    if role_name == "technical_analyst":
        return (title, *P36_PUBLIC_HEADING_TAILS[role_name])
    if role_name == "fundamentals_analyst":
        statement_available = _result_is_available(role_results, "calc_financial_ratios")
        second = "##### Reported record" if statement_available else "##### What was reviewed"
        return (title, second, *P36_PUBLIC_HEADING_TAILS[role_name])
    macro_available = _result_is_available(role_results, "calc_macro_series_change")
    macro = ("##### Macro backdrop",) if macro_available else ()
    return (title, P36_PUBLIC_HEADING_TAILS[role_name][0], *macro, *P36_PUBLIC_HEADING_TAILS[role_name][1:])


def _result_is_available(role_results: tuple[_ToolResultLike, ...], tool_name: str) -> bool:
    return any(
        result.tool_name == tool_name and result.availability in {"available", "limited"}
        for result in role_results
    )


def _frozen_symbol(role_results: tuple[_ToolResultLike, ...]) -> str | None:
    for result in role_results:
        if result.tool_name != "trade_intent_summary":
            continue
        payload = result.summary_payload
        if isinstance(payload, dict):
            symbol = payload.get("symbol_or_underlying")
            if isinstance(symbol, str) and re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", symbol.strip().upper()):
                return symbol.strip().upper()
    return None


def _macro_series_grounding_flag(*, markdown: str, role_results: tuple[_ToolResultLike, ...]) -> str | None:
    labels_by_value = _macro_series_labels_by_value(role_results)
    if not labels_by_value:
        return None
    for sentence in re.split(r"(?<=[.!?])\s+", markdown):
        lowered = sentence.lower()
        for match in NUMBER_RE.finditer(sentence):
            number = _decimal(match.group(0))
            if number is None:
                continue
            labels = labels_by_value.get(number, frozenset())
            if labels and not any(label in lowered for label in labels):
                return GROUNDING_FLAG
    return None


def _macro_series_labels_by_value(role_results: tuple[_ToolResultLike, ...]) -> dict[Decimal, frozenset[str]]:
    labels: dict[Decimal, set[str]] = {}
    for result in role_results:
        if result.tool_name != "calc_macro_series_change":
            continue
        payload = result.summary_payload
        rows = payload.get("value_labels") if isinstance(payload, dict) else None
        if not isinstance(rows, (tuple, list)):
            continue
        current_label: str | None = None
        for row in rows:
            if not isinstance(row, dict):
                continue
            key = row.get("fact_key")
            value = row.get("value_label")
            if key == "macro_series_label" and isinstance(value, str):
                candidate = value.lower()
                current_label = candidate if candidate in FRED_MACRO_SERIES_DISPLAY_ALIASES else None
                continue
            if current_label is None or key not in {"macro_current_value", "macro_prior_value", "macro_absolute_change"}:
                continue
            if not isinstance(value, str):
                continue
            for token in NUMBER_RE.findall(value):
                decimal = _decimal(token)
                if decimal is not None:
                    labels.setdefault(decimal, set()).add(current_label)
    return {value: frozenset(items) for value, items in labels.items()}


def _what_was_verified_flag(*, markdown: str, role_results: tuple[_ToolResultLike, ...]) -> str | None:
    start = markdown.find("##### What was verified")
    table_start = markdown.find(P36_RISK_TABLE_HEADER)
    if start < 0 or table_start < start:
        return WHAT_WAS_VERIFIED_FLAG
    section = markdown[start:table_start]
    allowed_dates = _allowed_numeric_values(role_results).dates
    if not any(token in section for token in allowed_dates):
        return WHAT_WAS_VERIFIED_FLAG
    source_or_method: set[str] = set()
    for result in role_results:
        source_label = getattr(result, "source_label", None)
        if isinstance(source_label, str) and source_label:
            source_or_method.add(source_label.lower())
        payload = getattr(result, "summary_payload", {})
        if isinstance(payload, dict):
            method = payload.get("method_label")
            if isinstance(method, str) and method:
                source_or_method.add(method.lower())
    return None if any(label in section.lower() for label in source_or_method) else WHAT_WAS_VERIFIED_FLAG
