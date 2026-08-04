from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from src.services.booking.common import iso, new_id
from src.services.booking.errors import BookingError

_id = new_id


class LifecycleService:
    def hold_slot(
        self,
        slot_id: str,
        ui_action_id: str,
        *,
        ttl_seconds: int = 900,
        source_channel: str = "web",
        _operation: str = "hold_slot",
        _idempotency_payload: dict | None = None,
    ) -> dict:
        if ttl_seconds != 900:
            raise BookingError("INVALID_INPUT", "Hold TTL được cố định ở 900 giây.")
        request_payload = _idempotency_payload or {"slot_id": slot_id, "source_channel": source_channel}
        with self.db.transaction(immediate=True) as c:
            cached = self._idempotent_response(c, ui_action_id, _operation, request_payload)
            if cached:
                return cached
            slot = c.execute(
                "SELECT s.*,d.is_active vehicle_active,d.operational_status,d.battery_soc,d.minimum_booking_soc,"
                "v.required_license_class FROM test_drive_slots s JOIN demo_vehicles d ON d.id=s.demo_vehicle_id "
                "JOIN vehicle_variants x ON x.id=d.variant_id JOIN vehicle_models v ON v.id=x.model_id WHERE s.id=?",
                (slot_id,),
            ).fetchone()
            if not slot or slot["status"] != "available":
                raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Slot khÃ´ng cÃ²n kháº£ dá»¥ng.", retryable=True)
            if datetime.fromisoformat(slot["start_at"]) <= self.now():
                raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Slot đã bắt đầu hoặc đã qua.", retryable=True)
            if not slot["vehicle_active"] or slot["operational_status"] != "available":
                raise BookingError("VEHICLE_NOT_READY", "Xe demo hiện không sẵn sàng.", retryable=True)
            if slot["battery_soc"] is None or slot["battery_soc"] < slot["minimum_booking_soc"]:
                raise BookingError("VEHICLE_NOT_READY", "Pin xe demo chưa đạt ngưỡng phục vụ.", retryable=True)
            overlap = c.execute(
                "SELECT 1 FROM test_drive_slots WHERE demo_vehicle_id=? AND id<>? AND start_at<? AND end_at>? AND status IN ('held','booked','blocked') LIMIT 1",
                (slot["demo_vehicle_id"], slot_id, slot["end_at"], slot["start_at"]),
            ).fetchone()
            if overlap:
                raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Xe demo Ä‘Ã£ cÃ³ lá»‹ch trÃ¹ng.", retryable=True)
            now, expires, booking_id = self.now(), self.now() + timedelta(seconds=ttl_seconds), _id("bkg")
            c.execute(
                "INSERT INTO bookings(id,slot_id,status,held_at,hold_expires_at,source_channel,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (booking_id, slot_id, "held", iso(now), iso(expires), source_channel, iso(now), iso(now)),
            )
            c.execute(
                "UPDATE test_drive_slots SET status='held',held_until=?,current_booking_id=?,updated_at=? WHERE id=?",
                (iso(expires), booking_id, iso(now), slot_id),
            )
            c.execute(
                "INSERT INTO booking_driver_details(booking_id,required_license_class,created_at,updated_at) VALUES(?,?,?,?)",
                (booking_id, slot["required_license_class"], iso(now), iso(now)),
            )
            c.execute(
                "INSERT INTO notification_plans(booking_id,created_at,updated_at) VALUES(?,?,?)",
                (booking_id, iso(now), iso(now)),
            )
            self._event(c, booking_id, "slot_held", "user", {"slot_id": slot_id})
            result = {
                "booking_id": booking_id,
                "status": "held",
                "hold_expires_at": iso(expires),
                "remaining_seconds": ttl_seconds,
            }
            self._save_idempotency(c, ui_action_id, _operation, request_payload, result, iso(now))
            return result

    def _draft(self, c, booking_id: str, *, require_held: bool = True) -> dict:
        booking = self._row(c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone())
        if not booking:
            raise BookingError("BOOKING_DRAFT_NOT_AVAILABLE", "Booking draft không khả dụng.")
        if require_held and booking["status"] != "held":
            raise BookingError("BOOKING_DRAFT_NOT_AVAILABLE", "Booking draft không khả dụng.")
        if require_held and datetime.fromisoformat(booking["hold_expires_at"]) <= self.now():
            self._expire_hold_in_transaction(c, booking)
            # Expiry reconciliation is durable even though the caller receives
            # a domain error after it. The transaction context would otherwise roll it back.
            c.commit()
            raise BookingError("HOLD_EXPIRED", "Hold đã hết hạn.")
        booking["booker"] = (
            self._row(c.execute("SELECT * FROM people WHERE id=?", (booking["booker_person_id"],)).fetchone())
            if booking["booker_person_id"]
            else None
        )
        booking["driver"] = (
            self._row(c.execute("SELECT * FROM people WHERE id=?", (booking["driver_person_id"],)).fetchone())
            if booking["driver_person_id"]
            else None
        )
        booking["license_declaration"] = self._row(
            c.execute("SELECT * FROM booking_driver_details WHERE booking_id=?", (booking_id,)).fetchone()
        )
        booking["notification_plan"] = self._row(
            c.execute("SELECT * FROM notification_plans WHERE booking_id=?", (booking_id,)).fetchone()
        )
        missing = []
        for role in ("booker", "driver"):
            if not booking[role]:
                missing.append(role)
            elif not booking[role]["phone"] and not booking[role]["email"]:
                missing.append(f"{role}.contact")
        lic = booking["license_declaration"] or {}
        if "has_driving_license" in lic and lic["has_driving_license"] is not None:
            lic["has_driving_license"] = bool(lic["has_driving_license"])
        if "validity_acknowledged" in lic:
            lic["validity_acknowledged"] = bool(lic["validity_acknowledged"])
        if lic.get("has_driving_license") is not True and lic.get("has_driving_license") != 1:
            missing.append("license.has_driving_license")
        if lic.get("has_driving_license") == 1 and not lic.get("declared_license_class"):
            missing.append("license.declared_license_class")
        if (
            lic.get("declared_license_class")
            and lic.get("required_license_class")
            and lic["declared_license_class"] != lic["required_license_class"]
        ):
            missing.append("license.declared_license_class")
        if lic.get("has_driving_license") == 1 and not lic.get("validity_acknowledged"):
            missing.append("license.validity_acknowledged")
        remaining = max(0, int((datetime.fromisoformat(booking["hold_expires_at"]) - self.now()).total_seconds()))
        booking.update(
            missing_required_fields=missing,
            validation_warnings=[],
            remaining_seconds=remaining,
            is_ready_to_confirm=not missing and remaining > 0,
        )
        return booking

    def get_booking_draft(self, booking_id: str) -> dict:
        with self.db.transaction(immediate=True) as c:
            return self._draft(c, booking_id)

    def _expire_hold_in_transaction(self, c, booking) -> None:
        now = iso(self.now())
        c.execute(
            "UPDATE bookings SET status='expired',version=version+1,updated_at=? WHERE id=? AND status='held'",
            (now, booking["id"]),
        )
        c.execute(
            "UPDATE test_drive_slots SET status='available',held_until=NULL,current_booking_id=NULL,updated_at=? "
            "WHERE id=? AND current_booking_id=?",
            (now, booking["slot_id"], booking["id"]),
        )
        self._event(c, booking["id"], "hold_expired")

    def update_booking_draft(
        self,
        booking_id: str,
        *,
        booker_patch=None,
        driver_patch=None,
        driver_same_as_booker: bool = False,
        license_patch=None,
        notification_plan_patch=None,
        expected_version=None,
    ) -> dict:
        with self.db.transaction(immediate=True) as c:
            b = c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
            if not b:
                raise BookingError("BOOKING_NOT_FOUND", "KhÃ´ng tÃ¬m tháº¥y booking.")
            if b["status"] != "held":
                raise BookingError("BOOKING_DRAFT_NOT_AVAILABLE", "Booking draft không khả dụng.")
            if datetime.fromisoformat(b["hold_expires_at"]) <= self.now():
                self._expire_hold_in_transaction(c, b)
                c.commit()
                raise BookingError("HOLD_EXPIRED", "Hold đã hết hạn.")
            if expected_version is not None and b["version"] != expected_version:
                raise BookingError("VERSION_CONFLICT", "Draft Ä‘Ã£ Ä‘Æ°á»£c cáº­p nháº­t á»Ÿ nÆ¡i khÃ¡c.", retryable=True)
            for role, patch in (("booker", booker_patch), ("driver", None if driver_same_as_booker else driver_patch)):
                if patch:
                    allowed = {
                        k: patch.get(k) for k in ("full_name", "phone", "email", "preferred_channel") if k in patch
                    }
                    if not allowed.get("full_name"):
                        raise BookingError("INVALID_INPUT", f"{role}.full_name lÃ  báº¯t buá»™c.")
                    current_pid = b[f"{role}_person_id"]
                    if role == "driver" and current_pid is not None and current_pid == b["booker_person_id"]:
                        # Changing a self-booking to on-behalf must preserve the
                        # Booker person and attach a new Driver person.
                        current_pid = None
                    pid = current_pid or _id("person")
                    now = iso(self.now())
                    if current_pid:
                        sets = ",".join(f"{k}=?" for k in allowed)
                        c.execute(f"UPDATE people SET {sets},updated_at=? WHERE id=?", (*allowed.values(), now, pid))
                        if "phone" in allowed or "email" in allowed:
                            c.execute(
                                "UPDATE people SET normalized_phone=?,normalized_email=? WHERE id=?",
                                (allowed.get("phone"), (allowed.get("email") or "").lower() or None, pid),
                            )
                    else:
                        c.execute(
                            "INSERT INTO people(id,full_name,phone,email,preferred_channel,normalized_phone,normalized_email,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (
                                pid,
                                allowed["full_name"],
                                allowed.get("phone"),
                                allowed.get("email"),
                                allowed.get("preferred_channel", "sms"),
                                allowed.get("phone"),
                                allowed.get("email", "").lower() or None,
                                now,
                                now,
                            ),
                        )
                        c.execute(f"UPDATE bookings SET {role}_person_id=? WHERE id=?", (pid, booking_id))
            if driver_same_as_booker:
                booker_id = c.execute("SELECT booker_person_id FROM bookings WHERE id=?", (booking_id,)).fetchone()[0]
                if not booker_id:
                    raise BookingError("INVALID_INPUT", "Cáº§n nháº­p thÃ´ng tin Booker trÆ°á»›c.")
                c.execute("UPDATE bookings SET driver_person_id=? WHERE id=?", (booker_id, booking_id))
            if license_patch:
                allowed = {}
                if "has_driving_license" in license_patch:
                    allowed["has_driving_license"] = int(bool(license_patch["has_driving_license"]))
                    allowed["license_check_status"] = (
                        "declared" if license_patch["has_driving_license"] else "not_provided"
                    )
                    if not license_patch["has_driving_license"]:
                        allowed["declared_license_class"] = None
                        allowed["validity_acknowledged"] = 0
                for key in ("declared_license_class", "validity_acknowledged"):
                    if key in license_patch:
                        allowed[key] = (
                            int(bool(license_patch[key])) if key == "validity_acknowledged" else license_patch[key]
                        )
                if allowed:
                    c.execute(
                        "UPDATE booking_driver_details SET "
                        + ",".join(f"{k}=?" for k in allowed)
                        + ",updated_at=? WHERE booking_id=?",
                        (*allowed.values(), iso(self.now()), booking_id),
                    )
            if notification_plan_patch:
                allowed = {
                    k: v
                    for k, v in notification_plan_patch.items()
                    if k
                    in (
                        "copy_booker",
                        "zalo_enabled",
                        "sms_enabled",
                        "email_enabled",
                        "reminder_24h_enabled",
                        "reminder_2h_enabled",
                    )
                }
                if allowed:
                    c.execute(
                        "UPDATE notification_plans SET "
                        + ",".join(f"{k}=?" for k in allowed)
                        + ",updated_at=? WHERE booking_id=?",
                        (*allowed.values(), iso(self.now()), booking_id),
                    )
            c.execute("UPDATE bookings SET version=version+1,updated_at=? WHERE id=?", (iso(self.now()), booking_id))
            self._event(c, booking_id, "booking_draft_updated", "agent")
            return self._draft(c, booking_id)

    def confirm_booking(self, booking_id: str, ui_action_id: str, expected_version: int) -> dict:
        request_payload = {"booking_id": booking_id, "expected_version": expected_version}
        with self.db.transaction(immediate=True) as c:
            cached = self._idempotent_response(c, ui_action_id, "confirm_booking", request_payload)
            if cached:
                return cached
            draft = self._draft(c, booking_id)
            if draft["status"] != "held" or draft["remaining_seconds"] <= 0:
                raise BookingError("HOLD_EXPIRED", "Hold Ä‘Ã£ háº¿t háº¡n.")
            if draft["version"] != expected_version:
                raise BookingError("VERSION_CONFLICT", "Draft Ä‘Ã£ thay Ä‘á»•i.", retryable=True)
            if not draft["is_ready_to_confirm"]:
                raise BookingError("INVALID_INPUT", "Draft chÆ°a Ä‘á»§ thÃ´ng tin.")
            slot = c.execute(
                "SELECT s.*,d.is_active vehicle_active,d.operational_status,d.battery_soc,d.minimum_booking_soc "
                "FROM test_drive_slots s JOIN demo_vehicles d ON d.id=s.demo_vehicle_id WHERE s.id=?",
                (draft["slot_id"],),
            ).fetchone()
            if slot["status"] != "held" or slot["current_booking_id"] != booking_id:
                raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Slot khÃ´ng thuá»™c booking.")
            if datetime.fromisoformat(slot["start_at"]) <= self.now():
                raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Slot đã bắt đầu hoặc đã qua.")
            if not slot["vehicle_active"] or slot["operational_status"] != "available":
                raise BookingError("VEHICLE_NOT_READY", "Xe demo không còn sẵn sàng.", retryable=True)
            if slot["battery_soc"] is None or slot["battery_soc"] < slot["minimum_booking_soc"]:
                raise BookingError("VEHICLE_NOT_READY", "Pin xe demo không còn đạt ngưỡng phục vụ.", retryable=True)
            assignment = c.execute(
                "SELECT a.sales_staff_id FROM slot_sales_assignments a JOIN sales_staff s ON s.id=a.sales_staff_id "
                "WHERE a.slot_id=? AND a.status='assigned' AND s.status='active' ORDER BY a.created_at LIMIT 1",
                (draft["slot_id"],),
            ).fetchone()
            code = "VF" + self.now().strftime("%y%m%d") + secrets.token_hex(3).upper()
            now = iso(self.now())
            c.execute(
                "UPDATE bookings SET status='confirmed',booking_code=?,confirmed_at=?,assigned_sales_staff_id=?,version=version+1,updated_at=? WHERE id=?",
                (code, now, assignment["sales_staff_id"] if assignment else None, now, booking_id),
            )
            c.execute(
                "UPDATE test_drive_slots SET status='booked',held_until=NULL,updated_at=? WHERE id=?",
                (now, draft["slot_id"]),
            )
            c.execute(
                "UPDATE booking_driver_details SET license_check_status='pending_in_person',updated_at=? WHERE booking_id=?",
                (now, booking_id),
            )
            self._create_jobs(c, booking_id, slot["start_at"])
            self._event(c, booking_id, "booking_confirmed", "user")
            result = {"booking_id": booking_id, "booking_code": code, "status": "confirmed", "confirmed_at": now}
            self._save_idempotency(c, ui_action_id, "confirm_booking", request_payload, result, now)
            return result

    def _create_jobs(self, c, bid, start, *, confirmation_type: str = "booking_confirmation"):
        start_dt = datetime.fromisoformat(start)
        now = iso(self.now())
        recipient_channels, plan = self._notification_recipient_channels(c, bid)
        schedule = [(confirmation_type, self.now())]
        if plan["reminder_24h_enabled"] and start_dt - timedelta(hours=24) > self.now():
            schedule.append(("reminder_24h", start_dt - timedelta(hours=24)))
        if plan["reminder_2h_enabled"] and start_dt - timedelta(hours=2) > self.now():
            schedule.append(("reminder_2h", start_dt - timedelta(hours=2)))
        for recipient, channels in recipient_channels:
            for typ, when in schedule:
                for channel in channels:
                    c.execute(
                        "INSERT INTO notification_jobs(id,booking_id,recipient_person_id,notification_type,channel,scheduled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                        (_id("job"), bid, recipient, typ, channel, iso(when), now, now),
                    )

    def _create_transactional_notification_jobs(self, c, bid: str, notification_type: str) -> None:
        now = iso(self.now())
        recipient_channels, _ = self._notification_recipient_channels(c, bid)
        for recipient, channels in recipient_channels:
            for channel in channels:
                c.execute(
                    "INSERT INTO notification_jobs(id,booking_id,recipient_person_id,notification_type,channel,scheduled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (_id("job"), bid, recipient, notification_type, channel, now, now, now),
                )

    def _notification_recipient_channels(self, c, bid: str):
        booking = c.execute("SELECT booker_person_id,driver_person_id FROM bookings WHERE id=?", (bid,)).fetchone()
        plan = c.execute("SELECT * FROM notification_plans WHERE booking_id=?", (bid,)).fetchone()
        recipients = [booking["driver_person_id"]]
        if plan["copy_booker"] and booking["booker_person_id"] != booking["driver_person_id"]:
            recipients.append(booking["booker_person_id"])
        result = []
        for recipient in recipients:
            person = c.execute("SELECT * FROM people WHERE id=?", (recipient,)).fetchone()
            channels = []
            if plan["zalo_enabled"] and person["phone"]:
                channels.append("zalo")
            if plan["sms_enabled"] and person["phone"]:
                channels.append("sms")
            if plan["email_enabled"] and person["email"]:
                channels.append("email")
            if not channels:
                channels = ["email" if person["email"] else "sms"]
            result.append((recipient, channels))
        return result, plan

    def expire_held_bookings(self) -> int:
        count = 0
        with self.db.transaction(immediate=True) as c:
            for b in c.execute(
                "SELECT * FROM bookings WHERE status='held' AND hold_expires_at<=?", (iso(self.now()),)
            ).fetchall():
                self._expire_hold_in_transaction(c, b)
                count += 1
        return count
