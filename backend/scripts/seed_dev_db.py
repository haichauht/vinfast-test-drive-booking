from __future__ import annotations

import os
import csv
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.config import get_settings
from src.database import Database
from src.services.booking import BookingService

RESET_ORDER = (
    "booking_access_sessions",
    "otp_challenges",
    "notification_jobs",
    "notification_plans",
    "booking_events",
    "booking_driver_details",
    "idempotency_records",
    "bookings",
    "slot_sales_assignments",
    "test_drive_slots",
    "demo_vehicles",
    "vehicle_variants",
    "vehicle_models",
    "sales_staff",
    "showrooms",
    "people",
)

SEED_CHECK_TABLES = ("vehicle_models", "showrooms", "sales_staff", "demo_vehicles", "test_drive_slots", "bookings")


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _seed_showrooms_from_csv(path: Path, now_str: str, limit: int = 8) -> list[tuple] | None:
    if not path.exists():
        return None
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                (
                    row["id"],
                    row["code"],
                    row["name"],
                    row["address"],
                    float(row["latitude"]),
                    float(row["longitude"]),
                    row.get("phone") or None,
                    row.get("email") or None,
                    row.get("timezone") or "Asia/Ho_Chi_Minh",
                    0 if str(row.get("is_active", "1")).lower() in {"0", "false", "no"} else 1,
                    row.get("created_at") or now_str,
                    row.get("updated_at") or now_str,
                )
            )
            if len(rows) >= limit:
                break
    return rows or None


