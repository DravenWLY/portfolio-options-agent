from datetime import datetime
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

AccountType = Literal["taxable_individual", "roth_ira", "traditional_ira", "other"]

_NICKNAME_ALLOWED_RE = re.compile(r"^[A-Za-z0-9 &'().,_/-]+$")
_NICKNAME_FORBIDDEN_TOKENS = (
    "account_number",
    "account number",
    "provider_account",
    "provider account",
    "broker_account",
    "broker account",
    "snaptrade",
    "secret",
    "token",
    "raw_payload",
    "raw payload",
    "raw provider",
    "buying_power",
    "buying power",
    "api_key",
    "api key",
    "access_token",
    "access token",
    "user_secret",
    "user secret",
    "consumer_key",
    "consumer key",
    "provider_user",
    "provider user",
    "portal_url",
    "portal url",
    "safe to trade",
    "ready to trade",
    "you should",
    "i recommend",
    "recommend buying",
    "recommend selling",
    "guaranteed",
    "guaranteed return",
    "place order",
    "submit order",
    "execute trade",
)


class AccountCreate(BaseModel):
    broker_name: str = Field(min_length=1, max_length=80)
    account_type: AccountType
    display_name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return value.upper()


class AccountUpdate(BaseModel):
    broker_name: str | None = Field(default=None, min_length=1, max_length=80)
    account_type: AccountType | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None


class AccountNicknameUpdate(BaseModel):
    nickname: str | None = None

    @field_validator("nickname")
    @classmethod
    def normalize_nickname(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        if not normalized:
            return None
        if len(normalized) > 60:
            raise ValueError("nickname must be 60 characters or fewer")
        if _NICKNAME_ALLOWED_RE.fullmatch(normalized) is None:
            raise ValueError("nickname contains unsupported characters")
        lowered = normalized.lower()
        phrase_text = re.sub(r"[-_]+", " ", lowered)
        if any(token in phrase_text for token in _NICKNAME_FORBIDDEN_TOKENS):
            raise ValueError("nickname contains private or unsupported wording")
        if re.search(r"\d{4,}", normalized):
            raise ValueError("nickname must not include account-number-like digits")
        return normalized

class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    broker_name: str
    account_type: str
    display_name: str
    base_currency: str
    is_manual: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
