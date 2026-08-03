from langchain_core.tools import tool

from src.dependencies import booking_service


@tool
def request_booking_access(booking_code: str, contact_value: str, purpose: str, preferred_channel: str = "sms") -> dict:
    """Tạo và gửi OTP để quản lý booking; không trả raw OTP."""
    return booking_service.request_access(booking_code, contact_value, purpose, preferred_channel)
