from src.config import get_settings
from src.database import Database
from src.internal_portal import InternalPortalService
from src.services.booking import BookingService
from src.services.booking.gmail_provider import GmailMessagingProvider
from src.services.booking.notifications import InMemoryMessagingProvider
from src.services.booking.notifications import RoutingMessagingProvider
from src.services.usage_budget import UsageBudgetService
from src.services.zalo_bot import ZaloBotClient, ZaloOtpSender

settings = get_settings()
database = Database(settings.database_url)
zalo_client = (
    ZaloBotClient(token=settings.zalo_bot_token, api_base_url=settings.zalo_bot_api_base_url)
    if settings.zalo_bot_enabled and settings.zalo_bot_token
    else None
)
zalo_otp_sender = ZaloOtpSender(database, zalo_client) if zalo_client else None
gmail_provider = (
    GmailMessagingProvider(
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        refresh_token=settings.gmail_refresh_token,
        sender_email=settings.gmail_sender_email,
        sender_name=settings.gmail_sender_name,
        timeout_seconds=settings.gmail_timeout_seconds,
    )
    if settings.gmail_enabled
    else None
)
fallback_provider = gmail_provider or InMemoryMessagingProvider()
booking_service = BookingService(
    database,
    otp_sender=gmail_provider or zalo_otp_sender,
    messaging_provider=RoutingMessagingProvider(zalo_provider=zalo_otp_sender, fallback=fallback_provider),
    otp_ttl_seconds=settings.booking_access_otp_ttl_seconds,
    otp_resend_cooldown_seconds=settings.booking_access_otp_resend_cooldown_seconds,
    otp_max_attempts=settings.booking_access_otp_max_attempts,
    otp_request_per_contact_per_hour=settings.rate_limit_otp_request_per_contact_per_hour,
    otp_verify_per_challenge_per_minute=settings.rate_limit_otp_verify_per_challenge_per_minute,
    otp_secret=settings.booking_access_otp_secret or "development-secret",
)
internal_portal_service = InternalPortalService(
    database,
    session_ttl_seconds=settings.internal_session_ttl_seconds,
)
usage_budget_service = UsageBudgetService(database, settings)
