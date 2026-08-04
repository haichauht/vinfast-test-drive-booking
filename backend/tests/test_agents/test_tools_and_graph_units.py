import pytest
from langchain_core.messages import AIMessage
from src.agents.graph import MAX_TOOL_CALLS, route_intent, should_continue_advise, should_continue_booking
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node
from src.agents.tools.calculator.tool import calculate
from src.agents.tools.search_knowledge.tool import search_knowledge


# test case of Chau + kiểm tra route_intent chọn đúng node theo intent và fallback domain
@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({"intent": "sensitive"}, "sensitive_policy"),
        ({"intent": "general"}, "general_respond"),
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


# test case of Chau + kiểm tra calculator tính đúng biểu thức và thứ tự phép toán
@pytest.mark.parametrize(
    ("expression", "expected"),
    [("2 + 3 * 4", "14"), ("(2 + 3) * 4", "20"), ("2 ** 3", "8")],
)
def test_calculator_supported_expressions(expression, expected):
    assert calculate.invoke({"expression": expression}) == expected


# test case of Chau + kiểm tra calculator từ chối code injection và phép chia cho không
@pytest.mark.parametrize(
    "expression",
    ["__import__('os').system('whoami')", "1 / 0", "[1, 2, 3]"],
)
def test_calculator_rejects_unsafe_or_invalid_expressions(expression):
    result = calculate.invoke({"expression": expression})

    assert result.startswith("Lỗi tính toán:")


# test case of Chau + kiểm tra knowledge tool trả kết quả gắn với query đầu vào
def test_search_knowledge_returns_query_context():
    result = search_knowledge.invoke({"query": "VF6 Plus"})

    assert "VF6 Plus" in result


# test case of Chau + kiểm tra sensitive policy dùng fallback an toàn cho sub intent lạ
@pytest.mark.asyncio
async def test_sensitive_policy_unknown_sub_intent_uses_safe_fallback():
    result = await sensitive_policy_node({"query": "unknown request", "metadata": {"sub_intent": "unknown"}})

    assert result["response"] == result["policy_response"]
    assert "ngoài phạm vi" in result["response"]
