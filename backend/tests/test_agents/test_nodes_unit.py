from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import HumanMessage
from src.agents.nodes import classifier_node as classifier_module
from src.agents.nodes.classifier_node import RouteSchema, classifier_node
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node


# test case of Chau + kiểm tra classifier xử lý query rỗng mà không gọi LLM
@pytest.mark.asyncio
async def test_classifier_empty_query_uses_advise_route_without_llm(monkeypatch):
    get_llm = MagicMock(side_effect=AssertionError("LLM must not be called"))
    monkeypatch.setattr(classifier_module, "get_classifier_llm", get_llm)

    result = await classifier_node({"query": "", "metadata": {"trace_id": "trace-1"}})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "advise"
    assert result["metadata"] == {"trace_id": "trace-1", "sub_intent": "empty_query"}
    assert isinstance(result["messages"][0], HumanMessage)
    assert result["messages"][0].content == ""
    get_llm.assert_not_called()


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
    [("booking", "booking"), ("booking_lookup", "booking"), ("vehicle_info", "advise")],
)
async def test_classifier_maps_domain_sub_intent_to_active_skill(monkeypatch, sub_intent, expected_skill):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(return_value=RouteSchema(intent="domain", sub_intent=sub_intent))
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node({"query": "Yêu cầu thuộc domain", "metadata": {"request_id": "r-1"}})

    assert result["intent"] == "domain"
    assert result["active_skill"] == expected_skill
    assert result["metadata"]["request_id"] == "r-1"
    assert result["metadata"]["sub_intent"] == sub_intent
    assert result["metadata"]["llm_call_count"] == 1
    assert result["intent_entities"] == {"contact_value": None}
    structured.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_classifier_extracts_booking_lookup_and_email_without_frontend_matching(monkeypatch):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value=RouteSchema(
            intent="domain",
            sub_intent="booking_lookup",
            contact_value="customer@example.com",
        )
    )
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: llm)

    result = await classifier_node(
        {
            "query": "Kiểm tra lịch của customer@example.com",
            "context": {"channel": "booking", "stage": "choose_showroom"},
        }
    )

    assert result["active_skill"] == "booking"
    assert result["metadata"]["sub_intent"] == "booking_lookup"
    assert result["intent_entities"] == {"contact_value": "customer@example.com"}


# test case of Chau + kiểm tra classifier fallback chọn booking hoặc advise khi LLM lỗi
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "expected_intent", "expected_skill"),
    [
        ("Xin chào bạn", "domain", "advise"),
        ("Tôi muốn đặt lịch lái thử VF6", "domain", "booking"),
        ("VF8 có gì nổi bật?", "domain", "advise"),
    ],
)
async def test_classifier_fallback_routes_without_network(monkeypatch, query, expected_intent, expected_skill):
    monkeypatch.setattr(
        classifier_module,
        "get_classifier_llm",
        MagicMock(side_effect=RuntimeError("classifier unavailable")),
    )

    result = await classifier_node({"query": query})

    assert result["intent"] == expected_intent
    assert result.get("active_skill") == expected_skill
    assert result["metadata"]["sub_intent"].startswith("fallback_")


@pytest.mark.asyncio
async def test_classifier_falls_back_when_llm_is_not_configured(monkeypatch):
    monkeypatch.setattr(classifier_module, "get_classifier_llm", lambda: None)

    result = await classifier_node({"query": "Tôi muốn đặt lịch lái thử VF6"})

    assert result["intent"] == "domain"
    assert result["active_skill"] == "booking"


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
        ("out_of_scope_math", "không hỗ trợ viết mã"),
        ("unknown", "ngoài phạm vi"),
    ],
)
async def test_sensitive_policy_covers_all_sub_intent_branches(sub_intent, expected_text):
    result = await sensitive_policy_node({"metadata": {"sub_intent": sub_intent}})

    assert expected_text in result["response"]
    assert result["policy_response"] == result["response"]
