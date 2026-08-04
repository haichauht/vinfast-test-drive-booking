from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Tin nhắn từ user")
    conversation_id: str = Field(
        default="", max_length=100, description="ID phiên hội thoại (để nhớ lịch sử nhiều lượt)"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tin nhắn không được chỉ chứa khoảng trắng.")
        return v


class ChatResponse(BaseModel):
    response: str = Field(..., description="Phản hồi từ agent")
    analysis: str = Field(default="", description="Phân tích nội bộ")
    conversation_id: str = Field(default="", description="ID phiên hội thoại trả về cho client")


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
