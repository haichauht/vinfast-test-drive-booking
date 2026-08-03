from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from src.agents.nodes.advise_skill_node import advise_skill_node
from src.agents.nodes.booking_skill_node import booking_skill_node
from src.agents.nodes.classifier_node import classifier_node
from src.agents.nodes.general_respond_node import general_respond_node
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node
from src.agents.state import AgentState
from src.agents.tools import (
    get_booking_details,
    get_booking_draft,
    request_booking_access,
    search_knowledge,
    search_test_drive_options,
    update_booking_draft,
    verify_booking_access,
)


def route_intent(state: AgentState) -> str:
    """Điều hướng dựa trên intent được phân loại."""
    intent = state.get("intent", "domain")
    if intent == "sensitive":
        return "sensitive_policy"
    elif intent == "general":
        return "general_respond"

    # If domain, route based on active_skill
    active_skill = state.get("active_skill", "advise")
    if active_skill == "booking":
        return "booking_skill"
    return "advise_skill"


def should_continue(state: AgentState) -> str:
    """Quyết định xem có tiếp tục gọi tool hay kết thúc."""
    messages = state.get("messages") or []
    if not messages:
        return "end"

    last_message = messages[-1]
    # Check if the last message has tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


def route_tool_output(state: AgentState) -> str:
    """Điều hướng kết quả từ tool quay lại node skill đang hoạt động."""
    active_skill = state.get("active_skill", "advise")
    if active_skill == "booking":
        return "booking_skill"
    return "advise_skill"


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    # Thêm các nodes phân lớp định tuyến và xử lý chính sách
    graph.add_node("classifier", classifier_node)
    graph.add_node("sensitive_policy", sensitive_policy_node)
    graph.add_node("general_respond", general_respond_node)

    # Các node xử lý Skill
    graph.add_node("booking_skill", booking_skill_node)
    graph.add_node("advise_skill", advise_skill_node)

    # Node thực thi Tools
    tools = [
        search_knowledge,
        search_test_drive_options,
        get_booking_draft,
        update_booking_draft,
        request_booking_access,
        verify_booking_access,
        get_booking_details,
    ]
    graph.add_node("tools", ToolNode(tools))

    # Thiết lập luồng điều hướng
    graph.set_entry_point("classifier")

    # Định tuyến từ node phân loại
    graph.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "sensitive_policy": "sensitive_policy",
            "general_respond": "general_respond",
            "booking_skill": "booking_skill",
            "advise_skill": "advise_skill",
        },
    )

    # Định tuyến cho booking skill
    graph.add_conditional_edges(
        "booking_skill",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    # Định tuyến cho advise skill
    graph.add_conditional_edges(
        "advise_skill",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    # Định tuyến quay lại sau khi chạy tool
    graph.add_conditional_edges(
        "tools",
        route_tool_output,
        {
            "booking_skill": "booking_skill",
            "advise_skill": "advise_skill",
        },
    )

    # Các luồng kết thúc trực tiếp
    graph.add_edge("sensitive_policy", END)
    graph.add_edge("general_respond", END)

    return graph.compile()


agent = build_graph()
