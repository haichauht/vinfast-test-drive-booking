import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from src.agents.graph import agent
from src.agents.nodes.booking_skill_node import booking_skill_node
from src.agents.nodes.classifier_node import classifier_node


@pytest.mark.asyncio
async def test_classified_lookup_creates_booking_access_ui_tool_call():
    result = await booking_skill_node(
        {
            "messages": [HumanMessage(content="Tôi muốn tra cứu lịch đã đặt")],
            "metadata": {"sub_intent": "booking_lookup"},
            "intent_entities": {"contact_value": None},
        }
    )

    tool_call = result["messages"][0].tool_calls[0]
    assert tool_call["name"] == "request_booking_access"
    assert tool_call["args"] == {"purpose": "lookup", "preferred_channel": "email"}


@pytest.mark.asyncio
async def test_booking_access_ui_directive_is_exposed_without_another_llm_call():
    tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call-access-form",
                "name": "request_booking_access",
                "args": {"purpose": "lookup", "preferred_channel": "email"},
            }
        ],
    )
    directive = {
        "requires_contact_value": True,
        "contact_type": "email",
        "purpose": "lookup",
        "suggested_next_action": "show_booking_access_email_form",
    }

    result = await booking_skill_node(
        {
            "messages": [
                HumanMessage(content="Tôi muốn tra cứu lịch đã đặt"),
                tool_call,
                ToolMessage(
                    content=json.dumps(directive),
                    tool_call_id="call-access-form",
                    name="request_booking_access",
                ),
            ],
            "metadata": {"sub_intent": "booking_lookup"},
        }
    )

    assert result["action_tool"] == "request_booking_access"
    assert result["action_result"] == directive
    assert result["action_input"] == {"purpose": "lookup", "preferred_channel": "email"}


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


@pytest.mark.asyncio
async def test_structured_action_strips_toolnode_exception_wrapper_from_user_error():
    result = await booking_skill_node(
        {
            "messages": [
                HumanMessage(content="Tôi xác nhận slot này"),
                ToolMessage(
                    content="Error: BookingError('Slot đã bắt đầu hoặc đã qua.')\n Please fix your mistakes.",
                    tool_call_id="call-1",
                    name="hold_test_drive_slot",
                    status="error",
                ),
            ],
            "requested_action": "hold_slot",
            "action_payload": {"slot_id": "slot-1", "ui_action_id": "hold-1"},
        }
    )

    assert result["response"] == "Slot đã bắt đầu hoặc đã qua."
    assert result["action_error"] == "Slot đã bắt đầu hoặc đã qua."
