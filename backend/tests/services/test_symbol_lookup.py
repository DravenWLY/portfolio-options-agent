import pytest

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.symbol_directory import clear_active_symbol_directory_snapshot
from app.services.symbols import DemoSymbolProvider, SymbolRecord, SymbolService


pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _clear_symbol_directory_snapshot():
    clear_active_symbol_directory_snapshot(disable_auto_restore=True)
    yield
    clear_active_symbol_directory_snapshot(disable_auto_restore=True)


def test_symbol_search_uses_strict_prefix_matching() -> None:
    result = SymbolService().search("NV")

    assert result.normalized_query == "NV"
    assert [item.symbol for item in result.items] == ["NVDA", "NVDL"]
    assert {item.match_type for item in result.items} == {"prefix"}
    assert {item.score_label for item in result.items} == {"Symbol prefix match"}
    assert result.no_match is False


def test_symbol_search_empty_query_returns_empty_non_search_state() -> None:
    result = SymbolService().search("")

    assert result.result_mode == "empty"
    assert result.section_label == ""
    assert result.message == ""
    assert result.normalized_query == ""
    assert result.items == ()
    assert result.no_match is False
    assert not find_forbidden_keys(result.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_symbol_search_normalizes_case_and_whitespace() -> None:
    result = SymbolService().search(" nvda ")

    assert result.query == "nvda"
    assert result.normalized_query == "NVDA"
    assert result.items[0].symbol == "NVDA"
    assert result.items[0].match_type == "exact"


def test_symbol_search_does_not_return_edit_distance_matches() -> None:
    result = SymbolService().search("NOKK")

    assert result.items == ()
    assert result.no_match is True
    assert result.result_mode == "no_match"
    assert result.message == "Symbol Not Found"


def test_symbol_search_empty_not_found_state_is_display_safe() -> None:
    result = SymbolService().search("ZZZ")

    assert result.items == ()
    assert result.no_match is True
    assert result.section_label == "Symbol Not Found"
    assert result.message == "Symbol Not Found"
    assert result.data_mode == "synthetic"


def test_symbol_search_offline_fallback_is_not_broad_directory() -> None:
    service = SymbolService()

    for query in ("INTC", "GLD", "SLV"):
        result = service.search(query)

        assert result.items == ()
        assert result.result_mode == "no_match"
        assert result.message == "Symbol Not Found"


def test_symbol_search_returns_exact_nok_first_then_related_matches() -> None:
    result = SymbolService().search("NOK")

    assert [item.symbol for item in result.items] == ["NOK", "NOKBF", "NOKPF", "LNOK", "NKRKF", "NKRKY"]
    assert [item.score_label for item in result.items] == [
        "Exact symbol match",
        "Symbol prefix match",
        "Symbol prefix match",
        "Symbol contains match",
        "Reference match",
        "Reference match",
    ]


def test_symbol_search_ranks_symbol_contains_before_name_contains() -> None:
    result = SymbolService().search("RAM")

    assert [item.symbol for item in result.items] == ["DRAM", "AMRX"]
    assert [item.score_label for item in result.items] == ["Symbol contains match", "Reference match"]


def test_symbol_search_respects_limit_after_backend_ordering() -> None:
    result = SymbolService().search("NOK", limit=3)

    assert [item.symbol for item in result.items] == ["NOK", "NOKBF", "NOKPF"]


def test_symbol_search_labels_etfs_and_filters_unsupported_test_issues() -> None:
    result = SymbolService().search("SP")

    assert [item.symbol for item in result.items] == ["SPY"]
    assert result.items[0].asset_class == "etf"
    assert "SPX" not in {item.symbol for item in result.items}
    assert "TESTU" not in {item.symbol for item in SymbolService().search("TEST").items}


def test_symbol_service_deduplicates_symbols_and_prefers_supported_record() -> None:
    provider = DemoSymbolProvider(
        records=(
            SymbolRecord(symbol="DUPL", name="Unsupported Duplicate", asset_class="index", exchange="CBOE", is_supported=False),
            SymbolRecord(symbol="dupl", name="Supported Duplicate", asset_class="stock", exchange="NASDAQ"),
        )
    )

    result = SymbolService(provider).search("DUP")

    assert [item.symbol for item in result.items] == ["DUPL"]
    assert result.items[0].name == "Supported Duplicate"
    assert result.items[0].asset_class == "stock"


def test_symbol_validation_distinguishes_supported_unsupported_and_not_found() -> None:
    service = SymbolService()

    supported = service.validate(" nvda ")
    unsupported = service.validate("SPX")
    missing = service.validate("NOPE")

    assert supported.normalized_symbol == "NVDA"
    assert supported.is_found is True
    assert supported.is_supported is True
    assert unsupported.is_found is True
    assert unsupported.is_supported is False
    assert unsupported.message == "Symbol found but not supported for this workflow."
    assert missing.is_found is False
    assert missing.is_supported is False
    assert missing.message == "Symbol Not Found"


def test_symbol_lookup_provider_failure_is_sanitized() -> None:
    class FailingProvider:
        data_mode = "synthetic"
        source_label = "Synthetic failing provider"
        as_of_label = "Synthetic"

        def list_symbols(self):
            raise RuntimeError("raw_payload provider_account_id secret detail")

    search = SymbolService(FailingProvider()).search("NV")
    validation = SymbolService(FailingProvider()).validate("NVDA")
    rendered = repr((search.model_dump(mode="python"), validation.model_dump(mode="python"))).lower()

    assert search.data_mode == "unavailable"
    assert search.result_mode == "unavailable"
    assert search.items == ()
    assert search.message == "Symbol lookup is temporarily unavailable."
    assert validation.data_mode == "unavailable"
    assert validation.message == "Symbol validation is temporarily unavailable."
    assert "raw_payload" not in rendered
    assert "provider_account_id" not in rendered
    assert "secret detail" not in rendered


def test_symbol_lookup_responses_exclude_private_fields_and_raw_payloads() -> None:
    payload = SymbolService().search("NV").model_dump(mode="python")

    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_provider_payload",
        "provider_account_id",
        "account_id",
        "threshold",
        "prompt",
        "llm_response",
        "safe to trade",
        "ready to trade",
        "recommended",
        "guaranteed return",
        "place order",
        "execute trade",
    )
    assert not any(text in rendered for text in forbidden_text)
