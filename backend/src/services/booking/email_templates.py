"""Mẫu email gửi cho khách: mã OTP và các thông báo về lịch lái thử.

Viết lại 18/08/2026 theo phản hồi của chủ dự án. Hai việc được sửa:

1. TOÀN BỘ CHỮ NAY CÓ DẤU. Bản trước viết tiếng Việt không dấu ("Ma OTP xac thuc lich lai
   thu") — đọc khó và trông như thư rác, nhất là khi đây là email xác nhận đầu tiên khách
   nhận từ VinFast. `EmailMessage.set_content()` / `add_alternative()` của Python tự chọn
   UTF-8 khi gặp ký tự ngoài ASCII, còn dòng Subject được tự mã hoá theo RFC 2047, nên
   không cần đổi gì ở `gmail_provider.py`.

2. BỐ CỤC HTML DỰNG LẠI. Bản trước chỉ có `<h2>`, `<p>` và một `<table>` trần: không khai
   báo charset, không giới hạn bề ngang nên trên màn rộng chữ chạy dài sát mép trái, cỡ chữ
   thả theo mặc định của từng ứng dụng mail nên mỗi nơi một kiểu.

   Nguyên tắc khi sửa file này: email KHÔNG dùng flex/grid/`<style>` ngoài — Outlook và một
   số webmail bỏ qua hoặc hiểu sai. Chỉ dùng bảng lồng bảng và style nội tuyến; đó là lý do
   mã dưới đây trông cổ hơn HTML thường.

3. RÚT NGẮN CHIỀU CAO (18/08/2026). Bản trước mỗi dòng xếp nhãn trên - giá trị dưới, 9 dòng
   liền nhau nên thư cao hơn 900px, mở trên Gmail phải cuộn mới xem hết. Nay mỗi dòng gói
   trong MỘT hàng: nhãn xám bên trái, giá trị đậm bên phải (kiểu hoá đơn), và gộp điện thoại
   với email thành một dòng "Liên hệ". Chiều cao còn khoảng một nửa, vừa trọn một màn.

4. LOGO THAY CHO CHỮ. Đầu thư trước đây là chữ "VINFAST" màu xanh dựng bằng CSS. Nay dùng
   ảnh logo thật, nhúng theo kiểu CID (`cid:vinfast-logo`) chứ không phải `data:` URI —
   Gmail chặn ảnh `data:`. File ảnh nằm cạnh file này ở `assets/vinfast-logo.png` và được
   `RenderedEmail.inline_images` trả về cho tầng gửi thư đính kèm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

from src.services.booking.common import parse_utc

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
WEEKDAYS_VI = ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật")

# Màu và font lấy đúng theo giao diện web để email không lạc khỏi thương hiệu.
_INK = "#171a20"
_MUTED = "#6b7280"
_BLUE = "#1464f4"
_PAPER = "#f4f4f4"
_LINE = "#e5e7eb"
_FONT = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
)

_LOGO_PATH = Path(__file__).with_name("assets") / "vinfast-logo.png"
_LOGO_CID = "vinfast-logo"


@lru_cache(maxsize=1)
def _logo_bytes() -> bytes:
    """Đọc một lần rồi giữ trong bộ nhớ — mỗi email đều cần đúng file này."""
    try:
        return _LOGO_PATH.read_bytes()
    except OSError:
        return b""


@dataclass(frozen=True)
class InlineImage:
    """Ảnh nhúng trong thân thư, tham chiếu bằng `cid:<cid>`."""

    cid: str
    content: bytes
    subtype: str = "png"


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    plain_text: str
    html: str
    # Tầng gửi thư đính kèm những ảnh này dưới dạng inline; rỗng thì thân thư vẫn đọc được
    # bình thường, chỉ mất logo và hiện chữ thay thế "VinFast".
    inline_images: tuple[InlineImage, ...] = field(default_factory=tuple)


def _inline_logo() -> tuple[InlineImage, ...]:
    data = _logo_bytes()
    return (InlineImage(cid=_LOGO_CID, content=data),) if data else ()


def render_otp_email(*, code: str, expires_in_seconds: int) -> RenderedEmail:
    minutes = max(1, expires_in_seconds // 60)
    subject = "Mã OTP xác thực lịch lái thử VinFast"
    plain = (
        f"Mã OTP của bạn là: {code}\n"
        f"Mã có hiệu lực trong {expires_in_seconds} giây.\n"
        "Vui lòng không chia sẻ mã này với bất kỳ ai."
    )
    html = _html_document(
        title="Mã OTP xác thực",
        intro="Dùng mã bên dưới để xác thực lịch lái thử VinFast của bạn.",
        # Không lặp lại mã trong bảng: nó đã nằm ở khối lớn phía trên.
        rows=(("Hiệu lực của mã", f"{minutes} phút"),),
        footer="Vui lòng không chia sẻ mã này với bất kỳ ai.",
        highlight=code,
    )
    return RenderedEmail(subject=subject, plain_text=plain, html=html, inline_images=_inline_logo())


def render_booking_email(notification_type: str, row) -> RenderedEmail:
    if not row:
        subject = "Cập nhật lịch lái thử VinFast"
        plain = "Lịch lái thử VinFast của bạn đã được cập nhật."
        return RenderedEmail(
            subject=subject,
            plain_text=plain,
            html=_html_document(title=subject, intro=plain, rows=()),
            inline_images=_inline_logo(),
        )

    start = parse_utc(row["start_at"]).astimezone(VIETNAM_TZ)
    heading = _heading(notification_type)
    subject = f"{heading} - {row['booking_code'] or 'VinFast'}"
    staff = row["staff_name"] or "VinFast sẽ liên hệ"
    if row["staff_phone"]:
        staff = f"{staff} - {row['staff_phone']}"
    booker = row["booker_name"] or "-"
    driver = row["driver_name"] or "-"
    contact = " · ".join(v for v in (row["driver_phone"], row["driver_email"]) if v) or "-"
    people = (
        # Đặt hộ mới cần tách hai dòng; đa số trường hợp người đặt cũng là người lái.
        (("Người đặt lịch", booker), ("Người lái thử", driver))
        if driver != booker
        else ((("Người đặt & lái thử"), booker),)
    )
    # Nút chỉ đường Google Maps — tính năng đến từ nhánh testing (PR #55), giữ nguyên khi gộp.
    showroom_name = row["showroom_name"] or "Showroom VinFast"
    maps_url = f"https://www.google.com/maps/search/?api=1&query={quote(showroom_name)}"
    rows = (
        ("Mã lịch", row["booking_code"] or "-"),
        (
            "Thời gian",
            f"{start.strftime('%H:%M')} - {WEEKDAYS_VI[start.weekday()]}, {start.strftime('%d/%m/%Y')}",
        ),
        ("Mẫu xe", f"{row['model_name']} {row['variant_name']}"),
        ("Showroom", showroom_name),
        *people,
        ("Liên hệ", contact),
        ("Tư vấn viên", staff),
    )
    plain = "\n".join((heading, *(f"{label}: {value}" for label, value in rows)))
    html = _html_document(
        title=heading,
        intro=_intro(notification_type),
        rows=rows,
        footer=(
            "Cần đổi giờ hoặc huỷ lịch, bạn tra cứu bằng email đã đăng ký trên website VinFast."
        ),
        maps_url=maps_url,
        showroom_name=showroom_name,
    )
    return RenderedEmail(subject=subject, plain_text=plain, html=html, inline_images=_inline_logo())


def _heading(notification_type: str) -> str:
    return {
        "booking_confirmation": "Lịch lái thử đã xác nhận",
        "booking_update": "Thông tin lịch lái thử đã cập nhật",
        "reschedule_confirmation": "Lịch lái thử đã đổi giờ",
        "cancellation_confirmation": "Lịch lái thử đã huỷ",
        "reminder": "Nhắc lịch lái thử VinFast",
        "reminder_24h": "Nhắc lịch lái thử VinFast",
        "reminder_2h": "Nhắc lịch lái thử VinFast",
    }.get(notification_type, "Cập nhật lịch lái thử VinFast")


def _intro(notification_type: str) -> str:
    return {
        "booking_confirmation": (
            "Cảm ơn bạn đã đặt lịch lái thử. Thông tin lịch hẹn của bạn như sau."
        ),
        "booking_update": "Thông tin lịch lái thử của bạn vừa được cập nhật.",
        "reschedule_confirmation": "Lịch lái thử của bạn đã được đổi sang thời gian mới.",
        "cancellation_confirmation": "Lịch lái thử của bạn đã được huỷ theo yêu cầu.",
        "reminder": "Đây là email nhắc lịch lái thử sắp diễn ra.",
        "reminder_24h": "Đây là email nhắc lịch lái thử sắp diễn ra.",
        "reminder_2h": "Đây là email nhắc lịch lái thử sắp diễn ra.",
    }.get(notification_type, "Lịch lái thử VinFast của bạn có cập nhật mới.")


def _row_html(label: str, value: str, *, last: bool) -> str:
    """Một dòng thông tin gói trong MỘT hàng: nhãn trái, giá trị phải.

    Bản trước xếp nhãn trên - giá trị dưới nên mỗi dòng cao ~70px, chín dòng là thư đã dài quá
    một màn. Kiểu hoá đơn này cao khoảng một nửa mà vẫn đọc được, và chạy đúng ở mọi ứng dụng
    mail vì chỉ là một `<tr>` hai `<td>`.
    """
    border = "" if last else f"border-bottom:1px solid {_LINE};"
    return (
        f'<tr>'
        f'<td style="padding:11px 12px 11px 0;{border}font-size:14px;line-height:20px;'
        f'color:{_MUTED};white-space:nowrap;vertical-align:top;">{escape(str(label))}</td>'
        f'<td align="right" style="padding:11px 0;{border}font-size:15px;line-height:20px;'
        f'color:{_INK};font-weight:600;word-break:break-word;">{escape(str(value))}</td>'
        "</tr>"
    )


def _html_document(
    *,
    title: str,
    intro: str,
    rows,
    footer: str | None = None,
    highlight: str | None = None,
    maps_url: str | None = None,
    showroom_name: str | None = None,
) -> str:
    row_list = list(rows)
    body_rows = "\n".join(
        _row_html(label, value, last=(index == len(row_list) - 1))
        for index, (label, value) in enumerate(row_list)
    )
    table_html = (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="100%" style="width:100%;border-collapse:collapse;">{body_rows}</table>'
        if body_rows
        else ""
    )

    # Mã OTP được tách riêng thành một khối lớn: đây là thứ duy nhất người nhận cần đọc,
    # để lẫn trong bảng thì phải dò từng dòng mới thấy.
    highlight_html = (
        f'<div style="margin:0 0 24px;padding:18px 20px;background:{_PAPER};'
        f'border-radius:14px;text-align:center;">'
        f'<div style="font-size:32px;line-height:38px;font-weight:700;color:{_INK};'
        f'letter-spacing:6px;">{escape(str(highlight))}</div></div>'
        if highlight
        else ""
    )

    # Nút chỉ đường: chỉ hiện ở email về lịch hẹn (có showroom), không hiện ở email OTP.
    maps_html = (
        f'<div style="margin:18px 0 0;text-align:center;">'
        f'<a href="{escape(maps_url)}" target="_blank" rel="noreferrer" '
        f'style="display:inline-block;padding:12px 24px;border-radius:10px;'
        f'background:{_BLUE};color:#ffffff;font-size:14px;font-weight:600;'
        f'text-decoration:none;">Chỉ đường đến {escape(showroom_name or "showroom")}</a></div>'
        if maps_url
        else ""
    )

    footer_html = (
        f'<p style="margin:22px 0 0;font-size:13px;line-height:20px;color:{_MUTED};">'
        f"{escape(footer)}</p>"
        if footer
        else ""
    )

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:{_PAPER};">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="width:100%;background:{_PAPER};">
  <tr>
    <td align="center" style="padding:24px 16px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="560"
             style="width:560px;max-width:100%;background:#ffffff;border-radius:20px;
                    border:1px solid {_LINE};">
        <tr>
          <td style="padding:24px 30px 0;font-family:{_FONT};">
            <img src="cid:{_LOGO_CID}" alt="VinFast" width="120"
                 style="display:block;width:120px;height:auto;border:0;">
          </td>
        </tr>
        <tr>
          <td style="padding:14px 30px 0;font-family:{_FONT};">
            <h1 style="margin:0;font-size:23px;line-height:29px;font-weight:650;
                       color:{_INK};letter-spacing:-0.4px;">{escape(title)}</h1>
            <p style="margin:9px 0 18px;font-size:15px;line-height:22px;color:{_MUTED};">
              {escape(intro)}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 30px 24px;font-family:{_FONT};">
            {highlight_html}{table_html}{maps_html}{footer_html}
          </td>
        </tr>
      </table>
      <div style="font-family:{_FONT};font-size:12px;line-height:18px;color:{_MUTED};
                  padding:14px 8px 0;">
        Email tự động từ hệ thống đặt lịch lái thử VinFast.
      </div>
    </td>
  </tr>
</table>
</body>
</html>"""
