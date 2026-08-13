# Guardrail And Limit

Tài liệu này mô tả các guardrail và limit đang được thực hiện trong code hiện tại, nhằm phục vụ kiểm tra bảo mật trước prompt injection, tool misuse, rò rỉ dữ liệu nhạy cảm, lỗi payload quá lớn, DDoS và rủi ro vượt budget khi gọi API/LLM.

## Phạm Vi Rà Soát

Các file chính đã kiểm tra:

- `backend/src/config.py`
- `backend/src/models/schemas.py`
- `backend/src/api/routes.py`
- `backend/src/api/site_routes.py`
- `backend/src/guardrails/*`
- `backend/src/agents/graph.py`
- `backend/src/agents/nodes/*`
- `backend/src/services/llm.py`
- `backend/src/services/booking/access.py`
- `backend/src/database/guard.py`
- `backend/src/main.py`
- `backend/src/logging_config.py`
- `.env.example`

## Tổng Quan Hiện Trạng

Project hiện có guardrail deterministic chạy ở 3 lớp chính:

1. Input guard trước khi gọi LangGraph/LLM.
2. Tool guard trước khi LangGraph ToolNode thực thi tool.
3. Output guard trước khi trả kết quả public API cho frontend.

Ngoài ra còn có một số limit ở Pydantic schema, query parameter, OTP/access session, vòng lặp tool, logging rotation và database query guard.

Điểm quan trọng: hiện tại chưa thấy global request rate limiting, IP throttling, concurrency limiting, LLM timeout/retry budget, token budget, quota per user/session, hay middleware chống DDoS ở tầng application. Các guardrail hiện tại giúp giảm rủi ro injection/tool abuse/payload phức tạp, nhưng không đủ để chống DDoS hoặc kiểm soát chi phí API trong môi trường public production.

## Limit Đang Được Set

| Nhóm | Setting / Code | Giá trị mặc định | Ràng buộc cấu hình | Ý nghĩa |
|---|---:|---:|---:|---|
| Chat message | `CHAT_MESSAGE_MAX_LENGTH` | `5000` chars | Pydantic `min_length=1`, `max_length=5000` | Giới hạn tin nhắn user gửi vào `/api/v1/chat`. |
| Conversation ID | `ChatRequest.conversation_id` | `""` | `max_length=100` | Giới hạn độ dài session/thread id. |
| Conversation ID format | `_SAFE_CONVERSATION_ID` | regex | `^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$` | Chặn ký tự lạ trong conversation id sau khi API tự sinh hoặc client gửi lên. |
| Guardrail enabled | `GUARDRAILS_ENABLED` | `true` | boolean | Bật/tắt toàn bộ deterministic guardrail. |
| Payload bytes | `GUARDRAILS_MAX_PAYLOAD_BYTES` | `16384` bytes | `1024..1048576` | Giới hạn JSON-like payload của context/action/tool args. |
| Payload depth | `GUARDRAILS_MAX_PAYLOAD_DEPTH` | `6` | `1..20` | Chặn object/list lồng quá sâu. |
| Payload nodes | `GUARDRAILS_MAX_PAYLOAD_NODES` | `256` | `16..10000` | Chặn payload có quá nhiều node. |
| Payload string | `GUARDRAILS_MAX_PAYLOAD_STRING_CHARS` | `5000` chars | `128..100000` | Chặn string quá dài trong payload. |
| Payload key length | hard-coded | `128` chars | fixed | Chặn key object quá dài. |
| Tool calls per AI message | `GUARDRAILS_MAX_TOOL_CALLS_PER_MESSAGE` | `3` | `1..8` | Chặn model gọi quá nhiều tool trong một message. |
| Agent tool loop | `MAX_TOOL_CALLS` | `8` | hard-coded | Dừng vòng lặp skill-tool để tránh loop vô hạn. |
| Public output chars | `GUARDRAILS_MAX_OUTPUT_CHARS` | `8000` chars | `256..100000` | Cắt response text quá dài trước khi trả client. |
| Site vehicle list | `GET /vehicles?limit=` | `20` | `1..50` | Giới hạn số vehicle public API trả ra. |
| Dashboard limit | `dashboard(limit=50)` | `50` | service clamp `1..200` | Giới hạn dashboard ở tầng service, nhưng route chưa dùng `Query`. |
| Client log message | `ClientLogRequest.message` | required | `1..2000` chars | Giới hạn message log từ frontend. |
| OTP TTL | `BOOKING_ACCESS_OTP_TTL_SECONDS` | `60s` | `60..900` | Thời gian sống OTP. |
| OTP resend cooldown | `BOOKING_ACCESS_OTP_RESEND_COOLDOWN_SECONDS` | `60s` | `1..900` | Chặn gửi lại OTP quá nhanh cho cùng booking/contact. |
| OTP max attempts | `BOOKING_ACCESS_OTP_MAX_ATTEMPTS` | `2` | `1..10` | Số lần nhập sai OTP trước khi lock. |
| Access session TTL | `BookingService.access_session_ttl_seconds` | `1800s` | hard-coded default constructor | Thời gian sống access token sau OTP. |
| Zalo poll timeout | `ZALO_BOT_POLL_TIMEOUT_SECONDS` | `25s` | `1..50` | Timeout long polling Zalo. |
| SQLite timeout | `sqlite3.connect(timeout=10)` | `10s` | hard-coded | Timeout lock DB SQLite. |
| SQLite busy timeout | `PRAGMA busy_timeout=10000` | `10000ms` | hard-coded | Chờ lock SQLite tối đa 10s. |
| Log rotation | `backend.log`, `ai_agent.log` | `5MB x 5` | hard-coded | Giới hạn file log backend/agent. |
| Frontend log rotation | `frontend.log` | `2MB x 3` | hard-coded | Giới hạn file log frontend. |

