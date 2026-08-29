import re
import unicodedata
from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.dependencies import profile_service, profile_update_queue
from src.services.profile.models import BookingSignalCandidate, ProfileSignalCandidate

_HOUSEHOLD_SIZE_ALIASES = {
    "family_size",
    "family_group_size",
    "custom.family_size",
    "custom.family_group_size",
    "custom.household_size",
}
_NUMBER_WORDS = {
    "mot": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "tu": 4,
    "nam": 5,
    "sau": 6,
    "bay": 7,
    "tam": 8,
    "chin": 9,
    "muoi": 10,
}


def _is_household_size_alias(key: str) -> bool:
    normalized = key.casefold().strip().replace(".", "_").replace("-", "_")
    return key.casefold().strip() in _HOUSEHOLD_SIZE_ALIASES or any(
        marker in normalized for marker in ("family_size", "household_size")
    )


def _validated_household_size(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("household_size must be an integer >= 1")
    return value


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold()).replace("đ", "d")
    return " ".join("".join(char for char in decomposed if not unicodedata.combining(char)).split())


def _explicit_household_size(message: str) -> int | None:
    match = re.search(
        r"\b(?:gia dinh|nha) (?:cua )?(?:toi|minh|em|anh|chi)? ?(?:co|gom) "
        r"(\d{1,2}|mot|hai|ba|bon|tu|nam|sau|bay|tam|chin|muoi) "
        r"(?:nguoi|thanh vien)\b",
        _normalize_text(message),
    )
    if not match:
        return None
    token = match.group(1)
    return _validated_household_size(int(token) if token.isdigit() else _NUMBER_WORDS[token])


def _states_booking_attendance(message: str) -> bool:
    folded = _normalize_text(message)
    return bool(
        re.search(
            r"\b(?:den|di|tham gia) (?:buoi )?lai thu\b|\b(?:den|di) cung\b|\btham du\b",
            folded,
        )
    )


def _child_guest_context(message: str) -> str | None:
    folded = _normalize_text(message)
    if not re.search(r"\b(?:di cung|tham gia|den lai thu)\b", folded):
        return None
    child = re.search(r"\b(?:con gai|be gai|con trai|be trai|em be|dua con|be|tre em)\b", folded)
    if not child:
        return None
    age = re.search(r"\b(\d{1,2}) tuoi\b", folded)
    relationship = "Bé gái" if re.search(r"\b(?:con gai|be gai)\b", folded) else "Trẻ em"
    return f"{relationship} {age.group(1)} tuổi đi cùng" if age else f"{relationship} đi cùng"


def _additional_driver_relationship(message: str) -> str | None:
    folded = _normalize_text(message)
    if not re.search(r"\b(?:lai thu|lai xe)\b", folded):
        return None
    if re.search(r"\bchong\b", folded):
        return "chồng"
    if re.search(r"\bvo\b", folded):
        return "vợ"
    return None


def _explicit_primary_use(message: str) -> str | None:
    folded = _normalize_text(message)
    if not re.search(r"\b(?:muc dich su dung|nhu cau su dung|dung xe chu yeu|su dung xe chinh)\b", folded):
        return None
    cleaned = " ".join(message.split()).strip(" .?")
    extracted = re.search(
        r"(?:mục đích sử dụng|nhu cầu sử dụng|dùng xe chủ yếu|sử dụng xe chính|"
        r"muc dich su dung|nhu cau su dung|dung xe chu yeu|su dung xe chinh)"
        r"(?:\s+xe)?(?:\s+chính|\s+chủ yếu|\s+chinh|\s+chu yeu)?"
        r"(?:\s+của\s+(?:tôi|mình|em|anh|chị)|\s+cua\s+(?:toi|minh|em|anh|chi))?"
        r"\s*(?:là|la|:)?\s*(.+)$",
        cleaned,
        re.IGNORECASE,
    )
    if extracted:
        cleaned = extracted.group(1).strip(" .?")
    cleaned = re.sub(r"\s+(?:thì|thi)\s+(?:cần|can)\s+.*$", "", cleaned, flags=re.IGNORECASE).strip(" .?")
    return cleaned or None


