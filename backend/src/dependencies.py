from src.config import get_settings
from src.database import Database
from src.services.booking import BookingService


def _sqlite_path(url: str) -> str:
    if not url.startswith("sqlite:///"):
        raise RuntimeError(
            "Phiên bản MVP hiện chỉ hỗ trợ DATABASE_URL SQLite.")
    return url.removeprefix("sqlite:///")


database = Database(_sqlite_path(get_settings().database_url))
database.initialize()
booking_service = BookingService(database)
