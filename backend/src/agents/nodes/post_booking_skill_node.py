import json
import logging
import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.agents.tools import search_knowledge, update_post_booking_signals
from src.agents.trace import message_to_log, messages_to_log, trace_async_operation, trace_event, trace_node
from src.agents.utils import get_system_prompt, window_messages
from src.dependencies import profile_service
from src.services.llm import extract_response_text, get_llm

SKILL_PATH = Path(__file__).parent.parent / "skills" / "post_booking_skill" / "SKILL.md"
_HOUSEHOLD_SIZE_STATEMENT = re.compile(
    r"\b(?:gia\s+đình|nhà)\s+(?:của\s+)?(?:tôi|mình|em|anh|chị|ta)?\s*"
    r"(?:có|gồm)\s+\d+\s+(?:người|thành\s+viên)\b",
    re.IGNORECASE,
)
_POST_BOOKING_SIGNAL_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:gia dinh|nha)\b.{0,45}\b(?:co|gom)\b.{0,15}\b(?:nguoi|thanh vien)\b",
        r"\b(?:chong|vo|con|con trai|con gai|be|em be|tre em|bo|me|ong|ba)\b.{0,80}\b(?:di cung|tham gia|den lai thu)\b",
        r"\b(?:chong|vo|toi|minh|anh|chi|nguoi di cung)\b.{0,70}\b(?:lai thu|lai xe)\b",
        r"\b(?:muc dich su dung|nhu cau su dung|dung xe chu yeu|su dung xe chinh)\b",
        r"\b(?:toi|minh|em|anh|chi)\b.{0,35}\b(?:moi co bang|moi lay bang|chua co kinh nghiem lai)\b",
        r"\b(?:toi noi nham|noi nham|sua lai|dinh chinh|khong di nua|khong tham gia nua|khong lai nua)\b",
    )
)
_FOLLOW_UPS_BLOCK = re.compile(r"<<<FOLLOW_UPS>>>\s*(\[.*?\])\s*<<<END_FOLLOW_UPS>>>", re.DOTALL)
_TEST_DRIVE_TERMS = ("lái thử", "lai thu", "buổi lái", "buoi lai", "kiểm tra", "kiem tra")


def _extract_follow_ups(content: str) -> tuple[str, list[dict[str, str]]]:
    """Remove the model-only block and retain exactly two valid exploration prompts."""
    match = _FOLLOW_UPS_BLOCK.search(content)
    visible_content = _FOLLOW_UPS_BLOCK.sub("", content).strip()
    if not match:
        return visible_content, []
    try:
        raw_items = json.loads(match.group(1))
    except json.JSONDecodeError:
        return visible_content, []
    if not isinstance(raw_items, list):
        return visible_content, []

    follow_ups: list[dict[str, str]] = []
    seen_texts: set[str] = set()
    for item in raw_items:
        text = " ".join(str(item).split()) if isinstance(item, str) else ""
        text_key = text.casefold()
        if not 1 <= len(text) <= 240 or text_key in seen_texts or "?" in text:
            continue
        follow_ups.append({"text": text})
        seen_texts.add(text_key)
        if len(follow_ups) == 2:
            break
    return visible_content, follow_ups if len(follow_ups) == 2 else []


def get_post_booking_prompt() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _folded_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold()).replace("đ", "d")
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character)).split()
    )


def _requires_profile_capture(messages: Sequence[object]) -> bool:
    """Identify explicit, durable statements that must not be answered without capture.

    The skill prompt governs general capture. This narrow gate protects a common,
    high-value correction such as "gia đình tôi có 4 người" from being skipped
    when the model prioritizes a knowledge-search tool for the same turn.
    """
    last = messages[-1] if messages else None
    if not last or getattr(last, "type", "") != "human":
        return False
    content = str(getattr(last, "content", ""))
    if _HOUSEHOLD_SIZE_STATEMENT.search(content):
        return True
    folded = _folded_text(content)
    return any(pattern.search(folded) for pattern in _POST_BOOKING_SIGNAL_PATTERNS)


def _last_user_text(messages: Sequence[object]) -> str:
    for message in reversed(messages):
        if getattr(message, "type", "") == "human":
            return str(getattr(message, "content", "")).strip()
    return ""


def _normalized_text(value: str) -> str:
    return re.sub(r"\W+", "", value, flags=re.UNICODE).casefold()


def _tool_call_prose_before(messages: Sequence[object]) -> str:
    """Recover prose emitted alongside a tool call when its continuation is empty."""
    for message in reversed(messages[:-1]):
        if isinstance(message, AIMessage) and getattr(message, "tool_calls", None):
            prose, _ = _extract_follow_ups(extract_response_text(message))
            return prose
    return ""