## Luồng Guardrail Cho `/api/v1/chat`

File: `backend/src/api/routes.py`

1. FastAPI/Pydantic validate `ChatRequest`.
2. Nếu thiếu `conversation_id`, server tự sinh UUID.
3. `get_guardrails().inspect_input(...)` chạy trước khi gọi agent.
4. Nếu input bị block, API trả `ChatResponse` với message an toàn và `action_error=<guardrail_code>`. Agent/LLM không được gọi.
5. Nếu input allowed, message đã normalize được đưa vào LangGraph agent.
6. Sau khi agent trả kết quả, `guardrails.protect_output(result)` sanitize dữ liệu public.
7. API trả `response`, `tool_input`, `action_data`, `action_error` đã qua output guard.

Nếu có exception ngoài ý muốn, route log lỗi và trả HTTP 500 với message chung: `Có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau.`

## Input Guard

File: `backend/src/guardrails/input_guard.py`

Input guard thực hiện:

- Normalize text bằng Unicode NFC.
- Xóa một số ký tự format/invisible như zero-width space, zero-width joiner, BOM.
- Xóa control characters loại `Cc`, trừ newline, carriage return, tab.
- Trim khoảng trắng đầu/cuối.
- Chặn message rỗng sau normalize với code `EMPTY_MESSAGE`.
- Chặn `conversation_id` sai regex với code `INVALID_CONVERSATION_ID`.
- Validate `context` và `action_payload` bằng payload limits.
- Nếu có `action`, validate action theo allowlist field contract.
- Quét prompt injection trên cả message và mọi string trong `context`.

Các pattern prompt injection nằm ở `backend/src/guardrails/policies.py`, gồm các nhóm:

