# Plan Limit - Thiết kế triển khai tinh gọn

Tài liệu này là nguồn thiết kế thống nhất để hoàn thiện rate limit và giới hạn chi phí LLM cho project hiện tại. Thiết kế ưu tiên tận dụng code và database schema đã có, chỉ bổ sung những thay đổi trực tiếp cần thiết để chặn spam và tránh vượt ngân sách.

Thiết kế không bổ sung Redis, không tạo thêm hệ thống budget bucket riêng, không thay đổi luồng nghiệp vụ booking và chưa bao gồm phạm vi viết testcase.

## 1. Mục tiêu

- Chặn request burst trước khi request đi vào agent hoặc gọi LLM.
- Hạn chế spam từ người dùng anonymous bằng anonymous session kết hợp IP.
- Ước lượng chi phí trước mỗi LLM call và chỉ gọi provider khi còn ngân sách.
- Giới hạn số LLM call có thể phát sinh từ một chat request.
- Hoạt động đúng khi production chạy nhiều backend instance sử dụng chung PostgreSQL.
- Tận dụng `rate_limit_counters`, `llm_budget_ledger` và `usage_budget.py` hiện có.

## 2. Phạm vi giữ lại

Thiết kế chỉ giữ ba nhóm kiểm soát:

1. HTTP rate limit theo anonymous session và IP.
2. OTP rate limit theo contact hash hoặc challenge ID.
3. LLM limit gồm số call mỗi chat request và ngân sách theo session/ngày, global/ngày.

Các nội dung sau không triển khai trong phạm vi hiện tại:

- Redis.
- Bảng `llm_budget_buckets` mới.
- Budget riêng theo conversation.
- Money budget theo IP vì rate limit IP đã đóng vai trò chống abuse cơ bản.
- Pricing registry hoặc bảng giá trong database.
- Chuyển toàn bộ dữ liệu tiền sang `microUSD`.
- Dashboard chi phí và reconciliation job riêng.
- Testcase tự động cho rate limit và budget.

## 3. Anonymous identity

Người dùng không cần đăng nhập nên backend sử dụng hai lớp nhận diện:

- `anon_session_id`: cookie ngẫu nhiên do server cấp, dùng làm identity chính.
- Client IP: lớp giới hạn bổ sung để chặn client xóa cookie hoặc tạo nhiều session.

Không dùng `conversation_id` làm user identity vì client có thể tự tạo conversation mới.

Cookie `anon_session_id` sử dụng:

- `HttpOnly=true`.
- `SameSite=Lax`.
- `Secure=true` khi chạy HTTPS/production.
- TTL mặc định 30 ngày.
- Không chứa thông tin cá nhân và không có giá trị authentication.

IP mặc định lấy từ `request.client.host`. Chỉ sử dụng `X-Forwarded-For` hoặc `X-Real-IP` khi `RATE_LIMIT_TRUST_PROXY_HEADERS=true` và reverse proxy production đã được cấu hình là nguồn tin cậy.

## 4. HTTP rate limit

### 4.1 Luồng xử lý

1. Request đi vào `RateLimitMiddleware`.
2. Middleware đọc hoặc tạo `anon_session_id` và xác định client IP.
3. Middleware ánh xạ request sang nhóm `chat` hoặc `demo_action`.
4. Store tăng counter theo session và IP trong window hiện tại.
5. Nếu vượt một trong các limit, backend trả `429` kèm `Retry-After`.
6. Nếu hợp lệ, request tiếp tục vào guardrail, route và agent hiện tại.

Việc kiểm tra `/chat` phải hoàn tất trước khi gọi agent để request bị chặn không phát sinh chi phí LLM.

### 4.2 Limit mặc định

- `/api/v1/chat`: 10 request/phút/session.
- `/api/v1/chat`: 60 request/phút/IP.
- `/api/v1/demo/action`: 30 request/phút/session.
- `/api/v1/demo/action`: 120 request/phút/IP.
- OTP request: 3 request/giờ/contact hash, ngoài cooldown hiện có.
- OTP verify: 5 request/phút/challenge ID, ngoài max attempts hiện có.

