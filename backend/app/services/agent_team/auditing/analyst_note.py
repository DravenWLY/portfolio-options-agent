"""K3 typed analyst-note parsing and note-scoped no-facts checks.

This module intentionally sits in front of the established P36 markdown gates.
It validates only model-authored note text; backend composition remains subject
to the unchanged existing gates.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Iterable

from app.services.agent_team.auditing.v3_value_gates import (
    ADVICE_BOUNDARY_FLAG,
    P36_PM_VERIFICATION_IMPERATIVES,
    _SPELLED_MAGNITUDE_RE,
    _advice_boundary_flag,
)
from app.services.agent_team.llm_clients.contracts import find_secret_like_values


ANALYST_NOTE_STRUCTURE_FLAG = "analyst_note_structure_blocked"
ANALYST_NOTE_NO_FACTS_FLAG = "analyst_note_no_facts_blocked"

_REQUIRED_KEYS = frozenset({"observation", "why_it_matters", "what_to_verify"})
_ROLE_ITEM_MAX_WORDS = {
    "risk_management_agent": 27,
    "technical_analyst": 22,
    "fundamentals_analyst": 22,
    "news_analyst": 22,
}
_MONTH_OR_PERIOD_RE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|q[1-4]|fy\s*\d{0,4}|fiscal\s+(?:year|quarter))\b",
    re.IGNORECASE,
)
_SOURCE_OR_ID_RE = re.compile(
    r"\b(?:sec|edgar|fred|fmp|nasdaq|nyse|form\s+[a-z0-9-]+|filref_[a-z0-9_]+|"
    r"[a-z][a-z0-9]*_[a-z0-9_]+|[a-z_]+(?:_snapshot|_summary|_calendar))\b",
    re.IGNORECASE,
)

_LOWERCASE_TICKER_RE = re.compile(
    r"\b(?:aapl|amzn|amd|avgo|brk[ab]|googl?|meta|msft|nvda|qqq|smh|soxx|spy|tsla|vti|voo|xle|xlk)\b",
    re.IGNORECASE,
)
_URL_OR_PATH_RE = re.compile(r"(?:https?://|www\.|(?:^|\s)/(?:[\w.-]+/)+[\w.-]+)", re.IGNORECASE)
_MARKDOWN_RE = re.compile(r"(?:^|\s)(?:#{1,6}\s|[-*+]\s|```|\|)")
_WORD_RE = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)?")
_INTERPRETATION_TERMS_RE = re.compile(
    r"\b(?:trend|drawdown|concentration|elevated|compressed|conventional|"
    r"overbought|oversold|uptrend|downtrend|leverage)\b",
    re.IGNORECASE,
)
_CATEGORY_LABEL_TOKENS = frozenset(
    {
        "available",
        "unavailable",
        "limited",
        "not available",
        "not reviewed",
        "fresh",
        "stale",
        "cached",
        "delayed",
        "unknown",
        "manual",
        "status",
        "freshness",
        "availability",
    }
)


@dataclass(frozen=True)
class AnalystNote:
    observation: tuple[str, ...]
    why_it_matters: tuple[str, ...]
    what_to_verify: tuple[str, ...]


def parse_analyst_note(content: str) -> AnalystNote | None:
    """Parse the exact three-key K3 JSON object, without coercion."""

    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or set(payload) != _REQUIRED_KEYS:
        return None
    values = tuple(payload[key] for key in ("observation", "why_it_matters", "what_to_verify"))
    if not all(isinstance(value, list) and all(isinstance(item, str) for item in value) for value in values):
        return None
    observation, why_it_matters, what_to_verify = (tuple(value) for value in values)
    if not 4 <= len(observation) <= 5 or not 2 <= len(why_it_matters) <= 3 or not 2 <= len(what_to_verify) <= 4:
        return None
    if not all(15 <= _word_count(item) <= 40 and _is_lowercase_clause(item) for item in (*observation, *why_it_matters)):
        return None
    if not all(8 <= _word_count(item) <= 28 and _is_verification_sentence(item) for item in what_to_verify):
        return None
    return AnalystNote(observation=observation, why_it_matters=why_it_matters, what_to_verify=what_to_verify)


def validate_analyst_note(
    note: AnalystNote,
    *,
    role_name: str | None = None,
    supplied_labels: Iterable[str] = (),
    frozen_symbol: str | None = None,
) -> str | None:
    """Return a note-scoped failure before any backend markdown is composed."""

    if role_name is not None:
        maximum = _ROLE_ITEM_MAX_WORDS.get(role_name)
        if maximum is None:
            return ANALYST_NOTE_STRUCTURE_FLAG
        if any(_word_count(item) > maximum for item in (*note.observation, *note.why_it_matters, *note.what_to_verify)):
            return ANALYST_NOTE_STRUCTURE_FLAG

    for item in (*note.observation, *note.why_it_matters, *note.what_to_verify):
        if any(character.isdigit() for character in item) or _SPELLED_MAGNITUDE_RE.search(item):
            return ANALYST_NOTE_NO_FACTS_FLAG
        if (
            _MONTH_OR_PERIOD_RE.search(item)
            or _SOURCE_OR_ID_RE.search(item)
            or _URL_OR_PATH_RE.search(item)
            or _LOWERCASE_TICKER_RE.search(item)
            or _MARKDOWN_RE.search(item)
            or find_secret_like_values(item)
        ):
            return ANALYST_NOTE_NO_FACTS_FLAG
        if (
            _contains_frozen_symbol(item, frozen_symbol)
            or _has_noninitial_proper_noun(item)
            or _copies_supplied_label(item, supplied_labels)
        ):
            return ANALYST_NOTE_NO_FACTS_FLAG
        if _advice_boundary_flag(item) is not None:
            return ADVICE_BOUNDARY_FLAG
    if any(_INTERPRETATION_TERMS_RE.search(item) for item in note.what_to_verify):
        return ANALYST_NOTE_NO_FACTS_FLAG
    return None


def _word_count(value: str) -> int:
    return len(_WORD_RE.findall(value))


def _is_lowercase_clause(value: str) -> bool:
    return bool(value) and value == value.lower() and not value.rstrip().endswith((".", "!", "?"))


def _is_verification_sentence(value: str) -> bool:
    words = _WORD_RE.findall(value.lower())
    stripped = value.strip()
    return (
        bool(words)
        and words[0] in P36_PM_VERIFICATION_IMPERATIVES
        and stripped.endswith((".", "!", "?"))
        and len(re.findall(r"[.!?]", stripped)) == 1
    )


def _has_noninitial_proper_noun(value: str) -> bool:
    tokens = re.findall(r"\b[A-Z][A-Za-z-]*\b", value)
    return bool(tokens and any(token != tokens[0] for token in tokens))


def _copies_supplied_label(value: str, labels: Iterable[str]) -> bool:
    value_tokens = tuple(re.findall(r"[a-z0-9]+", value.lower()))
    for label in labels:
        if label.strip().lower() in _CATEGORY_LABEL_TOKENS:
            continue
        label_tokens = tuple(re.findall(r"[a-z0-9]+", label.lower()))
        if len(label_tokens) == 1 and re.fullmatch(r"[a-z]{1,5}", label_tokens[0]):
            if _contains_token_phrase(value_tokens, label_tokens):
                return True
            continue
        if len(label_tokens) < 2 and len("".join(label_tokens)) < 12:
            continue
        if _contains_token_phrase(value_tokens, label_tokens):
            return True
    return False


def _contains_frozen_symbol(value: str, frozen_symbol: str | None) -> bool:
    """Match only the exact uppercase frozen ticker, never its English homograph."""

    if not frozen_symbol or not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", frozen_symbol):
        return False
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(frozen_symbol)}(?![A-Za-z0-9])", value) is not None


def _contains_token_phrase(haystack: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    return any(haystack[index : index + len(needle)] == needle for index in range(len(haystack) - len(needle) + 1))
