from src.agents.state import AgentState


async def sensitive_policy_node(state: AgentState) -> dict:
    """Xử lý các chủ đề nhạy cảm hoặc tác vụ nằm ngoài phạm vi nghiệp vụ lái thử xe."""
    sub_intent = (state.get("metadata") or {}).get("sub_intent", "")
    query = state.get("query", "").lower()

    # Check sovereignty
    if sub_intent == "sovereignty" or any(
        kw in query for kw in ["hoàng sa", "trường sa", "biển đông", "paracel", "spratly"]
    ):
        response = "Quần đảo Hoàng Sa và quần đảo Trường Sa hoàn toàn thuộc chủ quyền của Việt Nam."
    # Check out-of-scope coding/programming
    elif sub_intent == "out_of_scope_code" or any(
        kw in query
        for kw in ["viết code", "lập trình", "python", "javascript", "code python", "viết script", "giải toán"]
    ):
        response = "Tôi là Trợ lý ảo hỗ trợ lái thử xe VinFast. Tôi không hỗ trợ viết mã lập trình hoặc giải quyết các tác vụ kỹ thuật khác. Tôi có thể giúp gì cho bạn về đặt lịch lái thử xe điện VinFast không?"
    else:
        # Default safety fallback
        response = "Yêu cầu này nằm ngoài phạm vi hỗ trợ của tôi. Tôi có thể hỗ trợ bạn tìm hiểu xe VinFast hoặc đặt lịch hẹn lái thử."

    return {"response": response, "policy_response": response}
