from datetime import timedelta

import pytest
from src.services.booking import BookingError, iso

from tests.conftest import BOOKER_PHONE, FIXED_NOW


# test case of Chau + kiểm tra yêu cầu OTP trả destination đã mask và không lộ OTP thô
def test_request_access_masks_destination_and_hides_otp(booking_service, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()

    result = booking_service.request_access(confirmed["confirmed"]["booking_code"], BOOKER_PHONE, "lookup")

    assert result["destination_masked"].endswith(BOOKER_PHONE[-3:])
    assert BOOKER_PHONE not in result["destination_masked"]
    assert "otp_code" not in result


# test case of Chau + kiểm tra từ chối purpose OTP không được hỗ trợ
def test_request_access_rejects_invalid_purpose(booking_service, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()

    with pytest.raises(BookingError) as error:
        booking_service.request_access(confirmed["confirmed"]["booking_code"], BOOKER_PHONE, "delete_booking")

    assert error.value.code == "INVALID_INPUT"


# test case of Chau + kiểm tra contact không thuộc Booker hoặc Driver không được nhận OTP
def test_request_access_rejects_unregistered_contact(booking_service, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()

    with pytest.raises(BookingError) as error:
        booking_service.request_access(confirmed["confirmed"]["booking_code"], "0999999999", "lookup")

    assert error.value.code == "BOOKING_ACCESS_NOT_AVAILABLE"


# test case of Chau + kiểm tra OTP đúng tạo access session với permission theo purpose
@pytest.mark.parametrize(
    ("purpose", "expected_permission"),
    [
        ("lookup", "read_booking"),
        ("reschedule", "hold_reschedule"),
        ("cancel", "cancel_booking"),
        ("update_details", "update_details"),
        ("update_notifications", "update_notifications"),
    ],
)
def test_verify_access_grants_permission_for_purpose(
    booking_service, confirmed_booking_factory, purpose, expected_permission
):
    confirmed = confirmed_booking_factory()
    challenge = booking_service.request_access(
        confirmed["confirmed"]["booking_code"],
        BOOKER_PHONE,
        purpose,
        expose_otp=True,
    )

    session = booking_service.verify_access(challenge["challenge_id"], challenge["otp_code"])

    assert "read_booking" in session["permissions"]
    assert expected_permission in session["permissions"]
    assert session["booking_id"] == confirmed["booking_id"]


# test case of Chau + kiểm tra OTP chỉ được sử dụng thành công một lần
def test_otp_is_single_use(booking_service, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()
    challenge = booking_service.request_access(
        confirmed["confirmed"]["booking_code"],
        BOOKER_PHONE,
        "lookup",
        expose_otp=True,
    )
    booking_service.verify_access(challenge["challenge_id"], challenge["otp_code"])

    with pytest.raises(BookingError) as error:
        booking_service.verify_access(challenge["challenge_id"], challenge["otp_code"])

    assert error.value.code == "OTP_INVALID"


# test case of Chau + kiểm tra một lần nhập OTP sai phải tăng attempt count
def test_wrong_otp_increments_attempt_count(booking_service, booking_db, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()
    challenge = booking_service.request_access(
        confirmed["confirmed"]["booking_code"],
        BOOKER_PHONE,
        "lookup",
        expose_otp=True,
    )

    with pytest.raises(BookingError):
        booking_service.verify_access(challenge["challenge_id"], "000000")

    with booking_db.connect() as connection:
        attempt_count = connection.execute(
            "SELECT attempt_count FROM otp_challenges WHERE id=?",
            (challenge["challenge_id"],),
        ).fetchone()[0]
    assert attempt_count == 1


# test case of Chau + kiểm tra OTP bị khóa sau năm lần nhập sai
def test_otp_locks_after_max_attempts(booking_service, booking_db, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()
    challenge = booking_service.request_access(
        confirmed["confirmed"]["booking_code"],
        BOOKER_PHONE,
        "lookup",
        expose_otp=True,
    )

    for _ in range(5):
        with pytest.raises(BookingError):
            booking_service.verify_access(challenge["challenge_id"], "000000")

    with booking_db.connect() as connection:
        otp = connection.execute(
            "SELECT status,attempt_count FROM otp_challenges WHERE id=?",
            (challenge["challenge_id"],),
        ).fetchone()
    assert otp["status"] == "locked"
    assert otp["attempt_count"] == 5


# test case of Chau + kiểm tra OTP hết hạn bị từ chối
def test_expired_otp_is_rejected(booking_service, booking_db, confirmed_booking_factory):
    confirmed = confirmed_booking_factory()
    challenge = booking_service.request_access(
        confirmed["confirmed"]["booking_code"],
        BOOKER_PHONE,
        "lookup",
        expose_otp=True,
    )
    with booking_db.transaction(immediate=True) as connection:
        connection.execute(
            "UPDATE otp_challenges SET expires_at=? WHERE id=?",
            (iso(FIXED_NOW - timedelta(seconds=1)), challenge["challenge_id"]),
        )

    with pytest.raises(BookingError) as error:
        booking_service.verify_access(challenge["challenge_id"], challenge["otp_code"])

    assert error.value.code == "OTP_EXPIRED"


# test case of Chau + kiểm tra access session hết hạn không đọc được booking
def test_expired_access_session_is_rejected(booking_service, booking_db, access_factory):
    access = access_factory("lookup")
    with booking_db.transaction(immediate=True) as connection:
        connection.execute(
            "UPDATE booking_access_sessions SET expires_at=? WHERE booking_id=?",
            (iso(FIXED_NOW - timedelta(seconds=1)), access["booking"]["booking_id"]),
        )

    with pytest.raises(BookingError) as error:
        booking_service.get_booking_details(
            access["session"]["access_session_token"],
            booking_id=access["booking"]["booking_id"],
        )

    assert error.value.code == "ACCESS_SESSION_EXPIRED"


# test case of Chau + kiểm tra token lookup không được dùng để hủy booking
def test_lookup_permission_cannot_cancel_booking(booking_service, access_factory):
    access = access_factory("lookup")

    with pytest.raises(BookingError) as error:
        booking_service.cancel_booking(
            access["booking"]["booking_id"],
            access["session"]["access_session_token"],
            "cancel:with-lookup-token",
        )

    assert error.value.code == "ACCESS_DENIED"


# test case of Chau + kiểm tra token của booking này không đọc được booking khác
def test_access_session_is_scoped_to_one_booking(booking_service, access_factory, confirmed_booking_factory, catalog):
    first_access = access_factory("lookup")
    second = confirmed_booking_factory(catalog["slot_second_vehicle"])

    with pytest.raises(BookingError) as error:
        booking_service.get_booking_details(
            first_access["session"]["access_session_token"],
            booking_id=second["booking_id"],
        )

    assert error.value.code == "ACCESS_SESSION_SCOPE_MISMATCH"


# test case of Chau + kiểm tra API chi tiết chỉ trả cam kết GPLX và không trả số GPLX cũ
def test_booking_details_uses_boolean_license_commitment(booking_service, access_factory):
    access = access_factory("lookup")

    details = booking_service.get_booking_details(
        access["session"]["access_session_token"],
        booking_id=access["booking"]["booking_id"],
    )

    declaration = details["license_declaration"]
    assert declaration["has_driving_license"] is True
    assert "license_number" not in declaration
