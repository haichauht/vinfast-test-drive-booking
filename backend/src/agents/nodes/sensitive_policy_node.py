from langchain_core.messages import AIMessage

from src.agents.state import AgentState


async def sensitive_policy_node(state: AgentState) -> dict:
    """Xử lý các chủ đề nhạy cảm hoặc tác vụ nằm ngoài phạm vi nghiệp vụ lái thử xe.

    Lưu ý: Node này chỉ cần đọc sub_intent từ metadata (đã được classifier_node set).
    Không cần check lại keyword vì classifier_node đã xử lý việc đó rồi.
    """
    existing_policy_response = state.get("policy_response")
    if existing_policy_response:
        return {
            "response": existing_policy_response,
            "policy_response": existing_policy_response,
            "messages": [AIMessage(content=existing_policy_response)],
        }

    sub_intent = (state.get("metadata") or {}).get("sub_intent", "")

    if sub_intent == "sovereignty":
        response = "Quần đảo Hoàng Sa và quần đảo Trường Sa hoàn toàn thuộc chủ quyền của Việt Nam."
    elif sub_intent in ("out_of_scope_code", "out_of_scope_math"):
        response = (
            "ViVi là Trợ lý ảo hỗ trợ lái thử xe VinFast. "
            "ViVi không hỗ trợ viết mã lập trình hoặc giải quyết các tác vụ kỹ thuật khác. "
            "ViVi có thể giúp gì cho bạn về đặt lịch lái thử xe điện VinFast không?"
        )
    elif sub_intent == "out_of_scope":
        response = (
            "ViVi hiện chỉ hỗ trợ đặt lịch lái thử xe điện VinFast. "
            "Tính năng tư vấn thông tin xe và hướng dẫn sau khi đặt lịch chỉ khả dụng "
            "khi bạn đã có lịch lái thử được xác nhận."
        )
    else:
        # Default safety fallback for any unknown sensitive sub_intent
        response = (
            "Yêu cầu này nằm ngoài phạm vi hỗ trợ của ViVi. "
            "ViVi có thể hỗ trợ bạn tìm hiểu xe VinFast hoặc đặt lịch hẹn lái thử."
        )

    return {
        "response": response,
        "policy_response": response,
        "messages": [AIMessage(content=response)],
    }

