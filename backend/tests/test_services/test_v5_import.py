from pathlib import Path

import pytest
from src.database import Database
from src.internal_portal import InternalPrincipal, InternalRole
from src.internal_portal.service import InternalPortalService
from src.services.booking import BookingService
from src.services.zalo_bot import ZaloOtpSender

PROJECT_ROOT = Path(__file__).resolve().parents[3]
V5_DATASET_ROOT = PROJECT_ROOT / "eval" / "data"


@pytest.fixture(scope="module")
def v5_database(tmp_path_factory):
    if not (V5_DATASET_ROOT / "seed" / "32_internal_audit_events.csv").exists():
        pytest.skip("V5 incoming dataset is not present in this checkout.")
    database = Database(tmp_path_factory.mktemp("v5-database") / "v5.db", validate_schema=False)
    database.initialize()
    result = BookingService(database).import_eval_dataset_from_dir(V5_DATASET_ROOT)
    return database, result


def test_v5_import_loads_all_tables_atomically(v5_database):
    database, result = v5_database

    assert result["dataset_version"] == "v5"
    assert result["total_rows"] == 102_286
    assert result["missing_expected_files"] == []
    assert len(result["imported"]) == 32
    with database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM showrooms").fetchone()[0] == 319
        assert connection.execute("SELECT count(*) FROM test_drive_slots").fetchone()[0] == 45_825
        assert connection.execute("SELECT count(*) FROM bookings").fetchone()[0] == 423
        assert connection.execute("SELECT count(DISTINCT full_name) FROM sales_staff").fetchone()[0] == 94
        assert connection.execute("SELECT count(*) FROM internal_users").fetchone()[0] == 142
        assert connection.execute(
            "SELECT count(*) FROM (SELECT showroom_id FROM sales_staff GROUP BY showroom_id HAVING count(*)=2)"
        ).fetchone()[0] == 47
        assert connection.execute("SELECT count(DISTINCT full_name) FROM people").fetchone()[0] == 564
        assert {
            row["status"]: row["total"]
            for row in connection.execute("SELECT status,count(*) total FROM bookings GROUP BY status")
        } == {
            "cancelled": 47,
            "checked_in": 38,
            "completed": 73,
            "confirmed": 146,
            "expired": 17,
            "held": 23,
            "no_show": 32,
            "rescheduled": 47,
        }
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_v5_seed_is_usable_by_internal_portal_and_zalo(v5_database):
    database, _ = v5_database
    with database.connect() as connection:
        operations_admin = connection.execute(
            "SELECT * FROM internal_users WHERE role='operations_admin' AND is_active=1 LIMIT 1"
        ).fetchone()
        linked_phone = connection.execute(
            "SELECT p.phone FROM zalo_identity_links z JOIN people p ON p.id=z.person_id LIMIT 1"
        ).fetchone()[0]

    principal = InternalPrincipal(
        operations_admin["id"],
        operations_admin["username"],
        operations_admin["display_name"],
        InternalRole.OPERATIONS_ADMIN,
        operations_admin["staff_id"],
        (),
    )
    dashboard = InternalPortalService(database).dashboard(principal)

    assert sum(dashboard["booking_counts"].values()) == 423
    assert ZaloOtpSender(database, object()).is_linked(linked_phone)


@pytest.mark.parametrize(
    ("username", "expected_role"),
    [
        ("admin.check", InternalRole.OPERATIONS_ADMIN),
        ("thanglongtayho.check", InternalRole.SHOWROOM_MANAGER),
        ("ngan.thanglongtayho", InternalRole.STAFF),
    ],
)
def test_v5_seeded_internal_accounts_can_log_in(v5_database, username, expected_role):
    database, _ = v5_database
    result = InternalPortalService(database).login(username, "1234512345")

    assert result["user"]["username"] == username
    assert result["user"]["role"] == expected_role.value