def _profile_update_failure(message: object) -> str | None:
    if not isinstance(message, ToolMessage) or getattr(message, "name", "") != update_post_booking_signals.name:
        return None
    try:
        payload = json.loads(str(message.content))
    except (TypeError, json.JSONDecodeError):
        return None
    status = str(payload.get("status") or "") if isinstance(payload, dict) else ""
    if status == "unavailable":
        return "ViVi chưa lưu được thông tin này do hệ thống lưu hồ sơ đang tạm gián đoạn. Vui lòng thử lại sau."
    if status == "skipped":
        return "ViVi chưa xác định đủ dữ liệu để lưu thông tin này. Bạn vui lòng nói rõ thông tin cần ghi nhận cho buổi lái thử."
    return None


def _knowledge_fact_score(fact: dict, user_text: str) -> int:
    normalized_user = _normalized_text(user_text)
    searchable = _normalized_text(
        " ".join(str(fact.get(key) or "") for key in ("topic", "title", "content"))
    )
    words = {
        _normalized_text(word)
        for word in re.findall(r"\w+", user_text, flags=re.UNICODE)
        if len(_normalized_text(word)) > 1
    }
    score = sum(2 for word in words if word and word in searchable)
    topic = _normalized_text(str(fact.get("topic") or ""))
    if ("bảohành" in normalized_user or "warranty" in normalized_user) and topic == "ownershipwarranty":
        score += 25
    scope = fact.get("scope") or {}
    models = scope.get("models") or [] if isinstance(scope, dict) else []
    if any(_normalized_text(str(model)) in normalized_user for model in models):
        score += 20
    return score


def _render_grounded_knowledge_response(message: object, user_text: str) -> str | None:
    """Render review-pending knowledge without adding model-authored facts."""
    if not isinstance(message, ToolMessage) or getattr(message, "name", "") != search_knowledge.name:
        return None
    try:
        payload = json.loads(str(message.content))
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None

    facts = [fact for fact in payload.get("facts") or [] if isinstance(fact, dict) and fact.get("content")]
    if not facts:
        return (
            "Kho kiến thức chưa trả về thông tin đủ căn cứ cho câu hỏi này. "
            "Quý khách nên xác nhận trực tiếp với showroom hoặc nguồn VinFast chính thức trước khi sử dụng thông tin."
        )

    fact = max(facts, key=lambda candidate: _knowledge_fact_score(candidate, user_text))
    source = str(fact.get("source") or fact.get("publisher") or "nguồn VinFast chính thức").strip()
    content = str(fact["content"]).strip()
    source_uri = str(fact.get("source_uri") or "").strip()
    parts = [f"Theo {source}: {content}"]
    if source_uri:
        parts.append(f"Nguồn tham khảo: {source_uri}")
    if payload.get("review_warning"):
        parts.append(
            "Dữ liệu này đang chờ rà soát nội bộ; hãy xác nhận điều khoản hiện hành và đúng phiên bản xe "
            "với showroom trước khi quyết định."
        )

    normalized_user = _normalized_text(user_text)
    if any(_normalized_text(term) in normalized_user for term in _TEST_DRIVE_TERMS):
        parts.append(
            "Trong buổi lái thử, nên tự đánh giá phản hồi chân ga và phanh, độ êm và tiếng ồn, "
            "tầm nhìn khi đỗ xe, vị trí ngồi và không gian sử dụng; đồng thời đề nghị nhân viên "
            "chỉ rõ điều khoản bảo hành áp dụng cho chiếc xe được lái thử."
        )
    else:
        parts.append("Ưu tiên đối chiếu nội dung trên với đúng phiên bản xe và nhu cầu sử dụng thực tế.")
    return "\n\n".join(parts)


