from langchain_core.tools import tool

from src.dependencies import booking_service


@tool
def verify_booking_access(challenge_id: str, otp_code: str) -> dict:
    """Xác minh OTP single-use và tạo access session có permission theo purpose."""
    return booking_service.verify_access(challenge_id, otp_code)
