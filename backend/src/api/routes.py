import json
import logging
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from src.agents.graph import agent, get_agent
from src.agents.tools import (
    get_booking_details,
    get_booking_draft,
    verify_booking_access,
)
from src.agents.trace import redact, trace_event
from src.dependencies import booking_service
from src.guardrails import get_guardrails
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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat với AI agent."""
    try:
        # Tạo conversation_id mới nếu client không truyền
        conversation_id = request.conversation_id or str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        guardrails = get_guardrails()
        input_decision = guardrails.inspect_input(
            message=request.message,
            conversation_id=conversation_id,
            context=request.context,
            action=request.action,
            action_payload=request.action_payload,
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

        safe_message = input_decision.sanitized_text or request.message
        trace_event(
            "chat.request",
            trace_id=trace_id,
            conversation_id=conversation_id,
            message=safe_message,
            context=request.context,
            action=request.action,
            action_payload=request.action_payload,
        )
        config = {"configurable": {"thread_id": conversation_id}}
        logging.getLogger("agent.requests").info(
            "chat_started conversation_id=%s requested_action=%s", conversation_id, request.action or "llm"
        )
        # Keep the module-level `agent` overrideable by existing tests, while
        # production resolves the graph initialized with the Postgres saver.
        active_agent = agent if agent is not _default_agent else get_agent()
        result = await active_agent.ainvoke(
            {
                "query": safe_message,
                "context": request.context,
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
            "chat_finished conversation_id=%s tool=%s status=%s",
            conversation_id,
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
        raise HTTPException(status_code=503, detail={"code": "BOOKING_UNAVAILABLE", "message": "Dịch vụ đặt lịch tạm thời gián đoạn."})


AGENT_TOOLS = {"get_draft", "request_access", "verify_access", "get_details"}


@router.post("/demo/action")
async def demo_action(request: DemoActionRequest):
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
            lambda **kw: booking_service.request_access(**kw),
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
    name, handler = actions[request.action]
    try:
        data = handler(**p)
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
async def import_showrooms(request: CsvImportRequest):
    try:
        return {"success": True, "data": booking_service.import_showrooms_csv(request.csv_text)}
    except BookingError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)})


@router.post("/admin/import/eval-dataset")
async def import_eval_dataset(request: DatasetImportRequest):
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


@router.get("/dashboard")
async def dashboard(limit: int = 50):
    """Read-only monitoring endpoint for the booking demo."""
    return booking_service.get_dashboard(limit)
