from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from src.services.booking import catalog as catalog_module
from src.services.booking import BookingError

from tests.conftest import FIXED_NOW


# test case of Chau + kiểm tra tìm mẫu xe bằng code không phân biệt chữ hoa/chữ thường
def test_resolve_vehicle_model_case_insensitive(booking_service, catalog):
    result = booking_service.resolve_vehicle_model("vf6")

    assert result["id"] == catalog["model"]
    assert result["code"] == "VF6"


# test case of Chau + kiểm tra báo lỗi khi mẫu xe không tồn tại
def test_resolve_vehicle_model_not_found(booking_service, catalog):
    with pytest.raises(BookingError) as error:
        booking_service.resolve_vehicle_model("VF-UNKNOWN")

    assert error.value.code == "VEHICLE_NOT_FOUND"


# test case of Chau + kiểm tra tìm showroom và sắp xếp theo khoảng cách khách hàng
def test_search_showrooms_sorted_by_distance(booking_service, catalog):
    result = booking_service.search_options(vehicle_model="VF6", latitude=10.73, longitude=106.72)

    assert result["search_stage"] == "showroom_selection"
    assert result["showrooms"][0]["id"] == catalog["showroom_q7"]
    assert result["showrooms"][0]["distance_km"] <= result["showrooms"][1]["distance_km"]


def test_address_match_reuses_cached_showroom_tokens():
    catalog_module._SHOWROOM_TOKEN_CACHE.clear()
    showroom = {
        "id": "showroom-q7",
        "updated_at": "2026-08-07T00:00:00+07:00",
        "name": "VinFast Quận 7",
        "address": "Quận 7, Thành phố Hồ Chí Minh",
    }

    first = catalog_module.CatalogService._address_match_score("Quận 7", showroom)
    second = catalog_module.CatalogService._address_match_score("Hồ Chí Minh", showroom)

    assert first > 0
    assert second > 0
    assert len(catalog_module._SHOWROOM_TOKEN_CACHE) == 1

    showroom["updated_at"] = "2026-08-08T00:00:00+07:00"
    catalog_module.CatalogService._address_match_score("Quận 7", showroom)
    assert len(catalog_module._SHOWROOM_TOKEN_CACHE) == 2


# test case of Chau + kiểm tra chỉ trả slot tương lai đang available và giới hạn tối đa năm slot
def test_search_slots_returns_only_future_available_slots(booking_service, catalog):
    result = booking_service.search_options(vehicle_model="VF6", showroom_id=catalog["showroom_q7"], limit=20)

    assert result["search_stage"] == "slot_selection"
    assert 0 < len(result["slots"]) <= 5
    assert all(slot["status"] == "available" for slot in result["slots"])
    assert all(slot["start_at"] > FIXED_NOW.isoformat() for slot in result["slots"])
    assert catalog["slot_blocked"] not in {slot["id"] for slot in result["slots"]}
    assert catalog["slot_past"] not in {slot["id"] for slot in result["slots"]}


# test case of Chau + kiểm tra từ chối giờ mong muốn sai định dạng
@pytest.mark.parametrize("preferred_time", ["abc", "10", "10-aa"])
def test_search_slots_rejects_invalid_preferred_time(booking_service, catalog, preferred_time):
    with pytest.raises(BookingError) as error:
        booking_service.search_options(
            vehicle_model="VF6",
            showroom_id=catalog["showroom_q7"],
            preferred_time=preferred_time,
        )

    assert error.value.code == "INVALID_INPUT"


# test case of Chau + kiểm tra giữ slot tạo booking held và liên kết slot đúng booking
def test_hold_slot_creates_booking_and_related_records(booking_service, booking_db, catalog):
    result = booking_service.hold_slot(catalog["slot_main"], "hold:001")

    assert result["status"] == "held"
    assert result["remaining_seconds"] == 900
    with booking_db.connect() as connection:
        booking = connection.execute("SELECT * FROM bookings WHERE id=?", (result["booking_id"],)).fetchone()
        slot = connection.execute("SELECT * FROM test_drive_slots WHERE id=?", (catalog["slot_main"],)).fetchone()
        detail_count = connection.execute(
            "SELECT count(*) FROM booking_driver_details WHERE booking_id=?",
            (result["booking_id"],),
        ).fetchone()[0]
        plan_count = connection.execute(
            "SELECT count(*) FROM notification_plans WHERE booking_id=?",
            (result["booking_id"],),
        ).fetchone()[0]

    assert booking["status"] == "held"
    assert slot["status"] == "held"
    assert slot["current_booking_id"] == result["booking_id"]
    assert detail_count == 1
    assert plan_count == 1


