from __future__ import annotations

import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from src.services.booking.base import BookingBase
from src.services.booking.common import iso, parse_utc
from src.services.booking.email_templates import render_booking_email

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class BackgroundJobService(BookingBase):
    def dispatch_due_notifications(self, batch_size: int = 100, processing_timeout_seconds: int = 300) -> dict:
        stale_before = iso(self.now() - timedelta(seconds=processing_timeout_seconds))
        with self.db.transaction(immediate=True) as c:
            c.execute(
                "UPDATE notification_jobs SET status='pending',updated_at=?,error_message=? "
                "WHERE status='processing' AND last_attempt_at<=? AND attempt_count<max_attempts",
                (iso(self.now()), "processing_timeout_recovered", stale_before),
            )
            c.execute(
                "UPDATE notification_jobs SET status='failed',updated_at=?,error_message=? "
                "WHERE status='processing' AND last_attempt_at<=? AND attempt_count>=max_attempts",
                (iso(self.now()), "processing_timeout_terminal", stale_before),
            )
            rows = c.execute(
                "SELECT j.*,p.phone,p.email,p.preferred_channel FROM notification_jobs j "
                "JOIN people p ON p.id=j.recipient_person_id WHERE j.status='pending' AND j.scheduled_at<=? "
                "ORDER BY j.scheduled_at LIMIT ?",
                (iso(self.now()), batch_size),
            ).fetchall()
            ids = [row["id"] for row in rows]
            for job_id in ids:
                c.execute(
                    "UPDATE notification_jobs SET status='processing',attempt_count=attempt_count+1,last_attempt_at=?,updated_at=? WHERE id=? AND status='pending'",
                    (iso(self.now()), iso(self.now()), job_id),
                )
        sent = failed = 0
        for row in rows:
            destination = row["email"] if row["channel"] == "email" else row["phone"]
            try:
                rendered = self._render_notification(row["booking_id"], row["notification_type"])
                result = (
                    self.messaging_provider.send_message(
                        channel=row["channel"],
                        destination=destination,
                        subject=rendered.subject,
                        body=rendered.plain_text,
                        html_body=rendered.html,
                    )
                    if destination
                    else None
                )
                error_message = (
                    "recipient_channel_unavailable"
                    if result is None
                    else (result.sanitized_response or {}).get("error") or result.provider_status
                )
            except Exception as error:  # provider outages must not stop the remaining jobs
                result = None
                error_message = str(error)
            with self.db.transaction(immediate=True) as c:
                if result and result.provider_status == "sent":
                    c.execute(
                        "UPDATE notification_jobs SET status='sent',sent_at=?,provider_name=?,provider_status=?,provider_message_id=?,is_mock=?,provider_response_json=?,updated_at=? WHERE id=? AND status='processing'",
                        (
                            iso(self.now()),
                            result.provider,
                            result.provider_status,
                            result.provider_message_id,
                            int(result.is_mock),
                            json.dumps(result.sanitized_response or {}),
                            iso(self.now()),
                            row["id"],
                        ),
                    )
                    self._event(
                        c,
                        row["booking_id"],
                        "notification_sent",
                        "system",
                        {"job_id": row["id"], "provider_status": result.provider_status, "is_mock": result.is_mock},
                    )
                    sent += 1
                else:
                    retryable = getattr(result, "retryable", True) if result else True
                    terminal = not retryable or row["attempt_count"] + 1 >= row["max_attempts"]
                    c.execute(
                        "UPDATE notification_jobs SET status=?,provider_name=?,provider_status=?,is_mock=?,provider_response_json=?,error_message=?,updated_at=? WHERE id=? AND status='processing'",
                        (
                            "failed" if terminal else "pending",
                            getattr(result, "provider", None),
                            getattr(result, "provider_status", None),
                            int(getattr(result, "is_mock", True)),
                            json.dumps(getattr(result, "sanitized_response", None) or {}),
                            error_message,
                            iso(self.now()),
                            row["id"],
                        ),
                    )
                    failed += 1
        return {"claimed": len(rows), "sent": sent, "failed": failed, "is_mock": True}

    def _render_notification(self, booking_id: str, notification_type: str):
        with self.db.connect() as c:
            row = c.execute(
                "SELECT b.booking_code,booker.full_name booker_name,driver.full_name driver_name,"
                "driver.phone driver_phone,driver.email driver_email,m.name model_name,v.name variant_name,"
                "s.name showroom_name,t.start_at,staff.full_name staff_name,staff.phone staff_phone "
                "FROM bookings b JOIN test_drive_slots t ON t.id=b.slot_id JOIN showrooms s ON s.id=t.showroom_id "
                "JOIN demo_vehicles d ON d.id=t.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id "
                "JOIN vehicle_models m ON m.id=v.model_id "
                "LEFT JOIN people booker ON booker.id=b.booker_person_id "
                "LEFT JOIN people driver ON driver.id=b.driver_person_id "
                "LEFT JOIN sales_staff staff ON staff.id=b.assigned_sales_staff_id WHERE b.id=?",
                (booking_id,),
            ).fetchone()
        return render_booking_email(notification_type, row)
        if not row:
            return "Lịch lái thử VinFast của bạn đã được cập nhật."
        start = parse_utc(row["start_at"]).astimezone(VIETNAM_TZ)
        weekdays = ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật")
        heading = "Lịch lái thử đã xác nhận" if notification_type == "booking_confirmation" else "Cập nhật lịch lái thử"
        staff = row["staff_name"] or "Sẽ được VinFast liên hệ"
        if row["staff_phone"]:
            staff = f"{staff} · {row['staff_phone']}"
        return "\n".join(
            (
                heading,
                f"Mã lịch: {row['booking_code']}",
                f"Người đặt lịch: {row['booker_name'] or '—'}",
                f"Người lái thử: {row['driver_name'] or '—'}",
                f"Điện thoại: {row['driver_phone'] or '—'}",
                f"Email: {row['driver_email'] or '—'}",
                f"Mẫu xe: {row['model_name']} {row['variant_name']}",
                f"Showroom: {row['showroom_name']}",
                f"Thời gian: {start.strftime('%H:%M')} · {weekdays[start.weekday()]}, {start.strftime('%d/%m')}",
                f"Tư vấn viên: {staff}",
            )
        )
