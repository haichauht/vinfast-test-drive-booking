import logging
from typing import Annotated, Any, Literal

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.dependencies import profile_service, profile_update_queue
from src.observability import trace_backend_operation
from src.services.profile.models import SignalCandidate

logger = logging.getLogger("profile.tool")


@tool
@trace_backend_operation("ProfileUpdateQueue.enqueue")
async def update_user_profile(
    signals: list[SignalCandidate],
    profile_id: Annotated[str, InjectedState("profile_id")],
    metadata: Annotated[dict[str, Any], InjectedState("metadata")],
    participant_context: Annotated[dict[str, Any], InjectedState("participant_context")],
    subject: Literal["self", "third_party"] = "self",
) -> dict[str, Any]:
    """Queue profile signals identified from the current conversation.

    Use only for durable personalization information. Send explicit user statements
    as ``known``/``explicit_user``. Send useful inferences as ``likely`` or
    ``possible``/``implicit_user``. Revise or retract stale signals instead of
    adding contradictions. Never store OTPs, access tokens, contact details, or
    transient booking-operation data.

    Args:
        signals: SignalCandidate objects. Allowed categories: fact, usage,
            experience, interest, concern, test_drive_goal,
            conversation_preference, likely_intent, custom_intent. Certainty is
            known, likely, or possible. Source type is explicit_user,
            implicit_user, or trusted_domain. Operation is add, strengthen,
            weaken, revise, or retract. Confidence is between 0 and 1.
        subject: ``self`` for the current speaker, whether that speaker is the
            booker or driver. Use ``third_party`` only when the speaker provides
            information about the other participant in the same booking. The
            backend resolves that participant and records low-confidence
            third-party attribution.
    """
    if not profile_id:
        return {"status": "skipped", "reason": "profile_not_resolved"}
    conversation_id = str(metadata.get("conversation_id") or "")
    target_profile_id = profile_id
    if subject == "third_party":
        speaker_role = str(participant_context.get("role") or "")
        if speaker_role not in {"booker", "driver"} or not participant_context.get("booking_id"):
            return {"status": "skipped", "reason": "third_party_subject_not_allowed"}
        try:
            target = profile_service.resolve_booking_other_participant_profile(
                str(participant_context["booking_id"]), speaker_role
            )
        except KeyError:
            return {"status": "skipped", "reason": "third_party_profile_not_resolved"}
        target_profile_id = target.id
        conversation_id = f"third_party:{speaker_role}:{conversation_id}"
        signals = [
            item.model_copy(update={
                "certainty": "possible",
                "confidence": min(item.confidence, 0.35),
                "source_type": "implicit_user",
                "operation": "add",
            })
            for item in signals
        ]
    logger.info(
        "profile.tool.requested trace_id=%s conversation_id=%s profile_id=%s signals=%s",
        metadata.get("trace_id"),
        metadata.get("conversation_id"),
        target_profile_id,
        [{"category": item.category, "key": item.key, "operation": item.operation} for item in signals],
    )
    queued = await profile_update_queue.enqueue(
        profile_id=target_profile_id,
        conversation_id=conversation_id,
        trace_id=str(metadata.get("trace_id") or ""),
        candidates=signals,
    )
    status = "queued" if queued else "unavailable"
    logger.info(
        "profile.tool.completed trace_id=%s profile_id=%s status=%s signal_count=%s",
        metadata.get("trace_id"), target_profile_id, status, len(signals),
    )
    return {"status": status, "subject": subject, "signal_count": len(signals)}
