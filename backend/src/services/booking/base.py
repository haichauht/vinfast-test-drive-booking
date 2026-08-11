from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from src.database import Database
from src.services.booking.common import iso, new_id, row_to_dict
from src.services.booking.errors import BookingError

_id = new_id


class BookingBase:
    """Shared typed contract for the BookingService mixins.

    Concrete implementations live in sibling mixins on ``BookingService``.
    The declarations make those dependencies explicit to static type checkers.
    """

    db: Database
    now: Callable[[], datetime]
    map_provider: Any
    messaging_provider: Any
    otp_sender: Any
    otp_secret: bytes
    otp_max_attempts: int
    otp_ttl_seconds: int
    otp_resend_cooldown_seconds: int
    access_session_ttl_seconds: int
    IDEMPOTENCY_PREFIXES = {
        "hold_slot": "hold:",
        "confirm_booking": "confirm:",
        "hold_reschedule": "reschedule-hold:",
        "confirm_reschedule": "reschedule-confirm:",
        "cancel_booking": "cancel:",
        "record_license_check": "staff-license:",
        "check_in_booking": "staff-checkin:",
        "test_drive_completed": "staff-complete:",
        "booking_marked_no_show": "staff-noshow:",
    }

    @staticmethod
    def _row(row):
        return row_to_dict(row)

    def _event(self, c, booking_id: str, event: str, actor: str = "system", payload: dict | None = None):
        blocked = {
            "otp",
            "otp_code",
            "access_token",
            "access_session_token",
            "phone",
            "email",
            "contact_value",
            "reason",
            "note",
        }
        safe_payload = {key: value for key, value in (payload or {}).items() if key.lower() not in blocked}
        c.execute(
            "INSERT INTO booking_events VALUES(?,?,?,?,?,?,?)",
            (_id("evt"), booking_id, event, actor, None, json.dumps(safe_payload), iso(self.now())),
        )

    @staticmethod
    def _request_hash(payload: dict) -> str:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def _idempotent_response(cls, c, action_id: str, operation: str, payload: dict):
        prefix = cls.IDEMPOTENCY_PREFIXES[operation]
        if not action_id.startswith(prefix) or len(action_id) <= len(prefix):
            raise BookingError("INVALID_INPUT", f"ui_action_id của {operation} phải bắt đầu bằng '{prefix}'.")
        request_hash = cls._request_hash(payload)
        row = c.execute(
            "SELECT operation,request_hash,response_json FROM idempotency_records WHERE action_id=?", (action_id,)
        ).fetchone()
        if not row:
            return None
        if row["operation"] != operation:
            raise BookingError("IDEMPOTENCY_CONFLICT", "Idempotency key đã được dùng cho thao tác khác.")
        if row["request_hash"] and row["request_hash"] != request_hash:
            raise BookingError("IDEMPOTENCY_CONFLICT", "Idempotency key đã được dùng với payload khác.")
        return json.loads(row["response_json"])

    @classmethod
    def _save_idempotency(cls, c, action_id: str, operation: str, payload: dict, response: dict, created_at: str):
        c.execute(
            "INSERT INTO idempotency_records(action_id,operation,request_hash,status,response_json,created_at) "
            "VALUES(?,?,?,'succeeded',?,?)",
            (action_id, operation, cls._request_hash(payload), json.dumps(response), created_at),
        )

    # Implemented by sibling service mixins in the composed BookingService.
    def _require_access(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def _draft(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def _create_jobs(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def _create_transactional_notification_jobs(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def _hash(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def hold_slot(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
