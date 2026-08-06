from __future__ import annotations

import json
import secrets
from datetime import datetime

from src.services.booking.common import iso, new_id
from src.services.booking.errors import BookingError

_id = new_id


class ManagementService:
    def update_booking_details(
        self, booking_id: str, access_session_token: str, *, booker_patch=None, driver_patch=None
    ) -> dict:
        """Edit people data of an existing booking after OTP verification."""
        with self.db.transaction(immediate=True) as c:
            self._require_access(c, access_session_token, booking_id, "update_details")
            booking = c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
            if not booking or booking["status"] not in ("confirmed", "checked_in"):
                raise BookingError("BOOKING_NOT_EDITABLE", "Booking khÃ´ng thá»ƒ chá»‰nh sá»­a.")
            for role, patch in (("booker", booker_patch), ("driver", driver_patch)):
                if not patch:
                    continue
                pid = booking[f"{role}_person_id"]
                allowed = {k: v for k, v in patch.items() if k in ("full_name", "phone", "email", "preferred_channel")}
                if allowed:
                    c.execute(
                        "UPDATE people SET " + ",".join(f"{k}=?" for k in allowed) + ",updated_at=? WHERE id=?",
                        (*allowed.values(), iso(self.now()), pid),
                    )
            c.execute("UPDATE bookings SET version=version+1,updated_at=? WHERE id=?", (iso(self.now()), booking_id))
            self._event(c, booking_id, "booking_details_updated", "user")
            return self._draft(c, booking_id, require_held=False)

    def hold_reschedule_slot(
        self, current_booking_id: str, new_slot_id: str, access_session_token: str, ui_action_id: str
    ) -> dict:
        request_payload = {"current_booking_id": current_booking_id, "new_slot_id": new_slot_id}
        with self.db.transaction(immediate=True) as c:
            self._require_access(c, access_session_token, current_booking_id, "hold_reschedule")
            cached = self._idempotent_response(c, ui_action_id, "hold_reschedule", request_payload)
            if cached:
                return cached
            current = c.execute("SELECT status FROM bookings WHERE id=?", (current_booking_id,)).fetchone()
            if not current or current["status"] != "confirmed":
                raise BookingError("BOOKING_NOT_EDITABLE", "Booking khÃ´ng thá»ƒ dá»i lá»‹ch.")
        held = self.hold_slot(
            new_slot_id,
            ui_action_id,
            source_channel="reschedule",
            _operation="hold_reschedule",
            _idempotency_payload=request_payload,
        )
        with self.db.transaction(immediate=True) as c:
            current = c.execute("SELECT * FROM bookings WHERE id=?", (current_booking_id,)).fetchone()
            new_booking = c.execute(
                "SELECT rescheduled_from_booking_id FROM bookings WHERE id=?", (held["booking_id"],)
            ).fetchone()
            if new_booking["rescheduled_from_booking_id"] == current_booking_id:
                cached = self._idempotent_response(c, ui_action_id, "hold_reschedule", request_payload)
                return {**cached, "current_booking_id": current_booking_id}
            c.execute(
                "UPDATE bookings SET rescheduled_from_booking_id=?,booker_person_id=?,driver_person_id=?,updated_at=? WHERE id=?",
                (
                    current_booking_id,
                    current["booker_person_id"],
                    current["driver_person_id"],
                    iso(self.now()),
                    held["booking_id"],
                ),
            )
            old_detail = c.execute(
                "SELECT * FROM booking_driver_details WHERE booking_id=?", (current_booking_id,)
            ).fetchone()
            if old_detail:
                c.execute(
                    "UPDATE booking_driver_details SET has_driving_license=?,declared_license_class=?,validity_acknowledged=?,license_check_status='declared',updated_at=? WHERE booking_id=?",
                    (
                        old_detail["has_driving_license"],
                        old_detail["declared_license_class"],
                        old_detail["validity_acknowledged"],
                        iso(self.now()),
                        held["booking_id"],
                    ),
                )
            old_plan = c.execute(
                "SELECT * FROM notification_plans WHERE booking_id=?", (current_booking_id,)
            ).fetchone()
            if old_plan:
                c.execute(
                    "UPDATE notification_plans SET primary_recipient_role=?,copy_booker=?,zalo_enabled=?,sms_enabled=?,email_enabled=?,reminder_24h_enabled=?,reminder_2h_enabled=?,custom_plan_json=?,updated_at=? WHERE booking_id=?",
                    (
                        old_plan["primary_recipient_role"],
                        old_plan["copy_booker"],
                        old_plan["zalo_enabled"],
                        old_plan["sms_enabled"],
                        old_plan["email_enabled"],
                        old_plan["reminder_24h_enabled"],
                        old_plan["reminder_2h_enabled"],
                        old_plan["custom_plan_json"],
                        iso(self.now()),
                        held["booking_id"],
                    ),
                )
            self._event(
                c, held["booking_id"], "reschedule_slot_held", "user", {"current_booking_id": current_booking_id}
            )
            result = {**held, "current_booking_id": current_booking_id}
            c.execute(
                "UPDATE idempotency_records SET response_json=? WHERE action_id=?",
                (json.dumps(result), ui_action_id),
            )
        return result

    def confirm_reschedule(
        self, current_booking_id: str, new_booking_id: str, access_session_token: str, ui_action_id: str
    ) -> dict:
        request_payload = {"current_booking_id": current_booking_id, "new_booking_id": new_booking_id}
        with self.db.transaction(immediate=True) as c:
            self._require_access(c, access_session_token, current_booking_id, "confirm_reschedule")
            cached = self._idempotent_response(c, ui_action_id, "confirm_reschedule", request_payload)
            if cached:
                return cached
            old = c.execute("SELECT * FROM bookings WHERE id=?", (current_booking_id,)).fetchone()
            new = c.execute("SELECT * FROM bookings WHERE id=?", (new_booking_id,)).fetchone()
            if (
                not old
                or old["status"] != "confirmed"
                or not new
                or new["status"] != "held"
                or new["rescheduled_from_booking_id"] != current_booking_id
            ):
                raise BookingError("BOOKING_NOT_EDITABLE", "Cáº·p booking dá»i lá»‹ch khÃ´ng há»£p lá»‡.")
            if datetime.fromisoformat(new["hold_expires_at"]) <= self.now():
                raise BookingError("HOLD_EXPIRED", "Hold lá»‹ch má»›i Ä‘Ã£ háº¿t háº¡n.")
            new_slot = c.execute("SELECT * FROM test_drive_slots WHERE id=?", (new["slot_id"],)).fetchone()
            if new_slot["current_booking_id"] != new_booking_id:
                raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Slot má»›i khÃ´ng cÃ²n thuá»™c booking.")
            now = iso(self.now())

            code = "VF" + self.now().strftime("%y%m%d") + secrets.token_hex(3).upper()
            c.execute(
                "UPDATE bookings SET status='confirmed',booking_code=?,confirmed_at=?,version=version+1,updated_at=? WHERE id=?",
                (code, now, now, new_booking_id),
            )
            c.execute(
                "UPDATE test_drive_slots SET status='booked',held_until=NULL,updated_at=? WHERE id=?",
                (now, new["slot_id"]),
            )
            c.execute(
                "UPDATE booking_driver_details SET license_check_status='pending_in_person',updated_at=? WHERE booking_id=?",
                (now, new_booking_id),
            )
            c.execute(
                "UPDATE bookings SET status='rescheduled',replaced_by_booking_id=?,version=version+1,updated_at=? WHERE id=?",
                (new_booking_id, now, current_booking_id),
            )
            c.execute(
                "UPDATE test_drive_slots SET status='available',current_booking_id=NULL,held_until=NULL,updated_at=? WHERE id=? AND current_booking_id=?",
                (now, old["slot_id"], current_booking_id),
            )
            c.execute(
                "UPDATE notification_jobs SET status='cancelled',updated_at=? WHERE booking_id=? AND status='pending'",
                (now, current_booking_id),
            )
            self._create_jobs(
                c,
                new_booking_id,
                new_slot["start_at"],
                confirmation_type="reschedule_confirmation",
            )
            self._event(c, current_booking_id, "booking_rescheduled", "user", {"new_booking_id": new_booking_id})
            self._event(c, new_booking_id, "booking_confirmed", "user", {"old_booking_id": current_booking_id})
            result = {
                "old_booking_status": "rescheduled",
                "new_booking_status": "confirmed",
                "new_booking_id": new_booking_id,
                "new_booking_code": code,
                "released_old_slot_id": old["slot_id"],
            }
            self._save_idempotency(c, ui_action_id, "confirm_reschedule", request_payload, result, now)
            return result

    def cancel_booking(
        self, booking_id: str, access_session_token: str, ui_action_id: str, reason: str | None = None
    ) -> dict:
        request_payload = {"booking_id": booking_id, "reason": reason}
        with self.db.transaction(immediate=True) as c:
            # Authorization is deliberately evaluated before replaying a cached
            # destructive command response.
            self._require_access(c, access_session_token, booking_id, "cancel_booking")
            cached = self._idempotent_response(c, ui_action_id, "cancel_booking", request_payload)
            if cached:
                return cached
            b = c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
            if not b or b["status"] != "confirmed":
                raise BookingError("BOOKING_NOT_CANCELLABLE", "Booking khÃ´ng thá»ƒ há»§y.")
            now = iso(self.now())
            c.execute(
                "UPDATE bookings SET status='cancelled',cancelled_at=?,cancellation_reason=?,version=version+1,updated_at=? WHERE id=?",
                (now, reason, now, booking_id),
            )
            c.execute(
                "UPDATE test_drive_slots SET status='available',current_booking_id=NULL,held_until=NULL,updated_at=? WHERE id=? AND current_booking_id=?",
                (now, b["slot_id"], booking_id),
            )
            jobs = c.execute(
                "UPDATE notification_jobs SET status='cancelled',updated_at=? WHERE booking_id=? AND status='pending'",
                (now, booking_id),
            ).rowcount
            self._create_transactional_notification_jobs(c, booking_id, "cancellation_confirmation")
            self._event(c, booking_id, "booking_cancelled", "user", {"reason": reason})
            result = {
                "booking_status": "cancelled",
                "released_slot_id": b["slot_id"],
                "cancelled_notification_jobs_count": jobs,
            }
            self._save_idempotency(c, ui_action_id, "cancel_booking", request_payload, result, now)
            return result
