from src.agents.state import AgentState
from src.services.llm import get_llm


async def general_respond_node(state: AgentState) -> dict:
    """Xử lý hội thoại xã giao chào hỏi thông thường mà không cần truy xuất tools."""
    query = state.get("query", "")

    prompt = (
        "You are the VinFast Test Drive Assistant. Friendly and polite.\n"
        "The user is engaging in general pleasantry or greeting.\n"
        "Provide a polite, friendly, and very concise greeting/conversation in Vietnamese, "
        "and invite them to explore VinFast cars or book a test drive.\n"
        f"User greeting: {query}"
    )

    try:
        llm = get_llm()
        result = await llm.ainvoke(prompt)
        response = result.content
    except Exception:
        # Fallback greeting if LLM fails
        response = "Xin chào! Tôi có thể giúp gì cho bạn về xe VinFast hoặc đặt lịch hẹn lái thử hôm nay?"

    return {"response": response}
