from __future__ import annotations

import csv
import io
from pathlib import Path

from src.database import DatabaseIntegrityError
from src.services.booking.common import iso, new_id
from src.services.booking.errors import BookingError

_id = new_id


class ImportService:
    @staticmethod
    def _validate_coordinates(latitude: object, longitude: object, *, context: str) -> tuple[float, float]:
        try:
            lat, lon = float(latitude), float(longitude)
        except (TypeError, ValueError) as exc:
            raise BookingError("INVALID_INPUT", f"Invalid coordinates {context}.") from exc
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise BookingError("INVALID_INPUT", f"Coordinates out of range {context}.")
        return lat, lon

    def import_showrooms_csv(self, csv_text: str) -> dict:
        """Upsert showroom rows from a UTF-8 CSV document."""
        required = {"code", "name", "address", "latitude", "longitude"}
        reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise BookingError("INVALID_INPUT", "CSV thiáº¿u cá»™t báº¯t buá»™c: code,name,address,latitude,longitude.")
        imported = 0
        with self.db.transaction(immediate=True) as c:
            for line, row in enumerate(reader, start=2):
                lat, lon = self._validate_coordinates(
                    row["latitude"], row["longitude"], context=f"at line {line}"
                )
                now = iso(self.now())
                existing = c.execute("SELECT id FROM showrooms WHERE code=?", (row["code"].strip(),)).fetchone()
                sid = existing["id"] if existing else _id("showroom")
                c.execute(
                    "INSERT INTO showrooms(id,code,name,address,latitude,longitude,phone,email,timezone,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET name=excluded.name,address=excluded.address,latitude=excluded.latitude,longitude=excluded.longitude,phone=excluded.phone,email=excluded.email,timezone=excluded.timezone,is_active=excluded.is_active,updated_at=excluded.updated_at",
                    (
                        sid,
                        row["code"].strip(),
                        row["name"].strip(),
                        row["address"].strip(),
                        lat,
                        lon,
                        row.get("phone") or None,
                        row.get("email") or None,
                        row.get("timezone") or "Asia/Ho_Chi_Minh",
                        0 if str(row.get("is_active", "1")).lower() in ("0", "false", "no") else 1,
                        now,
                        now,
                    ),
                )
                imported += 1
        return {"imported": imported}

    DATASET_FILES = {
        "01_vehicle_models.csv": (
            "vehicle_models",
            [
                "id",
                "code",
                "name",
                "vehicle_type",
                "required_license_class",
                "license_requirement_note",
                "is_active",
                "created_at",
                "updated_at",
            ],
        ),
        "02_vehicle_variants.csv": (
            "vehicle_variants",
            [
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
            ],
        ),
        "03_showrooms.csv": (
            "showrooms",
            [
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
            ],
        ),
        "04_sales_staff.csv": (
            "sales_staff",
            ["id", "showroom_id", "employee_code", "full_name", "phone", "email", "status", "created_at", "updated_at"],
        ),
        "05_demo_vehicles.csv": (
            "demo_vehicles",
            [
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
            ],
        ),
        # normalized_phone/email are database-only nullable derivatives, not mock CSV fields.
        "08_people.csv": (
            "people",
            ["id", "full_name", "phone", "email", "preferred_channel", "created_at", "updated_at"],
        ),
        "06_test_drive_slots.csv": (
            "test_drive_slots",
            [
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
            ],
        ),
        "09_bookings.csv": (
            "bookings",
            [
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
                "source_channel",
                "version",
                "created_at",
                "updated_at",
            ],
        ),
        "07_slot_sales_assignments.csv": (
            "slot_sales_assignments",
            ["id", "slot_id", "sales_staff_id", "assignment_role", "status", "created_at", "updated_at"],
        ),
        "10_booking_driver_details.csv": (
            "booking_driver_details",
            [
                "booking_id",
                "license_number",
                "declared_license_class",
                "required_license_class",
                "validity_acknowledged",
                "license_check_status",
                "checked_at",
                "checked_by",
                "rejection_reason",
                "created_at",
                "updated_at",
            ],
        ),
        "11_notification_plans.csv": (
            "notification_plans",
            [
                "booking_id",
                "primary_recipient_role",
                "copy_booker",
                "sms_enabled",
                "email_enabled",
                "reminder_24h_enabled",
                "reminder_2h_enabled",
                "custom_plan_json",
                "created_at",
                "updated_at",
            ],
        ),
        "12_notification_jobs.csv": (
            "notification_jobs",
            [
                "id",
                "booking_id",
                "recipient_person_id",
                "notification_type",
                "channel",
                "scheduled_at",
                "status",
                "sent_at",
                "provider_message_id",
                "attempt_count",
                "error_message",
                "created_at",
                "updated_at",
            ],
        ),
        "13_otp_challenges.csv": (
            "otp_challenges",
            [
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
                "created_at",
            ],
        ),
        # token_hash is generated during import because mock sessions contain no usable raw token.
        "14_booking_access_sessions.csv": (
            "booking_access_sessions",
            ["id", "booking_id", "otp_challenge_id", "permissions_json", "expires_at", "revoked_at", "created_at"],
        ),
        "15_booking_events.csv": (
            "booking_events",
            ["id", "booking_id", "event_type", "actor_type", "actor_id", "payload_json", "created_at"],
        ),
    }

    DATASET_REFERENCES = {
        "02_vehicle_variants.csv": (("model_id", "vehicle_models", "id", "01_vehicle_models.csv"),),
        "04_sales_staff.csv": (("showroom_id", "showrooms", "id", "03_showrooms.csv"),),
        "05_demo_vehicles.csv": (
            ("showroom_id", "showrooms", "id", "03_showrooms.csv"),
            ("variant_id", "vehicle_variants", "id", "02_vehicle_variants.csv"),
        ),
        "06_test_drive_slots.csv": (
            ("showroom_id", "showrooms", "id", "03_showrooms.csv"),
            ("demo_vehicle_id", "demo_vehicles", "id", "05_demo_vehicles.csv"),
        ),
        "09_bookings.csv": (
            ("slot_id", "test_drive_slots", "id", "06_test_drive_slots.csv"),
            ("booker_person_id", "people", "id", "08_people.csv"),
            ("driver_person_id", "people", "id", "08_people.csv"),
        ),
        "07_slot_sales_assignments.csv": (
            ("slot_id", "test_drive_slots", "id", "06_test_drive_slots.csv"),
            ("sales_staff_id", "sales_staff", "id", "04_sales_staff.csv"),
        ),
        "10_booking_driver_details.csv": (("booking_id", "bookings", "id", "09_bookings.csv"),),
        "11_notification_plans.csv": (("booking_id", "bookings", "id", "09_bookings.csv"),),
        "12_notification_jobs.csv": (
            ("booking_id", "bookings", "id", "09_bookings.csv"),
            ("recipient_person_id", "people", "id", "08_people.csv"),
        ),
        "13_otp_challenges.csv": (("booking_id", "bookings", "id", "09_bookings.csv"),),
        "14_booking_access_sessions.csv": (
            ("booking_id", "bookings", "id", "09_bookings.csv"),
            ("otp_challenge_id", "otp_challenges", "id", "13_otp_challenges.csv"),
        ),
        "15_booking_events.csv": (("booking_id", "bookings", "id", "09_bookings.csv"),),
    }

    @staticmethod
    def _assert_dataset_references(c, filename, rows, references):
        problems = []
        for column, parent_table, parent_column, parent_file in references:
            values = {row[column] for row in rows if row[column]}
            if not values:
                continue
            marks = ",".join("?" * len(values))
            found = {
                row[0]
                for row in c.execute(
                    f"SELECT {parent_column} FROM {parent_table} WHERE {parent_column} IN ({marks})",
                    tuple(values),
                )
            }
            missing = sorted(values - found)
            if missing:
                preview = ", ".join(missing[:5])
                problems.append(f"{column} missing in {parent_table}: {preview}; import {parent_file} first")
        if problems:
            raise BookingError("MISSING_DEPENDENCY", f"Cannot import {filename}: " + " | ".join(problems))

    def import_eval_dataset(self, files: dict[str, str]) -> dict:
        """Import the relational eval CSV set in FK-safe order, atomically."""
        supplied = {name.split("/")[-1]: text for name, text in files.items()}
        unknown = sorted(
            set(supplied)
            - set(self.DATASET_FILES)
            - {"16_import_order.csv", "17_dataset_summary.csv", "18_dataset_metadata.csv"}
        )
        if unknown:
            raise BookingError("INVALID_INPUT", f"File không được hỗ trợ: {', '.join(unknown)}")
        counts = {}
        skipped = []
        with self.db.transaction(immediate=True) as c:
            for filename, (table, expected) in self.DATASET_FILES.items():
                if filename not in supplied:
                    continue
                reader = csv.DictReader(io.StringIO(supplied[filename].lstrip("\ufeff")))
                if reader.fieldnames != expected:
                    raise BookingError("INVALID_INPUT", f"Header {filename} không đúng. Cần: {','.join(expected)}")
                rows = list(reader)
                if not rows:
                    counts[table] = 0
                    continue
                if filename == "03_showrooms.csv":
                    for line, row in enumerate(rows, start=2):
                        self._validate_coordinates(
                            row["latitude"], row["longitude"], context=f"at line {line} of {filename}"
                        )
                self._assert_dataset_references(c, filename, rows, self.DATASET_REFERENCES.get(filename, ()))
                insert_columns = list(expected)
                if filename == "14_booking_access_sessions.csv":
                    insert_columns.insert(1, "token_hash")
                if filename == "10_booking_driver_details.csv":
                    # Legacy dataset compatibility: consume license_number but never persist it.
                    insert_columns.remove("license_number")
                    insert_columns.insert(1, "has_driving_license")
                marks = ",".join("?" * len(insert_columns))
                updates = ",".join(
                    f"{col}=excluded.{col}" for col in insert_columns if col != "id" and col != "booking_id"
                )
                conflict = "booking_id" if "booking_id" in insert_columns and "id" not in insert_columns else "id"
                sql = f"INSERT INTO {table}({','.join(insert_columns)}) VALUES({marks}) ON CONFLICT({conflict}) DO UPDATE SET {updates}"
                try:
                    for row in rows:
                        if filename == "10_booking_driver_details.csv":
                            has_license = (
                                "1" if row.get("declared_license_class") or row.get("license_number") else None
                            )
                            values = []
                            for col in insert_columns:
                                if col == "has_driving_license":
                                    values.append(has_license)
                                else:
                                    values.append(None if row[col] == "" else row[col])
                        else:
                            values = [None if row[col] == "" else row[col] for col in expected]
                        if filename == "14_booking_access_sessions.csv":
                            values.insert(1, self._hash(row["id"], "mock-session"))
                        c.execute(sql, values)
                except DatabaseIntegrityError as exc:
                    raise BookingError(
                        "INVALID_INPUT",
                        f"Không thể import {filename}: thiếu dữ liệu phụ thuộc hoặc vi phạm constraint ({exc}).",
                    ) from exc
                counts[table] = len(rows)
        return {
            "imported": counts,
            "total_rows": sum(counts.values()),
            "skipped": skipped,
            "missing_expected_files": [name for name in self.DATASET_FILES if name not in supplied],
        }

    def import_eval_dataset_from_dir(self, data_dir: str | Path) -> dict:
        """Import supported eval CSV files from a directory."""
        root = Path(data_dir)
        if not root.exists() or not root.is_dir():
            raise BookingError("INVALID_INPUT", f"Eval data folder not found: {root}")
        files = {}
        for filename in [*self.DATASET_FILES, "16_import_order.csv", "17_dataset_summary.csv", "18_dataset_metadata.csv"]:
            path = root / filename
            if path.exists():
                files[filename] = path.read_text(encoding="utf-8-sig")
        if not files:
            raise BookingError("INVALID_INPUT", f"No supported eval CSV files found in: {root}")
        return self.import_eval_dataset(files)
