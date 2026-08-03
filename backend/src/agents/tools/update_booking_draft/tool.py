from typing import Any

from langchain_core.tools import tool

from src.dependencies import booking_service


@tool
def update_booking_draft(
    booking_id: str,
    booker_patch: dict[str, Any] | None = None,
    driver_patch: dict[str, Any] | None = None,
    driver_same_as_booker: bool = False,
    license_patch: dict[str, Any] | None = None,
    notification_plan_patch: dict[str, Any] | None = None,
    expected_version: int | None = None,
) -> dict:
    """Patch booking held với optimistic concurrency; không đổi slot hoặc chốt lịch."""
    return booking_service.update_booking_draft(
        booking_id,
        booker_patch=booker_patch,
        driver_patch=driver_patch,
        driver_same_as_booker=driver_same_as_booker,
        license_patch=license_patch,
        notification_plan_patch=notification_plan_patch,
        expected_version=expected_version,
    )
