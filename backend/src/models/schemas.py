from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

CHAT_MESSAGE_MAX_LENGTH = 150


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=CHAT_MESSAGE_MAX_LENGTH, description="Tin nhắn từ user")
    conversation_id: str = Field(
        default="", max_length=100, description="ID phiên hội thoại (để nhớ lịch sử nhiều lượt)"
    )
    action: Literal["search_options", "hold_slot", "update_draft", "confirm_booking", "request_access", "verify_access"] | None = Field(
        default=None,
        description="Structured booking action requested by a confirmed UI interaction.",
    )
    action_payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tin nhắn không được chỉ chứa khoảng trắng.")
        return v


class UiDirective(BaseModel):
    event: str = ""
    phase: str = ""
    allowed_actions: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str = Field(..., description="Phản hồi từ agent")
    analysis: str = Field(default="", description="Phân tích nội bộ")
    conversation_id: str = Field(default="", description="ID phiên hội thoại trả về cho client")
    tool_name: str = ""
    tool_input: dict[str, Any] = Field(default_factory=dict)
    action_data: Any | None = None
    action_error: str = ""
    intent: str = ""
    ui: UiDirective | None = None


class DemoActionRequest(BaseModel):
    action: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class CsvImportRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)


class DatasetImportRequest(BaseModel):
    files: dict[str, str] = Field(..., min_length=1)


class ClientLogRequest(BaseModel):
    level: str = "error"
    message: str = Field(..., min_length=1, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)
