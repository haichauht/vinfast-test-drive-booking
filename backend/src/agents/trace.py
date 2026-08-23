from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langsmith import traceable

LOGGER_NAME = "ai_agent"
_T = TypeVar("_T")

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
    _publish_langsmith_event(event, payload)


def _publish_langsmith_event(event: str, payload: dict[str, Any]) -> None:
    """Mirror structured local events to LangSmith as optional nested spans."""
    if os.getenv("LANGSMITH_EVENT_LOGS", "false").casefold() not in {"1", "true", "yes", "on"}:
        return

    @traceable(
        name=f"event.{event}",
        run_type="chain",
        process_inputs=redact,
        process_outputs=redact,
    )
    def record_event(event_payload: dict[str, Any]) -> dict[str, Any]:
        return {"recorded": True, "event": event_payload["event"]}

    try:
        record_event(payload)
    except Exception:
        # Observability must never affect the chat/booking path.
        logging.getLogger(LOGGER_NAME).debug("Unable to mirror event to LangSmith", exc_info=True)


def error_details(exc: Exception) -> dict[str, str]:
    """Return a stable, safe error shape for trace events."""
    code = str(getattr(exc, "code", "") or type(exc).__name__.upper())
    return {
        "error_code": code,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }


def state_snapshot(state: Mapping[str, Any]) -> dict[str, Any]:
    """Keep node traces useful without serialising the complete graph state."""
    keys = (
        "query",
        "context",
        "requested_action",
        "action_payload",
        "intent",
        "active_skill",
        "action_tool",
        "action_input",
        "action_result",
        "action_error",
        "response",
        "tool_call_count",
    )
    snapshot = {key: state[key] for key in keys if key in state and state[key] is not None}
    messages = state.get("messages")
    if isinstance(messages, Sequence) and not isinstance(messages, (str, bytes, bytearray)):
        snapshot["messages"] = [message_to_log(item) if isinstance(item, BaseMessage) else redact(item) for item in messages]
    return redact(snapshot)


def trace_node(node: str) -> Callable[[Callable[..., Awaitable[dict[str, Any]]]], Callable[..., Awaitable[dict[str, Any]]]]:
    """Emit input, output, latency and failures around an async LangGraph node."""
    def decorator(func: Callable[..., Awaitable[dict[str, Any]]]) -> Callable[..., Awaitable[dict[str, Any]]]:
        @wraps(func)
        async def wrapped(state: Mapping[str, Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
            trace_id = str((state.get("metadata") or {}).get("trace_id") or "")
            started = time.perf_counter()
            trace_event("node.started", trace_id=trace_id, node=node, input=state_snapshot(state))
            try:
                output = await func(state, *args, **kwargs)
            except Exception as exc:
                trace_event(
                    "node.failed",
                    trace_id=trace_id,
                    node=node,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    **error_details(exc),
                )
                raise
            trace_event(
                "node.completed",
                trace_id=trace_id,
                node=node,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                status="error" if output.get("action_error") or output.get("error") else "success",
                output=state_snapshot(output),
            )
            return output
        return wrapped
    return decorator


async def trace_async_operation(
    operation: str,
    *,
    trace_id: str,
    input: Any,
    awaitable: Awaitable[_T],
) -> _T:
    """Trace one awaited dependency call, such as an LLM invocation."""
    started = time.perf_counter()
    trace_event("operation.started", trace_id=trace_id, operation=operation, input=input)
    try:
        output = await awaitable
    except Exception as exc:
        trace_event(
            "operation.failed",
            trace_id=trace_id,
            operation=operation,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            **error_details(exc),
        )
        raise
    trace_event(
        "operation.completed",
        trace_id=trace_id,
        operation=operation,
        latency_ms=round((time.perf_counter() - started) * 1000, 2),
        output=message_to_log(output) if isinstance(output, BaseMessage) else output,
    )
    return output
