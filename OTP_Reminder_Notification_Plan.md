# OTP, Reminder & Notification Implementation Plan

## 1. Mục tiêu và phạm vi

Thay OTP và notification mock bằng email thật qua Gmail API + OAuth2. MVP có khoảng 100 user, tối đa 1.000 OTP và 100 reminder/ngày; dùng PostgreSQL, một backend instance, không Redis/Celery. Email là channel chính; abstraction Zalo/SMS vẫn được giữ.

Không thêm bảng mới. Tiếp tục dùng `otp_challenges`, `booking_access_sessions`, `notification_plans`, `notification_jobs` và `booking_events`.

## 2. Hiện trạng

- `access.py` tạo, hash, lưu và verify OTP; OTP hiện cố định là `666666`.
- OTP policy được khai báo trong `backend/src/config.py`, truyền qua `backend/src/dependencies.py` vào `BookingService`.
- `notifications.py` đã có `MessagingProvider`, `OtpSender` và routing theo channel.
- `lifecycle.py` tạo confirmation, reminder 24h/2h; `management.py` hủy job cũ và tạo job mới khi reschedule/cancel.
- `background.py` đọc `notification_jobs`, gửi, retry và lưu provider metadata.
- `main.py` đã chạy dispatcher trong background, hiện polling mỗi 5 giây.

Còn thiếu Gmail provider, HTML template, custom reminder, OTP thật và phục hồi job `processing` bị kẹt.

## 3. Cấu hình Gmail và notification

### Implement

Thêm vào `backend/src/config.py` và `.env.example`:

```env
GMAIL_ENABLED=false
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_SENDER_EMAIL=
NOTIFICATION_POLL_INTERVAL_SECONDS=60
NOTIFICATION_BATCH_SIZE=100
NOTIFICATION_PROCESSING_TIMEOUT_SECONDS=300
```

Giữ nguyên OTP policy hiện tại:

```env
BOOKING_ACCESS_OTP_TTL_SECONDS=60
BOOKING_ACCESS_OTP_RESEND_COOLDOWN_SECONDS=60
BOOKING_ACCESS_OTP_MAX_ATTEMPTS=2
RATE_LIMIT_OTP_REQUEST_PER_CONTACT_PER_HOUR=3
RATE_LIMIT_OTP_VERIFY_PER_CHALLENGE_PER_MINUTE=5
```

### Logic

Production chỉ khởi tạo Gmail provider khi đủ credential và `GMAIL_ENABLED=true`; nếu bật nhưng thiếu secret thì fail startup. Secret chỉ đọc từ environment, không log hoặc trả qua API.

### Ảnh hưởng

Không đổi API/schema. Operator có thể chỉnh OTP, polling và retry mà không sửa service code.

## 4. Gmail provider

### Implement

Thêm `backend/src/services/booking/gmail_provider.py`. `GmailMessagingProvider` implement `MessagingProvider` và `OtpSender`. Dùng refresh token lấy access token với scope `gmail.send`, sau đó gửi MIME plain text + HTML.

Cập nhật `backend/requirements.txt` với thư viện Google OAuth/Gmail cần thiết. Cập nhật `backend/src/dependencies.py` để inject Gmail provider vào `BookingService` và `RoutingMessagingProvider`.

### Logic

- `channel=email`: gửi qua Gmail.
- `channel=zalo/sms`: giữ adapter/fallback hiện tại, chưa tự động fallback khi Gmail lỗi.
- Trả `ProviderResult` gồm provider status, Gmail message ID, `retryable` và response đã sanitize.
- Không log access token, refresh token, Authorization header, email body hoặc OTP.

### Ảnh hưởng

Business logic không phụ thuộc Gmail SDK; thêm Zalo/SMS sau này không cần sửa booking flow.

## 5. OTP email thật

### Implement

Sửa `request_access()` trong `backend/src/services/booking/access.py`:

- Thay `666666` bằng `f"{secrets.randbelow(1_000_000):06d}"`.
- Giữ salt + HMAC hash hiện tại; không lưu plaintext.
- Gọi `OtpSender.send(channel="email", ...)` sau khi transaction tạo challenge thành công.
- Không trả `otp_code` ngoài chế độ local/test có chủ đích.

### Logic

`request OTP -> validate booking/contact/rate limit -> supersede challenge cũ -> sinh và hash OTP -> commit challenge -> Gmail gửi OTP -> user verify -> tạo access session 1.800 giây`.

Nếu Gmail lỗi, challenge vẫn tồn tại và response báo gửi thất bại; cooldown/rate limit vẫn được áp dụng. Timeout/429/5xx được retry; invalid recipient/OAuth configuration là terminal.

### Ảnh hưởng

Không đổi `otp_challenges`, verify flow hoặc permissions. Tests/local vẫn dùng `InMemoryOtpSender`; production dùng Gmail provider.

## 6. Email template

### Implement

Thêm `backend/src/services/booking/email_templates.py` và template cho:

- `otp_verification`
- `booking_confirmation`
- `booking_update`
- `reschedule_confirmation`
- `reminder`
- `cancellation_confirmation`

Mỗi renderer trả subject, plain text và HTML. Chuyển logic `_render_notification()` trong `background.py` sang renderer chung; Gmail provider chỉ nhận nội dung đã render, không chứa business query.

