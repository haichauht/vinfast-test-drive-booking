import asyncio
import hashlib
import json
import logging
import uuid
from collections.abc import Callable
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from langchain_core.messages import HumanMessage

from src.agents.graph import agent, get_agent
from src.agents.tools import (
    get_booking_details,
    get_booking_draft,
    verify_booking_access,
)
from src.agents.trace import redact, trace_event
from src.config import get_settings
from src.database.redis_client import redis_client
from src.dependencies import booking_service, driver_invitation_service, internal_portal_service, profile_service, profile_update_queue
from src.guardrails import get_guardrails
from src.internal_portal import InternalPrincipal, InternalRole
from src.internal_portal.routes import current_principal
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    ClientLogRequest,
    CsvImportRequest,
    DatasetImportRequest,
    DemoActionRequest,
    UiDirective,
)
from src.services.booking import BookingError
from src.services.llm import summarize_user_profile
from src.services.profile.context import build_profile_context

router = APIRouter()
_default_agent = agent
SECURITY_STATE_DATASET_FILES = {
    "12_internal_users.csv",
    "13_internal_user_showrooms.csv",
    "14_internal_sessions.csv",
    "26_idempotency_records.csv",
    "29_otp_challenges.csv",
    "30_booking_access_sessions.csv",
    "31_zalo_identity_links.csv",
    "32_internal_audit_events.csv",
    # Equivalent runtime/security state in the legacy dataset.
    "13_otp_challenges.csv",
    "14_booking_access_sessions.csv",
    "15_zalo_identity_links.csv",
}


@router.on_event("startup")
async def start_profile_update_worker() -> None:
    profile_update_queue.start()


@router.on_event("shutdown")
async def stop_profile_update_worker() -> None:
    await profile_update_queue.stop()


def _chat_ui_directive(result: dict[str, Any]) -> UiDirective | None:
    tool = str(result.get("action_tool") or "")
    raw_data = result.get("action_result")
    data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
    phase = ""
    event = ""

    if tool == "request_booking_access":
        phase = "access_request" if data.get("requires_contact_value") else "access_verify"
        event = "ACCESS_REQUESTED" if data.get("requires_contact_value") else "ACCESS_VERIFY"
    elif tool == "verify_booking_access":
        phase, event = "booking_list", "ACCESS_VERIFIED"
    elif tool == "search_test_drive_options":
        phase = "choose_slot" if data.get("search_stage") == "slot_selection" else "choose_showroom"
        event = "SEARCH_OPTIONS"
    elif tool == "hold_test_drive_slot":
        phase, event = "collect_info", "SLOT_HELD"
    elif tool == "update_booking_draft":
        phase, event = "review", "DRAFT_UPDATED"
    elif tool == "confirm_test_drive_booking":
        phase, event = "success", "BOOKING_CONFIRMED"

    if not event:
        return None

    actions_by_phase = {
        "access_request": ["request_access", "cancel_access"],
        "access_verify": ["verify_access", "cancel_access"],
        "booking_list": ["select_booking", "exit_manage_booking"],
        "choose_showroom": ["select_showroom", "switch_vehicle", "start_lookup"],
        "choose_slot": ["select_slot", "switch_vehicle", "start_lookup"],
        "collect_info": ["update_draft"],
        "review": ["confirm_booking", "edit_draft"],
        "success": ["start_lookup"],
    }
    return UiDirective(event=event, phase=phase, allowed_actions=actions_by_phase.get(phase, []))


