from src.services.booking.notifications import (
    InMemoryMessagingProvider,
)


# test case of Chau + kiểm tra dispatcher chỉ gửi notification đã đến hạn và lưu metadata provider
def test_dispatch_due_notifications_sends_due_confirmation(booking_service, booking_db, confirmed_booking_factory):
    booking = confirmed_booking_factory()
    provider = InMemoryMessagingProvider()
    booking_service.messaging_provider = provider

    result = booking_service.dispatch_due_notifications()

    assert result == {"claimed": 1, "sent": 1, "failed": 0, "is_mock": True}
    assert len(provider.messages) == 1
    assert provider.messages[0]["channel"] == "sms"
    assert provider.messages[0]["destination"] == "0901234567"
    assert "Lịch lái thử đã xác nhận" in provider.messages[0]["body"]
    assert booking["confirmed"]["booking_code"] in provider.messages[0]["body"]
    with booking_db.connect() as connection:
        sent = connection.execute(
            "SELECT status,attempt_count,provider_name,provider_status,provider_message_id,"
            "provider_response_json,error_message FROM notification_jobs "
            "WHERE booking_id=? AND notification_type='booking_confirmation'",
            (booking["booking_id"],),
        ).fetchone()
        future_count = connection.execute(
            "SELECT count(*) AS total FROM notification_jobs WHERE booking_id=? AND status='pending'",
            (booking["booking_id"],),
        ).fetchone()["total"]

    assert sent["status"] == "sent"
    assert sent["attempt_count"] == 1
    assert sent["provider_name"] == "mock_sms"
    assert sent["provider_status"] == "mocked"
    assert sent["provider_message_id"].startswith("mock_")
    assert sent["provider_response_json"] == '{"accepted": true}'
    assert sent["error_message"] is None
    assert future_count == 2


# test case of Chau + kiểm tra job đã gửi không bị gửi trùng ở lần dispatcher kế tiếp
def test_dispatch_does_not_resend_sent_notification(booking_service, confirmed_booking_factory):
    confirmed_booking_factory()
    provider = InMemoryMessagingProvider()
    booking_service.messaging_provider = provider

    first = booking_service.dispatch_due_notifications()
    second = booking_service.dispatch_due_notifications()

    assert first["sent"] == 1
    assert second == {"claimed": 0, "sent": 0, "failed": 0, "is_mock": True}
    assert len(provider.messages) == 1


# test case of Chau + kiểm tra batch size giới hạn đúng số job được claim trong một lượt
def test_dispatch_respects_batch_size(booking_service, booking_db, confirmed_booking_factory):
    booking = confirmed_booking_factory()
    with booking_db.transaction(immediate=True) as connection:
        connection.execute(
            "UPDATE notification_jobs SET scheduled_at=? WHERE booking_id=?",
            (booking_service.now().isoformat(), booking["booking_id"]),
        )
    provider = InMemoryMessagingProvider()
    booking_service.messaging_provider = provider

    result = booking_service.dispatch_due_notifications(batch_size=2)

    assert result["claimed"] == 2
    assert result["sent"] == 2
    assert len(provider.messages) == 2
    with booking_db.connect() as connection:
        statuses = connection.execute(
            "SELECT status,count(*) AS total FROM notification_jobs WHERE booking_id=? GROUP BY status",
            (booking["booking_id"],),
        ).fetchall()
    assert {row["status"]: row["total"] for row in statuses} == {"pending": 1, "sent": 2}


# test case of Chau + kiểm tra thiếu địa chỉ nhận sẽ retry rồi chuyển failed khi hết số lần thử
def test_missing_recipient_destination_retries_then_fails(booking_service, booking_db, confirmed_booking_factory):
    booking = confirmed_booking_factory()
    with booking_db.transaction(immediate=True) as connection:
        connection.execute(
            "UPDATE people SET phone=NULL,email=NULL WHERE id=(SELECT driver_person_id FROM bookings WHERE id=?)",
            (booking["booking_id"],),
        )
        connection.execute(
            "UPDATE notification_jobs SET max_attempts=2 "
            "WHERE booking_id=? AND notification_type='booking_confirmation'",
            (booking["booking_id"],),
        )

    first = booking_service.dispatch_due_notifications()
    second = booking_service.dispatch_due_notifications()

    assert first == {"claimed": 1, "sent": 0, "failed": 1, "is_mock": True}
    assert second == {"claimed": 1, "sent": 0, "failed": 1, "is_mock": True}
    with booking_db.connect() as connection:
        row = connection.execute(
            "SELECT status,attempt_count,error_message FROM notification_jobs "
            "WHERE booking_id=? AND notification_type='booking_confirmation'",
            (booking["booking_id"],),
        ).fetchone()
    assert row["status"] == "failed"
    assert row["attempt_count"] == 2
    assert row["error_message"] == "recipient_channel_unavailable"


class _ExplodingProvider:
    def send_message(self, *, channel, destination, body):
        raise RuntimeError("provider unavailable")


# test case of Chau + kiểm tra lỗi provider được cô lập và job còn khả năng retry thay vì kẹt processing
def test_provider_exception_does_not_crash_dispatcher_or_stick_job(
    booking_service, booking_db, confirmed_booking_factory
):
    booking = confirmed_booking_factory()
    booking_service.messaging_provider = _ExplodingProvider()

    result = booking_service.dispatch_due_notifications()

    assert result["failed"] == 1
    with booking_db.connect() as connection:
        row = connection.execute(
            "SELECT status,attempt_count FROM notification_jobs "
            "WHERE booking_id=? AND notification_type='booking_confirmation'",
            (booking["booking_id"],),
        ).fetchone()
    assert row["status"] in {"pending", "failed"}
    assert row["attempt_count"] == 1