- `PROMPT_INJECTION_OVERRIDE`: yêu cầu ignore/disregard/forget/override/bypass previous/system/developer/hidden instructions; có cả pattern tiếng Việt như bỏ qua/phớt lờ/quên/vượt qua/ghi đè hướng dẫn/chỉ thị/luật/quy tắc trước đó/hệ thống/ẩn.
- `SECRET_EXFILTRATION`: yêu cầu reveal/show/print/return/dump/expose/leak system prompt/developer message/hidden instructions/API keys/access tokens/env/secrets; có cả pattern tiếng Việt như hiển thị/tiết lộ/in ra/trả về/đọc ra system prompt/chỉ thị ẩn/khóa API/token/biến môi trường/bí mật.
- `ROLE_INJECTION`: phát hiện tag hoặc role marker như `<tool_call>`, `<function_call>`, `<system>`, `<developer>`, hoặc dòng `system:` / `developer:`.
- `ROLE_INJECTION`: phát hiện "you are now" / "act as" kết hợp với linux terminal/shell/developer mode/system administrator.

Khi block prompt injection, message public trả về:

`Yêu cầu này có dấu hiệu cố gắng thay đổi chỉ dẫn hoặc truy cập thông tin nội bộ, nên tôi không thể xử lý. Tôi vẫn có thể hỗ trợ thông tin xe VinFast và đặt lịch lái thử.`

## Payload Guard

File: `backend/src/guardrails/structure.py`

`validate_payload` serialize payload bằng `json.dumps(..., default=str)` để tính byte size. Sau đó đi bộ qua object/list để kiểm tra:

- Payload có serialize được không.
- Tổng bytes không vượt `GUARDRAILS_MAX_PAYLOAD_BYTES`.
- Tổng node không vượt `GUARDRAILS_MAX_PAYLOAD_NODES`.
- Độ sâu không vượt `GUARDRAILS_MAX_PAYLOAD_DEPTH`.
- String không vượt `GUARDRAILS_MAX_PAYLOAD_STRING_CHARS`.
- Object key không vượt 128 ký tự.

Payload guard được dùng cho:

- `context` trong `/chat`.
- `action_payload` trong `/chat`.
- `payload` trong `/demo/action`.
- Tool arguments trước khi tool thực thi.

## Structured Action Guard

File: `backend/src/guardrails/policies.py`

`ACTION_ALLOWED_FIELDS` giới hạn field được phép cho action trong `/chat`:

- `search_options`
- `hold_slot`
- `update_draft`
- `confirm_booking`
- `request_access`
- `verify_access`

Nếu action không nằm trong contract: block `ACTION_NOT_ALLOWED`.

Nếu payload có field ngoài contract: block `ACTION_FIELDS_NOT_ALLOWED`.

`DEMO_ACTION_ALLOWED_FIELDS` áp dụng cho `/api/v1/demo/action`, mở rộng thêm các command authenticated như:

- `get_draft`
- `list_bookings`
- `get_details`
- `update_details`
- `hold_reschedule`
- `confirm_reschedule`
- `cancel_booking`

Route `/demo/action` vẫn có check `Unknown demo action` trước, sau đó mới guard action field contract.

## Tool Guard

File: `backend/src/guardrails/tool_guard.py`

Tool guard chạy trước LangGraph `ToolNode`:

- Chặn tool node nếu state cuối không phải `AIMessage` có `tool_calls`: `INVALID_TOOL_STATE`.
- Chặn số tool call trong một AI message vượt `GUARDRAILS_MAX_TOOL_CALLS_PER_MESSAGE`: `TOOL_CALL_LIMIT_EXCEEDED`.
- Chỉ cho gọi tool nằm trong allowlist của skill hiện tại: `TOOL_NOT_ALLOWED`.
- Tool args bắt buộc là object/dict: `INVALID_TOOL_ARGUMENTS`.
- Validate tool args bằng payload limits: `TOOL_PAYLOAD_LIMIT_EXCEEDED`.
- Chặn duplicate tool call cùng name/args trong một model message: `DUPLICATE_TOOL_CALL`.
- Chặn batch nhiều mutating tool, hoặc mutating tool đi kèm tool khác: `MUTATION_BATCH_NOT_ALLOWED`.
- Tool confirm booking cần xác nhận rõ từ user hoặc requested action từ UI: `EXPLICIT_CONFIRMATION_REQUIRED`.

