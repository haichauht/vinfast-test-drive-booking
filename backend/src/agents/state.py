from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State schema cho LangGraph agent.

    Mỗi node đọc và ghi vào state này.
    total=False cho phép tất cả fields là optional.
    """

    query: str
    context: dict
    analysis: str
    response: str
    error: str
    metadata: dict
    intent: str
    policy_response: str
    messages: Annotated[list[AnyMessage], add_messages]
    active_skill: str  # "booking" or "advise"
    tool_call_count: int  # số vòng tool đã gọi, giới hạn tối đa 8
    requested_action: str | None
    action_payload: dict
    action_result: object | None
    action_tool: str
    action_input: dict
    action_error: str
