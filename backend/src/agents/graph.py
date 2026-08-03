from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.nodes.classifier_node import classifier_node
from src.agents.nodes.example_node import analyze_node, respond_node
from src.agents.nodes.general_respond_node import general_respond_node
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node
from src.agents.state import AgentState


def route_intent(state: AgentState) -> str:
    """Điều hướng dựa trên intent được phân loại."""
    intent = state.get("intent", "domain")
    if intent == "sensitive":
        return "sensitive_policy"
    elif intent == "general":
        return "general_respond"
    return "analyze"


def should_continue(state: AgentState) -> str:
    """Route based on whether an error occurred during analysis."""
    if state.get("error"):
        return END
    return "respond"


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)


    # Thêm các nodes phân lớp định tuyến và xử lý chính sách
    graph.add_node("classifier", classifier_node)
    graph.add_node("sensitive_policy", sensitive_policy_node)
    graph.add_node("general_respond", general_respond_node)

    # Các node xử lý nghiệp vụ domain xe/booking
    graph.add_node("analyze", analyze_node)
    graph.add_node("respond", respond_node)

    # Thiết lập luồng điều hướng
    graph.set_entry_point("classifier")

    # Định tuyến từ node phân loại
    graph.add_conditional_edges(
        "classifier",
        route_intent,
        {"sensitive_policy": "sensitive_policy",
            "general_respond": "general_respond", "analyze": "analyze"},
    )

    # Luồng nghiệp vụ domain
    graph.add_conditional_edges("analyze", should_continue)
    graph.add_edge("respond", END)

    # Các luồng kết thúc trực tiếp
    graph.add_edge("sensitive_policy", END)
    graph.add_edge("general_respond", END)

    return graph.compile()


agent = build_graph()