Các mutating tool:

- `hold_test_drive_slot`
- `update_booking_draft`
- `confirm_test_drive_booking`
- `request_booking_access`
- `verify_booking_access`

Tool cần explicit confirmation:

- `confirm_test_drive_booking`

Nếu block, tool guard trả `ToolMessage` status error cho từng tool call thay vì execute tool thật.

## Skill Tool Allowlist

File: `backend/src/agents/graph.py`

Graph tách tool theo skill:

Booking skill được gọi:

- `search_test_drive_options`
- `hold_test_drive_slot`
- `get_booking_draft`
- `update_booking_draft`
- `request_booking_access`
- `verify_booking_access`
- `get_booking_details`
- `confirm_test_drive_booking`

Advise skill chỉ được gọi:

- `search_knowledge`

Điểm này giảm rủi ro model ở skill tư vấn gọi nhầm tool booking có side effect.

## Tool Loop Limit

File: `backend/src/agents/graph.py`

`MAX_TOOL_CALLS = 8`

`should_continue_booking` và `should_continue_advise` kết thúc graph nếu `tool_call_count >= 8`. Đây là guard chống vòng lặp tool vô hạn và một phần giảm rủi ro runaway LLM/tool loop.

Lưu ý: `tool_call_count` hiện tăng theo lượt AI response có tool call, không phải tổng số tool call thực tế. Một lượt AI message vẫn có thể chứa tối đa `GUARDRAILS_MAX_TOOL_CALLS_PER_MESSAGE=3`, nhưng mutating tool bị ép chạy đơn lẻ.

## Output Guard

File: `backend/src/guardrails/output_guard.py`

Output guard thực hiện trước khi trả public API:

- Không trả `analysis` nội bộ; luôn set `analysis=""`.
- Sanitize `response` và `action_error`.
- Redact secret values tìm được trong toàn bộ result.
- Redact assignment dạng `api_key=...`, `access_token=...`, `session_token=...`, `otp_code=...`, `password=...`, `secret=...`.
- Redact email thành `[email]`.
- Redact phone thành `[phone]`.
- Nếu response chứa marker giống system prompt/internal instruction như `--- system instructions ---`, `active skill guidelines`, `system instructions & behavioral protocol`, trả fallback an toàn.
- Cắt output vượt `GUARDRAILS_MAX_OUTPUT_CHARS`, thêm `…[truncated]`.
- Redact `tool_input` theo `PUBLIC_TOOL_INPUT_SECRET_KEYS`.
- Redact `action_data` theo `NEVER_PUBLIC_ACTION_DATA_KEYS`.

Secret keys không được hiện trong natural-language output hoặc public diagnostic:

- `access_session_token`
- `access_token`
- `api_key`
- `authorization`
- `challenge_id`
- `client_secret`
- `contact_value`
- `cookie`
- `license_number`
- `openai_api_key`
- `openrouter_api_key`
- `otp`
- `otp_code`
- `password`
- `refresh_token`
- `token`
- `zalo_bot_token`

Lưu ý quan trọng: `action_data` vẫn có thể giữ `challenge_id` và `access_session_token` vì frontend cần cho workflow OTP/authenticated booking. Raw OTP và backend credentials thì bị redact khỏi `action_data`.

## Intent / Sensitive Policy Guard

Files:

- `backend/src/agents/nodes/classifier_node.py`
- `backend/src/agents/nodes/sensitive_policy_node.py`
- `backend/src/agents/constants.py`

Classifier có keyword bypass để không cần gọi LLM trong một số trường hợp:

- Chủ quyền: `hoàng sa`, `trường sa`, `biển đông`, `paracel`, `spratly`.
- Out-of-scope code/task: `viết code`, `lập trình`, `python`, `javascript`, `code python`, `viết script`, `giải toán`.

