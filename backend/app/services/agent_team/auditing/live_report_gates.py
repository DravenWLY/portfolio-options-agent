"""Auditor gates for v3 live role report markdown.

The gates validate only additive live report sections. They never alter the
deterministic finding floor; callers drop ``live_report_markdown`` on failure.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from itertools import chain
import os
import re
from typing import Any, get_args

from app.services.agent_team.tools import (
    P36_CALC_TOOL_CONTRACT_VERSION,
    TOOL_AVAILABILITIES,
    ToolResult,
    validate_tool_payload,
)
from app.services.reports.display_labels import DISPLAY_TOKEN_BLOCKED_FLAG, display_label_for_code, find_internal_display_tokens
from app.services.market_data.models import FreshnessStatus

# T17A-F3: the freshness vocabulary is imported from the canonical market-data
# enum instead of being retyped — manual/eod_only/delayed are real categories
# (a manual-entry quote's envelope freshness IS "manual"), and quoting them
# truthfully must never be treated as a category hallucination.
FRESHNESS_CATEGORY_VOCABULARY = frozenset(get_args(FreshnessStatus))


SUMMARY_TABLE_HEADER = "| Context item | Frozen value or category | Status / caveat |"
ROLE_REQUIRED_HEADINGS: dict[str, tuple[str, ...]] = {
    "technical_analyst": (
        "### Saved market context",
        "### Price and range context",
        "### Trend and momentum context",
        "### Volatility context",
        "### Gaps and caveats",
        "### Summary table",
    ),
    "risk_management_agent": (
        "### Deterministic risk flags",
        "### Freshness and scope",
        "### Option-structure context",
        "### Gaps and caveats",
        "### Summary table",
    ),
    "fundamentals_analyst": (
        "### Reviewed context",
        "### Not reviewed",
        "### Summary table",
    ),
    "news_analyst": (
        "### Reviewed context",
        "### Not reviewed",
        "### Summary table",
    ),
}

STRUCTURE_FLAG = "structure_contract_blocked"
NUMERIC_FLAG = "numeric_consistency_blocked"
CATEGORY_FLAG = "category_consistency_blocked"
PORTFOLIO_CLAIM_FLAG = "portfolio_claim_blocked"
LIVE_GATE_WARNING_BY_FLAG = {
    STRUCTURE_FLAG: "live_structure_contract_dropped",
    NUMERIC_FLAG: "live_numeric_mismatch_dropped",
    CATEGORY_FLAG: "live_category_mismatch_dropped",
    PORTFOLIO_CLAIM_FLAG: "live_portfolio_claim_dropped",
    DISPLAY_TOKEN_BLOCKED_FLAG: "live_display_token_dropped",
}

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RE = re.compile(r"[+-]?\d+(?:,\d{3})*(?:\.\d+)?")
KEY_INT_RE = re.compile(r"\d+")
ASSERTION_CATEGORY_RE = re.compile(
    r"\b(freshness|availability)(?:\s+status)?\s+"
    r"(?:(?:is|was)(?:\s+(?:categorized|designated|marked|labeled)\s+as)?|"
    r"(?:categorized|designated|marked|labeled)\s+as)\s+"
    r"[\"'“]?([A-Za-z_]+(?:\s+[A-Za-z_]+)?)",
    re.IGNORECASE,
)
# T17A-F2 (T18 field finding): colon-form assertions ("freshness: manual")
# bypassed the connector regex and let a wrong category into a live table.
ASSERTION_COLON_CATEGORY_RE = re.compile(
    r"\b(freshness|availability)(?:\s+status)?\s*:\s*"
    r"[\"'“]?([A-Za-z_]+(?:\s+[A-Za-z_]+)?)",
    re.IGNORECASE,
)
PORTFOLIO_CONTEXT_TERMS = r"(?:portfolio|holdings|position|exposure|allocation|account|cash)"
PORTFOLIO_DIGIT_VALUE_TERMS = r"(?:\$|\d+(?:\.\d+)?\s?(?:%|percent|per\s+cent|dollars?)|(?:percent|per\s+cent|dollars?)\s+\d+(?:\.\d+)?)"
PORTFOLIO_CARDINAL_TERMS = (
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)"
)
# "this would roughly double your chip exposure" carries no cardinal, so
# digit/cardinal gates alone leave a portfolio-magnitude claim ungated. Keep
# this vocabulary scoped to portfolio-context windows, not broad prose.
PORTFOLIO_COMPARATIVE_MAGNITUDE_TERMS = r"(?:double|triple|halve|most|majority|bulk|dominant|concentrat\w*)"
PORTFOLIO_MAGNITUDE_TERMS = (
    rf"(?:{PORTFOLIO_DIGIT_VALUE_TERMS}|{PORTFOLIO_CARDINAL_TERMS}|{PORTFOLIO_COMPARATIVE_MAGNITUDE_TERMS})"
)
PORTFOLIO_WINDOW_RE = re.compile(
    rf"\b{PORTFOLIO_CONTEXT_TERMS}\b(?:\W+\w+){{0,8}}\W+\b{PORTFOLIO_MAGNITUDE_TERMS}\b|"
    rf"\b{PORTFOLIO_MAGNITUDE_TERMS}\b(?:\W+\w+){{0,8}}\W+\b{PORTFOLIO_CONTEXT_TERMS}\b",
    re.IGNORECASE,
)
# T18 field fix: the deterministic scope-caveat text that risk-role reports
# MUST restate contains "limited" ("scope is limited to ...") and "unknown"
# ("... scope membership unknown") as plain English, so those words cannot be
# bare-position trip tokens. Bare checking is kept only for words whose bare
# use in a report is itself a freshness claim; "unknown" joins the
# always-allowed ignorance/absence vocabulary (claiming ignorance is the
# fail-safe direction), and "limited"/"available" stay assertion-bound.
BARE_CATEGORY_TOKENS = frozenset({"fresh", "stale"})
ALWAYS_ALLOWED_BARE_GAP_TOKENS = frozenset({"not_reviewed", "not_available", "unknown"})


def freshness_category_from_label(label: str | None) -> str | None:
    """Map a freshness display label to its category token (shared with the
    deterministic layer so floor text and gate vocabulary can never drift)."""
    lowered = (label or "").lower()
    if "stale" in lowered:
        return "stale"
    if "unavailable" in lowered or "not available" in lowered:
        return "not_available"
    if "unknown" in lowered:
        return "unknown"
    if "manual" in lowered:
        return "manual"
    if "eod" in lowered:
        return "eod_only"
    if "delayed" in lowered:
        return "delayed"
    if "error" in lowered:
        return "error"
    if label:
        return "fresh"
    return None


def _gate_debug(message: str) -> None:
    """Terminal-only, default-off diagnostic. Prints single normalized tokens
    (our own enum words or one captured category/number token), never prose,
    never keys, never persisted anywhere."""
    if os.environ.get("POA_LIVE_GATE_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
        print(f"live_gate_debug {message}")


def validate_live_report_markdown(
    *,
    role_name: str,
    markdown: str,
    role_results: tuple[ToolResult, ...],
) -> str | None:
    """Return an eval flag when a live report should be dropped."""

    if _structure_contract_flag(role_name=role_name, markdown=markdown) is not None:
        return STRUCTURE_FLAG
    if _numeric_consistency_flag(markdown=markdown, role_results=role_results) is not None:
        return NUMERIC_FLAG
    if _category_consistency_flag(markdown=markdown, role_results=role_results) is not None:
        return CATEGORY_FLAG
    return None


def validate_live_report_structure(*, role_name: str, markdown: str) -> str | None:
    return _structure_contract_flag(role_name=role_name, markdown=markdown)


def validate_live_report_consistency(
    *,
    markdown: str,
    role_results: tuple[ToolResult, ...],
) -> str | None:
    if _numeric_consistency_flag(markdown=markdown, role_results=role_results) is not None:
        return NUMERIC_FLAG
    if _category_consistency_flag(markdown=markdown, role_results=role_results) is not None:
        return CATEGORY_FLAG
    if _portfolio_claim_flag(markdown=markdown) is not None:
        return PORTFOLIO_CLAIM_FLAG
    if find_internal_display_tokens(markdown):
        return DISPLAY_TOKEN_BLOCKED_FLAG
    return None


def prompt_fact_labels_for_tool_result(result: ToolResult) -> tuple[dict[str, str], ...]:
    """Project reviewed fact-label pairs for live prompts without raw payload passthrough."""

    rows: list[dict[str, str]] = []

    def add(fact_key: str, value: object) -> None:
        if value is None:
            return
        key = _safe_fact_key(fact_key)
        value_label = str(value).strip()
        if not key or not value_label:
            return
        rows.append({"fact_key": key, "value_label": value_label})

    add("availability_category", result.availability)
    add("freshness_category", _prompt_freshness_category(result.freshness))
    if result.as_of is not None:
        add("as_of_date", result.as_of.date().isoformat())

    payload = result.summary_payload
    if result.tool_name == "market_context_snapshot":
        add("market_context_as_of_date", payload.get("as_of_date"))
        add(
            "market_context_freshness_category",
            _prompt_freshness_category(payload.get("freshness_category")),
        )
        data_window = payload.get("data_window")
        if isinstance(data_window, dict):
            add("row_count_trading_days", data_window.get("row_count"))
            add("first_window_date", data_window.get("first_date"))
            add("last_window_date", data_window.get("last_date"))
        values = payload.get("values")
        if isinstance(values, dict):
            for key, value in values.items():
                add(_market_value_fact_key(str(key)), value)
        indicators = payload.get("indicators")
        if isinstance(indicators, dict):
            for key, value in indicators.items():
                add(_market_indicator_fact_key(str(key)), value)
        relationships = payload.get("relationships")
        if isinstance(relationships, dict):
            for key, value in relationships.items():
                add(_market_relationship_fact_key(str(key)), value)
        omitted = payload.get("omitted_indicators")
        if isinstance(omitted, (list, tuple)):
            for item in omitted:
                add("omitted_indicator_name", item)
    elif result.tool_name == "economic_awareness_context":
        for row in _as_dict_rows(payload.get("reviewed_release_metadata")):
            fact_key = str(row.get("fact_key") or "")
            if fact_key in {"release_name", "event_name", "release_date", "event_date"}:
                add(fact_key, row.get("value_label"))
    elif result.tool_name == "sec_recent_filings_metadata":
        for row in _as_dict_rows(payload.get("reviewed_filing_metadata")):
            fact_key = str(row.get("fact_key") or "")
            if fact_key in {"form_type", "filing_date"}:
                add(fact_key, row.get("value_label"))
    elif result.tool_name == "public_company_profile":
        for fact_key in _as_tuple(payload.get("fact_keys_present")):
            add("profile_fact_key_present", fact_key)
    elif result.tool_name.startswith("calc_"):
        for row in _as_dict_rows(payload.get("value_labels")):
            fact_key = row.get("fact_key")
            value_label = row.get("value_label")
            if isinstance(fact_key, str) and isinstance(value_label, str):
                add(fact_key, value_label)
        for index, as_of_label in enumerate(_as_tuple(payload.get("as_of_labels")), start=1):
            add(f"calculation_as_of_label_{index}", as_of_label)

    deduped = tuple(dict.fromkeys(tuple((row["fact_key"], row["value_label"]) for row in rows)))
    fact_labels = tuple(
        {"fact_key": key, "display_label": display_label_for_code(key), "value_label": value}
        for key, value in deduped
    )
    validate_tool_payload(
        {"fact_labels": fact_labels},
        label="live provider prompt fact labels",
        allow_p36_calculation_values=result.contract_version == P36_CALC_TOOL_CONTRACT_VERSION,
    )
    return fact_labels


def _structure_contract_flag(*, role_name: str, markdown: str) -> str | None:
    if role_name not in {"technical_analyst", "risk_management_agent"}:
        return STRUCTURE_FLAG
    cleaned = markdown.strip()
    if not cleaned:
        return STRUCTURE_FLAG
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if any(line.startswith("#") or line.startswith("|") or line.startswith(("-", "*")) for line in lines):
        return STRUCTURE_FLAG
    if SUMMARY_TABLE_HEADER in cleaned:
        return STRUCTURE_FLAG
    sentence_count = len(re.findall(r"[.!?](?:\s|$)", cleaned))
    if sentence_count < 1 or sentence_count > 4:
        return STRUCTURE_FLAG
    return None


def _portfolio_claim_flag(*, markdown: str) -> str | None:
    return PORTFOLIO_CLAIM_FLAG if PORTFOLIO_WINDOW_RE.search(markdown) else None


def _numeric_consistency_flag(*, markdown: str, role_results: tuple[ToolResult, ...]) -> str | None:
    allowed = _allowed_numbers(role_results)
    date_tokens = set(DATE_RE.findall(markdown))
    for token in date_tokens:
        if token not in allowed.date_strings:
            return NUMERIC_FLAG
    scrubbed = DATE_RE.sub(" ", markdown)
    for match in NUMBER_RE.finditer(scrubbed):
        token = match.group(0)
        if _numeric_token_allowed(token, allowed=allowed):
            continue
        _gate_debug(f"numeric token={token}")
        return NUMERIC_FLAG
    return None


def _category_consistency_flag(*, markdown: str, role_results: tuple[ToolResult, ...]) -> str | None:
    allowed = _allowed_categories(role_results)
    matches = chain(
        ((match, True) for match in ASSERTION_CATEGORY_RE.finditer(markdown)),
        ((match, False) for match in ASSERTION_COLON_CATEGORY_RE.finditer(markdown)),
    )
    for match, strict in matches:
        vocabulary = match.group(1).lower()
        category = _normalize_category_capture(match.group(2))
        if not category:
            if not strict:
                continue
            _gate_debug(f"category assertion unparsed vocabulary={vocabulary}")
            return CATEGORY_FLAG
        if category not in FRESHNESS_CATEGORY_VOCABULARY and category not in TOOL_AVAILABILITIES:
            if not strict:
                # Colon-form non-vocabulary captures are table item labels
                # ("... freshness | Market quote ..."), not assertions.
                continue
            _gate_debug(f"category assertion mismatch vocabulary={vocabulary} token={category}")
            return CATEGORY_FLAG
        if category in ALWAYS_ALLOWED_BARE_GAP_TOKENS:
            # Asserting absence is honest-gap wording, never a category
            # hallucination; the mandated gap vocabulary stays allowed here
            # exactly as it does in bare-token position.
            continue
        # Pick the membership set by the TOKEN's vocabulary class: the two
        # vocabularies are disjoint, and "X freshness: available" truthfully
        # describes the freshness item's availability, not a freshness
        # category (T18 field fix). The subject word only anchors the match.
        if category in FRESHNESS_CATEGORY_VOCABULARY:
            haystack = allowed.freshness
        elif category in TOOL_AVAILABILITIES:
            haystack = allowed.availability
        else:
            haystack = allowed.freshness if vocabulary == "freshness" else allowed.availability
        if category not in haystack:
            _gate_debug(f"category assertion mismatch vocabulary={vocabulary} token={category}")
            return CATEGORY_FLAG
    normalized_text = markdown.lower().replace("not available", "not_available").replace("not reviewed", "not_reviewed")
    for token in BARE_CATEGORY_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", normalized_text) and token not in allowed.all_categories:
            _gate_debug(f"category bare token={token}")
            return CATEGORY_FLAG
    return None


class _AllowedNumbers:
    def __init__(self) -> None:
        self.date_strings: set[str] = set()
        self.exact_strings: set[str] = set()
        self.decimals: set[Decimal] = set()
        self.structural_integers: set[str] = set()


class _AllowedCategories:
    def __init__(self) -> None:
        self.availability: set[str] = set()
        self.freshness: set[str] = set()

    @property
    def all_categories(self) -> set[str]:
        return set((*self.availability, *self.freshness, *ALWAYS_ALLOWED_BARE_GAP_TOKENS))


def _allowed_numbers(role_results: tuple[ToolResult, ...]) -> _AllowedNumbers:
    allowed = _AllowedNumbers()
    for result in role_results:
        for label in prompt_fact_labels_for_tool_result(result):
            fact_key = label["fact_key"]
            value_label = label["value_label"]
            allowed.structural_integers.update(KEY_INT_RE.findall(fact_key))
            allowed.structural_integers.update(KEY_INT_RE.findall(value_label))
            allowed.exact_strings.add(value_label)
            if DATE_RE.fullmatch(value_label):
                allowed.date_strings.add(value_label)
                continue
            decimal = _decimal_from_token(value_label)
            if decimal is not None:
                allowed.decimals.add(decimal)
    return allowed


def _allowed_categories(role_results: tuple[ToolResult, ...]) -> _AllowedCategories:
    allowed = _AllowedCategories()
    for result in role_results:
        availability = _normalize_category(result.availability)
        if availability in TOOL_AVAILABILITIES:
            allowed.availability.add(availability)
        freshness = _normalize_category(result.freshness) or freshness_category_from_label(result.freshness)
        if freshness:
            allowed.freshness.add(freshness)
        payload_freshness = _normalize_category(result.summary_payload.get("freshness_category"))
        if payload_freshness:
            allowed.freshness.add(payload_freshness)
        for label in prompt_fact_labels_for_tool_result(result):
            if label["fact_key"].endswith("freshness_category"):
                fact_freshness = _normalize_category(label["value_label"])
                if fact_freshness:
                    allowed.freshness.add(fact_freshness)
            if label["fact_key"].endswith("availability_category"):
                fact_availability = _normalize_category(label["value_label"])
                if fact_availability in TOOL_AVAILABILITIES:
                    allowed.availability.add(fact_availability)
    return allowed


def _numeric_token_allowed(token: str, *, allowed: _AllowedNumbers) -> bool:
    normalized = token.replace(",", "")
    if normalized in allowed.structural_integers or token in allowed.exact_strings or normalized in allowed.exact_strings:
        return True
    decimal = _decimal_from_token(token)
    if decimal is None:
        return False
    for allowed_decimal in allowed.decimals:
        if decimal == allowed_decimal:
            return True
        if decimal != 0 and allowed_decimal != 0 and (decimal < 0) != (allowed_decimal < 0):
            continue
        places = _decimal_places(normalized)
        quantum = Decimal("1").scaleb(-places)
        if allowed_decimal.quantize(quantum, rounding=ROUND_HALF_EVEN) == decimal:
            return True
    return False


def _decimal_from_token(token: object) -> Decimal | None:
    text = str(token).strip().replace(",", "")
    if not text or DATE_RE.fullmatch(text):
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _decimal_places(token: str) -> int:
    if "." not in token:
        return 0
    return max(0, len(token.split(".", 1)[1]))


def _normalize_category(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in TOOL_AVAILABILITIES or normalized in FRESHNESS_CATEGORY_VOCABULARY:
        return normalized
    return None


def _normalize_category_capture(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = _normalize_category_text(value)
    if normalized in TOOL_AVAILABILITIES or normalized in FRESHNESS_CATEGORY_VOCABULARY:
        return normalized
    first_word = value.strip().split(maxsplit=1)[0] if value.strip() else ""
    first_normalized = _normalize_category_text(first_word)
    if first_normalized:
        return first_normalized
    return None


def _normalize_category_text(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _prompt_freshness_category(value: object) -> str | None:
    """Keep live envelopes category-valued; render labels only in the document."""

    if value is None:
        return None
    text = str(value).strip()
    normalized = _normalize_category(text)
    if normalized in FRESHNESS_CATEGORY_VOCABULARY:
        return normalized
    return freshness_category_from_label(text)


def _market_value_fact_key(key: str) -> str:
    units = {
        "latest_close": "latest_close_usd",
        "prior_close": "prior_close_usd",
        "latest_volume": "latest_volume_count",
        "high_52_week": "high_52_week_usd",
        "low_52_week": "low_52_week_usd",
    }
    return units.get(key, key)


def _market_indicator_fact_key(key: str) -> str:
    if key in {"rsi14"}:
        return f"{key}_index"
    if key.startswith("macd") or key.startswith("bollinger") or key in {"sma50", "sma200", "ema10", "atr14"}:
        return f"{key}_usd"
    return key


def _market_relationship_fact_key(key: str) -> str:
    return key.replace("_percent", "_pct")


def _safe_fact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.strip().lower()).strip("_")


def _as_dict_rows(value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _as_tuple(value: object) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)