def require_operations_admin(
    principal: Annotated[InternalPrincipal, Depends(current_principal)],
) -> InternalPrincipal:
    internal_portal_service.require_roles(principal, InternalRole.OPERATIONS_ADMIN)
    return principal


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Chat với AI agent."""
    try:
        # Tạo conversation_id mới nếu client không truyền
        conversation_id = body.conversation_id or str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        identity = getattr(request.state, "client_identity", None)
        profile = None
        profile_context: dict[str, Any] = {}
        stored_booking_context: dict[str, Any] = {"active": False}
        participant_context: dict[str, Any] = {"role": "user"}
        try:
            driver_invitation = getattr(request.state, "driver_invitation", None)
            if not driver_invitation and body.driver_invitation_token:
                driver_invitation = await asyncio.to_thread(
                    driver_invitation_service.resolve, body.driver_invitation_token
                )
            if driver_invitation:
                profile = profile_service.bind_person_conversation(
                    conversation_id,
                    person_id=driver_invitation.driver_person_id,
                    email=driver_invitation.email,
                    phone=driver_invitation.phone,
                    source="driver_invitation",
                    trace_id=trace_id,
                )
                stored_booking_context = {
                    "active": True,
                    **profile_service.booking_context(driver_invitation.booking_id),
                    "participants": profile_service.booking_participants_context(
                        driver_invitation.booking_id
                    ),
                }
                participant_context = {"role": "driver", "booking_id": driver_invitation.booking_id}
            else:
                profile = profile_service.resolve_or_create(conversation_id, getattr(identity, "session_id", ""))
                stored_booking_context = profile_service.latest_booking_context(profile.id)
                if stored_booking_context.get("active"):
                    participant_context = {"role": "booker", "booking_id": stored_booking_context.get("id")}
            profile_context = build_profile_context(profile, body.message)
        except KeyError as exc:
            if body.driver_invitation_token:
                raise HTTPException(status_code=404, detail="Driver invitation is invalid or expired") from exc
            logging.getLogger("profile.lifecycle").exception("profile.lookup_failed trace_id=%s conversation_id=%s", trace_id, conversation_id)
        except Exception:
            logging.getLogger("profile.lifecycle").exception("profile.lookup_failed trace_id=%s conversation_id=%s", trace_id, conversation_id)
        guardrails = get_guardrails()
        input_decision = guardrails.inspect_input(
            message=body.message,
            conversation_id=conversation_id,
            context=body.context,
            action=body.action,
            action_payload=body.action_payload,
        )
        if not input_decision.allowed:
            trace_event(
                "guardrail.input_blocked",
                trace_id=trace_id,
                conversation_id=conversation_id,
                code=input_decision.code,
                reason=input_decision.reason,
                details=input_decision.details,
            )
            return ChatResponse(
                response=input_decision.user_message,
                conversation_id=conversation_id,
                action_error=input_decision.code,
            )

        safe_message = input_decision.sanitized_text or body.message
        trace_event(
            "chat.request",
            trace_id=trace_id,
            conversation_id=conversation_id,
            message=safe_message,
            context=body.context,
            action=body.action,
            action_payload=body.action_payload,
        )
        config = {"configurable": {"thread_id": conversation_id}}
        logging.getLogger("agent.requests").info(
            "chat_started conversation_id=%s requested_action=%s", conversation_id, body.action or "llm"
        )
        # Keep the module-level `agent` overrideable by existing tests, while
        # production resolves the graph initialized with the Postgres saver.
        active_agent = agent if agent is not _default_agent else get_agent()
        result = await cast(Any, active_agent).ainvoke(
            {
                "query": safe_message,
                "context": body.context,
                "requested_action": body.action,
                "action_payload": body.action_payload,
                "action_result": None,
                "action_tool": "",
                "action_input": {},
                "action_error": "",
                # Reset per-turn tool loop counter to 0 for each new user request
                # (ensures each message turn receives a fresh 8-call tool budget while preventing infinite loops within 1 turn)
                "tool_call_count": 0,
                "metadata": {
                    "trace_id": trace_id,
                    "conversation_id": conversation_id,
                    "anon_session_id": getattr(identity, "session_id", "unknown"),
                    "client_ip": getattr(identity, "client_ip", "unknown"),
                    "llm_call_count": 0,
                },
                "profile_id": profile.id if profile else "",
                "profile_context": profile_context,
                "post_booking_context": (
                    {"active": True, **stored_booking_context}
                    if stored_booking_context.get("active")
                    else {"active": False}
                ),
                "participant_context": participant_context,
            },
            config=config,
        )
        logging.getLogger("agent.requests").info(
            "chat_finished conversation_id=%s tool=%s status=%s",
            conversation_id,
            result.get("action_tool") or "none",
            "error" if result.get("action_error") else "success",
        )
        action_data = result.get("action_result")
        if result.get("action_tool") == "confirm_test_drive_booking" and isinstance(action_data, dict) and action_data.get("status") == "confirmed":
            try:
                promoted = profile_service.promote_from_booking(profile.id if profile else None, str(action_data["booking_id"]), source="booking_confirmed", trace_id=trace_id)
                if promoted:
                    result["profile_id"] = promoted.id
                    result["profile_context"] = build_profile_context(promoted, safe_message)
                    result["post_booking_context"] = {"active": True, **profile_service.booking_context(str(action_data["booking_id"]))}
            except Exception:
                logging.getLogger("profile.lifecycle").exception("profile.confirm_promotion_failed trace_id=%s booking_id=%s", trace_id, action_data.get("booking_id"))
        protected = guardrails.protect_output(result)
        response = ChatResponse(
            response=protected.response,
            analysis=protected.analysis,
            conversation_id=conversation_id,
            tool_name=result.get("action_tool", ""),
            tool_input=protected.tool_input,
            action_data=protected.action_data,
            action_error=protected.action_error,
            intent=str(result.get("intent") or ""),
            ui=_chat_ui_directive(result),
        )
        trace_event(
            "chat.response",
            trace_id=trace_id,
            conversation_id=conversation_id,
            response=response.model_dump(),
            intent=result.get("intent"),
            active_skill=result.get("active_skill"),
            tool_call_count=result.get("tool_call_count"),
            llm_call_count=(result.get("metadata") or {}).get("llm_call_count"),
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        trace_event(
            "chat.error",
            trace_id=locals().get("trace_id", ""),
            conversation_id=locals().get("conversation_id", body.conversation_id),
            error=str(e),
        )
        logging.getLogger(__name__).error("Internal error in chat endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau.")


@router.post("/driver-chat/{token}/chat", response_model=ChatResponse)
async def driver_chat(token: str, request: Request, body: ChatRequest) -> ChatResponse:
    """Chat as the driver identified by a private, expiring invitation link."""
    try:
        request.state.driver_invitation = await asyncio.to_thread(driver_invitation_service.resolve, token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Driver invitation is invalid or expired") from exc
    namespace = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    prefix = f"driver:{namespace}:"
    supplied = body.conversation_id
    conversation_id = supplied if supplied.startswith(prefix) else f"{prefix}{supplied or uuid.uuid4().hex}"
    return await chat(request, body.model_copy(update={"conversation_id": conversation_id[:100]}))


@router.post("/bookings/{booking_id}/driver-invitation")
async def send_driver_invitation(booking_id: str) -> dict[str, Any]:
    """Create and email a private chat invitation to a booking's separate driver."""
    try:
        return await asyncio.to_thread(driver_invitation_service.issue_and_send, booking_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Booking not found") from exc
    except ValueError as exc:
        code = str(exc)
        messages = {
            "DRIVER_IS_BOOKER": "Driver and booker are the same person; no separate invitation is needed.",
            "DRIVER_EMAIL_REQUIRED": "The driver does not have an email address.",
        }
        raise HTTPException(status_code=400, detail={"code": code, "message": messages.get(code, "Unable to create driver invitation")}) from exc


@router.get("/bookings/{booking_id}/profile-summary.md", response_class=PlainTextResponse)
async def booking_profile_summary(booking_id: str) -> PlainTextResponse:
    """Return the booking's booker/driver profile summary as Markdown."""
    try:
        source = await asyncio.to_thread(profile_service.booking_profiles_context, booking_id)
        markdown = await summarize_user_profile(source)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Booking not found") from exc
    except RuntimeError as exc:
        if str(exc) == "LLM_NOT_CONFIGURED":
            raise HTTPException(status_code=503, detail="Profile summary LLM is not configured") from exc
        raise
    return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8")


@router.get("/status")
async def agent_status():
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}


