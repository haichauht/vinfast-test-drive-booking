from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, cast

from src.guardrails.models import ProtectedOutput
from src.guardrails.policies import (
    NEVER_PUBLIC_ACTION_DATA_KEYS,
    PUBLIC_TOOL_INPUT_SECRET_KEYS,
    SECRET_VALUE_KEYS,
)
from src.guardrails.structure import normalize_text

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.-]?\d){8,10}(?!\d)")
_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_ -]?key|access[_ -]?token|session[_ -]?token|otp[_ -]?code|password|secret)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_SYSTEM_PROMPT_MARKERS = (
    "--- system instructions ---",
    "active skill guidelines",
    "system instructions & behavioral protocol",
)
_SAFE_LEAK_FALLBACK = (
    "Tôi không thể hiển thị chỉ dẫn nội bộ hoặc thông tin xác thực. "
    "Tôi có thể hỗ trợ thông tin xe VinFast và đặt lịch lái thử."
)


class OutputGuard:
    def __init__(self, *, max_output_chars: int) -> None:
        self.max_output_chars = max_output_chars

    def protect(self, result: Mapping[str, Any]) -> ProtectedOutput:
        secret_values = _collect_secret_values(result)
        response = self._sanitize_text(result.get("response", ""), secret_values=secret_values)
        action_error = self._sanitize_text(result.get("action_error", ""), secret_values=secret_values)
        action_input = result.get("action_input")
        tool_input = _redact_mapping(
            cast(Mapping[str, Any], action_input) if isinstance(action_input, Mapping) else {},
            blocked_keys=PUBLIC_TOOL_INPUT_SECRET_KEYS,
        )
        action_data = _redact_value(result.get("action_result"), blocked_keys=NEVER_PUBLIC_ACTION_DATA_KEYS)
        return ProtectedOutput(
            response=response,
            # Internal reasoning is never part of the public API contract.
            analysis="",
            tool_input=tool_input,
            action_data=action_data,
            action_error=action_error,
        )

    def _sanitize_text(self, value: Any, *, secret_values: set[str]) -> str:
        text = normalize_text(value if isinstance(value, str) else str(value or ""))
        lowered = text.casefold()
        if any(marker in lowered for marker in _SYSTEM_PROMPT_MARKERS):
            return _SAFE_LEAK_FALLBACK

        for secret in sorted(secret_values, key=len, reverse=True):
            if len(secret) >= 4:
                text = text.replace(secret, "[redacted]")
        text = _CREDENTIAL_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[redacted]", text)
        text = _EMAIL_RE.sub("[email]", text)
        text = _PHONE_RE.sub("[phone]", text)
        if len(text) > self.max_output_chars:
            text = text[: self.max_output_chars] + "…[truncated]"
        return text


def _collect_secret_values(value: Any, *, key: str = "") -> set[str]:
    found: set[str] = set()
    if key.casefold() in SECRET_VALUE_KEYS and isinstance(value, str) and value:
        found.add(value)
    if isinstance(value, Mapping):
        for nested_key, nested in value.items():
            found.update(_collect_secret_values(nested, key=str(nested_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            found.update(_collect_secret_values(nested, key=key))
    return found


def _redact_mapping(value: Mapping[str, Any], *, blocked_keys: frozenset[str]) -> dict[str, Any]:
    return {
        str(key): _redact_value(nested, key=str(key), blocked_keys=blocked_keys)
        for key, nested in value.items()
    }


def _redact_value(value: Any, *, key: str = "", blocked_keys: frozenset[str]) -> Any:
    if key.casefold() in blocked_keys:
        return "[redacted]"
    if isinstance(value, Mapping):
        return _redact_mapping(value, blocked_keys=blocked_keys)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_redact_value(item, blocked_keys=blocked_keys) for item in value]
    return value