# test case of Chau + kiểm tra idempotency khi người dùng bấm giữ slot hai lần cùng action id
def test_hold_slot_is_idempotent(booking_service, booking_db, catalog):
    first = booking_service.hold_slot(catalog["slot_main"], "hold:same-action")
    second = booking_service.hold_slot(catalog["slot_main"], "hold:same-action")

    assert second == first
    with booking_db.connect() as connection:
        count = connection.execute("SELECT count(*) FROM bookings").fetchone()[0]
    assert count == 1


# test case of Chau + kiểm tra slot đã được giữ không thể tạo thêm booking khác
def test_hold_slot_rejects_second_booking(booking_service, catalog):
    booking_service.hold_slot(catalog["slot_main"], "hold:first")

    with pytest.raises(BookingError) as error:
        booking_service.hold_slot(catalog["slot_main"], "hold:second")

    assert error.value.code == "SLOT_NO_LONGER_AVAILABLE"
    assert error.value.retryable is True


# test case of Chau + kiểm tra hai slot trùng thời gian của cùng xe không được giữ đồng thời
def test_hold_slot_rejects_overlapping_slot_of_same_vehicle(booking_service, catalog):
    booking_service.hold_slot(catalog["slot_main"], "hold:primary")

    with pytest.raises(BookingError) as error:
        booking_service.hold_slot(catalog["slot_overlap"], "hold:overlap")

    assert error.value.code == "SLOT_NO_LONGER_AVAILABLE"


# test case of Chau + kiểm tra hai request đồng thời chỉ có một request giữ slot thành công
def test_concurrent_hold_allows_only_one_winner(booking_service, catalog):
    barrier = Barrier(2)

    def attempt(index):
        barrier.wait()
        try:
            return booking_service.hold_slot(catalog["slot_main"], f"hold:concurrent-{index}")
        except BookingError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, [1, 2]))

    successes = [result for result in results if isinstance(result, dict)]
    failures = [result for result in results if isinstance(result, str)]
    assert len(successes) == 1
    assert failures == ["SLOT_NO_LONGER_AVAILABLE"]


# test case of Chau + kiểm tra job hết hạn hold giải phóng slot cho khách khác
def test_expire_held_booking_releases_slot(booking_service, booking_db, catalog):
    held = booking_service.hold_slot(catalog["slot_main"], "hold:to-expire")
    booking_service.now = lambda: FIXED_NOW.replace(hour=3)

    expired_count = booking_service.expire_held_bookings()

    assert expired_count == 1
    with booking_db.connect() as connection:
        booking = connection.execute("SELECT status FROM bookings WHERE id=?", (held["booking_id"],)).fetchone()
        slot = connection.execute(
            "SELECT status,current_booking_id FROM test_drive_slots WHERE id=?",
            (catalog["slot_main"],),
        ).fetchone()
    assert booking["status"] == "expired"
    assert slot["status"] == "available"
    assert slot["current_booking_id"] is None


# test case of Chau + kiểm tra không cho giữ slot với TTL bằng không hoặc âm
@pytest.mark.parametrize("ttl_seconds", [0, -1])
def test_hold_slot_rejects_non_positive_ttl(booking_service, catalog, ttl_seconds):
    with pytest.raises(BookingError) as error:
        booking_service.hold_slot(catalog["slot_main"], f"hold:invalid-ttl-{ttl_seconds}", ttl_seconds=ttl_seconds)

    assert error.value.code == "INVALID_INPUT"


# test case of Chau + kiểm tra không giữ slot của xe đang maintenance
def test_hold_slot_rejects_maintenance_vehicle(booking_service, catalog):
    with pytest.raises(BookingError) as error:
        booking_service.hold_slot(catalog["slot_maintenance"], "hold:not-ready-maintenance")

    assert error.value.code == "VEHICLE_NOT_READY"
