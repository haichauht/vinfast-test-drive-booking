from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.nodes.advise_skill_node import advise_skill_node
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
    search_knowledge,
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
    # All non-sensitive requests use one of the two domain skills.
    active_skill = state.get("active_skill", "advise")
    if active_skill == "booking":
        return "booking_skill"
    return "advise_skill"


def should_continue_booking(state: AgentState) -> str:
    """Quyết định booking_skill có tiếp tục gọi tool hay kết thúc."""
    # Kiểm tra giới hạn số vòng tool
    if (state.get("tool_call_count") or 0) >= MAX_TOOL_CALLS:
        return "end"

    messages = state.get("messages") or []
    if not messages:
        return "end"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


def should_continue_advise(state: AgentState) -> str:
    """Quyết định advise_skill có tiếp tục gọi tool hay kết thúc."""
    # Kiểm tra giới hạn số vòng tool
    if (state.get("tool_call_count") or 0) >= MAX_TOOL_CALLS:
        return "end"

    messages = state.get("messages") or []
    if not messages:
        return "end"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    # Nodes phân loại và chính sách
    graph.add_node("classifier", classifier_node)
    graph.add_node("sensitive_policy", sensitive_policy_node)

    # Nodes xử lý Skill
    graph.add_node("booking_skill", booking_skill_node)
    graph.add_node("advise_skill", advise_skill_node)

    # Tách ToolNode theo từng skill để kiểm soát quyền gọi tool
    # booking_skill chỉ được gọi 6 booking tools
    booking_tools_list = [
        search_test_drive_options,
        hold_test_drive_slot,
        get_booking_draft,
        update_booking_draft,
        request_booking_access,
        verify_booking_access,
        get_booking_details,
        confirm_test_drive_booking,
    ]
    # advise_skill chỉ được gọi search_knowledge
    advise_tools_list = [search_knowledge]

    graph.add_node(
        "booking_tools",
        build_guarded_tool_node(booking_tools_list, skill_name="booking"),
    )
    graph.add_node(
        "advise_tools",
        build_guarded_tool_node(advise_tools_list, skill_name="advise"),
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
            "advise_skill": "advise_skill",
        },
    )

    # Booking skill loop: booking_skill → booking_tools → booking_skill → END
    graph.add_conditional_edges(
        "booking_skill",
        should_continue_booking,
        {
            "continue": "booking_tools",
            "end": END,
        },
    )
    graph.add_edge("booking_tools", "booking_skill")

    # Advise skill loop: advise_skill → advise_tools → advise_skill → END
    graph.add_conditional_edges(
        "advise_skill",
        should_continue_advise,
        {
            "continue": "advise_tools",
            "end": END,
        },
    )
    graph.add_edge("advise_tools", "advise_skill")

    # Các luồng kết thúc trực tiếp
    graph.add_edge("sensitive_policy", END)

    # Dùng MemorySaver để lưu lịch sử hội thoại theo thread_id
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


agent = build_graph()