### 4.3 Storage

Tiếp tục dùng bảng `rate_limit_counters` hiện có. Không tạo thêm bảng rate-limit khác.

Counter production cần được tăng bằng thao tác atomic của PostgreSQL, ưu tiên `INSERT ... ON CONFLICT ... DO UPDATE SET count = count + 1 RETURNING count`. Cách này thay cho luồng đọc count rồi update tách rời hiện tại, tránh hai request đồng thời cùng đọc một giá trị cũ.

Đối với SQLite local, có thể giữ transaction hiện tại vì local không phải môi trường chạy nhiều instance.

Các row đã hết hạn có thể được dọn định kỳ bằng tác vụ bảo trì đơn giản. Việc cleanup không nằm trên critical path của request.

### 4.4 OTP

- OTP request dùng contact đã normalize và hash để tạo rate-limit key.
- Không lưu email hoặc số điện thoại thô trong key và log.
- OTP verify chỉ tăng counter theo challenge sau khi xác nhận challenge tồn tại, tránh tạo nhiều row từ challenge ID ngẫu nhiên.
- Cooldown và max attempts hiện tại tiếp tục được giữ nguyên.

### 4.5 Response

Khi vượt rate limit:

- HTTP status: `429 Too Many Requests`.
- Header: `Retry-After`.
- Error code: `RATE_LIMIT_EXCEEDED`.
- Message không tiết lộ bucket key hoặc limit global của hệ thống.

## 5. Giới hạn LLM call trong một chat request

Một request `/chat` có thể chạy classifier, skill node và quay lại skill node sau tool call. Vì vậy một HTTP request có thể tạo nhiều LLM call.

Thiết kế bổ sung `llm_call_count` vào metadata của agent state:

1. `/chat` khởi tạo `llm_call_count = 0`.
2. Trước mỗi LLM call, wrapper kiểm tra count với `LLM_MAX_CALLS_PER_TURN`.
3. Nếu còn quota, tăng count trước khi gọi provider.
4. Nếu đã đạt limit, không gọi provider và kết thúc graph bằng lỗi `LLM_CALL_LIMIT_EXCEEDED`.

Không cần lưu count này vào database vì count chỉ tồn tại trong thời gian xử lý một request. `trace_id` hiện có được dùng để log và liên kết các call của cùng request; chưa cần bổ sung `turn_id` riêng.

Tool-call limit hiện có trong LangGraph và guardrail vẫn được giữ. LLM-call limit là lớp bổ sung, không thay thế tool-call limit.

## 6. Money budget cho LLM

### 6.1 Budget được giữ lại

Chỉ enforce hai mức:

- Anonymous session/ngày: giới hạn chi phí một browser session có thể sử dụng trong ngày.
- Global/ngày: hard limit bảo vệ tổng chi phí hệ thống.

Không enforce budget theo conversation hoặc IP trong phạm vi hiện tại. IP đã có HTTP rate limit và có nguy cơ chặn nhầm nhiều người dùng chung NAT/Wi-Fi nếu dùng làm money budget.

Giá trị mặc định:

- Session: 1 USD/ngày/session.
- Global: 20 USD/ngày.

Các giá trị này chỉ là default và phải cấu hình lại theo ngân sách thực tế trước khi deploy production.

### 6.2 Ước lượng chi phí

Trước mỗi provider call:

1. Ước lượng input token từ toàn bộ payload gửi provider.
2. Dùng output token dự kiến từ config.
3. Tính estimated cost theo giá input/output được cấu hình.
4. Kiểm tra session budget và global budget.
5. Chỉ tạo reservation và gọi provider nếu cả hai budget còn đủ.

Công thức:

`estimated_cost = input_tokens / 1_000_000 * input_price + estimated_output_tokens / 1_000_000 * output_price`

