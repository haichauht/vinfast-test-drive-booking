from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import HumanMessage
from src.agents.nodes import classifier_node as classifier_module
from src.agents.nodes.classifier_node import RouteSchema, classifier_node
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node


# test case of Chau + kiểm tra classifier xử lý query rỗng mà không gọi LLM
@pytest.mark.asyncio
async def test_classifier_empty_query_uses_booking_route_without_llm(monkeypatch):
    get_llm = MagicMock(side_effect=AssertionError("LLM must not be called"))
    monkeypatch.setattr(classifier_module, "get_classifier_llm", get_llm)

    result = await classifier_node({"query": "", "metadata": {"trace_id": "trace-1"}})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"] == {"trace_id": "trace-1", "sub_intent": "empty_query"}
    assert isinstance(result["messages"][0], HumanMessage)
    assert result["messages"][0].content == ""
    get_llm.assert_not_called()


@pytest.mark.asyncio
async def test_classifier_prompt_marks_colloquial_locations_as_booking(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(return_value=RouteSchema(intent="domain", sub_intent="booking_new"))
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": "t ở Hồ Chí Minh"})

    prompt = structured.ainvoke.await_args.args[0]
    assert "t ở hcm" in prompt
    assert result["intent"] == "domain"
    assert result["metadata"]["sub_intent"] == "booking_new"


@pytest.mark.asyncio
async def test_classifier_marks_schedule_questions_as_booking_availability(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value=RouteSchema(intent="domain", sub_intent="booking_availability")
    )
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": "tui rảnh ngày 25-26"})

    prompt = structured.ainvoke.await_args.args[0]
    assert "booking_availability" in prompt
    assert result["intent"] == "domain"
    assert result["metadata"]["sub_intent"] == "booking_availability"


# test case of Chau + kiểm tra classifier ưu tiên sensitive keyword và không phụ thuộc LLM
@pytest.mark.asyncio
async def test_classifier_sensitive_keyword_bypasses_llm(monkeypatch):
    get_llm = MagicMock(side_effect=AssertionError("LLM must not be called"))
    monkeypatch.setattr(classifier_module, "get_classifier_llm", get_llm)

    result = await classifier_node({"query": "Hoàng Sa và Trường Sa thuộc về ai?"})

    assert result["intent"] == "sensitive"
    assert result["metadata"]["sub_intent"] == "sovereignty"
    assert result["messages"][0].content == "Hoàng Sa và Trường Sa thuộc về ai?"
    get_llm.assert_not_called()


# test case of Chau + kiểm tra classifier map sub intent domain sang đúng active skill
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sub_intent", "expected_skill"),
    [("booking", "booking"), ("vehicle_info", "booking")],
)
async def test_classifier_maps_domain_sub_intent_to_active_skill(monkeypatch, sub_intent, expected_skill):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(return_value=RouteSchema(intent="domain", sub_intent=sub_intent))
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": "Yêu cầu thuộc domain", "metadata": {"request_id": "r-1"}})

    assert result["intent"] == "domain"
    assert result["active_skill"] == expected_skill
    assert result["metadata"]["request_id"] == "r-1"
    assert result["metadata"]["sub_intent"] == sub_intent
    assert result["metadata"]["llm_call_count"] == 1
    structured.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_classifier_keeps_vehicle_info_inside_booking_channel(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(return_value=RouteSchema(intent="domain", sub_intent="vehicle_info"))
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node(
        {
            "query": "Tôi muốn xem VF5",
            "context": {"channel": "booking", "stage": "need_car"},
        }
    )

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == "vehicle_info"
    assert result["metadata"]["llm_call_count"] == 1


@pytest.mark.asyncio
async def test_classifier_keeps_new_test_drive_request_out_of_post_booking_shortcut(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value=RouteSchema(intent="domain", sub_intent="booking_new")
    )
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": "Tôi muốn lái thử VF9"})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == "booking_new"
    structured.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_driver_invitation_blocks_booking_availability(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value=RouteSchema(intent="domain", sub_intent="booking_availability")
    )
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node(
        {
            "query": "Ngày 25 còn giờ nào?",
            "participant_context": {"role": "driver"},
            "post_booking_context": {"active": True},
        }
    )

    assert result["intent"] == "out_of_scope"
    assert result["metadata"]["sub_intent"] == "driver_booking_scope"


@pytest.mark.asyncio
async def test_classifier_fallback_routes_without_network(monkeypatch):
    monkeypatch.setattr(
        classifier_module,
        "get_classifier_llm",
        MagicMock(side_effect=RuntimeError("classifier unavailable")),
    )

    result = await classifier_node({"query": "VF8 có gì nổi bật?"})

    assert result["intent"] == "domain"
    assert result.get("active_skill") == "booking"
    assert result["metadata"]["sub_intent"].startswith("fallback_")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "llm_sub_intent"),
    [
        ("hi", "greeting"),
        ("HI!!!", "greeting"),
        ("bạn là ai", "assistant_identity"),
        ("ViVi hỗ trợ gì?", "assistant_identity"),
    ],
)
async def test_classifier_uses_llm_for_greeting_and_identity(monkeypatch, query, llm_sub_intent):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value=RouteSchema(intent="domain", sub_intent=llm_sub_intent)
    )
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": query})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == llm_sub_intent
    prompt = structured.ainvoke.await_args.args[0]
    assert "Never classify them as out_of_scope" in prompt
    assert "assistant_identity" in prompt


