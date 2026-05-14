from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    email: EmailStr | None
    auth_provider: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
