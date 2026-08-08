"""Central policy constants.

Keeping policy data separate from enforcement code makes reviews and future
changes easier. These expressions intentionally target high-confidence attacks
instead of blocking every occurrence of words such as "prompt" or "system".
"""

from __future__ import annotations

PROMPT_INJECTION_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "PROMPT_INJECTION_OVERRIDE",
        r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,80}"
        r"\b(?:previous|prior|system|developer|hidden)\b.{0,50}"
        r"\b(?:instruction|instructions|prompt|message|rules?)\b",
    ),
    (
        "PROMPT_INJECTION_OVERRIDE",
        r"\b(?:bỏ\s+qua|phớt\s+lờ|quên|vượt\s+qua|ghi\s+đè)\b.{0,80}"
        r"\b(?:hướng\s+dẫn|chỉ\s+thị|system\s*prompt|luật|quy\s+tắc)\b.{0,50}"
        r"\b(?:trước|trước\s+đó|hệ\s+thống|ẩn)\b",
    ),
    (
        "SECRET_EXFILTRATION",
        r"\b(?:reveal|show|print|return|dump|expose|leak)\b.{0,80}"
        r"\b(?:system\s+prompt|developer\s+message|hidden\s+instructions?|api[_ -]?keys?|"
        r"access[_ -]?tokens?|environment\s+variables?|secrets?)\b",
    ),
    (
        "SECRET_EXFILTRATION",
        r"\b(?:hiển\s+thị|tiết\s+lộ|in\s+ra|trả\s+về|đọc\s+ra)\b.{0,80}"
        r"\b(?:system\s*prompt|chỉ\s+thị\s+ẩn|khóa\s*api|api\s*key|token|biến\s+môi\s+trường|bí\s+mật)\b",
    ),
    (
        "ROLE_INJECTION",
        r"<\s*/?\s*(?:tool_call|function_call|system|developer)\b|"
        r"(?:^|\n)\s*(?:system|developer)\s*:\s*",
    ),
    (
        "ROLE_INJECTION",
        r"\b(?:you\s+are\s+now|act\s+as)\b.{0,50}"
        r"\b(?:linux\s+terminal|shell|developer\s+mode|system\s+administrator)\b",
    ),
)

ACTION_ALLOWED_FIELDS: dict[str, frozenset[str]] = {
    "search_options": frozenset(
        {
            "vehicle_model",
            "vehicle_variant",
            "showroom_id",
            "showroom_query",
            "address",
            "preferred_date",
            "preferred_time",
            "latitude",
            "longitude",
            "limit",
        }
    ),
    "hold_slot": frozenset({"slot_id", "ui_action_id"}),
    "update_draft": frozenset(
        {
            "booking_id",
            "booker_patch",
            "driver_patch",
            "driver_same_as_booker",
            "has_valid_license_commitment",
            "notification_plan_patch",
            "expected_version",
        }
    ),
    "confirm_booking": frozenset({"booking_id", "expected_version", "ui_action_id"}),
    "request_access": frozenset({"booking_code", "contact_value", "purpose", "preferred_channel"}),
    "verify_access": frozenset({"challenge_id", "otp_code"}),
}

# `/demo/action` is also a public tool boundary, even though it bypasses the
# LLM. Keep a separate contract because it exposes additional authenticated
# booking-management commands.
DEMO_ACTION_ALLOWED_FIELDS: dict[str, frozenset[str]] = {
    "search_options": ACTION_ALLOWED_FIELDS["search_options"],
    "hold_slot": ACTION_ALLOWED_FIELDS["hold_slot"],
    "get_draft": frozenset({"booking_id"}),
    "update_draft": frozenset(
        {
            "booking_id",
            "booker_patch",
            "driver_patch",
            "driver_same_as_booker",
            "license_patch",
            "notification_plan_patch",
            "expected_version",
        }
    ),
    "confirm_booking": ACTION_ALLOWED_FIELDS["confirm_booking"],
    "request_access": ACTION_ALLOWED_FIELDS["request_access"],
    "verify_access": ACTION_ALLOWED_FIELDS["verify_access"],
    "get_details": frozenset({"access_session_token", "booking_id", "booking_code"}),
    "update_details": frozenset(
        {"booking_id", "access_session_token", "booker_patch", "driver_patch", "driver_same_as_booker"}
    ),
    "hold_reschedule": frozenset(
        {"current_booking_id", "new_slot_id", "access_session_token", "ui_action_id"}
    ),
    "confirm_reschedule": frozenset(
        {"current_booking_id", "new_booking_id", "access_session_token", "ui_action_id"}
    ),
    "cancel_booking": frozenset({"booking_id", "access_session_token", "ui_action_id", "reason"}),
}

MUTATING_TOOL_NAMES = frozenset(
    {
        "hold_test_drive_slot",
        "update_booking_draft",
        "confirm_test_drive_booking",
        "request_booking_access",
        "verify_booking_access",
    }
)

CONFIRMATION_TOOL_NAMES = frozenset({"confirm_test_drive_booking"})

# Values under these keys are never safe in natural-language output or public
# diagnostic fields. Some keys are still intentionally present in action_data so
# the authenticated frontend can continue an OTP workflow.
SECRET_VALUE_KEYS = frozenset(
    {
        "access_session_token",
        "access_token",
        "api_key",
        "authorization",
        "challenge_id",
        "client_secret",
        "contact_value",
        "cookie",
        "license_number",
        "openai_api_key",
        "openrouter_api_key",
        "otp",
        "otp_code",
        "password",
        "refresh_token",
        "token",
        "zalo_bot_token",
    }
)

PUBLIC_TOOL_INPUT_SECRET_KEYS = SECRET_VALUE_KEYS | frozenset(
    {"email", "normalized_email", "normalized_phone", "phone"}
)

# action_data is a machine-readable workflow channel. The browser needs
# challenge_id/access_session_token, but raw OTPs and backend credentials must
# never cross this boundary.
NEVER_PUBLIC_ACTION_DATA_KEYS = frozenset(
    {
        "api_key",
        "authorization",
        "client_secret",
        "cookie",
        "openai_api_key",
        "openrouter_api_key",
        "otp",
        "otp_code",
        "password",
        "refresh_token",
        "token",
        "zalo_bot_token",
    }
)