def _merge_context_values(existing: Any, additions: list[Any]) -> list[Any]:
    if isinstance(existing, list):
        values = existing
    elif existing is None or existing == "":
        values = []
    else:
        values = [existing]
    merged: list[Any] = []
    seen: set[str] = set()
    for value in [*values, *additions]:
        marker = repr(value).casefold()
        if marker not in seen:
            seen.add(marker)
            merged.append(value)
    return merged


def _upsert_booking_signal(
    signals: list[BookingSignalCandidate],
    candidate: BookingSignalCandidate,
    *,
    merge_list: bool = False,
) -> None:
    for index, signal in enumerate(signals):
        if signal.subject != candidate.subject or signal.key != candidate.key:
            continue
        if merge_list:
            signals[index] = candidate.model_copy(
                update={"value": _merge_context_values(signal.value, list(candidate.value))}
            )
        else:
            signals[index] = candidate
        return
    signals.append(candidate)


def _latest_user_message(messages: list[Any]) -> str:
    for message in reversed(messages):
        if str(getattr(message, "type", "")) not in {"human", "user"}:
            continue
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content
    return ""


def _normalize_post_booking_signals(
    profile_signals: list[ProfileSignalCandidate],
    booking_signals: list[BookingSignalCandidate],
    *,
    latest_user_message: str = "",
) -> tuple[list[ProfileSignalCandidate], list[BookingSignalCandidate]]:
    """Keep durable household size out of booking-scoped custom signals."""
    normalized_profiles: list[ProfileSignalCandidate] = []
    normalized_bookings: list[BookingSignalCandidate] = []
    household_candidate: ProfileSignalCandidate | None = None

    for signal in profile_signals:
        key = signal.key.casefold().strip()
        if key == "household_size":
            normalized_profiles.append(
                signal.model_copy(update={"value": _validated_household_size(signal.value)})
            )
        elif _is_household_size_alias(key):
            household_candidate = signal.model_copy(
                update={
                    "category": "fact",
                    "key": "household_size",
                    "value": _validated_household_size(signal.value),
                }
            )
        else:
            normalized_profiles.append(signal)

    for signal in booking_signals:
        key = signal.key.casefold().strip()
        if _is_household_size_alias(key):
            household_candidate = ProfileSignalCandidate(
                category="fact",
                key="household_size",
                value=_validated_household_size(signal.value),
                description=signal.description,
                subject="self",
                certainty=signal.certainty,
                confidence=signal.confidence,
                source_type=signal.source_type,
                operation=signal.operation,
            )
        else:
            normalized_bookings.append(signal)

    has_canonical_household_size = any(signal.key == "household_size" for signal in normalized_profiles)
    if household_candidate is not None and not has_canonical_household_size:
        normalized_profiles.append(household_candidate)
        has_canonical_household_size = True

    explicit_size = _explicit_household_size(latest_user_message)
    if explicit_size is not None:
        attendance_is_explicit = _states_booking_attendance(latest_user_message)
        # Household size is durable. Attendance is created only when the same
        # sentence explicitly scopes the number to this appointment.
        if attendance_is_explicit:
            normalized_bookings = [
                signal
                for signal in normalized_bookings
                if signal.key not in {"booker_attending", "additional_guest_count"}
            ]
            normalized_bookings.extend(
                [
                    BookingSignalCandidate(
                        category="participation",
                        key="booker_attending",
                        value=True,
                        description="Người đặt sẽ tham gia buổi lái thử.",
                        subject="booker",
                        certainty="known",
                        confidence=1,
                        source_type="explicit_user",
                        operation="add",
                    ),
                    BookingSignalCandidate(
                        category="participation",
                        key="additional_guest_count",
                        value=max(0, explicit_size - 1),
                        description=f"Tổng cộng {explicit_size} người sẽ tham gia, bao gồm người đặt.",
                        subject="group",
                        certainty="known",
                        confidence=1,
                        source_type="explicit_user",
                        operation="revise",
                    ),
                ]
            )
        else:
            normalized_bookings = [
                signal
                for signal in normalized_bookings
                if signal.key not in {"additional_guest_count", "additional_guest_context"}
            ]
        if not has_canonical_household_size:
            normalized_profiles.append(
                ProfileSignalCandidate(
                    category="fact",
                    key="household_size",
                    value=explicit_size,
                    description=f"Gia đình có {explicit_size} người.",
                    subject="self",
                    certainty="known",
                    confidence=1,
                    source_type="explicit_user",
                    operation="add",
                )
            )

    child_context = _child_guest_context(latest_user_message)
    if child_context:
        _upsert_booking_signal(
            normalized_bookings,
            BookingSignalCandidate(
                category="participants",
                key="additional_guest_context",
                value=[child_context],
                description=child_context,
                subject="group",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
                operation="add",
            ),
            merge_list=True,
        )

    additional_driver = _additional_driver_relationship(latest_user_message)
    if additional_driver:
        _upsert_booking_signal(
            normalized_bookings,
            BookingSignalCandidate(
                category="participation",
                key="booker_will_drive",
                value=True,
                description="Người đặt cũng sẽ trực tiếp lái thử.",
                subject="booker",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
                operation="add",
            ),
        )
        _upsert_booking_signal(
            normalized_bookings,
            BookingSignalCandidate(
                category="participants",
                key="additional_guest_context",
                value=[f"{additional_driver.capitalize()} đi cùng và cũng muốn lái thử"],
                description=f"{additional_driver.capitalize()} đi cùng và cũng muốn lái thử.",
                subject="group",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
                operation="add",
            ),
            merge_list=True,
        )
        _upsert_booking_signal(
            normalized_bookings,
            BookingSignalCandidate(
                category="participants",
                key="custom.additional_driver",
                value={"relationship": additional_driver, "will_drive": True},
                description=f"{additional_driver.capitalize()} của người đặt cũng muốn lái thử.",
                subject="group",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
                operation="add",
            ),
        )

    primary_use = _explicit_primary_use(latest_user_message)
    if primary_use and not any(signal.key == "primary_use" for signal in normalized_profiles):
        normalized_profiles.append(
            ProfileSignalCandidate(
                category="usage",
                key="primary_use",
                value=primary_use,
                description=primary_use,
                subject="self",
                certainty="known",
                confidence=1,
                source_type="explicit_user",
                operation="add",
            )
        )
    return normalized_profiles, normalized_bookings


