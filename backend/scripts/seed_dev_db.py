import sqlite3
from datetime import datetime, timedelta

def seed_db():
    db_path = 'data/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Disable foreign keys temporarily to clear all data
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DELETE FROM test_drive_slots;")
    cursor.execute("DELETE FROM demo_vehicles;")
    cursor.execute("DELETE FROM vehicle_variants;")
    cursor.execute("DELETE FROM vehicle_models;")
    cursor.execute("DELETE FROM showrooms;")
    cursor.execute("DELETE FROM sales_staff;")
    
    now_str = datetime.utcnow().isoformat() + "Z"
    
    # 1. Seed vehicle_models
    models = [
        ("model_vf3", "VF3", "VF 3", "Mini eSUV", "B1", "Yêu cầu GPLX hạng B1 trở lên", 1, now_str, now_str),
        ("model_vf5", "VF5", "VF 5", "A-SUV", "B1", "Yêu cầu GPLX hạng B1 trở lên", 1, now_str, now_str),
        ("model_vf6", "VF6", "VF 6", "B-SUV", "B1", "Yêu cầu GPLX hạng B1 trở lên", 1, now_str, now_str),
        ("model_vf7", "VF7", "VF 7", "C-SUV", "B1", "Yêu cầu GPLX hạng B1 trở lên", 1, now_str, now_str),
        ("model_vf8", "VF8", "VF 8", "D-SUV", "B1", "Yêu cầu GPLX hạng B1 trở lên", 1, now_str, now_str),
        ("model_vf9", "VF9", "VF 9", "E-SUV", "B1", "Yêu cầu GPLX hạng B1 trở lên", 1, now_str, now_str),
    ]
    cursor.executemany("""
        INSERT INTO vehicle_models (id, code, name, vehicle_type, required_license_class, license_requirement_note, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, models)
    
    # 2. Seed vehicle_variants
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
    cursor.executemany("""
        INSERT INTO vehicle_variants (id, model_id, code, name, battery_capacity_kwh, estimated_range_km, motor_power_kw, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, variants)
    
    # 3. Seed showrooms
    showrooms = [
        ("sr_hanoi", "SR-HANOI", "VinFast Nguyễn Văn Cừ", "Số 3-5 Nguyễn Văn Cừ, Long Biên, Hà Nội", 21.045, 105.882, "024-123456", "sr_hanoi@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_hcm", "SR-HCM", "VinFast Landmark 81", "Khu đô thị Vinhomes Central Park, Bình Thạnh, TP. Hồ Chí Minh", 10.795, 106.722, "028-123456", "sr_hcm@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_danang", "SR-DANANG", "VinFast Ngô Quyền", "Số 910A Ngô Quyền, Sơn Trà, Đà Nẵng", 16.071, 108.231, "0236-123456", "sr_danang@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_smart_city", "SR-SMARTCITY", "VinFast Smart City", "Vinhomes Smart City, Tây Mỗ, Nam Từ Liêm, Hà Nội", 21.004, 105.748, "024-123457", "sr_smartcity@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_royal_city", "SR-ROYAL", "VinFast Royal City", "TTTM Vincom Mega Mall Royal City, 72A Nguyễn Trãi, Thanh Xuân, Hà Nội", 21.003, 105.816, "024-123458", "sr_royal@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_mydinh", "SR-MYDINH", "VinFast Mỹ Đình", "Số 8 Phạm Hùng, Mai Dịch, Cầu Giấy, Hà Nội", 21.028, 105.782, "024-123459", "sr_mydinh@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_ocean_park", "SR-OCEANPARK", "VinFast Ocean Park", "Vinhomes Ocean Park, Gia Lâm, Hà Nội", 20.989, 105.952, "024-123460", "sr_oceanpark@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
        ("sr_tayho", "SR-TAYHO", "VinFast Tây Hồ", "Đường Võ Chí Công, Xuân La, Tây Hồ, Hà Nội", 21.072, 105.803, "024-123461", "sr_tayho@vinfast.vn", "Asia/Ho_Chi_Minh", 1, now_str, now_str),
    ]
    cursor.executemany("""
        INSERT INTO showrooms (id, code, name, address, latitude, longitude, phone, email, timezone, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, showrooms)
    
    # 4. Seed sales staff
    staff = [
        ("staff_hn_1", "sr_hanoi", "EMP-HN01", "Nguyễn Văn Hùng", "0911111111", "hung.nv@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_hcm_1", "sr_hcm", "EMP-HCM01", "Trần Thị Lan", "0922222222", "lan.tt@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_dn_1", "sr_danang", "EMP-DN01", "Lê Hoàng Nam", "0933333333", "nam.lh@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_sm_1", "sr_smart_city", "EMP-SM01", "Phạm Văn Minh", "0944444444", "minh.pv@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_ry_1", "sr_royal_city", "EMP-RY01", "Hoàng Thuỳ Linh", "0955555555", "linh.ht@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_md_1", "sr_mydinh", "EMP-MD01", "Đỗ Anh Tuấn", "0966666666", "tuan.da@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_op_1", "sr_ocean_park", "EMP-OP01", "Bùi Quốc Anh", "0977777777", "anh.bq@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
        ("staff_th_1", "sr_tayho", "EMP-TH01", "Vũ Thị Hà", "0988888888", "ha.vt@vinfast.vn", "sales_consultant", "active", 1, now_str, now_str),
    ]
    cursor.executemany("""
        INSERT INTO sales_staff (id, showroom_id, employee_code, full_name, phone, email, role, status, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, staff)

    # 5. Seed demo_vehicles (1 per variant per showroom)
    demo_vehicles = []
    vehicle_idx = 1
    for sr_id, sr_code in [
        ("sr_hanoi", "HN"),
        ("sr_hcm", "HCM"),
        ("sr_danang", "DN"),
        ("sr_smart_city", "SM"),
        ("sr_royal_city", "RY"),
        ("sr_mydinh", "MD"),
        ("sr_ocean_park", "OP"),
        ("sr_tayho", "TH"),
    ]:
        for var_id, var_code, model_code in [
            ("var_vf3_eco", "VF3", "VF3"),
            ("var_vf5_plus", "VF5", "VF5"),
            ("var_vf6_plus", "VF6", "VF6"),
            ("var_vf7_plus", "VF7", "VF7"),
            ("var_vf8_plus", "VF8", "VF8"),
            ("var_vf9_plus", "VF9", "VF9"),
        ]:
            dv_id = f"dv_{sr_code.lower()}_{var_code.lower()}"
            asset_code = f"AST-{sr_code}-{var_code}"
            vin = f"VIN{sr_code}DEMO{vehicle_idx:05d}"
            plate = f"{sr_code}-DEMO-{vehicle_idx:02d}"
            demo_vehicles.append(
                (dv_id, sr_id, var_id, asset_code, vin, plate, "available", 95.0, 15.0, "not_charging", 1, now_str, now_str)
            )
            vehicle_idx += 1
            
    cursor.executemany("""
        INSERT INTO demo_vehicles (id, showroom_id, variant_id, asset_code, vin, plate_number, operational_status, battery_soc, minimum_booking_soc, charging_status, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_vehicles)

    # 6. Seed test_drive_slots (next 7 days, 4 slots per day per demo vehicle)
    slots = []
    slot_idx = 1
    base_date = datetime.utcnow().date() + timedelta(days=1)  # start tomorrow
    
    for dv_id, sr_id, _, _, _, _, _, _, _, _, _, _, _ in demo_vehicles:
        for day_offset in range(7):
            date_str = (base_date + timedelta(days=day_offset)).isoformat()
            # 4 slots per day
            for start_time, end_time in [
                ("09:00:00", "10:00:00"),
                ("10:30:00", "11:30:00"),
                ("14:00:00", "15:00:00"),
                ("15:30:00", "16:30:00"),
            ]:
                slot_id = f"slot_{slot_idx}"
                start_at = f"{date_str}T{start_time}Z"
                end_at = f"{date_str}T{end_time}Z"
                slots.append(
                    (slot_id, sr_id, dv_id, start_at, end_at, "available", None, None, None, now_str, now_str)
                )
                slot_idx += 1
                
    cursor.executemany("""
        INSERT INTO test_drive_slots (id, showroom_id, demo_vehicle_id, start_at, end_at, status, held_until, current_booking_id, block_reason, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, slots)
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()
    print(f"Seeded developer database with {len(models)} models, {len(variants)} variants, {len(showrooms)} showrooms, {len(demo_vehicles)} vehicles, and {len(slots)} slots.")

if __name__ == "__main__":
    seed_db()
