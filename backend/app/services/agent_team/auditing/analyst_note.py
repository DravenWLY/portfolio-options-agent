"""K3 typed analyst-note parsing, fact-free checks, and offline diagnostics.

This module validates only model-authored note text. Backend composition remains
subject to the unchanged P36 markdown gates after a note is accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Iterable, Literal

from app.services.agent_team.auditing.v3_value_gates import (
    ADVICE_BOUNDARY_FLAG,
    _SPELLED_MAGNITUDE_RE,
    _advice_boundary_flag,
)
from app.services.agent_team.llm_clients.contracts import LLM_PROVIDER_STATUSES, find_secret_like_values


ANALYST_NOTE_STRUCTURE_FLAG = "analyst_note_structure_blocked"
ANALYST_NOTE_NO_FACTS_FLAG = "analyst_note_no_facts_blocked"

_REQUIRED_KEYS = frozenset({"observation", "why_it_matters", "what_to_verify"})
_NOTE_FAILURE_CODES = frozenset(
    {
        "note_unparseable",
        "note_field_empty",
        "note_clause_punctuation",
        "note_verify_form",
        "no_facts_number",
        "no_facts_date",
        "no_facts_identity",
        "no_facts_internal_token",
        "no_facts_markup",
        "no_facts_vocabulary",
        "advice_boundary",
        "length_below_window",
        "length_above_window",
    }
)
_DIAGNOSTIC_OUTCOME_CODES = _NOTE_FAILURE_CODES | frozenset({"accepted", "provider_unavailable", "note_incomplete_response"})
_ANALYST_ROLE_CODES = frozenset(
    {"risk_management_agent", "technical_analyst", "fundamentals_analyst", "news_analyst"}
)
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
_DOCUMENT_FATAL_VOCABULARY_RE = re.compile(
    r"\b(?:annualized|yield|support|resistance|entry\s+point|pivot|breakout|breakdown|"
    r"return\s+on\s+collateral)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AnalystNote:
    observation: tuple[str, ...]
    why_it_matters: tuple[str, ...]
    what_to_verify: tuple[str, ...]
    unrecognized_key_count: int = 0


@dataclass(frozen=True)
class AnalystNoteParseResult:
    note: AnalystNote | None
    failure_code: str | None


@dataclass(frozen=True)
class AnalystNoteDiagnostic:
    """Closed-code/integer-only offline replay metadata; never frozen or rendered."""

    role_name: str
    attempt_index: int
    outcome_code: str
    sub_rule_id: str | None
    field_item_counts: tuple[int, int, int]
    per_item_word_counts: tuple[int, ...]
    composed_projected_words: int | None
    window_low: int | None
    window_high: int | None
    unrecognized_key_count: int
    provider_status: str
    provider_finish_reason: Literal["none", "stop", "length", "unknown"]

    def as_dict(self) -> dict[str, object]:
        return {
            "role_name": self.role_name,
            "attempt_index": self.attempt_index,
            "outcome_code": self.outcome_code,
            "sub_rule_id": self.sub_rule_id,
            "field_item_counts": {
                "observation": self.field_item_counts[0],
                "why_it_matters": self.field_item_counts[1],
                "what_to_verify": self.field_item_counts[2],
            },
            "per_item_word_counts": self.per_item_word_counts,
            "composed_projected_words": self.composed_projected_words,
            "window_low": self.window_low,
            "window_high": self.window_high,
            "unrecognized_key_count": self.unrecognized_key_count,
            "provider_status": self.provider_status,
            "provider_finish_reason": self.provider_finish_reason,
        }


def parse_analyst_note_diagnostic(content: str) -> AnalystNoteParseResult:
    """Parse recognized fields only; unknown keys are counted then discarded."""

    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return AnalystNoteParseResult(None, "note_unparseable")
    if not isinstance(payload, dict):
        return AnalystNoteParseResult(None, "note_unparseable")
    if not _REQUIRED_KEYS <= set(payload):
        return AnalystNoteParseResult(None, "note_field_empty")
    values = tuple(payload[key] for key in ("observation", "why_it_matters", "what_to_verify"))
    if not all(isinstance(value, list) and value and all(isinstance(item, str) for item in value) for value in values):
        return AnalystNoteParseResult(None, "note_field_empty")
    observation, why_it_matters, what_to_verify = (tuple(value) for value in values)
    if any(not _is_clause(item) for item in (*observation, *why_it_matters)):
        return AnalystNoteParseResult(None, "note_clause_punctuation")
    if any(not _is_verification_sentence(item) for item in what_to_verify):
        return AnalystNoteParseResult(None, "note_verify_form")
    return AnalystNoteParseResult(
        AnalystNote(
            observation=observation,
            why_it_matters=why_it_matters,
            what_to_verify=what_to_verify,
            unrecognized_key_count=len(set(payload) - _REQUIRED_KEYS),
        ),
        None,
    )


def parse_analyst_note(content: str) -> AnalystNote | None:
    """Compatibility wrapper returning only an accepted note."""

    return parse_analyst_note_diagnostic(content).note


def validate_analyst_note_diagnostic(
    note: AnalystNote,
    *,
    supplied_labels: Iterable[str] = (),
    frozen_symbol: str | None = None,
) -> tuple[str | None, str | None]:
    """Return the external flag and closed recovery code for one model note."""

    del supplied_labels  # Label copying is intentionally no longer a drop rule.
    for field_name, items in (("observation", note.observation), ("why_it_matters", note.why_it_matters), ("what_to_verify", note.what_to_verify)):
        for item in items:
            if any(character.isdigit() for character in item) or _SPELLED_MAGNITUDE_RE.search(item):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_number"
            if _MONTH_OR_PERIOD_RE.search(item):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_date"
            if _SOURCE_OR_ID_RE.search(item) or _URL_OR_PATH_RE.search(item) or find_secret_like_values(item):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_internal_token"
            if _LOWERCASE_TICKER_RE.search(item) or _contains_frozen_symbol(item, frozen_symbol):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_identity"
            if _MARKDOWN_RE.search(item):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_markup"
            if _DOCUMENT_FATAL_VOCABULARY_RE.search(item):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_vocabulary"
            if field_name != "what_to_verify" and _has_noninitial_proper_noun(item):
                return ANALYST_NOTE_NO_FACTS_FLAG, "no_facts_identity"
            # F-4.6 attribution belongs to the backend-composed sentence; this
            # note-scoped check retains only the underlying advice boundary.
            if _advice_boundary_flag(f"Computed from the saved evidence, {item}") == ADVICE_BOUNDARY_FLAG:
                return ADVICE_BOUNDARY_FLAG, "advice_boundary"
    return None, None


def validate_analyst_note(
    note: AnalystNote,
    *,
    role_name: str | None = None,
    supplied_labels: Iterable[str] = (),
    frozen_symbol: str | None = None,
) -> str | None:
    """Return a note-scoped failure before backend markdown is composed."""

    del role_name
    return validate_analyst_note_diagnostic(
        note,
        supplied_labels=supplied_labels,
        frozen_symbol=frozen_symbol,
    )[0]


def build_analyst_note_diagnostic(
    *,
    role_name: str,
    attempt_index: int,
    outcome_code: str,
    sub_rule_id: str | None,
    note: AnalystNote | None,
    composed_projected_words: int | None,
    window: tuple[int, int] | None,
    provider_status: str,
    provider_finish_reason: object,
) -> AnalystNoteDiagnostic:
    """Build the contract's no-prose diagnostic record from sanitized shape data."""

    counts = (len(note.observation), len(note.why_it_matters), len(note.what_to_verify)) if note else (0, 0, 0)
    word_counts = tuple(_word_count(item) for item in (*note.observation, *note.why_it_matters, *note.what_to_verify)) if note else ()
    finish_reason: Literal["none", "stop", "length", "unknown"]
    if provider_finish_reason is None:
        finish_reason = "none"
    elif provider_finish_reason in {"stop", "length", "unknown"}:
        finish_reason = provider_finish_reason
    else:
        finish_reason = "unknown"
    return AnalystNoteDiagnostic(
        role_name=role_name if role_name in _ANALYST_ROLE_CODES else "unknown",
        attempt_index=attempt_index,
        outcome_code=outcome_code if outcome_code in _DIAGNOSTIC_OUTCOME_CODES else "note_unparseable",
        sub_rule_id=sub_rule_id if sub_rule_id in _NOTE_FAILURE_CODES else None,
        field_item_counts=counts,
        per_item_word_counts=word_counts,
        composed_projected_words=composed_projected_words,
        window_low=window[0] if window else None,
        window_high=window[1] if window else None,
        unrecognized_key_count=note.unrecognized_key_count if note else 0,
        provider_status=provider_status if provider_status in LLM_PROVIDER_STATUSES else "failed",
        provider_finish_reason=finish_reason,
    )