@router.get("/redis/health")
async def redis_health():
    """Kiểm tra kết nối Redis."""
    connected = redis_client.is_connected()
    return {"status": "connected" if connected else "disconnected", "enabled": redis_client.enabled}


@router.get("/user-profiles/{user_id}/summary")
async def user_profile_summary(user_id: str) -> dict[str, Any]:
    """Return an LLM-generated, sales-facing customer summary."""
    try:
        snapshot = await asyncio.to_thread(profile_service.load_for_user, user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="User profile not found") from exc
    source = build_profile_context(snapshot)
    source["latest_booking"] = await asyncio.to_thread(
        profile_service.latest_booking_context, snapshot.id
    )
    try:
        summary = await summarize_user_profile(source)
    except RuntimeError as exc:
        if str(exc) == "LLM_NOT_CONFIGURED":
            raise HTTPException(status_code=503, detail="Profile summary LLM is not configured") from exc
        raise
    except Exception as exc:
        logging.getLogger("profile.summary").exception(
            "profile.summary.failed user_id=%s profile_id=%s", user_id, snapshot.id
        )
        raise HTTPException(status_code=502, detail="Unable to generate profile summary") from exc
    logging.getLogger("profile.summary").info(
        "profile.summary.generated user_id=%s profile_id=%s version=%s",
        user_id, snapshot.id, snapshot.version,
    )
    return {"user_id": user_id, "profile_id": snapshot.id, "version": snapshot.version, "summary": summary}


