from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import HumanMessage
from src.agents.nodes import classifier_node as classifier_module
from src.agents.nodes import general_respond_node as general_module
from src.agents.nodes.classifier_node import RouteSchema, classifier_node
from src.agents.nodes.general_respond_node import general_respond_node
from src.agents.nodes.sensitive_policy_node import sensitive_policy_node


# test case of Chau + kiểm tra classifier xử lý query rỗng mà không gọi LLM
@pytest.mark.asyncio
async def test_classifier_empty_query_uses_general_route_without_llm(monkeypatch):
    get_llm = MagicMock(side_effect=AssertionError("LLM must not be called"))
    monkeypatch.setattr(classifier_module, "get_classifier_llm", get_llm)

    result = await classifier_node({"query": "", "metadata": {"trace_id": "trace-1"}})

    assert result["intent"] == "general"
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
    [("booking", "booking"), ("vehicle_info", "advise")],
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
    assert result["metadata"] == {"request_id": "r-1", "sub_intent": sub_intent}
    structured.ainvoke.assert_awaited_once()


# test case of Chau + kiểm tra classifier fallback chọn general booking hoặc advise khi LLM lỗi
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "expected_intent", "expected_skill"),
    [
        ("Xin chào bạn", "general", None),
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

    assert result["intent"] in {"domain", "general", "sensitive"}


# test case of Chau + kiểm tra general node trả đúng nội dung từ LLM
@pytest.mark.asyncio
async def test_general_respond_returns_llm_content_and_includes_query(monkeypatch):
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content="Xin chào từ Vini"))
    monkeypatch.setattr(general_module, "get_llm", lambda: llm)

    result = await general_respond_node({"query": "Chào buổi sáng"})

    assert result == {"response": "Xin chào từ Vini"}
    prompt = llm.ainvoke.await_args.args[0]
    assert "Chào buổi sáng" in prompt


# test case of Chau + kiểm tra general node dùng fallback an toàn khi LLM lỗi
@pytest.mark.asyncio
async def test_general_respond_falls_back_when_llm_fails(monkeypatch):
    monkeypatch.setattr(general_module, "get_llm", MagicMock(side_effect=RuntimeError("LLM unavailable")))

    result = await general_respond_node({"query": "Xin chào"})

    assert "VinFast" in result["response"]
    assert "lái thử" in result["response"]


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
