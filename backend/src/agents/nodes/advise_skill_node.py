from pathlib import Path
from typing import Any, cast

from langchain_core.messages import SystemMessage

from src.agents.state import AgentState
from src.agents.tools import search_knowledge
from src.services.llm import get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "advise_skill" / "SKILL.md"
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.md"


def get_advise_prompt() -> str:
    try:
        with open(SKILL_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are the Advisory Assistant. Help users explore VinFast electric vehicle models, specs, range, pricing, and features."


def get_system_prompt() -> str:
    try:
        with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are Vini, the VinFast Test Drive Virtual Assistant."


async def advise_skill_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])

    prompt = f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (ADVISE) ---\n{get_advise_prompt()}"

    llm = get_llm()
    tools = [search_knowledge]
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
