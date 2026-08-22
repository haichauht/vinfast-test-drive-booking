import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.agents.state import AgentState
from src.agents.tools import (
    confirm_test_drive_booking,
    get_booking_details,
    get_booking_draft,
    hold_test_drive_slot,
    request_booking_access,
    request_user_location,
    search_test_drive_options,
    update_booking_draft,
    verify_booking_access,
)
from src.agents.trace import message_to_log, messages_to_log, trace_event
from src.agents.utils import get_system_prompt, window_messages
from src.dependencies import usage_budget_service
from src.services.llm import get_llm
from src.services.usage_budget import BudgetExceededError, LLMCallLimitExceededError, invoke_with_budget

SKILL_PATH = Path(__file__).parent.parent / "skills" / "booking_skill" / "SKILL.md"
tool_logger = logging.getLogger("agent.tools")
_SENSITIVE_TOOL_FIELDS = {"otp_code", "access_session_token", "zalo_bot_token", "api_key", "token"}
_BOOKING_ERROR_MESSAGE_RE = re.compile(r"BookingError\((?:'|\")(?P<message>.*?)(?:'|\")\)")


def _safe_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep operational context in logs without persisting credentials or full contacts."""
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if key in _SENSITIVE_TOOL_FIELDS:
            safe[key] = "[redacted]"
        elif key in {"phone", "contact_value", "destination"} and isinstance(value, str):
            safe[key] = f"***{value[-4:]}" if len(value) >= 4 else "***"
        elif key == "email" and isinstance(value, str):
            safe[key] = f"***@{value.rsplit('@', 1)[-1]}" if "@" in value else "***"
        elif isinstance(value, dict):
            safe[key] = _safe_tool_input(value)
        else:
            safe[key] = value
    return safe

STRUCTURED_ACTION_TO_TOOL = {
    "search_options": search_test_drive_options,
    "hold_slot": hold_test_drive_slot,
    "update_draft": update_booking_draft,
    "confirm_booking": confirm_test_drive_booking,
    "request_access": request_booking_access,
    "verify_access": verify_booking_access,
}

STRUCTURED_ACTION_RESPONSES = {
    "search_options": "ViVi đã kiểm tra dữ liệu showroom và lịch trống mới nhất.",
    "hold_slot": "ViVi đã giữ khung giờ này trong 2 phút.",
    "update_draft": "ViVi đã lưu thông tin người đặt và người lái.",
    "confirm_booking": "Đặt lịch lái thử đã được xác nhận.",
    "request_access": "ViVi đã gửi mã xác thực qua email.",
    "verify_access": "Xác thực thành công.",
}

ACCESS_INTENT_PURPOSES = {
    "booking_lookup": "lookup",
    "booking_reschedule": "reschedule",
    "booking_cancel": "cancel",
    "booking_update_details": "update_details",
    "booking_update_notifications": "update_notifications",
}

PUBLIC_TOOL_ERRORS = {
    "SLOT_NO_LONGER_AVAILABLE": "Khung giờ này đã qua hoặc không còn khả dụng, vui lòng chọn giờ khác.",
    "SLOT_UNAVAILABLE": "Khung giờ này không còn khả dụng, vui lòng chọn giờ khác.",
    "HOLD_EXPIRED": "Thời gian giữ chỗ đã hết hạn, vui lòng chọn lại khung giờ.",
    "VEHICLE_NOT_READY": "Xe demo hiện không sẵn sàng cho khung giờ này, vui lòng chọn lịch khác.",
    "VERSION_CONFLICT": "Thông tin đặt lịch đã thay đổi, vui lòng tải lại và thử lại.",
    "INVALID_INPUT": "Thông tin gửi lên chưa hợp lệ, vui lòng kiểm tra lại.",
}

DEFAULT_PUBLIC_TOOL_ERROR = "Không thể hoàn tất thao tác đặt lịch. Vui lòng kiểm tra lại hoặc thử lại."


def _decode_tool_result(message: ToolMessage) -> object:
    content = message.content
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content


def _public_tool_error(decoded: object) -> tuple[str, str]:
    code = ""
    if isinstance(decoded, dict):
        nested_error = decoded.get("error")
        raw_code = decoded.get("code") or decoded.get("error_code")
        if not raw_code and isinstance(nested_error, dict):
            raw_code = nested_error.get("code")
        code = str(raw_code or "")
    else:
        text = str(decoded or "")
        for known_code in PUBLIC_TOOL_ERRORS:
            if known_code in text:
                code = known_code
                break
        if not code:
            if "không còn khả dụng" in text or "khai thác" in text or "đã qua" in text or "Slot đã bắt đầu" in text or "Slot da bat dau" in text:
                code = "SLOT_NO_LONGER_AVAILABLE"
            elif "hết hạn" in text:
                code = "HOLD_EXPIRED"
            elif "Xe demo" in text or "Pin xe" in text:
                code = "VEHICLE_NOT_READY"

    if code == "INVALID_INPUT" and isinstance(decoded, dict):
        nested_error = decoded.get("error")
        if isinstance(nested_error, dict) and isinstance(nested_error.get("message"), str):
            return code, nested_error["message"]
    if code in PUBLIC_TOOL_ERRORS:
        return code, PUBLIC_TOOL_ERRORS[code]
    return "AGENT_ACTION_FAILED", _tool_error_message(decoded)


def _tool_call_input(messages: list, tool_message: ToolMessage) -> dict[str, Any]:
    """Return the arguments belonging to a completed tool call."""
    for message in reversed(messages[:-1]):
        if not isinstance(message, AIMessage):
            continue
        for tool_call in message.tool_calls:
            if tool_call.get("id") == tool_message.tool_call_id:
                args = tool_call.get("args")
                return args if isinstance(args, dict) else {}
    return {}


def _tool_error_message(decoded: object) -> str:
    """Return a safe, conversational error instead of ToolNode's exception wrapper."""
    if isinstance(decoded, dict):
        error = decoded.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
    if isinstance(decoded, str):
        match = _BOOKING_ERROR_MESSAGE_RE.search(decoded)
        if match:
            return match.group("message")
    return "Thao tác chưa thể hoàn tất lúc này. Bạn vui lòng thử lại nhé."


