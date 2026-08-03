"""SQLite connection management and the MVP booking schema."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS vehicle_models (
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 vehicle_type TEXT NOT NULL, required_license_class TEXT NOT NULL,
 license_requirement_note TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vehicle_variants (
 id TEXT PRIMARY KEY, model_id TEXT NOT NULL REFERENCES vehicle_models(id), code TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL, battery_capacity_kwh REAL, estimated_range_km REAL, motor_power_kw REAL,
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)), created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS showrooms (
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, address TEXT NOT NULL,
 latitude REAL NOT NULL, longitude REAL NOT NULL, phone TEXT, email TEXT,
 timezone TEXT NOT NULL DEFAULT 'Asia/Ho_Chi_Minh', is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_vehicles (
 id TEXT PRIMARY KEY, showroom_id TEXT NOT NULL REFERENCES showrooms(id), variant_id TEXT NOT NULL REFERENCES vehicle_variants(id),
 asset_code TEXT NOT NULL UNIQUE, vin TEXT UNIQUE, plate_number TEXT,
 operational_status TEXT NOT NULL DEFAULT 'available' CHECK(operational_status IN ('available','in_use','charging','maintenance','out_of_service')),
 battery_soc REAL, minimum_booking_soc REAL NOT NULL DEFAULT 0,
 charging_status TEXT NOT NULL DEFAULT 'unknown' CHECK(charging_status IN ('not_charging','charging','fully_charged','unknown')),
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)), created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sales_staff (
 id TEXT PRIMARY KEY, showroom_id TEXT NOT NULL REFERENCES showrooms(id), employee_code TEXT NOT NULL UNIQUE,
 full_name TEXT NOT NULL, phone TEXT, email TEXT, status TEXT NOT NULL DEFAULT 'active',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS test_drive_slots (
 id TEXT PRIMARY KEY, showroom_id TEXT NOT NULL REFERENCES showrooms(id), demo_vehicle_id TEXT NOT NULL REFERENCES demo_vehicles(id),
 start_at TEXT NOT NULL, end_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','held','booked','blocked')),
 held_until TEXT, current_booking_id TEXT, block_reason TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 CHECK(end_at > start_at), UNIQUE(demo_vehicle_id,start_at,end_at)
);
CREATE TABLE IF NOT EXISTS people (
 id TEXT PRIMARY KEY, full_name TEXT NOT NULL, phone TEXT, email TEXT, preferred_channel TEXT NOT NULL DEFAULT 'sms',
 normalized_phone TEXT, normalized_email TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
 id TEXT PRIMARY KEY, booking_code TEXT UNIQUE, slot_id TEXT NOT NULL REFERENCES test_drive_slots(id),
 booker_person_id TEXT REFERENCES people(id), driver_person_id TEXT REFERENCES people(id),
 status TEXT NOT NULL CHECK(status IN ('held','confirmed','expired','cancelled','rescheduled','checked_in','completed','no_show')),
 held_at TEXT NOT NULL, hold_expires_at TEXT NOT NULL, confirmed_at TEXT, checked_in_at TEXT, completed_at TEXT,
 cancelled_at TEXT, cancellation_reason TEXT, rescheduled_from_booking_id TEXT REFERENCES bookings(id),
 replaced_by_booking_id TEXT REFERENCES bookings(id), source_channel TEXT NOT NULL DEFAULT 'web', version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS booking_driver_details (
 booking_id TEXT PRIMARY KEY REFERENCES bookings(id) ON DELETE CASCADE, license_number TEXT,
 declared_license_class TEXT, required_license_class TEXT NOT NULL, validity_acknowledged INTEGER NOT NULL DEFAULT 0,
 license_check_status TEXT NOT NULL DEFAULT 'declared' CHECK(license_check_status IN ('declared','pending_in_person','verified','rejected')),
 checked_at TEXT, checked_by TEXT, rejection_reason TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification_plans (
 booking_id TEXT PRIMARY KEY REFERENCES bookings(id) ON DELETE CASCADE,
 primary_recipient_role TEXT NOT NULL DEFAULT 'driver', copy_booker INTEGER NOT NULL DEFAULT 0,
 sms_enabled INTEGER NOT NULL DEFAULT 1, email_enabled INTEGER NOT NULL DEFAULT 1,
 reminder_24h_enabled INTEGER NOT NULL DEFAULT 1, reminder_2h_enabled INTEGER NOT NULL DEFAULT 1,
 custom_plan_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification_jobs (
 id TEXT PRIMARY KEY, booking_id TEXT NOT NULL REFERENCES bookings(id), recipient_person_id TEXT NOT NULL REFERENCES people(id),
 notification_type TEXT NOT NULL, channel TEXT NOT NULL, scheduled_at TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','processing','sent','failed','cancelled')),
 sent_at TEXT, provider_message_id TEXT, attempt_count INTEGER NOT NULL DEFAULT 0, error_message TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS otp_challenges (
 id TEXT PRIMARY KEY, booking_id TEXT NOT NULL REFERENCES bookings(id), purpose TEXT NOT NULL,
 channel TEXT NOT NULL, destination_masked TEXT NOT NULL, destination_hash TEXT NOT NULL, code_hash TEXT NOT NULL,
 expires_at TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 5,
 resend_count INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending', verified_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS booking_access_sessions (
 id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, booking_id TEXT NOT NULL REFERENCES bookings(id),
 otp_challenge_id TEXT NOT NULL REFERENCES otp_challenges(id), permissions_json TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS booking_events (
 id TEXT PRIMARY KEY, booking_id TEXT NOT NULL REFERENCES bookings(id), event_type TEXT NOT NULL,
 actor_type TEXT NOT NULL, actor_id TEXT, payload_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_records (
 action_id TEXT PRIMARY KEY, operation TEXT NOT NULL, response_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS slot_sales_assignments (
 id TEXT PRIMARY KEY, slot_id TEXT NOT NULL REFERENCES test_drive_slots(id), sales_staff_id TEXT NOT NULL REFERENCES sales_staff(id),
 assignment_role TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(slot_id, sales_staff_id, assignment_role)
);
CREATE INDEX IF NOT EXISTS idx_variants_model_active ON vehicle_variants(model_id,is_active);
CREATE INDEX IF NOT EXISTS idx_showrooms_active ON showrooms(is_active);
CREATE INDEX IF NOT EXISTS idx_demo_lookup ON demo_vehicles(showroom_id,variant_id,operational_status,is_active);
CREATE INDEX IF NOT EXISTS idx_slots_search ON test_drive_slots(showroom_id,start_at,status);
CREATE INDEX IF NOT EXISTS idx_slots_vehicle_time ON test_drive_slots(demo_vehicle_id,start_at,end_at);
CREATE INDEX IF NOT EXISTS idx_sales_showroom ON sales_staff(showroom_id,status);
CREATE INDEX IF NOT EXISTS idx_slot_sales_slot ON slot_sales_assignments(slot_id,status);
CREATE INDEX IF NOT EXISTS idx_bookings_expiry ON bookings(status,hold_expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_active ON otp_challenges(booking_id,status,expires_at);
CREATE INDEX IF NOT EXISTS idx_jobs_due ON notification_jobs(status,scheduled_at);
CREATE INDEX IF NOT EXISTS idx_events_timeline ON booking_events(booking_id,created_at);
"""


class Database:
    def __init__(self, path: str | Path = "data/app.db") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
