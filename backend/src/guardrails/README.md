# Guardrails cho VinFast Test Drive Agent

Folder này chứa các guardrail **deterministic** của backend. Chúng không phụ thuộc vào việc LLM có tuân thủ prompt hay không và không gọi thêm model, vì vậy có thể kiểm thử lặp lại, có độ trễ thấp và fail closed tại các ranh giới quan trọng.

## 1. Mục tiêu

Guardrails bảo vệ luồng `/api/v1/chat` trước các nhóm rủi ro chính:

1. Prompt injection và role injection nhằm thay đổi system instruction, giả mạo tool call hoặc buộc agent tiết lộ prompt/secret.
2. Payload abuse: JSON quá lớn, quá sâu, quá nhiều node hoặc chuỗi bất thường gây tốn tài nguyên.
3. Tool abuse: gọi tool ngoài skill đang hoạt động, gọi trùng, batch nhiều thao tác ghi, gọi quá nhiều tool hoặc xác nhận booking khi người dùng chưa đồng ý rõ ràng.
4. Data leakage: nội dung phản hồi làm lộ OTP, access token, API key, số điện thoại, email, system prompt hoặc internal analysis.
5. Contract abuse ở structured action: frontend gửi field không nằm trong allowlist của action.

Guardrails không thay thế xác thực người dùng, rate limit ở API gateway, phân quyền database, validation nghiệp vụ hay monitoring. Chúng là một lớp defense-in-depth dành riêng cho biên AI/tool.

## 2. Vị trí trong luồng xử lý

```text
Client
  │
  ▼
ChatRequest / Pydantic
  │
  ▼
InputGuard ── block ──► ChatResponse an toàn, không gọi LLM
  │ allow + normalize
  ▼
LangGraph classifier / skill
  │
  ▼
GuardedToolNode ── block ──► ToolMessage lỗi chuẩn hóa, không chạy side effect
  │ allow
  ▼
Booking/knowledge tool
  │
  ▼
OutputGuard ── redact/truncate/hide analysis
  │
  ▼
Public ChatResponse
```

Ba enforcement point tương ứng:

- `src/api/routes.py`: gọi `Guardrails.inspect_input()` trước `agent.ainvoke()`, `Guardrails.protect_output()` trước khi tạo `ChatResponse`, và kiểm tra contract cho `/demo/action`.
- `src/agents/graph.py`: dùng `build_guarded_tool_node()` thay cho `ToolNode` trực tiếp.
- `src/guardrails/`: chứa policy và implementation độc lập.

## 3. Cấu trúc folder

| File | Trách nhiệm |
|---|---|
| `input_guard.py` | Chuẩn hóa input, kiểm tra conversation ID, kích thước/cấu trúc payload, allowlist structured action và prompt injection. |
| `tool_guard.py` | Kiểm tra tool call ngay trước execution; enforce allowlist theo skill, budget, duplicate và transaction policy. |
| `output_guard.py` | Ẩn internal analysis, redaction secret/PII trong text và diagnostic fields, chặn system-prompt leakage, giới hạn output. |
| `policies.py` | Nơi review tập trung cho regex, action contract, danh sách tool ghi và sensitive key. |
| `structure.py` | Hàm dùng chung cho Unicode normalization và giới hạn JSON-like payload. |
| `models.py` | Kiểu dữ liệu quyết định guardrail và output đã bảo vệ. |
| `pipeline.py` | Facade kết nối settings với input/output guard. |

## 4. Chính sách input

### 4.1 Unicode normalization

Tin nhắn được chuẩn hóa NFC và loại các ký tự điều khiển/zero-width thường dùng để né pattern matching. Tab và newline hợp lệ vẫn được giữ. Agent chỉ nhận `sanitized_text`, không nhận bản raw.

### 4.2 Prompt injection

Guard chỉ block các pattern có độ tin cậy cao, ví dụ:

- “Ignore previous system instructions …”
- “Bỏ qua hướng dẫn hệ thống trước đó …”
- “Reveal the system prompt/API key …”
- giả mạo `<tool_call>`, `<system>` hoặc dòng `Developer:`.
- ép agent chuyển thành terminal/developer mode.

Một câu hỏi bình thường có chữ “prompt” hoặc “system” không tự động bị block. Pattern nằm trong `policies.py` để security review có thể theo dõi thay đổi.

`context` cũng được scan vì `booking_skill_node` đưa context vào prompt. `action_payload` không được đưa vào prompt khi chạy structured action; nó được bảo vệ bằng size/depth budget và field allowlist.