def replay_analyst_note_attempt(
    *,
    role_name: str,
    attempt_index: int,
    content: str,
    provider_status: str,
    provider_finish_reason: object,
    frozen_symbol: str | None = None,
) -> AnalystNoteDiagnostic:
    """Replay a synthetic/sanitized note shape without retaining its prose."""

    parsed = parse_analyst_note_diagnostic(content)
    if parsed.note is None:
        return build_analyst_note_diagnostic(
            role_name=role_name,
            attempt_index=attempt_index,
            outcome_code=parsed.failure_code or "note_unparseable",
            sub_rule_id=parsed.failure_code,
            note=None,
            composed_projected_words=None,
            window=None,
            provider_status=provider_status,
            provider_finish_reason=provider_finish_reason,
        )
    flag, sub_rule_id = validate_analyst_note_diagnostic(parsed.note, frozen_symbol=frozen_symbol)
    return build_analyst_note_diagnostic(
        role_name=role_name,
        attempt_index=attempt_index,
        outcome_code="accepted" if flag is None else sub_rule_id or "note_unparseable",
        sub_rule_id=sub_rule_id,
        note=parsed.note,
        composed_projected_words=None,
        window=None,
        provider_status=provider_status,
        provider_finish_reason=provider_finish_reason,
    )


def _word_count(value: str) -> int:
    return len(_WORD_RE.findall(value))


def _is_clause(value: str) -> bool:
    return bool(value.strip()) and not any(mark in value for mark in ".!?")


def _is_verification_sentence(value: str) -> bool:
    stripped = value.strip()
    marks = re.findall(r"[.!?]", stripped)
    return bool(stripped) and (not marks or (len(marks) == 1 and stripped.endswith((".", "!", "?"))))


def _has_noninitial_proper_noun(value: str) -> bool:
    tokens = re.findall(r"\b[A-Z][A-Za-z-]*\b", value)
    return bool(tokens and any(token != tokens[0] for token in tokens))


def _contains_frozen_symbol(value: str, frozen_symbol: str | None) -> bool:
    """Match only the exact uppercase frozen ticker, never its English homograph."""

    if not frozen_symbol or not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", frozen_symbol):
        return False
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(frozen_symbol)}(?![A-Za-z0-9])", value) is not None