def seed_db() -> None:
    settings = get_settings()
    database = Database(settings.database_url)
    database.initialize()
    service = BookingService(database)
    reset_requested = os.getenv("RESET_DEV_DB", "").lower() in {"1", "true", "yes"}

    with database.connect() as connection:
        existing_rows = sum(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in SEED_CHECK_TABLES)
    if existing_rows and not reset_requested:
        print(
            "Database already contains booking data; seed skipped. "
            "Set RESET_DEV_DB=1 to replace dev fixtures."
        )
        return

    data_dir = Path(settings.eval_data_dir)
    if settings.auto_load_eval_data and data_dir.exists():
        if reset_requested:
            with database.transaction(immediate=True) as connection:
                for table in RESET_ORDER:
                    connection.execute(f"DELETE FROM {table}")
        result = service.import_eval_dataset_from_dir(data_dir)
        print(f"Imported full eval dataset from {data_dir}: {result}")
        return

    now = datetime.now(UTC)
    now_str = _iso(now)

    models = [
        ("model_vf3", "VF3", "VF 3", "Mini eSUV", "B1", "Yeu cau GPLX hang B1 tro len", 1, now_str, now_str),
        ("model_vf5", "VF5", "VF 5", "A-SUV", "B1", "Yeu cau GPLX hang B1 tro len", 1, now_str, now_str),
        ("model_vf6", "VF6", "VF 6", "B-SUV", "B1", "Yeu cau GPLX hang B1 tro len", 1, now_str, now_str),
        ("model_vf7", "VF7", "VF 7", "C-SUV", "B1", "Yeu cau GPLX hang B1 tro len", 1, now_str, now_str),
        ("model_vf8", "VF8", "VF 8", "D-SUV", "B1", "Yeu cau GPLX hang B1 tro len", 1, now_str, now_str),
        ("model_vf9", "VF9", "VF 9", "E-SUV", "B1", "Yeu cau GPLX hang B1 tro len", 1, now_str, now_str),
    ]

    variants = [
        ("var_vf3_eco", "model_vf3", "VF3-ECO", "Eco", 18.4, 210.0, 32.0, 1, now_str, now_str),
        ("var_vf5_plus", "model_vf5", "VF5-PLUS", "Plus", 37.23, 300.0, 100.0, 1, now_str, now_str),
        ("var_vf6_eco", "model_vf6", "VF6-ECO", "Eco", 59.6, 399.0, 130.0, 1, now_str, now_str),
        ("var_vf6_plus", "model_vf6", "VF6-PLUS", "Plus", 59.6, 381.0, 150.0, 1, now_str, now_str),
        ("var_vf7_base", "model_vf7", "VF7-BASE", "Base", 59.6, 375.0, 110.0, 1, now_str, now_str),
        ("var_vf7_plus", "model_vf7", "VF7-PLUS", "Plus", 75.3, 431.0, 260.0, 1, now_str, now_str),
        ("var_vf8_eco", "model_vf8", "VF8-ECO", "Eco", 87.7, 471.0, 260.0, 1, now_str, now_str),
        ("var_vf8_plus", "model_vf8", "VF8-PLUS", "Plus", 87.7, 447.0, 300.0, 1, now_str, now_str),
        ("var_vf9_eco", "model_vf9", "VF9-ECO", "Eco", 123.0, 580.0, 300.0, 1, now_str, now_str),
        ("var_vf9_plus", "model_vf9", "VF9-PLUS", "Plus", 123.0, 580.0, 300.0, 1, now_str, now_str),
    ]

    showrooms = [
        ("sr_hanoi", "SR-HANOI", "VinFast Nguyen Van Cu", "3-5 Nguyen Van Cu, Long Bien, Ha Noi", 21.045, 105.882, "024123456", "sr_hanoi@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_hcm", "SR-HCM", "VinFast Landmark 81", "Vinhomes Central Park, Binh Thanh, TP. Ho Chi Minh", 10.795, 106.722, "028123456", "sr_hcm@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_danang", "SR-DANANG", "VinFast Ngo Quyen", "910A Ngo Quyen, Son Tra, Da Nang", 16.071, 108.231, "0236123456", "sr_danang@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_smart_city", "SR-SMARTCITY", "VinFast Smart City", "Vinhomes Smart City, Nam Tu Liem, Ha Noi", 21.004, 105.748, "024123457", "sr_smartcity@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_royal_city", "SR-ROYAL", "VinFast Royal City", "72A Nguyen Trai, Thanh Xuan, Ha Noi", 21.003, 105.816, "024123458", "sr_royal@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_mydinh", "SR-MYDINH", "VinFast My Dinh", "8 Pham Hung, Cau Giay, Ha Noi", 21.028, 105.782, "024123459", "sr_mydinh@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_ocean_park", "SR-OCEANPARK", "VinFast Ocean Park", "Vinhomes Ocean Park, Gia Lam, Ha Noi", 20.989, 105.952, "024123460", "sr_oceanpark@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_tayho", "SR-TAYHO", "VinFast Tay Ho", "Vo Chi Cong, Tay Ho, Ha Noi", 21.072, 105.803, "024123461", "sr_tayho@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
    ]
    showroom_csv = Path(settings.eval_data_dir) / "03_showrooms.csv"
    showrooms = _seed_showrooms_from_csv(showroom_csv, now_str) or showrooms

    staff = [
        (
            f"staff_{index + 1}",
            showroom[0],
            f"EMP-{index + 1:03d}",
            f"Sales Consultant {index + 1}",
            f"09000000{index + 1:02d}",
            f"sales{index + 1}@vinfast.vn",
            "sales_consultant",
            "active",
            1,
            now_str,
            now_str,
        )
        for index, showroom in enumerate(showrooms)
    ]

    demo_vehicles = []
    vehicle_idx = 1
    showroom_codes = [(showroom[0], f"SR{index + 1}") for index, showroom in enumerate(showrooms)]
    drive_variants = [
        ("var_vf3_eco", "VF3"),
        ("var_vf5_plus", "VF5"),
        ("var_vf6_plus", "VF6"),
        ("var_vf7_plus", "VF7"),
        ("var_vf8_plus", "VF8"),
        ("var_vf9_plus", "VF9"),
    ]
    for showroom_id, showroom_code in showroom_codes:
        for variant_id, variant_code in drive_variants:
            demo_vehicles.append(
                (
                    f"dv_{showroom_code.lower()}_{variant_code.lower()}",
                    showroom_id,
                    variant_id,
                    f"AST-{showroom_code}-{variant_code}",
                    f"VIN{showroom_code}DEMO{vehicle_idx:05d}",
                    f"{showroom_code}-DEMO-{vehicle_idx:02d}",
                    "available",
                    95.0,
                    15.0,
                    "not_charging",
                    1,
                    now_str,
                    now_str,
                )
            )
            vehicle_idx += 1

    slots = []
    slot_idx = 1
    base_date = now.date() + timedelta(days=1)
    for demo_vehicle in demo_vehicles:
        demo_vehicle_id, showroom_id = demo_vehicle[0], demo_vehicle[1]
        for day_offset in range(7):
            date = base_date + timedelta(days=day_offset)
            for start_time, end_time in (
                ("09:00:00", "10:00:00"),
                ("10:30:00", "11:30:00"),
                ("14:00:00", "15:00:00"),
                ("15:30:00", "16:30:00"),
            ):
                slots.append(
                    (
                        f"slot_{slot_idx}",
                        showroom_id,
                        demo_vehicle_id,
                        f"{date.isoformat()}T{start_time}+00:00",
                        f"{date.isoformat()}T{end_time}+00:00",
                        "available",
                        None,
                        None,
                        None,
                        now_str,
                        now_str,
                    )
                )
                slot_idx += 1

    with database.transaction(immediate=True) as connection:
        existing_rows = sum(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("vehicle_models", "showrooms", "sales_staff", "demo_vehicles", "test_drive_slots", "bookings")
        )
        reset_requested = os.getenv("RESET_DEV_DB", "").lower() in {"1", "true", "yes"}
        if existing_rows and not reset_requested:
            print(
                "Database already contains booking data; seed skipped. "
                "Set RESET_DEV_DB=1 to replace dev fixtures."
            )
            return

        for table in (
            "booking_access_sessions",
            "otp_challenges",
            "notification_jobs",
            "notification_plans",
            "booking_events",
            "booking_driver_details",
            "idempotency_records",
            "bookings",
            "slot_sales_assignments",
            "test_drive_slots",
            "demo_vehicles",
            "vehicle_variants",
            "vehicle_models",
            "sales_staff",
            "showrooms",
            "people",
        ):
            connection.execute(f"DELETE FROM {table}")

        connection.executemany(
            "INSERT INTO vehicle_models(id,code,name,vehicle_type,required_license_class,license_requirement_note,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            models,
        )
        connection.executemany(
            "INSERT INTO vehicle_variants(id,model_id,code,name,battery_capacity_kwh,estimated_range_km,motor_power_kw,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            variants,
        )
        connection.executemany(
            "INSERT INTO showrooms(id,code,name,address,latitude,longitude,phone,email,timezone,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            showrooms,
        )
        connection.executemany(
            "INSERT INTO sales_staff(id,showroom_id,employee_code,full_name,phone,email,role,status,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            staff,
        )
        connection.executemany(
            "INSERT INTO demo_vehicles(id,showroom_id,variant_id,asset_code,vin,plate_number,operational_status,battery_soc,minimum_booking_soc,charging_status,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            demo_vehicles,
        )
        connection.executemany(
            "INSERT INTO test_drive_slots(id,showroom_id,demo_vehicle_id,start_at,end_at,status,held_until,current_booking_id,block_reason,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            slots,
        )

    if showroom_csv.exists():
        result = BookingService(database).import_showrooms_csv(showroom_csv.read_text(encoding="utf-8-sig"))
        print(f"Imported {result['imported']} showrooms from {showroom_csv}.")

    print(
        "Seeded database "
        f"{settings.database_url} with {len(models)} models, {len(variants)} variants, "
        f"{len(showrooms)} showrooms, {len(staff)} staff, {len(demo_vehicles)} vehicles, and {len(slots)} slots."
    )


if __name__ == "__main__":
    seed_db()
