import logging

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.agents.constants import (
    ADVISORY_KEYWORDS,
    BOOKING_MUTATION_KEYWORDS,
    LOOKUP_KEYWORDS,
    OUT_OF_SCOPE_KEYWORDS,
    SOVEREIGNTY_KEYWORDS,
)
from src.agents.state import AgentState
from src.agents.trace import trace_event
from src.dependencies import usage_budget_service
from src.services.llm import get_classifier_llm
from src.services.usage_budget import (
    BudgetExceededError,
    LLMCallLimitExceededError,
    invoke_with_budget,
)

logger = logging.getLogger(__name__)


class RouteSchema(BaseModel):
    intent: str = Field(
        description="The classified intent of the user. Must be one of: 'domain' or 'sensitive'"
    )
    sub_intent: str = Field(
        description=(
            "Detailed classification. Must be one of: booking_new, booking_lookup, "
            "booking_reschedule, booking_cancel, booking_update_details, "
            "booking_update_notifications, vehicle_info, sovereignty, "
            "out_of_scope_code, out_of_scope_math, others"
        )
    )
    contact_value: str | None = Field(
        default=None,
        description="Email copied exactly from the user query, or null when no email was provided.",
    )


async def classifier_node(state: AgentState) -> dict:
    query = state.get("query", "")
    context = state.get("context") or {}
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")
    previous_skill = state.get("active_skill", "")
    post_booking_active = bool((state.get("post_booking_context") or {}).get("active"))
    if state.get("requested_action"):
        trace_event(
            "classifier.bypass",
            trace_id=trace_id,
            reason="structured_action",
            query=query,
            context=context,
        )
        return {
            "intent": "domain",
            "active_skill": "booking",
            "previous_active_skill": previous_skill,
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": "booking"},
            "tool_call_count": 0,
        }
    if not query:
        trace_event("classifier.empty_query", trace_id=trace_id)
        return {
            "intent": "domain",
            "active_skill": "booking",
            "previous_active_skill": previous_skill,
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
        return {"intent": "sensitive", "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "out_of_scope_code"}, "tool_call_count": 0}

    if any(kw in lower_query for kw in BOOKING_MUTATION_KEYWORDS):
        return {"intent": "domain", "active_skill": "booking", "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "booking"}, "tool_call_count": 0}
    if any(kw in lower_query for kw in ADVISORY_KEYWORDS):
        active_skill = "post_booking" if post_booking_active else "booking"
        return {"intent": "domain", "active_skill": active_skill, "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "vehicle_info"}, "tool_call_count": 0}
    if any(phrase in lower_query for phrase in ("xin chào", "chào bạn", "hello", "hi ")):
        return {"intent": "domain", "active_skill": "booking", "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "greeting"}, "tool_call_count": 0}
    if post_booking_active and previous_skill == "post_booking" and len(query.split()) <= 8:
        return {"intent": "domain", "active_skill": "post_booking", "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "contextual_followup"}, "tool_call_count": 0}

    # Construct prompt for the LLM classifier dynamically based on system_prompt.md
    prompt = (
        "You classify requests for a VinFast test-drive assistant.\n"
        "Return intent=domain for vehicle and booking requests, or intent=sensitive for unsafe/out-of-scope requests.\n"
        "Choose exactly one sub_intent: booking_new, booking_lookup, booking_reschedule, booking_cancel, "
        "booking_update_details, booking_update_notifications, vehicle_info, sovereignty, "
        "out_of_scope_code, out_of_scope_math, others.\n"
        "Use booking_lookup when the user wants to view, find, check, or retrieve an existing booking.\n"
        "If the query contains an email, copy it exactly to contact_value. Otherwise return null. "
        "Never invent contact_value.\n"
        f"UI context: channel={context.get('channel', '')}, stage={context.get('stage', '')}.\n"
        f"User query: {query}"
    )

    try:
        llm = get_classifier_llm()
        if llm is None:
            raise RuntimeError("LLM is not configured")
        structured_llm = llm.with_structured_output(RouteSchema)
        trace_event("llm.request", trace_id=trace_id, node="classifier", prompt=prompt)
        result = await invoke_with_budget(
            structured_llm,
            prompt,
            model=getattr(llm, "model_name", "") or "classifier",
            metadata=metadata,
            budget=usage_budget_service,
            call_purpose="classifier",
        )
        from typing import cast

        route_result = cast(RouteSchema, result)
        intent = route_result.intent
        if intent not in {"domain", "sensitive"}:
            intent = "domain"

        sub_intent = route_result.sub_intent
        # This public MVP only exposes booking. Keep the detailed sub-intent
        # for OTP/workflow handling, but do not route normal requests to the
        # unfinished advisory skill.
        active_skill = "post_booking" if post_booking_active and sub_intent == "vehicle_info" else "booking"
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
            "previous_active_skill": previous_skill,
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": sub_intent},
            "intent_entities": {"contact_value": route_result.contact_value},
            "tool_call_count": 0,
        }
    except (BudgetExceededError, LLMCallLimitExceededError) as e:
        error_code = "LLM_BUDGET_EXCEEDED" if isinstance(e, BudgetExceededError) else "LLM_CALL_LIMIT_EXCEEDED"
        safe_response = (
            "Hệ thống đã đạt giới hạn chi phí AI trong hôm nay. Vui lòng thử lại sau."
            if isinstance(e, BudgetExceededError)
            else "Yêu cầu này cần quá nhiều lượt xử lý AI. Vui lòng gửi lại yêu cầu ngắn gọn hơn."
        )
        trace_event("llm.limit", trace_id=trace_id, node="classifier", error_code=error_code)
        return {
            "intent": "sensitive",
            "messages": [HumanMessage(content=query)],
            "response": safe_response,
            "policy_response": safe_response,
            "action_error": error_code,
            "metadata": {**metadata, "sub_intent": "llm_limit"},
            "tool_call_count": 0,
        }
    except Exception as e:
        trace_event("llm.error", trace_id=trace_id, node="classifier", error=str(e))
        # Log the specific error for debugging before falling back to keyword classifier
        logger.warning("Classifier LLM call failed (%s: %s), falling back to keyword matching.", type(e).__name__, e)
        active_skill = (
            "post_booking"
            if post_booking_active and any(phrase in lower_query for phrase in ADVISORY_KEYWORDS)
            else "booking"
        )
        fallback_sub_intent = (
            "booking_lookup" if any(phrase in lower_query for phrase in LOOKUP_KEYWORDS) else "fallback_domain"
        )
        trace_event(
            "classifier.fallback_route",
            trace_id=trace_id,
            intent="domain",
            active_skill=active_skill,
            sub_intent=fallback_sub_intent,
        )
        return {
            "intent": "domain",
            "active_skill": active_skill,
            "previous_active_skill": previous_skill,
            "messages": [HumanMessage(content=query)],
            "metadata": {**metadata, "sub_intent": fallback_sub_intent},
            "tool_call_count": 0,
        }
