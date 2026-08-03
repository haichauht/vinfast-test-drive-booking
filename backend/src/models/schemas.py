from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Tin nhắn từ user")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Phản hồi từ agent")
    analysis: str = Field(default="", description="Phân tích nội bộ")


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
