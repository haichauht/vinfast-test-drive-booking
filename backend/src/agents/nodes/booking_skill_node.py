import json
import logging
import uuid
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from src.agents.state import AgentState
from src.agents.tools import (
    confirm_test_drive_booking,
    get_booking_details,
    get_booking_draft,
    hold_test_drive_slot,
    request_booking_access,
    search_test_drive_options,
    update_booking_draft,
    verify_booking_access,
)
from src.agents.utils import get_system_prompt
from src.services.llm import get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "booking_skill" / "SKILL.md"

STRUCTURED_ACTION_TO_TOOL = {
    "search_options": search_test_drive_options,
    "hold_slot": hold_test_drive_slot,
    "update_draft": update_booking_draft,
    "confirm_booking": confirm_test_drive_booking,
}

STRUCTURED_ACTION_RESPONSES = {
    "search_options": "Tôi đã kiểm tra dữ liệu showroom và lịch trống mới nhất.",
    "hold_slot": "Tôi đã giữ khung giờ này trong 15 phút.",
    "update_draft": "Tôi đã lưu thông tin người đặt và người lái.",
    "confirm_booking": "Đặt lịch lái thử đã được xác nhận.",
}


def _decode_tool_result(message: ToolMessage) -> object:
    content = message.content
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content


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


def get_booking_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are the Booking Assistant. Help users search, update, verify and confirm test drive bookings."


async def booking_skill_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])
    requested_action = state.get("requested_action")

    if requested_action:
        tool = STRUCTURED_ACTION_TO_TOOL.get(requested_action)
        if tool is None:
            message = AIMessage(content="Thao tác đặt lịch này chưa được hỗ trợ.")
            return {"messages": [message], "response": message.content, "action_error": message.content}

        last_message = messages[-1] if messages else None
        if isinstance(last_message, ToolMessage):
            failed = getattr(last_message, "status", "success") == "error"
            decoded = _decode_tool_result(last_message)
            response_text = (
                "Không thể hoàn tất thao tác đặt lịch. Vui lòng kiểm tra lại hoặc thử lại."
                if failed
                else STRUCTURED_ACTION_RESPONSES[requested_action]
            )
            response = AIMessage(content=response_text)
            return {
                "messages": [response],
                "response": response_text,
                "action_tool": tool.name,
                "action_input": state.get("action_payload") or {},
                "action_result": None if failed else decoded,
                "action_error": str(decoded) if failed else "",
            }

        tool_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": tool.name,
                    "args": state.get("action_payload") or {},
                    "id": f"call_{uuid.uuid4().hex}",
                    "type": "tool_call",
                }
            ],
        )
        return {"messages": [tool_call], "tool_call_count": 1}

    context = json.dumps(state.get("context") or {}, ensure_ascii=False)
    prompt = (
        f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (BOOKING) ---\n{get_booking_prompt()}"
        f"\n\n--- CURRENT UI CONTEXT ---\n{context}"
    )

    tools = [
        search_test_drive_options,
        hold_test_drive_slot,
        get_booking_draft,
        update_booking_draft,
        request_booking_access,
        verify_booking_access,
        get_booking_details,
        confirm_test_drive_booking,
    ]

    try:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke([SystemMessage(content=prompt)] + messages)
    except Exception as e:
        logging.getLogger(__name__).exception("Error in booking_skill_node")
        safe_response = AIMessage(content="Đã xảy ra lỗi khi kết nối với mô hình AI. Vui lòng thử lại sau.")
        return {
            "messages": [safe_response],
            "response": safe_response.content,
            "error": str(e),
        }

    # Extract response text for the API
    response_content = cast(str, response.content) if hasattr(response, "content") else ""

    # Tăng tool_call_count nếu LLM đang gọi tool
    has_tool_calls = hasattr(response, "tool_calls") and bool(response.tool_calls)
    current_count = state.get("tool_call_count") or 0

    output: dict[str, Any] = {
        "messages": [response],
        "tool_call_count": current_count + 1 if has_tool_calls else current_count,
    }
    if response_content:
        output["response"] = response_content

    last_message = messages[-1] if messages else None
    if isinstance(last_message, ToolMessage):
        failed = getattr(last_message, "status", "success") == "error"
        decoded = _decode_tool_result(last_message)
        output.update(
            {
                "action_tool": last_message.name or "",
                "action_input": _tool_call_input(messages, last_message),
                "action_result": None if failed else decoded,
                "action_error": str(decoded) if failed else "",
            }
        )

    return output
