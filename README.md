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

## Cấu Hình Local Để Test

Các tùy chọn dưới đây chỉ phù hợp cho máy local. Không dùng cấu hình này trong
production:

```env
APP_ENV=development

# Cho phép API trả OTP khi provider đang dùng là provider mock.
# Production luôn ẩn OTP dù biến này vô tình được bật.
BOOKING_ACCESS_EXPOSE_MOCK_OTP=true
GMAIL_ENABLED=false
BOOKING_ACCESS_OTP_TTL_SECONDS=300
BOOKING_ACCESS_OTP_MAX_ATTEMPTS=10

# Tắt rate limit của các public endpoint như chat và demo/action.
RATE_LIMIT_ENABLED=false

# OTP còn có bộ đếm riêng trong BookingService. Tăng các ngưỡng này và giảm
# resend cooldown khi cần lặp lại luồng OTP nhiều lần trong local.
RATE_LIMIT_OTP_REQUEST_PER_CONTACT_PER_HOUR=1000
RATE_LIMIT_OTP_VERIFY_PER_CHALLENGE_PER_MINUTE=1000
BOOKING_ACCESS_OTP_RESEND_COOLDOWN_SECONDS=1

# Tắt budget tiền LLM để phiên test dài không bị chặn.
LLM_DAILY_BUDGET_ENABLED=false

# Worker kiểm tra notification đến hạn mỗi 5 giây (giá trị nhỏ nhất hợp lệ).
NOTIFICATION_POLL_INTERVAL_SECONDS=5
```

Để quay về hành vi gần production:

```env
BOOKING_ACCESS_EXPOSE_MOCK_OTP=false
RATE_LIMIT_ENABLED=true
BOOKING_ACCESS_OTP_RESEND_COOLDOWN_SECONDS=60
NOTIFICATION_POLL_INTERVAL_SECONDS=60
```

Sau khi sửa `.env`, recreate backend để container nhận lại biến môi trường:

```powershell
docker compose up -d --force-recreate backend
```

`docker compose restart backend` không đảm bảo nạp lại giá trị mới từ `.env`.
`RATE_LIMIT_ENABLED=false` chỉ tắt middleware của public API; hai giới hạn OTP
vẫn hoạt động độc lập qua `RATE_LIMIT_OTP_REQUEST_PER_CONTACT_PER_HOUR` và
`RATE_LIMIT_OTP_VERIFY_PER_CHALLENGE_PER_MINUTE`.

### Test sửa, đổi và hủy lịch

Profile local ở trên phù hợp để kiểm tra liên tục các nghiệp vụ quản lý booking:

1. Tạo và xác nhận một booking có thời gian lái thử trong tương lai.
2. Để sửa hoặc đổi lịch, chọn tra cứu lịch đã đặt và nhập email của booking.
3. Dùng OTP mock hiển thị trong chat để xác thực, rồi chọn booking cần thao tác.
4. Để test hủy, bắt đầu một luồng riêng bằng yêu cầu hủy lịch với ViVi và xác
   thực OTP cho purpose `cancel`; không dùng lại token của luồng đổi lịch.

Booking phải ở trạng thái `confirmed` để đổi hoặc hủy. Đổi lịch cần một slot
mới còn trống và phải xác nhận trước khi thời gian giữ slot mới kết thúc. Quyền
được cấp theo purpose OTP: `reschedule` cho phép đọc, sửa và đổi lịch;
`cancel` cho phép đọc và hủy. Token có thể áp dụng cho các booking thuộc cùng
chủ sở hữu, nhưng không tự có thêm quyền ngoài purpose đã xác thực.

### Profile test rate limit

Để quan sát lỗi rate limit nhanh, bật middleware và hạ giới hạn theo session.
Giữ giới hạn IP cao để các tab/máy khác trong cùng mạng không ảnh hưởng bài test:

```env
APP_ENV=development
RATE_LIMIT_ENABLED=true

RATE_LIMIT_CHAT_PER_SESSION_PER_MINUTE=2
RATE_LIMIT_CHAT_PER_SESSION_PER_HOUR=3
RATE_LIMIT_CHAT_PER_IP_PER_MINUTE=1000
RATE_LIMIT_CHAT_PER_IP_PER_HOUR=1000

RATE_LIMIT_DEMO_ACTION_PER_SESSION_PER_MINUTE=2
RATE_LIMIT_DEMO_ACTION_PER_SESSION_PER_HOUR=3
RATE_LIMIT_DEMO_ACTION_PER_IP_PER_MINUTE=1000
RATE_LIMIT_DEMO_ACTION_PER_IP_PER_HOUR=1000

RATE_LIMIT_OTP_REQUEST_PER_CONTACT_PER_HOUR=2
RATE_LIMIT_OTP_VERIFY_PER_CHALLENGE_PER_MINUTE=2
BOOKING_ACCESS_OTP_RESEND_COOLDOWN_SECONDS=1
```

