from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from src.dependencies import profile_update_queue
from src.services.profile.models import SignalCandidate
import logging

logger = logging.getLogger("profile.tool")


@tool
async def update_user_profile(
    signals: list[SignalCandidate],
    profile_id: Annotated[str, InjectedState("profile_id")],
    metadata: Annotated[dict[str, Any], InjectedState("metadata")],
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
    """
    if not profile_id:
        return {"status": "skipped", "reason": "profile_not_resolved"}
    logger.info(
        "profile.tool.requested trace_id=%s conversation_id=%s profile_id=%s signals=%s",
        metadata.get("trace_id"),
        metadata.get("conversation_id"),
        profile_id,
        [{"category": item.category, "key": item.key, "operation": item.operation} for item in signals],
    )
    queued = await profile_update_queue.enqueue(
        profile_id=profile_id,
        conversation_id=str(metadata.get("conversation_id") or ""),
        trace_id=str(metadata.get("trace_id") or ""),
        candidates=signals,
    )
    status = "queued" if queued else "unavailable"
    logger.info(
        "profile.tool.completed trace_id=%s profile_id=%s status=%s signal_count=%s",
        metadata.get("trace_id"), profile_id, status, len(signals),
    )
    return {"status": status, "signal_count": len(signals)}
