from src.bootstrap import initialize_database
from src.config import get_settings
from src.database import Database
from src.services.booking import BookingService

settings = get_settings()
database = Database(settings.database_url)
initialize_database(database, settings)
booking_service = BookingService(database)