@router.get("/user-profiles/{user_id}/")
async def user_profile_detail(user_id: str) -> dict[str, Any]:
    """Return deterministic Markdown and structured JSON profile views."""
    try:
        snapshot = await asyncio.to_thread(profile_service.load_for_user, user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="User profile not found") from exc
    return {"user_id": user_id, **build_profile_context(snapshot)}


@router.get("/booking/health")
async def booking_health():
    """Lightweight readiness check for the deterministic booking UI."""
    try:
        with booking_service.db.connect() as connection:
            connection.execute("SELECT 1").fetchone()
        return {"status": "ready", "service": "booking"}
    except Exception as exc:
        logging.getLogger(__name__).error("Booking readiness check failed: %s", exc)
        raise HTTPException(
            status_code=503, detail={"code": "BOOKING_UNAVAILABLE", "message": "Dịch vụ đặt lịch tạm thời gián đoạn."}
        )


AGENT_TOOLS = {"get_draft", "request_access", "verify_access", "get_details"}


def _request_demo_access(**kwargs: Any) -> dict:
    settings = get_settings()
    expose_mock_otp = settings.app_env != "production" and getattr(
        settings, "booking_access_expose_mock_otp", True
    )
    kwargs.setdefault("booking_code", None)
    if expose_mock_otp and not settings.zalo_bot_enabled and kwargs.get("preferred_channel") == "zalo":
        kwargs["preferred_channel"] = "sms"
    return booking_service.request_access(**kwargs, expose_otp=expose_mock_otp)


