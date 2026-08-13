from src.config import get_settings
from src.database import Database
from src.internal_portal import InternalPortalService
from src.services.booking import BookingService
from src.services.booking.notifications import RoutingMessagingProvider
from src.services.zalo_bot import ZaloBotClient, ZaloOtpSender

settings = get_settings()
database = Database(settings.database_url)
zalo_client = (
    ZaloBotClient(token=settings.zalo_bot_token, api_base_url=settings.zalo_bot_api_base_url)
    if settings.zalo_bot_enabled and settings.zalo_bot_token
    else None
)
zalo_otp_sender = ZaloOtpSender(database, zalo_client) if zalo_client else None
booking_service = BookingService(
    database,
    otp_sender=zalo_otp_sender,
    messaging_provider=RoutingMessagingProvider(zalo_provider=zalo_otp_sender),
    otp_ttl_seconds=settings.booking_access_otp_ttl_seconds,
    otp_resend_cooldown_seconds=settings.booking_access_otp_resend_cooldown_seconds,
    otp_max_attempts=settings.booking_access_otp_max_attempts,
    otp_secret=settings.booking_access_otp_secret or "development-secret",
)
internal_portal_service = InternalPortalService(
    database,
    session_ttl_seconds=settings.internal_session_ttl_seconds,
)
