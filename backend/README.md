# VinFast Test Drive Booking Backend

Backend cung cấp database SQLite, business services, các LangChain tools và FastAPI API cho hệ thống đặt lịch lái thử VinFast.

Agent chưa được kết nối vào booking flow chính. Giao diện demo gọi các Agent-facing tools hoặc UI-confirmed commands thông qua FastAPI để kiểm tra luồng nghiệp vụ thực tế.

## Cấu trúc thư mục

```text
backend/
├── logs/
│   └── backend.log
├── src/
│   ├── agents/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── nodes/
│   │   └── tools/
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── booking.py
│   │   └── llm.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── logging_config.py
│   └── main.py
├── Dockerfile
├── Makefile
└── requirements.txt
```

## Thành phần chính

### Database

`src/database.py` quản lý kết nối và khởi tạo SQLite schema.

Database lưu:

- Mẫu xe và phiên bản xe.
- Showroom và tọa độ địa lý.
- Xe demo vật lý.
- Slot lái thử.
- Booker và Driver.
- Booking và khai báo giấy phép.
- Notification plan và notification jobs.
- OTP challenge và booking access session.
- Audit events.
- Sales staff và phân công sales theo slot.
- Idempotency records cho các UI commands quan trọng.

Các write operation quan trọng sử dụng `BEGIN IMMEDIATE` để xử lý cạnh tranh trên SQLite.

### Booking Service

`src/services/booking.py` chứa business logic chính:

- Tìm mẫu xe, showroom và slot.
- Tính khoảng cách showroom bằng Haversine.
- Giữ slot trong 15 phút.
- Đọc và cập nhật booking draft.
- Xác nhận booking.
- Xác minh OTP và tạo access session.
- Tra cứu và chỉnh sửa booking.
- Dời hoặc hủy booking.
- Tạo notification jobs và audit events.
- Giải phóng hold hết hạn.
- Import mock dataset.
- Cung cấp dữ liệu dashboard.

Business rules, transaction và state transition nằm trong service; tool và API chỉ đóng vai trò adapter.

### Agent-facing tools

Các booking tools nằm trong:

```text
src/agents/tools/<tool_name>/
├── __init__.py
├── tool.py
└── TOOL.md
```

Sáu tools chính:

1. `search_test_drive_options`
2. `get_booking_draft`
3. `update_booking_draft`
4. `request_booking_access`
5. `verify_booking_access`
6. `get_booking_details`

Các tool sử dụng decorator `@tool` của LangChain và gọi trực tiếp `BookingService`.

Các thao tác giữ, xác nhận, dời và hủy booking không phải Agent tools. Chúng là UI-confirmed commands và được backend gọi trực tiếp sau khi người dùng bấm nút xác nhận.

### API

`src/api/routes.py` cung cấp các endpoint chính:

| Method | Endpoint | Chức năng |
|---|---|---|
| `POST` | `/api/v1/chat` | Entry point của LangGraph Agent mẫu |
| `GET` | `/api/v1/status` | Trạng thái Agent |
| `POST` | `/api/v1/demo/action` | Chạy tool hoặc UI command từ giao diện demo |
| `POST` | `/api/v1/admin/import/showrooms` | Import một file showroom CSV |
| `POST` | `/api/v1/admin/import/eval-dataset` | Import bộ mock CSV theo dependency order |
| `GET` | `/api/v1/dashboard` | Dữ liệu giám sát booking và slot |
| `GET` | `/health` | Health check |

Swagger UI được cung cấp tại `/docs`.

### Import dữ liệu

Importer đầy đủ nhận các file trong thư mục `eval/data` của repository root.

Request tới endpoint:

```text
POST /api/v1/admin/import/eval-dataset
```

Body có dạng:

```json
{
  "files": {
    "01_vehicle_models.csv": "id,code,name,...",
    "02_vehicle_variants.csv": "id,model_id,code,..."
  }
}
```

Importer:

- Kiểm tra tên file và CSV header.
- Kiểm tra foreign-key dependency.
- Import theo thứ tự an toàn.
- Upsert các record đã tồn tại.
- Rollback toàn bộ nếu một file không hợp lệ.

### Logging

Backend ghi log tại:

```text
logs/backend.log
```

`backend.log` chứa request, latency, lifecycle và lỗi backend. Lỗi frontend được xem trong Browser DevTools Console, không ghi thành file ở backend.

Log sử dụng rotating file:

- `backend.log`: tối đa 5 MB, giữ 5 bản.

Theo dõi log realtime trên PowerShell:

```powershell
Get-Content logs\backend.log -Wait
```

## Cấu hình

Backend đọc biến môi trường từ `.env` tại repository root hoặc trong `backend`.

Cấu hình quan trọng:

```env
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DATABASE_URL=sqlite:///./data/app.db
```

Phiên bản hiện tại chỉ hỗ trợ SQLite cho booking persistence.

## Chạy backend local

Yêu cầu:

- Python 3.11 trở lên.
- Conda hoặc Python virtual environment.

Từ repository root:

```powershell
cd backend
```

### Sử dụng Conda

```powershell
conda activate p053
pip install -r requirements-dev.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Sử dụng Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Sau khi backend chạy:

- Health check: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- Dashboard API: http://localhost:8000/api/v1/dashboard

## Chạy bằng Docker

Từ repository root:

```powershell
Copy-Item .env.example .env
```

Sau đó sửa dòng database trong `.env` thành SQLite:

```env
DATABASE_URL=sqlite:///./data/app.db
```

Khởi động service:

```powershell
docker compose up --build backend
```

Backend được mở tại:

```text
http://localhost:8000
```

Docker Compose mount:

```text
backend/data → /app/data
backend/logs → /app/logs
```

Vì vậy database và log được giữ lại khi container được tạo lại.

## Khởi động lại database development

Database mặc định nằm tại:

```text
backend/data/app.db
```

Nếu cần một database development mới, hãy dừng backend, sao lưu hoặc xóa file này rồi khởi động lại. Schema sẽ được tạo tự động khi application import `src.dependencies`.

Không xóa database khi backend đang chạy.
