import logging

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.agents.constants import (
    GENERAL_GREETING_KEYWORDS,
    OUT_OF_SCOPE_KEYWORDS,
    SOVEREIGNTY_KEYWORDS,
)
from src.agents.state import AgentState
from src.agents.trace import trace_event
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
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")
    if state.get("requested_action") or context.get("channel") == "booking":
        trace_event(
            "classifier.bypass",
            trace_id=trace_id,
            reason="booking_context_or_action",
            query=query,
            context=context,
        )
        return {
            "intent": "domain",
            "active_skill": "booking",
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": "booking"},
            "tool_call_count": 0,
        }
    if not query:
        trace_event("classifier.empty_query", trace_id=trace_id)
        return {
            "intent": "general",
            "messages": [HumanMessage(content="")],
            "metadata": {**metadata, "sub_intent": "empty_query"},
            "tool_call_count": 0,
        }

    # Check basic keywords as immediate priority bypass for sensitive subjects
    # to avoid LLM hallucinations and save API token cost
    lower_query = query.lower()

    if any(kw in lower_query for kw in SOVEREIGNTY_KEYWORDS):
        trace_event("classifier.keyword_route", trace_id=trace_id, intent="sensitive", sub_intent="sovereignty")
        return {
            "intent": "sensitive",
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": "sovereignty"},
            "tool_call_count": 0,
        }

    if any(kw in lower_query for kw in OUT_OF_SCOPE_KEYWORDS):
        trace_event("classifier.keyword_route", trace_id=trace_id, intent="sensitive", sub_intent="out_of_scope_code")
        return {
            "intent": "sensitive",
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": "out_of_scope_code"},
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
        if llm is None:
            raise RuntimeError("LLM is not configured")
        structured_llm = llm.with_structured_output(RouteSchema)
        trace_event("llm.request", trace_id=trace_id, node="classifier", prompt=prompt)
        result = await structured_llm.ainvoke(prompt)
        from typing import cast

        route_result = cast(RouteSchema, result)
        intent = route_result.intent
        if intent not in {"domain", "general", "sensitive"}:
            intent = "general"

        sub_intent = route_result.sub_intent
        active_skill = "booking" if sub_intent == "booking" else "advise"
        trace_event(
            "llm.response",
            trace_id=trace_id,
            node="classifier",
            intent=intent,
            sub_intent=sub_intent,
            active_skill=active_skill,
        )
        return {
            "intent": intent,
            "active_skill": active_skill,
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": sub_intent},
            "tool_call_count": 0,
        }
    except Exception as e:
        trace_event("llm.error", trace_id=trace_id, node="classifier", error=str(e))
        # Log the specific error for debugging before falling back to keyword classifier
        logger.warning("Classifier LLM call failed (%s: %s), falling back to keyword matching.", type(e).__name__, e)
        if any(kw in lower_query for kw in GENERAL_GREETING_KEYWORDS):
            trace_event("classifier.fallback_route", trace_id=trace_id, intent="general", sub_intent="fallback_general")
            return {
                "intent": "general",
                "messages": [HumanMessage(content=query)],
                "metadata": {**metadata, "sub_intent": "fallback_general"},
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
            trace_event(
                "classifier.fallback_route",
                trace_id=trace_id,
                intent="domain",
                active_skill=active_skill,
                sub_intent="fallback_domain",
            )
            return {
                "intent": "domain",
                "active_skill": active_skill,
                "messages": [HumanMessage(content=query)],
                "metadata": {**metadata, "sub_intent": "fallback_domain"},
                "tool_call_count": 0,
            }