Nếu match, route sang `sensitive_policy_node`, tiết kiệm token và tránh model hallucination.

Nếu classifier LLM lỗi hoặc không có key, fallback route domain bằng keyword đơn giản. Với request booking context/action, classifier bypass thẳng sang booking skill.

## LLM/API Call Handling

File: `backend/src/services/llm.py`

Logic hiện tại:

- Nếu có `OPENROUTER_API_KEY`, dùng `ChatOpenAI` với `base_url=https://openrouter.ai/api/v1`.
- Nếu có `OPENAI_API_KEY`, dùng OpenAI model, remove prefix `openai/` nếu có.
- Nếu không có key, trả `None`; node sẽ fallback message an toàn thay vì tạo client với credential giả.
- `llm_temperature` default `0.7`, range `0.0..2.0`.
- Classifier dùng `classifier_model_name` hoặc fallback `model_name`, temperature `0.0`.

Các điểm chưa thấy trong code hiện tại:

- Chưa set explicit request timeout cho ChatOpenAI.
- Chưa set max retries riêng.
- Chưa set `max_tokens`/output token cap ở LLM call.
- Chưa có per-request API cost estimate.
- Chưa có per-user/session/day budget.
- Chưa có circuit breaker khi provider lỗi liên tục.
- Chưa có queue/concurrency limit cho LLM calls.

Vì vậy output char limit chỉ cắt response sau khi LLM trả về; nó không đảm bảo giới hạn token/cost phía provider.

## OTP Và Access Guard

Files:

- `backend/src/services/booking/access.py`
- `backend/src/services/booking/service.py`
- `backend/src/dependencies.py`
- `backend/src/config.py`

Các bảo vệ hiện tại:

- OTP chỉ cấp cho booking/contact khớp.
- Purpose phải thuộc allowlist: `lookup`, `reschedule`, `cancel`, `update_details`, `update_notifications`.
- Channel phải là `zalo`, `sms`, hoặc `email`.
- Contact được normalize theo phone/email.
- Destination được hash bằng HMAC.
- OTP code hash có salt riêng từng challenge.
- Production bắt buộc `BOOKING_ACCESS_OTP_SECRET` dài ít nhất 32 ký tự.
- Pending OTP cũ cùng booking bị `superseded` khi tạo challenge mới.
- Chặn resend OTP trong cooldown.
- OTP hết hạn bị đổi status `expired`.
- Sai OTP tăng `attempt_count`, đủ ngưỡng thì status `locked`.
- Session token sinh bằng `secrets.token_urlsafe(32)`, chỉ lưu hash.
- Access session có TTL 1800 giây.
- Access token bị scope theo booking ownership/same phone owner.
- Permission checked theo từng thao tác như `read_booking`, `cancel_booking`, `confirm_reschedule`, `update_details`.
- Idempotent/replay cancel vẫn require access token trước khi trả cache theo comment/test.

Limit mặc định khi khởi tạo service trong app:

- OTP TTL: `60s`.
- OTP resend cooldown: `60s`.
- OTP max attempts: `2`.
- Access session TTL: `1800s`.

## Database Guard

File: `backend/src/database/guard.py`

`QueryGuard` chạy trước SQL execute:

- Chặn SQL rỗng.
- Chặn nhiều statement trong một execute bằng dấu `;` giữa statement.
- Kiểm tra số placeholder `?` khớp số params.
- Validate table name trong `FROM`, `JOIN`, `UPDATE`, `INTO`, `ALTER TABLE`, `CREATE TABLE IF NOT EXISTS` theo schema known tables.
- Validate columns trong `INSERT INTO (...)`.
- Validate columns trong `UPDATE ... SET`.

Tác dụng: giảm lỗi schema và một phần giảm rủi ro SQL không mong muốn từ code nội bộ.

