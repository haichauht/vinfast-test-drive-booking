from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import cast

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from src.agents.state import AgentState
from src.agents.tools import search_knowledge, update_user_profile
from src.agents.trace import message_to_log, messages_to_log, trace_event
from src.agents.utils import get_system_prompt, window_messages
from src.dependencies import profile_service
from src.services.llm import get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "post_booking_skill" / "SKILL.md"


def get_post_booking_prompt() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


async def post_booking_skill_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")
    booking_context = state.get("post_booking_context") or {"active": False}
    action_result = state.get("action_result")
    if isinstance(action_result, dict) and action_result.get("status") == "confirmed" and action_result.get("booking_id"):
        booking_context = {"active": True, **profile_service.booking_context(str(action_result["booking_id"]))}
    prompt = (
        f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (POST BOOKING) ---\n{get_post_booking_prompt()}"
        f"\n\n--- USER PROFILE BRIEF ---\n{(state.get('profile_context') or {}).get('brief', 'Profile chưa có dữ liệu.')}"
        f"\n\n--- BOOKING CONTEXT ---\n{json.dumps(booking_context, ensure_ascii=False)}"
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
                    {"query": query, "model_code": str(booking_context.get("model_code") or "")}
                )
            )
            facts = grounded.get("facts") or []
            text = facts[0]["content"] if facts else "ViVi có thể giúp bạn chuẩn bị checklist lái thử, đánh giá pin/sạc, ADAS, không gian gia đình và các câu hỏi nên trao đổi với tư vấn viên."
            response = AIMessage(content=text)
        else:
            bound = llm.bind_tools([search_knowledge, update_user_profile])
            llm_messages = [SystemMessage(content=prompt)] + window_messages(messages)
            trace_event("llm.request", trace_id=trace_id, node="post_booking_skill", messages=messages_to_log(llm_messages), tools=[search_knowledge.name, update_user_profile.name])
            response = await bound.ainvoke(llm_messages)
    except Exception as exc:
        logging.getLogger(__name__).exception("Post booking skill failed")
        response = AIMessage(content="ViVi chưa lấy được nguồn thông tin phù hợp lúc này. Bạn có thể hỏi về checklist lái thử, pin/sạc, ADAS hoặc không gian sử dụng.")
        return {"messages": [response], "response": response.content, "error": str(exc), "active_skill": "post_booking", "metadata": metadata}
    content = cast(str, response.content) if isinstance(response.content, str) else ""
    calls = bool(getattr(response, "tool_calls", None))
    return {"messages": [response], "response": content, "active_skill": "post_booking", "post_booking_context": booking_context, "tool_call_count": (state.get("tool_call_count") or 0) + (1 if calls else 0), "metadata": metadata}
