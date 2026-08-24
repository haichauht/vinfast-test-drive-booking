import json
import logging
import re
from collections.abc import Sequence
from pathlib import Path

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.agents.tools import search_knowledge, update_user_profile
from src.agents.trace import message_to_log, messages_to_log, trace_async_operation, trace_event, trace_node
from src.agents.utils import get_system_prompt, window_messages
from src.dependencies import profile_service
from src.services.llm import extract_response_text, get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "post_booking_skill" / "SKILL.md"
_HOUSEHOLD_SIZE_STATEMENT = re.compile(
    r"\b(?:gia\s+đình|nhà)\s+(?:của\s+)?(?:tôi|mình|em|anh|chị|ta)?\s*"
    r"(?:có|gồm)\s+\d+\s+(?:người|thành\s+viên)\b",
    re.IGNORECASE,
)


def get_post_booking_prompt() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _requires_profile_capture(messages: Sequence[object]) -> bool:
    """Identify explicit, durable statements that must not be answered without capture.

    The skill prompt governs general capture. This narrow gate protects a common,
    high-value correction such as "gia đình tôi có 4 người" from being skipped
    when the model prioritizes a knowledge-search tool for the same turn.
    """
    last = messages[-1] if messages else None
    return bool(
        last
        and getattr(last, "type", "") == "human"
        and _HOUSEHOLD_SIZE_STATEMENT.search(str(getattr(last, "content", "")))
    )


@trace_node("post_booking_skill")
async def post_booking_skill_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    messages = list(state.get("messages") or [])
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")
    booking_context = state.get("post_booking_context") or {"active": False}
    participant_context = state.get("participant_context") or {"role": "booker"}
    action_result = state.get("action_result")
    if isinstance(action_result, dict) and action_result.get("status") == "confirmed" and action_result.get("booking_id"):
        booking_context = {"active": True, **profile_service.booking_context(str(action_result["booking_id"]))}
        participant_context = {"role": "booker", "booking_id": str(action_result["booking_id"])}
    prompt = (
        f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (POST BOOKING) ---\n{get_post_booking_prompt()}"
        f"\n\n--- USER PROFILE BRIEF ---\n{(state.get('profile_context') or {}).get('brief', 'Profile chưa có dữ liệu.')}"
        f"\n\n--- BOOKING CONTEXT ---\n{json.dumps(booking_context, ensure_ascii=False)}"
        f"\n\n--- CURRENT PARTICIPANT ---\n{json.dumps(participant_context, ensure_ascii=False)}"
        "\n\nFor a driver invitation, you are speaking directly to the authenticated driver named in "
        "BOOKING CONTEXT.participants.driver. Use that identity and the booking details when relevant; "
        "never claim you do not know who the driver is."
    )
    last = messages[-1] if messages else None
    if isinstance(last, ToolMessage):
        trace_event("tool.result", trace_id=trace_id, node="post_booking_skill", tool_message=message_to_log(last))
    try:
        llm = get_llm()
        if llm is None:
            query = str(state.get("query") or "")
            grounded = json.loads(
                search_knowledge.invoke(
                    {"query": query, "model_code": str(booking_context.get("model_code") or "")}, config=config
                )
            )
            facts = grounded.get("facts") or []
            text = facts[0]["content"] if facts else "ViVi có thể giúp bạn chuẩn bị checklist lái thử, đánh giá pin/sạc, ADAS, không gian gia đình và các câu hỏi nên trao đổi với tư vấn viên."
            response = AIMessage(content=text)
        else:
            tool_choice = update_user_profile.name if _requires_profile_capture(messages) else None
            bound = llm.bind_tools(
                [search_knowledge, update_user_profile],
                tool_choice=tool_choice,
            )
            llm_messages = [SystemMessage(content=prompt)] + window_messages(messages)
            trace_event("llm.request", trace_id=trace_id, node="post_booking_skill", messages=messages_to_log(llm_messages), tools=[search_knowledge.name, update_user_profile.name])
            response = await trace_async_operation(
                "llm.post_booking_skill",
                trace_id=trace_id,
                input={
                    "messages": messages_to_log(llm_messages),
                    "tools": [search_knowledge.name, update_user_profile.name],
                },
                awaitable=bound.ainvoke(llm_messages, config=config),
            )
    except Exception as exc:
        logging.getLogger(__name__).exception("Post booking skill failed")
        response = AIMessage(content="ViVi chưa lấy được nguồn thông tin phù hợp lúc này. Bạn có thể hỏi về checklist lái thử, pin/sạc, ADAS hoặc không gian sử dụng.")
        return {"messages": [response], "response": response.content, "error": str(exc), "active_skill": "post_booking", "metadata": metadata}
    content = extract_response_text(response)
    calls = bool(getattr(response, "tool_calls", None))
    return {"messages": [response], "response": content, "active_skill": "post_booking", "post_booking_context": booking_context, "tool_call_count": (state.get("tool_call_count") or 0) + (1 if calls else 0), "metadata": metadata}
