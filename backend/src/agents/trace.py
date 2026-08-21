from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from src.guardrails.policies import PUBLIC_TOOL_INPUT_SECRET_KEYS, SECRET_VALUE_KEYS, is_sensitive_key

LOGGER_NAME = "ai_agent"

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_RE = re.compile(
    r"(?<!\d)(?:(?:\(\s*\+?84\s*\)|\+?84|0)(?:[\s().-]?\d){8,10}|"
    r"\(\s*0\d{2,3}\s*\)(?:[\s.-]?\d){6,8})(?!\d)"
)
_VIETNAM_ID_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
_STANDALONE_SECRET_RE = re.compile(
    r"(?i)(?<![\w-])(?:"
    r"sk-(?:or-v1-)?[a-z0-9_-]{8,}|"
    r"xox[baprs]-[a-z0-9-]{10,}|"
    r"gh[pousr]_[a-z0-9]{20,}|"
    r"AIza[a-z0-9_-]{20,}|"
    r"eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}"
    r")"
)
_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)\b("
    r"(?:openai|openrouter|x)?[_ -]?api[_ -]?key|"
    r"access[_ -]?(?:session[_ -]?)?token|session[_ -]?token|refresh[_ -]?token|"
    r"authorization|client[_ -]?secret|private[_ -]?key|cookie|"
    r"otp(?:[_ -]?code)?|password|secret|token"
    r")\s*[:=]\s*(?:bearer\s+)?([^\s,;]+)"
)
_SECRET_KEYS = SECRET_VALUE_KEYS | PUBLIC_TOOL_INPUT_SECRET_KEYS


def _mask_text(value: str, *, limit: int = 4000) -> str:
    masked = _EMAIL_RE.sub("[email]", value)
    masked = _PHONE_RE.sub("[phone]", masked)
    masked = _CREDENTIAL_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[redacted]", masked)
    masked = _STANDALONE_SECRET_RE.sub("[redacted]", masked)
    masked = _VIETNAM_ID_RE.sub("[personal-id]", masked)
    return masked if len(masked) <= limit else masked[:limit] + "...[truncated]"


def redact(value: Any, *, key: str = "") -> Any:
    if is_sensitive_key(key, _SECRET_KEYS):
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
