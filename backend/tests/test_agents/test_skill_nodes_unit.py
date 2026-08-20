from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from src.agents.nodes.advise_skill_node import advise_skill_node
from src.agents.nodes.booking_skill_node import booking_skill_node
from src.agents.utils import window_messages

from src.agents.nodes import advise_skill_node as advise_module
from src.agents.nodes import booking_skill_node as booking_module


def _mock_bound_llm(response):
    llm = MagicMock()
    bound = MagicMock()
    bound.ainvoke = AsyncMock(return_value=response)
    llm.bind_tools.return_value = bound
    return llm, bound


# test case of Chau + kiểm tra booking skill chỉ bind đúng tám booking tools
@pytest.mark.asyncio
async def test_booking_skill_binds_only_booking_tools_and_returns_text(monkeypatch):
    llm, bound = _mock_bound_llm(AIMessage(content="Đã tìm thấy lịch lái thử"))
    monkeypatch.setattr(booking_module, "get_llm", lambda: llm)
    monkeypatch.setattr(booking_module, "get_system_prompt", lambda: "SYSTEM")
    monkeypatch.setattr(booking_module, "get_booking_prompt", lambda: "BOOKING")
    user_message = HumanMessage(content="Tìm lịch VF6")

    result = await booking_skill_node({"messages": [user_message], "tool_call_count": 2})

    bound_names = [item.name for item in llm.bind_tools.call_args.args[0]]
    assert bound_names == [
        "search_test_drive_options",
        "hold_test_drive_slot",
        "get_booking_draft",
        "update_booking_draft",
        "request_booking_access",
        "verify_booking_access",
        "get_booking_details",
        "confirm_test_drive_booking",
    ]
    sent_messages = bound.ainvoke.await_args.args[0]
    assert isinstance(sent_messages[0], SystemMessage)
    assert "SYSTEM" in sent_messages[0].content
    assert "BOOKING" in sent_messages[0].content
    assert sent_messages[1] is user_message
    assert result["response"] == "Đã tìm thấy lịch lái thử"
    assert result["tool_call_count"] == 2


# test case of Chau + kiểm tra booking skill tăng counter khi LLM tạo tool call
@pytest.mark.asyncio
async def test_booking_skill_increments_count_for_tool_call(monkeypatch):
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "booking-call-1",
                "name": "search_test_drive_options",
                "args": {"vehicle_model": "VF6"},
            }
        ],
    )
    llm, _ = _mock_bound_llm(response)
    monkeypatch.setattr(booking_module, "get_llm", lambda: llm)

    result = await booking_skill_node({"messages": [HumanMessage(content="VF6")], "tool_call_count": 3})

    assert result["messages"] == [response]
    assert result["tool_call_count"] == 4
    assert "response" not in result


@pytest.mark.asyncio
async def test_structured_booking_action_uses_a_stable_tool_call_id():
    state = {
        "requested_action": "hold_slot",
        "action_payload": {"slot_id": "slot-main", "ui_action_id": "hold:retry-safe"},
    }

    first = await booking_skill_node(state)
    second = await booking_skill_node(state)

    first_id = first["messages"][0].tool_calls[0]["id"]
    second_id = second["messages"][0].tool_calls[0]["id"]
    assert first_id == second_id


def test_message_window_keeps_a_tool_call_and_its_result_together():
    tool_request = AIMessage(
        content="",
        tool_calls=[{"id": "call-1", "name": "search_knowledge", "args": {"query": "VF8"}}],
    )
    tool_result = ToolMessage(content="result", tool_call_id="call-1")
    messages = [HumanMessage(content=f"old-{index}") for index in range(22)] + [tool_request, tool_result]

    window = window_messages(messages, limit=2)

    assert window == [tool_request, tool_result]


# test case of Chau + kiểm tra advise skill chỉ bind knowledge tool và trả lời tư vấn
@pytest.mark.asyncio
async def test_advise_skill_binds_only_knowledge_tool_and_returns_text(monkeypatch):
    llm, bound = _mock_bound_llm(AIMessage(content="VF8 có phạm vi di chuyển phù hợp nhu cầu đường dài"))
    monkeypatch.setattr(advise_module, "get_llm", lambda: llm)
    monkeypatch.setattr(advise_module, "get_system_prompt", lambda: "SYSTEM")
    monkeypatch.setattr(advise_module, "get_advise_prompt", lambda: "ADVISE")

    result = await advise_skill_node({"messages": [HumanMessage(content="Tư vấn VF8")]})

    bound_names = [item.name for item in llm.bind_tools.call_args.args[0]]
    assert bound_names == ["search_knowledge"]
    sent_messages = bound.ainvoke.await_args.args[0]
    assert "SYSTEM" in sent_messages[0].content
    assert "ADVISE" in sent_messages[0].content
    assert result["response"].startswith("VF8")
    assert result["tool_call_count"] == 0


# test case of Chau + kiểm tra advise skill tăng counter khi gọi knowledge tool
@pytest.mark.asyncio
async def test_advise_skill_increments_count_for_tool_call(monkeypatch):
    response = AIMessage(
        content="",
        tool_calls=[{"id": "advise-call-1", "name": "search_knowledge", "args": {"query": "VF8 range"}}],
    )
    llm, _ = _mock_bound_llm(response)
    monkeypatch.setattr(advise_module, "get_llm", lambda: llm)

    result = await advise_skill_node({"messages": [], "tool_call_count": 0})

    assert result["messages"] == [response]
    assert result["tool_call_count"] == 1
    assert "response" not in result


# test case of Chau + kiểm tra prompt loader của hai skill có fallback khi file không đọc được
def test_skill_prompt_loaders_have_safe_fallback(monkeypatch, tmp_path):
    missing = tmp_path / "missing-skill.md"
    monkeypatch.setattr(booking_module, "SKILL_PATH", missing)
    monkeypatch.setattr(advise_module, "SKILL_PATH", missing)

    assert "Booking Assistant" in booking_module.get_booking_prompt()
    assert "Advisory Assistant" in advise_module.get_advise_prompt()