@pytest.mark.asyncio
async def test_classifier_booking_keyword_still_bypasses_llm(monkeypatch):
    get_llm = MagicMock(side_effect=AssertionError("LLM must not be called"))
    monkeypatch.setattr(classifier_module, "get_classifier_llm", get_llm)

    result = await classifier_node({"query": "Tôi muốn đặt lịch lái thử VF6"})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == "booking"
    get_llm.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "internal_code"),
    [
        (classifier_module.BudgetExceededError("budget"), "LLM_BUDGET_EXCEEDED"),
        (classifier_module.LLMCallLimitExceededError("calls"), "LLM_CALL_LIMIT_EXCEEDED"),
    ],
)
async def test_classifier_returns_safe_response_when_llm_limit_is_exceeded(
    monkeypatch, exception, internal_code
):
    llm = MagicMock()
    llm.model_name = "test-classifier"
    llm.with_structured_output.return_value = MagicMock()
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)
    trace = MagicMock()
    monkeypatch.setattr(classifier_module, "trace_event", trace)
    monkeypatch.setattr(
        classifier_module,
        "invoke_with_budget",
        AsyncMock(side_effect=exception),
    )

    result = await classifier_node({"query": "hi"})

    assert result["intent"] == "sensitive"
    assert result["action_error"] == "SERVICE_TEMPORARILY_UNAVAILABLE"
    assert result["policy_response"] == result["response"]
    assert "AI" not in result["response"]
    assert "chi phí" not in result["response"]
    assert any(call.kwargs.get("error_code") == internal_code for call in trace.call_args_list)


@pytest.mark.asyncio
async def test_classifier_falls_back_when_llm_is_not_configured(monkeypatch):
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: None)

    result = await classifier_node({"query": "VF8 có gì nổi bật?"})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == "fallback_domain"


# test case of Chau + kiểm tra classifier từ chối intent lạ do LLM trả về
@pytest.mark.asyncio
async def test_classifier_rejects_unknown_llm_intent(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(return_value=RouteSchema(intent="unknown", sub_intent="booking"))
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": "Đặt lịch VF6"})

    assert result["intent"] in {"domain", "sensitive"}


# test case of Chau + kiểm tra sensitive node trả đúng policy cho từng sub intent
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sub_intent", "expected_text"),
    [
        ("sovereignty", "Việt Nam"),
        ("out_of_scope_code", "không hỗ trợ viết mã"),
        ("out_of_scope_math", "giải các bài toán"),
        ("out_of_scope", "tìm showroom"),
        ("post_booking_required", "đã có lịch lái thử"),
        ("unknown", "Việt Nam"),
    ],
)
async def test_sensitive_policy_covers_all_sub_intent_branches(sub_intent, expected_text):
    result = await sensitive_policy_node({"metadata": {"sub_intent": sub_intent}})

    assert expected_text in result["response"]
    assert result["policy_response"] == result["response"]
