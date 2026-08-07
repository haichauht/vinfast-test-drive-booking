from datetime import UTC, datetime, timedelta

from src.services.zalo_bot import ZaloPollingService


class FakeZaloClient:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_text(self, chat_id: str, text: str) -> dict:
        self.sent.append((chat_id, text))
        return {"ok": True}


def test_zalo_polling_deduplicates_message_ids_in_database(booking_db):
    client = FakeZaloClient()
    first_worker = ZaloPollingService(booking_db, client, timeout_seconds=1)
    second_worker = ZaloPollingService(booking_db, client, timeout_seconds=1)
    update = {"message": {"message_id": "message-1", "text": "LIENKET 0901234567", "chat": {"id": "chat-1"}}}

    first_worker._handle_update(update)
    second_worker._handle_update(update)

    with booking_db.connect() as connection:
        assert connection.execute("SELECT count(*) FROM zalo_identity_links").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM zalo_processed_messages").fetchone()[0] == 1
    assert len(client.sent) == 1


def test_zalo_polling_prunes_only_expired_processed_messages(booking_db):
    service = ZaloPollingService(booking_db, FakeZaloClient(), timeout_seconds=1, retention_days=30)
    now = datetime.now(UTC)
    with booking_db.transaction(immediate=True) as connection:
        connection.execute("INSERT INTO zalo_processed_messages VALUES(?,?)", ("old", (now - timedelta(days=31)).isoformat()))
        connection.execute("INSERT INTO zalo_processed_messages VALUES(?,?)", ("recent", (now - timedelta(days=29)).isoformat()))

    service._cleanup_processed_messages_if_due()

    with booking_db.connect() as connection:
        assert connection.execute("SELECT count(*) FROM zalo_processed_messages WHERE message_id='old'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM zalo_processed_messages WHERE message_id='recent'").fetchone()[0] == 1
