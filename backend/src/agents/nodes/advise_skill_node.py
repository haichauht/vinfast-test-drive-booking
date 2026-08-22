import logging
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import SystemMessage, ToolMessage

from src.agents.state import AgentState
from src.agents.tools import search_knowledge
from src.agents.trace import message_to_log, messages_to_log, trace_event
from src.agents.utils import get_system_prompt, window_messages
from src.guardrails.untrusted_content import protect_tool_result_messages
from src.services.llm import get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "advise_skill" / "SKILL.md"


def get_advise_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are the Advisory Assistant. Help users explore VinFast electric vehicle models, specs, range, pricing, and features."


async def advise_skill_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")
    last_message = messages[-1] if messages else None
    if isinstance(last_message, ToolMessage):
        trace_event(
            "tool.result",
            trace_id=trace_id,
            node="advise_skill",
            tool_message=message_to_log(last_message),
            failed=getattr(last_message, "status", "success") == "error",
        )

    prompt = f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (ADVISE) ---\n{get_advise_prompt()}"

    tools = [search_knowledge]

    try:
        llm = get_llm()
        if llm is None:
            raise RuntimeError("LLM is not configured")
        llm_with_tools = llm.bind_tools(tools)
        safe_history = protect_tool_result_messages(window_messages(messages))
        llm_messages = [SystemMessage(content=prompt), *safe_history]
        trace_event(
            "llm.request",
            trace_id=trace_id,
            node="advise_skill",
            tools=[tool.name for tool in tools],
            messages=messages_to_log(llm_messages),
        )
        response = await llm_with_tools.ainvoke(llm_messages)
    except Exception as e:
        trace_event("llm.error", trace_id=trace_id, node="advise_skill", error=str(e))
        logging.getLogger(__name__).exception("Error in advise_skill_node")
        from langchain_core.messages import AIMessage

        safe_response = AIMessage(content="Đã xảy ra lỗi khi kết nối với mô hình AI. Vui lòng thử lại sau.")
        return {
            "messages": [safe_response],
            "response": safe_response.content,
            "error": str(e),
        }

    # Extract response text for the API
    response_content = cast(str, response.content) if hasattr(response, "content") else ""

    # Tăng tool_call_count nếu LLM đang gọi tool
    has_tool_calls = hasattr(response, "tool_calls") and bool(response.tool_calls)
    current_count = state.get("tool_call_count") or 0
    trace_event(
        "llm.response",
        trace_id=trace_id,
        node="advise_skill",
        message=message_to_log(response),
        has_tool_calls=has_tool_calls,
    )
    if has_tool_calls:
        for tool_call in response.tool_calls:
            trace_event(
                "tool.call",
                trace_id=trace_id,
                node="advise_skill",
                source="llm",
                tool=tool_call.get("name"),
                args=tool_call.get("args"),
                tool_call_id=tool_call.get("id"),
            )

    output: dict[str, Any] = {
        "messages": [response],
        "tool_call_count": current_count + 1 if has_tool_calls else current_count,
    }
    if response_content:
        output["response"] = response_content

    return output
