from src.agents.state import AgentState
from src.agents.trace import trace_event
from src.services.llm import get_llm


async def general_respond_node(state: AgentState) -> dict:
    """Xử lý hội thoại xã giao chào hỏi thông thường mà không cần truy xuất tools."""
    query = state.get("query", "")
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")

    prompt = (
        "You are the VinFast Test Drive Assistant. Friendly and polite.\n"
        "The user is engaging in general pleasantry or greeting.\n"
        "Provide a polite, friendly, and very concise greeting/conversation in Vietnamese, "
        "and invite them to explore VinFast cars or book a test drive.\n"
        f"User greeting: {query}"
    )

    try:
        llm = get_llm()
        if llm is None:
            return {"response": "Xin chào! Tôi có thể giúp gì cho bạn về xe VinFast hoặc đặt lịch hẹn lái thử hôm nay?"}
        trace_event("llm.request", trace_id=trace_id, node="general_respond", prompt=prompt)
        result = await llm.ainvoke(prompt)
        response = result.content
        trace_event("llm.response", trace_id=trace_id, node="general_respond", response=response)
    except Exception as exc:
        trace_event("llm.error", trace_id=trace_id, node="general_respond", error=str(exc))
        # Fallback greeting if LLM fails
        response = "Xin chào! Tôi có thể giúp gì cho bạn về xe VinFast hoặc đặt lịch hẹn lái thử hôm nay?"

    return {"response": response}
