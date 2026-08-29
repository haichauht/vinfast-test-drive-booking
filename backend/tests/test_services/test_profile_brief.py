import pytest
from src.agents.tools.update_post_booking_signals.tool import _normalize_post_booking_signals
from src.services.llm import summarize_user_profile
from src.services.profile.models import BookingSignalCandidate, SignalCandidate
from src.services.profile.queue import ProfileUpdateQueue
from src.services.profile.service import ProfileService


def _booking_signal(key, value, description, *, subject="group", operation="add"):
    return BookingSignalCandidate(
        category="participants",
        key=key,
        value=value,
        description=description,
        subject=subject,
        certainty="known",
        confidence=1,
        source_type="explicit_user",
        operation=operation,
    )


def _profile_service_with_booking(booking_db, confirmed_booking_factory):
    booking = confirmed_booking_factory()
    service = ProfileService(booking_db, identity_secret="test-secret")
    profile = service.promote_from_booking(
        None,
        booking["booking_id"],
        source="test",
    )
    assert profile is not None
    return service, booking["booking_id"], profile.id


@pytest.mark.asyncio
async def test_sales_brief_keeps_all_previously_missing_facts(
    booking_db,
    confirmed_booking_factory,
):
    service, booking_id, profile_id = _profile_service_with_booking(
        booking_db,
        confirmed_booking_factory,
    )
    service.apply(
        profile_id,
        [
            SignalCandidate(
                category="fact",
                key="household_size",
                value=6,
                description="Gia đình có 6 người.",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
            ),
            SignalCandidate(
                category="usage",
                key="primary_use",
                value="Đi lại nội thành và đưa đón con.",
                description="Sử dụng xe chủ yếu để đi nội thành và đưa đón con.",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
            ),
        ],
        source_ref="conversation-test",
    )
    service.apply_booking_signals(
        booking_id,
        [
            _booking_signal("booker_attending", True, "Người đặt sẽ tham gia.", subject="booker"),
            _booking_signal("additional_guest_count", 5, "Có 5 người đi cùng."),
            _booking_signal("additional_guest_context", ["Bé gái 2 tuổi đi cùng"], "Bé gái đi cùng."),
        ],
        source_participant="booker",
        source_ref="conversation-test",
    )
    service.apply_booking_signals(
        booking_id,
        [
            _booking_signal(
                "additional_guest_context",
                ["Chồng đi cùng và cũng muốn lái thử"],
                "Chồng cũng muốn lái thử.",
            ),
            _booking_signal("booker_will_drive", True, "Người đặt sẽ lái.", subject="booker"),
        ],
        source_participant="booker",
        source_ref="conversation-test",
    )

    source = service.booking_profiles_context(booking_id)
    source["test_drive_context"] = service.booking_context_signals(booking_id)
    brief = await summarize_user_profile(source)

    assert "tổng cộng 6 người tham gia" in brief
    assert "Bé gái 2 tuổi đi cùng" in brief
    assert "Chồng đi cùng và cũng muốn lái thử" in brief
    assert "Đi lại nội thành và đưa đón con" in brief
    assert "tổng cộng 7 người" not in brief


@pytest.mark.asyncio
async def test_household_size_alone_is_not_presented_as_booking_attendance(
    booking_db,
    confirmed_booking_factory,
):
    service, booking_id, profile_id = _profile_service_with_booking(
        booking_db,
        confirmed_booking_factory,
    )
    service.apply(
        profile_id,
        [
            SignalCandidate(
                category="fact",
                key="household_size",
                value=4,
                description="Gia đình có 4 người.",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
            )
        ],
        source_ref="conversation-test",
    )

    source = service.booking_profiles_context(booking_id)
    source["test_drive_context"] = service.booking_context_signals(booking_id)
    brief = await summarize_user_profile(source)

    assert "Gia đình có 4 người" in brief
    assert "tổng cộng 4 người tham gia" not in brief


@pytest.mark.asyncio
async def test_post_booking_queue_falls_back_to_sql_when_redis_is_unavailable(
    booking_db,
    confirmed_booking_factory,
):
    service, booking_id, profile_id = _profile_service_with_booking(
        booking_db,
        confirmed_booking_factory,
    )

    class UnavailableRedis:
        available = False

    queue = ProfileUpdateQueue(UnavailableRedis(), service)  # type: ignore[arg-type]
    saved = await queue.enqueue_post_booking(
        profile_updates=[
            {
                "profile_id": profile_id,
                "candidates": [
                    SignalCandidate(
                        category="fact",
                        key="household_size",
                        value=6,
                        description="Gia đình có 6 người.",
                        certainty="known",
                        confidence=1,
                        source_type="explicit_user",
                    ).model_dump(mode="json")
                ],
            }
        ],
        booking_id=booking_id,
        booking_candidates=[
            _booking_signal("additional_guest_context", ["Bé gái 2 tuổi đi cùng"], "Bé gái đi cùng.")
        ],
        speaker_role="booker",
        conversation_id="conversation-test",
        trace_id="trace-test",
    )

    assert saved is True
    assert service.load(profile_id).signals[0]["key"] == "household_size"
    assert service.booking_context_signals(booking_id)[0]["value"] == ["Bé gái 2 tuổi đi cùng"]


@pytest.mark.asyncio
async def test_exact_failed_conversation_is_persisted_end_to_end_in_sales_brief(
    booking_db,
    confirmed_booking_factory,
):
    service, booking_id, profile_id = _profile_service_with_booking(
        booking_db,
        confirmed_booking_factory,
    )

    class UnavailableRedis:
        available = False

    queue = ProfileUpdateQueue(UnavailableRedis(), service)  # type: ignore[arg-type]
    messages = [
        "Gia đình tôi có 6 người đến lái thử hôm đó, theo bạn thì tôi nên quan tâm đến những điều gì khi lái thử",
        "có một đứa con gái 2 tuổi đi cùng nữa",
        "và chồng tôi sẽ lái thử cùng tôi",
        "nếu mục đích sử dụng xe chính của tôi là di chuyển nội thành như đưa đón con đi trẻ",
    ]
    for turn, message in enumerate(messages):
        profile_signals, booking_signals = _normalize_post_booking_signals(
            [],
            [],
            latest_user_message=message,
        )
        saved = await queue.enqueue_post_booking(
            profile_updates=[
                {
                    "profile_id": profile_id,
                    "candidates": [
                        signal.model_dump(mode="json", exclude={"subject"})
                        for signal in profile_signals
                    ],
                }
            ]
            if profile_signals
            else [],
            booking_id=booking_id,
            booking_candidates=booking_signals,
            speaker_role="booker",
            conversation_id=f"conversation-test-{turn}",
            trace_id=f"trace-test-{turn}",
        )
        assert saved is True

    source = service.booking_profiles_context(booking_id)
    source["test_drive_context"] = service.booking_context_signals(booking_id)
    brief = await summarize_user_profile(source)

    assert "tổng cộng 6 người tham gia" in brief
    assert "Bé gái 2 tuổi đi cùng" in brief
    assert "Chồng đi cùng và cũng muốn lái thử" in brief
    assert "di chuyển nội thành như đưa đón con đi trẻ" in brief
