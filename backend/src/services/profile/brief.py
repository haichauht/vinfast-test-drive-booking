from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def _unique_text(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = " ".join(str(item or "").split()).strip(" .")
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _render_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _profile_fact_lines(participant: dict[str, Any]) -> list[str]:
    profile = participant.get("profile") or {}
    sections = profile.get("sections") or {}
    lines: list[str] = []
    for section_name in (
        "known_facts",
        "usage_context",
        "interests",
        "concerns",
        "preferences",
        "likely_intents",
    ):
        for signal in sections.get(section_name) or []:
            if str(signal.get("certainty") or "") == "possible":
                continue
            key = str(signal.get("key") or "")
            value = signal.get("value")
            description = " ".join(str(signal.get("description") or "").split()).strip(" .")
            if key == "household_size" and isinstance(value, int):
                lines.append(f"Gia đình có {value} người")
            elif key == "primary_use" and value is not None and value != "":
                lines.append(f"Mục đích sử dụng chính: {_render_value(value)}")
            elif description:
                lines.append(description)
            elif key and value is not None and value != "":
                lines.append(f"{key.replace('_', ' ')}: {_render_value(value)}")
    return _unique_text(lines)


def _signal_map(signals: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for signal in signals:
        subject = str(signal.get("subject") or "")
        key = str(signal.get("key") or "")
        if subject and key:
            result[(subject, key)] = signal
    return result


def _signal_value(signals: dict[tuple[str, str], dict[str, Any]], subject: str, key: str) -> Any:
    signal = signals.get((subject, key))
    return signal.get("value") if signal else None


def _format_start_at(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "Chưa có thông tin"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return raw
        local = parsed.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
        return local.strftime("%H:%M · %d/%m/%Y")
    except ValueError:
        return raw


def _guest_context(signals: dict[tuple[str, str], dict[str, Any]]) -> list[str]:
    raw = _signal_value(signals, "group", "additional_guest_context")
    values = raw if isinstance(raw, list) else [raw] if raw else []
    rendered: list[str] = []
    for value in values:
        if isinstance(value, dict):
            relationship = str(value.get("relationship") or value.get("role") or "người đi cùng")
            details: list[str] = [relationship]
            if value.get("age") is not None:
                details.append(f"{value['age']} tuổi")
            if value.get("will_drive") is True:
                details.append("cũng muốn lái thử")
            rendered.append(", ".join(details))
        else:
            rendered.append(str(value))

    for (subject, key), signal in signals.items():
        if subject != "group" or not key.startswith("custom."):
            continue
        if not any(marker in key for marker in ("additional_driver", "guest_will_drive")):
            continue
        description = str(signal.get("description") or "").strip()
        rendered.append(description or _render_value(signal.get("value")))
    return _unique_text(rendered)


def render_booking_sales_brief(profile_data: dict[str, Any]) -> str:
    """Render factual sales-brief sections deterministically from stored signals.

    The renderer never converts a durable household fact into appointment
    attendance. Suggestions are simple, evidence-linked rules over normalized
    fields, so the LLM cannot omit supplied participant facts or recalculate
    totals with different semantics.
    """

    booking = profile_data.get("booking") or {}
    same_person = bool(profile_data.get("same_person"))
    booker = profile_data.get("booker") or {}
    driver = profile_data.get("driver") or {}
    booker_name = str(booker.get("name") or "Chưa có thông tin")
    driver_name = booker_name if same_person else str(driver.get("name") or "Chưa có thông tin")
    signals = _signal_map(list(profile_data.get("test_drive_context") or []))

    booker_attending = _signal_value(signals, "booker", "booker_attending")
    driver_attending = _signal_value(signals, "driver", "driver_attending")
    additional_guest_count = _signal_value(signals, "group", "additional_guest_count")
    guest_context = _guest_context(signals)

    context_lines: list[str] = []
    if same_person:
        context_lines.append(f"{booker_name} là người đặt và cũng là người lái thử")
    else:
        context_lines.append(f"{booker_name} là người đặt; {driver_name} là người lái đã đăng ký")

    if isinstance(additional_guest_count, int) and not isinstance(additional_guest_count, bool):
        if booker_attending is True:
            context_lines.append(
                f"Dự kiến có tổng cộng {additional_guest_count + 1} người tham gia, "
                f"gồm {booker_name} và {additional_guest_count} người đi cùng"
            )
        else:
            context_lines.append(f"Có {additional_guest_count} người đi cùng đã được ghi nhận")
    if driver_attending is True and not same_person:
        context_lines.append(f"{driver_name} sẽ tham gia buổi lái thử")
    context_lines.extend(f"Người đi cùng: {item}" for item in guest_context)

    booker_will_drive = _signal_value(signals, "booker", "booker_will_drive")
    driver_will_drive = _signal_value(signals, "driver", "driver_will_drive")
    if booker_will_drive is True:
        context_lines.append(f"{booker_name} sẽ trực tiếp lái thử")
    if driver_will_drive is True and not same_person:
        context_lines.append(f"{driver_name} sẽ trực tiếp lái thử")

    if len(context_lines) == 1:
        context_lines.append("Chưa có thông tin về người đi cùng, mục tiêu đánh giá hay nhu cầu hậu cần cụ thể")

    booker_facts = _profile_fact_lines(booker)
    driver_facts = [] if same_person else _profile_fact_lines(driver)
    all_facts = booker_facts + driver_facts
    all_known_text = " ".join(context_lines + all_facts).casefold()

    suggestions: list[str] = []
    preparations: list[str] = [
        "Kiểm tra lịch hẹn, mẫu xe và thời gian tại showroom trước khi khách đến",
    ]
    if "2 tuổi" in all_known_text or "bé" in all_known_text or "trẻ em" in all_known_text:
        suggestions.append("Xác nhận nhu cầu ghế trẻ em và ưu tiên kiểm tra thao tác đưa bé lên xuống, hàng ghế sau và không gian lắp ghế")
        preparations.append("Đề nghị khách mang ghế trẻ em đang sử dụng nếu muốn kiểm tra độ phù hợp thực tế")
    if "cũng muốn lái" in all_known_text or "chồng" in all_known_text and "lái" in all_known_text:
        suggestions.append("Xác nhận với showroom điều kiện để người đi cùng cũng lái thử và nhắc người đó mang giấy phép lái xe phù hợp")
        preparations.append("Sắp xếp thời gian để từng người lái điều chỉnh ghế, vô-lăng và gương trước lượt trải nghiệm")
    if "nội thành" in all_known_text or "đưa đón con" in all_known_text:
        suggestions.append("Ưu tiên trải nghiệm tầm nhìn, quay đầu, đỗ xe, thao tác lên xuống và sự thuận tiện khi di chuyển nội thành")
    if "gia đình" in all_known_text and not suggestions:
        suggestions.append("Hỏi thêm vị trí ngồi thường xuyên của từng thành viên và tiêu chí gia đình muốn đánh giá trên xe")
    if not suggestions:
        suggestions.append("Hỏi khách mục tiêu chính của buổi lái thử và tiêu chí cần ưu tiên đánh giá")
    preparations.append("Xác nhận lại số người tham dự thực tế và người sẽ trực tiếp lái trước buổi hẹn")

    def bullets(lines: list[str]) -> str:
        return "\n".join(f"- {line}." for line in _unique_text(lines))

    if same_person:
        participant_sections = (
            f"### 👤 {booker_name} – Người tham gia\n\n"
            "**Thông tin tự cung cấp (đã xác nhận):**\n\n"
            + (bullets(booker_facts) if booker_facts else "*Chưa có thông tin về sở thích, mối quan tâm, hay ý định cụ thể khác.*")
        )
        title = f"## Khách hàng: {booker_name} (người đặt & người lái)"
    else:
        participant_sections = (
            f"### 👤 {booker_name} – Người đặt\n\n"
            "**Thông tin tự cung cấp (đã xác nhận):**\n\n"
            + (bullets(booker_facts) if booker_facts else "*Chưa có thông tin về sở thích, mối quan tâm, hay ý định cụ thể khác.*")
            + "\n\n---\n\n"
            + f"### 👤 {driver_name} – Người lái\n\n"
            "**Thông tin tự cung cấp (đã xác nhận):**\n\n"
            + (bullets(driver_facts) if driver_facts else "*Chưa cung cấp thông tin cá nhân.*")
        )
        title = f"## Khách hàng: {booker_name} (người đặt) & {driver_name} (người lái)"

    return "\n\n".join(
        [
            title,
            f"**Xe:** {booking.get('vehicle_model') or 'Chưa có thông tin'}",
            f"**Showroom:** {booking.get('showroom_name') or 'Chưa có thông tin'}",
            f"**Thời gian lái thử:** {_format_start_at(booking.get('start_at'))}",
            "---",
            "### Bối cảnh buổi lái thử\n\n" + bullets(context_lines),
            "---",
            participant_sections,
            "---",
            "### 🧠 Gợi ý cho tư vấn viên\n\n" + bullets(suggestions),
            "---",
            "### 📋 Chuẩn bị cho buổi lái thử\n\n" + bullets(preparations),
        ]
    )


def is_booking_sales_brief_source(profile_data: dict[str, Any]) -> bool:
    return isinstance(profile_data.get("booking"), dict) and "test_drive_context" in profile_data