Giới hạn: đây không phải SQL injection firewall tổng quát. Những query động vẫn cần dùng parameter binding đúng cách. Trong `list_bookings`, code tự tạo placeholder list cho `IN (...)` dựa trên set phone, nhưng vẫn truyền params riêng nên ổn hơn nối raw value.

## HTTP, CORS, Static Và Logging

File: `backend/src/main.py`

Hiện có:

- `CORSMiddleware` với origin từ `CORS_ORIGINS`.
- `allow_credentials=True`.
- `allow_methods=["*"]`.
- `allow_headers=["*"]`.
- Middleware request logging ghi method/path/status/duration.
- Static media mount ở `/media`.
- `/health` endpoint.

Chưa thấy:

- TrustedHost middleware.
- HTTPS redirect middleware.
- Security headers middleware.
- Request body size middleware global.
- Global timeout middleware.
- Global exception response chuẩn hóa ngoài một số route.
- Rate limit middleware.

File: `backend/src/logging_config.py`

Có rotating logs:

- `logs/backend.log`: 5MB, 5 backups.
- `logs/ai_agent.log`: 5MB, 5 backups.
- `logs/frontend.log`: 2MB, 3 backups.
- `httpx` log level bị hạ xuống WARNING để tránh lộ credential trong URL Zalo.

## Site API Cache Và Query Limit

File: `backend/src/api/site_routes.py`

Public content/catalog endpoints có:

- `ETag`.
- `Cache-Control: public, max-age=300, stale-while-revalidate=86400`.
- `X-Request-ID`.
- `GET /vehicles` limit `1..50`.
- `category` chỉ nhận `personal|fleet`.

Cache giúp giảm tải cho nội dung public nếu client/CDN tôn trọng header, nhưng không thay thế rate limit.

## Đánh Giá Theo Rủi Ro

### Prompt Injection

Mức đảm bảo hiện tại: khá tốt ở lớp deterministic high-confidence pattern.

Điểm mạnh:

- Chặn trước khi gọi LLM.
- Quét cả `message` và string trong `context`.
- Normalize/xóa zero-width characters để giảm bypass đơn giản.
- Có pattern tiếng Anh và tiếng Việt.
- Tool guard độc lập với prompt, không chỉ dựa vào instruction.

Điểm còn thiếu:

- Pattern-based guard không bắt hết prompt injection biến thể thấp tín hiệu hoặc đa ngôn ngữ khác.
- Không thấy content moderation/secondary classifier chuyên chống injection.
- Context vẫn được stringify và đưa vào prompt; nếu pattern không bắt được thì prompt vẫn có thể bị ảnh hưởng, nhưng tool guard/output guard là lớp giảm thiểu tiếp theo.

### Tool Abuse / Unauthorized Action

Mức đảm bảo hiện tại: tốt hơn mức prompt-only vì có allowlist deterministic.

Điểm mạnh:

- Tool allowlist theo skill.
- Payload contract theo action.
- Mutating tool không được batch.
- Confirm booking cần xác nhận explicit.
- OTP/access permission scope theo booking.

Điểm còn thiếu:

- `/demo/action` là public boundary mạnh; hiện không thấy auth tổng quát cho route này, chỉ dựa vào action contract và token ở một số command.
- Các action không cần token như `search_options`, `hold_slot`, `update_draft`, `confirm_booking` vẫn cần được đánh giá theo workflow thực tế để tránh spam giữ slot hoặc confirm draft nếu attacker biết `booking_id`.

### Data Leakage

Mức đảm bảo hiện tại: trung bình-khá.

Điểm mạnh:

- Output guard redacts nhiều key nhạy cảm.
- Không trả `analysis`.
- Redact email/phone trong natural-language response.
- Log tool input có masking cho OTP/token/contact.
- `httpx` log bị hạ xuống WARNING.

Điểm còn thiếu:

