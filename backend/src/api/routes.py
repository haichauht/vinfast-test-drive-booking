import json
import logging

from fastapi import APIRouter, HTTPException

from src.agents.graph import agent
from src.agents.tools import (
    get_booking_details,
    get_booking_draft,
    search_test_drive_options,
    update_booking_draft,
    verify_booking_access,
)
from src.dependencies import booking_service
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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat với AI agent."""
    try:
        result = await agent.ainvoke({"query": request.message})
        return ChatResponse(
            response=result.get("response", ""),
            analysis=result.get("analysis", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def agent_status():
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}

AGENT_TOOLS = {"search_options", "get_draft", "update_draft",
               "request_access", "verify_access", "get_details"}


@router.post("/demo/action")
async def demo_action(request: DemoActionRequest):
    """Deterministic UI simulator: one button maps to one tool/command."""
    p = request.payload
    actions = {
        "search_options": ("search_test_drive_options", lambda **kw: search_test_drive_options.invoke(kw)),
        "hold_slot": ("HoldSlotCommand", booking_service.hold_slot),
        "get_draft": ("get_booking_draft", lambda **kw: get_booking_draft.invoke(kw)),
        "update_draft": ("update_booking_draft", lambda **kw: update_booking_draft.invoke(kw)),
        "confirm_booking": ("ConfirmBookingCommand", booking_service.confirm_booking),
        "request_access": ("request_booking_access", lambda **kw: booking_service.request_access(**kw, expose_otp=True)),
        "verify_access": ("verify_booking_access", lambda **kw: verify_booking_access.invoke(kw)),
        "get_details": ("get_booking_details", lambda **kw: get_booking_details.invoke(kw)),
        "update_details": ("UpdateBookingDetailsCommand", booking_service.update_booking_details),
        "hold_reschedule": ("HoldRescheduleSlotCommand", booking_service.hold_reschedule_slot),
        "confirm_reschedule": ("ConfirmRescheduleCommand", booking_service.confirm_reschedule),
        "cancel_booking": ("CancelBookingCommand", booking_service.cancel_booking),
    }
    if request.action not in actions:
        raise HTTPException(status_code=400, detail="Unknown demo action")
    name, handler = actions[request.action]
    try:
        data = handler(**p)
        kind = "Agent gọi tool" if request.action in AGENT_TOOLS else "Backend chạy UI command"
        return {"success": True, "message": f"{kind}: {name}", "tool": name, "data": data}
    except BookingError as exc:
        return {"success": False, "message": str(exc), "tool": name, "error": {"code": exc.code, "retryable": exc.retryable}}


@router.post("/admin/import/showrooms")
async def import_showrooms(request: CsvImportRequest):
    try:
        return {"success": True, "data": booking_service.import_showrooms_csv(request.csv_text)}
    except BookingError as exc:
        raise HTTPException(status_code=422, detail={
                            "code": exc.code, "message": str(exc)})


@router.post("/admin/import/eval-dataset")
async def import_eval_dataset(request: DatasetImportRequest):
    try:
        return {"success": True, "data": booking_service.import_eval_dataset(request.files)}
    except BookingError as exc:
        logging.getLogger("import").warning(
            "Dataset import rejected files=%s code=%s message=%s", sorted(request.files), exc.code, str(exc))
        raise HTTPException(status_code=422, detail={
                            "code": exc.code, "message": str(exc)})


@router.post("/client-log", status_code=204)
async def client_log(request: ClientLogRequest):
    level = request.level.lower() if request.level.lower() in {
        "debug", "info", "warning", "error"} else "error"
    safe_context = {k: v for k, v in request.context.items(
    ) if k not in {"otp_code", "access_session_token", "contact_value"}}
    getattr(logging.getLogger("frontend"), level)("%s | context=%s",
                                                  request.message, json.dumps(safe_context, ensure_ascii=False, default=str))


@router.get("/dashboard")
async def dashboard(limit: int = 50):
    """Read-only monitoring endpoint for the booking demo."""
    return booking_service.get_dashboard(limit)
