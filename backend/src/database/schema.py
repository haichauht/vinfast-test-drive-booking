"""Database schema metadata and DDL for the booking service."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: frozenset[str]


TABLES = {
    "vehicle_models": TableSchema(
        "vehicle_models",
        frozenset(
            {
                "id",
                "code",
                "name",
                "vehicle_type",
                "required_license_class",
                "license_requirement_note",
                "is_active",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "vehicle_variants": TableSchema(
        "vehicle_variants",
        frozenset(
            {
                "id",
                "model_id",
                "code",
                "name",
                "battery_capacity_kwh",
                "estimated_range_km",
                "motor_power_kw",
                "is_active",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "showrooms": TableSchema(
        "showrooms",
        frozenset(
            {
                "id",
                "code",
                "name",
                "address",
                "latitude",
                "longitude",
                "phone",
                "email",
                "timezone",
                "is_active",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "demo_vehicles": TableSchema(
        "demo_vehicles",
        frozenset(
            {
                "id",
                "showroom_id",
                "variant_id",
                "asset_code",
                "vin",
                "plate_number",
                "operational_status",
                "battery_soc",
                "minimum_booking_soc",
                "charging_status",
                "is_active",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "sales_staff": TableSchema(
        "sales_staff",
        frozenset(
            {
                "id",
                "showroom_id",
                "employee_code",
                "full_name",
                "phone",
                "email",
                "role",
                "status",
                "is_active",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "test_drive_slots": TableSchema(
        "test_drive_slots",
        frozenset(
            {
                "id",
                "showroom_id",
                "demo_vehicle_id",
                "start_at",
                "end_at",
                "status",
                "held_until",
                "current_booking_id",
                "block_reason",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "people": TableSchema(
        "people",
        frozenset(
            {
                "id",
                "full_name",
                "phone",
                "email",
                "preferred_channel",
                "normalized_phone",
                "normalized_email",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "bookings": TableSchema(
        "bookings",
        frozenset(
            {
                "id",
                "booking_code",
                "slot_id",
                "booker_person_id",
                "driver_person_id",
                "status",
                "held_at",
                "hold_expires_at",
                "confirmed_at",
                "checked_in_at",
                "completed_at",
                "cancelled_at",
                "cancellation_reason",
                "rescheduled_from_booking_id",
                "replaced_by_booking_id",
                "assigned_sales_staff_id",
                "source_channel",
                "version",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "booking_driver_details": TableSchema(
        "booking_driver_details",
        frozenset(
            {
                "booking_id",
                "has_driving_license",
                "declared_license_class",
                "required_license_class",
                "validity_acknowledged",
                "license_check_status",
                "checked_at",
                "checked_by",
                "rejection_reason",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "notification_plans": TableSchema(
        "notification_plans",
        frozenset(
            {
                "booking_id",
                "primary_recipient_role",
                "copy_booker",
                "zalo_enabled",
                "sms_enabled",
                "email_enabled",
                "reminder_24h_enabled",
                "reminder_2h_enabled",
                "custom_plan_json",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "notification_jobs": TableSchema(
        "notification_jobs",
        frozenset(
            {
                "id",
                "booking_id",
                "recipient_person_id",
                "notification_type",
                "channel",
                "scheduled_at",
                "status",
                "attempt_count",
                "max_attempts",
                "last_attempt_at",
                "sent_at",
                "provider_name",
                "provider_status",
                "provider_message_id",
                "is_mock",
                "provider_response_json",
                "error_message",
                "created_at",
                "updated_at",
            }
        ),
    ),
    "otp_challenges": TableSchema(
        "otp_challenges",
        frozenset(
            {
                "id",
                "booking_id",
                "purpose",
                "channel",
                "destination_masked",
                "destination_hash",
                "code_hash",
                "expires_at",
                "attempt_count",
                "max_attempts",
                "resend_count",
                "status",
                "verified_at",
                "consumed_at",
                "created_at",
            }
        ),
    ),
    "booking_access_sessions": TableSchema(
        "booking_access_sessions",
        frozenset(
            {
                "id",
                "token_hash",
                "booking_id",
                "otp_challenge_id",
                "permissions_json",
                "expires_at",
                "revoked_at",
                "created_at",
            }
        ),
    ),
    "booking_events": TableSchema(
        "booking_events",
        frozenset({"id", "booking_id", "event_type", "actor_type", "actor_id", "payload_json", "created_at"}),
    ),
    "idempotency_records": TableSchema(
        "idempotency_records",
        frozenset(
            {
                "action_id",
                "operation",
                "request_hash",
                "status",
                "resource_id",
                "response_json",
                "error_code",
                "created_at",
                "expires_at",
            }
        ),
    ),
    "slot_sales_assignments": TableSchema(
        "slot_sales_assignments",
        frozenset({"id", "slot_id", "sales_staff_id", "assignment_role", "status", "created_at", "updated_at"}),
    ),
    "zalo_identity_links": TableSchema(
        "zalo_identity_links",
        frozenset({"phone", "chat_id", "linked_at", "updated_at"}),
    ),
    "zalo_processed_messages": TableSchema(
        "zalo_processed_messages",
        frozenset({"message_id", "processed_at"}),
    ),
    "rate_limit_counters": TableSchema(
        "rate_limit_counters",
        frozenset({"bucket_key", "window_start", "expires_at", "count", "created_at", "updated_at"}),
    ),
    "llm_budget_ledger": TableSchema(
        "llm_budget_ledger",
        frozenset(
            {
                "id",
                "usage_date",
                "session_id",
                "client_ip",
                "conversation_id",
                "model",
                "estimated_cost_usd",
                "actual_cost_usd",
                "estimated_input_tokens",
                "estimated_output_tokens",
                "actual_input_tokens",
                "actual_output_tokens",
                "status",
                "created_at",
                "finalized_at",
            }
        ),
    ),
}

SCHEMA_SQL = """
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
 full_name TEXT NOT NULL, phone TEXT, email TEXT, role TEXT NOT NULL DEFAULT 'sales_consultant',
 status TEXT NOT NULL DEFAULT 'active', is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
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
 replaced_by_booking_id TEXT REFERENCES bookings(id), assigned_sales_staff_id TEXT REFERENCES sales_staff(id),
 source_channel TEXT NOT NULL DEFAULT 'web', version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS booking_driver_details (
 booking_id TEXT PRIMARY KEY REFERENCES bookings(id) ON DELETE CASCADE,
 has_driving_license INTEGER CHECK(has_driving_license IS NULL OR has_driving_license IN (0,1)),
 declared_license_class TEXT, required_license_class TEXT NOT NULL,
 validity_acknowledged INTEGER NOT NULL DEFAULT 0 CHECK(validity_acknowledged IN (0,1)),
 license_check_status TEXT NOT NULL DEFAULT 'not_provided'
  CHECK(license_check_status IN ('not_provided','declared','pending_in_person','verified','rejected')),
 checked_at TEXT, checked_by TEXT REFERENCES sales_staff(id), rejection_reason TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 CHECK(has_driving_license != 0 OR validity_acknowledged = 0)
);
CREATE TABLE IF NOT EXISTS notification_plans (
 booking_id TEXT PRIMARY KEY REFERENCES bookings(id) ON DELETE CASCADE,
 primary_recipient_role TEXT NOT NULL DEFAULT 'driver', copy_booker INTEGER NOT NULL DEFAULT 0,
 zalo_enabled INTEGER NOT NULL DEFAULT 0, sms_enabled INTEGER NOT NULL DEFAULT 1, email_enabled INTEGER NOT NULL DEFAULT 1,
 reminder_24h_enabled INTEGER NOT NULL DEFAULT 1, reminder_2h_enabled INTEGER NOT NULL DEFAULT 1,
 custom_plan_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification_jobs (
 id TEXT PRIMARY KEY, booking_id TEXT NOT NULL REFERENCES bookings(id), recipient_person_id TEXT NOT NULL REFERENCES people(id),
 notification_type TEXT NOT NULL, channel TEXT NOT NULL, scheduled_at TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','processing','sent','failed','cancelled')),
 attempt_count INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3,
 last_attempt_at TEXT, sent_at TEXT, provider_name TEXT, provider_status TEXT, provider_message_id TEXT,
 is_mock INTEGER NOT NULL DEFAULT 1 CHECK(is_mock IN (0,1)), provider_response_json TEXT, error_message TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS otp_challenges (
 id TEXT PRIMARY KEY, booking_id TEXT NOT NULL REFERENCES bookings(id), purpose TEXT NOT NULL,
 channel TEXT NOT NULL, destination_masked TEXT NOT NULL, destination_hash TEXT NOT NULL, code_hash TEXT NOT NULL,
 expires_at TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 5,
 resend_count INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending',
 verified_at TEXT, consumed_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS booking_access_sessions (
 id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, booking_id TEXT NOT NULL REFERENCES bookings(id),
 otp_challenge_id TEXT NOT NULL REFERENCES otp_challenges(id), permissions_json TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS zalo_identity_links (
 phone TEXT PRIMARY KEY, chat_id TEXT NOT NULL UNIQUE,
 linked_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS zalo_processed_messages (
 message_id TEXT PRIMARY KEY, processed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rate_limit_counters (
 bucket_key TEXT NOT NULL, window_start TEXT NOT NULL, expires_at TEXT NOT NULL,
 count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(bucket_key, window_start)
);
CREATE TABLE IF NOT EXISTS llm_budget_ledger (
 id TEXT PRIMARY KEY, usage_date TEXT NOT NULL, session_id TEXT NOT NULL, client_ip TEXT NOT NULL,
 conversation_id TEXT, model TEXT NOT NULL, estimated_cost_usd REAL NOT NULL,
 actual_cost_usd REAL, estimated_input_tokens INTEGER NOT NULL DEFAULT 0,
 estimated_output_tokens INTEGER NOT NULL DEFAULT 0, actual_input_tokens INTEGER,
 actual_output_tokens INTEGER, status TEXT NOT NULL,
 created_at TEXT NOT NULL, finalized_at TEXT
);
CREATE TABLE IF NOT EXISTS booking_events (
 id TEXT PRIMARY KEY, booking_id TEXT NOT NULL REFERENCES bookings(id), event_type TEXT NOT NULL,
 actor_type TEXT NOT NULL, actor_id TEXT, payload_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_records (
 action_id TEXT PRIMARY KEY, operation TEXT NOT NULL, request_hash TEXT,
 status TEXT NOT NULL DEFAULT 'succeeded', resource_id TEXT,
 response_json TEXT NOT NULL, error_code TEXT, created_at TEXT NOT NULL, expires_at TEXT
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
CREATE INDEX IF NOT EXISTS idx_access_booking_expiry ON booking_access_sessions(booking_id,expires_at);
CREATE INDEX IF NOT EXISTS idx_zalo_identity_chat ON zalo_identity_links(chat_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_expiry ON rate_limit_counters(expires_at);
CREATE INDEX IF NOT EXISTS idx_llm_budget_date_status ON llm_budget_ledger(usage_date,status);
CREATE INDEX IF NOT EXISTS idx_llm_budget_session_date ON llm_budget_ledger(session_id,usage_date,status);
CREATE INDEX IF NOT EXISTS idx_llm_budget_ip_date ON llm_budget_ledger(client_ip,usage_date,status);
"""

