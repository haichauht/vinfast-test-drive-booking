import json

from langchain_core.messages import ToolMessage
from src.agents.nodes.post_booking_skill_node import _extract_follow_ups, _render_grounded_knowledge_response
from src.services.knowledge.service import KnowledgeService


def test_follow_up_transport_requires_exactly_two_unique_declarative_items():
    visible, follow_ups = _extract_follow_ups(
        'Nội dung trả lời. <<<FOLLOW_UPS>>>["Chuẩn bị trước buổi lái thử", '
        '"Tìm hiểu các tính năng an toàn"]<<<END_FOLLOW_UPS>>>'
    )

    assert visible == "Nội dung trả lời."
    assert follow_ups == [
        {"text": "Chuẩn bị trước buổi lái thử"},
        {"text": "Tìm hiểu các tính năng an toàn"},
    ]

    _, incomplete = _extract_follow_ups(
        'Trả lời. <<<FOLLOW_UPS>>>["Chỉ còn một mục hợp lệ", "Có dấu hỏi?"]<<<END_FOLLOW_UPS>>>'
    )
    assert incomplete == []


def test_review_pending_knowledge_is_rendered_without_model_authored_policy_claims():
    result = {
        "facts": [
            {
                "topic": "test_drive.general_process",
                "content": "Xe được đưa tới địa điểm theo yêu cầu để khách hàng trải nghiệm.",
                "source": "VinFast generic FAQ",
                "source_uri": "https://example.test/generic",
                "scope": {"models": []},
            },
            {
                "topic": "ownership.warranty",
                "content": "VF 8 và pin cao áp được nêu 10 năm/200.000 km.",
                "source": "VinFast official VF 8 FAQ",
                "source_uri": "https://example.test/vf8",
                "scope": {"models": ["VF 8"]},
            }
        ],
        "review_warning": "Pending internal review.",
    }
    message = ToolMessage(
        content=json.dumps(result, ensure_ascii=False),
        name="search_knowledge",
        tool_call_id="knowledge-1",
    )

    response = _render_grounded_knowledge_response(
        message,
        "VF 8 bảo hành pin thế nào và nên kiểm tra gì khi lái thử?",
    )

    assert response is not None
    assert "VF 8 và pin cao áp được nêu 10 năm/200.000 km" in response
    assert "https://example.test/vf8" in response
    assert "đang chờ rà soát nội bộ" in response
    assert "tùy điều kiện nào đến trước" not in response


def test_knowledge_search_prioritizes_requested_topic_with_exact_model_scope():
    result = KnowledgeService().search(
        "VF 8 được bảo hành pin như thế nào và tôi nên kiểm tra gì trong buổi lái thử?",
        model_code="VF 8",
        topics=["warranty", "battery", "test_drive"],
    )

    assert result["facts"][0]["id"] == "vinfast.vf_8.faq.12"
