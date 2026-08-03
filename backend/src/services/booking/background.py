from __future__ import annotations

import json

from src.services.booking.common import iso


class BackgroundJobService:
    def dispatch_due_notifications(self, batch_size: int = 100) -> dict:
        with self.db.transaction(immediate=True) as c:
            rows = c.execute(
                "SELECT j.*,p.phone,p.email,p.preferred_channel FROM notification_jobs j "
                "JOIN people p ON p.id=j.recipient_person_id WHERE j.status='pending' AND j.scheduled_at<=? "
                "ORDER BY j.scheduled_at LIMIT ?",
                (iso(self.now()), batch_size),
            ).fetchall()
            ids = [row["id"] for row in rows]
            for job_id in ids:
                c.execute("UPDATE notification_jobs SET status='processing',attempt_count=attempt_count+1,last_attempt_at=?,updated_at=? WHERE id=? AND status='pending'", (iso(self.now()), iso(self.now()), job_id))
        sent = failed = 0
        for row in rows:
            destination = row["email"] if row["channel"] == "email" else row["phone"]
            if not destination:
                result = None
            else:
                result = self.messaging_provider.send_message(
                    channel=row["channel"], destination=destination, body=self._render_notification(row["booking_id"], row["notification_type"])
                )
            with self.db.transaction(immediate=True) as c:
                if result:
                    c.execute(
                        "UPDATE notification_jobs SET status='sent',sent_at=?,provider_name=?,provider_status=?,provider_message_id=?,is_mock=?,provider_response_json=?,updated_at=? WHERE id=? AND status='processing'",
                        (iso(self.now()), result.provider, result.provider_status, result.provider_message_id, int(result.is_mock), json.dumps(result.sanitized_response or {}), iso(self.now()), row["id"]),
                    )
                    self._event(c, row["booking_id"], "notification_sent", "system", {"job_id": row["id"], "provider_status": result.provider_status, "is_mock": result.is_mock})
                    sent += 1
                else:
                    terminal = row["attempt_count"] + 1 >= row["max_attempts"]
                    c.execute("UPDATE notification_jobs SET status=?,error_message=?,updated_at=? WHERE id=? AND status='processing'", ("failed" if terminal else "pending", "recipient_channel_unavailable", iso(self.now()), row["id"]))
                    failed += 1
        return {"claimed": len(rows), "sent": sent, "failed": failed, "is_mock": True}

    def _render_notification(self, booking_id: str, notification_type: str) -> str:
        with self.db.connect() as c:
            row = c.execute(
                "SELECT m.name model_name,v.name variant_name,s.name showroom_name,t.start_at,t.end_at "
                "FROM bookings b JOIN test_drive_slots t ON t.id=b.slot_id JOIN showrooms s ON s.id=t.showroom_id "
                "JOIN demo_vehicles d ON d.id=t.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id "
                "JOIN vehicle_models m ON m.id=v.model_id WHERE b.id=?", (booking_id,)
            ).fetchone()
        return f"{notification_type}: {row['model_name']} {row['variant_name']}, {row['start_at']}–{row['end_at']}, {row['showroom_name']}."
