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


from urllib.parse import quote

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
    showroom_name = row["showroom_name"] or "Showroom VinFast"
    maps_url = f"https://www.google.com/maps/search/?api=1&query={quote(showroom_name)}"

    rows = (
        ("Ma lich", row["booking_code"] or "-"),
        ("Nguoi dat lich", row["booker_name"] or "-"),
        ("Nguoi lai thu", row["driver_name"] or "-"),
        ("Dien thoai", row["driver_phone"] or "-"),
        ("Email", row["driver_email"] or "-"),
        ("Mau xe", f"{row['model_name']} {row['variant_name']}"),
        ("Showroom", showroom_name),
        ("Thoi gian", f"{start.strftime('%H:%M')} - {WEEKDAYS_VI[start.weekday()]}, {start.strftime('%d/%m/%Y')}"),
        ("Tu van vien", staff),
    )
    plain = "\n".join((heading, *(f"{label}: {value}" for label, value in rows), f"Chi duong Google Maps: {maps_url}"))
    html = _html_document(title=heading, intro=_intro(notification_type), rows=rows, maps_url=maps_url, showroom_name=showroom_name)
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


def _html_document(*, title: str, intro: str, rows, footer: str | None = None, maps_url: str | None = None, showroom_name: str | None = None) -> str:
    # 1. Render từng hàng dữ liệu (Bảng thông tin 2 cột đẹp mắt)
    body_rows = "".join(
        f"""
        <tr>
          <td style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; color: #6b7280; font-size: 13px; font-weight: 500; width: 35%;">{escape(str(label))}</td>
          <td style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; color: #111827; font-size: 14px; font-weight: 600;">{escape(str(value))}</td>
        </tr>
        """ for label, value in rows
    )

    footer_html = f'<p style="margin-top: 20px; font-size: 12px; color: #6b7280; text-align: center;">{escape(footer)}</p>' if footer else ""

    button_url = maps_url or "https://vinfast-mvp.pages.dev"
    button_label = f"🗺️ Chỉ đường đến {escape(showroom_name or 'Showroom')} (Google Maps) →" if maps_url else "Quản lý Lịch hẹn của bạn →"

    # 2. Khung HTML Email chuẩn thương hiệu VinFast
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 20px 0; background-color: #f3f4f6; font-family: 'Segoe UI', Arial, sans-serif; -webkit-font-smoothing: antialiased;">

  <!-- Container chính 600px -->
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f3f4f6;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
          
          <!-- Header Banner VinFast -->
          <tr>
            <td style="background-color: #0C64E6; padding: 28px 32px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800; letter-spacing: 2px;">VINFAST</h1>
              <p style="margin: 4px 0 0; color: #dbeafe; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Mãnh liệt tinh thần Việt Nam</p>
            </td>
          </tr>

          <!-- Nội dung chính -->
          <tr>
            <td style="padding: 32px;">
              <h2 style="margin: 0 0 12px; color: #111827; font-size: 20px; font-weight: 700;">{escape(title)}</h2>
              <p style="margin: 0 0 24px; color: #4b5563; font-size: 14px; line-height: 1.6;">{escape(intro)}</p>

              <!-- Bảng Thông tin Booking -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f9fafb; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden;">
                {body_rows}
              </table>

              <!-- Nút Action chỉ đường Google Maps -->
              <div style="margin-top: 28px; text-align: center;">
                <a href="{escape(button_url)}" target="_blank" style="display: inline-block; background-color: #0C64E6; color: #ffffff; font-size: 14px; font-weight: 600; text-decoration: none; padding: 13px 28px; border-radius: 8px;">
                  {button_label}
                </a>
              </div>

              {footer_html}
            </td>
          </tr>

          <!-- Footer Email -->
          <tr>
            <td style="background-color: #f9fafb; padding: 20px 32px; border-top: 1px solid #e5e7eb; text-align: center; color: #9ca3af; font-size: 12px;">
              <p style="margin: 0 0 4px;">© 2026 VinFast. Tất cả các quyền được bảo lưu.</p>
              <p style="margin: 0;">Hotline hỗ trợ: 1900 23 23 89 | Email: cskh@vinfast.vn</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""
