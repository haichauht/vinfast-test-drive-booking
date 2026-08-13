# VinFast Test Drive Booking

MVP công khai cho phép người dùng xem catalogue VinFast, trò chuyện với ViVi, tìm showroom, tạo lịch lái thử và tra cứu/sửa/hủy lịch bằng luồng OTP demo.

## Môi trường đang triển khai

| Thành phần | Dịch vụ | Địa chỉ |
| --- | --- | --- |
| Frontend production | Cloudflare Pages | <https://vinfast-mvp.pages.dev> |
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
eval/data/      Bộ CSV nguồn cho lần khởi tạo database
change_logs/    Nhật ký thay đổi theo ngày
.github/        Frontend và backend CI/CD workflows
```

Các route public `/api/v1/dashboard` và `/api/v1/admin/import/*` đã được gỡ. Streamlit admin chỉ còn là Docker profile tùy chọn và không được chạy trên production.

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
- Backend: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- PostgreSQL: `localhost:5432`

Service Streamlit admin nằm trong profile `admin`, không tự chạy cùng `docker compose up`.

`docker compose down` giữ nguyên volume PostgreSQL. `docker compose down -v` xóa toàn bộ database local và chỉ nên dùng khi chủ động muốn tạo lại dữ liệu phát triển.

## Chạy local không dùng Docker

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
CORS_ORIGINS=https://vinfast-mvp.pages.dev,https://vinfast-booking.vercel.app
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
