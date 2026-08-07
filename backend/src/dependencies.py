from src.config import get_settings
from src.database import Database
from src.services.booking import BookingService
from src.services.booking.notifications import RoutingMessagingProvider
from src.services.zalo_bot import ZaloBotClient, ZaloOtpSender


def _sqlite_path(url: str) -> str:
    if not url.startswith("sqlite:///"):
        raise RuntimeError("Phiên bản MVP hiện chỉ hỗ trợ DATABASE_URL SQLite.")
    return url.removeprefix("sqlite:///")


database = Database(_sqlite_path(get_settings().database_url))
database.initialize()
settings = get_settings()
zalo_client = ZaloBotClient(token=settings.zalo_bot_token, api_base_url=settings.zalo_bot_api_base_url) if settings.zalo_bot_enabled and settings.zalo_bot_token else None
booking_service = BookingService(
    database,
    otp_sender=ZaloOtpSender(database, zalo_client) if zalo_client else None,
    messaging_provider=RoutingMessagingProvider(
        zalo_provider=ZaloOtpSender(database, zalo_client) if zalo_client else None,
    ),
    otp_ttl_seconds=settings.booking_access_otp_ttl_seconds,
    otp_resend_cooldown_seconds=settings.booking_access_otp_resend_cooldown_seconds,
    otp_max_attempts=settings.booking_access_otp_max_attempts,
)
