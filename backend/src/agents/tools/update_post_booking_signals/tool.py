from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.dependencies import profile_service, profile_update_queue
from src.services.profile.models import BookingSignalCandidate, ProfileSignalCandidate


@tool
async def update_post_booking_signals(
    profile_signals: list[ProfileSignalCandidate],
    booking_signals: list[BookingSignalCandidate],
    profile_id: Annotated[str, InjectedState("profile_id")],
    metadata: Annotated[dict[str, Any], InjectedState("metadata")],
    participant_context: Annotated[dict[str, Any], InjectedState("participant_context")],
) -> dict[str, Any]:
    """Queue durable person facts and/or booking-specific test-drive facts in one call.

    Booking facts include attendance, who will drive, evaluation/purchase involvement,
    guests, logistics, and custom.* context. Never put those transient facts in profiles.
    The backend supplies all identities and the booking id; do not send them.
    """
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