Input token có thể tiếp tục ước lượng bằng `ceil(character_count / 4)` trong phạm vi hiện tại. Payload tính token phải gồm system prompt, conversation history và tool schema nếu chúng được gửi đến provider.

Project hiện chỉ cấu hình một model hoạt động tại một thời điểm, vì vậy tiếp tục dùng một bộ giá input/output tập trung trong `Settings`; chưa tạo pricing registry riêng. Khi đổi model hoặc provider, operator phải cập nhật giá trong environment config.

### 6.3 Reservation và xử lý đồng thời

Tiếp tục sử dụng `llm_budget_ledger` hiện có, không tạo `llm_budget_buckets`.

Để tránh race condition khi nhiều instance cùng kiểm tra budget:

1. Mở database transaction.
2. Trên PostgreSQL, lấy transaction advisory lock theo `usage_date` trước khi tính tổng ledger và insert reservation.
3. Tính tổng các row có trạng thái đang giữ hoặc đã hoàn thành trong ngày.
4. Kiểm tra global và session limit.
5. Insert ledger row trạng thái `reserved` trong cùng transaction.
6. Commit để nhả lock.

Advisory lock theo ngày làm các thao tác reserve tuần tự trong một khoảng rất ngắn, đủ phù hợp với lưu lượng hiện tại và không yêu cầu thêm bảng. Nếu lưu lượng LLM tăng cao đến mức lock này trở thành bottleneck, khi đó mới cần cân nhắc budget counter riêng.

SQLite local dùng transaction hiện có; không dùng SQLite làm căn cứ đánh giá concurrency production.

### 6.4 Finalize sau provider call

- Nếu provider trả usage metadata, cập nhật actual input/output token và actual cost.
- Nếu provider không trả usage, dùng estimated cost làm actual cost bảo thủ.
- Nếu lỗi chắc chắn xảy ra trước khi request được gửi đến provider, chuyển reservation sang `failed` và không tính chi phí.
- Nếu timeout hoặc mất kết nối mà không biết provider đã xử lý hay chưa, chuyển trạng thái sang `unknown` và tiếp tục tính estimated cost vào daily usage để tránh underestimate.

Không cần thêm cột mới để có trạng thái `unknown` vì cột `status` hiện tại là text. Chưa triển khai reconciliation job; trạng thái `unknown` được giữ để audit thủ công khi cần.

Chi phí tiếp tục dùng schema USD hiện tại để tránh migration lớn. Trong code tính toán sử dụng `Decimal`, chỉ convert tại biên đọc/ghi database, tránh cộng tiền trực tiếp bằng binary float trong business logic.

## 7. Điểm gọi LLM thống nhất

Tiếp tục sử dụng `invoke_with_budget(...)` trong `backend/src/services/usage_budget.py` làm wrapper chung. Chưa cần tạo thêm `LLMGateway`, `PricingRegistry` hoặc nhiều service class mới.

Wrapper chịu trách nhiệm:

1. Kiểm tra `llm_call_count`.
2. Ước lượng token và chi phí.
3. Reserve budget trong PostgreSQL.
4. Gọi `llm.ainvoke(...)`.
5. Finalize actual usage hoặc cập nhật trạng thái lỗi.

Các agent node không được gọi provider trực tiếp ngoài wrapper này.

Classifier phải xử lý `BudgetExceededError` và `LLMCallLimitExceededError` riêng. Không được bắt các lỗi này bằng exception chung rồi fallback sang skill node, vì fallback có thể tiếp tục phát sinh LLM call sau khi đã chạm limit.

## 8. Config tập trung

Config tiếp tục đặt trong `backend/src/config.py` và được khai báo tại `.env.example`.

Rate limit giữ các config hiện có:

