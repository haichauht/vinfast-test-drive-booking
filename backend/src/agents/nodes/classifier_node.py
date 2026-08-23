import logging

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from src.agents.constants import (
    ADVISORY_KEYWORDS,
    BOOKING_CANCEL_KEYWORDS,
    BOOKING_MUTATION_KEYWORDS,
    BOOKING_RESCHEDULE_KEYWORDS,
    LOOKUP_KEYWORDS,
    OUT_OF_SCOPE_KEYWORDS,
    PUBLIC_LLM_UNAVAILABLE_CODE,
    PUBLIC_LLM_UNAVAILABLE_MESSAGE,
    SOVEREIGNTY_KEYWORDS,
)
from src.agents.state import AgentState
from src.agents.trace import trace_event
from src.dependencies import usage_budget_service
from src.services.llm import extract_response_text, get_classifier_llm
from src.services.usage_budget import (
    BudgetExceededError,
    LLMCallLimitExceededError,
    invoke_with_budget,
)

logger = logging.getLogger(__name__)

DRIVER_BOOKING_SCOPE_MESSAGE = (
    "Link này dùng để ViVi hỗ trợ người lái chuẩn bị cho buổi lái thử. "
    "Các thao tác tra cứu, đổi, hủy hoặc cập nhật lịch cần được thực hiện bởi "
    "người đặt lịch qua luồng xác thực booking."
)
_DRIVER_BLOCKED_SUB_INTENTS = frozenset({
    "booking_new", "booking_availability", "booking_reschedule", "booking_cancel",
    "booking_update_details", "booking_update_notifications",
})


def _driver_scope_block(state: AgentState, query: str, *, sub_intent: str) -> dict:
    metadata = state.get("metadata") or {}
    return {
        "intent": "out_of_scope",
        "response": DRIVER_BOOKING_SCOPE_MESSAGE,
        "policy_response": DRIVER_BOOKING_SCOPE_MESSAGE,
        "messages": [HumanMessage(content=query)],
        "metadata": {**metadata, "sub_intent": sub_intent},
        "tool_call_count": 0,
    }


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
            "booking_availability, booking_reschedule, booking_cancel, booking_update_details, "
            "booking_update_notifications, post_booking_advisory, vehicle_info, greeting, "
            "assistant_identity, "
            "out_of_scope, others. If intent is sensitive, use others."
        )
    )
    contact_value: str | None = Field(
        default=None,
        description="Email copied exactly from the user query, or null when no email was provided.",
    )
    has_schedule_preference: bool = Field(
        description=(
            "True when the user states, changes, or asks about a preferred test-drive date, "
            "date range, day, or time, including shorthand such as '28 t mới rảnh'."
        ),
    )


