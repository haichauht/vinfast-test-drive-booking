# VinFast Test Drive Booking

> Dự án nhóm thực hiện trong chương trình AI20K Build Phase (Cohort 3). Đây là dự án học tập,
> không phải sản phẩm chính thức của VinFast.
>
> Bản public này giữ lại code, test và kết quả đánh giá; đã lược bỏ ảnh, video, brochure, dữ liệu
> nguồn và ghi chú nội bộ. Khi chạy local, đặt `VITE_MEDIA_BASE_URL` để frontend lấy ảnh từ CDN.
> Các địa chỉ triển khai bên dưới thuộc giai đoạn thực hiện dự án và có thể không còn hoạt động.

MVP công khai cho phép người dùng xem catalogue VinFast, trò chuyện với ViVi, tìm showroom, tạo lịch lái thử và tra cứu/sửa/hủy lịch bằng luồng OTP demo.

## Thành phần ứng dụng

- `backend`: FastAPI, LangGraph agent, booking service, PostgreSQL/SQLite adapter.
- `frontend`: Vite React UI cho trang sản phẩm, tư vấn và đặt lịch.
- `internal-portal/frontend`: React UI riêng cho Staff, Showroom Manager và Operations Admin.
- `human-review/frontend`: ứng dụng độc lập để reviewer chấm benchmark, dùng tài khoản và API riêng.
- `backend/src/internal_portal`: authentication, RBAC, showroom scope và Internal API dùng chung booking service.
- `admin`: Streamlit dashboard/import data cũ, chỉ chạy qua Docker profile tùy chọn.
- `eval/data`: bộ CSV seed dữ liệu booking/catalog.
- `eval/golden`: bộ case đánh giá agent và bảo mật được version-control, không import vào DB.

## Môi trường đang triển khai

| Thành phần | Dịch vụ | Địa chỉ |
| --- | --- | --- |
| Frontend production | Cloudflare Pages | <https://c3-app-053.pages.dev> |
| Backend API | Render Web Service, chạy Docker image | <https://vinfastbooking-api-latest.onrender.com> |
| API health | FastAPI | <https://vinfastbooking-api-latest.onrender.com/health> |
| PostgreSQL production | Neon | Cấu hình bằng `DATABASE_URL` trên Render |
| Ảnh, video, brochure | Cloudflare R2 | <https://pub-216eea433b9e4529979ce534d5ce0ae1.r2.dev> |
| Docker registry | Docker Hub | `nguyen1oc/vinfastbooking-api` |

Kiến trúc production:

```text
Người dùng
    |
    v
Cloudflare Pages (React/Vite)
    | API                              | media
    v                                  v
Render (FastAPI/LangGraph)       Cloudflare R2
    |
    v
Neon PostgreSQL
```

Neon là PostgreSQL được quản lý trên Internet. Docker image backend chỉ chứa code và dependency; dữ liệu thay đổi theo thời gian không được đóng vào image.

## Tech stack

| Lớp | Công nghệ |
| --- | --- |
| Frontend | React 18, Vite 5, React Router, GSAP, Three.js, Model Viewer, Mapbox GL |
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic |
| AI agent | LangGraph, LangChain, OpenAI/OpenRouter-compatible models |
| Database | PostgreSQL, Psycopg 3, LangGraph PostgreSQL checkpointer |
| Media | Cloudflare R2 public object storage; file local chỉ dùng cho phát triển/fallback |
| Container | Docker multi-stage image, Docker Hub |
| Hosting | Cloudflare Pages cho frontend; Render cho backend; Neon cho PostgreSQL |
| CI/CD | GitHub Actions trên self-hosted runner, Ruff, Mypy, Bandit, Pytest, Vite build, Docker Buildx, Wrangler |

## Cấu trúc repository

```text
backend/        FastAPI, agent, booking service, database adapter, seed scripts
frontend/       React/Vite UI và công cụ upload media R2
human-review/   Human Review Portal độc lập và hướng dẫn cấp tài khoản reviewer
eval/data/      Bộ CSV nguồn cho lần khởi tạo database
.github/        Frontend và backend CI/CD workflows
```

Route public cũ `/api/v1/dashboard` đã được gỡ. Các route `/api/v1/admin/import/*` chỉ chấp nhận tài khoản Internal Portal có quyền Operations Admin; request ẩn danh không thể import dữ liệu. Streamlit admin chỉ còn là Docker profile tùy chọn và không được chạy trên production.

## Chạy local bằng Docker

Từ thư mục root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Với `AUTO_LOAD_EVAL_DATA=true`, lần backend đầu tiên khởi động trên database rỗng sẽ tự import dataset. Nếu muốn tách rõ bước seed và tránh backend giữ startup trong lúc import, dùng trình tự sau:

```powershell
docker compose build backend frontend
docker compose up -d postgres
docker compose --profile seed run --rm -e AUTO_LOAD_EVAL_DATA=true db-seed
docker compose up -d backend frontend
```

Các service mặc định:

- Frontend: <http://localhost:3000>
- Internal Portal: <http://localhost:3100>
- Human Review Portal: <http://localhost:3300>
- Human Review API độc lập: <http://localhost:8300>
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
- **V5/V5.2:** 32 file nằm trong `eval/data/seed`, bắt đầu bằng
  `01_provinces.csv` và kết thúc bằng `32_internal_audit_events.csv`. Bộ này có
  thêm geography, RBAC/Internal Portal, ca làm, thời gian không khả dụng, fleet,
  điều chuyển xe và audit.

Repository hiện có business snapshot V5.2 trong `eval/data/seed`. Baseline được
xuất từ PostgreSQL sau khi gộp 10 showroom trùng, gồm 319 showroom, 900 staff,
319 manager, một operations admin, 1.356 xe demo, 576.300 slot và 9.369 booking.
Lịch seed kéo dài đến 31/10/2026; cửa sổ đặt lịch mặc định là 30 ngày và có thể
cấu hình. Số liệu chi tiết nằm trong `eval/data/DATASET_OVERVIEW.md` và
`eval/data/VALIDATION_REPORT.json`. Dữ liệu nguồn đầy đủ không có trong repo công khai này.

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

Snapshot không chứa session portal đang hoạt động, LangGraph checkpoints, trạng
thái đã đọc của thông báo web hoặc Zalo polling offsets. Các phần này được tạo
lại khi ứng dụng chạy.

## Xuất Snapshot Từ PostgreSQL

PostgreSQL đang chạy là nguồn dữ liệu gốc. Sau khi chỉnh dữ liệu trực tiếp trong
DB, xuất lại business snapshot vào `eval/data` bằng đúng container backend để
tránh kết nối nhầm một PostgreSQL local khác:

```powershell
docker compose run --rm --no-deps `
  -v "${PWD}/backend/scripts:/app/scripts:ro" `
  -v "${PWD}/eval/data:/app/export" `
  backend python scripts/export_postgres_baseline.py --output-dir /app/export
```

Exporter ghi lại 32 file seed, metadata, validation report, manifest và checksum.
Lệnh trả về lỗi nếu DB không còn đúng baseline 319 showroom, 900 staff, 319
manager và một operations admin. Nên tạo `pg_dump` trước khi chạy migration hoặc
thay đổi dữ liệu hàng loạt.

Để nạp danh mục hành chính chính thức và sinh dữ liệu vận hành từ slot hiện có,
chạy dry-run trước rồi mới thêm `--apply`:

```powershell
docker compose run --rm --no-deps `
  -v "${PWD}/backend/scripts:/app/scripts:ro" `
  -v "${PWD}/backend/reference:/app/reference:ro" `
  backend python scripts/enrich_postgres_reference_data.py

docker compose run --rm --no-deps `
  -v "${PWD}/backend/scripts:/app/scripts:ro" `
  -v "${PWD}/backend/reference:/app/reference:ro" `
  backend python scripts/enrich_postgres_reference_data.py --apply
```

Script bắt buộc map duy nhất đủ 319 showroom và rollback nếu số lượng địa giới,
metadata, giờ demo, ca staff hoặc khoảng xe không khả dụng không khớp.

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

Frontend, ở terminal khác:

```powershell
cd frontend
npm install
npm run dev
```

Vite proxy `/api` và `/media` sang `http://127.0.0.1:8000` khi chạy local.

## Khởi tạo dữ liệu Neon

Full seed chỉ dùng để khởi tạo một database Neon trống. Dataset hiện có 159.127 dòng và được import trong một transaction; vì vậy thao tác có thể mất nhiều thời gian, còn dữ liệu chỉ xuất hiện sau khi transaction commit.

### Chuẩn bị

1. Trong Neon, mở **Connect** và copy PostgreSQL connection string.
2. Không ghi connection string thật vào source, README hoặc Git.
3. Đảm bảo `eval/data` chứa đủ các CSV từ `01_vehicle_models.csv` đến `15_booking_events.csv`.
4. Cài đủ `backend/requirements.txt`, bao gồm `psycopg`.

### Seed từ WSL/Linux

Chạy từ `backend/`:

```bash
conda activate vinai_env
python -m pip install -r requirements.txt

export DATABASE_URL='postgresql://USER:PASSWORD@HOST/neondb?sslmode=require'
export APP_ENV='development'
export AUTO_LOAD_EVAL_DATA='true'
export EVAL_DATA_DIR='../eval/data'

python scripts/seed_dev_db.py

unset DATABASE_URL APP_ENV AUTO_LOAD_EVAL_DATA EVAL_DATA_DIR
```

Thành công khi terminal kết thúc bằng:

```text
Imported full eval dataset from ../eval/data: ... 'total_rows': 159127 ...
```

### Seed từ PowerShell

```powershell
cd backend
$env:DATABASE_URL = "postgresql://USER:PASSWORD@HOST/neondb?sslmode=require"
$env:APP_ENV = "development"
$env:AUTO_LOAD_EVAL_DATA = "true"
$env:EVAL_DATA_DIR = "../eval/data"

python scripts/seed_dev_db.py

Remove-Item Env:DATABASE_URL
Remove-Item Env:APP_ENV
Remove-Item Env:AUTO_LOAD_EVAL_DATA
Remove-Item Env:EVAL_DATA_DIR
```