- `RATE_LIMIT_ENABLED`.
- `RATE_LIMIT_TRUST_PROXY_HEADERS`.
- `RATE_LIMIT_ANON_COOKIE_NAME`.
- `RATE_LIMIT_ANON_COOKIE_TTL_SECONDS`.
- `RATE_LIMIT_CHAT_PER_SESSION_PER_MINUTE`.
- `RATE_LIMIT_CHAT_PER_IP_PER_MINUTE`.
- `RATE_LIMIT_DEMO_ACTION_PER_SESSION_PER_MINUTE`.
- `RATE_LIMIT_DEMO_ACTION_PER_IP_PER_MINUTE`.
- `RATE_LIMIT_OTP_REQUEST_PER_CONTACT_PER_HOUR`.
- `RATE_LIMIT_OTP_VERIFY_PER_CHALLENGE_PER_MINUTE`.

LLM budget giữ các config hiện có:

- `LLM_DAILY_BUDGET_ENABLED`.
- `LLM_DAILY_MAX_COST_USD`.
- `LLM_SESSION_MAX_COST_USD_PER_DAY`.
- `LLM_ESTIMATED_INPUT_TOKEN_PRICE_PER_1M`.
- `LLM_ESTIMATED_OUTPUT_TOKEN_PRICE_PER_1M`.
- `LLM_ESTIMATED_OUTPUT_TOKENS_PER_CALL`.

Bổ sung duy nhất:

- `LLM_MAX_CALLS_PER_TURN`.

`LLM_IP_MAX_COST_USD_PER_DAY` hiện có sẽ không được dùng và nên được xóa khỏi config để tránh hiểu nhầm policy.

## 9. Thay đổi source code cần thực hiện

### `backend/src/security/rate_limit.py`

- Giữ middleware, route rules và cookie logic hiện có.
- Đổi counter update sang PostgreSQL atomic upsert.
- Đảm bảo nhiều rule không làm mất quota ngoài ý muốn khi một rule khác reject request.
- Giữ interface đủ đơn giản để có thể đổi store sau này nhưng không implement Redis.

Ảnh hưởng: chỉ thay đổi request bị spam; không thay đổi business logic.

### `backend/src/security/client_identity.py`

- Giữ logic identity hiện tại.
- Đảm bảo cookie có `Secure` trong production HTTPS.
- Chỉ trust proxy header khi config bật.

Ảnh hưởng: thêm cookie anonymous, không tạo user account và không thay đổi authentication.

### `backend/src/services/booking/access.py`

- Dùng contact hash cho OTP request.
- Validate challenge trước khi tăng challenge counter.
- Tận dụng `rate_limit_counters` hiện có.

Ảnh hưởng: giữ nguyên cooldown, OTP expiry và max attempts.

### `backend/src/services/usage_budget.py`

- Giữ module và wrapper hiện có.
- Dùng `Decimal` trong logic tính tiền.
- Bỏ IP budget check.
- Thêm PostgreSQL advisory lock trong transaction reserve.
- Thêm `llm_call_count` check.
- Phân biệt pre-provider failure với ambiguous timeout.
- Hỗ trợ trạng thái `unknown`.

Ảnh hưởng: không đổi prompt hoặc provider configuration; có thể từ chối LLM call trước provider khi hết budget.

### `backend/src/api/routes.py`

- Tiếp tục truyền `trace_id`, `conversation_id`, `anon_session_id` và `client_ip` vào metadata.
- Khởi tạo `llm_call_count = 0` cho mỗi chat request.

Ảnh hưởng: không thay đổi request/response model hiện tại.

### Agent nodes

Các file:

- `backend/src/agents/nodes/classifier_node.py`.
- `backend/src/agents/nodes/booking_skill_node.py`.
- `backend/src/agents/nodes/advise_skill_node.py`.

Thay đổi:

- Tất cả LLM call tiếp tục đi qua `invoke_with_budget(...)`.
- Truyền và cập nhật `llm_call_count`.
- Budget/call-limit exception phải kết thúc luồng an toàn, không fallback sang một LLM call khác.

Ảnh hưởng: không đổi graph topology, prompt hoặc tool logic.

### `backend/src/config.py` và `.env.example`

- Thêm `LLM_MAX_CALLS_PER_TURN`.
- Xóa `LLM_IP_MAX_COST_USD_PER_DAY`.
- Giữ các config rate limit, daily/session budget và estimated pricing hiện có.

