import logging
from contextlib import AbstractAsyncContextManager
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.nodes.booking_skill_node import booking_skill_node
from src.agents.nodes.classifier_node import classifier_node
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node
from src.agents.state import AgentState
from src.agents.tools import (
    confirm_test_drive_booking,
    get_booking_details,
    get_booking_draft,
    hold_test_drive_slot,
    request_booking_access,
    request_user_location,
    search_test_drive_options,
    update_booking_draft,
    verify_booking_access,
)
from src.guardrails.tool_guard import build_guarded_tool_node

# Giới hạn số vòng tool tối đa để tránh vòng lặp vô hạn
MAX_TOOL_CALLS = 8


def route_intent(state: AgentState) -> str:
    """Điều hướng dựa trên intent được phân loại."""
    intent = state.get("intent", "domain")
    if intent == "sensitive":
        return "sensitive_policy"
    # The public MVP has a single domain skill: booking.
    return "booking_skill"


def should_continue_booking(state: AgentState) -> str:
    """Quyết định booking_skill có tiếp tục gọi tool hay kết thúc."""
    messages = state.get("messages") or []
    if not messages:
        return "end"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        if (state.get("tool_call_count") or 0) >= MAX_TOOL_CALLS:
            return "max_tool_limit"
        return "continue"
    return "end"


async def max_tool_limit_node(state: AgentState) -> dict:
    """Xử lý an toàn khi số lần gọi tool vượt quá MAX_TOOL_CALLS."""
    messages = state.get("messages") or []
    last_message = messages[-1] if messages else None

    blocked_messages: list[ToolMessage] = []
    if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for call in last_message.tool_calls:
            blocked_messages.append(
                ToolMessage(
                    content='{"error": {"code": "MAX_TOOL_CALLS_EXCEEDED", "message": "Đã đạt giới hạn số lần xử lý tool cho câu hỏi này."}}',
                    tool_call_id=str(call.get("id") or "max-tools-exceeded"),
                    name=str(call.get("name") or "unknown"),
                    status="error",
                )
            )

    response_text = "Yêu cầu này cần quá nhiều lượt xử lý tự động. Bạn vui lòng thử lại với yêu cầu ngắn gọn hơn nhé."
    ai_msg = AIMessage(content=response_text)

    return {
        "messages": blocked_messages + [ai_msg],
        "response": response_text,
        "action_error": "MAX_TOOL_CALLS_EXCEEDED",
    }


def build_graph(checkpointer: Any | None = None) -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    # Nodes phân loại và chính sách
    graph.add_node("classifier", classifier_node)
    graph.add_node("sensitive_policy", sensitive_policy_node)
    graph.add_node("max_tool_limit", max_tool_limit_node)

    # Public MVP skill
    graph.add_node("booking_skill", booking_skill_node)

    # Tách ToolNode theo từng skill để kiểm soát quyền gọi tool
    booking_tools_list = [
        search_test_drive_options,
        hold_test_drive_slot,
        get_booking_draft,
        update_booking_draft,
        request_booking_access,
        request_user_location,
        verify_booking_access,
        get_booking_details,
        confirm_test_drive_booking,
    ]
    graph.add_node(
        "booking_tools",
        build_guarded_tool_node(booking_tools_list, skill_name="booking"),
    )

    # Entry point
    graph.set_entry_point("classifier")

    # Định tuyến từ classifier
    graph.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "sensitive_policy": "sensitive_policy",
            "booking_skill": "booking_skill",
        },
    )

    # Booking skill loop: booking_skill → booking_tools → booking_skill → END / max_tool_limit
    graph.add_conditional_edges(
        "booking_skill",
        should_continue_booking,
        {
            "continue": "booking_tools",
            "max_tool_limit": "max_tool_limit",
            "end": END,
        },
    )
    graph.add_edge("booking_tools", "booking_skill")

    # Các luồng kết thúc trực tiếp
    graph.add_edge("sensitive_policy", END)
    graph.add_edge("max_tool_limit", END)

    # Unit tests and local SQLite development keep an in-memory checkpointer.
    return graph.compile(checkpointer=checkpointer or MemorySaver())



# Default graph for unit tests and non-PostgreSQL local environments.
agent = build_graph()
_runtime_agent = agent
_checkpointer_context: AbstractAsyncContextManager[Any] | None = None


def uses_postgres(database_url: str) -> bool:
    """Return whether a database URL can be used by the Postgres checkpointer."""
    normalized = database_url.lower()
    return normalized.startswith(("postgres://", "postgresql://", "postgresql+psycopg://"))


def get_agent() -> CompiledStateGraph:
    """Return the checkpointer-backed graph selected during application startup."""
    return _runtime_agent


async def initialize_persistent_agent(database_url: str, *, required: bool = False) -> None:
    """Use PostgreSQL checkpoints for conversation memory when PostgreSQL is configured.

    SQLite remains intentionally in-memory for local tests. In production, the
    checkpointer is required so a restart or another backend instance can resume
    a conversation using the same LangGraph ``thread_id``.
    """
    global _runtime_agent, _checkpointer_context

    if not uses_postgres(database_url):
        if required:
            raise RuntimeError("Production conversation memory requires a PostgreSQL DATABASE_URL")
        logging.getLogger(__name__).info("LangGraph is using in-memory checkpoints (non-PostgreSQL database)")
        return

    context: AbstractAsyncContextManager[Any] | None = None
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        context = AsyncPostgresSaver.from_conn_string(database_url)
        checkpointer = await context.__aenter__()
        await checkpointer.setup()
    except Exception:
        if context is not None:
            await context.__aexit__(None, None, None)
        logging.getLogger(__name__).exception("Unable to initialize the PostgreSQL LangGraph checkpointer")
        if required:
            raise
        return

    _checkpointer_context = context
    _runtime_agent = build_graph(checkpointer=checkpointer)
    logging.getLogger(__name__).info("LangGraph conversation checkpoints are stored in PostgreSQL")


async def close_persistent_agent() -> None:
    """Release the PostgreSQL checkpointer connection during application shutdown."""
    global _runtime_agent, _checkpointer_context

    if _checkpointer_context is not None:
        await _checkpointer_context.__aexit__(None, None, None)
        _checkpointer_context = None
    _runtime_agent = agent
