from langchain_core.tools import tool

from src.dependencies import booking_service


@tool
def search_test_drive_options(
    vehicle_model: str,
    vehicle_variant: str | None = None,
    showroom_id: str | None = None,
    showroom_query: str | None = None,
    address: str | None = None,
    preferred_date: str | None = None,
    preferred_time: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    showroom_limit: int = 5,
    slot_limit: int | None = None,
) -> dict:
    """Tìm showroom hoặc slot lái thử; không giữ slot."""
    return booking_service.search_options(
        vehicle_model=vehicle_model,
        vehicle_variant=vehicle_variant,
        showroom_id=showroom_id,
        showroom_query=showroom_query,
        address=address,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        latitude=latitude,
        longitude=longitude,
        showroom_limit=showroom_limit,
        slot_limit=slot_limit,
    )