@router.post("/chat/stream")
@router.post("/booking-agent/stream")
async def chat_stream(body: ChatRequest, request: Request):
    """Stream ViVi responses using Server-Sent Events (Streamable HTTP).

    Streams real-time LLM token chunks via astream_events when supported,
    with seamless fallback to full chat response payload.
    """
    async def event_generator():
        try:
            active_agent = get_agent()
            guardrails = get_guardrails()
            conversation_id = body.conversation_id or str(uuid.uuid4())
            identity = getattr(request.state, "identity", None)
            trace_id = getattr(request.state, "trace_id", "") or str(uuid.uuid4())
            config = {"configurable": {"thread_id": conversation_id}}
            inputs = {
                "messages": [HumanMessage(content=body.message)],
                "requested_action": body.action,
                "action_payload": body.action_payload,
                "tool_call_count": 0,
                "metadata": {
                    "trace_id": trace_id,
                    "conversation_id": conversation_id,
                    "anon_session_id": getattr(identity, "session_id", "unknown"),
                    "client_ip": getattr(identity, "client_ip", "unknown"),
                    "llm_call_count": 0,
                },
            }

            token_streamed = False
            async for event in active_agent.astream_events(inputs, config=config, version="v2"):
                if event.get("event") == "on_chat_model_stream":
                    chunk = (event.get("data") or {}).get("chunk")
                    if hasattr(chunk, "content") and chunk.content and isinstance(chunk.content, str):
                        token_streamed = True
                        payload = json.dumps({"type": "token", "content": chunk.content}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"

            if not token_streamed:
                response_data = await chat(request, body)
                content = response_data.response or ""
                words = content.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    payload = json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"
                    await asyncio.sleep(0.01)
                final_payload = json.dumps({"type": "done", "response": response_data.model_dump()}, ensure_ascii=False)
                yield f"data: {final_payload}\n\n"
                return

            final_state = await active_agent.aget_state(config)
            state_values = final_state.values if final_state else {}
            protected = guardrails.protect_output(state_values)
            final_response = ChatResponse(
                response=protected.response,
                analysis=protected.analysis,
                conversation_id=conversation_id,
                tool_name=state_values.get("action_tool", ""),
                tool_input=protected.tool_input,
                action_data=protected.action_data,
                action_error=protected.action_error,
                intent=str(state_values.get("intent") or ""),
                ui=_chat_ui_directive(state_values),
            )
            final_payload = json.dumps({"type": "done", "response": final_response.model_dump()}, ensure_ascii=False)
            yield f"data: {final_payload}\n\n"
        except Exception as exc:
            logging.getLogger(__name__).warning("astream_events fallback: %s", exc)
            response_data = await chat(request, body)
            final_payload = json.dumps({"type": "done", "response": response_data.model_dump()}, ensure_ascii=False)
            yield f"data: {final_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/demo/action")