Script tự bỏ qua nếu database đã có booking data. Không đặt `RESET_DEV_DB=1` trên production: tùy chọn đó xóa fixture hiện có trước khi import lại và có thể làm mất booking của người dùng.

Kiểm tra nhanh trong Neon SQL Editor:

```sql
SELECT
  (SELECT count(*) FROM vehicle_models) AS vehicle_models,
  (SELECT count(*) FROM showrooms) AS showrooms,
  (SELECT count(*) FROM test_drive_slots) AS slots,
  (SELECT count(*) FROM bookings) AS bookings;
```

Kết quả của dataset hiện tại là `6`, `329`, `47460`, `9361`.

## Cập nhật dữ liệu sau lần seed đầu

Không chạy full seed mỗi lần deploy.

- Booking, OTP, access session và trạng thái slot được backend ghi trực tiếp vào Neon khi người dùng thao tác.
- Thay đổi frontend, backend hoặc ảnh R2 không yêu cầu seed lại Neon.
- Thêm showroom, xe hoặc slot nên dùng script/import tăng dần cho đúng bảng, sau khi backup hoặc thử trên Neon branch.
- Thay đổi cấu trúc bảng cần một migration SQL có version; không xóa và tạo lại database production.
- Không dùng dataset fixture để ghi đè một database đã nhận booking thật.

Render production phải giữ:

```env
APP_ENV=production
AUTO_LOAD_EVAL_DATA=false
DATABASE_URL=<Neon PostgreSQL connection string>
```

Backend vẫn tự tạo các bảng còn thiếu khi khởi động, nhưng không tự import 159.127 dòng khi `AUTO_LOAD_EVAL_DATA=false`.

## Cấu hình production

### Render backend

Các biến tối thiểu:

```env
APP_ENV=production
DATABASE_URL=<Neon connection string>
AUTO_LOAD_EVAL_DATA=false
BOOKING_ACCESS_OTP_SECRET=<random secret tối thiểu 32 ký tự>
CORS_ORIGINS=https://c3-app-053.pages.dev,https://vinfast-booking.vercel.app
MEDIA_BASE_URL=https://pub-216eea433b9e4529979ce534d5ce0ae1.r2.dev
OPENAI_API_KEY=<server-side secret nếu dùng OpenAI>
OPENROUTER_API_KEY=<server-side secret nếu dùng OpenRouter>
MODEL_NAME=<model đang dùng>
CLASSIFIER_MODEL_NAME=<classifier model nếu có>
ZALO_BOT_ENABLED=false
ZALO_BOT_POLLING_ENABLED=false
```

Không thêm dấu ngoặc kép, khoảng trắng hoặc dấu `/` cuối các origin trong `CORS_ORIGINS`. Health check path của Render là `/health`.

### Cloudflare Pages frontend

Vite nhúng hai URL public trong lúc build:

```env
VITE_API_BASE_URL=https://vinfastbooking-api-latest.onrender.com/api/v1
VITE_MEDIA_BASE_URL=https://pub-216eea433b9e4529979ce534d5ce0ae1.r2.dev
```

Đây là URL public, không phải secret. API key, database password và OTP secret tuyệt đối không dùng prefix `VITE_`.

GitHub Actions cần:

```text
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
RENDER_DEPLOY_HOOK_URL
```

Push/merge vào `main` mới deploy production. Frontend được build một lần rồi artifact `dist` được Wrangler deploy lên Pages. Backend chạy test, build/push Docker image rồi gọi Render Deploy Hook.

## Cập nhật media R2

Tạo lại thư mục media chuẩn từ kho frontend, sau đó upload object lên R2:

```powershell
cd backend
python scripts/publish_site_media.py

cd ../frontend
npx wrangler whoami
npm run media:upload:r2
```

Nếu ghi đè đúng object key cũ, frontend nhận file mới mà không cần sửa Neon. Nếu đổi đường dẫn hoặc tên object, phải cập nhật media map/catalogue trong source và deploy lại frontend hoặc backend tương ứng.

## Kiểm tra

Backend:

```powershell
ruff check backend/src/ backend/tests/
mypy --ignore-missing-imports backend/src/
pytest backend/tests/ -q
```

Frontend:

```powershell
cd frontend
npm run build
```

Kiểm tra production:

```powershell
Invoke-RestMethod https://vinfastbooking-api-latest.onrender.com/health
Invoke-RestMethod https://vinfastbooking-api-latest.onrender.com/api/v1/booking/health
```

## An toàn dữ liệu

- Không commit `.env`, Neon connection string, API key hoặc access token.
- Nếu secret từng được gửi công khai, hãy rotate và cập nhật lại Render/GitHub Secrets.
- Tạo Neon branch hoặc backup trước khi import/migration số lượng lớn.
- Giữ `AUTO_LOAD_EVAL_DATA=false` trên production.
- R2 public URL phù hợp cho MVP public media; nội dung riêng tư không được đặt trong bucket public.
