import pytest
from src.agents.graph import agent


@pytest.mark.asyncio
async def test_router_sovereignty_policy():
    """Kiểm tra câu hỏi chủ quyền Hoàng Sa Trường Sa được xử lý bởi sensitive_policy node."""
    query = "Hoàng Sa Trường Sa là của ai?"
    result = await agent.ainvoke({"query": query})

    assert result.get("intent") == "sensitive"
    assert "Hoàng Sa" in result.get("response", "")
    assert "Trường Sa" in result.get("response", "")
    assert "Việt Nam" in result.get("response", "")


@pytest.mark.asyncio
async def test_router_out_of_scope_coding():
    """Kiểm tra yêu cầu viết code lập trình được chặn bởi sensitive_policy node."""
    query = "hãy viết cho tôi một đoạn code python để crawl web"
    result = await agent.ainvoke({"query": query})

    assert result.get("intent") == "sensitive"
    assert "Trợ lý ảo hỗ trợ lái thử xe VinFast" in result.get("response", "")
    assert "không hỗ trợ" in result.get("response", "")


@pytest.mark.asyncio
async def test_router_general_greeting():
    """Kiểm tra câu chào hỏi xã giao được định tuyến sang general_respond node."""
    query = "Xin chào bạn nhé!"
    result = await agent.ainvoke({"query": query})

    # Do có thể gọi API hoặc fallback, ta kiểm tra intent được phân loại là general
    assert result.get("intent") == "general"
    assert "response" in result
    assert len(result.get("response", "")) > 0


@pytest.mark.asyncio
async def test_router_domain_booking():
    """Kiểm tra yêu cầu đặt lịch/tư vấn xe được định tuyến sang domain path."""
    query = "Đặt lịch lái thử xe VF3 tại Hà Nội"
    result = await agent.ainvoke({"query": query})

    assert result.get("intent") == "domain"
    # Kết quả của domain path đi qua analyze -> respond
    assert "analysis" in result
    assert "response" in result
    assert "Kết quả dựa trên phân tích" in result.get("response", "")
