# VinFast Test Drive Booking

Ứng dụng demo đặt lịch lái thử VinFast gồm:

- `backend`: FastAPI, LangGraph agent, booking service, PostgreSQL/SQLite adapter.
- `frontend`: Vite React UI cho trang sản phẩm, tư vấn và đặt lịch.
- `internal-portal/frontend`: React UI riêng cho Staff, Showroom Manager và Operations Admin.
- `backend/src/internal_portal`: authentication, RBAC, showroom scope và Internal API dùng chung booking service.
- `admin`: Streamlit dashboard/import data.
- `eval/data`: bộ CSV seed dữ liệu booking/catalog.

## Chạy Bằng Docker

Từ thư mục root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Các service chính:

- Frontend: <http://localhost:3000>
- Internal Portal: <http://localhost:3100>
- Backend API: <http://localhost:8001>
- Swagger: <http://localhost:8001/docs>
- Legacy Streamlit admin (profile `legacy-admin`): <http://localhost:8501>
- PostgreSQL: `localhost:5432`

Docker Compose mặc định publish backend ở cổng host `8001` để tránh xung đột với
các ứng dụng thường dùng cổng `8000`. Có thể đổi bằng `BACKEND_HOST_PORT` trong
file `.env`; backend bên trong Docker network vẫn lắng nghe ở cổng `8000`.

## Setup Data

Mặc định Docker mount folder local:

```text
eval/data -> /app/eval/data
```

Importer tự nhận diện một trong hai định dạng:

- Legacy: các file `01_vehicle_models.csv` đến `15_booking_events.csv` nằm trực tiếp trong `eval/data`.
- V5: package đầy đủ nằm trong `eval/data`, với 32 file CSV trong thư mục `eval/data/seed`.

Khi database rỗng, backend sẽ import toàn bộ các file theo thứ tự dependency. Bộ legacy gồm:

```text
01_vehicle_models.csv
02_vehicle_variants.csv
03_showrooms.csv
04_sales_staff.csv
05_demo_vehicles.csv
06_test_drive_slots.csv
07_slot_sales_assignments.csv
08_people.csv
09_bookings.csv
10_booking_driver_details.csv
11_notification_plans.csv
12_notification_jobs.csv
13_otp_challenges.csv
14_booking_access_sessions.csv
15_booking_events.csv
```

Bộ V5 bắt đầu bằng `seed/01_provinces.csv`, kết thúc bằng
`seed/32_internal_audit_events.csv`, và bao gồm geography, showroom metadata,
RBAC/Internal Portal, vận hành xe/nhân viên, booking, OTP, notification và audit.

Các file data gốc được lưu tại Google Drive:

<REMOVED-PRIVATE-LINK>

Tải các file CSV từ Drive về `eval/data`, sau đó chạy:

```powershell
docker compose down -v
docker compose up --build
```

Khi import thành công, log `db-seed` sẽ có dạng:

```text
Imported full eval dataset from /app/eval/data: ...
```

## Reset Và Re-Import

`docker compose down` chỉ tắt/xóa container, không xóa database volume. Booking đã tạo vẫn còn.

```powershell
docker compose down
docker compose up
```

`docker compose down -v` xóa cả PostgreSQL volume `postgres-data`. Lần `up` sau database rỗng và hệ thống import lại từ `eval/data`.

```powershell
docker compose down -v
docker compose up --build
```

Nếu đã sửa code seed/import, luôn dùng `--build`; nếu không Docker có thể chạy image cũ.

## Backup PostgreSQL

Backup trước khi xóa volume:

```powershell
New-Item -ItemType Directory -Force backups
docker compose exec postgres pg_dump -U vinfast -d vinfast_booking -Fc -f /tmp/vinfast_booking.dump
docker compose cp postgres:/tmp/vinfast_booking.dump ./backups/vinfast_booking.dump
```

Restore:

```powershell
docker compose cp ./backups/vinfast_booking.dump postgres:/tmp/vinfast_booking.dump
docker compose exec postgres pg_restore -U vinfast -d vinfast_booking --clean --if-exists /tmp/vinfast_booking.dump
```

## Chạy Local Không Docker

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Nếu chạy SQLite local, cấu hình:

```env
DATABASE_URL=sqlite:///./data/app.db
AUTO_LOAD_EVAL_DATA=true
EVAL_DATA_DIR=../eval/data
```

Xóa `backend/data/app.db` nếu muốn import lại từ đầu.

## Biến Môi Trường Quan Trọng

```env
DATABASE_URL=postgresql://vinfast:vinfast@postgres:5432/vinfast_booking
AUTO_LOAD_EVAL_DATA=true
EVAL_DATA_DIR=/app/eval/data
OPENAI_API_KEY=
OPENROUTER_API_KEY=
MODEL_NAME=gpt-4o-mini
CLASSIFIER_MODEL_NAME=
MEDIA_ROOT=./data/media
MEDIA_BASE_URL=/media
CHROMA_PERSIST_DIR=./data/chroma
```

## Kiểm Tra

Backend tests:

```powershell
python -m pytest backend/tests -q
```

Frontend build:

```powershell
cd frontend
npm run build
```

## Ghi Chú Về Khoảng Cách

Nếu frontend dùng GPS, backend tính khoảng cách bằng Haversine từ tọa độ người dùng tới tọa độ showroom.

Nếu người dùng chỉ nhập địa chỉ dạng text, backend match token địa danh trong địa chỉ showroom. Khi tìm thấy showroom khớp địa danh, backend dùng tọa độ showroom khớp tốt nhất làm origin tạm để sắp xếp và trả `distance_km`. Frontend chỉ hiển thị khoảng cách khi backend trả `distance_km`; không tự ép giá trị thiếu thành `0 km`.