Khi block, API trả `200` với câu từ chối thân thiện và `action_error` là mã máy đọc được, đồng thời **không gọi LLM hoặc tool**. Cách này giúp frontend tiếp tục render như một chat message; metric có thể nhóm theo code.

### 4.3 Structured action contract

Mỗi action chỉ nhận các top-level field được khai báo trong `ACTION_ALLOWED_FIELDS`. Ví dụ `verify_access` chỉ nhận `challenge_id` và `otp_code`; một field như `admin=true` sẽ bị chặn trước khi đến tool.

Type, required field và validation nghiệp vụ vẫn do Pydantic schema của tool và `BookingService` xử lý. Guardrail không lặp lại các rule nghiệp vụ để tránh hai source of truth.

## 5. Chính sách tool

Mỗi skill có một allowlist độc lập do `graph.py` truyền vào:

- Booking skill chỉ có thể chạy booking tools.
- Advise skill chỉ có thể chạy `search_knowledge`.

Trước khi `ToolNode` chạy, guard kiểm tra:

1. Message cuối phải là `AIMessage` có tool call hợp lệ.
2. Số call không vượt `GUARDRAILS_MAX_TOOL_CALLS_PER_MESSAGE`.
3. Tên tool thuộc allowlist của skill đang active.
4. Arguments là object và nằm trong payload budget.
5. Không có hai call giống hệt nhau trong cùng model response.
6. Tool có side effect phải chạy một mình; không batch với tool khác.
7. `confirm_test_drive_booking` chỉ chạy khi structured action đã xác nhận hoặc câu hiện tại có ý xác nhận rõ ràng.

Nếu một call trong batch vi phạm, **toàn bộ batch bị chặn** để tránh trạng thái partial-write. Guard tạo `ToolMessage(status="error")`; booking skill xử lý nó theo luồng lỗi hiện có.

Giới hạn `MAX_TOOL_CALLS=8` trong graph vẫn được giữ. Hai lớp có ý nghĩa khác nhau: graph limit chặn loop cả turn, tool guard limit chặn fan-out trong một model message.

## 6. Chính sách output và dữ liệu nhạy cảm

`OutputGuard` áp dụng các rule sau trước public response:

- `analysis` luôn trở thành chuỗi rỗng. Internal reasoning không phải API contract công khai.
- Literal secret tìm được trong kết quả tool bị loại khỏi natural-language `response` và `action_error`.
- Assignment dạng `api_key=...`, `password: ...`, `otp_code=...` bị redact.
- Số điện thoại trong natural-language response được thay bằng “hotline chính thức của showroom”; email được thay bằng `[email]`.
- Nếu output chứa marker của system prompt, toàn bộ text được thay bằng safe fallback.
- Output quá dài bị cắt theo `GUARDRAILS_MAX_OUTPUT_CHARS`.
- `tool_input` là diagnostic field nên phone, email, OTP, token và contact đều bị redact đệ quy.
- `action_data` là workflow channel cho frontend. `challenge_id` và `access_session_token` được giữ vì frontend cần chúng để hoàn tất OTP flow; raw OTP, API key, password và backend token vẫn bị redact.

`/demo/action` không còn bật `expose_otp`; raw OTP chỉ được phép dùng trong service test fixture. Production phải gửi OTP qua provider đã cấu hình và client chỉ nhận `destination_masked` cùng `challenge_id`.

Việc giữ access token trong `action_data` đòi hỏi HTTPS, CORS chính xác, không log response body ở reverse proxy và không lưu token vào localStorage lâu dài. Guardrail không thể bù cho transport/session security sai.

## 7. Cấu hình

Các biến có default an toàn trong `src/config.py` và được minh họa ở `.env.example`:

| Biến | Default | Ý nghĩa |
|---|---:|---|
| `GUARDRAILS_ENABLED` | `true` | Bật toàn bộ deterministic guardrails. |
| `GUARDRAILS_MAX_PAYLOAD_BYTES` | `16384` | Kích thước tối đa cho từng context/action/tool payload. |
| `GUARDRAILS_MAX_PAYLOAD_DEPTH` | `6` | Độ sâu JSON tối đa. |
| `GUARDRAILS_MAX_PAYLOAD_NODES` | `256` | Tổng số node tối đa trong payload. |
| `GUARDRAILS_MAX_PAYLOAD_STRING_CHARS` | `5000` | Độ dài tối đa của một string trong payload. |
| `GUARDRAILS_MAX_TOOL_CALLS_PER_MESSAGE` | `3` | Fan-out tối đa trong một model response. |
| `GUARDRAILS_MAX_OUTPUT_CHARS` | `8000` | Độ dài text tối đa trả về client. |

