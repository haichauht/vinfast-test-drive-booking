# P-053 Human Review Portal

Ứng dụng độc lập dành riêng cho reviewer đánh giá benchmark. Portal không dùng tài khoản,
menu hoặc quyền của Internal Portal và không có API truy cập booking/hồ sơ khách hàng.

## Tạo tài khoản reviewer

Từ repository root:

```powershell
.\.venv\Scripts\python.exe backend\scripts\manage_human_reviewer.py `
  --username reviewer.one `
  --display-name "Reviewer One"
```

Tài khoản và khóa ký phiên được lưu cục bộ tại `eval/human/reviewers.json`, được Git ignore.
Mỗi reviewer phải dùng tài khoản riêng để đo agreement chính xác.

## Chạy local

```powershell
# Terminal 1, từ repository root
.\.venv\Scripts\python.exe -m uvicorn src.evaluation.human_review_app:app `
  --app-dir backend --reload --port 8300

# Terminal 2
cd human-review\frontend
npm install
npm run dev
```

Mở <http://localhost:3300>. Kết quả hoàn chỉnh được ghi vào
`eval/human/reviews.csv`; bản nháp chưa hoàn chỉnh chỉ nằm trên trình duyệt reviewer.

## Docker

```powershell
docker compose up --build human-review-api human-review
```

- Trên chính máy chạy Docker: <http://localhost:3300>.
- Đồng đội trong cùng mạng LAN/Wi-Fi: <http://DESKTOP-KELIBTC:3300>.
- API nội bộ ở cổng `8300`; kết quả chấm được ghi vào `eval/human/reviews.csv`.

Đây là một Human Review Portal duy nhất. Portal không khởi tạo booking database, Redis hay agent.
Dataset, predictions và evaluation artifact chỉ được đọc; portal chỉ ghi file review.

Địa chỉ `DESKTOP-KELIBTC` là hostname trong mạng nội bộ, không phải link Internet công khai. Máy chạy
Docker phải đang bật và đồng đội phải ở cùng LAN/Wi-Fi (hoặc cùng VPN) mới truy cập được.

## Nhập kết quả vào benchmark

```powershell
.\.venv\Scripts\python.exe backend\scripts\run_agent_evaluation.py `
  --predictions eval\results\agent-predictions.json `
  --human-ratings eval\human\reviews.csv
```
