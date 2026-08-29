import json

from langchain_core.messages import HumanMessage, ToolMessage
from src.agents.nodes.post_booking_skill_node import (
    _extract_follow_ups,
    _render_grounded_knowledge_response,
    _requires_profile_capture,
)
from src.agents.tools.update_post_booking_signals.tool import _normalize_post_booking_signals
from src.services.knowledge.service import KnowledgeService
from src.services.profile.models import BookingSignalCandidate, ProfileSignalCandidate


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


def test_family_size_booking_alias_is_normalized_to_profile_household_size():
    profiles, bookings = _normalize_post_booking_signals(
        [],
        [
            BookingSignalCandidate(
                category="custom",
                key="custom.family_size",
                value=4,
                description="Gia đình có 4 người.",
                subject="group",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
                operation="add",
            )
        ],
    )

    assert bookings == []
    assert len(profiles) == 1
    assert profiles[0].key == "household_size"
    assert profiles[0].value == 4
    assert profiles[0].subject == "self"


def test_generated_family_size_aliases_are_normalized_to_household_size():
    profiles, bookings = _normalize_post_booking_signals(
        [
            ProfileSignalCandidate(
                category="fact",
                key="family_household_size",
                value=4,
                description="Gia đình có 4 người.",
                subject="self",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
            )
        ],
        [
            BookingSignalCandidate(
                category="custom",
                key="custom.family_size_for_test_drive_advice",
                value=4,
                description="Gia đình có 4 người.",
                subject="booking",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
            )
        ],
    )

    assert bookings == []
    assert [(signal.key, signal.value, signal.subject) for signal in profiles] == [
        ("household_size", 4, "self")
    ]


def test_boolean_involvement_is_normalized_before_contract_validation():
    signal = BookingSignalCandidate(
        category="participation",
        key="booker_evaluation_involvement",
        value=True,
        description="Người đặt trực tiếp đánh giá xe.",
        subject="booker",
    )

    assert signal.value == "high"


def test_explicit_household_message_overrides_booking_guest_inference():
    profiles, bookings = _normalize_post_booking_signals(
        [],
        [
            BookingSignalCandidate(
                category="group",
                key="additional_guest_count",
                value=2,
                description="Gia đình gồm 4 người.",
                subject="group",
            ),
            BookingSignalCandidate(
                category="group",
                key="additional_guest_context",
                value="Gia đình gồm 4 người.",
                description="Cần tư vấn cho gia đình.",
                subject="group",
            ),
        ],
        latest_user_message="Gia đình tôi có 4 người, hãy lưu ý để tư vấn phù hợp.",
    )

    assert bookings == []
    assert [(signal.key, signal.value, signal.subject) for signal in profiles] == [
        ("household_size", 4, "self")
    ]


def test_household_attendance_is_split_into_durable_and_booking_facts():
    profiles, bookings = _normalize_post_booking_signals(
        [],
        [],
        latest_user_message="Gia đình tôi có 6 người đến lái thử hôm đó.",
    )

    assert [(signal.key, signal.value, signal.subject) for signal in profiles] == [
        ("household_size", 6, "self")
    ]
    assert {(signal.key, signal.subject): signal.value for signal in bookings} == {
        ("booker_attending", "booker"): True,
        ("additional_guest_count", "group"): 5,
    }


def test_child_attendance_is_captured_as_booking_guest_context():
    _, bookings = _normalize_post_booking_signals(
        [],
        [],
        latest_user_message="Có một đứa con gái 2 tuổi đi cùng nữa.",
    )

    context = next(signal for signal in bookings if signal.key == "additional_guest_context")
    assert context.value == ["Bé gái 2 tuổi đi cùng"]


def test_spouse_driving_is_captured_without_changing_registered_driver():
    _, bookings = _normalize_post_booking_signals(
        [],
        [],
        latest_user_message="Chồng tôi sẽ lái thử cùng tôi.",
    )

    values = {(signal.key, signal.subject): signal.value for signal in bookings}
    assert values[("booker_will_drive", "booker")] is True
    assert values[("custom.additional_driver", "group")] == {
        "relationship": "chồng",
        "will_drive": True,
    }
    assert values[("additional_guest_context", "group")] == [
        "Chồng đi cùng và cũng muốn lái thử"
    ]


def test_explicit_primary_use_is_saved_as_profile_fact():
    profiles, _ = _normalize_post_booking_signals(
        [],
        [],
        latest_user_message=(
            "nếu mục đích sử dụng xe chính của tôi là di chuyển nội thành như đưa đón con đi trẻ"
        ),
    )

    assert len(profiles) == 1
    assert profiles[0].key == "primary_use"
    assert profiles[0].value == "di chuyển nội thành như đưa đón con đi trẻ"


def test_capture_gate_covers_previously_dropped_post_booking_facts():
    messages = [
        "Có một đứa con gái 2 tuổi đi cùng nữa.",
        "Chồng tôi sẽ lái thử cùng tôi.",
        "Mục đích sử dụng chủ yếu là đi lại nội thành và đưa đón con.",
    ]

    assert all(_requires_profile_capture([HumanMessage(content=message)]) for message in messages)