Không nên tắt guardrails ở production. Nếu cần debug local, tắt bằng env và khởi động lại process vì settings/guardrails được cache.

## 8. Logging và quan sát vận hành

Input bị chặn phát event `guardrail.input_blocked` qua hệ thống trace hiện có với `code`, `reason` và metadata không chứa raw message. `trace_event()` tiếp tục redact PII/secret.

Các metric nên theo dõi:

- số block theo `code` và endpoint;
- tỉ lệ false positive được support xác nhận;
- số `TOOL_NOT_ALLOWED`, `MUTATION_BATCH_NOT_ALLOWED` và `EXPLICIT_CONFIRMATION_REQUIRED`;
- p95 response latency cho request allow/block;
- số output bị truncate hoặc system-prompt fallback (có thể bổ sung counter khi đưa vào production observability).

Không ghi raw prompt, OTP, contact, access token hoặc tool result vào log để “debug guardrail”. Dùng trace ID và dữ liệu đã redact.

## 9. Kiểm thử

Test tập trung nằm tại `backend/tests/test_guardrails/` và API integration test tại `backend/tests/test_api/test_guardrails.py`.

Chạy từ folder `backend`:

```bash
pytest tests/test_guardrails tests/test_api/test_guardrails.py -q
```

Chạy toàn bộ backend regression:

```bash
pytest -q
```

Khi thêm policy mới, tối thiểu cần ba testcase:

1. attack rõ ràng phải bị block;
2. câu gần giống nhưng hợp lệ phải được allow để kiểm soát false positive;
3. API/tool phải không được gọi khi decision là block.

## 10. Cách mở rộng an toàn

### Thêm structured action

1. Thêm action vào `ChatRequest.action`.
2. Thêm mapping action → tool trong `booking_skill_node.py`.
3. Thêm field contract vào `ACTION_ALLOWED_FIELDS`.
4. Nếu có side effect, thêm tool name vào `MUTATING_TOOL_NAMES`.
5. Nếu là hành động irreversible/high-impact, thêm confirmation policy riêng.
6. Viết test allow, unknown field, missing confirmation và side-effect isolation.

### Thêm tool

1. Bind tool đúng skill trong `graph.py`.
2. Không dùng một ToolNode chung cho mọi skill.
3. Phân loại read-only hay mutating.
4. Đảm bảo tool có Pydantic schema chặt và domain service tự kiểm tra authorization/idempotency.
5. Thêm sensitive output key vào policy nếu tool trả credential mới.

### Thêm regex prompt injection

Chỉ thêm pattern có tín hiệu hành động + mục tiêu rõ ràng. Tránh block theo một keyword đơn lẻ. Luôn có negative testcase để chứng minh câu hợp lệ không bị chặn.

## 11. Giới hạn đã biết

- Regex không phát hiện mọi prompt injection đa ngôn ngữ hoặc được mã hóa tinh vi. Boundary allowlist và tool authorization mới là lớp bảo vệ quan trọng nhất.
- Guardrails không đánh giá tính đúng/sai của nội dung tư vấn xe; cần grounding/RAG citation và eval riêng.
- Guardrails không thay API rate limiter theo IP/user. OTP cooldown hiện nằm trong `BookingService`; chat endpoint vẫn nên có gateway rate limit khi public Internet.
- Guardrails không thay authentication cho admin import/dashboard endpoints.
- Output redaction giảm rủi ro accidental leakage nhưng secret không nên được đưa vào LLM context ngay từ đầu.

## 12. Checklist production

- Giữ `GUARDRAILS_ENABLED=true`.
- Bắt buộc HTTPS và cấu hình CORS theo origin cụ thể.
- Rate limit `/api/v1/chat`, structured action và OTP theo IP + user/session.
- Bảo vệ admin endpoints bằng authentication/authorization.
- Không log request/response body tại proxy/APM nếu chưa redact.
- Alert khi guardrail block tăng đột biến hoặc khi tool policy bị vi phạm.
- Chạy guardrail test và full regression trước mỗi release.
- Review `policies.py` khi thêm action, tool, credential hoặc kênh tích hợp mới.