async def classifier_node(state: AgentState) -> dict:
    query = state.get("query", "")
    context = state.get("context") or {}
    metadata = state.get("metadata") or {}
    previous_assistant_message = ""
    for message in reversed(state.get("messages") or []):
        if isinstance(message, AIMessage):
            previous_assistant_message = extract_response_text(message)
            if previous_assistant_message:
                break
    trace_id = metadata.get("trace_id", "")
    previous_skill = state.get("active_skill", "")
    post_booking_active = bool((state.get("post_booking_context") or {}).get("active"))
    is_driver_invitation = (state.get("participant_context") or {}).get("role") == "driver"
    if state.get("requested_action"):
        if is_driver_invitation:
            return _driver_scope_block(state, query, sub_intent="driver_booking_scope")
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
        "- Greetings and questions about ViVi's identity, role, or supported capabilities are "
        "domain. Never classify them as out_of_scope.\n"
        "- When a request is ambiguous but has a reasonable interpretation within the test-drive "
        "journey, prefer domain.\n"
        "\n"
        "For intent=domain, choose exactly one sub_intent:\n"
        "- booking_new\n"
        "- booking_lookup\n"
        "- booking_availability\n"
        "- booking_reschedule\n"
        "- booking_cancel\n"
        "- booking_update_details\n"
        "- booking_update_notifications\n"
        "- post_booking_advisory\n"
        "- vehicle_info\n"
        "- greeting\n"
        "- assistant_identity\n"
        "- others\n"
        "\n"
        "Domain sub-intent rules:\n"
        "- booking_new: create or start a new test-drive booking.\n"
        "- booking_lookup: retrieve or check an existing booking.\n"
        "- booking_availability: check which test-drive dates or times are free.\n"
        "- booking_reschedule: change the booking date, time, or slot.\n"
        "- booking_cancel: cancel an existing booking.\n"
        "- booking_update_details: change participant or booking details.\n"
        "- booking_update_notifications: change booking notification preferences.\n"
        "- post_booking_advisory: after a confirmed booking, guidance that helps the user prepare "
        "for, participate in, or evaluate the upcoming test drive.\n"
        "- vehicle_info: general VinFast vehicle/product questions not specifically tied to "
        "preparing for an already-confirmed test drive.\n"
        "- greeting: a social opening or greeting directed at ViVi, for example 'hi', 'hello', "
        "'xin chào', or 'alo'.\n"
        "- assistant_identity: a question about who ViVi is, ViVi's role, or what ViVi can help "
        "with, for example 'bạn là ai?' or 'ViVi hỗ trợ gì?'.\n"
        "- others: domain requests that do not fit another domain sub_intent.\n"
        "\n"
        "Use booking_lookup when the user wants to view, find, check, or retrieve an existing booking.\n"
        "IMPORTANT: When the user mentions changing/switching a vehicle model (e.g. 'đổi VF8', 'đổi xe VF5', "
        "'chuyển sang VF7', 'xem xe VF3'), classify as booking_new (NOT booking_reschedule). Only use "
        "booking_reschedule when the user explicitly asks to change an existing appointment time/date "
        "('đổi lịch', 'đổi giờ hẹn', 'dời sang buổi chiều', 'chuyển sang ngày mai', "
        "'cho tôi hẹn trễ hơn').\n"
        "\n"
        "Use booking_availability whenever the user asks which dates/times are free or available, "
        "including informal forms such as 'rảnh ngày 25-26', 'ngày 26 27 có lịch không', "
        "'từ 25 đến 30', or 'tuần sau có giờ nào'.\n"
        "CRITICAL AVAILABILITY PRECEDENCE: a statement of when the user is free is an availability "
        "request even when it is not phrased as a question and omits words such as 'ngày' or 'giờ'. "
        "Examples: 'thôi 28 t mới rảnh', 'chắc 27 được á', 'tầm 3 giờ chiều nha', and "
        "'cuối tuần tôi mới đi được' are booking_availability. When UI stage=choose_slot, prefer "
        "booking_availability for any date/time preference refinement; use booking_new only when "
        "the user explicitly starts another booking or changes the vehicle/location. Set "
        "has_schedule_preference=true for these date/time refinements.\n"
        "A user stating a location is a booking request, including casual or missing-accent "
        "Vietnamese such as 't ở hcm', 'tôi đang ở Đà Nẵng', 'ở Quế Sơn', and "
        "'mình ở miền tay'. Classify these as booking_new.\n"
        "A broad region such as miền Bắc/Trung/Nam/Tây still belongs to booking_new; "
        "the booking skill will ask for a province or city.\n"
        "Classify 'hi' as domain/greeting. Classify 'bạn là ai?' and 'bạn hỗ trợ gì?' as "
        "domain/assistant_identity.\n"
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
        f"Confirmed post-booking context active: {post_booking_active}.\n"
        f"Previous active skill: {previous_skill or '(none)'}.\n"
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
        if (
            intent == "domain"
            and context.get("stage") == "choose_slot"
            and not post_booking_active
            and route_result.has_schedule_preference
            and sub_intent in {"booking_new", "booking_reschedule", "others"}
        ):
            trace_event(
                "classifier.route_correction",
                trace_id=trace_id,
                from_sub_intent=sub_intent,
                to_sub_intent="booking_availability",
                reason="schedule_preference_while_choosing_slot",
            )
            sub_intent = "booking_availability"
        if is_driver_invitation and sub_intent in _DRIVER_BLOCKED_SUB_INTENTS:
            return _driver_scope_block(state, query, sub_intent="driver_booking_scope")
        if intent == "domain" and not post_booking_active and sub_intent == "post_booking_advisory":
            intent = "out_of_scope"
            sub_intent = "post_booking_required"
        use_post_booking = intent == "domain" and post_booking_active and (
            sub_intent in {"post_booking_advisory", "vehicle_info"}
            or (is_driver_invitation and sub_intent == "booking_lookup")
        )
        active_skill = "post_booking" if use_post_booking else "booking"
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
        internal_error_code = (
            "LLM_BUDGET_EXCEEDED" if isinstance(e, BudgetExceededError) else "LLM_CALL_LIMIT_EXCEEDED"
        )
        trace_event("llm.limit", trace_id=trace_id, node="classifier", error_code=internal_error_code)
        return {
            "intent": "sensitive",
            "messages": [HumanMessage(content=query)],
            "response": PUBLIC_LLM_UNAVAILABLE_MESSAGE,
            "policy_response": PUBLIC_LLM_UNAVAILABLE_MESSAGE,
            "action_error": PUBLIC_LLM_UNAVAILABLE_CODE,
            "metadata": {**metadata, "sub_intent": "llm_limit"},
            "tool_call_count": 0,
        }
    except Exception as e:
        trace_event("llm.error", trace_id=trace_id, node="classifier", error=str(e))
        # Log the specific error for debugging before falling back to keyword classifier
        logger.warning("Classifier LLM call failed (%s: %s), falling back to keyword matching.", type(e).__name__, e)
        if any(phrase in lower_query for phrase in LOOKUP_KEYWORDS):
            fallback_sub_intent = "booking_lookup"
        elif any(phrase in lower_query for phrase in BOOKING_RESCHEDULE_KEYWORDS):
            fallback_sub_intent = "booking_reschedule"
        elif any(phrase in lower_query for phrase in BOOKING_CANCEL_KEYWORDS):
            fallback_sub_intent = "booking_cancel"
        elif any(phrase in lower_query for phrase in BOOKING_MUTATION_KEYWORDS):
            fallback_sub_intent = "booking_new"
        else:
            fallback_sub_intent = "fallback_domain"
        active_skill = (
            "post_booking"
            if post_booking_active
            and (
                any(phrase in lower_query for phrase in ADVISORY_KEYWORDS)
                or (is_driver_invitation and fallback_sub_intent == "booking_lookup")
            )
            else "booking"
        )
        if is_driver_invitation and fallback_sub_intent in _DRIVER_BLOCKED_SUB_INTENTS:
            return _driver_scope_block(state, query, sub_intent="driver_booking_scope")
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
