import logging

from pydantic import BaseModel, Field

from src.agents.constants import (
    GENERAL_GREETING_KEYWORDS,
    OUT_OF_SCOPE_KEYWORDS,
    SOVEREIGNTY_KEYWORDS,
)
from src.agents.state import AgentState
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

    # Check basic keywords as immediate priority bypass for sensitive subjects
    # to avoid LLM hallucinations and save API token cost
    lower_query = query.lower()

    if any(kw in lower_query for kw in SOVEREIGNTY_KEYWORDS):
        return {"intent": "sensitive", "metadata": {**(state.get("metadata") or {}), "sub_intent": "sovereignty"}}

    if any(kw in lower_query for kw in OUT_OF_SCOPE_KEYWORDS):
        return {"intent": "sensitive", "metadata": {**(state.get("metadata") or {}), "sub_intent": "out_of_scope_code"}}

    # Construct prompt for the LLM classifier
    prompt = (
        "You are an Intent Classifier Router for a VinFast Test Drive Assistant. "
        "Your task is to classify the user's input query into one of three intents:\n"
        "1. 'domain': Queries about VinFast electric vehicle models (VF3, VF5, VF7, VF8, VF9, etc.), specifications, pricing, showrooms, or booking/scheduling/cancelling a test drive.\n"
        "2. 'general': Simple greetings ('chào bạn', 'hello'), pleasantries, small talk, or general questions about who you are.\n"
        "3. 'sensitive': Geopolitical questions, national sovereignty questions, or out-of-scope tasks (e.g., requests to write code, program, solve complex math, write essays).\n\n"
        f"User Query: {query}"
    )

    try:
        llm = get_classifier_llm()
        structured_llm = llm.with_structured_output(RouteSchema)
        result = await structured_llm.ainvoke(prompt)
        from typing import cast
        route_result = cast(RouteSchema, result)
        return {"intent": route_result.intent, "metadata": {**(state.get("metadata") or {}), "sub_intent": route_result.sub_intent}}
    except Exception as e:
        # Log the specific error for debugging before falling back to keyword classifier
        logger.warning(
            "Classifier LLM call failed (%s: %s), falling back to keyword matching.", type(e).__name__, e)
        if any(kw in lower_query for kw in GENERAL_GREETING_KEYWORDS):
            return {
                "intent": "general",
                "metadata": {**(state.get("metadata") or {}), "sub_intent": "fallback_general"},
            }
        else:
            return {"intent": "domain", "metadata": {**(state.get("metadata") or {}), "sub_intent": "fallback_domain"}}
