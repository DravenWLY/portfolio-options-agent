import pytest
from fastapi.testclient import TestClient

from app.api.routes.symbols import get_symbol_directory_refresh_runner
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.symbol_directory import (
    SymbolDirectoryRefreshError,
    clear_active_symbol_directory_snapshot,
    import_nasdaq_symbol_directory_files,
)


pytestmark = [pytest.mark.api, pytest.mark.unit]


@pytest.fixture(autouse=True)
def _clear_symbol_directory_snapshot():
    clear_active_symbol_directory_snapshot(disable_auto_restore=True)
    yield
    clear_active_symbol_directory_snapshot(disable_auto_restore=True)


def test_symbol_search_route_returns_provider_neutral_shape(client: TestClient) -> None:
    response = client.get("/symbols/search", params={"q": "NV"})

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "query",
        "normalized_query",
        "data_mode",
        "result_mode",
        "section_label",
        "source_label",
        "as_of_label",
        "items",
        "no_match",
        "message",
    }
    assert payload["query"] == "NV"
    assert payload["normalized_query"] == "NV"
    assert payload["data_mode"] == "synthetic"
    assert payload["result_mode"] == "search"
    assert payload["section_label"] == "Search results"
    assert payload["source_label"] == "Offline symbol fallback fixture"
    assert payload["as_of_label"] == "Offline fixture · not live market data"
    assert payload["no_match"] is False
    assert payload["message"] == "Search results"
    assert [item["symbol"] for item in payload["items"]] == ["NVDA", "NVDL"]
    assert set(payload["items"][0]) == {
        "symbol",
        "name",
        "asset_class",
        "exchange",
        "region",
        "currency",
        "is_supported",
        "match_type",
        "score_label",
        "source_label",
        "as_of_label",
    }
    assert payload["items"][0]["asset_class"] == "stock"
    assert payload["items"][1]["asset_class"] == "etf"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_symbol_search_route_returns_empty_non_search_state_for_empty_query(client: TestClient) -> None:
    response = client.get("/symbols/search", params={"q": ""})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result_mode"] == "empty"
    assert payload["section_label"] == ""
    assert payload["message"] == ""
    assert payload["items"] == []
    assert payload["no_match"] is False


def test_symbol_search_route_returns_symbol_not_found_without_edit_distance_match(client: TestClient) -> None:
    response = client.get("/symbols/search", params={"q": "NOKK"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_query"] == "NOKK"
    assert payload["result_mode"] == "no_match"
    assert payload["section_label"] == "Symbol Not Found"
    assert payload["items"] == []
    assert payload["no_match"] is True
    assert payload["message"] == "Symbol Not Found"


def test_symbol_search_route_returns_exact_first_related_nok_matches(client: TestClient) -> None:
    response = client.get("/symbols/search", params={"q": "nok", "limit": "6"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_query"] == "NOK"
    assert [item["symbol"] for item in payload["items"]] == ["NOK", "NOKBF", "NOKPF", "LNOK", "NKRKF", "NKRKY"]
    assert [item["score_label"] for item in payload["items"]] == [
        "Exact symbol match",
        "Symbol prefix match",
        "Symbol prefix match",
        "Symbol contains match",
        "Reference match",
        "Reference match",
    ]


def test_symbol_search_route_respects_limit(client: TestClient) -> None:
    response = client.get("/symbols/search", params={"q": "NOK", "limit": "2"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["symbol"] for item in payload["items"]] == ["NOK", "NOKBF"]


def test_symbol_validate_route_returns_supported_and_unsupported_states(client: TestClient) -> None:
    supported = client.get("/symbols/validate", params={"symbol": " nvda "})
    unsupported = client.get("/symbols/validate", params={"symbol": "SPX"})
    missing = client.get("/symbols/validate", params={"symbol": "ZZZ"})

    assert supported.status_code == 200
    assert supported.json()["normalized_symbol"] == "NVDA"
    assert supported.json()["is_found"] is True
    assert supported.json()["is_supported"] is True
    assert unsupported.status_code == 200
    assert unsupported.json()["normalized_symbol"] == "SPX"
    assert unsupported.json()["is_found"] is True
    assert unsupported.json()["is_supported"] is False
    assert missing.status_code == 200
    assert missing.json()["is_found"] is False
    assert missing.json()["message"] == "Symbol Not Found"


def test_symbol_routes_avoid_private_fields_and_execution_language(client: TestClient) -> None:
    search_payload = client.get("/symbols/search", params={"q": "NV"}).json()
    validation_payload = client.get("/symbols/validate", params={"symbol": "NVDA"}).json()
    rendered = repr((search_payload, validation_payload)).lower()

    assert not find_forbidden_keys(search_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(validation_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
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


def test_symbol_search_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/symbols/search", params={"q": "NV"})

    assert response.status_code == 401


def test_symbol_directory_refresh_route_returns_sanitized_success(app, client: TestClient, tmp_path) -> None:
    nasdaq_path = tmp_path / "nasdaqlisted.txt"
    nasdaq_path.write_text(
        "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
        "NVDA|NVIDIA Corporation - Common Stock|Q|N|N|100|N|N\n"
        "File Creation Time: 0528202618:00|||||||\n",
        encoding="utf-8",
    )

    def runner():
        return import_nasdaq_symbol_directory_files((nasdaq_path,))

    app.dependency_overrides[get_symbol_directory_refresh_runner] = lambda: runner
    try:
        response = client.post("/symbols/directory/refresh")
    finally:
        app.dependency_overrides.pop(get_symbol_directory_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refreshed"
    assert payload["data_mode"] == "provider_reference"
    assert payload["source_label"] == "Nasdaq Symbol Directory"
    assert payload["record_count"] == 1
    assert payload["message"] == "Symbol directory refresh completed."
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_symbol_directory_refresh_route_returns_sanitized_failure(app, client: TestClient) -> None:
    def runner():
        raise SymbolDirectoryRefreshError("raw_payload provider_account_id secret row")

    app.dependency_overrides[get_symbol_directory_refresh_runner] = lambda: runner
    try:
        response = client.post("/symbols/directory/refresh")
    finally:
        app.dependency_overrides.pop(get_symbol_directory_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    assert payload["status"] == "failed"
    assert payload["data_mode"] == "unavailable"
    assert payload["record_count"] == 0
    assert payload["message"] == "Symbol directory refresh failed; last good snapshot was preserved."
    assert "raw_payload" not in rendered
    assert "provider_account_id" not in rendered
    assert "secret" not in rendered


def test_symbol_directory_refresh_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.post("/symbols/directory/refresh")

    assert response.status_code == 401
