from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from src.database.rows import DbRow
from src.services.booking.base import BookingBase
from src.services.booking.common import iso, new_id, normalize_phone, parse_utc
from src.services.booking.errors import BookingError

_id = new_id


class AccessService(BookingBase):
    def request_access(
        self,
        booking_code: str | None,
        contact_value: str,
        purpose: str,
        preferred_channel: str = "sms",
        *,
        expose_otp: bool = False,
    ) -> dict:
        permissions = {
            "lookup": ["read_booking"],
            "reschedule": ["read_booking", "search_reschedule", "hold_reschedule", "confirm_reschedule", "update_details"],
            "cancel": ["read_booking", "cancel_booking"],
            "update_details": ["read_booking", "update_details"],
            "update_notifications": ["read_booking", "update_notifications"],
        }
        if purpose not in permissions:
            raise BookingError("INVALID_INPUT", "Purpose khong hop le.")
        normalized_code = (booking_code or "").strip().upper()
        if preferred_channel not in {"zalo", "sms", "email"}:
            raise BookingError("INVALID_INPUT", "Kênh OTP phải là zalo, sms hoặc email.")
        contact = contact_value.strip()
        normalized = contact.lower() if preferred_channel == "email" else normalize_phone(contact)
        if not normalized or (preferred_channel == "email") != ("@" in normalized):
            raise BookingError("INVALID_INPUT", "Thong tin lien he khong phu hop voi kenh OTP.")
        destination_hash = self._hash(normalized, "destination")
        with self.db.transaction(immediate=True) as c:
            booking = c.execute("SELECT * FROM bookings WHERE booking_code=?", (normalized_code,)).fetchone() if normalized_code else c.execute(
                "SELECT b.* FROM bookings b JOIN people booker ON booker.id=b.booker_person_id "
                "LEFT JOIN people driver ON driver.id=b.driver_person_id "
                "WHERE booker.normalized_phone=? OR driver.normalized_phone=? "
                "ORDER BY COALESCE(b.confirmed_at,b.held_at) DESC LIMIT 1",
                (normalized, normalized),
            ).fetchone()
            if not booking:
                raise BookingError("BOOKING_ACCESS_NOT_AVAILABLE", "Không tìm thấy lịch hẹn thuộc số điện thoại này.")
            contact_matches = c.execute(
                "SELECT 1 FROM people WHERE id IN (?,?) AND (lower(email)=? OR normalized_phone=? OR phone=?) LIMIT 1",
                (booking["booker_person_id"], booking["driver_person_id"], normalized, normalized, contact),
            ).fetchone()
            if not contact_matches:
                raise BookingError("BOOKING_ACCESS_NOT_AVAILABLE", "Số điện thoại hoặc email không thuộc mã lịch này.")
            if preferred_channel == "zalo" and not hasattr(self.otp_sender, "is_linked"):
                raise BookingError("ZALO_NOT_CONFIGURED", "Kênh Zalo chưa được cấu hình.")
            if preferred_channel == "zalo" and not self.otp_sender.is_linked(contact_value):
                raise BookingError("ZALO_NOT_LINKED", "Số điện thoại chưa liên kết với Zalo Bot.")
            if booking["status"] == "held" or (
                purpose in {"reschedule", "cancel", "update_details", "update_notifications"}
                and booking["status"] != "confirmed"
            ):
                raise BookingError("BOOKING_ACCESS_NOT_AVAILABLE", "Không thể cấp quyền truy cập booking.")
            latest = c.execute(
                "SELECT created_at FROM otp_challenges WHERE booking_id=? AND destination_hash=? "
                "ORDER BY created_at DESC LIMIT 1",
                (booking["id"], destination_hash),
            ).fetchone()
            if latest:
                elapsed = (parse_utc(self.now()) - parse_utc(latest["created_at"])).total_seconds()
                if elapsed < self.otp_resend_cooldown_seconds:
                    remaining = max(1, int(self.otp_resend_cooldown_seconds - elapsed))
                    raise BookingError("OTP_RATE_LIMITED", f"Vui lòng chờ {remaining} giây trước khi gửi lại OTP.", retryable=True)
            c.execute(
                "UPDATE otp_challenges SET status='superseded' WHERE booking_id=? AND status='pending'",
                (booking["id"],),
            )
            code = f"{secrets.randbelow(1000000):06d}"
            salt = secrets.token_hex(8)
            challenge_id = _id("otp")
            expires_at = self.now() + timedelta(seconds=self.otp_ttl_seconds)
            masked = self._mask(contact_value)
            c.execute(
                "INSERT INTO otp_challenges(id,booking_id,purpose,channel,destination_masked,"
                "destination_hash,code_hash,expires_at,max_attempts,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    challenge_id,
                    booking["id"],
                    purpose,
                    preferred_channel,
                    masked,
                    destination_hash,
                    salt + ":" + self._hash(code, salt),
                    iso(expires_at),
                    self.otp_max_attempts,
                    iso(self.now()),
                ),
            )
            self._event(c, booking["id"], "otp_requested", "user", {"purpose": purpose})
        delivery = self.otp_sender.send(
            channel=preferred_channel,
            destination=contact_value,
            code=code,
            expires_in_seconds=self.otp_ttl_seconds,
        )
        result = {
            "challenge_id": challenge_id,
            "destination_masked": masked,
            "expires_at": iso(expires_at),
            "retry_after_seconds": self.otp_resend_cooldown_seconds,
            "max_attempts": self.otp_max_attempts,
            "available_channels": [preferred_channel],
            "provider_status": getattr(delivery, "provider_status", "mocked"),
            "provider_message_id": getattr(delivery, "provider_message_id", None),
            "is_mock": getattr(delivery, "is_mock", True),
            "missing_fields": [],
            "suggested_next_action": "enter_otp",
        }
        if expose_otp:
            result["otp_code"] = code
        return result

    def _hash(self, value, salt):
        return hmac.new(self.otp_secret, (salt + value).encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _mask(value):
        if "@" in value:
            account, domain = value.split("@", 1)
            return account[:1] + "***@" + domain
        return "*" * max(0, len(value) - 3) + value[-3:]

    def verify_access(self, challenge_id: str, otp_code: str) -> dict:
        with self.db.transaction(immediate=True) as c:
            ch = c.execute("SELECT * FROM otp_challenges WHERE id=?", (challenge_id,)).fetchone()
            if not ch:
                raise BookingError("OTP_INVALID", "OTP không hợp lệ.")
            if ch["status"] != "pending":
                raise BookingError(
                    "OTP_LOCKED" if ch["status"] == "locked" else "OTP_INVALID", "OTP không còn dùng được."
                )
            if parse_utc(ch["expires_at"]) <= parse_utc(self.now()):
                c.execute("UPDATE otp_challenges SET status='expired' WHERE id=?", (challenge_id,))
                raise BookingError("OTP_EXPIRED", "OTP đã hết hạn.")
            salt, digest = ch["code_hash"].split(":", 1)
            if not hmac.compare_digest(self._hash(otp_code, salt), digest):
                attempts = ch["attempt_count"] + 1
                status = "locked" if attempts >= ch["max_attempts"] else "pending"
                c.execute(
                    "UPDATE otp_challenges SET attempt_count=?,status=? WHERE id=?", (attempts, status, challenge_id)
                )
                # Persist the security counter before raising the domain error;
                # otherwise the transaction context would roll it back.
                c.commit()
                error = BookingError(
                    "OTP_LOCKED" if status == "locked" else "OTP_INVALID",
                    f"OTP không đúng. Còn {max(0, ch['max_attempts'] - attempts)} lần thử.",
                )
                error.remaining_attempts = max(0, ch["max_attempts"] - attempts)
                raise error
            now = iso(self.now())
            c.execute(
                "UPDATE otp_challenges SET status='verified',verified_at=?,consumed_at=? WHERE id=?",
                (now, now, challenge_id),
            )
            raw = secrets.token_urlsafe(32)
            token_hash = self._hash(raw, "session")
            perms = {
                "lookup": ["read_booking"],
                "reschedule": ["read_booking", "search_reschedule", "hold_reschedule", "confirm_reschedule", "update_details"],
                "cancel": ["read_booking", "cancel_booking"],
                "update_details": ["read_booking", "update_details"],
                "update_notifications": ["read_booking", "update_notifications"],
            }[ch["purpose"]]
            expiry = self.now() + timedelta(seconds=self.access_session_ttl_seconds)
            c.execute(
                "INSERT INTO booking_access_sessions VALUES(?,?,?,?,?,?,?,?)",
                (_id("session"), token_hash, ch["booking_id"], challenge_id, json.dumps(perms), iso(expiry), None, now),
            )
            self._event(c, ch["booking_id"], "otp_verified", "user")
            return {
                "access_session_token": raw,
                "booking_id": ch["booking_id"],
                "permissions": perms,
                "session_expires_at": iso(expiry),
            }

    def get_booking_details(
        self, access_session_token: str, *, booking_id: str | None = None, booking_code: str | None = None
    ) -> dict:
        if (booking_id is None) == (booking_code is None):
            raise BookingError("INVALID_INPUT", "Cần đúng một trong booking_id hoặc booking_code.")
        with self.db.connect() as c:
            session = c.execute(
                "SELECT * FROM booking_access_sessions WHERE token_hash=?",
                (self._hash(access_session_token, "session"),),
            ).fetchone()
            if not session or session["revoked_at"] or parse_utc(session["expires_at"]) <= parse_utc(self.now()):
                raise BookingError("ACCESS_SESSION_EXPIRED", "Phiên truy cập đã hết hạn.")
            if "read_booking" not in json.loads(session["permissions_json"]):
                raise BookingError("ACCESS_DENIED", "Không có quyền đọc booking.")
            target_id = booking_id or c.execute("SELECT id FROM bookings WHERE booking_code=?", (booking_code,)).fetchone()
            target_id = target_id["id"] if target_id and not isinstance(target_id, str) else target_id
            if target_id != session["booking_id"]:
                raise BookingError("ACCESS_SESSION_SCOPE_MISMATCH", "Phiên không thuộc booking này.")
            target_booking = c.execute("SELECT * FROM bookings WHERE id=?", (target_id,)).fetchone()
            result = self._draft(c, target_id, require_held=False)
            result["slot"] = self._row(
                c.execute("SELECT * FROM test_drive_slots WHERE id=?", (result["slot_id"],)).fetchone()
            )
            catalog = c.execute(
                "SELECT m.*,v.id variant_id,v.name variant_name,s.name showroom_name,s.address showroom_address FROM test_drive_slots t JOIN demo_vehicles d ON d.id=t.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id JOIN vehicle_models m ON m.id=v.model_id JOIN showrooms s ON s.id=t.showroom_id WHERE t.id=?",
                (result["slot_id"],),
            ).fetchone()
            result["vehicle"] = self._row(catalog)
            result["showroom"] = {"id": result["slot"]["showroom_id"], "name": catalog["showroom_name"], "address": catalog["showroom_address"]}
            advisor = c.execute("SELECT full_name,phone FROM sales_staff WHERE id=?", (target_booking["assigned_sales_staff_id"],)).fetchone() if target_booking["assigned_sales_staff_id"] else None
            result["advisor"] = self._row(advisor) or {"full_name": "Chưa phân công", "phone": None}
            permissions = json.loads(session["permissions_json"])
            result["allowed_actions"] = [
                action
                for action in ("reschedule", "cancel", "update_details", "update_notifications")
                if result["status"] == "confirmed"
                and {
                    "reschedule": "confirm_reschedule",
                    "cancel": "cancel_booking",
                    "update_details": "update_details",
                    "update_notifications": "update_notifications",
                }[action]
                in permissions
            ]
            result["session_expires_at"] = session["expires_at"]
            return result

    def list_bookings(self, access_session_token: str) -> list[dict]:
        with self.db.connect() as c:
            session = c.execute("SELECT * FROM booking_access_sessions WHERE token_hash=?", (self._hash(access_session_token, "session"),)).fetchone()
            if not session or session["revoked_at"] or parse_utc(session["expires_at"]) <= parse_utc(self.now()):
                raise BookingError("ACCESS_SESSION_EXPIRED", "Phiên truy cập đã hết hạn.")
            anchor = c.execute("SELECT * FROM bookings WHERE id=?", (session["booking_id"],)).fetchone()
            ids = [anchor["booker_person_id"], anchor["driver_person_id"]]
            phones = {row["normalized_phone"] for row in c.execute("SELECT normalized_phone FROM people WHERE id IN (?,?)", ids).fetchall() if row["normalized_phone"]}
            if not phones:
                return []
            marks = ",".join("?" * len(phones))
            rows = c.execute(
                f"SELECT b.id,b.booking_code,b.status,b.confirmed_at,booker.full_name booker_name,booker.phone,booker.email,m.name vehicle_name,s.name showroom_name,t.start_at "
                f"FROM bookings b JOIN people booker ON booker.id=b.booker_person_id JOIN test_drive_slots t ON t.id=b.slot_id JOIN demo_vehicles d ON d.id=t.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id JOIN vehicle_models m ON m.id=v.model_id JOIN showrooms s ON s.id=t.showroom_id "
                f"LEFT JOIN people driver ON driver.id=b.driver_person_id WHERE b.booking_code IS NOT NULL AND b.status IN ('confirmed','checked_in','completed','no_show') AND (booker.normalized_phone IN ({marks}) OR driver.normalized_phone IN ({marks})) ORDER BY CASE WHEN t.start_at >= ? THEN 0 ELSE 1 END, CASE WHEN t.start_at >= ? THEN t.start_at END ASC, t.start_at DESC",
                (*phones, *phones, iso(self.now()), iso(self.now())),
            ).fetchall()
            return [dict(row) for row in rows]

    def _same_phone_owner(self, c, anchor, target_id: str) -> bool:
        target = c.execute("SELECT * FROM bookings WHERE id=?", (target_id,)).fetchone()
        if not target:
            return False
        anchor_ids = [anchor["booker_person_id"], anchor["driver_person_id"]]
        target_ids = [target["booker_person_id"], target["driver_person_id"]]
        anchor_phones = {row["normalized_phone"] for row in c.execute("SELECT normalized_phone FROM people WHERE id IN (?,?)", anchor_ids).fetchall() if row["normalized_phone"]}
        target_phones = {row["normalized_phone"] for row in c.execute("SELECT normalized_phone FROM people WHERE id IN (?,?)", target_ids).fetchall() if row["normalized_phone"]}
        return bool(anchor_phones & target_phones)
    def _require_access(self, c, token: str, booking_id: str, permission: str) -> DbRow:
        session = c.execute(
            "SELECT * FROM booking_access_sessions WHERE token_hash=?", (self._hash(token, "session"),)
        ).fetchone()
        if not session or session["revoked_at"] or parse_utc(session["expires_at"]) <= parse_utc(self.now()):
            raise BookingError("ACCESS_SESSION_EXPIRED", "Phiên truy cập đã hết hạn.")
        if booking_id != session["booking_id"]:
            raise BookingError("ACCESS_SESSION_SCOPE_MISMATCH", "Phiên không thuộc booking này.")
        if permission not in json.loads(session["permissions_json"]):
            raise BookingError("ACCESS_DENIED", "Phiên không có quyền thực hiện thao tác này.")
        return session
