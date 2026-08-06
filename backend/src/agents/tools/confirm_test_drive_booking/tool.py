from langchain_core.tools import tool

from src.dependencies import booking_service


@tool
def confirm_test_drive_booking(booking_id: str, expected_version: int, ui_action_id: str) -> dict:
    """Chốt booking sau khi người dùng bấm xác nhận trên UI."""
    return booking_service.confirm_booking(booking_id, ui_action_id, expected_version)
