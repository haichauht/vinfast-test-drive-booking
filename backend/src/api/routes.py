import json
import logging
import uuid
from collections.abc import Callable
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request

from src.agents.graph import agent, get_agent
from src.agents.tools import (
    get_booking_details,
    get_booking_draft,
    verify_booking_access,
)
from src.agents.trace import redact, trace_event
from src.config import get_settings
from src.dependencies import booking_service, internal_portal_service
from src.guardrails import get_guardrails
from src.guardrails.abuse import AbuseStatus, get_abuse_tracker
from src.guardrails.conversation import get_conversation_token_manager
from src.guardrails.policies import ABUSE_VIOLATION_CODES
from src.guardrails.rate_limit import get_rate_limiter
from src.internal_portal import InternalPrincipal, InternalRole
from src.internal_portal.routes import current_principal
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    ClientLogRequest,
    CsvImportRequest,
    DatasetImportRequest,
    DemoActionRequest,
)
from src.services.booking import BookingError

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


def _client_subject(request: Request) -> str:
    return request.client.host if request.client else "unknown-client"


def _enforce_rate_limit(
    request: Request,
    *,
    bucket: str,
    limit: int,
    subject: str | None = None,
    include_ip: bool = True,
) -> None:
    settings = get_settings()
    if not getattr(settings, "rate_limits_enabled", True):
        return
    window_seconds = int(getattr(settings, "rate_limit_window_seconds", 60))
    limiter = get_rate_limiter()
    subjects = [(f"{bucket}.ip", _client_subject(request))] if include_ip else []
    if subject:
        subjects.append((f"{bucket}.subject", subject))
    for scoped_bucket, scoped_subject in subjects:
        decision = limiter.check(
            scoped_bucket,
            scoped_subject,
            limit=limit,
            window_seconds=window_seconds,
        )
        if decision.allowed:
            continue
        trace_event(
            "rate_limit.blocked",
            bucket=bucket,
            scope=scoped_bucket.rsplit(".", 1)[-1],
            retry_after_seconds=decision.retry_after_seconds,
        )
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Bạn thao tác quá nhanh. Vui lòng chờ một chút rồi thử lại.",
                "retryable": True,
            },
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


def _enforce_action_rate_limit(request: Request, action: str | None, payload: dict[str, Any]) -> None:
    if not action:
        return
    settings = get_settings()
    if action in {"hold_slot", "hold_reschedule"}:
        subject = str(payload.get("slot_id") or payload.get("new_slot_id") or "")
        _enforce_rate_limit(
            request,
            bucket="booking_hold",
            limit=int(getattr(settings, "booking_hold_rate_limit_requests", 20)),
            subject=subject,
        )
    elif action in {"confirm_booking", "confirm_reschedule"}:
        subject = str(payload.get("booking_id") or payload.get("current_booking_id") or "")
        _enforce_rate_limit(
            request,
            bucket="booking_confirm",
            limit=int(getattr(settings, "booking_confirm_rate_limit_requests", 10)),
            subject=subject,
        )
    elif action in {"request_access", "verify_access"}:
        subject = str(payload.get("contact_value") or payload.get("challenge_id") or "")
        _enforce_rate_limit(
            request,
            bucket="booking_otp",
            limit=int(getattr(settings, "booking_otp_rate_limit_requests", 10)),
            subject=subject,
        )


def _abuse_subjects(request: Request, thread_id: str) -> tuple[str, ...]:
    subjects = [f"thread:{thread_id}"]
    if request.client and request.client.host:
        subjects.append(f"ip:{request.client.host}")
    return tuple(subjects)


def _raise_abuse_ban(status: AbuseStatus) -> None:
    retry_after = max(1, status.retry_after_seconds)
    raise HTTPException(
        status_code=403,
        detail={
            "code": "ABUSE_BANNED",
            "message": "Phiên truy cập đã bị khóa do vi phạm chính sách nhiều lần.",
            "retryable": True,
        },
        headers={"Retry-After": str(retry_after)},
    )