Các kịch bản kiểm tra nhanh:

- Gửi 3 chat request liên tiếp; request thứ ba phải bị giới hạn theo session.
- Thực hiện 3 thao tác qua `/api/v1/demo/action`; thao tác thứ ba phải bị giới hạn.
- Xin OTP 3 lần cho cùng email; lần thứ ba phải bị chặn bởi bộ đếm OTP.
- Nhập sai OTP liên tiếp để kiểm tra cả rate limit và `BOOKING_ACCESS_OTP_MAX_ATTEMPTS`.

Counter được lưu trong PostgreSQL. Chỉ trên database local, reset counter giữa
các test bằng:

```powershell
docker compose exec postgres psql -U vinfast -d vinfast_booking -c "DELETE FROM rate_limit_counters;"
```

Sau khi test xong, quay lại profile local không giới hạn bằng
`RATE_LIMIT_ENABLED=false`, đặt hai ngưỡng OTP thành `1000`, rồi recreate backend.

### Bật Gmail thật

Nếu cần kiểm tra email thực sự đi tới inbox, cấu hình OAuth Gmail trong `.env`:

```env
GMAIL_ENABLED=true
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_SENDER_EMAIL=
GMAIL_SENDER_NAME=VinFast
GMAIL_TIMEOUT_SECONDS=15
NOTIFICATION_POLL_INTERVAL_SECONDS=5
NOTIFICATION_BATCH_SIZE=100
NOTIFICATION_PROCESSING_TIMEOUT_SECONDS=30

# Gmail thật không phải provider mock nên OTP không được trả về UI.
BOOKING_ACCESS_EXPOSE_MOCK_OTP=false
```

Khi `GMAIL_ENABLED=false`, hệ thống dùng provider in-memory và không gửi email
ra ngoài. Ở trạng thái code hiện tại, provider mock trả `provider_status=mocked`
nhưng dispatcher chỉ coi `provider_status=sent` là thành công; do đó job mock có
thể bị ghi `failed`. Dùng Gmail thật để test end-to-end cho tới khi contract này
được thống nhất.

## Test Notification Không Cần Chờ

Khi xác nhận booking, job `booking_confirmation` được đặt lịch ngay lập tức.
Với `NOTIFICATION_POLL_INTERVAL_SECONDS=5`, worker sẽ nhận job trong tối đa
khoảng 5 giây. Có thể gọi dispatcher thủ công để không phải chờ worker:

```powershell
docker compose exec backend python -c "from src.dependencies import booking_service; print(booking_service.dispatch_due_notifications())"
```

Reminder 24 giờ và 2 giờ được lưu thành các job `reminder_24h` và
`reminder_2h`. Để test nhanh một booking đã xác nhận, chỉ đưa các job reminder
của booking đó về thời điểm hiện tại trong database local:

```powershell
docker compose exec postgres psql -U vinfast -d vinfast_booking -c "UPDATE notification_jobs SET scheduled_at=NOW(), status='pending', attempt_count=0, last_attempt_at=NULL, sent_at=NULL, error_message=NULL WHERE booking_id='BOOKING_ID' AND notification_type IN ('reminder_24h','reminder_2h');"

docker compose exec backend python -c "from src.dependencies import booking_service; print(booking_service.dispatch_due_notifications())"
```

Thay `BOOKING_ID` bằng ID thật. Cách này chỉ thay thời điểm chạy job local, không
thay đổi thời gian lái thử. Kiểm tra kết quả:

```powershell
docker compose exec postgres psql -U vinfast -d vinfast_booking -c "SELECT id,notification_type,channel,scheduled_at,status,attempt_count,provider_name,provider_status,error_message FROM notification_jobs WHERE booking_id='BOOKING_ID' ORDER BY scheduled_at;"
```

Hệ thống cũng hỗ trợ `custom_plan_json` dạng
`{"reminder_offsets_minutes":[5,2]}` trước lúc xác nhận booking. Các số này là
số phút **trước giờ lái thử**, không phải số phút kể từ hiện tại. Để smoke test
ngay một booking bất kỳ, cập nhật `notification_jobs.scheduled_at` như trên dễ
kiểm soát hơn.

## Setup Data

Web khách và Internal Portal dùng chung một backend và một PostgreSQL database
`vinfast_booking`. Booking tạo từ web khách sẽ xuất hiện trong portal; thay đổi
từ portal cũng được đọc từ cùng nguồn dữ liệu.

Docker mount thư mục dữ liệu ở chế độ read-only:

```text
eval/data -> /app/eval/data
```

Trong `.env`, giữ các giá trị sau khi chạy bằng Docker Compose:

```env
AUTO_LOAD_EVAL_DATA=true
EVAL_DATA_DIR=/app/eval/data
```

`DATABASE_URL` của container backend được Docker Compose đặt thành
`postgresql://vinfast:vinfast@postgres:5432/vinfast_booking`; giá trị
`DATABASE_URL` dành cho host trong `.env` không ghi đè cấu hình này.

### Chọn dataset

Importer tự nhận diện một trong hai định dạng và không cho trộn legacy với V5
trong cùng một lần import:

- **Legacy:** 15 file từ `01_vehicle_models.csv` đến
  `15_booking_events.csv` nằm trực tiếp trong `eval/data`. Bộ này đủ cho luồng
  booking cơ bản: mẫu xe, showroom, nhân viên, xe demo, slot, khách hàng,
  booking, notification và OTP.
- **V5:** 32 file nằm trong `eval/data/seed`, bắt đầu bằng
  `01_provinces.csv` và kết thúc bằng `32_internal_audit_events.csv`. Bộ này có
  thêm geography, RBAC/Internal Portal, ca làm, thời gian không khả dụng, fleet,
  điều chuyển xe và audit.

Repository hiện có bộ legacy trong `eval/data`. Dữ liệu nguồn đầy đủ được lưu tại:

<REMOVED-PRIVATE-LINK>

### Import lần đầu

Nếu chưa có `.env`, tạo từ file mẫu rồi đặt dataset vào đúng vị trí:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose logs -f backend
```

Khi backend khởi động, nó thực hiện theo thứ tự:

1. Tạo hoặc migrate toàn bộ schema PostgreSQL.
2. Kiểm tra các bảng dữ liệu booking chính.
3. Nếu dataset đang rỗng và `AUTO_LOAD_EVAL_DATA=true`, import CSV từ
   `EVAL_DATA_DIR` trong một transaction.
4. Nếu database đã có dữ liệu booking, bỏ qua auto-import để không ghi đè dữ
   liệu đang sử dụng.

Log thành công có nội dung tương tự:

```text
Auto-loaded eval dataset from /app/eval/data: ...
```

Xác minh dữ liệu sau import:

```powershell
docker compose exec postgres psql -U vinfast -d vinfast_booking -c "SELECT 'showrooms' AS table_name,count(*) FROM showrooms UNION ALL SELECT 'sales_staff',count(*) FROM sales_staff UNION ALL SELECT 'vehicles',count(*) FROM demo_vehicles UNION ALL SELECT 'slots',count(*) FROM test_drive_slots UNION ALL SELECT 'bookings',count(*) FROM bookings;"
```

### Tài khoản Internal Portal

`showrooms` và `sales_staff` là dữ liệu nghiệp vụ, không phải tài khoản đăng
nhập. Bộ legacy không tạo tài khoản Admin, Manager hoặc Staff mặc định. Tạo
Operations Admin đầu tiên bằng CLI; lệnh sẽ yêu cầu nhập mật khẩu hai lần:

```powershell
docker compose exec backend python scripts/manage_internal_user.py `
  --username ops.admin `
  --display-name "Operations Admin" `
  --role operations_admin
```

Sau đó đăng nhập tại <http://localhost:3100> và tạo Manager/Staff trong mục tài
khoản. Nếu cần tạo bằng CLI, lấy ID hợp lệ trước:

```powershell
docker compose exec postgres psql -U vinfast -d vinfast_booking -c "SELECT id,code,name FROM showrooms WHERE is_active=1 ORDER BY name;"
docker compose exec postgres psql -U vinfast -d vinfast_booking -c "SELECT id,showroom_id,employee_code,full_name FROM sales_staff WHERE status='active' ORDER BY showroom_id,full_name LIMIT 30;"
```

Manager phải gắn đúng một `--showroom-id`; Staff phải gắn một `--staff-id` đang
active. Showroom của Staff được suy ra từ hồ sơ `sales_staff`.

## Reset Và Re-Import

`docker compose down` chỉ tắt/xóa container, không xóa volume PostgreSQL. Các
booking và tài khoản portal đã tạo vẫn còn:

```powershell
docker compose down
docker compose up
```

`docker compose down -v` xóa volume `postgres-data`, bao gồm toàn bộ booking,
notification, rate-limit counter và tài khoản portal local. Chỉ dùng khi chắc
chắn muốn import lại từ đầu:

```powershell
docker compose down -v
docker compose up --build
```

Nếu đã sửa code seed/import, luôn dùng `--build`; nếu không Docker có thể chạy image cũ.

Nếu chỉ thay file CSV nhưng giữ volume cũ, backend sẽ thấy database đã có dữ
liệu và bỏ qua auto-import. Hãy backup trước khi reset nếu cần giữ booking hoặc
tài khoản đã tạo.

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