- `trace_event` nhận `context`, `action_payload`, `response.model_dump()`; cần kiểm tra implementation `backend/src/agents/trace.py` để bảo đảm redaction đầy đủ ở mọi log sink.
- `action_data` cố ý trả `challenge_id` và `access_session_token` cho frontend; cần bảo vệ bằng HTTPS, same-origin/session policy, và không log ở frontend.

### DDoS / Server Stability

Mức đảm bảo hiện tại: chưa đủ cho public production.

Đã có:

- Payload limit ở guardrail cho context/action/tool args.
- Pydantic max length cho chat message.
- Tool loop limit.
- Site API cache/ETag.
- SQLite busy timeout.
- Log rotation.

Chưa thấy:

- IP/user/session rate limit.
- Request body size limit ở middleware/server/proxy.
- Concurrency limit cho `/chat`.
- Queue/backpressure.
- Global timeout cho request xử lý agent.
- Uvicorn/gunicorn worker/process config trong code.
- Circuit breaker khi DB/LLM chậm.
- Nginx/API gateway rate limit cho Docker backend.

Nếu deploy public, cần đặt thêm rate limit ở reverse proxy/API gateway và trong app cho `/api/v1/chat`, `/api/v1/demo/action`, OTP endpoints.

### API Budget / LLM Cost Explosion

Mức đảm bảo hiện tại: chưa đủ.

Đã có:

- Classifier keyword bypass cho một số sensitive/out-of-scope request để tránh gọi LLM.
- Message/context/tool payload limit.
- History window `MAX_LLM_HISTORY_MESSAGES = 24`.
- Tool loop limit `8`.
- Nếu không có key thì fallback an toàn.

Chưa thấy:

- `max_tokens` cho ChatOpenAI.
- Per-call timeout.
- Per-call retry limit.
- Token counting trước khi gọi model.
- Budget theo IP/user/session/day.
- Cache semantic cho câu hỏi lặp.
- Abort khi provider response lâu.
- Giới hạn số request đồng thời gọi LLM.

Vì vậy nếu bị spam `/chat`, app vẫn có thể gọi LLM nhiều lần và gây tăng chi phí.

## Khuyến Nghị Ưu Tiên

P0 cho production/public exposure:

1. Thêm rate limit cho `/api/v1/chat`, `/api/v1/demo/action`, OTP request/verify theo IP + conversation_id/contact hash.
2. Thêm request timeout cho agent/LLM call, ví dụ timeout tổng `/chat`.
3. Set `max_tokens`/output token limit khi tạo `ChatOpenAI`.
4. Thêm concurrency limit/queue cho LLM calls để tránh cạn worker khi bị spam.
5. Đặt reverse proxy limit: body size, requests per second, burst, connection limit.
6. Bảo vệ hoặc tách `/demo/action`; các command mutating nên yêu cầu token/workflow state rõ ràng.

P1:

1. Thêm token/cost accounting theo conversation/session/day.
2. Thêm circuit breaker khi LLM provider lỗi hoặc latency cao.
3. Chuẩn hóa security headers và TrustedHost/HTTPS ở production.
4. Rà `trace_event` để chắc chắn không log `access_session_token`, OTP, contact raw, API key.
5. Thêm tests cho bypass injection đa ngôn ngữ/obfuscation nâng cao.

P2:

1. Thêm dashboard metric cho guardrail block count, LLM calls, latency, error rate.
2. Cache response cho content/FAQ ít thay đổi.
3. Tách config dev/prod chặt hơn để tránh `GUARDRAILS_ENABLED=false` hoặc OTP secret yếu trong production.

## Kết Luận

Project hiện có nền guardrail deterministic khá rõ ràng cho prompt injection cơ bản, payload phức tạp, tool allowlist, side-effect batching, output redaction và OTP/access control. Tuy nhiên, với mục tiêu chống DDoS và tránh vượt budget API, hiện tại còn thiếu các lớp kiểm soát lưu lượng và chi phí bắt buộc: rate limit, concurrency limit, timeout, token/max cost cap và reverse proxy protection.
