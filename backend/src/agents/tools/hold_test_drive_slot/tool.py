from langchain_core.tools import tool

from src.dependencies import booking_service


@tool
def hold_test_drive_slot(slot_id: str, ui_action_id: str) -> dict:
    """Giữ slot lái thử trong 15 phút sau khi người dùng xác nhận lựa chọn trên UI."""
    return booking_service.hold_slot(slot_id, ui_action_id)
