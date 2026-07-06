"""P34A-T10A ordered model-candidate chain tests (offline, fake providers only).

Covers: POA_LLM_MODEL_CANDIDATES parsing, ChainedLLMProvider advance/abort
semantics, sticky forward-only index, all-exhausted degradation, resolver
wiring, and chain-metadata leak safety. No live calls, no SDK imports, no
process env, no keys.
"""

from dataclasses import asdict

import pytest

from app.services.agent_team.llm_clients.contracts import (
    LLMProviderMessage,
    LLMProviderRequest,
    LLMProviderResponse,
    find_forbidden_string_values,
    find_secret_like_values,
)
from app.services.agent_team.llm_clients.config import (
    LLMProviderConfig,
    LLMProviderConfigurationError,
    LLMProviderSecrets,
    load_llm_provider_config,
)
from app.services.agent_team.llm_clients.factory import (
    CHAIN_ADVANCE_STATUSES,
    ChainedLLMProvider,
    resolve_llm_provider,
)


class _ScriptedProvider:
    """Fake per-model provider returning a scripted status sequence."""

    def __init__(self, *, model: str, statuses: tuple[str, ...], provider_name: str = "google") -> None:
        self.provider_name = provider_name
        self.model = model
        self._statuses = list(statuses)
        self.calls = 0

    def complete(self, request: LLMProviderRequest) -> LLMProviderResponse:
        self.calls += 1
        status = self._statuses.pop(0) if self._statuses else "ok"
        return LLMProviderResponse(
            request_id=request.request_id,
            role_name=request.role_name,
            status=status,  # type: ignore[arg-type]
            provider=self.provider_name,
            model=self.model,
            prompt_version=request.prompt_version,
            content_markdown=(
                "Scripted qualitative background context sentence for review." if status == "ok" else None
            ),
            is_mock=False,
            error_code=None if status == "ok" else status,
            error_message=None if status == "ok" else "safe scripted failure",
        )


def _request(role_name: str = "risk_management_agent") -> LLMProviderRequest:
    return LLMProviderRequest(
        request_id=f"chain_test_{role_name}",
        role_name=role_name,  # type: ignore[arg-type]
        messages=(LLMProviderMessage(role="user", content="safe synthetic chain-test message"),),
        provider="google",
        model="chain-under-test",
        prompt_version="p34a-tool-mediated-role-v2",
    )


def test_candidates_env_parsing_trims_dedupes_caps_and_overrides_model() -> None:
    config = load_llm_provider_config(
        {
            "POA_LLM_MODE": "live",
            "POA_LLM_PROVIDER": "google",
            "POA_LLM_MODEL": "single-model-ignored",
            "POA_LLM_MODEL_CANDIDATES": " model-a , model-b ,model-a,, model-c ",
            "GOOGLE_API_KEY": "configured",
        }
    )
    assert config.model_candidates == ("model-a", "model-b", "model-c")
    assert config.model == "model-a"
    snapshot = config.public_snapshot()
    assert snapshot["model_candidates"] == ["model-a", "model-b", "model-c"]
    assert "api_key" not in repr(snapshot).lower()


def test_candidates_env_parsing_rejects_more_than_four() -> None:
    with pytest.raises(LLMProviderConfigurationError):
        load_llm_provider_config(
            {
                "POA_LLM_MODE": "live",
                "POA_LLM_PROVIDER": "google",
                "POA_LLM_MODEL_CANDIDATES": "m1,m2,m3,m4,m5",
                "GOOGLE_API_KEY": "configured",
            }
        )


def test_candidates_are_ignored_in_mock_mode_and_single_model_behavior_is_unchanged() -> None:
    config = load_llm_provider_config({"POA_LLM_MODEL_CANDIDATES": "m1,m2"})
    assert config.mode == "mock"
    assert config.model_candidates == ()
    assert config.model == "mock-agent-team-v1"

    live_single = load_llm_provider_config(
        {
            "POA_LLM_MODE": "live",
            "POA_LLM_PROVIDER": "google",
            "POA_LLM_MODEL": "single-live-model",
            "GOOGLE_API_KEY": "configured",
        }
    )
    assert live_single.model_candidates == ()
    assert live_single.model == "single-live-model"


