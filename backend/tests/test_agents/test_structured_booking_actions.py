import json

import pytest
from langchain_core.messages import HumanMessage, ToolMessage
from src.agents.graph import agent
from src.agents.nodes.booking_skill_node import booking_skill_node
from src.agents.nodes.classifier_node import classifier_node


@pytest.mark.asyncio
async def test_booking_context_routes_to_booking_without_llm():
    result = await classifier_node(
        {
            "query": "Tôi muốn tiếp tục",
            "context": {"channel": "booking", "stage": "choose_showroom"},
        }
    )

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == "booking"


@pytest.mark.asyncio
async def test_structured_action_creates_the_expected_tool_call():
    result = await booking_skill_node(
        {
            "messages": [HumanMessage(content="Tôi chọn slot này")],
            "requested_action": "hold_slot",
            "action_payload": {"slot_id": "slot-1", "ui_action_id": "hold-1"},
        }
    )

    tool_call = result["messages"][0].tool_calls[0]
    assert tool_call["name"] == "hold_test_drive_slot"
    assert tool_call["args"] == {"slot_id": "slot-1", "ui_action_id": "hold-1"}


@pytest.mark.asyncio
async def test_structured_action_exposes_tool_result_to_chat_contract():
    tool_result = {"booking_id": "bkg-1", "status": "held", "version": 1}
    result = await booking_skill_node(
        {
            "messages": [
                HumanMessage(content="Tôi chọn slot này"),
                ToolMessage(
                    content=json.dumps(tool_result),
                    tool_call_id="call-1",
                    name="hold_test_drive_slot",
                ),
            ],
            "requested_action": "hold_slot",
            "action_payload": {"slot_id": "slot-1", "ui_action_id": "hold-1"},
        }
    )

    assert result["action_tool"] == "hold_test_drive_slot"
    assert result["action_input"] == {"slot_id": "slot-1", "ui_action_id": "hold-1"}
    assert result["action_result"] == tool_result
    assert result["action_error"] == ""


@pytest.mark.asyncio
async def test_structured_action_runs_through_the_compiled_graph_and_tool_node():
    result = await agent.ainvoke(
        {
            "query": "Tôi xác nhận slot này",
            "context": {"channel": "booking", "stage": "choose_slot"},
            "requested_action": "hold_slot",
            "action_payload": {"slot_id": "missing-slot", "ui_action_id": "hold-missing-slot"},
            "action_result": None,
            "action_tool": "",
            "action_input": {},
            "action_error": "",
        },
        config={"configurable": {"thread_id": "structured-action-tool-node"}},
    )

    assert result["action_tool"] == "hold_test_drive_slot"
    assert result["action_result"] is None
    assert result["action_error"]
