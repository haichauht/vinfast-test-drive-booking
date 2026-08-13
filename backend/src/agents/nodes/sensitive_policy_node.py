from src.agents.state import AgentState


async def sensitive_policy_node(state: AgentState) -> dict:
    """Xử lý các chủ đề nhạy cảm hoặc tác vụ nằm ngoài phạm vi nghiệp vụ lái thử xe.

    Lưu ý: Node này chỉ cần đọc sub_intent từ metadata (đã được classifier_node set).
    Không cần check lại keyword vì classifier_node đã xử lý việc đó rồi.
    """
    sub_intent = (state.get("metadata") or {}).get("sub_intent", "")

    if sub_intent == "sovereignty":
        response = "Quần đảo Hoàng Sa và quần đảo Trường Sa hoàn toàn thuộc chủ quyền của Việt Nam."
    elif sub_intent in ("out_of_scope_code", "out_of_scope_math"):
        response = (
            "Tôi là Trợ lý ảo hỗ trợ lái thử xe VinFast. "
            "Tôi không hỗ trợ viết mã lập trình hoặc giải quyết các tác vụ kỹ thuật khác. "
            "Tôi có thể giúp gì cho bạn về đặt lịch lái thử xe điện VinFast không?"
        )
    else:
        # Default safety fallback for any unknown sensitive sub_intent
        response = (
            "Yêu cầu này nằm ngoài phạm vi hỗ trợ của tôi. "
            "Tôi có thể hỗ trợ bạn tìm hiểu xe VinFast hoặc đặt lịch hẹn lái thử."
        )

    return {"response": response, "policy_response": response}
