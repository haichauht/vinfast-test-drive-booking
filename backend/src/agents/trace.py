from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

LOGGER_NAME = "ai_agent"

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.-]?\d){8,10}(?!\d)")
_SECRET_KEYS = {
    "access_session_token",
    "access_token",
    "api_key",
    "authorization",
    "code_hash",
    "contact_value",
    "destination_hash",
    "email",
    "license_number",
    "normalized_email",
    "normalized_phone",
    "otp",
    "otp_code",
    "password",
    "phone",
    "token",
    "token_hash",
}


def _mask_text(value: str, *, limit: int = 4000) -> str:
    masked = _EMAIL_RE.sub("[email]", value)
    masked = _PHONE_RE.sub("[phone]", masked)
    return masked if len(masked) <= limit else masked[:limit] + "...[truncated]"


def redact(value: Any, *, key: str = "") -> Any:
    if key.lower() in _SECRET_KEYS:
        return "[redacted]"
    if isinstance(value, str):
        return _mask_text(value)
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]
    return value


def message_to_log(message: BaseMessage) -> dict[str, Any]:
    data: dict[str, Any] = {
        "type": message.__class__.__name__,
        "content": redact(getattr(message, "content", "")),
    }
    if isinstance(message, AIMessage) and message.tool_calls:
        data["tool_calls"] = redact(message.tool_calls)
    if isinstance(message, ToolMessage):
        data.update(
            {
                "name": message.name,
                "tool_call_id": message.tool_call_id,
                "status": getattr(message, "status", "success"),
            }
        )
    if isinstance(message, (HumanMessage, SystemMessage)):
        data["role"] = message.type
    return data


def messages_to_log(messages: Sequence[BaseMessage]) -> list[dict[str, Any]]:
    return [message_to_log(message) for message in messages]


def trace_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **redact(fields)}
    logging.getLogger(LOGGER_NAME).info(json.dumps(payload, ensure_ascii=False, default=str))