### Database

- Không tạo bảng mới.
- Không thêm budget bucket table.
- Không migration ledger sang microUSD.
- Giữ `rate_limit_counters` và `llm_budget_ledger` hiện tại.
- Chỉ điều chỉnh câu query/transaction để counter và reservation an toàn hơn trên PostgreSQL.

Ảnh hưởng DB chủ yếu là write counter và ledger đã tồn tại; không thay đổi cấu trúc dữ liệu nghiệp vụ booking.

## 10. Error contract

Các error code cần dùng thống nhất:

- `RATE_LIMIT_EXCEEDED`: HTTP `429` và có `Retry-After`.
- `LLM_BUDGET_EXCEEDED`: không gọi provider, agent trả message an toàn.
- `LLM_CALL_LIMIT_EXCEEDED`: dừng graph vì một request đã tạo quá nhiều LLM call.
- `LLM_PROVIDER_FAILED`: provider call thất bại thông thường.

Không trả current global usage, budget còn lại hoặc internal bucket key cho client.

## 11. Logging tối thiểu

Không xây dashboard hoặc hệ thống metrics mới trong phạm vi này. Chỉ bổ sung structured log cần thiết để vận hành:

- `trace_id`, `conversation_id`.
- Ledger reservation ID.
- Model và loại call: classifier, booking hoặc advise.
- Estimated/actual token và cost.
- Final status hoặc error code.

Không log raw prompt, OTP, contact hoặc anonymous cookie.

## 12. Rủi ro còn lại

- PostgreSQL advisory lock theo ngày tuần tự hóa reservation. Đây là lựa chọn đơn giản phù hợp lưu lượng hiện tại nhưng có thể thành bottleneck nếu LLM QPS tăng cao.
- Estimate token bằng số ký tự có thể lệch với tiếng Việt hoặc tool schema; actual usage được dùng để hiệu chỉnh sau call.
- Pricing config có thể lỗi thời khi đổi model/provider; cần cập nhật cùng lúc thay model.
- `anon_session_id` có thể bị xóa hoặc đổi; IP rate limit và global budget vẫn là lớp bảo vệ còn lại.
- User dùng chung NAT có thể cùng chạm IP rate limit; cần theo dõi thực tế trước khi giảm ngưỡng.
- Ledger dùng USD schema hiện tại nên không chính xác bằng integer microUSD tuyệt đối; sử dụng `Decimal` trong code giúp giảm rủi ro mà không cần migration lớn.
- Trạng thái `unknown` chưa có job reconcile tự động; estimated cost vẫn được tính để hệ thống không vượt budget do timeout.

## 13. Tiêu chí hoàn thành

Implementation được xem là hoàn thành khi:

- Chat/demo/OTP bị chặn đúng trước khi tạo tác vụ tốn chi phí.
- Rate-limit counter production được tăng atomically.
- Mỗi chat request không vượt `LLM_MAX_CALLS_PER_TURN`.
- Tất cả agent LLM call đi qua `invoke_with_budget(...)`.
- Global và session daily budget được reserve an toàn khi chạy nhiều instance PostgreSQL.
- Classifier không fallback sang LLM call khác sau khi chạm budget/call limit.
- Timeout không rõ trạng thái provider được ghi `unknown` và vẫn giữ estimated cost.
- Không có bảng database mới và không thay đổi schema nghiệp vụ booking.

## 14. Kết luận

Thiết kế tinh gọn giữ lại các lớp bảo vệ có giá trị trực tiếp: anonymous session + IP rate limit, giới hạn số LLM call mỗi request và money budget theo session/global. Hệ thống tận dụng hai bảng và wrapper hiện có, chỉ sửa logic atomicity và exception handling. Cách tiếp cận này giảm đáng kể thay đổi database và source code nhưng vẫn bảo vệ được các rủi ro chính là spam request, agent gọi LLM quá nhiều và tổng chi phí provider vượt ngân sách.
