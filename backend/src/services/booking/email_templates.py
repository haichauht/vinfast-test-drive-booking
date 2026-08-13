from __future__ import annotations

from dataclasses import dataclass
from html import escape
from zoneinfo import ZoneInfo

from src.services.booking.common import parse_utc

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
WEEKDAYS_VI = ("Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "Chu nhat")


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    plain_text: str
    html: str


def render_otp_email(*, code: str, expires_in_seconds: int) -> RenderedEmail:
    minutes = max(1, expires_in_seconds // 60)
    subject = "Ma OTP xac thuc lich lai thu VinFast"
    plain = (
        "Ma OTP cua ban la: "
        f"{code}\nMa co hieu luc trong {expires_in_seconds} giay. "
        "Vui long khong chia se ma nay voi bat ky ai."
    )
    html = _html_document(
        title="Ma OTP xac thuc",
        intro="Dung ma ben duoi de xac thuc lich lai thu VinFast cua ban.",
        rows=(("Ma OTP", code), ("Hieu luc", f"{minutes} phut")),
        footer="Vui long khong chia se ma nay voi bat ky ai.",
    )
    return RenderedEmail(subject=subject, plain_text=plain, html=html)


def render_booking_email(notification_type: str, row) -> RenderedEmail:
    if not row:
        subject = "Cap nhat lich lai thu VinFast"
        plain = "Lich lai thu VinFast cua ban da duoc cap nhat."
        return RenderedEmail(subject=subject, plain_text=plain, html=_html_document(title=subject, intro=plain, rows=()))

    start = parse_utc(row["start_at"]).astimezone(VIETNAM_TZ)
    heading = _heading(notification_type)
    subject = f"{heading} - {row['booking_code'] or 'VinFast'}"
    staff = row["staff_name"] or "VinFast se lien he"
    if row["staff_phone"]:
        staff = f"{staff} - {row['staff_phone']}"
    rows = (
        ("Ma lich", row["booking_code"] or "-"),
        ("Nguoi dat lich", row["booker_name"] or "-"),
        ("Nguoi lai thu", row["driver_name"] or "-"),
        ("Dien thoai", row["driver_phone"] or "-"),
        ("Email", row["driver_email"] or "-"),
        ("Mau xe", f"{row['model_name']} {row['variant_name']}"),
        ("Showroom", row["showroom_name"]),
        ("Thoi gian", f"{start.strftime('%H:%M')} - {WEEKDAYS_VI[start.weekday()]}, {start.strftime('%d/%m/%Y')}"),
        ("Tu van vien", staff),
    )
    plain = "\n".join((heading, *(f"{label}: {value}" for label, value in rows)))
    html = _html_document(title=heading, intro=_intro(notification_type), rows=rows)
    return RenderedEmail(subject=subject, plain_text=plain, html=html)


def _heading(notification_type: str) -> str:
    return {
        "booking_confirmation": "Lich lai thu da xac nhan",
        "booking_update": "Thong tin lich lai thu da cap nhat",
        "reschedule_confirmation": "Lich lai thu da doi gio",
        "cancellation_confirmation": "Lich lai thu da huy",
        "reminder": "Nhac lich lai thu VinFast",
        "reminder_24h": "Nhac lich lai thu VinFast",
        "reminder_2h": "Nhac lich lai thu VinFast",
    }.get(notification_type, "Cap nhat lich lai thu VinFast")


def _intro(notification_type: str) -> str:
    return {
        "booking_confirmation": "Cam on ban da dat lich lai thu. Thong tin lich hen cua ban nhu sau.",
        "booking_update": "Thong tin lich lai thu cua ban vua duoc cap nhat.",
        "reschedule_confirmation": "Lich lai thu cua ban da duoc doi sang thoi gian moi.",
        "cancellation_confirmation": "Lich lai thu cua ban da duoc huy theo yeu cau.",
        "reminder": "Day la email nhac lich lai thu sap dien ra.",
        "reminder_24h": "Day la email nhac lich lai thu sap dien ra.",
        "reminder_2h": "Day la email nhac lich lai thu sap dien ra.",
    }.get(notification_type, "Lich lai thu VinFast cua ban co cap nhat moi.")


def _html_document(*, title: str, intro: str, rows, footer: str | None = None) -> str:
    body_rows = "\n".join(
        f"<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>" for label, value in rows
    )
    footer_html = f"  <p>{escape(footer)}</p>" if footer else ""
    return f"""<!doctype html>
<html>
<body style="font-family:Arial,sans-serif;color:#111827;line-height:1.5">
  <h2>{escape(title)}</h2>
  <p>{escape(intro)}</p>
  <table cellpadding="6" cellspacing="0" style="border-collapse:collapse">{body_rows}</table>
{footer_html}
</body>
</html>"""
