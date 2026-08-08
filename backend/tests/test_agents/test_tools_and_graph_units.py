import pytest
from langchain_core.messages import AIMessage
from src.agents.graph import MAX_TOOL_CALLS, route_intent, should_continue_advise, should_continue_booking


# test case of Chau + kiểm tra route_intent chọn đúng node theo intent và fallback domain
@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({"intent": "sensitive"}, "sensitive_policy"),
        ({"intent": "domain", "active_skill": "booking"}, "booking_skill"),
        ({"intent": "domain", "active_skill": "advise"}, "advise_skill"),
        ({"intent": "domain"}, "advise_skill"),
        ({}, "advise_skill"),
        ({"intent": "unknown"}, "advise_skill"),
    ],
)
def test_route_intent_mapping(state, expected):
    assert route_intent(state) == expected


# test case of Chau + kiểm tra skill chỉ gọi tool khi có tool call và chưa vượt loop limit
@pytest.mark.parametrize("router", [should_continue_booking, should_continue_advise])
def test_should_continue_skill_respects_tool_calls_and_loop_limit(router):
    tool_message = AIMessage(
        content="",
        tool_calls=[{"id": "call-1", "name": "search_knowledge", "args": {"query": "VF6"}}],
    )

    assert router({"messages": []}) == "end"
    assert router({"messages": [AIMessage(content="done")]}) == "end"
    assert router({"messages": [tool_message], "tool_call_count": 0}) == "continue"
    assert router({"messages": [tool_message], "tool_call_count": MAX_TOOL_CALLS}) == "end"