@router.post("/test-drive/actions")
async def demo_action(body: DemoActionRequest, request: Request):
    """Deterministic UI simulator: one button maps to one tool/command."""
    p = body.payload
    actions: dict[str, tuple[str, Callable[..., Any]]] = {
        "search_options": ("SearchOptionsQuery", booking_service.search_options),
        "hold_slot": ("HoldSlotCommand", booking_service.hold_slot),
        "release_hold": ("release_hold", lambda **kw: booking_service.release_hold(kw.get("booking_id", ""))),
        "get_draft": ("get_booking_draft", lambda **kw: get_booking_draft.invoke(kw)),
        "update_draft": ("UpdateBookingDraftCommand", booking_service.update_booking_draft),
        "confirm_booking": ("ConfirmBookingCommand", booking_service.confirm_booking),
        "request_access": (
            "request_booking_access",
            _request_demo_access,
        ),
        "verify_access": ("verify_booking_access", lambda **kw: verify_booking_access.invoke(kw)),
        "get_details": ("get_booking_details", lambda **kw: get_booking_details.invoke(kw)),
        "list_bookings": ("list_bookings", booking_service.list_bookings),
        "update_details": ("UpdateBookingDetailsCommand", booking_service.update_booking_details),
        "hold_reschedule": ("HoldRescheduleSlotCommand", booking_service.hold_reschedule_slot),
        "confirm_reschedule": ("ConfirmRescheduleCommand", booking_service.confirm_reschedule),
        "cancel_booking": ("CancelBookingCommand", booking_service.cancel_booking),
    }
    if body.action not in actions:
        raise HTTPException(status_code=400, detail="Unknown demo action")
    action_decision = get_guardrails().inspect_demo_action(action=body.action, payload=p)
    if not action_decision.allowed:
        trace_event(
            "guardrail.demo_action_blocked",
            code=action_decision.code,
            reason=action_decision.reason,
            details=action_decision.details,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": action_decision.code, "message": action_decision.user_message},
        )
    name, handler = actions[body.action]
    try:
        data = handler(**p)
        if body.action == "verify_access" and isinstance(data, dict) and data.get("booking_id"):
            try:
                identity = getattr(request.state, "client_identity", None)
                current_profile = None
                if body.conversation_id:
                    current_profile = profile_service.resolve_or_create(body.conversation_id, getattr(identity, "session_id", ""))
                verified = booking_service.verified_identity(str(p.get("challenge_id") or ""))
                verified_email = (verified or {}).get("normalized_email") or (verified or {}).get("email")
                verified_phone = (verified or {}).get("normalized_phone") or (verified or {}).get("phone") or ""
                if verified and verified_email:
                    profile_service.promote_identity(current_profile.id if current_profile else None, person_id=str(verified["id"]), email=str(verified_email), phone=str(verified_phone), source="access_verified", trace_id=str(uuid.uuid4()))
            except Exception:
                logging.getLogger("profile.lifecycle").exception("profile.otp_promotion_failed conversation_id=%s booking_id=%s", body.conversation_id, data.get("booking_id"))
        protected = get_guardrails().protect_output(
            {
                "response": "",
                "action_input": p,
                "action_result": data,
                "action_error": "",
            }
        )
        # Action results may be mappings (most commands) or lists
        # (`list_bookings`). Preserve either shape for the public API instead
        # of silently replacing valid list results with an empty object.
        response_data: Any = protected.action_data
        if response_data is None:
            response_data = {}
        settings = get_settings()
        expose_mock_otp = settings.app_env != "production" and getattr(
            settings, "booking_access_expose_mock_otp", True
        )
        if body.action == "request_access" and expose_mock_otp and data.get("is_mock") is True:
            response_data = dict(response_data)
            response_data["otp_code"] = data.get("otp_code")
        elif body.action == "request_access":
            # Output redaction may replace the code with "[redacted]". Do not
            # expose that field at all in production because it advertises a
            # mock credential in the public response.
            response_data = dict(response_data)
            response_data.pop("otp_code", None)
        kind = "Agent gọi tool" if body.action in AGENT_TOOLS else "Backend chạy UI command"
        return {"success": True, "message": f"{kind}: {name}", "tool": name, "data": response_data}
    except BookingError as exc:
        return {
            "success": False,
            "message": str(exc),
            "tool": name,
            "error": {"code": exc.code, "retryable": exc.retryable},
        }


@router.post("/admin/import/showrooms")
async def import_showrooms(
    request: CsvImportRequest,
    principal: Annotated[InternalPrincipal, Depends(require_operations_admin)],
):
    del principal
    try:
        return {"success": True, "data": booking_service.import_showrooms_csv(request.csv_text)}
    except BookingError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)})


@router.post("/admin/import/eval-dataset")
async def import_eval_dataset(
    request: DatasetImportRequest,
    principal: Annotated[InternalPrincipal, Depends(require_operations_admin)],
):
    del principal
    supplied_names = {name.replace("\\", "/").rsplit("/", 1)[-1] for name in request.files}
    blocked = sorted(supplied_names & SECURITY_STATE_DATASET_FILES)
    if blocked:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "SECURITY_STATE_IMPORT_FORBIDDEN",
                "message": "Không được import tài khoản, phiên đăng nhập hoặc dữ liệu bảo mật qua API.",
                "files": blocked,
            },
        )
    try:
        return {"success": True, "data": booking_service.import_eval_dataset(request.files)}
    except BookingError as exc:
        logging.getLogger("import").warning(
            "Dataset import rejected files=%s code=%s message=%s", sorted(request.files), exc.code, str(exc)
        )
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)})


@router.post("/client-log", status_code=204)
async def client_log(request: ClientLogRequest):
    level = request.level.lower() if request.level.lower() in {"debug", "info", "warning", "error"} else "error"
    safe_message = redact(request.message)
    safe_context = redact(request.context)
    getattr(logging.getLogger("frontend"), level)(
        "%s | context=%s", safe_message, json.dumps(safe_context, ensure_ascii=False, default=str)
    )