def test_config_constructor_rejects_duplicates_mock_candidates_and_model_mismatch() -> None:
    with pytest.raises(LLMProviderConfigurationError):
        LLMProviderConfig(
            mode="live",
            provider="google",
            model="m1",
            model_candidates=("m1", "m1"),
            google_credential_available=True,
        )
    with pytest.raises(LLMProviderConfigurationError):
        LLMProviderConfig(mode="mock", provider="mock", model_candidates=("m1",))
    with pytest.raises(LLMProviderConfigurationError):
        LLMProviderConfig(
            mode="live",
            provider="google",
            model="not-first",
            model_candidates=("m1", "m2"),
            google_credential_available=True,
        )


def test_chain_advances_on_quota_exceeded_and_freezes_attempt_metadata() -> None:
    first = _ScriptedProvider(model="chain-a", statuses=("quota_exceeded",))
    second = _ScriptedProvider(model="chain-b", statuses=("ok",))
    chain = ChainedLLMProvider(providers=(first, second))

    response = chain.complete(_request())

    assert response.status == "ok"
    assert response.model == "chain-b"
    assert response.metadata["model_chain_position"] == "1"
    assert response.metadata["attempted_models"] == "chain-a,chain-b"
    assert (first.calls, second.calls) == (1, 1)


@pytest.mark.parametrize("status", sorted(CHAIN_ADVANCE_STATUSES))
def test_chain_advances_on_every_availability_status(status: str) -> None:
    first = _ScriptedProvider(model="chain-a", statuses=(status,))
    second = _ScriptedProvider(model="chain-b", statuses=("ok",))
    chain = ChainedLLMProvider(providers=(first, second))

    response = chain.complete(_request())

    assert response.status == "ok"
    assert response.model == "chain-b"
    assert second.calls == 1


def test_chain_sticky_forward_index_skips_exhausted_models_for_later_roles() -> None:
    first = _ScriptedProvider(model="chain-a", statuses=("quota_exceeded",))
    second = _ScriptedProvider(model="chain-b", statuses=("ok", "ok"))
    chain = ChainedLLMProvider(providers=(first, second))

    chain.complete(_request("fundamentals_analyst"))
    second_response = chain.complete(_request("technical_analyst"))

    assert first.calls == 1, "exhausted model must not be retried by later roles"
    assert second.calls == 2
    assert second_response.metadata["model_chain_position"] == "1"
    assert second_response.metadata["attempted_models"] == "chain-b"
    assert chain.model == "chain-b"


def test_chain_aborts_on_auth_error_without_trying_next_model() -> None:
    first = _ScriptedProvider(model="chain-a", statuses=("provider_auth_error",))
    second = _ScriptedProvider(model="chain-b", statuses=("ok",))
    chain = ChainedLLMProvider(providers=(first, second))

    response = chain.complete(_request())

    assert response.status == "provider_auth_error"
    assert second.calls == 0, "auth failure must abort the chain (same key everywhere)"
    assert response.metadata["attempted_models"] == "chain-a"
    assert response.metadata["model_chain_position"] == "0"


def test_chain_never_advances_past_safety_validation_failed() -> None:
    first = _ScriptedProvider(model="chain-a", statuses=("safety_validation_failed",))
    second = _ScriptedProvider(model="chain-b", statuses=("ok",))
    chain = ChainedLLMProvider(providers=(first, second))

    response = chain.complete(_request())

    assert response.status == "safety_validation_failed"
    assert second.calls == 0, "unsafe output must never be retried on another model"
    assert response.metadata["attempted_models"] == "chain-a"