### Logic

Template context được lấy từ booking, người nhận, xe, showroom, thời gian và tư vấn viên. Escape dữ liệu trước khi chèn vào HTML. OTP template chỉ nhận OTP ở memory trong lúc gửi; OTP không đi qua `notification_jobs`.

### Ảnh hưởng

Thay phần plain-text hardcode hiện tại, không đổi booking API. Template có thể chỉnh độc lập với Gmail integration và tái dùng cho provider khác.

## 7. Tạo notification theo booking event

### Implement

Cập nhật `backend/src/services/booking/lifecycle.py` và `management.py`:

- Confirm: tạo `booking_confirmation` và reminder.
- Update details: tạo `booking_update` nếu dữ liệu người nhận/nội dung booking thay đổi.
- Reschedule: cancel pending job cũ, tạo `reschedule_confirmation`, tạo reminder theo `start_at` mới.
- Cancel: cancel pending reminder/notification cũ, tạo `cancellation_confirmation`.

Tiếp tục dùng `_create_jobs()` và `_create_transactional_notification_jobs()` thay vì tạo service flow mới.

### Logic

Việc đổi booking và tạo/cancel job nằm trong cùng DB transaction. Idempotency hiện có của booking command tiếp tục ngăn cùng UI action tạo job lặp.

### Ảnh hưởng

Happy path booking không đổi. Mỗi event có thể tạo thêm row `notification_jobs`, nhưng không thay schema nghiệp vụ.

## 8. Reminder mặc định và tùy chỉnh

### Implement

Mở rộng `_create_jobs()` trong `lifecycle.py` để đọc `notification_plans.custom_plan_json`:

```json
{"reminder_offsets_minutes": [1440, 120, 30]}
```

Hai cờ `reminder_24h_enabled` và `reminder_2h_enabled` vẫn được hỗ trợ để backward compatible. Chuẩn hóa offset thành số nguyên dương, loại trùng và giới hạn số mốc hợp lý cho MVP.

### Logic

Với mỗi offset: `scheduled_at = start_at - offset`. Không tạo job nếu `scheduled_at <= now`. Reschedule tạo lại toàn bộ reminder theo giờ mới; cancel chuyển các job `pending` sang `cancelled`.

### Ảnh hưởng

Tái sử dụng `custom_plan_json`, không migration DB. UI/API chỉ cần thay đổi khi muốn cho business nhập mốc tùy chỉnh; hai mốc mặc định vẫn hoạt động như hiện tại.

## 9. Scheduler, retry và recovery

### Implement

Cập nhật `main.py` dùng polling interval từ config, mặc định 60 giây. Cập nhật `background.py`:

- Batch tối đa 100 job.
- Trước khi claim, đưa job `processing` quá 5 phút về `pending` nếu chưa vượt `max_attempts`.
- Claim/update status trong transaction hiện có.
- Dùng `ProviderResult.retryable` để quyết định `pending` hay `failed`.
- Retry timeout, Gmail 429 và 5xx; không retry invalid recipient hoặc OAuth/config lỗi.

### Logic

`booking event -> persisted notification_jobs -> scheduler poll -> claim processing -> render -> Gmail send -> sent/pending/failed`.

Restart không mất reminder vì job nằm trong PostgreSQL. Một instance MVP không cần distributed lock. Gmail message ID và provider response được lưu để audit; không thể bảo đảm exactly-once nếu process chết ngay sau Gmail gửi nhưng trước khi update DB, nên recovery phải ghi log rõ khả năng duplicate.

### Ảnh hưởng

Giảm polling từ 5 giây xuống 60 giây; reminder vẫn nằm trong mức trễ chấp nhận 5 phút. Không thêm worker, Redis hoặc scheduler service.

## 10. Audit và bảo mật

### Implement

Giữ metadata hiện có trong `notification_jobs` và event trong `booking_events`. Chuẩn hóa log theo job ID, booking ID, notification type, attempt, provider status và error code.

### Logic

Không lưu/log OAuth credential, OTP plaintext hoặc Gmail Authorization header. Provider response phải loại token và nội dung nhạy cảm trước khi ghi DB.

### Ảnh hưởng

Không đổi schema; tăng khả năng debug gửi chậm, retry và email lỗi.

## 11. Kiểm thử dự kiến

- Unit test Gmail provider bằng fake HTTP/client, không gọi Gmail thật.
- OTP: secure random, hash/verify, expiry, resend, attempts, single-use và không lộ plaintext.
- Template: subject/plain/HTML đúng và HTML được escape.
- Reminder: mặc định, custom offset, bỏ mốc quá khứ, loại trùng.
- Notification: confirm/update/reschedule/cancel tạo hoặc hủy đúng job.
- Retry/recovery: timeout, 429, 5xx, invalid recipient và stale `processing`.
- Gmail integration test chạy riêng bằng credential test, không nằm trong unit test mặc định.

## 12. Thứ tự triển khai

1. Config và Gmail provider.
2. Template renderer.
3. OTP secure random + email delivery.
4. Notification event và custom reminder.
5. Scheduler retry/recovery.
6. Kiểm tra audit, secret redaction và regression booking flow.

Kết quả không thay topology booking hoặc database schema; thay đổi tập trung trong provider, template, OTP delivery và dispatcher hiện có.
