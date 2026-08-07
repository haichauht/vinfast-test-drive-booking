from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from datetime import datetime, timedelta

from src.services.booking.common import iso, new_id
from src.services.booking.errors import BookingError

_id = new_id


class AccessService:
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
        if not normalized_code:
            raise BookingError("INVALID_INPUT", "Cần nhập mã lịch để xác thực.")
        if preferred_channel not in {"zalo", "sms", "email"}:
            raise BookingError("INVALID_INPUT", "Kênh OTP phải là zalo, sms hoặc email.")
        normalized = contact_value.strip().lower()
        if not normalized or (preferred_channel == "email") != ("@" in normalized):
            raise BookingError("INVALID_INPUT", "Thong tin lien he khong phu hop voi kenh OTP.")
        destination_hash = self._hash(normalized, "destination")
        with self.db.transaction(immediate=True) as c:
            # The booking code is the primary identifier. Never fall back to a
            # different booking merely because the same phone appears there.
            booking = c.execute("SELECT * FROM bookings WHERE booking_code=?", (normalized_code,)).fetchone()
            if not booking:
                raise BookingError("BOOKING_ACCESS_NOT_AVAILABLE", "Không tìm thấy mã lịch này.")
            contact_matches = c.execute(
                "SELECT 1 FROM people WHERE id IN (?,?) AND (lower(email)=? OR phone=?) LIMIT 1",
                (booking["booker_person_id"], booking["driver_person_id"], normalized, contact_value.strip()),
            ).fetchone()
            if not contact_matches:
                raise BookingError("BOOKING_ACCESS_NOT_AVAILABLE", "Số điện thoại hoặc email không thuộc mã lịch này.")
            if preferred_channel == "zalo" and not hasattr(self.otp_sender, "is_linked"):
                raise BookingError("ZALO_NOT_CONFIGURED", "KÃªnh Zalo chÆ°a Ä‘Æ°á»£c cáº¥u hÃ¬nh.")
            if preferred_channel == "zalo" and not self.otp_sender.is_linked(contact_value):
                raise BookingError("ZALO_NOT_LINKED", "Sá»‘ Ä‘iá»‡n thoáº¡i chÆ°a liÃªn káº¿t vá»›i Zalo Bot.")
            if booking["status"] == "held" or (
                purpose in {"reschedule", "cancel", "update_details", "update_notifications"}
                and booking["status"] != "confirmed"
            ):
                raise BookingError("BOOKING_ACCESS_NOT_AVAILABLE", "Không thể cấp quyền truy cập booking.")
            latest = c.execute(
                "SELECT created_at FROM otp_challenges WHERE booking_id=? AND destination_hash=? AND status='pending' AND expires_at>? "
                "ORDER BY created_at DESC LIMIT 1",
                (booking["id"], destination_hash, iso(self.now())),
            ).fetchone()
            if latest:
                elapsed = (self.now() - datetime.fromisoformat(latest["created_at"])).total_seconds()
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
                raise BookingError("OTP_INVALID", "OTP khÃ´ng há»£p lá»‡.")
            if ch["status"] != "pending":
                raise BookingError(
                    "OTP_LOCKED" if ch["status"] == "locked" else "OTP_INVALID", "OTP khÃ´ng cÃ²n dÃ¹ng Ä‘Æ°á»£c."
                )
            if datetime.fromisoformat(ch["expires_at"]) <= self.now():
                c.execute("UPDATE otp_challenges SET status='expired' WHERE id=?", (challenge_id,))
                raise BookingError("OTP_EXPIRED", "OTP Ä‘Ã£ háº¿t háº¡n.")
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
                    f"OTP khÃ´ng Ä‘Ãºng. CÃ²n {max(0, ch['max_attempts'] - attempts)} láº§n thá»­.",
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
            if not session or session["revoked_at"] or datetime.fromisoformat(session["expires_at"]) <= self.now():
                raise BookingError("ACCESS_SESSION_EXPIRED", "PhiÃªn truy cáº­p Ä‘Ã£ háº¿t háº¡n.")
            if "read_booking" not in json.loads(session["permissions_json"]):
                raise BookingError("ACCESS_DENIED", "KhÃ´ng cÃ³ quyá»n Ä‘á»c booking.")
            b = c.execute("SELECT * FROM bookings WHERE id=?", (session["booking_id"],)).fetchone()
            if (booking_id and booking_id != b["id"]) or (booking_code and booking_code != b["booking_code"]):
                raise BookingError("ACCESS_SESSION_SCOPE_MISMATCH", "Phiên không thuộc booking này.")
            result = self._draft(c, b["id"], require_held=False)
            result["slot"] = self._row(
                c.execute("SELECT * FROM test_drive_slots WHERE id=?", (b["slot_id"],)).fetchone()
            )
            catalog = c.execute(
                "SELECT m.*,v.id variant_id,v.name variant_name,s.name showroom_name FROM test_drive_slots t JOIN demo_vehicles d ON d.id=t.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id JOIN vehicle_models m ON m.id=v.model_id JOIN showrooms s ON s.id=t.showroom_id WHERE t.id=?",
                (b["slot_id"],),
            ).fetchone()
            result["vehicle"] = self._row(catalog)
            result["showroom"] = {"id": result["slot"]["showroom_id"], "name": catalog["showroom_name"]}
            permissions = json.loads(session["permissions_json"])
            result["allowed_actions"] = [
                action
                for action in ("reschedule", "cancel", "update_details", "update_notifications")
                if b["status"] == "confirmed"
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

    def _require_access(self, c, token: str, booking_id: str, permission: str) -> sqlite3.Row:
        session = c.execute(
            "SELECT * FROM booking_access_sessions WHERE token_hash=?", (self._hash(token, "session"),)
        ).fetchone()
        if not session or session["revoked_at"] or datetime.fromisoformat(session["expires_at"]) <= self.now():
            raise BookingError("ACCESS_SESSION_EXPIRED", "PhiÃªn truy cáº­p Ä‘Ã£ háº¿t háº¡n.")
        if session["booking_id"] != booking_id:
            raise BookingError("ACCESS_SESSION_SCOPE_MISMATCH", "Phiên không thuộc booking này.")
        if permission not in json.loads(session["permissions_json"]):
            raise BookingError("ACCESS_DENIED", "Phiên không có quyền thực hiện thao tác này.")
        return session