def require_operations_admin(
    principal: Annotated[InternalPrincipal, Depends(current_principal)],
) -> InternalPrincipal:
    internal_portal_service.require_roles(principal, InternalRole.OPERATIONS_ADMIN)
    return principal


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    """Chat với AI agent."""
    try:
        settings = get_settings()
        _enforce_rate_limit(
            http_request,
            bucket="chat",
            limit=int(getattr(settings, "chat_rate_limit_requests", 120)),
        )
        trace_id = str(uuid.uuid4())
        token_manager = get_conversation_token_manager()
        identity = token_manager.verify(request.conversation_id) if request.conversation_id else None
        if identity is None:
            identity = token_manager.issue()
            if request.conversation_id:
                trace_event(
                    "guardrail.conversation_reset",
                    trace_id=trace_id,
                    reason="invalid_or_expired_conversation_token",
                )
        conversation_id = identity.public_token
        abuse_tracker = get_abuse_tracker()
        abuse_subjects = _abuse_subjects(http_request, identity.thread_id)
        existing_abuse_status = abuse_tracker.check(abuse_subjects)
        if existing_abuse_status.banned:
            trace_event(
                "guardrail.abuse_ban_enforced",
                trace_id=trace_id,
                retry_after_seconds=existing_abuse_status.retry_after_seconds,
            )
            _raise_abuse_ban(existing_abuse_status)

        guardrails = get_guardrails()
        input_decision = guardrails.inspect_input(
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
            action=request.action,
            action_payload=request.action_payload,
        )
        if not input_decision.allowed:
            if input_decision.code in ABUSE_VIOLATION_CODES:
                abuse_status = abuse_tracker.record_violation(
                    abuse_subjects,
                    violation_code=input_decision.code,
                    max_strikes=settings.guardrails_abuse_max_strikes,
                    strike_window_seconds=settings.guardrails_abuse_strike_window_seconds,
                    ban_seconds=settings.guardrails_abuse_ban_seconds,
                )
                trace_event(
                    "guardrail.abuse_strike",
                    trace_id=trace_id,
                    code=input_decision.code,
                    strike_count=abuse_status.strike_count,
                    banned=abuse_status.banned,
                )
                if abuse_status.banned:
                    _raise_abuse_ban(abuse_status)
            trace_event(
                "guardrail.input_blocked",
                trace_id=trace_id,
                conversation_id=conversation_id,
                code=input_decision.code,
                reason=input_decision.reason,
                details=input_decision.details,
            )
            warning = ""
            if input_decision.code in ABUSE_VIOLATION_CODES:
                warning = (
                    f" Cảnh báo vi phạm {abuse_status.strike_count}/"
                    f"{settings.guardrails_abuse_max_strikes}; lần thứ "
                    f"{settings.guardrails_abuse_max_strikes} sẽ bị khóa."
                )
            return ChatResponse(
                response=input_decision.user_message + warning,
                conversation_id=conversation_id,
                action_error=input_decision.code,
            )

        safe_message = input_decision.sanitized_text or request.message
        safe_context = input_decision.sanitized_context or {}
        _enforce_rate_limit(
            http_request,
            bucket="chat",
            limit=int(getattr(settings, "chat_rate_limit_requests", 120)),
            subject=identity.thread_id,
            include_ip=False,
        )
        _enforce_action_rate_limit(http_request, request.action, request.action_payload)
        trace_event(
            "chat.request",
            trace_id=trace_id,
            conversation_id=conversation_id,
            message=safe_message,
            context=safe_context,
            action=request.action,
            action_payload=request.action_payload,
        )
        config = {"configurable": {"thread_id": identity.thread_id}}
        logging.getLogger("agent.requests").info(
            "chat_started trace_id=%s requested_action=%s", trace_id, request.action or "llm"
        )
        # Keep the module-level `agent` overrideable by existing tests, while
        # production resolves the graph initialized with the Postgres saver.
        active_agent = agent if agent is not _default_agent else get_agent()
        result = await cast(Any, active_agent).ainvoke(
            {
                "query": safe_message,
                "context": safe_context,
                "requested_action": request.action,
                "action_payload": request.action_payload,
                "action_result": None,
                "action_tool": "",
                "action_input": {},
                "action_error": "",
                "metadata": {"trace_id": trace_id},
            },
            config=config,
        )
        logging.getLogger("agent.requests").info(
            "chat_finished trace_id=%s tool=%s status=%s",
            trace_id,
            result.get("action_tool") or "none",
            "error" if result.get("action_error") else "success",
        )
        protected = guardrails.protect_output(result)
        response = ChatResponse(
            response=protected.response,
            analysis=protected.analysis,
            conversation_id=conversation_id,
            tool_name=result.get("action_tool", ""),
            tool_input=protected.tool_input,
            action_data=protected.action_data,
            action_error=protected.action_error,
        )
        trace_event(
            "chat.response",
            trace_id=trace_id,
            conversation_id=conversation_id,
            response=response.model_dump(),
            intent=result.get("intent"),
            active_skill=result.get("active_skill"),
            tool_call_count=result.get("tool_call_count"),
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        trace_event(
            "chat.error",
            trace_id=locals().get("trace_id", ""),
            conversation_id=locals().get("conversation_id", request.conversation_id),
            error=str(e),
        )
        logging.getLogger(__name__).error("Internal error in chat endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau.")


@router.get("/status")
async def agent_status():
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}


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
    expose_mock_otp = settings.app_env != "production"
    kwargs.setdefault("booking_code", None)
    if expose_mock_otp and not settings.zalo_bot_enabled and kwargs.get("preferred_channel") == "zalo":
        kwargs["preferred_channel"] = "sms"
    return booking_service.request_access(**kwargs, expose_otp=expose_mock_otp)


@router.post("/demo/action")
async def demo_action(request: DemoActionRequest, http_request: Request):
    """Deterministic UI simulator: one button maps to one tool/command."""
    p = request.payload
    actions: dict[str, tuple[str, Callable[..., Any]]] = {
        "search_options": ("SearchOptionsQuery", booking_service.search_options),
        "hold_slot": ("HoldSlotCommand", booking_service.hold_slot),
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
    if request.action not in actions:
        raise HTTPException(status_code=400, detail="Unknown demo action")
    action_decision = get_guardrails().inspect_demo_action(action=request.action, payload=p)
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
    _enforce_action_rate_limit(http_request, request.action, p)
    name, handler = actions[request.action]
    try:
        data = handler(**p)
        if request.action == "request_access":
            allow_mock_otp = get_settings().app_env != "production" and data.get("is_mock") is True
            if not allow_mock_otp:
                data.pop("otp_code", None)
        kind = "Agent gọi tool" if request.action in AGENT_TOOLS else "Backend chạy UI command"
        return {"success": True, "message": f"{kind}: {name}", "tool": name, "data": data}
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