@tool
async def update_post_booking_signals(
    profile_signals: list[ProfileSignalCandidate],
    booking_signals: list[BookingSignalCandidate],
    profile_id: Annotated[str, InjectedState("profile_id")],
    metadata: Annotated[dict[str, Any], InjectedState("metadata")],
    participant_context: Annotated[dict[str, Any], InjectedState("participant_context")],
    messages: Annotated[list[Any], InjectedState("messages")],
) -> dict[str, Any]:
    """Queue durable person facts and/or booking-specific test-drive facts in one call.

    Booking facts include attendance, who will drive, evaluation/purchase involvement,
    guests, logistics, and custom.* context. Never put those transient facts in profiles.
    The backend supplies all identities and the booking id; do not send them.
    """
    profile_signals, booking_signals = _normalize_post_booking_signals(
        profile_signals,
        booking_signals,
        latest_user_message=_latest_user_message(messages),
    )
    if not profile_signals and not booking_signals:
        return {"status": "skipped", "reason": "no_signals"}
    speaker_role = str(participant_context.get("role") or "")
    booking_id = str(participant_context.get("booking_id") or "")
    if booking_signals and (speaker_role not in {"booker", "driver"} or not booking_id):
        return {"status": "skipped", "reason": "booking_context_not_resolved"}
    updates: dict[str, list[dict[str, Any]]] = {}
    for signal in profile_signals:
        target = profile_id
        candidate = signal.model_dump(exclude={"subject"})
        if signal.subject == "third_party":
            if speaker_role not in {"booker", "driver"} or not booking_id:
                continue
            try:
                target = profile_service.resolve_booking_other_participant_profile(booking_id, speaker_role).id
            except KeyError:
                continue
            candidate.update({"certainty": "possible", "confidence": min(signal.confidence, .35), "source_type": "implicit_user", "operation": "add"})
        if target:
            updates.setdefault(target, []).append(candidate)
    queued = await profile_update_queue.enqueue_post_booking(
        profile_updates=[{"profile_id": key, "candidates": value} for key, value in updates.items()],
        booking_id=booking_id, booking_candidates=booking_signals, speaker_role=speaker_role or "system",
        conversation_id=str(metadata.get("conversation_id") or ""), trace_id=str(metadata.get("trace_id") or ""),
    )
    return {"status": "queued" if queued else "unavailable", "profile_signal_count": len(profile_signals), "booking_signal_count": len(booking_signals)}
