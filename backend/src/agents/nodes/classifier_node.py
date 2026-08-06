import logging

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.agents.constants import (
    GENERAL_GREETING_KEYWORDS,
    OUT_OF_SCOPE_KEYWORDS,
    SOVEREIGNTY_KEYWORDS,
)
from src.agents.state import AgentState
from src.agents.utils import get_system_prompt
from src.services.llm import get_classifier_llm

logger = logging.getLogger(__name__)


class RouteSchema(BaseModel):
    intent: str = Field(
        description="The classified intent of the user. Must be one of: 'domain', 'general', 'sensitive'"
    )
    sub_intent: str = Field(
        description="Detailed classification. e.g., 'booking', 'vehicle_info', 'small_talk', 'sovereignty', 'out_of_scope_code', 'out_of_scope_math', 'others'"
    )


async def classifier_node(state: AgentState) -> dict:
    query = state.get("query", "")
    context = state.get("context") or {}
    if state.get("requested_action") or context.get("channel") == "booking":
        return {
            "intent": "domain",
            "active_skill": "booking",
            "messages": [HumanMessage(content=query)],
            "metadata": {**(state.get("metadata") or {}), "sub_intent": "booking"},
            "tool_call_count": 0,
        }
    if not query:
        return {
            "intent": "general",
            "messages": [HumanMessage(content="")],
            "metadata": {**(state.get("metadata") or {}), "sub_intent": "empty_query"},
            "tool_call_count": 0,
        }

    # Check basic keywords as immediate priority bypass for sensitive subjects
    # to avoid LLM hallucinations and save API token cost
    lower_query = query.lower()

    if any(kw in lower_query for kw in SOVEREIGNTY_KEYWORDS):
        return {
            "intent": "sensitive",
            "messages": [HumanMessage(content=query)],
            "metadata": {**(state.get("metadata") or {}), "sub_intent": "sovereignty"},
            "tool_call_count": 0,
        }

    if any(kw in lower_query for kw in OUT_OF_SCOPE_KEYWORDS):
        return {
            "intent": "sensitive",
            "messages": [HumanMessage(content=query)],
            "metadata": {**(state.get("metadata") or {}), "sub_intent": "out_of_scope_code"},
            "tool_call_count": 0,
        }

    # Construct prompt for the LLM classifier dynamically based on system_prompt.md
    prompt = (
        "You are an Intent Classifier Router for a VinFast Test Drive Assistant.\n"
        "Your task is to classify the user's input query into one of three intents (domain, general, sensitive) "
        "and determine the sub_intent based on the system instructions below.\n\n"
        "--- SYSTEM INSTRUCTIONS ---\n"
        f"{get_system_prompt()}\n\n"
        f"User Query: {query}"
    )

    try:
        llm = get_classifier_llm()
        structured_llm = llm.with_structured_output(RouteSchema)
        result = await structured_llm.ainvoke(prompt)
        from typing import cast

        route_result = cast(RouteSchema, result)
        intent = route_result.intent
        if intent not in {"domain", "general", "sensitive"}:
            intent = "general"

        sub_intent = route_result.sub_intent
        active_skill = "booking" if sub_intent == "booking" else "advise"
        return {
            "intent": intent,
            "active_skill": active_skill,
            "messages": [HumanMessage(content=query)],
            "metadata": {**(state.get("metadata") or {}), "sub_intent": sub_intent},
            "tool_call_count": 0,
        }
    except Exception as e:
        # Log the specific error for debugging before falling back to keyword classifier
        logger.warning("Classifier LLM call failed (%s: %s), falling back to keyword matching.", type(e).__name__, e)
        if any(kw in lower_query for kw in GENERAL_GREETING_KEYWORDS):
            return {
                "intent": "general",
                "messages": [HumanMessage(content=query)],
                "metadata": {**(state.get("metadata") or {}), "sub_intent": "fallback_general"},
                "tool_call_count": 0,
            }
        else:
            active_skill = (
                "booking"
                if any(
                    kw in lower_query for kw in ["đặt lịch", "lái thử", "booking", "lịch hẹn", "hủy lịch", "dời lịch"]
                )
                else "advise"
            )
            return {
                "intent": "domain",
                "active_skill": active_skill,
                "messages": [HumanMessage(content=query)],
                "metadata": {**(state.get("metadata") or {}), "sub_intent": "fallback_domain"},
                "tool_call_count": 0,
            }
