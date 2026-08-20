import logging

from langchain_core.messages import AIMessage, HumanMessage
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
        description=(
            "The classified intent of the user. Must be one of: 'domain', 'out_of_scope', "
            "or 'sensitive'."
        )
    )
    sub_intent: str = Field(
        description=(
            "Detailed classification. Must be one of: booking_new, booking_lookup, "
            "booking_reschedule, booking_cancel, booking_update_details, "
            "booking_update_notifications, post_booking_advisory, vehicle_info, "
            "out_of_scope, others. If intent is sensitive, use others."
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
    previous_assistant_message = ""
    for message in reversed(state.get("messages") or []):
        if isinstance(message, AIMessage) and isinstance(message.content, str) and message.content.strip():
            previous_assistant_message = message.content.strip()
            break
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
        if not post_booking_active:
            return {"intent": "out_of_scope", "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "out_of_scope"}, "tool_call_count": 0}
        active_skill = "post_booking"
        return {"intent": "domain", "active_skill": active_skill, "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "vehicle_info"}, "tool_call_count": 0}
    if any(phrase in lower_query for phrase in ("xin chào", "chào bạn", "hello", "hi ")):
        return {"intent": "domain", "active_skill": "booking", "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "greeting"}, "tool_call_count": 0}
    if post_booking_active and previous_skill == "post_booking" and len(query.split()) <= 8:
        return {"intent": "domain", "active_skill": "post_booking", "previous_active_skill": previous_skill, "messages": [HumanMessage(content=query)], "metadata": {**metadata, "sub_intent": "contextual_followup"}, "tool_call_count": 0}

    # Construct prompt for the LLM classifier dynamically based on system_prompt.md
    prompt = (
        "You classify requests for a VinFast test-drive assistant.\n"
        "\n"
        "Choose exactly one intent:\n"
        "- domain: the request is meaningfully related to VinFast vehicles, test-drive booking, "
        "booking management, test-drive preparation, vehicle evaluation, or support surrounding "
        "the user's test-drive journey.\n"
        "- out_of_scope: the request is unrelated to the responsibilities of a VinFast test-drive "
        "assistant and does not require safety-sensitive handling.\n"
        "- sensitive: the request requires safety or policy-sensitive handling, such as requests "
        "involving harmful or dangerous activity, illegal wrongdoing, privacy abuse, credentials "
        "or secrets, or other content that should not be handled as a normal domain request.\n"
        "\n"
        "Important boundaries:\n"
        "- Never classify a request as sensitive merely because it is unfamiliar, ambiguous, "
        "unsupported, or outside the assistant's domain.\n"
        "- A benign unrelated request is out_of_scope, not sensitive.\n"
        "- A request related to the user's test-drive journey is domain even when it is not a "
        "booking transaction.\n"
        "- When a request is ambiguous but has a reasonable interpretation within the test-drive "
        "journey, prefer domain.\n"
        "\n"
        "For intent=domain, choose exactly one sub_intent:\n"
        "- booking_new\n"
        "- booking_lookup\n"
        "- booking_reschedule\n"
        "- booking_cancel\n"
        "- booking_update_details\n"
        "- booking_update_notifications\n"
        "- post_booking_advisory\n"
        "- vehicle_info\n"
        "- others\n"
        "\n"
        "Domain sub-intent rules:\n"
        "- booking_new: create or start a new test-drive booking.\n"
        "- booking_lookup: retrieve or check an existing booking.\n"
        "- booking_reschedule: change the booking date, time, or slot.\n"
        "- booking_cancel: cancel an existing booking.\n"
        "- booking_update_details: change participant or booking details.\n"
        "- booking_update_notifications: change booking notification preferences.\n"
        "- post_booking_advisory: after a confirmed booking, guidance that helps the user prepare "
        "for, participate in, or evaluate the upcoming test drive.\n"
        "- vehicle_info: general VinFast vehicle/product questions not specifically tied to "
        "preparing for an already-confirmed test drive.\n"
        "- others: domain requests that do not fit another domain sub_intent.\n"
        "\n"
        "Use UI context as supporting evidence, not as a replacement for the user's request. "
        "A successful/confirmed booking makes post_booking_advisory more likely for subsequent "
        "test-drive-related guidance, unless the user is clearly requesting another booking action.\n"
        "\n"
        "If intent is out_of_scope, use sub_intent=out_of_scope. If intent is sensitive, use sub_intent=others.\n"
        "\n"
        "If the query contains an email, copy it exactly to contact_value. "
        "Otherwise return null. Never invent contact_value.\n"
        "\n"
        f"UI context: channel={context.get('channel', '')}, "
        f"stage={context.get('stage', '')}.\n"
        f"Previous ViVi message: {previous_assistant_message or '(none)'}\n"
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
        if intent not in {"domain", "out_of_scope", "sensitive"}:
            intent = "domain"

        sub_intent = route_result.sub_intent
        if intent == "domain" and not post_booking_active and sub_intent in {"post_booking_advisory", "vehicle_info"}:
            intent = "out_of_scope"
            sub_intent = "out_of_scope"
        active_skill = (
            "post_booking"
            if (
                intent == "domain"
                and post_booking_active
                and sub_intent in {"post_booking_advisory", "vehicle_info"}
            )
            else "booking"
        )
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
