from pathlib import Path
from typing import Any, cast

from langchain_core.messages import SystemMessage

from src.agents.state import AgentState
from src.agents.tools import (
    get_booking_details,
    get_booking_draft,
    request_booking_access,
    search_test_drive_options,
    update_booking_draft,
    verify_booking_access,
)
from src.agents.utils import get_system_prompt
from src.services.llm import get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "booking_skill" / "SKILL.md"


def get_booking_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are the Booking Assistant. Help users search, update, verify and confirm test drive bookings."


async def booking_skill_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])

    prompt = f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (BOOKING) ---\n{get_booking_prompt()}"

    llm = get_llm()
    tools = [
        search_test_drive_options,
        get_booking_draft,
        update_booking_draft,
        request_booking_access,
        verify_booking_access,
        get_booking_details,
    ]
    llm_with_tools = llm.bind_tools(tools)

    response = await llm_with_tools.ainvoke([SystemMessage(content=prompt)] + messages)

    # Extract response text for the API
    response_content = cast(str, response.content) if hasattr(response, "content") else ""

    output: dict[str, Any] = {
        "messages": [response],
    }
    if response_content:
        output["response"] = response_content

    return output
