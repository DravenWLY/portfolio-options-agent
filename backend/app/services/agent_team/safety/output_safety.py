"""Generated-output safety validation for real-provider-capable LLM responses."""

from __future__ import annotations

import re

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


PROHIBITED_OUTPUT_PHRASES = frozenset(
    {
        "you should buy",
        "you should sell",
        "safe to trade",
        "ready to trade",
        "guaranteed return",
        "place an order",
        "place order",
        "submit an order",
        "submit order",
        "execute the trade",
        "execute trade",
        "order instruction",
    }
)

PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b(account|broker|provider)_(account_)?id\b", re.IGNORECASE),
    re.compile(r"\bprovider_(connection|contract|authorization)_id\b", re.IGNORECASE),
    re.compile(r"\b(raw_payload|raw_metadata|secret_ref|portal_url|access_token|api_key)\b", re.IGNORECASE),
    re.compile(r"\b[Aa][Ii]za[0-9A-Za-z_\-]{20,}\b"),
    re.compile(r"\bsk-[0-9A-Za-z_\-]{16,}\b"),
)

GENERATED_METRIC_PATTERNS = (
    re.compile(r"(?<![A-Za-z])\$[0-9][0-9,]*(?:\.[0-9]+)?"),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s?%"),
    re.compile(r"\bprice target\b", re.IGNORECASE),
    re.compile(r"\b(probability|odds|chance)\s+(?:of|is|are)\b", re.IGNORECASE),
    re.compile(r"\b(?:roi|yield|breakeven|break-even)\b", re.IGNORECASE),
    re.compile(r"\b(?:delta|gamma|theta|vega|rho)\s*[:=]?\s*-?[0-9]", re.IGNORECASE),
    re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s*(?:shares?|contracts?)\b", re.IGNORECASE),
)


def validate_llm_provider_output(
    payload: object,
    *,
    label: str,
    allow_value_bearing_markdown: bool = False,
) -> None:
    """Reject private data, advice/execution wording, and generated metric claims."""

    forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{label} contains forbidden private fields: {blocked}")
    private_values = _find_pattern_matches(payload, patterns=PRIVATE_VALUE_PATTERNS)
    if private_values:
        blocked = ", ".join(sorted(private_values))
        raise ValueError(f"{label} contains private identifier or secret-like value(s): {blocked}")
    prohibited = _find_phrase_matches(payload, phrases=PROHIBITED_OUTPUT_PHRASES)
    if prohibited:
        blocked = ", ".join(sorted(prohibited))
        raise ValueError(f"{label} contains prohibited advice/execution phrase(s): {blocked}")
    metric_payload = _without_value_bearing_markdown(payload) if allow_value_bearing_markdown else payload
    generated_metrics = _find_pattern_matches(metric_payload, patterns=GENERATED_METRIC_PATTERNS)
    if generated_metrics:
        blocked = ", ".join(sorted(generated_metrics))
        raise ValueError(f"{label} contains generated financial metric pattern(s): {blocked}")


def _without_value_bearing_markdown(value: object) -> object:
    """Exclude only P36-gated prose from the legacy generated-metric scan.

    P36 role text is immediately subject to F-5 provenance and the remaining
    v3 gate stack. Private identifiers, secrets, and advice are still scanned
    above over the complete payload. Legacy outputs do not call this helper.
    """

    if isinstance(value, dict):
        return {
            str(key): "" if str(key) in {"content_markdown", "live_report_markdown"} else _without_value_bearing_markdown(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return tuple(_without_value_bearing_markdown(item) for item in value)
    return value


def _find_phrase_matches(value: object, *, phrases: frozenset[str], prefix: str = "") -> set[str]:
    if isinstance(value, str):
        value_lower = value.strip().lower()
        if any(phrase in value_lower for phrase in phrases):
            return {prefix or "<value>"}
        return set()
    return _find_nested_matches(value, prefix=prefix, matcher=lambda item: _find_phrase_matches(item, phrases=phrases))


def _find_pattern_matches(value: object, *, patterns: tuple[re.Pattern[str], ...], prefix: str = "") -> set[str]:
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in patterns):
            return {prefix or "<value>"}
        return set()
    return _find_nested_matches(value, prefix=prefix, matcher=lambda item: _find_pattern_matches(item, patterns=patterns))


def _find_nested_matches(value: object, *, prefix: str, matcher) -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(matcher(key_text))
            found.update(_with_prefix(matcher(item), key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(_with_prefix(matcher(item), item_path))
        return found
    return set()


def _with_prefix(paths: set[str], prefix: str) -> set[str]:
    if not paths:
        return set()
    return {prefix if path == "<value>" else path for path in paths}
