import pytest
from src.agents.graph import agent


def _cfg(thread_id: str) -> dict:
    """Helper tạo config với thread_id cho LangGraph MemorySaver."""
    return {"configurable": {"thread_id": thread_id}}


@pytest.mark.asyncio
# test case of Chau + kiểm tra câu hỏi chủ quyền được route sang sensitive policy
async def test_router_sovereignty_policy():
    """Kiểm tra câu hỏi chủ quyền Hoàng Sa Trường Sa được xử lý bởi sensitive_policy node."""
    query = "Hoàng Sa Trường Sa là của ai?"
    result = await agent.ainvoke({"query": query}, config=_cfg("test-sovereignty"))

    assert result.get("intent") == "sensitive"
    assert "Hoàng Sa" in result.get("response", "")
    assert "Trường Sa" in result.get("response", "")
    assert "Việt Nam" in result.get("response", "")


@pytest.mark.asyncio
# test case of Chau + kiểm tra yêu cầu viết code ngoài phạm vi bị từ chối
async def test_router_out_of_scope_coding():
    """Kiểm tra yêu cầu viết code lập trình được chặn bởi sensitive_policy node."""
    query = "hãy viết cho tôi một đoạn code python để crawl web"
    result = await agent.ainvoke({"query": query}, config=_cfg("test-coding"))

    assert result.get("intent") == "sensitive"
    assert "Trợ lý ảo hỗ trợ lái thử xe VinFast" in result.get("response", "")
    assert "không hỗ trợ" in result.get("response", "")


@pytest.mark.asyncio
# test case of Chau + kiểm tra câu chào được route sang general response
async def test_router_general_greeting():
    """Kiểm tra câu chào hỏi xã giao được định tuyến sang general_respond node."""
    query = "Xin chào bạn nhé!"
    result = await agent.ainvoke({"query": query}, config=_cfg("test-greeting"))

    assert result.get("intent") == "general"
    assert "response" in result
    assert len(result.get("response", "")) > 0


@pytest.mark.asyncio
# test case of Chau + kiểm tra yêu cầu đặt lịch được route sang domain booking
async def test_router_domain_booking():
    """Kiểm tra yêu cầu đặt lịch/tư vấn xe được định tuyến sang booking skill."""
    query = "Đặt lịch lái thử xe VF3 tại Hà Nội"
    result = await agent.ainvoke({"query": query}, config=_cfg("test-booking"))

    assert result.get("intent") == "domain"
    assert result.get("active_skill") == "booking"
    assert "response" in result
    assert "Mocked LLM" in result.get("response", "")


@pytest.mark.asyncio
async def test_router_domain_advisory():
    """Kiểm tra câu hỏi tư vấn thông số xe được định tuyến sang advise skill."""
    query = "VF8 đi được bao nhiêu km sau một lần sạc đầy?"
    result = await agent.ainvoke({"query": query}, config=_cfg("test-advisory"))

    assert result.get("intent") == "domain"
    assert result.get("active_skill") == "advise"
    assert "response" in result
    assert "Mocked LLM" in result.get("response", "")


@pytest.mark.asyncio
async def test_tool_call_count_starts_at_zero():
    """Kiểm tra tool_call_count bắt đầu từ 0 khi không gọi tool."""
    query = "Xin chào!"
    result = await agent.ainvoke({"query": query}, config=_cfg("test-count-zero"))

    # general flow không gọi tool → tool_call_count phải là 0 hoặc không có
    assert (result.get("tool_call_count") or 0) == 0
