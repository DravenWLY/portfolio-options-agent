"""Provider-neutral symbol lookup read contracts."""

from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


SymbolLookupDataMode: TypeAlias = Literal["synthetic", "replay", "provider_reference", "unavailable"]
SymbolAssetClass: TypeAlias = Literal["stock", "etf", "adr", "option", "index", "unknown"]
SymbolMatchType: TypeAlias = Literal["exact", "prefix", "contains", "alias", "not_found"]
SymbolSearchResultMode: TypeAlias = Literal["empty", "search", "no_match", "unavailable"]
SymbolDirectoryRefreshStatus: TypeAlias = Literal["refreshed", "failed"]

PROHIBITED_SYMBOL_LOOKUP_PHRASES = (
    "i recommend",
    "recommended",
    "top pick",
    "safe to trade",
    "ready to trade",
    "place order",
    "submit order",
    "execute trade",
    "guaranteed return",
)


def validate_symbol_lookup_payload(value: object) -> None:
    """Reject private fields and advice/execution wording in symbol lookup responses."""

    forbidden = find_forbidden_keys(value, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    if forbidden:
        raise ValueError(f"symbol lookup payload contains forbidden private fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for phrase in PROHIBITED_SYMBOL_LOOKUP_PHRASES:
        if phrase in rendered:
            raise ValueError(f"symbol lookup payload contains prohibited wording: {phrase}")


class SymbolSearchItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    symbol: str
    name: str
    asset_class: SymbolAssetClass
    exchange: str
    region: str
    currency: str
    is_supported: bool
    match_type: SymbolMatchType
    score_label: str
    source_label: str
    as_of_label: str


class SymbolSearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    query: str
    normalized_query: str
    data_mode: SymbolLookupDataMode
    result_mode: SymbolSearchResultMode
    section_label: str
    source_label: str
    as_of_label: str
    items: tuple[SymbolSearchItemRead, ...]
    no_match: bool
    message: str

    @model_validator(mode="after")
    def symbol_search_payload_must_be_safe(self) -> "SymbolSearchRead":
        validate_symbol_lookup_payload(self.model_dump(mode="python"))
        return self


class SymbolValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    symbol: str
    normalized_symbol: str
    is_found: bool
    is_supported: bool
    asset_class: SymbolAssetClass
    exchange: str | None = None
    name: str | None = None
    data_mode: SymbolLookupDataMode
    source_label: str
    as_of_label: str
    message: str

    @model_validator(mode="after")
    def symbol_validation_payload_must_be_safe(self) -> "SymbolValidationRead":
        validate_symbol_lookup_payload(self.model_dump(mode="python"))
        return self


class SymbolDirectoryRefreshStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    status: SymbolDirectoryRefreshStatus
    data_mode: SymbolLookupDataMode
    source_label: str
    as_of_label: str
    imported_at: datetime | None = None
    record_count: int
    message: str

    @model_validator(mode="after")
    def symbol_directory_refresh_status_must_be_safe(self) -> "SymbolDirectoryRefreshStatusRead":
        validate_symbol_lookup_payload(self.model_dump(mode="python"))
        return self
