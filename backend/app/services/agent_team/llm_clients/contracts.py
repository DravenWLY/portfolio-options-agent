"""App-owned LLM provider contracts for the Phase 19A agent team.

This module defines a provider boundary only. It must not import live provider
SDKs, TradingAgents, broker adapters, or market-data providers.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
import re
from typing import Iterable, Literal, Protocol

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


AgentTeamRole = Literal[
    "fundamentals_analyst",
    "news_analyst",
    "technical_analyst",
    "risk_management_agent",
    "portfolio_manager_agent",
]
LLMProviderStatus = Literal[
    "ok",
    "skipped",
    "failed",
    "rate_limited",
    "quota_exceeded",
    "provider_timeout",
    "provider_auth_error",
    "provider_unavailable",
    "invalid_response",
    "safety_validation_failed",
]
LLMProviderFinishReason = Literal["length", "stop", "unknown"]
LLMMessageRole = Literal["system", "user", "assistant"]

AGENT_TEAM_ROLES: tuple[AgentTeamRole, ...] = (
    "fundamentals_analyst",
    "news_analyst",
    "technical_analyst",
    "risk_management_agent",
    "portfolio_manager_agent",
)
LLM_PROVIDER_STATUSES: tuple[LLMProviderStatus, ...] = (
    "ok",
    "skipped",
    "failed",
    "rate_limited",
    "quota_exceeded",
    "provider_timeout",
    "provider_auth_error",
    "provider_unavailable",
    "invalid_response",
    "safety_validation_failed",
)
LLM_PROVIDER_CONTRACT_VERSION = "llm-provider-contract-v1"
_P36_VALUE_BEARING_PROMPT_VERSIONS = frozenset({
    "p36-role-analysis-v1",
    "p36-pm-synthesis-v1",
})

# Registered by the tool-mediated orchestration module after it renders the
# approved static system prompts. Exact full-string membership is used only by
# segment-aware input validation; dynamic prompt content remains strict.
_STATIC_SYSTEM_PROMPT_REGISTRY: frozenset[str] = frozenset()
_REVIEWED_STATIC_SYSTEM_PROMPT_VERSIONS: dict[str, frozenset[str]] = {}
_STATIC_SYSTEM_PROMPT_PLAIN_TOPIC_TOKENS = frozenset({"cash", "holdings", "positions", "threshold"})


@dataclass(frozen=True)
class ReviewedStaticSystemPrompt:
    """One reviewed, static system prompt with an approved prompt version.

    The class intentionally carries no runtime configuration. Creating one is
    a code-and-review act that pins the exact rendered prompt text and version.
    """

    content: str
    prompt_version: str

LLM_PROVIDER_FORBIDDEN_KEYS = FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS | {
    "raw_holdings",
    "raw_positions",
    "broker_ids",
    "provider_ids",
    "private_strategy_settings",
    "account_specific_threshold",
    "account_specific_thresholds",
}
LLM_PROVIDER_FORBIDDEN_VALUE_TOKENS = frozenset(
    {
        "account_id",
        "broker_account_id",
        "provider_account_id",
        "provider_connection_id",
        "provider_contract_id",
        "account_value",
        "account_values",
        "cash",
        "cash_balance",
        "buying_power",
        "holdings",
        "positions",
        "raw_payload",
        "raw_metadata",
        "secret",
        "api_key",
        "access_token",
        "portal_url",
        "trade_journal",
        "threshold",
        "strategy_settings",
    }
)
PROHIBITED_LLM_OUTPUT_PHRASES = frozenset(
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
SECRET_LIKE_VALUE_PATTERNS = (
    re.compile(r"\b[Aa][Ii]za[0-9A-Za-z_\-]{20,}\b"),
    re.compile(r"\bsk-[0-9A-Za-z_\-]{16,}\b"),
    re.compile(r"\b(?:api|access|secret)[_-]?key\s*[:=]\s*[0-9A-Za-z_\-]{8,}\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class LLMProviderMessage:
    """Single safe prompt/response message for provider calls."""

    role: LLMMessageRole
    content: str

    def __post_init__(self) -> None:
        if self.role not in ("system", "user", "assistant"):
            raise ValueError(f"unsupported message role: {self.role}")
        if not self.content.strip():
            raise ValueError("message content must not be empty")
        validate_llm_provider_payload(asdict(self), label="LLM provider message")


@dataclass(frozen=True)
class LLMProviderRequest:
    """Provider request shape owned by Portfolio Copilot."""

    request_id: str
    role_name: AgentTeamRole
    messages: tuple[LLMProviderMessage, ...]
    provider: str = "mock"
    model: str = "mock-agent-team-v1"
    prompt_version: str = "agent-team-prompt-v1"
    max_tokens: int = 800
    timeout_seconds: int = 30
    temperature: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = LLM_PROVIDER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if self.role_name not in AGENT_TEAM_ROLES:
            raise ValueError(f"unsupported agent-team role: {self.role_name}")
        if not self.messages:
            raise ValueError("messages must not be empty")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        validate_llm_provider_payload(asdict(self), label="LLM provider request")


@dataclass(frozen=True)
class LLMProviderResponse:
    """Provider response shape safe for agent-step persistence and frontend summaries."""

    request_id: str
    role_name: AgentTeamRole
    status: LLMProviderStatus
    provider: str
    model: str
    prompt_version: str
    content_markdown: str | None
    is_mock: bool
    finish_reason: LLMProviderFinishReason | None = None
    generated_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    estimated_cost: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = LLM_PROVIDER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if self.role_name not in AGENT_TEAM_ROLES:
            raise ValueError(f"unsupported agent-team role: {self.role_name}")
        if self.status not in LLM_PROVIDER_STATUSES:
            raise ValueError(f"unsupported provider status: {self.status}")
        if self.finish_reason not in (None, "length", "stop", "unknown"):
            raise ValueError(f"unsupported provider finish reason: {self.finish_reason}")
        if self.status == "ok" and not (self.content_markdown or "").strip():
            raise ValueError("ok provider responses must include content_markdown")
        from app.services.agent_team.safety.output_safety import validate_llm_provider_output

        validate_llm_provider_output(
            asdict(self),
            label="LLM provider response",
            allow_value_bearing_markdown=self.prompt_version in _P36_VALUE_BEARING_PROMPT_VERSIONS,
        )


class LLMProvider(Protocol):
    """Provider boundary for app-owned agent-team calls."""

    provider_name: str
    model: str

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        """Return a provider response without exposing private brokerage data."""


def validate_llm_provider_payload(payload: object, *, label: str) -> None:
    """Reject private data keys/values and prohibited advice/execution phrases."""

    forbidden = find_forbidden_keys(payload, forbidden_keys=LLM_PROVIDER_FORBIDDEN_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{label} contains forbidden private fields: {blocked}")
    private_values = _find_forbidden_string_values_segmentwise(payload)
    if private_values:
        blocked = ", ".join(sorted(private_values))
        raise ValueError(f"{label} contains forbidden private value token(s): {blocked}")
    secret_values = find_secret_like_values(payload)
    if secret_values:
        blocked = ", ".join(sorted(secret_values))
        raise ValueError(f"{label} contains secret-like value pattern(s): {blocked}")
    prohibited_phrases = _find_prohibited_llm_phrases_segmentwise(payload)
    if prohibited_phrases:
        blocked = ", ".join(sorted(prohibited_phrases))
        raise ValueError(f"{label} contains prohibited advice/execution phrase(s): {blocked}")


def _find_prohibited_llm_phrases_segmentwise(value: object, *, prefix: str = "") -> set[str]:
    """Apply phrase scanning per message, narrowly exempting reviewed static text.

    Only a system-role message whose content exactly matches a reviewed static
    registry entry skips this one scan. All other message segments, nested
    dynamic values, and every non-phrase validator remain strict.
    """

    if isinstance(value, dict):
        messages = value.get("messages")
        if isinstance(messages, (list, tuple)):
            found = find_prohibited_llm_phrases(
                {key: item for key, item in value.items() if key != "messages"},
                prefix=prefix,
            )
            prompt_version = value.get("prompt_version")
            for index, message in enumerate(messages):
                message_prefix = f"{prefix}.messages[{index}]" if prefix else f"messages[{index}]"
                found.update(
                    _find_prohibited_llm_phrases_message(
                        message,
                        prefix=message_prefix,
                        prompt_version=prompt_version if isinstance(prompt_version, str) else None,
                    )
                )
            return found
        if "role" in value and "content" in value:
            return _find_prohibited_llm_phrases_message(value, prefix=prefix, prompt_version=None)
    return find_prohibited_llm_phrases(value, prefix=prefix)


def _find_forbidden_string_values_segmentwise(value: object, *, prefix: str = "") -> set[str]:
    """Retain private-token scans on static prompts except plain topic words.

    Reviewed system prompts teach ordinary Risk vocabulary such as ``cash``.
    That is not a private identifier. Compound/private tokens, keys, secrets,
    and every non-system or dynamically assembled segment remain strict.
    """

    if isinstance(value, dict):
        messages = value.get("messages")
        if isinstance(messages, (list, tuple)):
            found = find_forbidden_string_values(
                {key: item for key, item in value.items() if key != "messages"},
                prefix=prefix,
            )
            prompt_version = value.get("prompt_version")
            for index, message in enumerate(messages):
                message_prefix = f"{prefix}.messages[{index}]" if prefix else f"messages[{index}]"
                found.update(
                    _find_forbidden_string_values_message(
                        message,
                        prefix=message_prefix,
                        prompt_version=prompt_version if isinstance(prompt_version, str) else None,
                    )
                )
            return found
        if "role" in value and "content" in value:
            return _find_forbidden_string_values_message(value, prefix=prefix, prompt_version=None)
    return find_forbidden_string_values(value, prefix=prefix)


def _find_forbidden_string_values_message(
    message: object,
    *,
    prefix: str,
    prompt_version: str | None,
) -> set[str]:
    if not isinstance(message, dict):
        return find_forbidden_string_values(message, prefix=prefix)
    role = message.get("role")
    content = message.get("content")
    if _is_registered_static_system_segment(role=role, content=content):
        found = find_forbidden_string_values(
            {key: item for key, item in message.items() if key != "content"},
            prefix=prefix,
        )
        found.update(
            find_forbidden_string_values(
                content,
                prefix=f"{prefix}.content" if prefix else "content",
                ignored_plain_tokens=_STATIC_SYSTEM_PROMPT_PLAIN_TOPIC_TOKENS,
            )
        )
        return found
    return find_forbidden_string_values(message, prefix=prefix)


def _find_prohibited_llm_phrases_message(
    message: object,
    *,
    prefix: str,
    prompt_version: str | None,
) -> set[str]:
    if not isinstance(message, dict):
        return find_prohibited_llm_phrases(message, prefix=prefix)
    role = message.get("role")
    content = message.get("content")
    if _is_reviewed_static_system_segment(role=role, content=content, prompt_version=prompt_version):
        return find_prohibited_llm_phrases({key: item for key, item in message.items() if key != "content"}, prefix=prefix)
    return find_prohibited_llm_phrases(message, prefix=prefix)


def _is_reviewed_static_system_segment(*, role: object, content: object, prompt_version: str | None) -> bool:
    if role != "system" or not isinstance(content, str):
        return False
    approved_versions = _REVIEWED_STATIC_SYSTEM_PROMPT_VERSIONS.get(content)
    if not approved_versions:
        return False
    return prompt_version is None or prompt_version in approved_versions


def _is_registered_static_system_segment(*, role: object, content: object) -> bool:
    return role == "system" and isinstance(content, str) and content in _STATIC_SYSTEM_PROMPT_REGISTRY


def find_forbidden_string_values(
    value: object,
    *,
    prefix: str = "",
    ignored_plain_tokens: frozenset[str] = frozenset(),
) -> set[str]:
    """Return recursive string paths that include private-data token values.

    ``ignored_plain_tokens`` is intentionally opt-in for a narrow output-side
    prose audit. Input and envelope validation retain the full token list.
    """

    if isinstance(value, str):
        value_lower = value.strip().lower()
        if any(
            token in value_lower
            for token in LLM_PROVIDER_FORBIDDEN_VALUE_TOKENS
            if token not in ignored_plain_tokens
        ):
            return {prefix or "<value>"}
        return set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(
                find_forbidden_string_values(
                    key_text,
                    prefix=key_path,
                    ignored_plain_tokens=ignored_plain_tokens,
                )
            )
            found.update(
                find_forbidden_string_values(
                    item,
                    prefix=key_path,
                    ignored_plain_tokens=ignored_plain_tokens,
                )
            )
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(
                find_forbidden_string_values(
                    item,
                    prefix=item_path,
                    ignored_plain_tokens=ignored_plain_tokens,
                )
            )
        return found
    return set()


def find_prohibited_llm_phrases(value: object, *, prefix: str = "") -> set[str]:
    """Return recursive string paths that contain prohibited output phrasing."""

    if isinstance(value, str):
        value_lower = value.strip().lower()
        if any(phrase in value_lower for phrase in PROHIBITED_LLM_OUTPUT_PHRASES):
            return {prefix or "<value>"}
        return set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(find_prohibited_llm_phrases(item, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(find_prohibited_llm_phrases(item, prefix=item_path))
        return found
    return set()


def find_secret_like_values(value: object, *, prefix: str = "") -> set[str]:
    """Return recursive string paths containing secret/API-token-like values."""

    if isinstance(value, str):
        if any(pattern.search(value) for pattern in SECRET_LIKE_VALUE_PATTERNS):
            return {prefix or "<value>"}
        return set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(find_secret_like_values(item, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(find_secret_like_values(item, prefix=item_path))
        return found
    return set()


def register_static_system_prompts(
    prompts: Iterable[str | ReviewedStaticSystemPrompt],
) -> frozenset[str]:
    """Register approved, exact static system prompts for input token scanning.

    The registry is intentionally append-only and matches full strings only.
    Plain string registrations remain subject to every scan. A
    ``ReviewedStaticSystemPrompt`` pins an exact approved prompt/version pair
    and is exempt only from the prohibited-phrase scan when later used as a
    system-message segment. All other validators remain in force.
    """

    entries = tuple(prompts)
    rendered = frozenset(
        entry.content if isinstance(entry, ReviewedStaticSystemPrompt) else entry
        for entry in entries
    )
    if not rendered or any(not prompt.strip() for prompt in rendered):
        raise ValueError("static system prompt registry requires non-empty prompts")
    for entry in entries:
        prompt = entry.content if isinstance(entry, ReviewedStaticSystemPrompt) else entry
        if not isinstance(prompt, str):
            raise ValueError("static system prompt registry requires string content")
        secret_values = find_secret_like_values(prompt)
        if secret_values:
            raise ValueError("static system prompt contains secret-like value")
        private_values = find_forbidden_string_values(
            prompt,
            ignored_plain_tokens=_STATIC_SYSTEM_PROMPT_PLAIN_TOPIC_TOKENS,
        )
        if private_values:
            raise ValueError("static system prompt contains forbidden private value token")
        if not isinstance(entry, ReviewedStaticSystemPrompt):
            prohibited_phrases = find_prohibited_llm_phrases(prompt)
            if prohibited_phrases:
                raise ValueError("static system prompt contains prohibited advice/execution phrase")
        elif not entry.prompt_version.strip():
            raise ValueError("reviewed static system prompt requires prompt_version")

    global _STATIC_SYSTEM_PROMPT_REGISTRY, _REVIEWED_STATIC_SYSTEM_PROMPT_VERSIONS
    _STATIC_SYSTEM_PROMPT_REGISTRY = frozenset((*_STATIC_SYSTEM_PROMPT_REGISTRY, *rendered))
    reviewed_versions = dict(_REVIEWED_STATIC_SYSTEM_PROMPT_VERSIONS)
    for entry in entries:
        if isinstance(entry, ReviewedStaticSystemPrompt):
            reviewed_versions[entry.content] = frozenset(
                (*reviewed_versions.get(entry.content, ()), entry.prompt_version)
            )
    _REVIEWED_STATIC_SYSTEM_PROMPT_VERSIONS = reviewed_versions
    return _STATIC_SYSTEM_PROMPT_REGISTRY


def registered_static_system_prompts() -> frozenset[str]:
    """Return the exact prompt strings approved for the static input exception."""

    return _STATIC_SYSTEM_PROMPT_REGISTRY