def test_chain_all_exhausted_returns_last_failure_and_stays_on_last_model() -> None:
    first = _ScriptedProvider(model="chain-a", statuses=("quota_exceeded",))
    second = _ScriptedProvider(model="chain-b", statuses=("rate_limited", "quota_exceeded"))
    chain = ChainedLLMProvider(providers=(first, second))

    response = chain.complete(_request("fundamentals_analyst"))
    assert response.status == "rate_limited"
    assert response.metadata["attempted_models"] == "chain-a,chain-b"
    assert response.metadata["model_chain_position"] == "1"

    followup = chain.complete(_request("technical_analyst"))
    assert followup.status == "quota_exceeded"
    assert (first.calls, second.calls) == (1, 2), "later roles retry only the final candidate"


def test_chain_requires_at_least_one_provider_and_single_provider_name() -> None:
    with pytest.raises(LLMProviderConfigurationError):
        ChainedLLMProvider(providers=())
    with pytest.raises(LLMProviderConfigurationError):
        ChainedLLMProvider(
            providers=(
                _ScriptedProvider(model="chain-a", statuses=()),
                _ScriptedProvider(model="chain-b", statuses=(), provider_name="openai"),
            )
        )


def test_resolver_builds_google_chain_from_candidates_without_sdk_import() -> None:
    config = LLMProviderConfig(
        mode="live",
        provider="google",
        model="model-a",
        model_candidates=("model-a", "model-b", "model-c"),
        google_credential_available=True,
    )
    resolution = resolve_llm_provider(
        config,
        secrets=LLMProviderSecrets(google_api_key="test-key-not-real"),
    )

    assert resolution.available
    assert resolution.provider_name == "google"
    assert resolution.model == "model-a"
    assert isinstance(resolution.provider, ChainedLLMProvider)
    assert resolution.provider.model == "model-a"


def test_resolver_without_candidates_keeps_plain_single_provider_and_no_chain_metadata() -> None:
    config = LLMProviderConfig(
        mode="live",
        provider="google",
        model="single-model",
        google_credential_available=True,
    )
    resolution = resolve_llm_provider(
        config,
        secrets=LLMProviderSecrets(google_api_key="test-key-not-real"),
    )

    assert resolution.available
    assert not isinstance(resolution.provider, ChainedLLMProvider)

    single = _ScriptedProvider(model="single-model", statuses=("ok",))
    response = single.complete(_request())
    assert "model_chain_position" not in response.metadata
    assert "attempted_models" not in response.metadata


def test_resolver_builds_openai_chain_from_candidates() -> None:
    config = LLMProviderConfig(
        mode="live",
        provider="openai",
        model="model-a",
        model_candidates=("model-a", "model-b"),
        openai_credential_available=True,
    )
    resolution = resolve_llm_provider(
        config,
        secrets=LLMProviderSecrets(openai_api_key="test-key-not-real"),
    )

    assert resolution.available
    assert resolution.provider_name == "openai"
    assert isinstance(resolution.provider, ChainedLLMProvider)
    assert resolution.provider.model == "model-a"


def test_chain_metadata_parsing_is_fail_safe_for_malformed_inputs() -> None:
    from app.services.agent_team.tool_mediated_report import _chain_metadata

    assert _chain_metadata(None) == (None, ())
    assert _chain_metadata("not-a-dict") == (None, ())
    assert _chain_metadata({}) == (None, ())
    assert _chain_metadata({"model_chain_position": "-1", "attempted_models": ""}) == (None, ())
    assert _chain_metadata({"model_chain_position": "abc", "attempted_models": " , , "}) == (None, ())
    assert _chain_metadata({"model_chain_position": 2, "attempted_models": ("tuple",)}) == (None, ())
    assert _chain_metadata({"model_chain_position": "1", "attempted_models": " m1 , m2 "}) == (
        1,
        ("m1", "m2"),
    )


def test_chain_response_metadata_leaks_no_secret_or_private_values() -> None:
    first = _ScriptedProvider(model="chain-a", statuses=("quota_exceeded",))
    second = _ScriptedProvider(model="chain-b", statuses=("ok",))
    chain = ChainedLLMProvider(providers=(first, second))

    payload = asdict(chain.complete(_request()))

    assert find_secret_like_values(payload) == set()
    assert find_forbidden_string_values(payload) == set()
