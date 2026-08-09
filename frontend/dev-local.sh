#!/usr/bin/env bash
# Khởi động môi trường dev local cho P-053 (backend SQLite + frontend Vite).
# Không cần Docker. Dừng bằng Ctrl+C.
#
# Cách dùng:  bash frontend/dev-local.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
SHIM="${TMPDIR:-/tmp}/p053-media-shim"

# SQLite thay cho PostgreSQL: biến môi trường luôn thắng giá trị trong .env
export DATABASE_URL="sqlite:///./data/app.db"
export AUTO_LOAD_EVAL_DATA="false"
export MEDIA_ROOT="./data/media"

# ---- 1. Python venv ----
if [ -x "$BACKEND/.venv/bin/python" ]; then
  PY="$BACKEND/.venv/bin/python"
elif [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
else
  echo "==> Tạo backend/.venv (chỉ chạy lần đầu, mất vài phút)"
  python3 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/python" -m pip install --quiet --upgrade pip
  "$BACKEND/.venv/bin/python" -m pip install -r "$BACKEND/requirements.txt"
  PY="$BACKEND/.venv/bin/python"
fi
echo "==> Python: $PY"

mkdir -p "$BACKEND/data" "$BACKEND/logs"

# ---- 2. Seed dữ liệu showroom/xe/khung giờ (bỏ qua nếu DB đã có) ----
echo "==> Seed database"
(cd "$BACKEND" && "$PY" scripts/seed_dev_db.py)

# ---- 3. Copy ảnh xe sang media origin của backend ----
# TODO [BACKEND/MEDIA]: backend/scripts/publish_site_media.py còn trỏ tới layout cũ
# (frontend/"Ảnh xe vinfast" và frontend/src/assets). Media hiện nằm ở
# frontend/src/media/local/{vehicle-media,common}. Shim dưới đây chỉ là workaround
# tạm; backend nên cập nhật đường dẫn nguồn trong script.
if [ ! -f "$BACKEND/data/media/content/home/hero.webp" ]; then
  echo "==> Publish media"
  rm -rf "$SHIM"
  mkdir -p "$SHIM/src"
  ln -s "$FRONTEND/src/media/local/vehicle-media" "$SHIM/Ảnh xe vinfast"
  ln -s "$FRONTEND/src/media/local/common" "$SHIM/src/assets"
  (cd "$BACKEND" && "$PY" scripts/publish_site_media.py "$SHIM" data/media)
fi

# ---- 3b. Đẩy ảnh ghi đè theo mã xe (src/media/local/by-model/) sang kho media backend ----
# Chỉ ghi vào backend/data/media — dữ liệu sinh lúc chạy, đã nằm trong .gitignore.
echo "==> Áp dụng ảnh ghi đè theo mã xe"
(cd "$FRONTEND" && node scripts/apply-model-overrides.mjs)

# ---- 4. Chạy backend + frontend ----
echo "==> Backend  http://localhost:8000  (docs: /docs)"
(cd "$BACKEND" && exec "$PY" -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

cleanup() { echo; echo "==> Dừng backend"; kill "$BACKEND_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

sleep 3
echo "==> Frontend http://localhost:3000"
(cd "$FRONTEND" && npm run dev)