@trace_node("post_booking_skill")
async def post_booking_skill_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    messages = list(state.get("messages") or [])
    metadata = state.get("metadata") or {}
    trace_id = metadata.get("trace_id", "")
    booking_context = state.get("post_booking_context") or {"active": False}
    participant_context = state.get("participant_context") or {"role": "booker"}
    action_result = state.get("action_result")
    if (
        isinstance(action_result, dict)
        and action_result.get("status") == "confirmed"
        and action_result.get("booking_id")
    ):
        booking_context = {"active": True, **profile_service.booking_context(str(action_result["booking_id"]))}
        participant_context = profile_service.participant_context(str(action_result["booking_id"]), "booker")
    prompt = (
        f"{get_system_prompt()}\n\n--- ACTIVE SKILL GUIDELINES (POST BOOKING) ---\n{get_post_booking_prompt()}"
        f"\n\n--- USER PROFILE BRIEF ---\n{(state.get('profile_context') or {}).get('brief', 'Profile chưa có dữ liệu.')}"
        f"\n\n--- BOOKING CONTEXT ---\n{json.dumps(booking_context, ensure_ascii=False)}"
        f"\n\n--- CURRENT PARTICIPANT ---\n{json.dumps(participant_context, ensure_ascii=False)}"
        "\n\nFor a driver invitation, you are speaking directly to the authenticated driver named in "
        "BOOKING CONTEXT.participants.driver. Use that identity and the booking details when relevant; "
        "never claim you do not know who the driver is."
    )
    last = messages[-1] if messages else None
    if isinstance(last, ToolMessage):
        trace_event("tool.result", trace_id=trace_id, node="post_booking_skill", tool_message=message_to_log(last))
        update_failure = _profile_update_failure(last)
        if update_failure:
            response = AIMessage(content=update_failure)
            return {
                "messages": [response],
                "response": update_failure,
                "active_skill": "post_booking",
                "post_booking_context": booking_context,
                "metadata": metadata,
            }
    try:
        llm = get_llm()
        grounded_knowledge_response = _render_grounded_knowledge_response(last, _last_user_text(messages))
        if grounded_knowledge_response is not None:
            response = AIMessage(content=grounded_knowledge_response)
        elif llm is None:
            query = str(state.get("query") or "")
            grounded = json.loads(
                search_knowledge.invoke(
                    {"query": query, "model_code": str(booking_context.get("model_code") or "")}, config=config
                )
            )
            facts = grounded.get("facts") or []
            text = (
                facts[0]["content"]
                if facts
                else "ViVi có thể giúp bạn chuẩn bị checklist lái thử, đánh giá pin/sạc, ADAS, không gian gia đình và các câu hỏi nên trao đổi với tư vấn viên."
            )
            response = AIMessage(content=text)
        else:
            tool_choice = update_post_booking_signals.name if _requires_profile_capture(messages) else None
            bound = llm.bind_tools(
                [search_knowledge, update_post_booking_signals],
                tool_choice=tool_choice,
            )
            continuation_instruction = ""
            if isinstance(last, ToolMessage):
                continuation_instruction = (
                    "\n\nThe tool result has just been received. Your earlier draft was not sent to the user. "
                    "Now return one complete user-visible answer: useful information, a practical recommendation, "
                    "and only then any eligible follow-up transport block. Never return only the transport block."
                )
            llm_messages = [SystemMessage(content=prompt + continuation_instruction)] + window_messages(messages)
            trace_event(
                "llm.request",
                trace_id=trace_id,
                node="post_booking_skill",
                messages=messages_to_log(llm_messages),
                tools=[search_knowledge.name, update_post_booking_signals.name],
            )
            response = await trace_async_operation(
                "llm.post_booking_skill",
                trace_id=trace_id,
                input={
                    "messages": messages_to_log(llm_messages),
                    "tools": [search_knowledge.name, update_post_booking_signals.name],
                },
                awaitable=bound.ainvoke(llm_messages, config=config),
            )
    except Exception as exc:
        logging.getLogger(__name__).exception("Post booking skill failed")
        response = AIMessage(
            content="ViVi chưa lấy được nguồn thông tin phù hợp lúc này. Bạn có thể hỏi về checklist lái thử, pin/sạc, ADAS hoặc không gian sử dụng."
        )
        return {
            "messages": [response],
            "response": response.content,
            "error": str(exc),
            "active_skill": "post_booking",
            "metadata": metadata,
        }
    content = extract_response_text(response)
    calls = bool(getattr(response, "tool_calls", None))
    visible_content, follow_ups = _extract_follow_ups(content)
    if not calls and not visible_content and isinstance(last, ToolMessage):
        visible_content = _tool_call_prose_before(messages)
        if visible_content:
            response = AIMessage(content=visible_content)

    last_user_text = _last_user_text(messages)
    if (
        not calls
        and llm is not None
        and (not visible_content or _normalized_text(visible_content) == _normalized_text(last_user_text))
    ):
        repair_messages = [
            SystemMessage(
                content=(
                    prompt + "\n\nReturn a complete post-booking advisory answer to the latest user message. "
                    "The previous draft merely repeated the user's words and must not be shown. "
                    "Do not call tools in this repair response."
                )
            ),
            *window_messages(messages),
        ]
        response = await trace_async_operation(
            "llm.post_booking_skill_repair",
            trace_id=trace_id,
            input={"messages": messages_to_log(repair_messages)},
            awaitable=llm.ainvoke(repair_messages, config=config),
        )
        content = extract_response_text(response)
        visible_content, follow_ups = _extract_follow_ups(content)
        if not visible_content:
            visible_content = (
                "ViVi cần thêm một chút thông tin về nhu cầu sử dụng để gợi ý đúng các bài kiểm tra cho buổi lái thử."
            )
            response = AIMessage(content=visible_content)
    if not calls and visible_content != content:
        # Do not retain transport instructions in the conversation history.
        response = AIMessage(content=visible_content)
    result = {
        "messages": [response],
        "response": visible_content,
        "active_skill": "post_booking",
        "post_booking_context": booking_context,
        "tool_call_count": (state.get("tool_call_count") or 0) + (1 if calls else 0),
        "metadata": metadata,
    }
    # Tool-call turns are intermediate graph turns, never a completed response.
    if not calls:
        result["follow_ups"] = follow_ups
    return result