def _structured_tool_call_id(action: str, payload: dict[str, Any]) -> str:
    """Use a stable ID so a graph retry represents the same UI command."""
    canonical = json.dumps(
        {"action": action, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return f"call_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]}"


def get_booking_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are the Booking Assistant. Help users search, update, verify and confirm test drive bookings."


async def booking_skill_node(state: AgentState) -> dict:
    response: Any
    messages = list(state.get("messages") or [])
    requested_action = state.get("requested_action")
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")

    last_message = messages[-1] if messages else None



    if requested_action:
        tool = STRUCTURED_ACTION_TO_TOOL.get(requested_action)
        if tool is None:
            message = AIMessage(content="Thao tác đặt lịch này chưa được hỗ trợ.")
            return {"messages": [message], "response": message.content, "action_error": message.content}

        if isinstance(last_message, ToolMessage):
            failed = getattr(last_message, "status", "success") == "error"
            decoded = _decode_tool_result(last_message)
            error_code, public_error = _public_tool_error(decoded)
            trace_event(
                "tool.result",
                trace_id=trace_id,
                node="booking_skill",
                tool_message=message_to_log(last_message),
                result=decoded,
                failed=failed,
            )
            tool_logger.info(
                "tool_completed tool=%s status=%s",
                tool.name,
                "error" if failed else "success",
            )
            response_text = public_error if failed else STRUCTURED_ACTION_RESPONSES[requested_action]
            if (
                not failed
                and requested_action == "search_options"
                and isinstance(decoded, dict)
                and decoded.get("search_stage") == "location_clarification"
            ):
                response_text = str(decoded.get("clarification_message") or response_text)
            tool_response = AIMessage(content=response_text)
            return {
                "messages": [tool_response],
                "response": response_text,
                "action_tool": tool.name,
                "action_input": state.get("action_payload") or {},
                "action_result": None if failed else decoded,
                "action_error": error_code if failed else "",
            }

        action_payload = state.get("action_payload") or {}
        tool_logger.info("tool_dispatched tool=%s mode=structured input=%s", tool.name, _safe_tool_input(action_payload))
        tool_call_message = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": tool.name,
                    "args": action_payload,
                    "id": _structured_tool_call_id(requested_action, action_payload),
                    "type": "tool_call",
                }
            ],
        )
        trace_event(
            "tool.call",
            trace_id=trace_id,
            node="booking_skill",
            source="structured_action",
            action=requested_action,
            tool=tool.name,
            args=action_payload,
            tool_call_id=tool_call_message.tool_calls[0].get("id"),
        )
        return {"messages": [tool_call_message], "tool_call_count": 1}

    # Broad regions must not be geocoded to an arbitrary representative point.
    # End the tool loop deterministically instead of asking the LLM to
    # paraphrase the clarification.
    if isinstance(last_message, ToolMessage):
        decoded = _decode_tool_result(last_message)
        if isinstance(decoded, dict) and decoded.get("search_stage") == "location_clarification":
            response_text = str(
                decoded.get("clarification_message")
                or "Quý khách cho ViVi xin tỉnh hoặc thành phố cụ thể."
            )
            message = AIMessage(content=response_text)
            return {
                "messages": [message],
                "response": response_text,
                "action_tool": last_message.name or "",
                "action_input": _tool_call_input(messages, last_message),
                "action_result": decoded,
                "action_error": "",
                "metadata": metadata,
            }

    now_vietnam = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d")
    context = json.dumps(state.get("context") or {}, ensure_ascii=False)
    prompt = (
        f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (BOOKING) ---\n{get_booking_prompt()}"
        f"\n\n--- REAL-TIME CONTEXT ---\nCurrent Date (Vietnam): {now_vietnam}"
        f"\n\n--- CURRENT UI CONTEXT ---\n{context}"
    )

    tools = [
        search_test_drive_options,
        hold_test_drive_slot,
        get_booking_draft,
        update_booking_draft,
        request_booking_access,
        request_user_location,
        verify_booking_access,
        get_booking_details,
        confirm_test_drive_booking,
    ]

    try:
        llm = get_llm()
        if llm is None:
            raise RuntimeError("LLM is not configured")
        force_availability_search = (
            metadata.get("sub_intent") == "booking_availability"
            and isinstance(last_message, HumanMessage)
            and bool((state.get("context") or {}).get("selected_vehicle_name"))
            and bool((state.get("context") or {}).get("selected_showroom_id"))
        )
        llm_with_tools = (
            llm.bind_tools(tools, tool_choice=search_test_drive_options.name)
            if force_availability_search
            else llm.bind_tools(tools)
        )
        llm_messages = [SystemMessage(content=prompt)] + window_messages(messages)
        trace_event(
            "llm.request",
            trace_id=trace_id,
            node="booking_skill",
            tools=[tool.name for tool in tools],
            messages=messages_to_log(llm_messages),
        )
        response = await invoke_with_budget(
            llm_with_tools,
            llm_messages,
            model=getattr(llm, "model_name", "") or "chat",
            metadata=metadata,
            budget=usage_budget_service,
            call_purpose="booking_skill",
        )
    except (BudgetExceededError, LLMCallLimitExceededError) as e:
        budget_exceeded = isinstance(e, BudgetExceededError)
        error_code = "LLM_BUDGET_EXCEEDED" if budget_exceeded else "LLM_CALL_LIMIT_EXCEEDED"
        error_message = (
            "Hệ thống đã đạt giới hạn chi phí AI trong hôm nay. Vui lòng thử lại sau."
            if budget_exceeded
            else "Yêu cầu này cần quá nhiều lượt xử lý AI. Vui lòng gửi lại yêu cầu ngắn gọn hơn."
        )
        safe_response = AIMessage(content=error_message)
        return {
            "messages": [safe_response],
            "response": safe_response.content,
            "action_error": error_code,
            "metadata": metadata,
        }
    except Exception as e:
        trace_event("llm.error", trace_id=trace_id, node="booking_skill", error=str(e))
        logging.getLogger(__name__).exception("Error in booking_skill_node")
        safe_response = AIMessage(content="ViVi chưa xử lý được yêu cầu này lúc này. Bạn vui lòng thử lại hoặc chọn trực tiếp từ bảng hỗ trợ bên trái giúp ViVi nhé.")
        return {
            "messages": [safe_response],
            "response": safe_response.content,
            "error": str(e),
            "metadata": metadata,
        }

    # Extract response text for the API
    response_content = cast(str, response.content) if hasattr(response, "content") else ""

    # Tăng tool_call_count nếu LLM đang gọi tool
    has_tool_calls = hasattr(response, "tool_calls") and bool(response.tool_calls)
    current_count = state.get("tool_call_count") or 0
    trace_event(
        "llm.response",
        trace_id=trace_id,
        node="booking_skill",
        message=message_to_log(response),
        has_tool_calls=has_tool_calls,
    )
    if has_tool_calls:
        for tool_call_data in cast(list[dict[str, Any]], response.tool_calls):
            trace_event(
                "tool.call",
                trace_id=trace_id,
                node="booking_skill",
                source="llm",
                tool=tool_call_data.get("name"),
                args=tool_call_data.get("args"),
                tool_call_id=tool_call_data.get("id"),
            )
            arguments = tool_call_data.get("args")
            tool_logger.info(
                "tool_dispatched tool=%s mode=llm input=%s",
                tool_call_data.get("name", "unknown"),
                _safe_tool_input(arguments if isinstance(arguments, dict) else {}),
            )

    output: dict[str, Any] = {
        "messages": [response],
        "tool_call_count": current_count + 1 if has_tool_calls else current_count,
        "metadata": metadata,
    }
    if response_content:
        output["response"] = response_content

    last_message = messages[-1] if messages else None
    if isinstance(last_message, ToolMessage):
        failed = getattr(last_message, "status", "success") == "error"
        decoded = _decode_tool_result(last_message)
        error_code, public_error = _public_tool_error(decoded)
        trace_event(
            "tool.result",
            trace_id=trace_id,
            node="booking_skill",
            tool_message=message_to_log(last_message),
            input=_tool_call_input(messages, last_message),
            result=decoded,
            failed=failed,
        )
        tool_logger.info(
            "tool_completed tool=%s status=%s input=%s",
            last_message.name or "unknown",
            "error" if failed else "success",
            _safe_tool_input(_tool_call_input(messages, last_message)),
        )
        output.update(
            {
                "action_tool": last_message.name or "",
                "action_input": _tool_call_input(messages, last_message),
                "action_result": None if failed else decoded,
                "action_error": error_code if failed else "",
            }
        )
        if failed and not output.get("response"):
            output["response"] = public_error

    return output
