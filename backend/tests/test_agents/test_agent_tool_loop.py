from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from src.agents.graph import agent
from src.agents.nodes.classifier_node import classifier_node

from src.agents.nodes import advise_skill_node as advise_module


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _scripted_tool_llm(*responses):
    bound = MagicMock()
    bound.ainvoke = AsyncMock(side_effect=responses)
    llm = MagicMock()
    llm.bind_tools.return_value = bound
    return llm, bound


# test case of Chau + kiểm tra agent chạy đủ vòng advise gọi tool nhận ToolMessage rồi trả câu trả lời cuối
@pytest.mark.asyncio
async def test_advise_agent_executes_tool_and_returns_final_response(monkeypatch):
    tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_knowledge",
                "args": {"query": "VF8 range"},
                "id": "call-search-knowledge",
                "type": "tool_call",
            }
        ],
    )
    llm, bound = _scripted_tool_llm(tool_call, AIMessage(content="VF8 information found"))
    monkeypatch.setattr(advise_module, "get_llm", lambda: llm)

    result = await agent.ainvoke({"query": "VF8 range"}, config=_config("chau-agent-real-tool-loop"))

    assert result["active_skill"] == "advise"
    assert result["response"] == "VF8 information found"
    assert result["tool_call_count"] == 1
    tool_messages = [message for message in result["messages"] if isinstance(message, ToolMessage)]
    assert len(tool_messages) == 1
    assert "VF8 range" in tool_messages[0].content
    assert bound.ainvoke.await_count == 2


# test case of Chau + kiểm tra advise agent không được gọi booking tool ngoài whitelist của skill
@pytest.mark.asyncio
async def test_advise_agent_converts_unauthorized_tool_call_to_tool_error(monkeypatch):
    unauthorized_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_booking_draft",
                "args": {"booking_id": "booking-secret"},
                "id": "call-unauthorized-booking-tool",
                "type": "tool_call",
            }
        ],
    )
    llm, _ = _scripted_tool_llm(
        unauthorized_call,
        AIMessage(content="I cannot use that booking tool from advise skill"),
    )
    monkeypatch.setattr(advise_module, "get_llm", lambda: llm)

    result = await agent.ainvoke({"query": "VF8 price"}, config=_config("chau-agent-tool-whitelist"))

    tool_messages = [message for message in result["messages"] if isinstance(message, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].status == "error"
    assert "get_booking_draft" in tool_messages[0].content
    assert result["response"] == "I cannot use that booking tool from advise skill"


# test case of Chau + kiểm tra lỗi LLM trong advise skill không làm toàn bộ API agent thất bại
@pytest.mark.asyncio
async def test_advise_agent_handles_llm_exception_with_safe_response(monkeypatch):
    llm, _ = _scripted_tool_llm(RuntimeError("LLM unavailable"))
    monkeypatch.setattr(advise_module, "get_llm", lambda: llm)

    result = await agent.ainvoke({"query": "VF8 specifications"}, config=_config("chau-agent-llm-failure"))

    assert result["response"]
    assert "error" in result or "thử lại" in result["response"].lower()


# test case of Chau + kiểm tra bộ đếm tool được reset ở đầu mỗi user turn thay vì cộng dồn cả conversation
@pytest.mark.asyncio
async def test_classifier_resets_tool_call_counter_for_new_user_turn():

    result = await classifier_node({"query": "VF8 range", "tool_call_count": 8})

    assert result["tool_call_count"] == 0
