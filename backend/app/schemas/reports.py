from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ReportThreadStatus = Literal["draft", "running", "completed", "failed", "cancelled"]
ReportMessageSender = Literal["user", "system", "agent", "tool"]
ReportMessageType = Literal[
    "user_input",
    "system_event",
    "agent_output",
    "tool_output",
    "error",
    "retry_notice",
    "final_report",
    "markdown_report",
]
ReportMessageVisibility = Literal["private", "internal", "public_demo"]


class ReportThreadCreate(BaseModel):
    account_id: UUID | None = None
    title: str = Field(min_length=1, max_length=200)
    report_type: str = Field(default="portfolio_report", min_length=1, max_length=80)
    status: ReportThreadStatus = "draft"


class ReportThreadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID | None
    title: str
    report_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ReportMessageCreate(BaseModel):
    sender_type: ReportMessageSender
    message_type: ReportMessageType
    content_markdown: str | None = None
    content_json: dict[str, Any] | None = None
    sequence: int = Field(ge=1)
    visibility: ReportMessageVisibility = "private"


class ReportMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    sender_type: str
    message_type: str
    content_markdown: str | None
    content_json: dict[str, Any] | None
    sequence: int
    visibility: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ReportThreadDetailRead(ReportThreadRead):
    messages: list[ReportMessageRead] = Field(default_factory=list)
