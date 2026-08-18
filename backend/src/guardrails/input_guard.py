from __future__ import annotations

import re
from typing import Any

from src.guardrails.models import GuardrailDecision
from src.guardrails.policies import ACTION_ALLOWED_FIELDS, PROMPT_INJECTION_PATTERNS
from src.guardrails.structure import PayloadLimits, iter_strings, normalize_text, validate_payload

_SAFE_CONVERSATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")

_BLOCKED_MESSAGE = (
    "Yêu cầu này có dấu hiệu cố gắng thay đổi chỉ dẫn hoặc truy cập thông tin nội bộ, "
    "nên ViVi không thể xử lý. ViVi vẫn có thể hỗ trợ thông tin xe VinFast và đặt lịch lái thử."
)
_INVALID_PAYLOAD_MESSAGE = "Dữ liệu gửi lên không hợp lệ hoặc quá phức tạp. Vui lòng tải lại trang và thử lại."


class InputGuard:
    def __init__(self, payload_limits: PayloadLimits) -> None:
        self.payload_limits = payload_limits
        self._injection_patterns = tuple(
            (code, re.compile(expression, re.IGNORECASE | re.DOTALL))
            for code, expression in PROMPT_INJECTION_PATTERNS
        )

    def inspect(
        self,
        *,
        message: str,
        conversation_id: str,
        context: dict[str, Any],
        action: str | None,
        action_payload: dict[str, Any],
    ) -> GuardrailDecision:
        normalized_message = normalize_text(message)
        if not normalized_message:
            return GuardrailDecision.block(
                "EMPTY_MESSAGE",
                "message is empty after normalization",
                "Tin nhắn không được để trống.",
            )

        if conversation_id and not _SAFE_CONVERSATION_ID.fullmatch(conversation_id):
            return GuardrailDecision.block(
                "INVALID_CONVERSATION_ID",
                "conversation_id contains unsupported characters",
                _INVALID_PAYLOAD_MESSAGE,
            )

        for label, payload in (("context", context), ("action_payload", action_payload)):
            payload_decision = self.inspect_payload(payload, label=label)
            if not payload_decision.allowed:
                return payload_decision

        if action:
            action_decision = self.inspect_structured_payload(
                action=action,
                payload=action_payload,
                contracts=ACTION_ALLOWED_FIELDS,
            )
            if not action_decision.allowed:
                return action_decision

        # Context is interpolated into an LLM prompt in booking_skill_node, so it
        # receives the same injection screening as the visible chat message.
        candidates = [normalized_message, *iter_strings(context)]
        for candidate in candidates:
            normalized_candidate = normalize_text(candidate)
            for code, pattern in self._injection_patterns:
                if pattern.search(normalized_candidate):
                    return GuardrailDecision.block(
                        code,
                        "high-confidence prompt/role injection pattern matched",
                        _BLOCKED_MESSAGE,
                    )

        return GuardrailDecision.allow(sanitized_text=normalized_message)

    def inspect_payload(self, payload: Any, *, label: str) -> GuardrailDecision:
        violation = validate_payload(payload, self.payload_limits)
        if violation:
            return GuardrailDecision.block(
                "PAYLOAD_LIMIT_EXCEEDED",
                f"{label}: {violation}",
                _INVALID_PAYLOAD_MESSAGE,
                details={"field": label},
            )
        return GuardrailDecision.allow()

    def inspect_structured_payload(
        self,
        *,
        action: str,
        payload: dict[str, Any],
        contracts: dict[str, frozenset[str]],
    ) -> GuardrailDecision:
        payload_decision = self.inspect_payload(payload, label="action_payload")
        if not payload_decision.allowed:
            return payload_decision
        allowed_fields = contracts.get(action)
        if allowed_fields is None:
            return GuardrailDecision.block(
                "ACTION_NOT_ALLOWED",
                f"structured action is not allowlisted: {action}",
                "Thao tác này không được hỗ trợ.",
            )
        unexpected = sorted(set(payload) - allowed_fields)
        if unexpected:
            return GuardrailDecision.block(
                "ACTION_FIELDS_NOT_ALLOWED",
                "structured action contains fields outside its contract",
                _INVALID_PAYLOAD_MESSAGE,
                details={"action": action, "fields": unexpected},
            )
        return GuardrailDecision.allow()
